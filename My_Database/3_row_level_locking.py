"""
ROW-LEVEL LOCKING — Only the modified row is locked, not the whole table
=========================================================================
InnoDB locks at the ROW level. This means:
  • Many users can write to the SAME TABLE simultaneously
  • A lock only blocks another transaction trying to touch the SAME ROW
  • Readers (SELECT) never block writers (UPDATE) — thanks to MVCC

Lock types InnoDB uses:
  S-lock  (Shared)     — for reads;  multiple transactions can hold simultaneously
  X-lock  (Exclusive)  — for writes; only ONE transaction at a time
  IS/IX   (Intention)  — table-level signals that row locks exist below

This demo:
  1. Shows table-level locking (the OLD way, e.g. MyISAM) — slow, blocking
  2. Shows row-level locking (InnoDB way) — concurrent, fast
  3. Shows a deadlock (what happens when two row locks cycle) + detection
"""

import sqlite3
import threading
import time
import queue

DB = "row_lock_demo.db"


# ── Setup ──────────────────────────────────────────────────────────────
def setup():
    conn = sqlite3.connect(DB)
    conn.execute("DROP TABLE IF EXISTS inventory")
    conn.execute("""
                 CREATE TABLE inventory (
                                            id       INTEGER PRIMARY KEY,
                                            product  TEXT,
                                            stock    INTEGER
                 )
                 """)
    conn.executemany("INSERT INTO inventory VALUES (?,?,?)", [
        (1, "Widget-A", 100),
        (2, "Widget-B", 200),
        (3, "Widget-C", 300),
    ])
    conn.commit()
    conn.close()
    print("✅ Inventory table created\n")
    print("   Row 1: Widget-A  stock=100")
    print("   Row 2: Widget-B  stock=200")
    print("   Row 3: Widget-C  stock=300\n")


# ══════════════════════════════════════════════════════════════════════
# PART 1 — Table-level locking (old MyISAM style — simulate with a mutex)
# ══════════════════════════════════════════════════════════════════════

def demo_table_lock():
    """
    With table-level locking, even if User A updates row 1 and User B
    updates row 3, User B must WAIT for User A to finish — even though
    they're touching completely different rows. Terrible for concurrency.
    """
    print("=" * 60)
    print("DEMO 1: TABLE-LEVEL LOCKING (MyISAM style) — serialized")
    print("=" * 60)

    table_lock = threading.Lock()   # simulates MyISAM's single table lock
    timeline   = []

    def user(name, row_id, delay_start, hold_seconds):
        time.sleep(delay_start)
        t0 = time.time()
        timeline.append(f"[{name}] Waiting for TABLE lock...")
        with table_lock:                        # must lock ENTIRE table
            wait_time = time.time() - t0
            timeline.append(
                f"[{name}] Got lock after {wait_time:.2f}s — updating row {row_id}"
            )
            time.sleep(hold_seconds)            # simulate work
            timeline.append(f"[{name}] Done — releasing table lock")

    t1 = threading.Thread(target=user, args=("User-A", 1, 0.0, 0.3))
    t2 = threading.Thread(target=user, args=("User-B", 3, 0.05, 0.2))  # different row!
    t3 = threading.Thread(target=user, args=("User-C", 2, 0.05, 0.1))  # different row!

    t1.start(); t2.start(); t3.start()
    t1.join();  t2.join();  t3.join()

    for msg in timeline:
        print(" ", msg)
    print("\n☹️  Users B & C had to wait even though they touched DIFFERENT rows!\n")


# ══════════════════════════════════════════════════════════════════════
# PART 2 — Row-level locking (InnoDB style)
# ══════════════════════════════════════════════════════════════════════

def demo_row_lock():
    """
    With row-level locking, each user only locks the specific row they
    modify. Different rows can be updated simultaneously — true concurrency.
    """
    print("=" * 60)
    print("DEMO 2: ROW-LEVEL LOCKING (InnoDB style) — concurrent")
    print("=" * 60)

    row_locks = {1: threading.Lock(), 2: threading.Lock(), 3: threading.Lock()}
    timeline  = []
    timings   = {}

    def user(name, row_id, new_stock, delay_start, hold_seconds):
        time.sleep(delay_start)
        t0 = time.time()
        timeline.append(f"[{name}] Waiting for ROW {row_id} lock...")
        with row_locks[row_id]:                  # lock ONLY this row
            wait_time = time.time() - t0
            timeline.append(
                f"[{name}] Got row-{row_id} lock after {wait_time:.2f}s — updating"
            )
            conn = sqlite3.connect(DB, check_same_thread=False)
            conn.execute("UPDATE inventory SET stock=? WHERE id=?", (new_stock, row_id))
            conn.commit()
            conn.close()
            time.sleep(hold_seconds)
            timeline.append(f"[{name}] Done — row {row_id} updated to {new_stock}")
        timings[name] = time.time() - t0

    t1 = threading.Thread(target=user, args=("User-A", 1,  50, 0.0,  0.3))  # row 1
    t2 = threading.Thread(target=user, args=("User-B", 3, 250, 0.05, 0.2))  # row 3 — different!
    t3 = threading.Thread(target=user, args=("User-C", 2, 180, 0.05, 0.1))  # row 2 — different!
    # User-D contends with User-A on the same row:
    t4 = threading.Thread(target=user, args=("User-D", 1,  75, 0.01, 0.1))  # row 1 — same!

    t1.start(); t2.start(); t3.start(); t4.start()
    t1.join();  t2.join();  t3.join();  t4.join()

    for msg in timeline:
        print(" ", msg)

    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT * FROM inventory ORDER BY id").fetchall()
    conn.close()
    print(f"\n   Final inventory: {rows}")
    print("\n✅ Users B & C ran concurrently (different rows). Only User-D had to wait (same row as A)!\n")


# ══════════════════════════════════════════════════════════════════════
# PART 3 — Deadlock demonstration + detection
# ══════════════════════════════════════════════════════════════════════

def demo_deadlock():
    """
    Deadlock: Transaction A holds lock on row 1, wants row 2.
              Transaction B holds lock on row 2, wants row 1.
    Neither can proceed — circular wait.
    InnoDB detects this automatically and kills one transaction (victim).
    """
    print("=" * 60)
    print("DEMO 3: DEADLOCK — circular row-lock wait")
    print("=" * 60)
    print("   Txn A: lock row1 → then try row2")
    print("   Txn B: lock row2 → then try row1  ← circular!\n")

    lock1 = threading.Lock()
    lock2 = threading.Lock()
    result_q = queue.Queue()

    def txn_a():
        with lock1:
            result_q.put("[Txn A] Acquired lock on ROW 1")
            time.sleep(0.1)          # pause so Txn B grabs lock2
            result_q.put("[Txn A] Waiting for ROW 2 lock...")
            acquired = lock2.acquire(timeout=0.5)   # InnoDB deadlock timeout
            if acquired:
                result_q.put("[Txn A] Got ROW 2 — committed ✅")
                lock2.release()
            else:
                result_q.put("[Txn A] ⏰ Timeout! Deadlock detected — rolling back 🔄")

    def txn_b():
        time.sleep(0.05)             # slight delay so Txn A grabs lock1 first
        with lock2:
            result_q.put("[Txn B] Acquired lock on ROW 2")
            time.sleep(0.1)
            result_q.put("[Txn B] Waiting for ROW 1 lock...")
            acquired = lock1.acquire(timeout=0.5)
            if acquired:
                result_q.put("[Txn B] Got ROW 1 — committed ✅")
                lock1.release()
            else:
                result_q.put("[Txn B] ⏰ Timeout! Deadlock detected — rolling back 🔄")

    ta = threading.Thread(target=txn_a)
    tb = threading.Thread(target=txn_b)
    ta.start(); tb.start()
    ta.join();  tb.join()

    # Print events in the order they were queued
    while not result_q.empty():
        print(" ", result_q.get())

    print("""
   HOW InnoDB HANDLES THIS:
   • InnoDB has a built-in deadlock detector (waits-for graph)
   • It picks the cheaper transaction to roll back (the 'victim')
   • The other transaction proceeds normally
   • The victim receives error 1213: ER_LOCK_DEADLOCK
   • Application should catch this and retry the transaction

   PREVENTION TIP: Always acquire locks in the SAME ORDER in all
   transactions (e.g., always lock lower IDs before higher IDs).
""")


# ── Main ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    setup()
    demo_table_lock()
    demo_row_lock()
    demo_deadlock()

    import os; os.remove(DB)
    print("🧹 Demo database removed.")