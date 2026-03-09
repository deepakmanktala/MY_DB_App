"""
ISOLATION — Concurrent transactions don't interfere with each other.
=====================================================================
InnoDB supports 4 isolation levels:
  1. READ UNCOMMITTED  – can read dirty (uncommitted) data
  2. READ COMMITTED    – only reads committed data (default in many DBs)
  3. REPEATABLE READ   – same query returns same rows within a transaction (InnoDB default)
  4. SERIALIZABLE      – fully sequential; strongest isolation

This demo simulates two concurrent users (threads) updating the same
bank account and shows HOW isolation prevents corruption.
"""

import sqlite3
import threading
import time

DB = "isolation_demo.db"

# ── Setup ──────────────────────────────────────────────────────────────
def setup():
    conn = sqlite3.connect(DB)
    conn.execute("DROP TABLE IF EXISTS accounts")
    conn.execute("""
                 CREATE TABLE accounts (
                                           id      INTEGER PRIMARY KEY,
                                           name    TEXT,
                                           balance REAL
                 )
                 """)
    conn.execute("INSERT INTO accounts VALUES (1, 'Alice', 1000.00)")
    conn.commit()
    conn.close()
    print("✅ Table created. Alice's balance = $1000\n")


# ── PROBLEM: No isolation (dirty read simulation) ─────────────────────
def dirty_read_demo():
    """
    Without isolation, Transaction B could read a value that
    Transaction A hasn't committed yet — a 'dirty read'.
    InnoDB prevents this at READ COMMITTED and above.
    """
    print("=" * 60)
    print("DEMO 1: Dirty Read (what happens WITHOUT isolation)")
    print("=" * 60)

    shared_state = {"balance": 1000}  # simulating in-memory dirty read

    def transaction_a():
        print("[Txn A] Starting — will temporarily set balance to $5000 then rollback")
        shared_state["balance"] = 5000   # uncommitted change
        time.sleep(0.1)                  # pause while Txn B runs
        shared_state["balance"] = 1000  # rollback
        print("[Txn A] Rolled back. Balance restored to $1000")

    def transaction_b():
        time.sleep(0.05)  # read DURING Txn A's uncommitted change
        seen = shared_state["balance"]
        print(f"[Txn B] Read balance = ${seen}  ← DIRTY READ! (actual value is $1000)")

    t_a = threading.Thread(target=transaction_a)
    t_b = threading.Thread(target=transaction_b)
    t_a.start(); t_b.start()
    t_a.join();  t_b.join()
    print("\n👆 InnoDB PREVENTS this by default (REPEATABLE READ isolation)\n")


# ── SOLUTION: Proper isolation with SQLite (simulating REPEATABLE READ) ─
def repeatable_read_demo():
    """
    REPEATABLE READ: Once Transaction B reads a row, it always sees
    the same value for that row — even if Transaction A commits a change.
    InnoDB achieves this via MVCC (Multi-Version Concurrency Control):
    each transaction gets a 'snapshot' of the data at start time.
    """
    print("=" * 60)
    print("DEMO 2: REPEATABLE READ — snapshot isolation")
    print("=" * 60)

    barrier = threading.Barrier(2)  # sync both threads
    results = {}

    def transaction_a(conn_a):
        """Transaction A: updates Alice's balance mid-flight"""
        conn_a.execute("BEGIN")
        time.sleep(0.05)
        conn_a.execute("UPDATE accounts SET balance = 9999 WHERE id = 1")
        conn_a.commit()
        print("[Txn A] Committed: set Alice's balance to $9999")

    def transaction_b(conn_b):
        """Transaction B: reads BEFORE and AFTER Txn A commits"""
        conn_b.execute("BEGIN")

        row = conn_b.execute("SELECT balance FROM accounts WHERE id=1").fetchone()
        results["before"] = row[0]
        print(f"[Txn B] First read  → ${row[0]}")

        barrier.wait()          # let Txn A commit now
        time.sleep(0.15)        # wait for Txn A to finish

        row = conn_b.execute("SELECT balance FROM accounts WHERE id=1").fetchone()
        results["after"] = row[0]
        print(f"[Txn B] Second read → ${row[0]}  (same snapshot = repeatable)")
        conn_b.commit()

    conn_a = sqlite3.connect(DB, check_same_thread=False)
    conn_b = sqlite3.connect(DB, check_same_thread=False)
    conn_b.isolation_level = "DEFERRED"   # SQLite's REPEATABLE READ equivalent

    t_b = threading.Thread(target=transaction_b, args=(conn_b,))
    t_a = threading.Thread(target=transaction_a, args=(conn_a,))

    t_b.start()
    time.sleep(0.02)
    barrier.wait()  # release Txn A after Txn B's first read
    t_a.start()
    t_a.join(); t_b.join()
    conn_a.close(); conn_b.close()

    if results["before"] == results["after"]:
        print("\n✅ Both reads returned the same value — REPEATABLE READ works!")
    else:
        print("\n⚠️  Values differed — weaker isolation level detected")


# ── SOLUTION: Serializable isolation ──────────────────────────────────
def serializable_demo():
    """
    SERIALIZABLE: The strictest level. Transactions run as if they
    were sequential (one after another), even if concurrent.
    Second transaction WAITS until first is fully done.
    """
    print("\n" + "=" * 60)
    print("DEMO 3: SERIALIZABLE — strictest isolation")
    print("=" * 60)

    lock = threading.Lock()  # simulates serializable row lock
    log = []

    def user(name, amount, delay):
        time.sleep(delay)
        with lock:   # only one transaction at a time
            conn = sqlite3.connect(DB)
            conn.execute("BEGIN EXCLUSIVE")  # serializable in SQLite
            row = conn.execute("SELECT balance FROM accounts WHERE id=1").fetchone()
            old_bal = row[0]
            new_bal = old_bal + amount
            conn.execute("UPDATE accounts SET balance=? WHERE id=1", (new_bal,))
            conn.commit()
            conn.close()
            log.append(f"[{name}] {old_bal:.0f} → {new_bal:.0f}  (change: {amount:+.0f})")

    # Reset balance
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE accounts SET balance=1000 WHERE id=1"); conn.commit(); conn.close()

    threads = [
        threading.Thread(target=user, args=("User-1", +200, 0.0)),
        threading.Thread(target=user, args=("User-2", -150, 0.01)),
        threading.Thread(target=user, args=("User-3", +500, 0.02)),
    ]
    for t in threads: t.start()
    for t in threads: t.join()

    for entry in log:
        print(entry)

    conn = sqlite3.connect(DB)
    final = conn.execute("SELECT balance FROM accounts WHERE id=1").fetchone()[0]
    conn.close()
    expected = 1000 + 200 - 150 + 500
    print(f"\nFinal balance: ${final:.0f}  |  Expected: ${expected}")
    print("✅ No lost updates — each transaction saw consistent state!" if final == expected
          else "❌ Lost update detected!")


# ── Main ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    setup()
    dirty_read_demo()
    repeatable_read_demo()
    serializable_demo()

    import os; os.remove(DB)
    print("\n🧹 Demo database removed.")