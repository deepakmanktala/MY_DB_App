"""
================================================================================
FILE: system_test.py
PURPOSE: Full end-to-end test of the client against a REAL (but local) TLS server.

WHAT IS A SYSTEM TEST?
------------------------
A system test (also called an integration test) tests the WHOLE SYSTEM working
together, not just individual functions. Where smoke_test.py tests isolated
functions with fake inputs, system_test.py:

  1. Starts a REAL TLS server (running in a background thread on your machine)
  2. Runs the REAL client (exasol_client.py) as a subprocess
  3. Verifies the client and server communicate correctly end-to-end

This is the closest we can get to testing against the actual Exasol server
without actually connecting to the internet.

WHY A BACKGROUND THREAD FOR THE SERVER?
-----------------------------------------
The mock server must run SIMULTANEOUSLY with the client:
  - Server: waits for client to connect, then sends HELO, POW, questions, END
  - Client: connects, solves POW, sends answers, receives END

If we ran them sequentially, neither could complete (the server waits for a
client that hasn't started yet, or the client tries to connect to a server that
isn't running). Threading allows both to run in parallel.

WHAT THE MOCK SERVER DOES:
---------------------------
  1. Sends "HELO\n" → expects "TOAKUEI"
  2. Sends "POW <authdata> 3\n" (difficulty=3 for fast test, ~few ms)
  3. Validates the POW suffix is correct
  4. Asks all 10 personal-data questions in RANDOM ORDER (critical test!)
  5. Validates each response has the correct SHA-1 checksum and value
  6. Sends "END\n" → expects "OK"

WHY RANDOM ORDER?
------------------
The real Exasol server sends personal-data questions in an unpredictable order.
Our client must not assume they arrive in any particular sequence.
Shuffling them here proves the client handles any ordering correctly.

HOW TO RUN:
-----------
    python system_test.py

Takes ~1 second. Requires no network access (all traffic is localhost).
================================================================================
"""

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from __future__ import annotations   # Allow "type | None" syntax on Python 3.9

import hashlib      # SHA-1 for verifying POW solutions and response checksums
import os           # os.urandom() for random authdata bytes
import random       # random.shuffle() for randomizing question order
import socket       # Low-level TCP socket for the mock server
import ssl          # TLS wrapping for the mock server
import subprocess   # For running exasol_client.py as a separate process
import sys          # sys.executable and sys.exit()
import tempfile     # For creating temporary directories to store test files
import threading    # For running the mock server in a background thread
import time         # For timeouts
from pathlib import Path   # Cross-platform file paths

# Ensure THIS file's directory is on sys.path so we can import _test_certs
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Import functions that write the pre-generated test certificates to disk
from _test_certs import write_test_server_pem, write_test_client_pem


# ── TEST CERTIFICATE HELPERS ──────────────────────────────────────────────────

def make_test_certs(workdir: Path) -> tuple[Path, Path]:
    """
    Write the embedded mock server certificate and private key to disk files.

    The mock server needs a TLS certificate to accept HTTPS connections.
    We use pre-generated throwaway certificates stored in _test_certs.py
    (not the real challenge.pem — this is purely for local testing).

    Returns: (cert_path, key_path)
    """
    return write_test_server_pem(workdir)   # Writes server.crt and server.key to workdir


def make_client_certs(workdir: Path) -> Path:
    """
    Write the embedded mock client certificate+key combined PEM to disk.

    The client needs credentials to authenticate itself.
    For tests, we use a throwaway cert instead of the real challenge.pem.

    Returns: path to the combined client PEM file
    """
    return write_test_client_pem(workdir)   # Writes client.pem to workdir


# ── MOCK TLS SERVER ───────────────────────────────────────────────────────────

class MockServer:
    """
    A complete fake Exasol challenge server that runs in a background thread.

    This class:
      1. Sets up a real TLS server socket on localhost
      2. Waits for the client to connect
      3. Runs through the full Exasol protocol (HELO → POW → Q&A → END)
      4. Validates every response from the client
      5. Records the received values for the test to inspect afterwards

    The server and client run in parallel:
      - MockServer runs in a background thread (started by .start())
      - The real client runs as a subprocess (started by subprocess.run())
    """

    # The profile data the mock server "expects" the client to submit.
    # This must match the profile.json we write for the test.
    EXPECTED_PROFILE = {
        "NAME":      "System Test User",
        "MAIL1":     "test@example.com",
        "MAIL2":     "alt@example.com",
        "SKYPE":     "test.skype",
        "BIRTHDATE": "01.01.1990",
        "COUNTRY":   "Germany",
        "ADDR1":     "Test Street 1",
        "ADDR2":     "12345 Test City",
    }

    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self.host = host      # Only listen on localhost (127.0.0.1), not the network
        self.port = port      # 0 = let the OS pick a free port (avoids conflicts)
        self.actual_port: int | None = None   # Will be set after bind()
        self.thread: threading.Thread | None = None   # Background server thread
        self.error: Exception | None = None           # Any exception from the server thread
        self.completed = False    # Set to True when END handshake completes successfully

        # Create a temp directory to store test cert files
        self.workdir = Path(tempfile.mkdtemp(prefix="exasol-systest-"))

        # Write the mock server's TLS certificate and key to disk
        self.server_cert, self.server_key = make_test_certs(self.workdir)

        # Dictionary to record what the client actually sent for each command
        # e.g. {"NAME": "System Test User", "MAIL1": "test@example.com", ...}
        self.received_responses: dict[str, str] = {}

    def start(self) -> int:
        """
        Start the mock server in a background thread.

        We use a threading.Event() as a "ready signal":
          1. The thread starts and begins setting up the server
          2. When the server socket is bound and listening, it calls ready.set()
          3. start() blocks on ready.wait(5.0) — at most 5 seconds
          4. Once ready is set, start() returns the actual port number

        Returns: the port the server is listening on
        """
        ready = threading.Event()   # Create the ready signal (starts unset)

        def run():
            """The function that runs in the background thread."""
            try:
                self._run(ready)   # Run the actual server logic
            except Exception as e:
                self.error = e     # Save any exception so start() can re-raise it
                ready.set()        # Signal readiness even on error so start() doesn't hang

        # daemon=True means the thread dies automatically if the main process exits
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()   # Launch the background thread

        # Wait up to 5 seconds for the server to be ready
        if not ready.wait(5.0):
            raise RuntimeError("Mock server failed to start within 5s")

        if self.error:
            raise self.error   # Re-raise any server startup exception

        assert self.actual_port is not None   # Should be set by now
        return self.actual_port   # Return the port the client should connect to

    def _run(self, ready: threading.Event) -> None:
        """
        Set up the TLS server socket and accept one connection.

        This runs in the background thread. It creates a server socket,
        binds to localhost, waits for a client, and then handles the session.
        """
        # Create a TLS server context (server-side TLS settings)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # Load the mock server's certificate and private key
        ctx.load_cert_chain(certfile=str(self.server_cert), keyfile=str(self.server_key))
        # Note: we don't require client certs here — the real Exasol server does,
        # but for the test we use --insecure on the client side

        # Create a plain TCP socket
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR lets us reuse a port that was recently in use
        # (prevents "address already in use" errors when running tests rapidly)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))   # Bind to localhost on the chosen port
        srv.listen(1)                      # Accept 1 pending connection at a time

        # Record the actual port (OS may have assigned a random one if we passed 0)
        self.actual_port = srv.getsockname()[1]

        # Signal the main thread that we're ready to accept connections
        ready.set()

        # Wait up to 30 seconds for a client to connect
        srv.settimeout(30.0)
        try:
            client_sock, _ = srv.accept()   # Blocks until a client connects
        finally:
            srv.close()   # Close the listening socket — we only need one connection

        # Set a 60-second timeout on the client socket (the session shouldn't take longer)
        client_sock.settimeout(60.0)

        # Wrap the plain socket with TLS encryption (perform TLS handshake)
        with ctx.wrap_socket(client_sock, server_side=True) as tls:
            self._handle_session(tls)   # Run the Exasol protocol

        self.completed = True   # Mark session as successfully completed

    def _handle_session(self, tls: ssl.SSLSocket) -> None:
        """
        Run the full Exasol challenge protocol as the SERVER side.

        This is the mirror image of exasol_client.py — it sends commands
        and verifies responses rather than receiving commands and sending responses.
        """
        buf = b""   # Read-ahead buffer for the server's line reader

        def read_line() -> bytes:
            """Read one complete \n-terminated line from the client."""
            nonlocal buf   # Access the outer buf variable
            while b"\n" not in buf:   # Keep reading until we have a complete line
                chunk = tls.recv(4096)   # Receive up to 4096 bytes
                if not chunk:
                    raise ConnectionError("client disconnected")
                buf += chunk   # Append to buffer
            line, _, buf = buf.partition(b"\n")   # Split at first newline
            if line.endswith(b"\r"):
                line = line[:-1]   # Strip \r (Windows line endings)
            return line

        def write(data: bytes) -> None:
            """Send bytes to the client."""
            tls.sendall(data)   # sendall guarantees all bytes are sent

        # ── STEP 1: HELO handshake ────────────────────────────────────────────
        write(b"HELO\n")        # Server sends greeting
        resp = read_line()      # Client should respond
        assert resp == b"TOAKUEI", f"bad HELO response: {resp!r}"   # Verify magic word

        # ── STEP 2: POW challenge ─────────────────────────────────────────────
        # Generate random authdata using os.urandom() + hex encoding
        # This creates a unique session token for each test run
        authdata = b"mock-server-auth-" + os.urandom(8).hex().encode()

        difficulty = 3   # Very low difficulty — 16^3 = 4096 hashes, takes < 100ms
                         # (The real server uses difficulty 6-9 which takes hours)

        # Send the POW challenge line
        write(b"POW " + authdata + b" " + str(difficulty).encode() + b"\n")

        # Read the client's suffix solution
        suffix = read_line()

        # Verify the solution: SHA1(authdata + suffix) must start with 3 zeros
        digest = hashlib.sha1(authdata + suffix).hexdigest()
        assert digest.startswith("0" * difficulty), f"bad POW: {digest}"

        # ── STEP 3: Personal data Q&A in random order ─────────────────────────
        # Build the full list of commands and expected answers
        commands = [
            ("NAME",      self.EXPECTED_PROFILE["NAME"]),       # Full name
            ("MAILNUM",   "2"),                                  # Number of emails
            ("MAIL1",     self.EXPECTED_PROFILE["MAIL1"]),      # First email
            ("MAIL2",     self.EXPECTED_PROFILE["MAIL2"]),      # Second email
            ("SKYPE",     self.EXPECTED_PROFILE["SKYPE"]),      # Skype handle
            ("BIRTHDATE", self.EXPECTED_PROFILE["BIRTHDATE"]), # Date of birth
            ("COUNTRY",   self.EXPECTED_PROFILE["COUNTRY"]),   # Country name
            ("ADDRNUM",   "2"),                                  # Number of address lines
            ("ADDRLINE1", self.EXPECTED_PROFILE["ADDR1"]),     # First address line
            ("ADDRLINE2", self.EXPECTED_PROFILE["ADDR2"]),     # Second address line
        ]

        # Shuffle to a random order — proves the client doesn't assume fixed ordering
        random.shuffle(commands)

        for cmd, expected_value in commands:
            # Generate a unique random token for this specific question.
            # os.urandom(4).hex() gives 8 random hex characters like "a3f29c11"
            # This ensures each question has a unique "arg" token.
            arg = "arg" + os.urandom(4).hex()

            # Send the question: e.g. "NAME a3f29c11\n"
            write(f"{cmd} {arg}\n".encode())

            # Read the client's response: "<sha1hex> <value>"
            resp = read_line()

            # Split the response at the first space
            sha_part, _, value = resp.partition(b" ")

            # Compute what the checksum SHOULD be: SHA1(authdata + arg)
            expected_sha = hashlib.sha1(authdata + arg.encode()).hexdigest().encode()

            # Verify the checksum is correct
            assert sha_part == expected_sha, (
                f"{cmd}: bad checksum (got {sha_part}, expected {expected_sha})"
            )

            # Verify the value matches what we expected
            assert value.decode() == expected_value, (
                f"{cmd}: wrong value (got {value!r}, expected {expected_value!r})"
            )

            # Record the received response for post-test inspection
            self.received_responses[cmd] = value.decode()

        # ── STEP 4: END — confirm successful submission ───────────────────────
        write(b"END\n")       # Server tells client all data was received
        resp = read_line()    # Client should acknowledge with "OK"
        assert resp == b"OK", f"bad END response: {resp!r}"
        # Session complete — self.completed will be set True by _run()


# ── TEST RUNNER ───────────────────────────────────────────────────────────────

def main() -> int:
    """
    Orchestrate the full system test:
      1. Start mock server in background thread
      2. Create matching profile.json
      3. Run exasol_client.py as a subprocess against the mock server
      4. Verify both client and server report success
    """
    print("[systest] starting mock TLS server...")
    srv = MockServer()             # Create mock server object
    port = srv.start()             # Start it in background thread, get its port
    print(f"[systest] mock server listening on 127.0.0.1:{port}")

    # ── Create profile.json matching what the mock server expects ─────────────
    profile_path = srv.workdir / "profile.json"
    import json   # JSON writing for the profile file
    with open(profile_path, "w") as f:
        json.dump({
            "NAME":      srv.EXPECTED_PROFILE["NAME"],
            "MAILS":     [srv.EXPECTED_PROFILE["MAIL1"],
                          srv.EXPECTED_PROFILE["MAIL2"]],   # Both emails as a list
            "SKYPE":     srv.EXPECTED_PROFILE["SKYPE"],
            "BIRTHDATE": srv.EXPECTED_PROFILE["BIRTHDATE"],
            "COUNTRY":   srv.EXPECTED_PROFILE["COUNTRY"],
            "ADDRESS":   [srv.EXPECTED_PROFILE["ADDR1"],
                          srv.EXPECTED_PROFILE["ADDR2"]],  # Both address lines as a list
        }, f)

    # Write the mock client certificate to disk (used for TLS client auth)
    client_pem = make_client_certs(srv.workdir)

    print(f"[systest] running client against mock server...")

    # ── Run the REAL client as a subprocess ───────────────────────────────────
    # This is the production exasol_client.py code being tested end-to-end
    proc = subprocess.run(
        [
            sys.executable,                    # The current Python interpreter
            str(HERE / "exasol_client.py"),    # The client script to test
            "--cert",     str(client_pem),     # Client certificate for TLS auth
            "--key",      str(client_pem),     # Private key (same file as cert)
            "--insecure",                      # Skip verifying mock server's cert
                                               # (mock cert is self-signed, not from a real CA)
            "--profile",  str(profile_path),   # Personal answers
            "--host",     "127.0.0.1",         # Connect to localhost (not real server)
            "--port",     str(port),           # Use our mock server's port
            "--no-selftest",                   # Skip the 1-second self-test (already tested separately)
        ],
        capture_output=True,   # Capture all stdout and stderr
        text=True,             # Return output as text strings (not bytes)
        timeout=60,            # Fail if client doesn't finish within 60 seconds
    )

    # ── Print client output for debugging ─────────────────────────────────────
    print(f"\n[systest] client stdout:\n{proc.stdout}")
    if proc.stderr:
        print(f"\n[systest] client stderr:\n{proc.stderr}")
    print(f"[systest] client exit code: {proc.returncode}")

    # ── Wait for the server thread to finish ──────────────────────────────────
    # Give it up to 10 seconds to complete after the client disconnects
    if srv.thread is not None:
        srv.thread.join(timeout=10)

    # ── Verify both sides succeeded ───────────────────────────────────────────

    # Check: did the server thread crash with an exception?
    if srv.error:
        print(f"[systest] FAIL: server error: {srv.error}")
        return 1

    # Check: did the server complete the full session (reach the END handshake)?
    if not srv.completed:
        print(f"[systest] FAIL: server did not complete the session")
        return 1

    # Check: did the client exit with code 0 (success)?
    if proc.returncode != 0:
        print(f"[systest] FAIL: client exited {proc.returncode}")
        return 1

    # Check: did the client's stdout confirm the submission was accepted?
    if "submission accepted" not in proc.stdout:
        print(f"[systest] FAIL: client didn't acknowledge END")
        return 1

    # Print the verified data for human inspection
    print(f"[systest] received responses from client: {srv.received_responses}")
    print(f"[systest] PASS: full system test completed end-to-end")
    return 0   # Success


# ── SCRIPT ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.exit(main())   # Exit with 0 on success, 1 on failure
