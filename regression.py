"""
================================================================================
FILE: regression.py
PURPOSE: The "master test runner" — runs ALL five test suites in one command.

WHAT IS A REGRESSION TEST?
----------------------------
A regression test is a test you run after every change to make sure you haven't
accidentally BROKEN something that was working before. The word "regression"
means going backwards — a regression failure means the code got WORSE.

WHAT THIS FILE DOES:
---------------------
It runs each of the five test script files as a separate subprocess (a child
Python process), collects their exit codes and output, and prints a summary
table at the end showing PASS or FAIL for each.

WHY SUBPROCESSES (not just function calls)?
--------------------------------------------
Each test file is a standalone script. Running them as subprocesses:
  1. Isolates failures — a crash in one suite doesn't kill the runner
  2. Captures ALL output (stdout + stderr) cleanly
  3. Applies a time limit — if a test hangs, we can detect it
  4. Mimics how CI/CD pipelines (like GitHub Actions) would run them

HOW TO RUN:
-----------
    python regression.py

EXPECTED OUTPUT (all passing):
    === Summary ===
      [PASS] Solver tests + benchmark        3.0s
      [PASS] Protocol unit tests             0.1s
      [PASS] End-to-end system test          0.8s
      [PASS] Failure-mode tests             34.1s
      [PASS] Aggressive failure tests        3.1s

    All regression tests passed.

EXIT CODE:
    0 = all suites passed
    1 = at least one suite failed
================================================================================
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from __future__ import annotations   # Allow "type | None" union syntax on Python 3.9

import subprocess   # Lets us launch each test file as a separate child process
import sys          # For sys.executable (path to current Python) and sys.exit()
import time         # For time.monotonic() — measures wall-clock elapsed time
from pathlib import Path   # Cross-platform file paths

# Path to the directory containing this file (and all test scripts).
# Path(__file__) = absolute path to regression.py itself
# .resolve()     = canonicalize (resolve symlinks, make absolute)
# .parent        = the folder containing regression.py
# This means tests work regardless of what directory you run Python from.
HERE = Path(__file__).resolve().parent

# ── TEST SUITE REGISTRY ───────────────────────────────────────────────────────
# Each tuple is: (human-readable name, script filename, extra args list)
# Extra args are passed on the command line to the script (empty here).
SUITES = [
    ("Solver tests + benchmark",  "test_pow.py",        []),  # Tests pow_solver.py
    ("Protocol unit tests",       "smoke_test.py",      []),  # Tests handle_command() logic
    ("End-to-end system test",    "system_test.py",     []),  # Full session against mock TLS server
    ("Failure-mode tests",        "failure_test.py",    []),  # 7 server misbehavior scenarios
    ("Aggressive failure tests",  "aggressive_test.py", []),  # Network edge cases
]


# ── SUITE RUNNER ──────────────────────────────────────────────────────────────

def run_suite(name: str, script: str, args: list[str]) -> tuple[bool, float, str]:
    """
    Run one test script as a subprocess and return the result.

    WHY subprocess.run()?
    ----------------------
    subprocess.run() launches a completely separate Python process to execute
    the test file. This is better than just importing and calling functions
    because:
      - A segfault or hard crash in the test won't bring down regression.py
      - Each script gets a clean environment (no leftover global state)
      - We can set a time limit (timeout=) to catch infinite loops

    Returns a tuple:
        (passed: bool, elapsed_seconds: float, output_text: str)
    """
    t0 = time.monotonic()   # Record start time before launching the process

    try:
        proc = subprocess.run(
            # Build the command: "python test_pow.py" (using THIS Python executable)
            # sys.executable ensures we use the same Python as the one running regression.py
            # str(HERE / script) builds the full absolute path to the script file
            # *args unpacks any extra arguments into the command list
            [sys.executable, str(HERE / script), *args],

            capture_output=True,   # Capture both stdout and stderr (don't print to terminal yet)
            text=True,             # Decode output as UTF-8 text (not raw bytes)

            # Kill the process if it runs longer than 300 seconds (5 minutes).
            # failure_test.py takes ~35s (it tests a 30s hang timeout).
            # 300s gives plenty of slack without waiting forever if something freezes.
            timeout=300,
        )

    except subprocess.TimeoutExpired as e:
        # The test script didn't finish within 300 seconds — it's hanging.
        elapsed = time.monotonic() - t0   # How long we waited

        # e.stdout and e.stderr may be bytes or str depending on Python version
        # Decode them safely with errors="replace" to avoid crashing on bad encoding
        out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")

        # Return False (failed) with a TIMEOUT marker in the output
        return False, elapsed, f"TIMEOUT after {elapsed:.0f}s\n{out}\n{err}"

    elapsed = time.monotonic() - t0   # Measure total wall-clock time for the suite

    # A process exits with code 0 on success and non-zero on failure (Unix convention)
    ok = proc.returncode == 0

    # Combine stdout and stderr into one string for display
    # If there's any stderr output, append it after a newline
    output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")

    return ok, elapsed, output   # Return (passed, time_taken, combined_output)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> int:
    """
    Run all suites, print results, return exit code.

    Flow:
      1. Run each suite, collect results
      2. For passing suites: show only the last 8 lines (brief summary)
      3. For failing suites: show ALL output (you need to see what went wrong)
      4. Print the summary table
      5. Return 0 if all passed, 1 if any failed
    """
    # Print header showing how many test groups we're running
    print(f"=== Regression suite ({len(SUITES)} test groups) ===\n")

    results = []   # Accumulate (name, passed, elapsed) tuples for the summary table

    for name, script, args in SUITES:
        # Print a section header for each suite so you can find it in the output
        print(f"--- {name} ({script}) ---")

        # Actually run the suite (blocking — waits for it to finish)
        ok, elapsed, output = run_suite(name, script, args)

        # Store the result for the summary table at the end
        results.append((name, ok, elapsed))

        # Split the output into individual lines for selective display
        lines = output.strip().split("\n")

        if ok:
            # Success: only show the last 8 lines (usually the "[ok]" summary lines)
            # Showing everything would flood the screen — the details only matter on failure
            print("\n".join(lines[-8:]))
            print(f"PASS ({elapsed:.1f}s)\n")   # Show the time taken
        else:
            # Failure: show ALL output so you can debug what went wrong
            print(output)
            print(f"FAIL ({elapsed:.1f}s)\n")

    # ── Summary table ─────────────────────────────────────────────────────────
    print("=== Summary ===")
    all_pass = True   # Assume all passed until proven otherwise

    for name, ok, elapsed in results:
        status = "PASS" if ok else "FAIL"   # Human-readable status string
        # Print a formatted row: [PASS] Suite Name                    3.0s
        # The :35s format pads the name to 35 characters for alignment
        # The :>6.1f right-aligns the time with 1 decimal place
        print(f"  [{status}] {name:35s}  {elapsed:>6.1f}s")
        if not ok:
            all_pass = False   # At least one suite failed

    if all_pass:
        print("\nAll regression tests passed.")
        return 0   # Exit code 0 = success
    else:
        print("\nREGRESSION FAILURE. See output above.")
        return 1   # Exit code 1 = failure


# ── SCRIPT ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    # sys.exit() sets the process exit code so the OS and calling scripts
    # (like CI pipelines) know whether the tests passed or failed.
    sys.exit(main())
