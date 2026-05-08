"""
================================================================================
FILE: aggressive_test.py
PURPOSE: Test unusual/tricky network scenarios the client must handle correctly.

WHAT ARE "AGGRESSIVE" FAILURE TESTS?
--------------------------------------
While failure_test.py tests obvious server misbehaviors (disconnect, error, hang),
aggressive_test.py tests subtler network edge cases that happen in real-world
networks but are harder to reproduce:

  TEST 1 — Partial line then close:
    Server sends "POW partial-no-newline" WITHOUT a \n, then disconnects.
    This tests the buffer handling in LineConn.read_line() — what happens
    when the server sends incomplete data?

  TEST 2 — Pipelined commands (TCP coalescing):
    Server sends "HELO\n" and "POW auth 2\n" in ONE TCP packet.
    Normally each command arrives separately, but TCP is a byte stream —
    packets can be merged by the OS. This tests that our buffered line
    reader handles multiple commands arriving at once.

  TEST 3 — High-byte authdata:
    Server uses authdata containing bytes with values 0x80-0x8F (high-bit bytes).
    The real spec doesn't restrict authdata charset. Our code keeps authdata
    as bytes (never decodes it), so the SHA-1 checksum should be byte-exact.
    This verifies we don't accidentally corrupt high-bit bytes by decoding.

  TEST 4 — TCP RST after POW:
    Server sends HELO + POW, then immediately sends a TCP RESET (RST) signal
    instead of a normal close. RST is an abrupt connection termination that
    bypasses the normal TCP close handshake — simulating a server crash.
    Client should detect this and fail cleanly, not hang.

WHY USE SCRIPTEDSSERVER?
--------------------------
ScriptedServer executes a list of (action, payload) instructions:
  ("send", b"data")          → send bytes to the client
  ("expect", b"value")       → read a line and assert it equals value
  ("send_raw_then_rst", ...) → send bytes then force TCP RST
  ("sleep", seconds)         → wait N seconds
  ("close", None)            → close connection

This is more flexible than FailServer's hardcoded behaviors — we can script
any arbitrary sequence without writing a new class method.

HOW TO RUN:
-----------
    python aggressive_test.py

Takes ~5 seconds.
================================================================================
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from __future__ import annotations   # Allow "type | None" syntax on Python 3.9

import hashlib    # SHA-1 for verifying checksums in test 3
import os         # (available if needed in future tests)
import socket     # TCP socket for mock servers
import ssl        # TLS wrapping
import struct     # struct.pack() for SO_LINGER socket option in TCP RST test
import subprocess # Running exasol_client.py as a subprocess
import sys        # sys.executable and sys.exit()
import tempfile   # Temporary directories for test files
import threading  # Background server threads
import time       # time.sleep() for timing
from pathlib import Path   # Cross-platform paths

# Ensure this file's directory is on sys.path for _test_certs import
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Pre-generated throwaway TLS certificates for local testing
from _test_certs import write_test_server_pem, write_test_client_pem


# ── CERTIFICATE HELPERS ───────────────────────────────────────────────────────

def make_certs(workdir: Path) -> tuple[Path, Path]:
    """Write the mock server's TLS certificate and key to disk."""
    return write_test_server_pem(workdir)   # (cert_path, key_path)


def make_client_pem(workdir: Path) -> Path:
    """Write the mock client's combined cert+key PEM to disk."""
    return write_test_client_pem(workdir)   # combined PEM path


def make_profile(workdir: Path) -> Path:
    """
    Write a minimal valid profile.json.

    Content only matters for tests that reach the personal-data Q&A phase.
    For tests that fail earlier (partial line, RST), any valid profile works.
    """
    import json
    p = workdir / "profile.json"
    with open(p, "w") as f:
        json.dump({
            "NAME":      "Test User",          # Two-word name required
            "MAILS":     ["test@example.com"], # At least one email
            "SKYPE":     "N/A",
            "BIRTHDATE": "01.01.1990",
            "COUNTRY":   "Germany",
            "ADDRESS":   ["Line 1"],
        }, f)
    return p


# ── SCRIPTABLE MOCK SERVER ────────────────────────────────────────────────────

class ScriptedServer:
    """
    A flexible TLS server that executes a list of scripted instructions.

    Each instruction is a tuple: (action, payload)
    Actions:
        "send"              → tls.sendall(payload)  — send bytes to client
        "expect"            → read a line, assert it equals payload
        "send_raw_then_rst" → send payload, then force a TCP RST (abrupt close)
        "sleep"             → time.sleep(payload)
        "close"             → break the instruction loop (graceful close)

    This is more flexible than FailServer because tests can compose any
    sequence of actions without writing new server methods.
    """

    def __init__(self, script: list[tuple], workdir: Path):
        self.script = script      # List of (action, payload) tuples to execute
        self.workdir = workdir    # Where to write cert files
        self.cert, self.key = make_certs(workdir)   # Write TLS certs to disk
        self.port: int | None = None                # Set after bind()
        self.thread: threading.Thread | None = None # Background thread
        self.error: Exception | None = None         # Any exception from thread

    def start(self) -> int:
        """Start server in background thread, wait until ready, return port."""
        ready = threading.Event()   # Signal from thread when socket is ready

        def run():
            """Background thread body."""
            try:
                self._run(ready)
            except Exception as e:
                self.error = e     # Save exception for main thread
            finally:
                ready.set()        # Always signal — prevent main thread from hanging

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()   # Launch background thread

        if not ready.wait(5.0):
            raise RuntimeError("server didn't start")
        return self.port   # Return the OS-assigned port number

    def _run(self, ready: threading.Event) -> None:
        """Set up TLS server socket, signal ready, accept one client, run script."""
        # Create TLS server context with our mock certificate
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=str(self.cert), keyfile=str(self.key))

        # Create TCP socket
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # Allow port reuse
        srv.bind(("127.0.0.1", 0))   # Bind to OS-assigned free port on localhost
        srv.listen(1)                 # Accept one pending connection
        self.port = srv.getsockname()[1]   # Record actual port number
        ready.set()   # Signal main thread: server is now accepting connections

        # Wait for the client to connect (20 second timeout)
        srv.settimeout(20.0)
        client_sock, _ = srv.accept()   # Blocks until client connects
        srv.close()   # Close listening socket — only handle one connection

        # Wrap plain socket with TLS (perform TLS handshake with client)
        try:
            tls = ctx.wrap_socket(client_sock, server_side=True)
        except Exception:
            client_sock.close()   # TLS handshake failed — just close
            return

        # Read-ahead buffer for the server's line reader
        buf = b""

        def read_line():
            """Read one \n-terminated line from the client."""
            nonlocal buf
            while b"\n" not in buf:
                chunk = tls.recv(4096)
                if not chunk:
                    raise ConnectionError("client closed")
                buf += chunk
            line, _, buf = buf.partition(b"\n")
            return line.rstrip(b"\r")   # Strip \r (Windows line endings)

        try:
            # Execute each instruction in the script
            for action, payload in self.script:

                if action == "send":
                    # Send bytes to the client
                    tls.sendall(payload)

                elif action == "expect":
                    # Read a line from the client and verify it matches expected
                    got = read_line()
                    if got != payload:
                        raise AssertionError(f"expected {payload!r}, got {got!r}")

                elif action == "send_raw_then_rst":
                    # Send payload bytes, then force a TCP RST (abrupt connection termination).
                    #
                    # WHAT IS TCP RST?
                    # Normal TCP close: both sides send FIN packets politely
                    # TCP RST: one side immediately drops the connection, discarding
                    #          any unread data. This is what happens when a server crashes.
                    #
                    # HOW SO_LINGER FORCES RST:
                    # socket.SO_LINGER with l_onoff=1 (enabled) and l_linger=0 (zero timeout)
                    # tells the OS: "when this socket is closed, don't send FIN — send RST"
                    # struct.pack("ii", 1, 0) encodes linger_on=1, linger_time=0 as two ints
                    tls.sendall(payload)   # Send the payload first
                    sock = tls.unwrap()    # Unwrap TLS to access the raw TCP socket
                    # Set SO_LINGER: enabled=1, timeout=0 → force RST on close
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                                    struct.pack("ii", 1, 0))
                    sock.close()   # This sends RST instead of FIN
                    return   # Script is done — connection forcibly terminated

                elif action == "sleep":
                    # Wait N seconds (payload is a float number of seconds)
                    time.sleep(payload)

                elif action == "close":
                    # End the script and close normally
                    break

        finally:
            try:
                tls.close()   # Close TLS connection (sends proper FIN)
            except Exception:
                pass   # Ignore errors during cleanup


# ── CLIENT RUNNER ─────────────────────────────────────────────────────────────

def run_client(workdir: Path, port: int, timeout: float = 30) -> tuple[int, str, str]:
    """
    Run exasol_client.py as a subprocess against the mock server.

    Returns: (exit_code, stdout, stderr)
    """
    profile = make_profile(workdir)      # Create profile.json
    client_pem = make_client_pem(workdir)   # Create client TLS cert

    proc = subprocess.run(
        [sys.executable, str(HERE / "exasol_client.py"),
         "--cert",    str(client_pem),   # Client certificate
         "--key",     str(client_pem),   # Private key
         "--insecure",                   # Don't verify mock server's cert
         "--profile", str(profile),      # Personal answers
         "--host",    "127.0.0.1",       # Localhost only
         "--port",    str(port),         # Our mock server port
         "--no-selftest"],               # Skip solver self-test
        capture_output=True,   # Capture output
        text=True,             # Return as text
        timeout=timeout,       # Kill if takes too long
    )
    return proc.returncode, proc.stdout, proc.stderr


# ── TEST 1: Partial line then server close ────────────────────────────────────

def test_partial_line_then_close():
    """
    SCENARIO: Server sends "POW partial-no-newline-no-diff" WITHOUT a newline,
    then closes the connection.

    WHAT HAPPENS IN LineConn.read_line():
    ----------------------------------------
    1. recv(4096) returns b"POW partial-no-newline-no-diff" (no \n)
    2. The while loop continues (b"\n" not in buf)
    3. Next recv(4096) returns b"" (empty = connection closed)
    4. We raise ConnectionError("Server closed connection mid-line")
    5. run_session catches this as TransientError
    6. All ports exhausted → exit non-zero

    WHY THIS MATTERS:
    Without the empty-recv check in read_line(), we'd loop forever trying to
    receive from a closed connection. The check `if not chunk: raise ConnectionError`
    handles this gracefully.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ftf1-"))

    # Script: send HELO normally, read TOAKUEI, then send incomplete POW (no \n), close
    srv = ScriptedServer([
        ("send",   b"HELO\n"),           # Normal HELO
        ("expect", b"TOAKUEI"),          # Read and verify client's response
        ("send",   b"POW partial-no-newline-no-diff"),  # No \n at end!
        ("close",  None),                # Close connection — client sees EOF
    ], workdir)

    port = srv.start()   # Start server in background thread
    code, _, err = run_client(workdir, port, timeout=15)   # Run client

    assert code != 0, f"expected fail, got {code}"   # Client must fail
    print(f"[ok] partial_line: client failed cleanly, exit={code}")


# ── TEST 2: Pipelined commands (TCP coalescing) ────────────────────────────────

def test_pipelined_commands():
    """
    SCENARIO: Server sends HELO and POW in a single TCP packet.

    WHAT IS TCP COALESCING?
    -----------------------
    TCP is a BYTE STREAM, not a message stream. When you call sendall() twice
    quickly, the OS might merge both calls into one packet:
        sendall(b"HELO\n")            →
        sendall(b"POW auth 2\n")      →   One TCP packet: b"HELO\nPOW auth 2\n"

    This happens because of Nagle's algorithm — TCP buffers small sends to
    reduce network overhead.

    WHY THIS COULD BE A BUG:
    If our read_line() only called recv() once and processed one line, it
    would miss the second line. The second call to read_line() would then
    block waiting for data that's already in the OS buffer but not in our
    Python-level read buffer.

    HOW OUR CODE HANDLES IT:
    LineConn has a self.buf buffer. After reading "HELO\nPOW auth 2\n" in
    one recv() call, it partitions at the first \n, returns "HELO", and
    stores "POW auth 2\n" in self.buf. The next read_line() call finds \n
    in self.buf immediately without any recv() — correctly returning "POW auth 2".

    This test sends HELO + POW concatenated in ONE sendall() call to simulate
    TCP coalescing, then verifies the client handles it correctly.

    SPECIAL IMPLEMENTATION NOTE:
    This test needs to fully participate in the protocol (read TOAKUEI,
    verify POW, send questions, send END). The ScriptedServer infrastructure
    is simpler but doesn't do POW verification. So we write the server inline
    with a manual threading.Thread for full control.
    """
    workdir2 = Path(tempfile.mkdtemp(prefix="ftf2b-"))   # Temp dir for this test
    cert, key = make_certs(workdir2)   # Write test TLS certs

    authdata = b"pipelined-auth-12345"   # Fixed authdata for this test

    ready = threading.Event()   # Signal when server is accepting connections
    port_box = []               # Mutable container to pass port from thread to main
    err_box = []                # Container to pass any server exception to main

    def server():
        """The pipelined-commands mock server, running in a background thread."""
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))

            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))    # OS assigns port
            sock.listen(1)
            port_box.append(sock.getsockname()[1])   # Save port for main thread
            ready.set()   # Signal: server is now accepting connections

            sock.settimeout(15)
            client, _ = sock.accept()   # Wait for client
            sock.close()

            with ctx.wrap_socket(client, server_side=True) as tls:
                # ── THE KEY TEST: Send HELO + POW as one concatenated packet ──
                # tls.sendall sends both lines in one call.
                # At the TCP level this LIKELY arrives as one packet (coalesced).
                # Our client's LineConn must buffer correctly and return each line
                # separately despite receiving them together.
                tls.sendall(b"HELO\nPOW " + authdata + b" 2\n")

                # Now read the client's responses (these arrive separately)
                buf = b""

                # Helper: read one line from the buffer
                def readln():
                    nonlocal buf
                    while b"\n" not in buf:
                        buf += tls.recv(4096)
                    line, _, buf = buf.partition(b"\n")
                    return line.rstrip(b"\r")

                # Read "TOAKUEI" — client's response to HELO
                line1 = readln()
                assert line1 == b"TOAKUEI"   # Verify correct greeting response

                # Read the POW suffix — client's response to the POW challenge
                line2 = readln()
                suffix = line2   # The suffix bytes

                # Verify the suffix actually solves the POW (difficulty=2)
                d = hashlib.sha1(authdata + suffix).hexdigest()
                assert d.startswith("00")   # Must start with 2 zero hex chars

                # Ask one personal-data question to confirm the session continues
                tls.sendall(b"NAME q\n")
                line3 = readln()
                # Verify the response contains " Test User" (from profile.json)
                assert b" Test User" in line3

                # Send END to complete the session
                tls.sendall(b"END\n")
                line4 = readln()
                assert line4 == b"OK"   # Client must acknowledge END

        except Exception as e:
            err_box.append(e)   # Save any exception for main thread to check

    # Start the server thread
    t = threading.Thread(target=server, daemon=True)
    t.start()
    ready.wait(5)   # Wait for server to be ready

    # Run the client against this server
    code, out, err = run_client(workdir2, port_box[0], timeout=15)

    t.join(timeout=10)   # Wait for server thread to finish

    if err_box:
        raise err_box[0]   # Re-raise any server-side assertion failure

    assert code == 0, f"expected success, got {code}; stderr={err}"
    print(f"[ok] pipelined_commands: client handled coalesced HELO+POW correctly")


# ── TEST 3: High-bit bytes in authdata ────────────────────────────────────────

def test_authdata_with_special_bytes():
    """
    SCENARIO: Server uses authdata containing bytes with values >= 128 (0x80+).

    WHY THIS MATTERS:
    -----------------
    In Python, bytes are just integers 0-255. Text is Unicode strings.
    If code accidentally does authdata.decode('utf-8') with high-bit bytes,
    it would raise UnicodeDecodeError (bytes 0x80-0x8F are invalid UTF-8).

    Our code keeps authdata as raw bytes throughout and NEVER decodes it.
    This test verifies that invariant:
      1. The POW is solved using the raw bytes (hashlib handles bytes directly)
      2. The checksums for personal-data responses use the raw bytes
      3. No decode() error is raised anywhere

    The authdata bytes(range(0x80, 0x90)) + b"abcd" are deliberately chosen
    to be invalid UTF-8, ensuring any accidental decode would fail loudly.

    We also verify there are no whitespace bytes in the authdata — because
    our tokeniser splits on whitespace, and authdata appears as a token in
    the POW line. The server would need to ensure this too.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ftf3-"))
    cert, key = make_certs(workdir)

    # Create authdata with high-bit bytes (0x80-0x8F) + normal ASCII
    # bytes(range(0x80, 0x90)) = b'\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f'
    authdata = bytes(range(0x80, 0x90)) + b"abcd"

    # Safety check: none of these bytes should be whitespace (would break protocol parsing)
    # Checking: space=0x20, tab=0x09, newline=0x0a, carriage return=0x0d
    assert not any(b in authdata for b in (0x20, 0x09, 0x0a, 0x0d))

    ready = threading.Event()   # Server ready signal
    port_box = []               # Port number from server thread
    err_box = []                # Exceptions from server thread

    def server():
        """Mock server that uses high-bit-byte authdata."""
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            port_box.append(sock.getsockname()[1])
            ready.set()
            sock.settimeout(15)
            client, _ = sock.accept()
            sock.close()
            with ctx.wrap_socket(client, server_side=True) as tls:
                buf = b""

                def readln():
                    """Read one line from the client."""
                    nonlocal buf
                    while b"\n" not in buf:
                        buf += tls.recv(4096)
                    line, _, buf = buf.partition(b"\n")
                    return line.rstrip(b"\r")

                tls.sendall(b"HELO\n")
                assert readln() == b"TOAKUEI"   # Verify greeting

                # Send POW with high-bit-byte authdata
                # Note: authdata is sent as raw bytes — the server concatenates it directly
                tls.sendall(b"POW " + authdata + b" 2\n")
                suffix = readln()   # Read POW solution suffix

                # Verify POW using raw bytes — hashlib takes bytes directly
                d = hashlib.sha1(authdata + suffix).hexdigest()
                assert d.startswith("00"), f"bad: {d}"

                # Ask NAME question
                tls.sendall(b"NAME q\n")
                resp = readln()   # Client's checksummed response

                # Verify the checksum was computed over raw authdata bytes + b"q"
                # If client had decoded authdata, the checksum would be wrong here
                expected = hashlib.sha1(authdata + b"q").hexdigest()
                assert resp.startswith(expected.encode()), f"bad checksum: {resp[:50]}"

                # Complete the session
                tls.sendall(b"END\n")
                readln()   # Read "OK"

        except Exception as e:
            err_box.append(e)

    t = threading.Thread(target=server, daemon=True)
    t.start()
    ready.wait(5)

    code, _, err = run_client(workdir, port_box[0], timeout=15)
    t.join(timeout=10)

    if err_box:
        raise err_box[0]   # Re-raise any server assertion failure

    assert code == 0, f"failed: code={code}, stderr={err}"
    print(f"[ok] authdata_with_special_bytes: high-bit authdata handled correctly")


# ── TEST 4: TCP RST after POW ─────────────────────────────────────────────────

def test_truncated_reply_during_pow():
    """
    SCENARIO: Server sends HELO + POW, then immediately forces a TCP RST.

    WHAT IS TCP RST?
    ----------------
    Normally, closing a TCP connection sends FIN packets back and forth
    (a polite goodbye). TCP RST (Reset) is an abrupt termination — the OS
    immediately discards the connection, and the other side gets an error
    on their next read/write.

    This simulates:
    - Server process crashing mid-session
    - Network equipment forcibly dropping the connection
    - Server hitting an internal error after sending POW

    WHAT HAPPENS IN OUR CLIENT:
    1. Client receives HELO and POW successfully
    2. Client starts solving the POW (this takes ~1-100ms at difficulty=2)
    3. Meanwhile, server sends TCP RST
    4. When client calls conn.write(suffix + b"\n") to send the solution...
       OR when client calls conn.read_line() to read the next command...
       ...it gets ConnectionResetError (or BrokenPipeError on some systems)
    5. run_session catches this as TransientError
    6. All ports exhausted → exit non-zero

    HOW WE FORCE RST:
    socket.SO_LINGER with l_onoff=1 and l_linger=0 tells the OS:
    "On close(), don't perform graceful shutdown — send RST immediately"
    struct.pack("ii", 1, 0) packs two C ints: linger_on=1, linger_time=0

    The time.sleep(0.5) gives the client time to receive the POW line
    and start solving before we send the RST. Without it, the RST might
    arrive before POW and be caught at a different point.
    """
    workdir = Path(tempfile.mkdtemp(prefix="ftf4-"))
    cert, key = make_certs(workdir)

    ready = threading.Event()   # Server ready signal
    port_box = []               # Port from server thread

    def server():
        """Server that sends HELO+POW then forces TCP RST."""
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        port_box.append(sock.getsockname()[1])
        ready.set()   # Signal: server is ready

        sock.settimeout(15)
        client, _ = sock.accept()   # Accept client connection
        sock.close()

        try:
            tls = ctx.wrap_socket(client, server_side=True)   # TLS handshake

            # Send HELO
            tls.sendall(b"HELO\n")

            # Read TOAKUEI (client's greeting response)
            buf = b""
            while b"\n" not in buf:
                buf += tls.recv(4096)

            # Send POW at very low difficulty (2) so client can solve it quickly
            tls.sendall(b"POW someauth 2\n")

            # Wait 0.5 seconds to let the client receive POW and start solving
            time.sleep(0.5)

            # Now force TCP RST (abrupt connection termination)
            # tls.unwrap() removes the TLS layer and returns the underlying raw socket
            sock_inner = tls.unwrap()
            # SO_LINGER with timeout=0 → close() sends RST instead of FIN
            sock_inner.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                                  struct.pack("ii", 1, 0))
            sock_inner.close()   # This sends RST — client will get ConnectionResetError

        except Exception:
            pass   # Any exception during cleanup is fine

    t = threading.Thread(target=server, daemon=True)
    t.start()
    ready.wait(5)   # Wait for server to be ready

    # Run client — it should fail because the connection is reset
    code, _, err = run_client(workdir, port_box[0], timeout=20)
    t.join(timeout=10)

    assert code != 0, f"expected fail, got {code}"   # Client must detect the RST and fail
    print(f"[ok] truncated_reply: client failed cleanly after RST, exit={code}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> int:
    """
    Run all 4 aggressive failure tests and report results.

    Same structure as failure_test.py: run ALL tests, collect failures,
    print summary, return exit code.
    """
    tests = [
        test_partial_line_then_close,         # Server sends partial line then closes
        test_pipelined_commands,              # Server pipelines HELO+POW in one packet
        test_authdata_with_special_bytes,     # Server uses high-bit-byte authdata
        test_truncated_reply_during_pow,      # Server sends TCP RST after POW
    ]

    failed = 0   # Count of failed tests

    for t in tests:
        try:
            t()   # Run each test
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERR ] {t.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()   # Print full traceback for debugging
            failed += 1

    # Summary line: e.g. "4/4 aggressive failure tests passed"
    print(f"\n{len(tests)-failed}/{len(tests)} aggressive failure tests passed")
    return 1 if failed else 0   # Non-zero exit code if any test failed


# ── SCRIPT ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.exit(main())   # Exit with result code
