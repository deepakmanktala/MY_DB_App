"""
================================================================================
FILE: failure_test.py
PURPOSE: Test how the client behaves when the SERVER misbehaves.

WHAT IS A FAILURE-MODE TEST?
------------------------------
Normal tests check that things work correctly when everything goes right.
Failure-mode tests ask: "what happens when things go WRONG?"

This file tests 7 server misbehavior scenarios:
  1. Server disconnects immediately (before saying anything)
  2. Server sends ERROR right away (no greeting)
  3. Server sends a huge line (100 KB) without a newline (memory bomb attempt)
  4. Server stops responding after HELO (hang attack)
  5. Server sends NAME before POW (protocol violation)
  6. Server sends a malformed POW line (missing fields)
  7. Normal happy path (sanity check that the test infrastructure works)

WHY TEST THESE FAILURE MODES?
-------------------------------
Without proper failure handling:
  - A server hang would cause our client to wait forever (2+ hours)
  - An error after a 2-hour POW would be lost if we retried silently
  - A huge line without a newline would cause unbounded memory growth
  - A protocol violation would cause cryptic crashes instead of clear errors

Each test verifies the client exits with the correct code AND logs appropriate
error messages.

HOW IT WORKS:
--------------
Each test:
  1. Creates a FailServer with a specific "behavior" (e.g. "immediate_disconnect")
  2. Starts it in a background thread on localhost
  3. Runs exasol_client.py as a subprocess against it
  4. Checks the exit code and stderr message

HOW TO RUN:
-----------
    python failure_test.py

Takes ~35 seconds (most time is the hang_after_helo test which waits 30s
for the client to detect the server timeout).
================================================================================
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from __future__ import annotations   # Allow "type | None" syntax on Python 3.9

import hashlib      # SHA-1 for verifying POW solutions in the happy-path test
import os           # (unused directly but available for subclasses)
import socket       # TCP socket for the mock server
import ssl          # TLS wrapping for the mock server
import subprocess   # Running exasol_client.py as a subprocess
import sys          # sys.executable and sys.exit()
import tempfile     # Creating temporary directories for test files
import threading    # Running the mock server in a background thread
import time         # time.sleep() for simulating hangs; timing assertions
from pathlib import Path   # Cross-platform file paths

# Add this file's directory to Python's import path so _test_certs can be imported
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Import functions that write pre-generated test certificates to disk
from _test_certs import write_test_server_pem, write_test_client_pem


# ── CERTIFICATE HELPERS ───────────────────────────────────────────────────────

def make_server_certs(workdir: Path) -> tuple[Path, Path]:
    """Write the mock server's TLS certificate and private key to disk."""
    return write_test_server_pem(workdir)   # Returns (cert_path, key_path)


def make_client_pem(workdir: Path) -> Path:
    """Write the mock client's combined certificate+key PEM to disk."""
    return write_test_client_pem(workdir)   # Returns combined PEM path


def make_profile(workdir: Path) -> Path:
    """
    Write a minimal valid profile.json to the work directory.

    Every test that runs the real client needs a profile file.
    The content doesn't matter for failure tests — the server misbehaves
    before asking personal questions, so these values are never sent.
    """
    import json
    p = workdir / "profile.json"   # Path for the profile file
    with open(p, "w") as f:
        json.dump({
            "NAME":      "Failure Test",         # Any valid two-word name
            "MAILS":     ["test@example.com"],   # At least one email
            "SKYPE":     "N/A",
            "BIRTHDATE": "01.01.1990",
            "COUNTRY":   "Germany",
            "ADDRESS":   ["Line 1"],
        }, f)
    return p   # Return the path so run_client() can use it


# ── CONFIGURABLE MISBEHAVING SERVER ───────────────────────────────────────────

class FailServer:
    """
    A TLS server that deliberately misbehaves in a configured way.

    The `behavior` parameter controls how the server acts. This single class
    handles all 7 misbehavior scenarios by switching on the behavior string
    inside _misbehave().

    This design means we write the server startup/TLS code ONCE and reuse
    it for all test cases, only varying the misbehavior logic.
    """

    def __init__(self, behavior: str, workdir: Path):
        self.behavior = behavior      # Which misbehavior to simulate (see _misbehave)
        self.host = "127.0.0.1"       # Listen only on localhost (secure)
        self.port = 0                 # 0 = OS assigns a free port
        self.actual_port: int | None = None    # Set after bind() — the real port
        self.workdir = workdir        # Where to store cert files
        # Write TLS certificate files to disk
        self.server_cert, self.server_key = make_server_certs(workdir)
        self.thread: threading.Thread | None = None   # Background thread
        self.error: Exception | None = None           # Any exception from the thread

    def start(self) -> int:
        """
        Start the misbehaving server in a background thread.

        Uses a threading.Event as a "ready" signal — the thread sets it
        when the socket is bound and listening, so start() doesn't return
        until the server is actually ready to accept connections.

        Returns: the port the server is listening on
        """
        ready = threading.Event()   # Unset initially; thread sets it when ready

        def run():
            """Body of the background server thread."""
            try:
                self._run(ready)   # Run server setup and wait for client
            except Exception as e:
                self.error = e     # Save any exception
            finally:
                ready.set()        # Always signal ready (even on error) so start() doesn't hang

        self.thread = threading.Thread(target=run, daemon=True)   # daemon dies with main process
        self.thread.start()   # Launch background thread

        # Wait up to 5 seconds for the server to be ready
        if not ready.wait(5.0):
            raise RuntimeError("server failed to start")

        assert self.actual_port is not None   # Should be set by now
        return self.actual_port   # Return port for the client to connect to

    def _run(self, ready: threading.Event) -> None:
        """
        Set up TLS server socket, signal ready, then accept one connection.

        After accepting, immediately calls _misbehave() to perform the
        configured bad behavior.
        """
        # TLS server context
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=str(self.server_cert), keyfile=str(self.server_key))

        # Plain TCP socket
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # Reuse port
        srv.bind((self.host, 0))    # Bind to OS-assigned free port
        srv.listen(1)               # Ready to accept one connection
        self.actual_port = srv.getsockname()[1]   # Save the assigned port
        ready.set()   # Signal the main thread that we're listening

        # Wait up to 30 seconds for a client to connect
        srv.settimeout(30.0)
        try:
            client_sock, _ = srv.accept()   # Block until client connects
        finally:
            srv.close()   # Close listening socket — only need one connection

        # Wrap with TLS encryption
        with ctx.wrap_socket(client_sock, server_side=True) as tls:
            self._misbehave(tls)   # Perform the configured bad behavior

    def _misbehave(self, tls: ssl.SSLSocket) -> None:
        """
        Perform the configured misbehavior on the connected TLS socket.

        Each `behavior` string triggers a different scenario.
        """
        b = self.behavior   # Short alias for readability

        # ── Scenario 1: immediate_disconnect ──────────────────────────────────
        if b == "immediate_disconnect":
            # Don't send ANYTHING. Just return, which closes the TLS connection.
            # Client should detect "server closed connection" and fail gracefully.
            return

        # ── Scenario 2: send_error ────────────────────────────────────────────
        if b == "send_error":
            # Send ERROR before HELO — skipping the normal handshake entirely.
            # A real server might do this if our certificate is invalid or expired.
            # Client should: detect ERROR, raise ProtocolError, exit 1, NOT retry.
            tls.sendall(b"ERROR something is wrong\n")
            return   # Close connection after error

        # ── Scenario 3: send_error_after_helo ─────────────────────────────────
        if b == "send_error_after_helo":
            tls.sendall(b"HELO\n")         # Send normal greeting
            self._read_line(tls)            # Read (and discard) client's TOAKUEI response
            tls.sendall(b"ERROR rejected\n")  # Then immediately send error
            return   # Close connection

        # ── Scenario 4: huge_line ─────────────────────────────────────────────
        if b == "huge_line":
            # Send 100,000 bytes (100 KB) of 'X' characters WITH NO NEWLINE.
            # This tests whether our client has a memory safety limit.
            # Without MAX_LINE_BYTES, the client would keep accumulating bytes forever.
            # With it, the client should raise "line exceeded 65536 bytes" and exit.
            tls.sendall(b"X" * 100_000)   # 100 KB of garbage without \n
            time.sleep(2)   # Give client time to read and react before we close
            return

        # ── Scenario 5: hang_after_helo ───────────────────────────────────────
        if b == "hang_after_helo":
            tls.sendall(b"HELO\n")         # Send normal greeting
            self._read_line(tls)            # Read TOAKUEI response
            # Then do NOTHING for 60 seconds — simulates a server that freezes
            # after the handshake. Client should time out at ~30 seconds
            # (our READ_TIMEOUT_SHORT = 30.0 in run_session).
            time.sleep(60)
            return

        # ── Scenario 6: command_before_pow ────────────────────────────────────
        if b == "command_before_pow":
            tls.sendall(b"HELO\n")          # Normal greeting
            self._read_line(tls)             # Read TOAKUEI
            # Send NAME BEFORE POW — this is a server-side protocol violation.
            # Client should detect "got NAME before POW" and raise ProtocolError.
            tls.sendall(b"NAME someargument\n")
            return

        # ── Scenario 7: malformed_pow ─────────────────────────────────────────
        if b == "malformed_pow":
            tls.sendall(b"HELO\n")            # Normal greeting
            self._read_line(tls)               # Read TOAKUEI
            # Send POW with only ONE field (should be THREE: POW <authdata> <difficulty>)
            tls.sendall(b"POW only_one_field\n")
            return

        # ── Scenario 8: successful_low_difficulty ─────────────────────────────
        if b == "successful_low_difficulty":
            # This is the HAPPY PATH — a normal successful session at difficulty 2.
            # Used as a sanity check that our test infrastructure works correctly.
            tls.sendall(b"HELO\n")
            self._read_line(tls)   # Read TOAKUEI

            authdata = b"failtest-auth"   # Fixed authdata for this test
            # Send difficulty=2 (16^2=256 hashes expected, < 1ms)
            tls.sendall(b"POW " + authdata + b" 2\n")

            # Read client's POW solution suffix
            suffix = self._read_line(tls)
            # Verify the suffix actually solves the POW
            d = hashlib.sha1(authdata + suffix).hexdigest()
            assert d.startswith("00")   # Difficulty 2 = 2 leading zero hex chars

            # Ask a few personal-data questions and read the responses
            # (We don't verify checksums here — that's tested in smoke_test.py)
            tls.sendall(b"NAME q\n")
            r = self._read_line(tls)    # Read (and ignore) the response
            tls.sendall(b"MAILNUM q\n")
            self._read_line(tls)
            tls.sendall(b"MAIL1 q\n")
            self._read_line(tls)
            tls.sendall(b"SKYPE q\n")
            self._read_line(tls)
            tls.sendall(b"BIRTHDATE q\n")
            self._read_line(tls)
            tls.sendall(b"COUNTRY q\n")
            self._read_line(tls)
            tls.sendall(b"ADDRNUM q\n")
            self._read_line(tls)
            tls.sendall(b"ADDRLINE1 q\n")
            self._read_line(tls)
            tls.sendall(b"END\n")       # Signal successful completion
            self._read_line(tls)        # Read "OK"
            return

    @staticmethod
    def _read_line(tls: ssl.SSLSocket) -> bytes:
        """
        Simple line reader for the server side.

        Accumulates bytes until a newline, then returns the line without \n.
        If the client disconnects, returns whatever was in the buffer.
        (Static method — doesn't need access to self)
        """
        buf = b""
        while b"\n" not in buf:
            chunk = tls.recv(4096)   # Read up to 4096 bytes
            if not chunk:
                return buf   # Client disconnected — return partial data
            buf += chunk
        line, _, _ = buf.partition(b"\n")   # Split at newline, discard remainder
        return line   # Return the line without the newline character


# ── CLIENT RUNNER ─────────────────────────────────────────────────────────────

def run_client(workdir: Path, port: int, timeout: float = 60.0) -> tuple[int, str, str]:
    """
    Run exasol_client.py as a subprocess and return (exit_code, stdout, stderr).

    WHY SUBPROCESS?
    ----------------
    We need to test the full client program — including its argument parsing,
    self-test, profile loading, and session management. Running it as a
    subprocess tests the whole thing, not just individual functions.

    Parameters:
        workdir: directory containing profile.json and client PEM
        port:    which port the mock server is listening on
        timeout: max seconds to wait for the client to exit
    """
    profile = make_profile(workdir)      # Create profile.json in the work directory
    client_pem = make_client_pem(workdir)   # Create client TLS credentials

    proc = subprocess.run(
        [
            sys.executable,                    # Current Python interpreter
            str(HERE / "exasol_client.py"),    # The client script to test
            "--cert",     str(client_pem),     # Client certificate
            "--key",      str(client_pem),     # Private key (same file)
            "--insecure",                      # Don't verify mock server cert
            "--profile",  str(profile),        # Personal answers file
            "--host",     "127.0.0.1",         # Connect to localhost
            "--port",     str(port),           # Connect to our mock server's port
            "--no-selftest",                   # Skip self-test (saves time)
        ],
        capture_output=True,   # Capture stdout and stderr separately
        text=True,             # Return as text strings
        timeout=timeout,       # Kill and fail if takes too long
    )
    return proc.returncode, proc.stdout, proc.stderr


# ── INDIVIDUAL FAILURE TESTS ──────────────────────────────────────────────────

def test_immediate_disconnect():
    """
    SCENARIO: Server disconnects immediately before sending anything.

    WHAT WE EXPECT:
    - Client tries to read_line() and gets an empty/closed connection
    - Client raises TransientError (connection closed = network error)
    - Since only one port is configured, all ports are exhausted
    - Client exits with non-zero code (failure)
    - stderr contains "transient" or "fatal"

    WHY THIS MATTERS:
    This simulates a server that crashed, a firewall that resets connections,
    or a network route that doesn't reach the server.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ft1-"))   # Create temp directory
    srv = FailServer("immediate_disconnect", workdir)  # Server that disconnects immediately
    port = srv.start()                                 # Start in background thread
    code, _, err = run_client(workdir, port, timeout=10)   # Run client with 10s timeout
    assert code != 0, "expected failure on immediate disconnect"   # Must fail
    # Verify the error is categorized correctly in stderr
    assert "transient" in err.lower() or "fatal" in err.lower(), f"unexpected stderr: {err}"
    print(f"[ok] immediate_disconnect: client exited {code}, error logged")


def test_send_error():
    """
    SCENARIO: Server sends ERROR immediately (before HELO, even).

    WHAT WE EXPECT:
    - Client reads "ERROR something is wrong"
    - Client raises ProtocolError (not TransientError)
    - Client exits with code 1 (fatal, no retry on other ports)
    - stderr contains "ERROR"

    WHY THIS MATTERS:
    If a server ERROR was treated as transient, the client would retry on
    all 6 ports — submitting the same bad data 6 times. ERROR must be fatal.

    WHY exit 1 specifically?
    exit 1 = ProtocolError = "server rejected us, don't retry"
    exit 1 means it tried all ports and failed = wrong behavior
    The test specifically checks for exit 1 to confirm no retry happened.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ft2-"))
    srv = FailServer("send_error", workdir)
    port = srv.start()
    code, out, err = run_client(workdir, port, timeout=10)
    assert code == 1, f"expected exit 1 (fatal), got {code}"   # Must be exactly 1 (fatal)
    # Verify ERROR message appears somewhere in the output
    assert "ERROR" in err or "ERROR" in out, f"expected ERROR message: out={out!r} err={err!r}"
    print(f"[ok] send_error: client exited 1 (fatal), no retry")


def test_huge_line():
    """
    SCENARIO: Server sends 100 KB of data without any newline.

    WHAT WE EXPECT:
    - Client accumulates data in its read buffer
    - At 65,536 bytes (MAX_LINE_BYTES), client raises "line exceeded ... bytes"
    - Client wraps this as TransientError and exits
    - stderr contains "exceeded" or "transient"

    WHY THIS MATTERS:
    Without this limit, a malicious or broken server could send endless data
    and exhaust all available memory. The 64KB cap prevents this.

    Note: The server sends 100KB > 64KB limit, so the client hits the cap
    before reading all the data.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ft3-"))
    srv = FailServer("huge_line", workdir)
    port = srv.start()
    code, _, err = run_client(workdir, port, timeout=15)   # 15s for the 2s server sleep
    assert code != 0   # Must fail
    assert "exceeded" in err.lower() or "transient" in err.lower(), f"stderr: {err}"
    print(f"[ok] huge_line: client rejected oversized line cleanly")


def test_hang_after_helo():
    """
    SCENARIO: Server stops sending data after receiving TOAKUEI.

    WHAT WE EXPECT:
    - Client sends TOAKUEI and then calls read_line(timeout=30.0)
    - After 30 seconds of silence, socket.timeout is raised
    - Client wraps this as TransientError and exits
    - Total elapsed time is between 25-45 seconds (the 30s read timeout)

    WHY THIS MATTERS:
    Without a read timeout, the client would wait FOREVER — blocking the
    terminal and never completing the submission. The 30s timeout ensures
    the client fails within a reasonable time.

    The test verifies timing to confirm:
    - We waited long enough (> 25s) — the timeout actually fired
    - We didn't wait too long (< 45s) — we didn't hang beyond the timeout
    """
    workdir = Path(tempfile.mkdtemp(prefix="ft4-"))
    srv = FailServer("hang_after_helo", workdir)
    port = srv.start()
    t0 = time.monotonic()   # Record start time to measure elapsed
    code, _, err = run_client(workdir, port, timeout=50)   # 50s > 30s timeout
    elapsed = time.monotonic() - t0   # How long the client actually took
    assert code != 0   # Must fail
    # The client should have timed out in ~30 seconds
    assert elapsed < 45, f"client took too long to detect hang: {elapsed:.1f}s"
    assert elapsed > 25, f"client gave up too quickly: {elapsed:.1f}s"
    print(f"[ok] hang_after_helo: client timed out in {elapsed:.1f}s as expected")


def test_command_before_pow():
    """
    SCENARIO: Server sends NAME command before sending POW.

    WHAT WE EXPECT:
    - Client receives "NAME someargument" but authdata is not set yet
    - Client raises ProtocolError("got NAME before POW")
    - Client exits with code 1 (fatal — this is a protocol violation)
    - stderr contains "before POW"

    WHY THIS MATTERS:
    Our response to personal-data questions requires authdata from the POW step.
    If we tried to answer without it, we'd either crash (KeyError) or compute
    a wrong checksum (using empty authdata). Either way is wrong.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ft5-"))
    srv = FailServer("command_before_pow", workdir)
    port = srv.start()
    code, _, err = run_client(workdir, port, timeout=10)
    assert code == 1, f"expected fatal exit, got {code}"   # Fatal, no retry
    assert "before POW" in err, f"unexpected stderr: {err}"   # Clear error message
    print(f"[ok] command_before_pow: client detected violation")


def test_malformed_pow():
    """
    SCENARIO: Server sends "POW only_one_field" (missing difficulty number).

    WHAT WE EXPECT:
    - Client parses "POW only_one_field" and finds only 2 tokens (need 3)
    - Client raises ProtocolError("malformed POW line")
    - Client exits with code 1 (fatal)
    - stderr contains "malformed POW"

    WHY THIS MATTERS:
    Without this check, splitting on tokens[2] would raise IndexError with
    a confusing traceback. We validate the line structure first and give
    a clear, specific error message.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ft6-"))
    srv = FailServer("malformed_pow", workdir)
    port = srv.start()
    code, _, err = run_client(workdir, port, timeout=10)
    assert code == 1   # Fatal error
    assert "malformed POW" in err, f"unexpected stderr: {err}"   # Specific message
    print(f"[ok] malformed_pow: client rejected malformed line")


def test_happy_path():
    """
    SCENARIO: A normal successful session at very low difficulty.

    WHAT WE EXPECT:
    - Client connects, solves POW (difficulty=2, ~instant), answers questions
    - Server sends END, client replies OK
    - Client exits with code 0
    - stdout contains "submission accepted"

    WHY THIS TEST EXISTS HERE:
    This confirms that the test infrastructure (FailServer + run_client) itself
    works correctly for the normal case. If this test fails, something is wrong
    with how the test framework is set up, not with failure handling.
    It also serves as a baseline: "at least the happy path works" before
    testing edge cases.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ft7-"))
    srv = FailServer("successful_low_difficulty", workdir)
    port = srv.start()
    code, out, err = run_client(workdir, port, timeout=30)
    assert code == 0, f"happy path failed: code={code}, stderr={err}"   # Must succeed
    assert "submission accepted" in out   # Must confirm acceptance
    print(f"[ok] happy_path: client completed successfully")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> int:
    """
    Run all 7 failure-mode tests and report results.

    We run ALL tests even if some fail, then report a summary at the end.
    This is better than stopping at the first failure — you see ALL problems
    in one run rather than fixing one issue and discovering another.

    Returns 0 if all tests passed, 1 if any failed.
    """
    # List of all test functions to run (in order)
    tests = [
        test_immediate_disconnect,    # Server disconnects before saying anything
        test_send_error,              # Server sends ERROR immediately
        test_huge_line,               # Server sends 100KB without newline
        test_hang_after_helo,         # Server hangs after HELO (30s timeout test)
        test_command_before_pow,      # Server sends NAME before POW
        test_malformed_pow,           # Server sends malformed POW line
        test_happy_path,              # Normal successful session (sanity check)
    ]

    failed = 0   # Count of failed tests

    for t in tests:
        try:
            t()   # Run the test function
        except AssertionError as e:
            # An assert statement failed — the test found a bug
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            # An unexpected exception — could be a bug in the test itself
            print(f"[ERR ] {t.__name__}: {type(e).__name__}: {e}")
            failed += 1

    # Print summary: e.g. "7/7 failure-mode tests passed"
    print(f"\n{len(tests) - failed}/{len(tests)} failure-mode tests passed")

    return 1 if failed else 0   # Non-zero exit code if any test failed


# ── SCRIPT ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.exit(main())   # Exit with result code for regression.py to check
