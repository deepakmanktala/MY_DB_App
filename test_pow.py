"""
================================================================================
FILE: test_pow.py
PURPOSE: Tests and performance benchmark for pow_solver.py.

WHAT IS TESTED HERE?
---------------------
This file tests the SHA-1 brute-force solver (pow_solver.py) from three angles:

  1. CORRECTNESS — Does the solver produce valid answers?
     - Alphabet check: does it contain only safe characters?
     - Counter encoding: are all values unique (no collisions)?
     - Target construction: does _make_target() produce the right byte patterns?
     - Single-core solve: does it find valid suffixes at difficulties 1-5?
     - Parallel solve: does multi-process work correctly?

  2. PERFORMANCE — How fast is it on THIS machine?
     - Measures hashes/second on one CPU core
     - Extrapolates to estimate difficulty-9 wall-clock time
     - Helps you decide whether to run on a faster machine

  3. REAL-WORLD SAMPLE (optional --d6 flag):
     - Actually solves a difficulty-6 POW with all cores
     - Gives an accurate projection for difficulty-9 from real data

HOW TO RUN:
-----------
    python test_pow.py           # correctness tests + 2-second benchmark
    python test_pow.py --bench   # correctness tests + 10-second benchmark
    python test_pow.py --d6      # also solve a real difficulty-6 (takes ~5-30s)

SAMPLE OUTPUT:
--------------
    === correctness ===
    [ok] alphabet: 92 chars, none of \n \r \t space
    [ok] counter encoding unique across 50,000 values
    [ok] difficulty=4: 118.9ms  suffix=<|*   digest=0000a330b756...
    [ok] parallel solver d=5 -> digest=00000a5a9174...

    === single-core throughput ===
    single-core:      867,618 hashes/sec
    22 cores:      19,087,592 hashes/sec (ideal linear)
    projected difficulty-9 wall-clock: 60.0 min (1.00 hr)
================================================================================
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from __future__ import annotations   # Allow "type | None" syntax on Python 3.9

import argparse   # For parsing --bench and --d6 command-line flags
import hashlib    # SHA-1 for verifying solver results
import os         # os.cpu_count() — number of CPU cores available
import time       # time.monotonic() — high-resolution clock for benchmarking

# Import the internals of pow_solver.py that we want to test directly.
# Leading underscore (_) means these are "private" but we import them here
# for testing purposes — that's acceptable in test files.
from pow_solver import (
    _ALPHABET,        # The 92-character safe suffix alphabet
    _BASE,            # The base number for counter encoding (= 92)
    _encode_counter,  # Function that converts an integer counter to suffix bytes
    _make_target,     # Function that converts difficulty to raw byte comparison target
    _solve_single,    # Single-process solver (no multiprocessing overhead)
    solve_pow,        # Full multi-process solver (main entry point)
)


# ── TEST 1: Alphabet safety ────────────────────────────────────────────────────

def test_alphabet_excludes_forbidden() -> None:
    """
    Verify that the suffix alphabet doesn't contain protocol-breaking characters.

    The Exasol protocol is line-based, using specific characters as delimiters:
      - \n  (newline)     → ends every protocol line
      - \r  (carriage return) → Windows line ending
      - \t  (tab)         → could be parsed as whitespace separator
      - ' ' (space)       → separates command tokens

    If ANY of these appeared in a suffix, the server's line parser would
    misinterpret it. For example, if suffix contained \n, the server would
    think the line ended there and get confused by the remaining bytes.

    This test confirms the _ALPHABET byte string contains none of those 4.
    It also verifies the total size is exactly 92 characters (our expected base).
    """
    # Build a set of the 4 forbidden byte values
    forbidden = {ord("\n"), ord("\r"), ord("\t"), ord(" ")}

    # set(_ALPHABET) converts the bytes to a set of integer code points
    # set intersection (&) gives characters that appear in BOTH sets
    # If the intersection is empty, no forbidden chars are in the alphabet
    assert not (set(_ALPHABET) & forbidden), "alphabet contains forbidden chars"

    # _BASE must equal len(_ALPHABET) — both should be 92
    assert _BASE == len(_ALPHABET) == 92

    print(f"[ok] alphabet: {_BASE} chars, none of \\n \\r \\t space")


# ── TEST 2: Counter encoding uniqueness ───────────────────────────────────────

def test_counter_encoding_unique() -> None:
    """
    Verify that no two counter values produce the same suffix bytes.

    The solver uses a counter (0, 1, 2, 3, ...) encoded in base-92 as the
    suffix string. For this to work correctly as a search space, every counter
    value must map to a DIFFERENT byte string — otherwise we'd try the same
    suffix twice and miss other parts of the space.

    This test encodes 50,000 consecutive counter values and checks for
    duplicates. 50,000 is enough to verify the encoding works across multiple
    "digit" lengths (1-digit = 92 values, 2-digit = 92^2 = 8464 more, etc.).

    A collision would indicate a bug in _encode_counter() such as incorrect
    base conversion or buffer overwrite.
    """
    seen: set[bytes] = set()   # All suffix bytes seen so far
    buf = bytearray(16)         # Reusable 16-byte output buffer

    for n in range(50_000):    # Test the first 50,000 counter values
        # Encode counter n into buf, returns number of bytes written
        ln = _encode_counter(n, buf)
        # Copy just the written bytes (not the full 16-byte buffer)
        s = bytes(buf[:ln])
        # Check for collision — if s is already in seen, we have a bug
        assert s not in seen, f"collision at n={n}: {s!r}"
        seen.add(s)   # Record this suffix as seen

    print(f"[ok] counter encoding unique across {len(seen):,} values")


# ── TEST 3: Target construction ────────────────────────────────────────────────

def test_target_construction() -> None:
    """
    Verify _make_target() produces the correct byte patterns for each difficulty.

    BACKGROUND: Why bytes instead of hex strings?
    -----------------------------------------------
    SHA-1 digest() returns raw bytes. hexdigest() converts to a 40-char hex string.
    Checking hexdigest().startswith("0"*d) requires converting 20 bytes to 40 chars
    on every attempt — 68 BILLION hex conversions at difficulty 9.

    Instead, _make_target() precomputes what the raw bytes should look like:
      - difficulty=6 → need 6 hex zeros = 3 zero bytes
      - difficulty=7 → need 7 hex zeros = 3 zero bytes + top 4 bits of next byte = 0

    The "half_byte" flag handles odd difficulties:
      - If difficulty is even, we check whole bytes (half=0)
      - If difficulty is odd,  we also check the high nibble of the next byte (half=1)

    Test cases (difficulty → expected full_zero_bytes, half_byte_flag):
        d=0 → b"",           0   (nothing to check — always passes)
        d=1 → b"",           1   (check high nibble of first byte)
        d=2 → b"\x00",       0   (one full zero byte)
        d=3 → b"\x00",       1   (one full byte + high nibble of next)
        d=8 → b"\x00\x00\x00\x00", 0  (four full zero bytes)
        d=9 → b"\x00\x00\x00\x00", 1  (four bytes + high nibble of 5th)
    """
    # (difficulty, expected_full_zero_bytes, expected_half_byte_flag)
    cases = [
        (0, b"",                 0),   # No zeros required — always true
        (1, b"",                 1),   # Just the high nibble of byte 0
        (2, b"\x00",             0),   # One full zero byte
        (3, b"\x00",             1),   # One full byte + high nibble
        (8, b"\x00\x00\x00\x00",0),   # Four full zero bytes
        (9, b"\x00\x00\x00\x00",1),   # Four bytes + high nibble of fifth
    ]

    for d, full, half in cases:
        f, h = _make_target(d)   # Call the function under test
        # Assert both return values match expected
        assert (f, h) == (full, half), f"d={d}: got {(f, h)}"

    print("[ok] target construction matches difficulty -> (bytes, half)")


# ── TEST 4: Single-core solver correctness ────────────────────────────────────

def test_solver_low_difficulty() -> None:
    """
    Verify _solve_single() finds correct answers at difficulties 1 through 5.

    For each difficulty:
      1. Call _solve_single() to get a suffix
      2. Compute SHA1(authdata + suffix) independently with hashlib
      3. Verify the digest starts with the required number of '0' hex chars
      4. Verify the suffix contains none of the 4 forbidden characters
      5. Print timing so we can see how long each difficulty takes

    Difficulty 5 is the hardest tested here (16^5 = 1 million expected hashes).
    At ~1M hashes/sec, this takes about 1 second in the worst case.
    We skip difficulty 6+ here because they'd take too long in a unit test.
    """
    auth = b"test-authdata-12345"   # Fixed authdata (any bytes work for testing)

    for difficulty in (1, 2, 3, 4, 5):
        t0 = time.monotonic()                  # Start timing
        suffix = _solve_single(auth, difficulty)  # Run the solver
        elapsed = time.monotonic() - t0        # Stop timing

        # Independently verify: compute SHA1 from scratch using standard hashlib
        digest = hashlib.sha1(auth + suffix).hexdigest()

        # Check that the digest starts with exactly 'difficulty' zero hex chars
        assert digest.startswith("0" * difficulty), (
            f"d={difficulty}: suffix={suffix!r} digest={digest}"
        )

        # Check that no forbidden character snuck into the suffix
        for forbidden in (b"\n", b"\r", b"\t", b" "):
            assert forbidden not in suffix

        # Print timing and result for human inspection
        print(f"[ok] difficulty={difficulty}: {elapsed*1000:>7.1f}ms  "
              f"suffix={suffix.decode():<8s}  digest={digest[:12]}...")


# ── TEST 5: Parallel multi-process solver ─────────────────────────────────────

def test_parallel_solver() -> None:
    """
    Verify solve_pow() (the multi-process version) works correctly.

    This tests the full parallel path:
      - Spawns one process per CPU core
      - Workers search disjoint slices of the counter space
      - First worker to find a hit signals all others to stop
      - Parent receives the suffix via a Queue

    We test at difficulty=5 to get a meaningful parallel workload
    without waiting too long. The result is verified the same way as
    the single-core test: SHA1(auth+suffix).hexdigest().startswith("00000")
    """
    auth = b"parallel-auth"   # Fixed test authdata

    # os.cpu_count() returns the number of logical CPU cores (may include hyperthreading)
    suffix = solve_pow(auth, 5, num_workers=os.cpu_count())

    # Independently verify the answer
    digest = hashlib.sha1(auth + suffix).hexdigest()
    assert digest.startswith("00000"), digest   # Must start with 5 zeros

    print(f"[ok] parallel solver d=5 -> digest={digest[:12]}...")


# ── BENCHMARK ─────────────────────────────────────────────────────────────────

def benchmark_single_core(seconds: float) -> float:
    """
    Measure raw hashes-per-second on one CPU core.

    This runs the EXACT same inner loop as the production solver,
    so the measurement reflects real-world throughput.

    WHY WE USE difficulty=40 FOR BENCHMARKING:
    -------------------------------------------
    We set full_zero = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    (20 zero bytes = difficulty 40 = impossible to satisfy).
    This means the loop NEVER early-exits — we always run exactly `seconds`
    of hashing. If we used a real difficulty, the loop might exit early
    after getting lucky, giving an inaccurate rate.

    WHY INNER BATCHES OF 10,000:
    -----------------------------
    time.monotonic() has overhead (syscall). Checking it every iteration
    would itself skew the measurement. We check every 10,000 iterations
    to amortize the overhead.

    Returns:
        hashes_per_second (float)
    """
    auth = b"benchmark-authdata-of-realistic-length-0123456789"  # Realistic authdata length

    # Pre-compute SHA-1 state with authdata — same as the real solver
    base = hashlib.sha1(auth)
    base_copy = base.copy   # Hoist into local for CPython speed

    encode = _encode_counter   # Local reference for speed

    # Use difficulty=40 so the target is NEVER satisfied (pure throughput test)
    full_zero, _ = _make_target(40)   # b"\x00" * 20 (impossible)
    full_zero_len = len(full_zero)    # 20 bytes

    buf = bytearray(16)         # Reusable buffer — no allocation per attempt
    mv = memoryview(buf)        # Zero-copy view for update()

    counter = 0    # Counter starts at 0 — same as single-core solver
    count = 0      # Total hashes computed so far

    t0 = time.monotonic()
    end = t0 + seconds    # Keep hashing until this time

    while time.monotonic() < end:
        # Inner batch of 10,000 — don't check the clock on every iteration
        for _ in range(10_000):
            n = encode(counter, buf)   # Encode counter → suffix bytes
            h = base_copy()            # Clone pre-computed SHA-1 state
            h.update(mv[:n])           # Hash just the suffix (authdata already in state)
            d = h.digest()             # Get raw 20-byte digest
            # Check (will always be False since target is impossible)
            if d[:full_zero_len] == full_zero:
                pass
            counter += 1   # Next counter value

        count += 10_000   # We just did 10,000 more hashes

    # Calculate actual elapsed time (slightly more than `seconds` due to batch rounding)
    actual_elapsed = time.monotonic() - t0

    return count / actual_elapsed   # Hashes per second


# ── OPTIONAL: Real difficulty-6 multi-core sample ─────────────────────────────

def test_d6_real(num_workers: int | None = None) -> None:
    """
    Solve an actual difficulty-6 POW with all CPU cores and project d=9 ETA.

    WHY THIS IS USEFUL:
    --------------------
    The single-core benchmark gives a rate measurement, but it's theoretical.
    Actual parallel performance depends on:
      - Inter-process overhead (Queue, Event, Process startup)
      - How well processes stay busy (no lock contention in Python's multiprocessing)
      - OS scheduler behavior

    By solving a REAL difficulty-6 POW (16^6 ≈ 16 million expected hashes),
    we get an actual measurement of aggregate throughput across all cores.
    The difficulty-9 projection from this is more accurate than from the
    single-core benchmark times num_workers.

    How the projection works:
      - difficulty-6 takes on average 16^6 hashes
      - difficulty-9 takes on average 16^9 hashes
      - ratio = 16^9 / 16^6 = 16^3 = 4096
      - If d=6 took T seconds, d=9 will take ~T * 4096 seconds
      - But we measure the actual RATE from d=6 and use that directly
    """
    auth = b"real-d6-test-authdata"   # Fixed authdata for this test
    cores = num_workers or os.cpu_count() or 1   # Use all available cores

    print(f"[d6] solving difficulty 6 on {cores} cores (expected ~16M hashes)...")

    t0 = time.monotonic()
    suffix = solve_pow(auth, 6, num_workers=cores)   # Actually solve d=6
    elapsed = time.monotonic() - t0

    # Verify the answer is correct
    digest = hashlib.sha1(auth + suffix).hexdigest()
    assert digest.startswith("000000"), digest   # Must start with 6 zeros

    print(f"[d6] solved in {elapsed:.2f}s -> {digest[:12]}...")

    # Calculate actual aggregate rate from the measured time.
    # We assume we tried approximately 16^6 hashes (the expected value).
    # Note: actual count may vary due to luck, but this is a good estimate.
    rate = (16**6) / elapsed   # Hashes per second across all cores

    # Project how long difficulty-9 would take at the same rate
    eta_d9 = (16**9) / rate    # Expected seconds for d=9

    print(f"[d6] effective aggregate rate: {rate/1e6:.2f} M hashes/sec")
    print(f"[d6] -> projected difficulty-9 wall-clock: "
          f"{eta_d9/60:.1f} min ({eta_d9/3600:.2f} hr)")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Parse command-line flags, run correctness tests, then benchmark.

    Flags:
        --bench   Run a 10-second benchmark instead of 2-second (more accurate)
        --d6      Also solve a real difficulty-6 POW for a parallel throughput sample
    """
    # Set up argument parser
    p = argparse.ArgumentParser()
    p.add_argument("--bench", action="store_true",
                   help="Longer 10-second single-core benchmark (more accurate)")
    p.add_argument("--d6", action="store_true",
                   help="Also solve a real difficulty-6 POW with all cores")
    args = p.parse_args()

    # ── Correctness section ───────────────────────────────────────────────────
    print("=== correctness ===")
    test_alphabet_excludes_forbidden()   # Alphabet has no forbidden chars
    test_counter_encoding_unique()       # 50,000 unique encodings
    test_target_construction()           # Byte target matches expected for each difficulty
    test_solver_low_difficulty()         # Single-core finds valid answers at d=1..5
    test_parallel_solver()               # Multi-process finds valid answer at d=5

    # ── Benchmark section ─────────────────────────────────────────────────────
    print("\n=== single-core throughput ===")

    # Use 10 seconds if --bench, otherwise 2 seconds (faster for routine checks)
    duration = 10.0 if args.bench else 2.0
    rate = benchmark_single_core(duration)   # Measure actual hashes/sec

    cores = os.cpu_count() or 1   # Number of logical CPU cores

    # Ideal linear speedup: if one core does R hashes/sec, N cores do N*R (assuming no overhead)
    # This is an optimistic upper bound — real speedup is slightly less due to process startup
    aggregate = rate * cores

    # Calculate expected wall-clock time for difficulty-9
    # 16^9 = 68,719,476,736 ≈ 68.7 billion expected hashes
    eta_d9 = (16**9) / aggregate

    # Print the results in a human-readable format
    print(f"single-core: {rate:>12,.0f} hashes/sec")
    print(f"{cores} cores:    {aggregate:>12,.0f} hashes/sec (ideal linear)")
    print(f"projected difficulty-9 wall-clock: "
          f"{eta_d9/60:.1f} min ({eta_d9/3600:.2f} hr)")

    # ── Optional real-world parallel sample ───────────────────────────────────
    if args.d6:
        print("\n=== real difficulty-6 multi-core sample ===")
        test_d6_real()   # Actually solve d=6 with all cores and project d=9

    print("\nAll tests passed.")


# ── SCRIPT ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()   # Run all tests — Python exits 0 on success, 1 on assertion failure
