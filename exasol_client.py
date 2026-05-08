"""
================================================================================
FILE: exasol_client.py
PURPOSE: The MAIN program that talks to the Exasol challenge server.

WHAT THIS ASSIGNMENT IS ABOUT (Plain English):
----------------------------------------------
Exasol (a database company) runs a hiring challenge.
To apply for a job, you must:

  STEP 1 — PROVE YOU ARE HUMAN / CAPABLE (Proof of Work):
    The server gives you a random string (called "authdata") and a number
    called "difficulty". Your job is to find another short string (called
    "suffix") such that when you stick them together and run SHA-1 hashing
    on them, the result starts with that many zeros.

    Example: difficulty=6 means SHA1("authdata" + "yoursuffix") must start
    with "000000". The ONLY way to find this is by trying millions of random
    suffixes until one works. This is intentionally hard (like Bitcoin mining).

  STEP 2 — PROVE WHO YOU ARE (Personal Data Handshake):
    After solving the puzzle, the server asks you for your name, email,
    date of birth, country, address, and Skype. But it doesn't just ask
    plainly — each question comes with a random "arg" token, and you must
    reply with SHA1(authdata + arg) + " " + your_answer. This proves your
    answers are fresh (can't be copy-pasted from someone else's session).

  STEP 3 — SERVER CONFIRMS:
    If everything is correct, the server sends "END" and your application
    is recorded in their database.

HOW TLS (Security) WORKS HERE:
--------------------------------
The connection uses TLS — the same security as HTTPS in your browser.
You have a certificate (challenge.pem) that acts like a digital ID card.
The server checks it to confirm you are the registered applicant.
Without this certificate, the server won't even talk to you.

HOW TO RUN:
-----------
    python exasol_client.py --pem challenge.pem --profile profile.json

    Add --verbose to see every single message sent and received.
================================================================================
"""

# ── PYTHON STANDARD LIBRARY IMPORTS ──────────────────────────────────────────
from __future__ import annotations   # Allows "type | None" syntax on Python 3.9

import argparse    # Parses command-line arguments like --pem, --profile, --verbose
import hashlib     # Provides SHA-1 hashing — the core cryptographic function used
import json        # Reads the profile.json file (your personal answers)
import socket      # Low-level network connection (TCP/IP)
import ssl         # Wraps the TCP connection with TLS encryption (HTTPS-style)
import sys         # Access to stdout/stderr and sys.exit()
import time        # Used for timing the POW solve and progress display
from pathlib import Path  # Cross-platform file path handling (works on Win/Mac/Linux)

# ── OUR OWN MODULE ────────────────────────────────────────────────────────────
from pow_solver import solve_pow   # Import the parallel SHA-1 brute-force engine


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

# The IP address of Exasol's challenge server (never changes)
DEFAULT_HOST = "18.202.148.130"

# Exasol runs their server on 6 different ports in case one is blocked by a
# firewall. We try each one in order until we get a connection.
DEFAULT_PORTS = (3336, 8083, 8446, 49155, 3481, 65532)

# These are the keys we expect to find in your profile.json file.
# If any is missing, we catch it BEFORE connecting — not 90 minutes into a
# long POW solve.
REQUIRED_PROFILE_KEYS = ("NAME", "MAILS", "SKYPE", "BIRTHDATE", "COUNTRY", "ADDRESS")


# ── SHA-1 HELPER ──────────────────────────────────────────────────────────────

def sha1_hex(data: bytes) -> str:
    """
    Run SHA-1 on raw bytes and return the result as a 40-character hex string.

    SHA-1 is a "hash function" — it takes any amount of data and produces a
    fixed-size 160-bit (40 hex char) fingerprint. Even a tiny change in the
    input completely changes the output, so it cannot be reverse-engineered.

    Example:
        sha1_hex(b"hello") -> "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d"
    """
    return hashlib.sha1(data).hexdigest()


def build_response(authdata: bytes, arg1: bytes, value: str) -> bytes:
    """
    Build one checksummed answer line to send to the server.

    The server doesn't just accept plain answers. For each question, it sends
    a random "arg" token (like "fjxi"). You must prove the answer is fresh by
    prepending SHA1(authdata + arg) as a checksum.

    So if the server says: NAME fjxi
    You reply:             562ba351... Deepak Manktala

    The checksum proves:
      - You solved the POW (only you know the authdata from this session)
      - This answer is from THIS session (not replayed from another user)

    Output format:  "<40-char-sha1-hex> <your answer>\n"

    `arg1` stays as raw bytes — we never decode it to avoid accidentally
    changing its content.
    """
    checksum = sha1_hex(authdata + arg1)         # SHA1 of session_token + question_token
    return f"{checksum} {value}\n".encode("utf-8")  # Format as bytes for the network


# ── VERBOSE LOGGING (--verbose flag) ─────────────────────────────────────────

# Global flag — True when user passes --verbose on the command line
_VERBOSE = False

# Global session start time — used to show elapsed time in verbose output
_T0: float = 0.0


def _vlog(direction: str, data: bytes) -> None:
    """
    Print one line of raw network traffic when --verbose mode is active.

    This is purely for human debugging — it shows every message sent and
    received, with a timestamp. Has no effect on the actual protocol.

    direction: "send" means we sent it, "recv" means server sent it.
    data:      the raw bytes that went over the wire.
    """
    if not _VERBOSE:
        return   # Skip entirely if verbose mode is off

    elapsed = time.monotonic() - _T0   # Seconds since session started
    # Decode bytes to a printable string; replace any undecodable bytes with ?
    text = data.rstrip(b"\n").decode("utf-8", errors="replace")
    # Cap display at 120 chars — POW authdata is 64 chars and fits fine
    display = text if len(text) <= 120 else text[:117] + "..."
    # Build the arrow and label depending on direction
    arrow = "  >>>  " if direction == "send" else "  <<<  "
    side  = "CLIENT " if direction == "send" else "SERVER "
    # Print: [timestamp]  CLIENT >>>  TOAKUEI
    print(f"  [{elapsed:6.2f}s] {side}{arrow}{display}")


# ── LINE-ORIENTED NETWORK CONNECTION ─────────────────────────────────────────

class LineConn:
    """
    A wrapper around a TLS socket that speaks line-by-line.

    The Exasol protocol is "line-oriented" — every message ends with a newline
    character (\n). This class hides the low-level socket details and lets the
    rest of the code just call read_line() and write() without worrying about
    partial reads, buffering, or byte boundaries.

    Why we need a buffer:
        TCP can deliver data in chunks that don't align with message boundaries.
        For example, the server might send "HELO\nPOW auth" in one TCP packet.
        We'd read "HELO\nPOW auth" but should only return "HELO" on the first
        call. The remaining "POW auth" stays in self.buf for the next call.
    """

    # Safety limit: if a server sends 65536 bytes without a newline, something
    # is very wrong (attack or bug). We abort rather than let memory grow forever.
    MAX_LINE_BYTES = 65536

    def __init__(self, sock: ssl.SSLSocket) -> None:
        self.sock = sock    # The encrypted TLS socket
        self.buf = b""      # Internal read-ahead buffer (starts empty)

    def read_line(self, timeout: float | None = None) -> bytes:
        """
        Read and return the next complete line from the server (without the \n).

        Blocks until a full line arrives. If the buffer already has a full line
        from a previous recv() call, returns it immediately without going to the
        network.

        timeout: how many seconds to wait before giving up (raises socket.timeout)
        """
        if timeout is not None:
            self.sock.settimeout(timeout)   # Apply read deadline to the socket

        # Keep receiving from the network until we have a complete line in buffer
        while b"\n" not in self.buf:
            # Safety check: abort if line is growing too large (memory protection)
            if len(self.buf) > self.MAX_LINE_BYTES:
                raise ConnectionError(
                    f"line exceeded {self.MAX_LINE_BYTES} bytes without newline; "
                    "aborting to avoid unbounded memory use"
                )
            # Ask the OS for up to 4096 bytes from the encrypted socket
            chunk = self.sock.recv(4096)
            if not chunk:
                # Empty recv means the server closed the connection mid-message
                raise ConnectionError("Server closed connection mid-line.")
            self.buf += chunk   # Append new bytes to our internal buffer

        # Split buffer at the first newline: line gets everything before it,
        # self.buf keeps everything after it (for the next read_line call)
        line, _, self.buf = self.buf.partition(b"\n")

        # Some systems add \r before \n (Windows-style line endings).
        # Strip it defensively even though the protocol says \n only.
        if line.endswith(b"\r"):
            line = line[:-1]

        _vlog("recv", line + b"\n")   # Show in verbose mode
        return line

    def write(self, data: bytes) -> None:
        """
        Send bytes to the server.

        sendall() guarantees ALL bytes are sent (unlike send() which may send
        only part of them). The TLS layer encrypts them before they leave your
        machine.
        """
        _vlog("send", data)        # Show in verbose mode
        self.sock.sendall(data)    # Send every byte, encrypted over TLS

    def close(self) -> None:
        """
        Cleanly close the TLS connection.

        We try to do a proper TLS shutdown (sends a "close_notify" alert to
        the server), then close the underlying TCP socket. Errors are ignored
        because we call this in finally blocks where the socket might already
        be broken.
        """
        try:
            try:
                # Tell the server we're done (graceful TLS shutdown)
                self.sock.shutdown(socket.SHUT_RDWR)
            except (OSError, ssl.SSLError):
                pass   # Already closed or broken — that's fine
            self.sock.close()    # Release the OS file descriptor
        except Exception:
            pass   # Never raise in close() — we're cleaning up


# ── TLS CONNECTION SETUP ──────────────────────────────────────────────────────

def make_tls_socket(
    host: str,
    port: int,
    cert: str,
    key: str,
    ca: str | None,
    connect_timeout: float = 15.0,
) -> ssl.SSLSocket:
    """
    Open an encrypted TLS connection to the Exasol server.

    TLS (Transport Layer Security) is the same encryption used by HTTPS.
    It ensures:
      1. All data is encrypted in transit (nobody can sniff your credentials)
      2. You prove your identity to the server using your certificate

    Parameters:
        host: IP address or hostname of the server
        port: TCP port number to connect to
        cert: Path to your client certificate file (proves who you are)
        key:  Path to your private key file (proves you own the certificate)
        ca:   Optional path to the CA certificate (verifies the SERVER's identity)
        connect_timeout: Seconds to wait for the initial TCP connection

    Why check_hostname=False?
        The server's certificate says "exatest.dynu.net" but we connect to an
        IP address (18.202.148.130). Python's TLS library would normally reject
        this mismatch. We disable that specific check but still verify the cert
        chain if --ca is provided.
    """
    # Create a fresh TLS configuration (like a settings object)
    ctx = ssl.create_default_context()

    # Disable hostname matching — server cert says "exatest.dynu.net" but
    # we connect by IP. This is intentional — see docstring above.
    ctx.check_hostname = False

    if ca:
        # Load the CA certificate so Python can verify the server is genuine
        ctx.load_verify_locations(cafile=ca)
        ctx.verify_mode = ssl.CERT_REQUIRED   # Fail if server cert is invalid
    else:
        # No CA provided — skip server verification entirely.
        # Our client cert still authenticates US to the server.
        ctx.verify_mode = ssl.CERT_NONE

    # Load YOUR certificate and private key — this proves to the server that
    # you are the registered applicant (not someone else)
    ctx.load_cert_chain(certfile=cert, keyfile=key)

    # Step 1: Open a plain TCP connection to the server (no encryption yet)
    raw = socket.create_connection((host, port), timeout=connect_timeout)

    # Step 2: Wrap the plain connection with TLS encryption.
    # This performs the TLS handshake — server and client exchange keys,
    # verify certificates, and agree on an encryption algorithm.
    return ctx.wrap_socket(raw, server_hostname=host)


# ── PROFILE VALIDATION ────────────────────────────────────────────────────────

def _validate_profile_string(label: str, value: str) -> None:
    """
    Validate that a profile field is a safe, non-empty string.

    WHY WE VALIDATE:
    The protocol is "line-oriented" — each message ends at a newline (\n).
    If your name or address accidentally contained a newline character, it
    would break the protocol framing and confuse the server. We catch this
    before connecting so you get a clear error message, not a mysterious failure.

    WHAT WE REJECT:
    - Non-string values (e.g. a number where a string is expected)
    - Empty or whitespace-only strings
    - Any ASCII control characters (invisible chars like newline, tab, NUL, etc.)

    WHAT WE ALLOW:
    - Normal letters (including international: é, ü, 你好, etc.)
    - Numbers, punctuation, spaces within values
    - Emoji (if your name contains one, we won't stop you)
    """
    # Ensure it's actually a string — not a number or None from bad JSON
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string, got {type(value).__name__}")

    # Reject empty strings or strings that are only spaces/tabs
    if not value.strip():
        raise ValueError(f"{label} must be non-empty")

    # Check every character for dangerous control characters.
    # ord(ch) gives the Unicode code point number.
    # Control characters are 0x00-0x1F (e.g. \n=10, \r=13, \t=9, \0=0)
    # and DEL is 0x7F. All of these could corrupt the line-based protocol.
    for ch in value:
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            raise ValueError(
                f"{label} contains control character U+{ord(ch):04X} "
                f"which is not safe for the line-oriented protocol"
            )


def load_profile(path: str) -> dict:
    """
    Read and validate your profile.json file.

    profile.json contains your personal answers that will be submitted to
    Exasol as part of your job application. We validate everything here,
    BEFORE making any network connection, so a typo doesn't waste 90 minutes
    of POW solving time.

    Returns the profile as a Python dictionary if valid.
    Raises ValueError with a clear message if anything is wrong.
    """
    # Open the file and parse it as JSON into a Python dictionary
    with open(path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    # JSON could be a list, string, etc. — we need an object (dict)
    if not isinstance(profile, dict):
        raise ValueError("profile must be a JSON object")

    # Check that all required fields are present
    missing = [k for k in REQUIRED_PROFILE_KEYS if k not in profile]
    if missing:
        raise ValueError(f"profile missing required keys: {missing}")

    # Validate the simple string fields (must be non-empty, no control chars)
    for k in ("NAME", "SKYPE", "BIRTHDATE", "COUNTRY"):
        _validate_profile_string(f"profile.{k}", profile[k])

    # NAME must have at least two words (first name AND last name).
    # The server spec explicitly requires "first and last name separated by space".
    if len(profile["NAME"].split()) < 2:
        raise ValueError("profile.NAME must contain first AND last name separated by space")

    # MAILS and ADDRESS must be non-empty lists of valid strings
    for k in ("MAILS", "ADDRESS"):
        v = profile[k]
        # Must be a list AND must have at least one item
        if not isinstance(v, list) or not v:
            raise ValueError(f"profile.{k} must be a non-empty list")
        # Validate each item in the list individually
        for i, item in enumerate(v):
            _validate_profile_string(f"profile.{k}[{i}]", item)

    return profile   # All checks passed — return the validated profile dict


def answer_for(cmd: str, profile: dict) -> str:
    """
    Look up the correct answer for a given server command.

    The server sends commands in random order (NAME, MAIL1, COUNTRY, etc.)
    This function maps each command name to the right value from your profile.

    Examples:
        "NAME"      -> "Deepak Manktala"
        "MAILNUM"   -> "1"          (how many email addresses)
        "MAIL1"     -> "deepak@..."  (first email, index 1-based)
        "ADDRNUM"   -> "2"          (how many address lines)
        "ADDRLINE1" -> "B2211, M Block..."
    """
    if cmd == "NAME":
        return profile["NAME"]   # Your full name

    if cmd == "MAILNUM":
        # Tell the server how many email addresses you're providing
        return str(len(profile["MAILS"]))

    # MAIL1, MAIL2, MAIL3... — server asks for each email by 1-based index
    if cmd.startswith("MAIL") and cmd[4:].isdigit():
        idx = int(cmd[4:]) - 1    # Convert "MAIL1" -> index 0, "MAIL2" -> index 1
        if 0 <= idx < len(profile["MAILS"]):
            return profile["MAILS"][idx]
        raise RuntimeError(f"server requested {cmd} but profile only has {len(profile['MAILS'])} mails")

    if cmd == "SKYPE":
        # Return Skype handle, or "N/A" if not set (per the spec)
        return profile.get("SKYPE", "N/A")

    if cmd == "BIRTHDATE":
        return profile["BIRTHDATE"]   # Format: dd.mm.yyyy

    if cmd == "COUNTRY":
        return profile["COUNTRY"]   # Must match official country name list

    if cmd == "ADDRNUM":
        # Tell the server how many address lines you're providing
        return str(len(profile["ADDRESS"]))

    # ADDRLINE1, ADDRLINE2... — server asks for each address line by 1-based index
    if cmd.startswith("ADDRLINE") and cmd[8:].isdigit():
        idx = int(cmd[8:]) - 1   # Convert "ADDRLINE1" -> index 0
        if 0 <= idx < len(profile["ADDRESS"]):
            return profile["ADDRESS"][idx]
        raise RuntimeError(f"server requested {cmd} but profile only has {len(profile['ADDRESS'])} address lines")

    # If we get here, the server sent a command we don't recognise
    raise RuntimeError(f"Unknown server command: {cmd!r}")


# ── ERROR TYPES ───────────────────────────────────────────────────────────────

class ProtocolError(Exception):
    """
    Raised when the SERVER rejects us or sends something invalid.

    This is a PERMANENT failure — retrying on a different port won't help
    because the server's objection is about our DATA (bad answers, wrong
    format), not the network connection.

    Examples: server sends "ERROR invalid country", or malformed POW line.
    """


class TransientError(Exception):
    """
    Raised for NETWORK failures that might succeed on another port.

    The Exasol server runs on 6 ports. If one is unreachable (firewall,
    temporary blip), we try the next one. This error signals "try again"
    rather than "give up entirely".

    Examples: TCP connection refused, TLS handshake timeout, socket reset.
    """


# ── POW PROGRESS DISPLAY ──────────────────────────────────────────────────────

def _pow_progress(total: int, elapsed: float, rate: float) -> None:
    """
    Print a live progress counter that updates in-place on a terminal.

    Uses \r (carriage return) to overwrite the same line repeatedly,
    creating the effect of a counter ticking up. Only used when stdout
    is a real terminal (not redirected to a file).

    total:   total hashes tried so far across all CPU cores
    elapsed: seconds elapsed since POW started
    rate:    hashes per second (current speed)
    """
    # \r moves the cursor to the start of the current line without newline,
    # so the next write overwrites the previous progress display
    sys.stdout.write(
        f"\r[pow] {total:>15,} hashes  "  # e.g.  9,297,920 hashes
        f"{elapsed:>6.1f}s  "             # e.g.      3.3s
        f"{rate/1e6:>6.2f} M/s   "        # e.g.   2.45 M/s
    )
    sys.stdout.flush()   # Force the output to appear immediately (no buffering)


def _make_line_progress():
    """
    Build a progress reporter for non-interactive use (log files, pipes).

    When stdout is redirected to a file, \r doesn't work — it just creates
    garbled output. Instead, we print a full line every 30 seconds.

    Returns a closure (a function with its own private state). The state
    (last_print) resets every time you call _make_line_progress(), which
    means retries start fresh instead of suppressing the first log line.

    A "closure" is a function that "closes over" variables from its outer
    scope — here, last_print persists between calls to callback().
    """
    last_print = [-1.0]   # A list with one float: last time we printed.
                          # Using a list so the inner function can modify it.
                          # (Python doesn't allow rebinding outer-scope variables
                          # with plain assignment in a closure — a list works around that)

    def callback(total: int, elapsed: float, rate: float) -> None:
        # Skip if less than 30 seconds since last print AND more than 0.5s elapsed
        # (the 0.5s check prevents printing "0.00 M/s" before workers have started)
        if elapsed - last_print[0] < 30.0 and elapsed > 0.5:
            return
        last_print[0] = elapsed   # Record this print time
        sys.stdout.write(
            f"[pow] {total:>15,} hashes  {elapsed:>6.1f}s  {rate/1e6:>6.2f} M/s\n"
        )
        sys.stdout.flush()

    return callback   # Return the inner function (with its private state)


# ── COMMAND HANDLER ───────────────────────────────────────────────────────────

def handle_command(conn: LineConn, line: bytes, state: dict, profile: dict) -> bool:
    """
    Process one command received from the server.

    This is the heart of the protocol logic. Each time the server sends a
    line, this function decides what to do and sends back the right response.

    Returns True  → conversation is still going (read the next command)
    Returns False → conversation is over (END received, or fatal error)

    state: a shared dictionary that persists across commands in one session.
           We use it to remember authdata (received in POW) for use in
           all subsequent checksummed responses.
    """
    # Guard against completely empty lines from the server
    if not line:
        raise ProtocolError("got empty line from server")

    # Split the line into tokens on any whitespace.
    # e.g. b"POW GisTfIx... 6" -> [b"POW", b"GisTfIx...", b"6"]
    # e.g. b"NAME fjxi"        -> [b"NAME", b"fjxi"]
    # Using .split() (no args) handles multiple spaces or tabs gracefully.
    tokens = line.split()
    if not tokens:
        raise ProtocolError(f"got blank line from server: {line!r}")

    # Decode just the command word to ASCII for comparison.
    # errors="replace" means bad bytes become ? rather than crashing.
    cmd = tokens[0].decode("ascii", errors="replace")

    # ── HELO: Server's greeting ───────────────────────────────────────────────
    if cmd == "HELO":
        # The server always sends this first to start the handshake.
        # We must reply with exactly "TOAKUEI" — this is the magic word
        # that Exasol chose as the greeting. No other response is accepted.
        conn.write(b"TOAKUEI\n")
        return True   # Keep going — next command will be POW

    # ── ERROR: Server rejected something ─────────────────────────────────────
    if cmd == "ERROR":
        # Server is unhappy — maybe invalid country name, bad date format, etc.
        # Concatenate any extra tokens to form the full error message.
        msg = b" ".join(tokens[1:]).decode("utf-8", errors="replace")
        raise ProtocolError(f"server ERROR: {msg}")  # Fatal — don't retry

    # ── END: Server confirmed successful submission ───────────────────────────
    if cmd == "END":
        # This is the success signal — server has recorded your application.
        conn.write(b"OK\n")   # Acknowledge receipt
        print("[ok] server sent END — submission accepted.")
        return False   # Stop the loop — we're done!

    # ── POW: The proof-of-work challenge ─────────────────────────────────────
    if cmd == "POW":
        # Format: POW <authdata> <difficulty>
        # Example: POW GisTfIxtrOOAfpP...ZnUF 6
        if len(tokens) < 3:
            raise ProtocolError(f"malformed POW line: {line!r}")

        authdata = tokens[1]   # The random session token (keep as bytes)
        try:
            difficulty = int(tokens[2])   # How many leading hex zeros needed
        except ValueError:
            raise ProtocolError(f"non-integer POW difficulty: {tokens[2]!r}")

        # Sanity check: SHA-1 produces 40 hex chars max, so difficulty > 40
        # is mathematically impossible. Negative is nonsensical.
        if difficulty < 0 or difficulty > 40:
            raise ProtocolError(f"out-of-range POW difficulty: {difficulty}")

        # Save authdata in the shared session state — we need it for ALL
        # subsequent checksummed responses (NAME, MAIL1, etc.)
        state["authdata"] = authdata

        print(f"[pow] difficulty={difficulty}, authdata_len={len(authdata)}")
        t0 = time.monotonic()   # Record when the solve started (for timing)

        # Choose progress display: live updating line for terminals,
        # throttled line-per-30s for log files
        callback = _pow_progress if sys.stdout.isatty() else _make_line_progress()

        try:
            # *** THE BIG WORK HAPPENS HERE ***
            # solve_pow() launches one worker process per CPU core.
            # Each worker tries millions of suffixes per second until one
            # produces a SHA1 hash with 'difficulty' leading zero hex chars.
            # This may take minutes to hours depending on difficulty.
            suffix = solve_pow(authdata, difficulty, progress_callback=callback)
        except RuntimeError as e:
            # All workers crashed — unlikely but handled. Treat as transient
            # so the caller can retry on a different port with a fresh session.
            raise TransientError(f"POW solver failed: {e}")

        elapsed = time.monotonic() - t0   # How long the solve took

        # For terminal display: the progress line used \r so there's no newline
        # at the end. Print one now to start a fresh line.
        if sys.stdout.isatty():
            sys.stdout.write("\n")

        # Verify the answer locally before sending it to the server.
        # Better to catch a solver bug HERE than have the server reject us
        # after we've spent hours solving.
        digest = hashlib.sha1(authdata + suffix).hexdigest()
        if not digest.startswith("0" * difficulty):
            raise ProtocolError(f"solver returned invalid suffix: digest={digest}")

        # Paranoia check: the spec says the suffix must NOT contain \n, \r,
        # \t, or space — they'd break the line-based protocol. The solver's
        # alphabet excludes these by design, but verify anyway.
        for forbidden in (b"\n", b"\r", b"\t", b" "):
            if forbidden in suffix:
                raise ProtocolError(
                    f"solver returned suffix containing forbidden byte {forbidden!r}: "
                    f"suffix={suffix!r}"
                )

        # Print the solution summary for the user to see
        print(f"[pow] solved in {elapsed:.1f}s — "
              f"suffix={suffix.decode('ascii', errors='backslashreplace')!r}, "
              f"digest={digest[:12]}...")

        # Send the winning suffix to the server.
        # The server will compute SHA1(authdata + suffix) itself and verify
        # it starts with 'difficulty' zeros. If it does, we pass the POW.
        conn.write(suffix + b"\n")
        return True   # Keep going — server will now ask personal questions

    # ── PERSONAL DATA COMMANDS (NAME, MAIL1, COUNTRY, etc.) ──────────────────
    # These all follow the same pattern: server sends a random "arg" token,
    # we reply with SHA1(authdata + arg) + " " + our_answer

    # Sanity check: we should never get personal questions before the POW.
    # If we do, the server is behaving unexpectedly.
    if "authdata" not in state:
        raise ProtocolError(f"got {cmd} before POW — server protocol violation")

    # Every personal-data command sends an argument token (e.g. "fjxi")
    if len(tokens) < 2:
        raise ProtocolError(f"command {cmd} missing argument: {line!r}")

    authdata = state["authdata"]  # Retrieve the session token we saved during POW
    arg1 = tokens[1]              # The server's random nonce for this specific question
    value = answer_for(cmd, profile)   # Look up our answer from profile.json

    # Build and send the checksummed response
    conn.write(build_response(authdata, arg1, value))
    print(f"[answer] {cmd} -> {value!r}")
    return True   # Keep going — more questions may follow


# ── SESSION RUNNER ────────────────────────────────────────────────────────────

def run_session(
    host: str,
    port: int,
    cert: str,
    key: str,
    ca: str | None,
    profile: dict,
    verbose: bool = False,
) -> bool:
    """
    Run one complete session: connect, HELO, POW, Q&A, END.

    Returns True if the server sent END (success).
    Raises ProtocolError if the server rejected us (don't retry).
    Raises TransientError if the network failed (safe to retry on next port).

    READ TIMEOUTS EXPLAINED:
    ─────────────────────────
    - The server-side timeout for non-POW commands is 6 seconds.
    - We use 30 seconds on our side to give plenty of slack for network jitter.
    - The POW itself runs entirely locally — we never wait on the server during
      the solve. The 2-hour POW deadline is enforced by the server waiting for
      our suffix, not by a read timeout on our end.
    """
    global _VERBOSE, _T0
    _VERBOSE = verbose          # Store verbose setting for _vlog() to use
    _T0 = time.monotonic()     # Record session start time for verbose timestamps

    READ_TIMEOUT_SHORT = 30.0  # Seconds to wait for each server response

    print(f"[net] connecting to {host}:{port}")
    if verbose:
        # Print a visual separator in verbose mode
        print(f"\n{'='*70}")
        print(f"  TLS HANDSHAKE  -->  {host}:{port}")
        print(f"{'='*70}")

    try:
        # Establish the encrypted TLS connection (may raise if unreachable)
        sock = make_tls_socket(host, port, cert, key, ca)
    except (socket.timeout, OSError, ssl.SSLError) as e:
        # Any network-level failure here is transient — try another port
        raise TransientError(f"connect failed: {type(e).__name__}: {e}")

    # Wrap the raw socket with our line-reading helper
    conn = LineConn(sock)

    # state dict holds data that persists across commands in this session.
    # Currently only used for: state["authdata"] = bytes from the POW line.
    state: dict = {}

    try:
        # Main protocol loop: read a command, handle it, repeat until done
        while True:
            try:
                # Wait for the next line from the server (30-second timeout)
                line = conn.read_line(timeout=READ_TIMEOUT_SHORT)
            except (socket.timeout, ConnectionError, OSError, ssl.SSLError) as e:
                # Network failure while reading — safe to retry on another port
                raise TransientError(f"read failed: {type(e).__name__}: {e}")

            try:
                # Process the command and send our response
                keep_going = handle_command(conn, line, state, profile)
            except (socket.timeout, ConnectionError, OSError, ssl.SSLError) as e:
                # Network failure while writing our response
                raise TransientError(f"send failed: {type(e).__name__}: {e}")

            if not keep_going:
                return True   # Server sent END — success, we're done

    finally:
        # Always close the connection, even if an exception occurred.
        # "finally" runs whether we return normally or crash.
        conn.close()


# ── SELF-TEST ─────────────────────────────────────────────────────────────────

def self_test() -> None:
    """
    Quick sanity check that runs BEFORE connecting to the server.

    Solves a difficulty-4 POW locally and verifies the answer is correct.
    If this fails, your Python environment is broken and the real run would
    fail too — better to know now in 1 second than after 2 hours.

    Difficulty 4 means finding a suffix where SHA1(auth+suffix) starts with
    "0000" — typically takes a few milliseconds.
    """
    from pow_solver import _solve_single   # Import the single-core solver directly

    auth = b"selftest-authdata"   # Fixed test input (doesn't matter what it is)
    suffix = _solve_single(auth, 4)   # Find a suffix with 4 leading zero hex chars
    digest = hashlib.sha1(auth + suffix).hexdigest()   # Compute SHA1 to verify

    # Assert the result is actually correct
    assert digest.startswith("0000"), f"self-test failed: {digest}"

    # Assert no forbidden characters in the suffix
    for forbidden in (b"\n", b"\r", b"\t", b" "):
        assert forbidden not in suffix

    print(f"[selftest] OK — solver produced suffix={suffix.decode('latin1')!r}, digest={digest[:12]}...")


# ── MAIN ENTRY POINT ──────────────────────────────────────────────────────────

def main() -> int:
    """
    Parse command-line arguments and orchestrate the full submission.

    Returns an exit code:
        0  = success (server sent END)
        1  = failure (server error or all ports failed)
        2  = bad arguments or invalid profile
        130 = interrupted by Ctrl+C
    """
    # argparse builds a --help message and parses sys.argv automatically
    p = argparse.ArgumentParser(
        description="Exasol challenge client (TLS + SHA-1 POW + personal-data handshake).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Credential arguments — how to identify yourself to the server
    g = p.add_argument_group("credentials (use either --pem OR all of --cert/--key)")
    g.add_argument("--pem",  help="Combined PEM file with key + cert in one file (challenge.pem)")
    g.add_argument("--cert", help="Client certificate file (PEM format). Overrides --pem.")
    g.add_argument("--key",  help="Client private key file (PEM format). Overrides --pem.")
    g.add_argument("--ca",   help="CA certificate to verify the server's identity.")
    g.add_argument("--insecure", action="store_true",
                   help="Skip server certificate verification (not recommended).")

    # Other arguments
    p.add_argument("--profile",  required=True,  help="JSON file with your personal answers.")
    p.add_argument("--host",     default=DEFAULT_HOST, help="Server IP address.")
    p.add_argument("--port",     type=int, default=None,
                   help="Use only this port. Default: try all 6 known ports.")
    p.add_argument("--no-selftest", action="store_true",
                   help="Skip the startup solver self-test (saves ~1 second).")
    p.add_argument("--verbose",  action="store_true",
                   help="Show every line sent and received (raw protocol traffic).")

    args = p.parse_args()   # Parse the actual command-line arguments

    # ── Resolve certificate paths ─────────────────────────────────────────────
    # If --cert is given, use it; otherwise fall back to --pem for the cert.
    cert = args.cert or args.pem
    # Same logic for the private key
    key = args.key or args.pem

    if args.insecure:
        # User explicitly asked to skip server verification
        if args.ca:
            print("warning: --ca ignored because --insecure was given.", file=sys.stderr)
        ca = None
    else:
        # Server verification is OPT-IN via explicit --ca only.
        # We do NOT auto-default --ca to --pem here because challenge.pem
        # contains the CLIENT cert (not a CA cert). Passing a non-CA cert to
        # load_verify_locations() causes OpenSSL to reject it with
        # "invalid CA certificate" — the bug that was causing all ports to fail.
        ca = args.ca

    # ── Validate file paths ───────────────────────────────────────────────────
    if not cert or not key:
        print("error: must provide --pem or both --cert and --key", file=sys.stderr)
        return 2

    # Check that cert and key files actually exist on disk
    for name, path in (("cert", cert), ("key", key)):
        if not Path(path).is_file():
            print(f"error: {name} not found: {path}", file=sys.stderr)
            return 2

    if ca and not Path(ca).is_file():
        print(f"error: ca not found: {ca}", file=sys.stderr)
        return 2

    # ── Load and validate the profile ─────────────────────────────────────────
    # Do this BEFORE connecting so a bad profile fails fast (not after hours of POW).
    try:
        profile = load_profile(args.profile)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
        # OSError: file not found; JSONDecodeError: bad JSON syntax
        # UnicodeDecodeError: file has wrong encoding; ValueError: our validation
        print(f"error: invalid profile {args.profile}: {e}", file=sys.stderr)
        return 2

    print(f"[profile] loaded {args.profile} — name={profile['NAME']!r}, "
          f"mails={len(profile['MAILS'])}, address_lines={len(profile['ADDRESS'])}")

    # ── Run self-test ──────────────────────────────────────────────────────────
    if not args.no_selftest:
        try:
            self_test()   # Solve difficulty-4 POW locally as a health check
        except Exception as e:
            print(f"error: self-test failed: {type(e).__name__}: {e}", file=sys.stderr)
            print("       run with --no-selftest to skip, but expect "
                  "the real run to fail too.", file=sys.stderr)
            return 2

    # ── Attempt connection on each port ───────────────────────────────────────
    # Use only the specified port if --port was given, otherwise try all 6.
    ports = (args.port,) if args.port else DEFAULT_PORTS

    last_transient: TransientError | None = None

    for port in ports:
        try:
            # Try a full session on this port
            ok = run_session(args.host, port, cert, key, ca, profile, verbose=args.verbose)
            return 0 if ok else 1   # 0 = success (END received)

        except KeyboardInterrupt:
            # User pressed Ctrl+C — exit gracefully
            print("\n[interrupt] cancelled by user.", file=sys.stderr)
            return 130   # Unix convention: 128 + signal 2 (SIGINT) = 130

        except ProtocolError as e:
            # Server rejected our data — no point trying another port.
            # The problem is in our profile or our code, not the network.
            print(f"[fatal] {e}", file=sys.stderr)
            return 1

        except TransientError as e:
            # Network failure — try the next port
            print(f"[retry] port {port} transient failure: {e}", file=sys.stderr)
            last_transient = e
            continue   # Go to next port in the loop

        except Exception as e:
            # Unexpected bug — log it and try the next port (defensive)
            print(f"[bug] unexpected {type(e).__name__} on port {port}: {e}",
                  file=sys.stderr)
            last_transient = TransientError(f"{type(e).__name__}: {e}")
            continue

    # If we get here, all 6 ports failed
    print(f"[fatal] all ports exhausted; last error: {last_transient}", file=sys.stderr)
    return 1


# ── SCRIPT ENTRY POINT ────────────────────────────────────────────────────────

if __name__ == "__main__":
    # This block only runs when the file is executed directly:
    #     python exasol_client.py ...
    # It does NOT run when the file is imported by another module.
    try:
        sys.exit(main())   # Run main() and exit with its return code
    except KeyboardInterrupt:
        # Belt-and-braces catch: handles Ctrl+C during argument parsing or
        # profile loading, before the per-port try/except is active.
        sys.stderr.write("\n[interrupt] cancelled by user.\n")
        sys.exit(130)
