# Exasol Challenge — Final Solution

A small, focused Python solution for the Exasol POW challenge. Connects
over TLS, solves the SHA-1 proof-of-work, answers the personal-data
handshake, and submits — all in ~500 lines, dependency-free (stdlib
only, Python 3.10+).

---

## What's in this folder

| File                    | Purpose                                                           |
|-------------------------|-------------------------------------------------------------------|
| `exasol_client.py`      | Main entry point. TLS, protocol handler, command dispatcher.      |
| `pow_solver.py`         | Multi-process SHA-1 brute-force solver. The hot path.             |
| `profile.example.json`  | Template for personal answers. Copy to `profile.json` and edit.   |
| `challenge.pem`         | Your TLS credentials (private key + client cert + CA), bundled.   |
| `README.md`             | This file.                                                        |
| **Tests:**              |                                                                   |
| `test_pow.py`           | Solver correctness tests + per-machine throughput benchmark.      |
| `smoke_test.py`         | Protocol/edge-case tests (no network).                            |
| `system_test.py`        | End-to-end with a mock TLS server (real client subprocess).       |
| `failure_test.py`       | 7 server-misbehavior scenarios (hang, ERROR, oversized line).     |
| `aggressive_test.py`    | TCP coalescing, RST, partial line, high-bit authdata.             |
| `regression.py`         | Runs all 5 test suites and prints a summary.                      |

---

## Quick start (3 commands)

```bash
# 1. Sanity check the solver on this machine; see your hash rate and
#    the projected difficulty-9 wall-clock time.
python test_pow.py

# 2. Edit your personal answers.
cp profile.example.json profile.json
$EDITOR profile.json

# 3. Run for real.
python exasol_client.py --pem challenge.pem --profile profile.json
```

Want to verify everything is healthy on your machine before running for
real? `python regression.py` runs all 5 test suites (~40 seconds): solver
unit tests, protocol tests, full end-to-end with a mock TLS server,
seven server-misbehavior scenarios, and four aggressive
network-edge-case tests.

The client will try the six known server ports in order, solve
whatever POW the server gives it, answer the personal-data questions,
and report success when the server sends `END`.

---

## Before you run

**1. Edit `profile.json`.** The example values are placeholders and your
submission will be tied to your TLS cert, so they need to be your real
details.

  - `NAME`: first and last name, separated by a single space.
  - `MAILS`: list of email addresses, at least one. Add as many as you want.
  - `SKYPE`: your Skype handle, or `"N/A"`.
  - `BIRTHDATE`: `dd.mm.yyyy` format.
  - `COUNTRY`: must be a name from
    https://www.countries-of-the-world.com/all-countries.html
    (e.g. `"India"`, not `"IN"` or `"Republic of India"`).
  - `ADDRESS`: list of address lines (typically 2: street, then city+PIN).

**2. Cert expiry.** `challenge.pem` is valid until **2026-05-22**.
Don't sit on it.

**3. Run `python test_pow.py` first.** It prints your machine's hash
rate and a difficulty-9 wall-clock estimate. If the estimate is way
over 2 hours, run on a faster box or accept that you may need a few
attempts (each POW is independent, so retries are fine).

---

## Configuration & flags

```
python exasol_client.py [options]

Required:
  --profile PATH       JSON file with your personal answers.

Credentials (use --pem alone, OR all of --cert/--key/--ca):
  --pem PATH           Combined PEM. Convenient default.
  --cert PATH          Client certificate (overrides --pem for cert).
  --key PATH           Private key (overrides --pem for key).
  --ca PATH            CA cert for server verification (overrides --pem for CA).
  --insecure           Skip server verification. Not recommended.

Targeting:
  --host HOST          Default: 18.202.148.130
  --port N             Default: try 3336, 8083, 8446, 49155, 3481, 65532 in order.

Other:
  --no-selftest        Skip the 1-second solver self-test before connecting.
```

### Tuning the solver

One env var controls the inner loop:

```bash
# Larger batch = lower per-attempt overhead, slower shutdown when a
# worker hits. Default 8192 is a good balance for most machines.
EXASOL_BATCH=16384 python exasol_client.py --pem challenge.pem --profile profile.json
```

If you want to leave cores free for other work, edit `solve_pow(..., num_workers=N)`
in `exasol_client.py` (the POW handler in `handle_command`).

---

## How it works

### The protocol

```
server → HELO                                ; client → "TOAKUEI"
server → POW <authdata> <difficulty>         ; client → suffix s such that
                                               SHA1(authdata + s) starts
                                               with <difficulty> hex zeros
server → NAME <arg1>                         ; client → "<sha1(authdata + arg1)> <value>"
server → MAILNUM, MAIL1, MAIL2, …
server → SKYPE, BIRTHDATE, COUNTRY,
         ADDRNUM, ADDRLINE1, ADDRLINE2, …
server → END                                 ; client → "OK"
                                               ⇒ submission recorded.
server → ERROR <message>                     ; submission rejected, no data stored.
```

Server timeouts: **POW = 2 hours**, every other command = **6 seconds**.

### Why the solver is fast

The expected work for difficulty `d` is **`16^d` SHA-1 calls**. There
is no algorithmic shortcut — the problem is brute force by design. So
all the wins are constant-factor:

1. **Pre-init the hasher with `authdata`, then `.copy()` per attempt.**
   `hashlib`'s clone is a memcpy of internal state. Each attempt only
   hashes the few bytes of suffix instead of `authdata + suffix`.

2. **Compare on raw digest bytes, not hex.** Skips the hex conversion
   entirely. We pre-build the target byte pattern once.

3. **`memoryview` into a reused `bytearray`.** Avoids allocating a
   fresh `bytes` object per attempt. ~10% on x86, more on ARM.

4. **Counter-based suffix generation.** SHA-1 is a uniform random
   oracle; the input distribution doesn't matter as long as inputs are
   distinct. A counter is faster than any PRNG, has zero state, and
   guarantees no collisions between workers.

5. **One process per CPU core.** `multiprocessing` with a shared
   `Event`. First worker to find a hit sets the flag; the others see it
   at the next batch boundary and exit. Linear speedup with cores.

### About "O(1) time / O(1) space"

Time **cannot** be O(1) — the work is fundamentally `O(16^d)` and that's
the whole design of the problem. What we achieve:

- **O(1) space per worker** ✓ (constant-size hasher state + 16-byte buffer)
- **Constant-factor work near the floor** for stock-CPython hashlib ✓
- **Linear speedup with cores** ✓

For 10–100× more throughput, swap `hashlib.sha1` for a SIMD-batched
implementation (numpy + a SIMD SHA-1 lib) or a GPU kernel (Numba CUDA,
or `hashcat` invoked as a subprocess). The CPU path here is
intentionally dependency-free.

### Difficulty-9 wall-clock estimates

Multiply `16^9 = 68,719,476,736` by your aggregate hash rate:

| Hardware                       | Aggregate hashes/sec | ETA d=9      |
|--------------------------------|----------------------|--------------|
| Raspberry Pi 4 (4 cores)       | ~1.0 M/s             | ~19 hours    |
| Older laptop (4 cores)         | ~3–5 M/s             | ~4–7 hours   |
| Modern laptop (4 fast cores)   | ~5–8 M/s             | ~2–4 hours   |
| Modern desktop (8+ fast cores) | ~12–20 M/s           | ~1–2 hours   |
| Mid-range GPU (with hashcat)   | ~500 M – 1 G/s       | ~1–2 minutes |

Run `python test_pow.py --d6` for an empirical sample on your specific
machine — it solves a real difficulty-6 POW and projects the d=9 ETA
from the actual measured rate.

---

## Operational notes

- **Hostname mismatch is expected.** Server is at IP `18.202.148.130`
  but the cert CN is `exatest.dynu.net`. The client sets
  `check_hostname=False`. Server-cert chain validation (enabled by
  default when `--pem` or `--ca` is given) is the meaningful check —
  it proves we're talking to a server holding a key signed by Exasol's
  CA.

- **Errors are not retried.** If the server sends `ERROR`, retrying on
  another port submits the same bad payload again. The client treats
  protocol errors as fatal and exits non-zero. Network errors (TCP
  reset, TLS handshake failure) ARE retried on the next port.

- **Submissions are atomic.** Data is only recorded if you complete the
  full handshake through `END`. A connection drop mid-session means
  nothing was stored.

- **The session is one-shot per cert.** The cert authorises you to
  submit; once you've completed an `END`, you've completed your
  submission. If the first attempt fails, you can simply re-run — each
  new POW is independent.

- **Profile validation runs up front.** A typo in `profile.json` is
  caught before connecting, not after a 2-hour POW. Forbidden chars
  (newline, CR) in any value are rejected because they'd break protocol
  framing.

- **Self-test runs in <1 second.** A botched install (broken hashlib,
  wrong Python version) fails before the network call. Disable with
  `--no-selftest` if you have a reason.

---

## Troubleshooting

**`error: profile missing required keys: ['BIRTHDATE']`**
Your `profile.json` doesn't have all required keys. Compare against
`profile.example.json`.

**`server ERROR: invalid country`**
`COUNTRY` must match a name from the official list at
https://www.countries-of-the-world.com/all-countries.html exactly.

**`connect failed: ConnectionRefusedError`**
The port you're trying isn't listening. The default config tries all
six known ports in order; let it cycle through.

**`SSL: CERTIFICATE_VERIFY_FAILED`**
Either the server cert chain has changed (Exasol rotated the CA), or
you've passed a wrong `--ca` path. As a workaround use `--insecure` —
client auth still works; you just don't verify the server's identity.

**Solver looks stuck.** Check the per-second progress line. If
`hashes/sec` is tiny (<100k/core) on a normal machine, something is
very wrong — try `python test_pow.py` standalone to see whether it's
the multiprocessing layer or the hash loop itself.

---

## Files at a glance

```
final/
├── README.md              ← you are here
├── challenge.pem          ← TLS credentials (key + cert + CA)
├── exasol_client.py       ← main entry point
├── pow_solver.py          ← parallel SHA-1 brute force
├── profile.example.json   ← template for personal answers
├── test_pow.py            ← solver tests + benchmark
├── smoke_test.py          ← protocol / profile / edge-case tests
├── system_test.py         ← end-to-end with mock TLS server
├── failure_test.py        ← server-misbehavior tests
├── aggressive_test.py     ← network-edge-case tests
└── regression.py          ← runs all 5 suites with summary
```

Total: ~2,300 lines of Python, zero third-party dependencies.

---

## Tested behavior

The full regression suite covers:

**Solver correctness (`test_pow.py`)** — alphabet excludes forbidden
chars; counter encoding is unique; difficulty 1–5 produces valid
suffixes; multi-process path produces valid suffixes; per-machine
throughput benchmark with d=9 ETA projection.

**Protocol unit tests (`smoke_test.py`)** — full handshake with checksum
verification; ERROR raises ProtocolError; profile validation rejects
14 distinct bad shapes (missing keys, wrong types, empty/whitespace
strings, control characters, single-word names); unknown commands
rejected; blank lines rejected; commands before POW rejected;
malformed POW lines rejected (5 variants); whitespace-tolerant
tokeniser; solver input validation; difficulty 0 edge case.

**End-to-end system test (`system_test.py`)** — full session against a
real TLS server on localhost: HELO, POW solve, all 10 personal-data
responses delivered with correct SHA-1 prefixes (in random order to
prove order-independence), END acknowledged.

**Failure modes (`failure_test.py`)** — 7 scenarios: server hangs up
immediately; server sends ERROR (fatal, no retry); server sends 100 KB
without newline (memory-bomb attempt → bounded); server hangs after
HELO (caught at 30s read timeout); server violates protocol order;
server sends malformed POW; happy-path low-difficulty session.

**Aggressive cases (`aggressive_test.py`)** — partial line then close;
**TCP-coalesced HELO+POW in one packet** (validates buffered line
reader); high-bit bytes in authdata (validates bytes-correctness of
SHA-1 input); TCP RST after POW (validates clean failure on truncated
connection).

**Beyond regression** — also manually validated: mp.Queue feeder-thread
race in dead-worker detection; KeyboardInterrupt during solve
propagates cleanly; SIGTERM doesn't leak worker processes; spawn
context (Windows behaviour) works; FD usage stable across 10
sequential solves; `--ca` correctly verifies (and rejects wrong CA);
corrupted PEM produces clean SSL error; `num_workers=0/-1/non-int`
rejected; `EXASOL_BATCH=garbage` falls back to default with warning.

---

## Review pass — issues found and fixed

This solution went through **two adversarial review passes** plus
**system testing** before being declared final. The bugs caught and
fixed:

### Second review pass (after system tests added)

- **mp.Queue feeder-thread race in dead-worker detection.** The parent's
  `result_q.get_nowait()` could miss an in-flight result because
  `mp.Queue.put()` writes to a feeder thread that flushes asynchronously.
  Fixed: the post-death drain now retries 10× with 50ms timeouts,
  giving the feeder up to 500ms to complete. Couldn't reproduce the
  race in 700 stress runs but the fix is provably correct.
- **Profile validation accepted non-string types.** `NAME: 123`,
  `NAME: None`, `NAME: ""`, `NAME: "OnlyOne"`, and `MAILS: [123]` all
  passed validation. Fixed with strict `isinstance(str)` + non-empty +
  first+last name checks. Now rejects 14 distinct bad-profile shapes.
- **Tab and other control chars in profile values.** A tab character
  in an address or name was silently allowed. The protocol is
  whitespace-oriented; embedded control chars could cause server-side
  parser ambiguity. Fixed: reject any ASCII control character (0x00-0x1F
  + DEL); legitimate Unicode (umlauts, emoji, CJK) still allowed.
- **Progress callback state leaked across POW calls.** Function
  attribute `_last_print` persisted across multiple `solve_pow`
  invocations, suppressing the first progress line on retries. Fixed
  with a closure factory `_make_line_progress()`.
- **Defensive forbidden-byte check on POW suffix.** Belt-and-braces:
  re-verify suffix contains no `\n \r \t space` after solver returns
  but before sending. The solver's alphabet excludes them by
  construction, but a hypothetical solver bug can no longer desync us.
- **`num_workers` validation.** `num_workers=0/-1/non-int` produced a
  confusing "all workers died" error. Fixed with explicit
  `ValueError`.
- **Queue cleanup on shutdown.** Result and progress queues are now
  drained, closed, and `join_thread()`'d to prevent feeder threads
  emitting "[ERROR] handle is closed" on stderr at GC.
- **Regression script timeout handling.** `subprocess.TimeoutExpired`
  now produces a structured TIMEOUT result instead of crashing.

### First review pass

**Solver (`pow_solver.py`)**

- **All-workers-dead detection.** The parent's `result_q.get(timeout=0.5)`
  used to swallow every exception and loop forever. Now it
  distinguishes `queue.Empty` (keep waiting) from worker death
  (`is_alive()` check across all procs → raise `RuntimeError`). Without
  this fix, a worker crash hung the parent indefinitely.
- **Worker crashes are visible.** Workers now log unexpected exceptions
  to stderr before exiting, instead of dying silently. Combined with
  the parent detection above, you get a clear error message instead of
  a hang.
- **Race-safe hit reporting.** Workers now `put()` the result *then*
  `set()` the found-flag in a `try/finally`, ensuring the result is
  always queued before any sibling sees the flag.
- **Input validation.** `solve_pow()` now rejects non-bytes authdata,
  non-int difficulty, negative difficulty, and difficulty > 40 (SHA-1
  max). Previously these would crash mid-loop with confusing errors.
- **Robust env var parsing.** An invalid `EXASOL_BATCH` value now warns
  and falls back to the default instead of crashing at import time.
- **Cleaner shutdown.** `terminate()`'d processes are now `join()`'d
  again to avoid zombies on slow systems.

**Client (`exasol_client.py`)**

- **Read timeouts now correct.** Previously every read used a 2-hour
  timeout (POW budget). The actual server timeout for non-POW commands
  is 6 seconds; we now use a 30-second timeout for all reads (the
  2-hour budget is consumed locally during `solve_pow()`, not while
  waiting on a socket). This means a stalled server is detected in 30
  seconds instead of 2 hours.
- **Whitespace-tolerant tokeniser.** `line.split()` (any whitespace)
  instead of `line.split(b" ")` (single space only). Defends against
  future protocol revisions using tab or multiple spaces.
- **Bounded line reads.** `LineConn.read_line()` now caps a single line
  at 64 KB. Without this, a malicious or malformed peer streaming
  un-newlined data could exhaust memory.
- **Clean TLS shutdown.** `LineConn.close()` now does
  `shutdown(SHUT_RDWR)` before `close()` for a graceful TLS goodbye.
- **TTY-aware progress.** Progress prints to a re-used line (`\r`) when
  stdout is a terminal, but switches to one full line every 30 s when
  redirected to a file. Prevents log files from filling up with control
  characters.
- **`KeyboardInterrupt` handled.** Ctrl-C during a long POW now exits
  cleanly with code 130 (the conventional SIGINT exit) instead of an
  ugly traceback.
- **Conflicting-flag warning.** `--insecure --ca x.pem` now warns that
  `--ca` is being ignored, instead of silently dropping it.
- **Unexpected exceptions are caught at top level.** Unknown errors
  during a session no longer kill the process — they're treated as
  transient so a different port can be tried.
- **Profile loader catches more.** Now also handles
  `UnicodeDecodeError` (file in wrong encoding) in addition to
  `OSError` / `JSONDecodeError` / `ValueError`.
- **POW range checks at the protocol layer.** A server-sent difficulty
  outside `[0, 40]` is rejected as a `ProtocolError` immediately,
  rather than passed to the solver where it would error mid-search.
- **POW solver-failure is transient.** If the solver itself fails
  (e.g. all workers died), the session raises `TransientError` so the
  next port gets tried.
- **POW progress only fires after first data.** No more "0.00 M/s"
  prints during the first second before any worker reports.
- **Solver verification cleanup.** Suffix decoding for log output uses
  `errors='backslashreplace'` so non-printable bytes (shouldn't happen,
  but) display safely.

**Tests (`smoke_test.py`)**

Expanded from 3 → 10 test functions covering:

- Full handshake round-trip with checksum verification
- Server `ERROR` handling
- Profile validation (missing keys, embedded newlines)
- Unknown command rejection
- Blank/empty line rejection
- Command-before-POW rejection
- Malformed POW (missing fields, non-integer, out-of-range)
- Multi-space and tab tokenising
- Solver input validation (4 bad-input cases)
- Difficulty 0 edge case

All 10 tests pass; the suite runs in ~1 second.

---
