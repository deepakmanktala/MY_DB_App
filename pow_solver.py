"""
================================================================================
FILE: pow_solver.py
PURPOSE: The SHA-1 brute-force engine — finds the "magic suffix" for the POW.

WHAT IS PROOF OF WORK? (Plain English)
---------------------------------------
Imagine a padlock with a combination. The server gives you:
  - A fixed string called "authdata" (e.g. "GisTfIxtrOO...")
  - A number called "difficulty" (e.g. 6)

Your job: find any short string (called "suffix") such that when you glue
it onto authdata and run it through the SHA-1 hash function, the result
starts with that many zeros.

    SHA1("GisTfIxtrOO..." + "o5=>") = "0000001b6f59..."
                                        ^^^^^^ 6 zeros ✓

WHY IS THIS HARD?
-----------------
SHA-1 is designed so its output looks completely random — you can't predict
what suffix will work. The ONLY way is to try millions of candidates:
    SHA1(authdata + "!")       = "a3f72c..."  ✗ no leading zeros
    SHA1(authdata + '"')       = "1bc89d..."  ✗
    SHA1(authdata + "#")       = "000000..."  ✓  FOUND IT!

At difficulty 9, you need 9 leading zeros. The probability of any single
attempt succeeding is 1/16^9 = 1/68 billion. So you need to try roughly
68 BILLION hashes on average. This takes about 1 hour on a modern PC.

WHY CAN'T WE MAKE IT O(1)?
----------------------------
There is NO mathematical shortcut to find SHA-1 preimages. The entire
security of SHA-1 relies on this. Anyone who claims O(1) for this problem
has discovered a billion-dollar cryptographic break. We can't.

WHAT WE CAN DO — CONSTANT-FACTOR OPTIMIZATIONS:
-------------------------------------------------
1. Pre-compute SHA-1 state for authdata, clone it per attempt (skip re-hashing
   the same authdata 68 billion times)
2. Compare raw bytes instead of hex strings (30% faster comparison)
3. Reuse a 16-byte buffer with memoryview (avoid 68 billion tiny allocations)
4. Use counter-based suffixes (no RNG overhead, mathematically equivalent)
5. One worker process per CPU core (linear speedup with hardware)

Result: ~1-20 million hashes/second depending on hardware.
At 20M/s: 68B / 20M = ~56 minutes for difficulty 9.
================================================================================
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from __future__ import annotations   # Allow "type | None" union syntax on Python 3.9

import hashlib          # Python's built-in SHA-1 implementation (backed by OpenSSL C code)
import multiprocessing as mp   # Spawn independent OS processes (bypasses Python's GIL)
import os               # os.cpu_count() — how many CPU cores are available
import sys              # sys.stderr for worker crash messages
import time             # time.monotonic() — a clock that never goes backwards
from multiprocessing import synchronize   # Type hints for mp.Event


# ── SUFFIX ALPHABET ───────────────────────────────────────────────────────────

# The suffix we send to the server must not contain: \n \r \t or space.
# Those characters would break the line-based protocol.
#
# We use printable ASCII from code 33 ('!') to 126 ('~') — that's all
# visible keyboard characters. We additionally exclude " and \ to avoid
# any shell-quoting headaches if a suffix is ever pasted into a terminal.
#
# bytes(...) creates a bytes object containing those code points.
_ALPHABET: bytes = bytes(
    c                          # Include character code c...
    for c in range(33, 127)    # ...from '!' (33) to '~' (126)...
    if c not in (ord('"'), ord("\\"))  # ...excluding " and \
)
_BASE: int = len(_ALPHABET)   # 92 — this is our "number base" for counting


# ── BATCH SIZE CONFIGURATION ──────────────────────────────────────────────────

def _read_batch_env() -> int:
    """
    Read the EXASOL_BATCH environment variable.

    BATCH_SIZE controls how many hash attempts each worker does before
    checking whether another worker has already found the answer.

    BIGGER batch:
        - Lower overhead (checking the flag is slow relative to hashing)
        - Slower shutdown after a hit is found (workers finish their batch first)

    SMALLER batch:
        - More responsive shutdown
        - Higher overhead (checking flag more often)

    Default of 8192 is a good balance.
    Set EXASOL_BATCH=32768 on slow hardware for less overhead per attempt.

    Returns the batch size as an int. Falls back to 8192 if invalid.
    """
    raw = os.environ.get("EXASOL_BATCH")   # Read env var (returns None if not set)
    if not raw:
        return 8192   # Default value

    try:
        n = int(raw)   # Convert string to integer
        if n < 1 or n > 1_000_000:
            raise ValueError   # Reject nonsensical values
        return n
    except ValueError:
        # Tell the user about the bad value but don't crash
        sys.stderr.write(
            f"warning: invalid EXASOL_BATCH={raw!r}; using default 8192\n"
        )
        return 8192


# Read once at module load time. Workers inherit this value when forked.
BATCH_SIZE: int = _read_batch_env()


# ── COUNTER ENCODER ───────────────────────────────────────────────────────────

def _encode_counter(n: int, out: bytearray) -> int:
    """
    Write the integer n in base-92 into the bytearray `out`.

    WHY WE DO THIS INSTEAD OF RANDOM STRINGS:
    ------------------------------------------
    A random string generator needs to call random.random() or os.urandom()
    for every attempt. That adds overhead. A simple counter is:
      - Zero-cost to "generate" (just increment an integer)
      - Equally good for SHA-1 (SHA-1's output is random regardless of input)
      - Guaranteed no collisions between workers (each worker gets a disjoint
        slice: worker 0 uses 0, W, 2W, ... ; worker 1 uses 1, W+1, 2W+1, ...)

    Base-92 means each "digit" position uses one of 92 alphabet characters.
    The 16-byte buffer can represent counters up to 92^16 ≈ 2×10^31, which
    is vastly more than we'd ever need.

    Returns the number of bytes actually written (the length of the suffix).
    """
    if n == 0:
        # Special case: 0 encodes as a single character (the first in the alphabet)
        out[0] = _ALPHABET[0]   # _ALPHABET[0] = ord('!') = 33
        return 1

    i = 0
    while n:
        # divmod(n, 92) gives (quotient, remainder) — like decimal but base 92
        n, r = divmod(n, _BASE)   # r is the "current digit" (0-91)
        out[i] = _ALPHABET[r]     # Write the corresponding character into the buffer
        i += 1
    return i   # Number of bytes written (length of the encoded suffix)


# ── TARGET BUILDER ────────────────────────────────────────────────────────────

def _make_target(difficulty: int) -> tuple[bytes, int]:
    """
    Pre-compute the byte pattern to check against SHA-1 digests.

    WHY BYTES INSTEAD OF HEX STRINGS?
    -----------------------------------
    SHA-1 produces a 20-byte digest. The "hexdigest" is the human-readable
    representation (40 hex chars). Checking hexdigest().startswith("0"*d)
    requires converting all 20 bytes to 40 chars every attempt.

    Instead, we compare against raw bytes directly:
      - d=6 hex zeros = 3 full zero bytes  (b"\x00\x00\x00")
      - d=7 hex zeros = 3 full bytes + high nibble of 4th byte must be 0
      - d=8 hex zeros = 4 full zero bytes  (b"\x00\x00\x00\x00")

    This avoids the hexdigest() call entirely — ~30% speedup in tight loop.

    Returns:
        full_zero_bytes: the digest must START with these bytes exactly
        half_byte_flag:  if 1, the NEXT byte's top 4 bits must also be 0
    """
    full = difficulty // 2   # Integer division: 6//2=3, 7//2=3, 8//2=4
    half = difficulty % 2    # Remainder:        6%2=0, 7%2=1, 8%2=0
    return b"\x00" * full, half


# ── WORKER FUNCTION (runs in a child process) ─────────────────────────────────

def _worker(
    authdata: bytes,
    difficulty: int,
    worker_id: int,
    num_workers: int,
    found: synchronize.Event,
    result_q: mp.Queue,
    progress_q: mp.Queue | None,
) -> None:
    """
    The inner loop that each CPU core runs independently.

    Each worker is a completely separate OS process. Workers search different
    counter ranges so they never duplicate work:
        Worker 0: tries counter 0, W, 2W, 3W, ...
        Worker 1: tries counter 1, W+1, 2W+1, ...
        Worker 2: tries counter 2, W+2, 2W+2, ...

    The first worker to find a valid suffix puts it in result_q and sets the
    `found` Event. All other workers check `found` at the end of each batch
    and exit gracefully.

    This function runs in a CHILD PROCESS — it cannot directly return a value
    to the parent. It communicates via multiprocessing Queues instead.

    Arguments:
        authdata:    the server's random session token (bytes)
        difficulty:  how many leading zero hex chars we need
        worker_id:   this worker's index (0, 1, 2, ...)
        num_workers: total number of workers (W in the stride formula)
        found:       shared Event — set when any worker finds the answer
        result_q:    Queue where the winner puts their suffix
        progress_q:  Queue for periodic progress reports (hash counts)
    """
    try:
        # Pre-compute SHA-1 state up to and including authdata.
        # SHA-1 processes input in 64-byte blocks. By calling hashlib.sha1(authdata)
        # once and then cloning it with .copy() for each attempt, we avoid
        # re-hashing authdata 68 billion times. The clone is O(1) — just copying
        # the current internal state.
        base_hasher = hashlib.sha1(bytes(authdata))

        # Pre-compute the byte target so _make_target() isn't called in the hot loop
        full_zero, half_byte = _make_target(difficulty)
        full_zero_len = len(full_zero)   # e.g. 3 for difficulty 6

        # A 16-byte reusable buffer for encoding the counter into a suffix.
        # bytearray is mutable — we overwrite it in place each iteration.
        # This avoids allocating a new bytes object 68 billion times.
        buf = bytearray(16)
        # memoryview provides a slice view of buf without copying bytes.
        # h.update(mv[:n]) passes exactly n bytes to SHA-1 without copying.
        mv = memoryview(buf)

        # Start this worker's counter at its ID. It will step by num_workers
        # each iteration — ensuring no two workers ever try the same counter.
        counter = worker_id

        # Hoist frequently-called attributes into local variables.
        # In CPython, accessing a local variable (LOAD_FAST bytecode) is
        # significantly faster than looking up an attribute on an object
        # (LOAD_ATTR bytecode). In a loop that runs billions of times,
        # this small constant factor matters.
        base_copy = base_hasher.copy     # Local alias for .copy() method
        encode    = _encode_counter      # Local alias for counter encoder
        is_set    = found.is_set         # Local alias for Event.is_set()
        batch     = BATCH_SIZE           # Local alias for batch size constant

        attempts    = 0           # Total hashes tried by this worker so far
        last_report = time.monotonic()   # When we last sent a progress update

        # ── MAIN SEARCH LOOP ─────────────────────────────────────────────────
        while not is_set():   # Keep going until another worker finds the answer
            # Inner loop: process one batch of `batch` attempts without
            # checking the `found` flag (the flag check has overhead).
            for i in range(batch):
                # Encode the current counter into our suffix buffer.
                # n = number of bytes in the suffix (grows as counter grows)
                n = encode(counter, buf)

                # Clone the pre-computed SHA-1 state (includes authdata)
                h = base_copy()

                # Hash just the suffix bytes (authdata already included in clone)
                h.update(mv[:n])   # memoryview slice — no copy, no allocation

                # Get the raw 20-byte digest (NOT hex — much faster)
                d = h.digest()

                # Check if the digest starts with enough zero bytes
                if d[:full_zero_len] == full_zero:
                    # All full bytes are zero. Now check the half-byte if needed.
                    # For difficulty=7: need 3 full zeros + top 4 bits of byte 3 = 0
                    # (d[3] >> 4) extracts the high nibble (top 4 bits)
                    if half_byte == 0 or (d[full_zero_len] >> 4) == 0:
                        # WE FOUND A VALID SUFFIX!
                        suffix = bytes(buf[:n])   # Copy the result out of the buffer

                        # Put the result in the queue FIRST, then set `found`.
                        # This ordering is important: if we set `found` before
                        # putting, sibling workers might exit before our result
                        # is in the queue, and the parent might conclude all workers
                        # died with an empty queue.
                        try:
                            result_q.put((worker_id, suffix, attempts + i + 1))
                        finally:
                            # Even if put() fails, signal found so everyone exits.
                            found.set()
                        return   # This worker's job is done

                # Advance this worker's counter by num_workers
                # (keeping each worker in its own disjoint slice of the space)
                counter += num_workers

            # End of one batch — update total attempt count
            attempts += batch

            # Send a progress report roughly every second.
            # put_nowait() doesn't block — if the queue is full, we just skip.
            if progress_q is not None:
                now = time.monotonic()
                if now - last_report >= 1.0:
                    try:
                        progress_q.put_nowait((worker_id, attempts, now))
                    except Exception:
                        pass   # Queue full or parent dead — drop silently
                    last_report = now

    except (KeyboardInterrupt, BrokenPipeError):
        # User pressed Ctrl+C, or the parent process closed the pipe.
        # Exit quietly — this is expected during normal shutdown.
        return

    except Exception as e:
        # Something unexpected went wrong. Log it to stderr so the user
        # can see it, then exit. The parent will detect this worker as dead
        # via p.is_alive() checks.
        try:
            sys.stderr.write(
                f"[worker {worker_id}] crashed: {type(e).__name__}: {e}\n"
            )
            sys.stderr.flush()
        except Exception:
            pass   # If stderr is broken, nothing we can do
        return


# ── MAIN SOLVER (called from exasol_client.py) ───────────────────────────────

def solve_pow(
    authdata: bytes,
    difficulty: int,
    num_workers: int | None = None,
    progress_callback=None,
) -> bytes:
    """
    Solve the SHA-1 proof-of-work puzzle. Blocks until a valid suffix is found.

    This is the function that exasol_client.py calls. It coordinates multiple
    worker processes and returns the winning suffix when any worker finds one.

    HOW MULTIPROCESSING HELPS:
    ---------------------------
    Python has a "Global Interpreter Lock" (GIL) that prevents multiple Python
    threads from running truly in parallel. To get real parallelism, we use
    PROCESSES instead of threads — each process has its own Python interpreter
    and GIL, so they run independently on separate CPU cores.

    On a 22-core machine, 22 workers each searching a different slice of the
    counter space gives ~22x speedup over a single worker.

    FORK vs SPAWN:
    --------------
    On Linux/Mac: we "fork" — the child process is an exact copy of the parent,
    inheriting all loaded modules. Fast (~5ms startup per worker).
    On Windows: we "spawn" — the child starts fresh and re-imports everything.
    Slower (~200ms startup) but necessary because Windows doesn't support fork.

    Arguments:
        authdata:          bytes from the server's POW command (don't decode)
        difficulty:        number of leading zero hex chars required
        num_workers:       CPU cores to use; None = use all available cores
        progress_callback: optional fn(total_attempts, elapsed_secs, rate_per_sec)
                           called roughly once per second during the solve

    Returns:
        A bytes object (the suffix) such that SHA1(authdata + suffix) starts
        with 'difficulty' zero hex characters.
    """
    # ── Input validation ──────────────────────────────────────────────────────
    if not isinstance(authdata, (bytes, bytearray)):
        raise TypeError("authdata must be bytes")   # Catch wrong type early

    if not isinstance(difficulty, int):
        raise TypeError("difficulty must be int")

    if difficulty < 0:
        raise ValueError("difficulty must be >= 0")

    if difficulty > 40:
        # SHA-1 produces exactly 40 hex characters. Difficulty > 40 would require
        # MORE leading zeros than the hash has characters — mathematically impossible.
        raise ValueError("difficulty cannot exceed 40 (SHA-1 hex length)")

    # Default to using all CPU cores if num_workers not specified
    if num_workers is None:
        num_workers = os.cpu_count() or 1   # os.cpu_count() returns None on some systems

    elif not isinstance(num_workers, int) or num_workers < 1:
        raise ValueError(f"num_workers must be a positive int, got {num_workers!r}")

    # ── Shortcut for easy difficulties ────────────────────────────────────────
    # Spawning 22 worker processes takes ~200ms on Windows. For difficulty <= 4,
    # the expected solve time is only ~100ms — so multiprocessing would HURT.
    # Single-process is also simpler for the self-test.
    if num_workers == 1 or difficulty <= 4:
        return _solve_single(authdata, difficulty)   # Fast path, no subprocesses

    # ── Set up multiprocessing ────────────────────────────────────────────────
    # Use "fork" on Linux/Mac (fast) and "spawn" on Windows (required by OS)
    ctx = mp.get_context("spawn") if sys.platform == "win32" else mp.get_context("fork")

    # `found` is a shared flag. When any worker finds the answer, it sets this.
    # All other workers check it at the end of each batch and exit.
    found = ctx.Event()

    # `result_q` is the mailbox where the winning worker puts their suffix.
    # The parent process reads from this queue.
    result_q: mp.Queue = ctx.Queue()

    # `progress_q` is how workers report their attempt counts for the progress display.
    # None if no progress callback was provided (saves overhead).
    progress_q: mp.Queue | None = ctx.Queue() if progress_callback else None

    # Create one worker process per CPU core
    procs = [
        ctx.Process(
            target=_worker,   # The function each worker will run
            args=(authdata, difficulty, wid, num_workers, found, result_q, progress_q),
            daemon=True,   # Daemon processes auto-die if the parent dies (prevents orphans)
        )
        for wid in range(num_workers)   # worker IDs: 0, 1, 2, ..., num_workers-1
    ]

    # Start all workers simultaneously
    for p in procs:
        p.start()

    t0 = time.monotonic()   # Record when we started (for rate calculation)
    per_worker_attempts = [0] * num_workers   # Track each worker's attempt count
    have_progress_data = False   # Don't show "0.00 M/s" before first report

    # Import inside function to get the specific queue.Empty exception class.
    # Distinguishing Empty from OSError/EOFError is important for dead-worker detection.
    from queue import Empty as QueueEmpty

    try:
        # ── Parent monitoring loop ────────────────────────────────────────────
        while True:
            # STEP 1: Drain any progress messages from workers (non-blocking)
            if progress_q is not None:
                try:
                    while True:
                        # get_nowait() returns immediately with Empty if nothing there
                        wid, attempts, _now = progress_q.get_nowait()
                        per_worker_attempts[wid] = attempts   # Update worker's count
                        have_progress_data = True   # We now have real data to display
                except QueueEmpty:
                    pass   # No more progress messages — that's fine
                except (OSError, EOFError):
                    # Progress queue is broken (worker crashed, pipe closed).
                    # We can live without progress — the result queue still works.
                    progress_q = None

                # Call the user's progress callback if we have data
                if have_progress_data and progress_callback is not None:
                    total   = sum(per_worker_attempts)     # Sum across all workers
                    elapsed = time.monotonic() - t0        # Seconds elapsed
                    rate    = total / elapsed if elapsed > 0 else 0.0   # Hashes/sec
                    try:
                        progress_callback(total, elapsed, rate)
                    except Exception:
                        pass   # Never let a buggy callback kill the search

            # STEP 2: Check if any worker found the answer (wait up to 0.5s)
            try:
                # result_q.get() blocks for up to 0.5 seconds.
                # If a worker put a result, we get it immediately.
                # If 0.5s pass with nothing, raises QueueEmpty.
                _wid, suffix, _attempts = result_q.get(timeout=0.5)
                return suffix   # SUCCESS — return the winning suffix to the caller

            except QueueEmpty:
                # No result yet. Check if all workers are still alive.
                if all(not p.is_alive() for p in procs):
                    # All workers have exited without sending a result.
                    # BUT: mp.Queue.put() is asynchronous — the result might
                    # still be in the queue's internal buffer, not yet readable.
                    # Wait a bit and try draining the queue multiple times.
                    for _ in range(10):
                        try:
                            _wid, suffix, _attempts = result_q.get(timeout=0.05)
                            return suffix   # Found it in the buffer
                        except QueueEmpty:
                            continue   # Not yet — wait 50ms more and retry

                    # After 10 retries (500ms total), still nothing.
                    # Workers really did die without finding an answer.
                    raise RuntimeError(
                        "all POW workers died before finding a solution; "
                        "check stderr for worker crash messages"
                    )
                continue   # Workers still alive — keep waiting

            except (OSError, EOFError) as e:
                # The result queue itself is broken — this is fatal
                raise RuntimeError(f"POW result queue broken: {e}")

    finally:
        # ── Cleanup — always runs, even on exception ──────────────────────────
        # Signal all workers to stop (those still searching will see this and exit)
        found.set()

        # Wait for each worker to exit (give them 2 seconds, then force-kill)
        for p in procs:
            p.join(timeout=2.0)   # Wait up to 2s for graceful exit
            if p.is_alive():
                p.terminate()     # Send SIGTERM (Unix) or TerminateProcess (Windows)
                p.join(timeout=1.0)   # Wait for termination to complete

        # Drain and close queues so feeder threads can exit cleanly.
        # Without this, a worker that hasn't finished flushing its queue
        # write can produce "[ERROR] handle is closed" on stderr at GC time.
        for q in (result_q, progress_q):
            if q is None:
                continue
            try:
                while True:
                    q.get_nowait()   # Drain any remaining messages
            except Exception:
                pass
            try:
                q.close()         # Signal the feeder thread to stop
                q.join_thread()   # Wait for the feeder thread to finish
            except Exception:
                pass


# ── SINGLE-PROCESS SOLVER ─────────────────────────────────────────────────────

def _solve_single(authdata: bytes, difficulty: int) -> bytes:
    """
    Single-process in-line SHA-1 solver.

    Used for:
    1. Low difficulties (<=4) where multiprocessing overhead would dominate
    2. Self-test in exasol_client.py (simple, no subprocess setup)
    3. When num_workers=1 is explicitly requested

    This is the same algorithm as _worker() but runs directly in the current
    process — no forking, no queues, no events. Just the tight inner loop.
    """
    # Pre-compute SHA-1 state with authdata already "fed in"
    # Cloning this is much faster than calling hashlib.sha1(authdata + suffix)
    # from scratch every iteration.
    base_hasher = hashlib.sha1(authdata)

    # Pre-compute byte target for fast comparison (see _make_target docstring)
    full_zero, half_byte = _make_target(difficulty)
    full_zero_len = len(full_zero)

    # Reusable 16-byte buffer — no allocation per attempt
    buf = bytearray(16)
    mv = memoryview(buf)   # Zero-copy view into buf

    # Hoist into locals for CPython speed (LOAD_FAST vs LOAD_ATTR)
    base_copy = base_hasher.copy
    encode    = _encode_counter

    counter = 0   # Start from the beginning (no worker ID offset needed)

    # Simple infinite loop — keep trying until we find the answer
    while True:
        n = encode(counter, buf)   # Write counter as suffix into buf
        h = base_copy()            # Clone SHA-1 state (has authdata pre-loaded)
        h.update(mv[:n])           # Hash just the suffix bytes
        d = h.digest()             # Get raw 20-byte digest

        # Check for required leading zero bytes
        if d[:full_zero_len] == full_zero:
            # All full zero bytes match. Check the half-byte if needed.
            if half_byte == 0 or (d[full_zero_len] >> 4) == 0:
                return bytes(buf[:n])   # Return a copy of the winning suffix

        counter += 1   # Try the next counter value
