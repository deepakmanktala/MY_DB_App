"""
================================================================================
FILE: smoke_test.py
PURPOSE: Fast unit tests for the protocol logic — NO network connection needed.

WHAT IS A SMOKE TEST?
----------------------
A "smoke test" is a quick sanity check — like turning on a device to see if
it smokes before you do full testing. These tests verify the core logic works
WITHOUT needing the real Exasol server, certificates, or network access.

WHAT IS TESTED HERE?
---------------------
This file tests the PROTOCOL HANDLING CODE in exasol_client.py:
  - Does HELO respond with TOAKUEI?
  - Does POW get solved correctly and the suffix verified?
  - Does each answer carry the right SHA-1 checksum?
  - Does END stop the session?
  - Are bad inputs (errors, blank lines, wrong order) rejected properly?
  - Does profile.json validation catch all known bad shapes?
  - Does the solver reject nonsensical difficulty values?

HOW IT WORKS (The "Fake" Trick):
---------------------------------
Instead of a real network socket, we create a FakeConn class that just
records all bytes "written" to it. Then we call handle_command() directly
with scripted input and check what it "wrote" to FakeConn.

This approach is called "mocking" or "stubbing" — replacing a complex real
dependency (network socket) with a simple fake that behaves predictably.

HOW TO RUN:
-----------
    python smoke_test.py

Takes < 1 second. Safe to run any time without network access.
================================================================================
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from __future__ import annotations   # Allow "type | None" union syntax on Python 3.9

import hashlib   # SHA-1 for verifying checksums in tests
import sys       # For sys.exit() at the bottom

# Import the specific functions we want to test from exasol_client.py
from exasol_client import (
    handle_command,   # The main protocol dispatcher — processes one server command
    load_profile,     # Profile JSON loader and validator
    LineConn,         # The real socket wrapper (imported for type reference only)
    answer_for,       # Maps server command names to profile values
)


# ── FAKE CONNECTION ───────────────────────────────────────────────────────────

class FakeConn:
    """
    A fake replacement for LineConn that captures writes without a real socket.

    WHAT PROBLEM DOES THIS SOLVE?
    --------------------------------
    handle_command() calls conn.write(data) to send responses to the server.
    In production, conn is a LineConn wrapping a TLS socket over the network.
    In tests, we don't want a real network connection — we just want to see
    what handle_command() WOULD have sent.

    FakeConn stores every write() call in a list (self.writes) so tests can
    inspect them afterwards.

    Example usage:
        conn = FakeConn()
        handle_command(conn, b"HELO", state, profile)
        assert conn.writes[-1] == b"TOAKUEI\n"  # Check what was "sent"
    """
    def __init__(self):
        # List to accumulate every bytes object passed to write()
        # [-1] gives the most recent write, [0] gives the first
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> None:
        """Capture the bytes that would have been sent to the server."""
        self.writes.append(data)   # Store instead of sending over network


# ── TEST 1: Full happy-path handshake ─────────────────────────────────────────

def test_full_handshake() -> None:
    """
    Simulate a complete server conversation and verify every response.

    This test drives handle_command() through the full sequence:
    HELO → POW → NAME/MAILNUM/MAIL1/MAIL2/SKYPE/BIRTHDATE/COUNTRY/ADDRNUM/ADDRLINE1/ADDRLINE2 → END

    For each step it checks:
      1. The function returns the right True/False (keep going vs stop)
      2. The bytes written to FakeConn are exactly correct
    """
    # Build a profile dict directly (bypassing file I/O)
    profile = {
        "NAME": "Test User",
        "MAILS": ["a@x.com", "b@x.com"],   # Two emails — tests MAILNUM=2, MAIL1, MAIL2
        "SKYPE": "N/A",
        "BIRTHDATE": "01.01.1990",
        "COUNTRY": "India",
        "ADDRESS": ["Line 1", "Line 2"],   # Two lines — tests ADDRNUM=2, ADDRLINE1, ADDRLINE2
    }
    conn = FakeConn()     # Our fake "socket" to capture responses
    state: dict = {}      # Empty session state (authdata will be populated by POW handler)

    # ── Step 1: HELO ──────────────────────────────────────────────────────────
    # Simulate the server sending "HELO"
    keep = handle_command(conn, b"HELO", state, profile)

    # handle_command should return True (keep going — session not over)
    assert keep is True

    # The last write should be exactly "TOAKUEI\n" — the magic greeting word
    assert conn.writes[-1] == b"TOAKUEI\n", conn.writes[-1]

    # ── Step 2: POW ───────────────────────────────────────────────────────────
    # We use difficulty=2 (only 16^2=256 expected hashes) so the test
    # finishes in milliseconds instead of minutes.
    authdata = b"mock-auth-12345"            # Pretend this came from the server
    pow_line = b"POW " + authdata + b" 2"   # Build the POW command bytes

    keep = handle_command(conn, pow_line, state, profile)

    # Should still be True (session continues after POW)
    assert keep is True

    # The last write is the suffix. Strip the trailing \n that the protocol adds.
    suffix = conn.writes[-1].rstrip(b"\n")

    # Verify the suffix actually satisfies difficulty=2 (digest starts with "00")
    digest = hashlib.sha1(authdata + suffix).hexdigest()
    assert digest.startswith("00"), f"bad pow: {digest}"

    # Verify that authdata got saved into the session state
    # (needed for all subsequent checksummed responses)
    assert state["authdata"] == authdata

    # ── Step 3: Personal data Q&A ─────────────────────────────────────────────
    # Helper function to test one personal-data command.
    # It simulates the server sending "CMD arg" and checks the response.
    def expect(line: bytes, value: str) -> None:
        """
        Send one server command and verify the response.

        The expected response format is:
            "<sha1(authdata + arg1)> <value>\n"

        This proves:
          1. The checksum is computed correctly from authdata and the arg
          2. The value matches what's in the profile
        """
        keep = handle_command(conn, line, state, profile)
        assert keep is True   # Session should still be going

        last = conn.writes[-1]   # Get the most recent response

        # Split the response at the first space:
        #   sha_prefix = "562ba3511339..."  (40-char hex checksum)
        #   payload    = "Deepak Manktala" (the actual answer)
        sha_prefix, _, payload = last.rstrip(b"\n").partition(b" ")

        # Extract arg1 from the server's command line (e.g. "NAME fjxi" -> "fjxi")
        arg1 = line.split(b" ", 1)[1] if b" " in line else b""

        # Compute what the checksum SHOULD be: SHA1(authdata + arg1)
        expected_sha = hashlib.sha1(authdata + arg1).hexdigest().encode()

        # Verify both the checksum and the value are correct
        assert sha_prefix == expected_sha, f"bad checksum on {line!r}: got {sha_prefix} expected {expected_sha}"
        assert payload.decode() == value, f"bad payload: {payload!r} vs {value!r}"

    # Test every possible command the server might ask, with different arg tokens
    expect(b"NAME randomarg",   "Test User")      # Name response
    expect(b"MAILNUM xyz",      "2")              # How many emails (we have 2)
    expect(b"MAIL1 abc",        "a@x.com")        # First email (1-indexed)
    expect(b"MAIL2 def",        "b@x.com")        # Second email
    expect(b"SKYPE qqq",        "N/A")            # Skype handle
    expect(b"BIRTHDATE www",    "01.01.1990")     # Date of birth
    expect(b"COUNTRY ttt",      "India")          # Country name
    expect(b"ADDRNUM rrr",      "2")              # How many address lines
    expect(b"ADDRLINE1 sss",    "Line 1")         # First address line
    expect(b"ADDRLINE2 uuu",    "Line 2")         # Second address line

    # ── Step 4: END ───────────────────────────────────────────────────────────
    # Server sends END — session is complete, data has been recorded
    keep = handle_command(conn, b"END", state, profile)

    # Should return False — this signals the caller to stop the loop
    assert keep is False

    # Our response to END must be exactly "OK\n"
    assert conn.writes[-1] == b"OK\n"

    # Print summary with total write count (HELO + POW + 10 answers + END = 13)
    print(f"[ok] full mock handshake passed ({len(conn.writes)} writes)")


# ── TEST 2: Server ERROR should raise ProtocolError ───────────────────────────

def test_error_raises() -> None:
    """
    Verify that a server ERROR command is treated as a FATAL error (no retry).

    When the server sends "ERROR something went wrong", our code must raise
    ProtocolError — NOT silently continue or retry on another port.
    This is critical: if we retried after a protocol error, we'd submit
    the same bad data 6 times across 6 ports.
    """
    from exasol_client import ProtocolError   # Import our custom exception class

    # Minimal profile — content doesn't matter for this test
    profile = {
        "NAME": "x", "MAILS": ["a@b.c"], "SKYPE": "N/A",
        "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"],
    }
    conn = FakeConn()
    state = {"authdata": b"x"}   # Pretend POW already completed

    try:
        # Simulate the server sending an error message
        handle_command(conn, b"ERROR something went wrong", state, profile)

    except ProtocolError as e:
        # Verify the error message contains the server's error text
        assert "something went wrong" in str(e)
        print(f"[ok] ERROR raises ProtocolError: {e}")
        return   # Test passed

    # If we get here, no exception was raised — that's a bug
    raise AssertionError("ERROR did not raise")


# ── TEST 3: Unknown command should raise RuntimeError ─────────────────────────

def test_unknown_command_raises() -> None:
    """
    Verify that an unrecognised server command raises an error.

    The server protocol defines exactly which commands exist. If the server
    sends something we don't recognise (e.g. "FROBNICATE"), we should
    raise an error rather than silently skipping it. Silent skipping could
    cause us to miss a required field and have our application rejected.
    """
    profile = {
        "NAME": "x", "MAILS": ["a@b.c"], "SKYPE": "N/A",
        "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"],
    }
    conn = FakeConn()
    state = {"authdata": b"x"}   # POW already "done"

    try:
        # "FROBNICATE" is not a real protocol command — should raise
        handle_command(conn, b"FROBNICATE arg1", state, profile)

    except RuntimeError as e:
        # Verify the error message names the problematic command
        assert "Unknown server command" in str(e)
        print(f"[ok] unknown command raises: {e}")
        return

    raise AssertionError("unknown command did not raise")


# ── TEST 4: Blank/empty lines should raise ────────────────────────────────────

def test_blank_line_raises() -> None:
    """
    Verify that empty or whitespace-only lines from the server are rejected.

    An empty line is not a valid protocol command. If we tried to parse
    it, tokens[0] would fail. We should detect and reject it early with
    a clear ProtocolError rather than crashing with an IndexError.

    Tests three variants:
        b""    — empty bytes (zero-length line)
        b"   " — spaces only
        b"\t"  — tab only
    """
    from exasol_client import ProtocolError

    profile = {
        "NAME": "x", "MAILS": ["a@b.c"], "SKYPE": "N/A",
        "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"],
    }
    conn = FakeConn()
    state: dict = {}

    # Test each blank-line variant
    for line in (b"", b"   ", b"\t"):
        try:
            handle_command(conn, line, state, profile)
        except ProtocolError as e:
            print(f"[ok] blank line {line!r} raises: {e}")
            continue   # This line correctly raised — test passes for this variant
        raise AssertionError(f"blank line {line!r} did not raise")


# ── TEST 5: Personal data command before POW should raise ─────────────────────

def test_command_before_pow_raises() -> None:
    """
    Verify that personal-data commands before POW are rejected.

    Protocol order: HELO → POW → (personal questions) → END.
    If the server sends NAME before POW, that's a protocol violation.
    We should reject it, not try to compute a checksum with no authdata.

    Without this check, answer_for() would try to use state["authdata"]
    which doesn't exist yet, causing a KeyError. We want a clearer error.
    """
    from exasol_client import ProtocolError

    profile = {
        "NAME": "x", "MAILS": ["a@b.c"], "SKYPE": "N/A",
        "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"],
    }
    conn = FakeConn()
    state: dict = {}   # Empty — authdata has NOT been set (no POW yet)

    try:
        # Simulate server skipping POW and sending NAME directly
        handle_command(conn, b"NAME someargument", state, profile)

    except ProtocolError as e:
        # Verify the error message explains the problem clearly
        assert "before POW" in str(e)
        print(f"[ok] command before POW raises: {e}")
        return

    raise AssertionError("command before POW did not raise")


# ── TEST 6: Malformed POW lines should raise ──────────────────────────────────

def test_malformed_pow_raises() -> None:
    """
    Verify that malformed POW commands are rejected with clear errors.

    The POW line must be: "POW <authdata> <difficulty>"
    We test 5 ways it can be wrong:
      1. "POW" alone          — missing authdata and difficulty
      2. "POW onlyone"        — only authdata, missing difficulty
      3. "POW auth notanum"   — difficulty is not an integer
      4. "POW auth -5"        — negative difficulty (impossible)
      5. "POW auth 99"        — difficulty > 40 (SHA-1 only has 40 hex chars)

    Each should raise ProtocolError with a message containing the
    expected keyword.
    """
    from exasol_client import ProtocolError

    profile = {
        "NAME": "x", "MAILS": ["a@b.c"], "SKYPE": "N/A",
        "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"],
    }

    # (command_bytes, expected_substring_in_error_message)
    cases = [
        (b"POW",                        "malformed"),    # No fields at all
        (b"POW onlyone",                "malformed"),    # Only one field (authdata), missing difficulty
        (b"POW someauth notanumber",    "non-integer"),  # Difficulty is a word, not a number
        (b"POW someauth -5",            "out-of-range"), # Negative difficulty (nonsensical)
        (b"POW someauth 99",            "out-of-range"), # SHA-1 only has 40 hex chars max
    ]

    for line, expected in cases:
        conn = FakeConn()
        state: dict = {}

        try:
            handle_command(conn, line, state, profile)

        except ProtocolError as e:
            # Check the error message contains the expected keyword
            assert expected in str(e), f"line={line!r}: expected {expected!r} in {e}"
            print(f"[ok] malformed POW {line!r} raises: {e}")
            continue   # This case passed

        raise AssertionError(f"malformed POW {line!r} did not raise")


# ── TEST 7: Multiple spaces/tabs between tokens should still parse ─────────────

def test_multispace_tolerant() -> None:
    """
    Verify the tokeniser handles multiple spaces or tab characters gracefully.

    The Exasol protocol uses single spaces. But defensive parsing means we
    should tolerate "NAME  argval" (double space) and "NAME\targval" (tab)
    and parse them identically to "NAME argval".

    This matters because:
      - Future protocol revisions might change spacing
      - Some server implementations might accidentally send extra spaces
      - A tab from a misconfigured server shouldn't break us

    We verify that both double-space and tab produce IDENTICAL responses
    (since the arg token "argval" is the same in both cases, the SHA-1
    checksums should be identical).
    """
    profile = {
        "NAME": "Test", "MAILS": ["a@b.c"], "SKYPE": "N/A",
        "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"],
    }
    conn = FakeConn()
    state = {"authdata": b"auth"}   # Pretend POW is done

    # Send "NAME  argval" (double space between NAME and argval)
    handle_command(conn, b"NAME  argval", state, profile)

    # Send "NAME\targval" (tab between NAME and argval)
    handle_command(conn, b"NAME\targval", state, profile)

    # Both responses should be identical — same arg "argval" → same SHA-1 checksum
    assert conn.writes[0] == conn.writes[1], "multi-space and tab gave different results"
    print(f"[ok] tokeniser handles multi-space and tab uniformly")


# ── TEST 8: Solver input validation ───────────────────────────────────────────

def test_pow_solver_input_validation() -> None:
    """
    Verify solve_pow() rejects bad inputs immediately with clear exceptions.

    These checks happen BEFORE any hashing, so they're instant (no compute).
    We test four bad input scenarios:
      1. authdata is a string instead of bytes  → TypeError
      2. difficulty is a float instead of int   → TypeError
      3. difficulty is negative                 → ValueError
      4. difficulty > 40                        → ValueError (SHA-1 max is 40 hex chars)

    Why test this? If these checks are missing, you'd get cryptic errors deep
    inside the hot loop (like a struct.pack failure) instead of a clear message
    at the point where the bad value was passed.
    """
    from pow_solver import solve_pow   # Import the solver function directly

    # (description, authdata, difficulty, expected_exception_class)
    bad_inputs = [
        ("authdata not bytes",  "string",  5,    TypeError),   # Should be bytes, not str
        ("difficulty not int",  b"auth",   5.0,  TypeError),   # Should be int, not float
        ("difficulty negative", b"auth",   -1,   ValueError),  # Must be >= 0
        ("difficulty too large",b"auth",   41,   ValueError),  # SHA-1 only has 40 hex chars
    ]

    for name, auth, diff, exc_type in bad_inputs:
        try:
            solve_pow(auth, diff)   # This should raise before doing any hashing

        except exc_type as e:
            # Got the expected exception type — test passes for this case
            print(f"[ok] solver rejects {name}: {type(e).__name__}: {e}")
            continue

        # If we get here, the exception wasn't raised — that's a bug
        raise AssertionError(f"{name}: did not raise {exc_type.__name__}")


# ── TEST 9: Difficulty 0 edge case ────────────────────────────────────────────

def test_difficulty_zero() -> None:
    """
    Verify that difficulty=0 works correctly.

    Difficulty 0 means "find a suffix where SHA1(auth+suffix) starts with
    zero leading zero hex chars" — which is always true (EVERY hash satisfies
    this). So the solver should return a valid suffix on the very first attempt.

    Why test this edge case? The target computation:
        full_zero = b""   (0 bytes)
        half_byte = 0
    Means the comparison d[:0] == b"" is always True.
    The solver could accidentally return an EMPTY suffix (b"") which violates
    the protocol (server rejects empty suffixes). We verify len >= 1.
    """
    from pow_solver import _solve_single   # Use the single-core solver directly

    suffix = _solve_single(b"auth", 0)   # Solve with zero required zeros

    # Suffix must be at least 1 byte long (empty suffix is not allowed)
    assert len(suffix) >= 1

    # Verify no forbidden characters (these would break the line protocol)
    for forbidden in (b"\n", b"\r", b"\t", b" "):
        assert forbidden not in suffix

    print(f"[ok] difficulty=0 returns valid suffix={suffix!r}")


# ── TEST 10: Profile validation catches all bad inputs ────────────────────────

def test_profile_validation() -> None:
    """
    Verify that load_profile() rejects 14 known bad profile shapes.

    WHY THIS MATTERS:
    -----------------
    The profile.json contains your personal data. A typo (wrong format) or
    bad value (missing field, number where string expected) would cause the
    server to reject your application AFTER you've spent hours on the POW.
    We validate everything upfront to catch mistakes immediately.

    This test checks 14 different bad shapes, including:
      - Missing required keys
      - Wrong JSON type (list instead of object)
      - Number where string is expected
      - Empty strings
      - Single-word NAME (must be first + last)
      - Control characters (newline, tab, NUL) in values
      - Non-list MAILS
      - Empty MAILS list
      - Non-string items in MAILS list
      - Empty address line

    Each case must raise ValueError with a message containing a specific keyword.
    """
    import tempfile   # For creating temporary files without naming them manually
    import json       # For writing test profiles to disk
    import os         # For deleting temporary files
    from exasol_client import load_profile   # The function we're testing

    # Each tuple: (test_label, profile_data, expected_substring_in_error)
    bad_cases = [
        # ── Missing fields ────────────────────────────────────────────────────
        ("missing_keys",
         {"NAME": "x"},   # Only NAME, missing MAILS/SKYPE/BIRTHDATE/COUNTRY/ADDRESS
         "missing required keys"),

        # ── Wrong top-level type ──────────────────────────────────────────────
        ("not_a_dict",
         ["a", "b"],   # A list, not a JSON object (dict)
         "must be a JSON object"),

        # ── NAME type errors ──────────────────────────────────────────────────
        ("name_not_string",
         {"NAME": 123, "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "must be a string"),   # 123 is an integer, not a string

        ("name_none",
         {"NAME": None, "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "must be a string"),   # None is not a string

        # ── NAME content errors ───────────────────────────────────────────────
        ("name_empty",
         {"NAME": "", "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "non-empty"),   # Empty string is not a valid name

        ("name_whitespace",
         {"NAME": "   ", "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "non-empty"),   # Whitespace-only string is not valid

        ("name_one_word",
         {"NAME": "OnlyOne", "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "first AND last name"),   # Server requires both first and last name

        # ── NAME control character errors ─────────────────────────────────────
        ("name_with_newline",
         {"NAME": "First\nLast", "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "control character"),   # \n would break the line-based protocol

        ("name_with_tab",
         {"NAME": "First\tLast", "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "control character"),   # \t could be interpreted as a field separator

        # ── ADDRESS control character errors ──────────────────────────────────
        ("address_with_nul",
         {"NAME": "First Last", "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x\x00y"]},
         "control character"),   # NUL byte (\x00) in address — protocol-unsafe

        # ── MAILS structure errors ────────────────────────────────────────────
        ("mails_not_list",
         {"NAME": "First Last", "MAILS": "string", "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "non-empty list"),   # MAILS must be a JSON array, not a string

        ("mails_empty",
         {"NAME": "First Last", "MAILS": [], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "non-empty list"),   # Empty list means no email — server would reject

        ("mails_has_int",
         {"NAME": "First Last", "MAILS": ["a@b.c", 123], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": ["x"]},
         "must be a string"),   # List items must be strings, not numbers

        # ── ADDRESS content errors ────────────────────────────────────────────
        ("address_empty_item",
         {"NAME": "First Last", "MAILS": ["a@b.c"], "SKYPE": "N/A",
          "BIRTHDATE": "01.01.1990", "COUNTRY": "India", "ADDRESS": [""]},
         "non-empty"),   # Empty string address line is not valid
    ]

    # Run each bad case through load_profile() and verify it raises the right error
    for label, data, expected_err in bad_cases:
        # Write the bad profile to a real temporary file (load_profile reads files)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)    # Write test data as JSON
            path = f.name         # Remember the temp file path

        try:
            load_profile(path)    # This should raise ValueError
            # If we get here, load_profile accepted bad data — that's a bug
            raise AssertionError(f"{label}: should have rejected {data!r}")

        except (ValueError, TypeError) as e:
            # Verify the error message contains the expected keyword
            assert expected_err in str(e), (
                f"{label}: expected {expected_err!r} in error, got: {e}"
            )

        finally:
            os.unlink(path)   # Always clean up the temporary file

    print(f"[ok] profile validation rejects {len(bad_cases)} bad cases")

    # ── Also verify a VALID profile passes without raising ────────────────────
    valid = {
        "NAME": "First Last",        # Two words — OK
        "MAILS": ["a@b.c"],          # Non-empty list — OK
        "SKYPE": "N/A",
        "BIRTHDATE": "01.01.1990",
        "COUNTRY": "India",
        "ADDRESS": ["Line 1"],       # Non-empty address — OK
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(valid, f)
        path = f.name

    try:
        load_profile(path)   # Should NOT raise — a valid profile must be accepted
        print(f"[ok] valid profile is accepted")
    finally:
        os.unlink(path)   # Clean up


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """Run all smoke tests in order. Any assertion failure stops execution."""
    test_full_handshake()             # Full HELO→POW→Q&A→END flow
    test_error_raises()               # Server ERROR → ProtocolError
    test_profile_validation()         # 14 bad profile shapes + 1 valid
    test_unknown_command_raises()     # Unknown command → RuntimeError
    test_blank_line_raises()          # Empty/whitespace lines → ProtocolError
    test_command_before_pow_raises()  # NAME before POW → ProtocolError
    test_malformed_pow_raises()       # 5 malformed POW variants → ProtocolError
    test_multispace_tolerant()        # Double-space and tab both parse correctly
    test_pow_solver_input_validation()# 4 bad solver inputs → TypeError/ValueError
    test_difficulty_zero()            # d=0 returns valid non-empty suffix

    print("\nAll smoke tests passed.")


# ── SCRIPT ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    main()   # No sys.exit needed — Python exits 0 on success, 1 on uncaught exception
