"""
DURABILITY — Committed data survives crashes (via Write-Ahead Log)
==================================================================
InnoDB uses a Write-Ahead Log (WAL) — also called the redo log.

HOW IT WORKS:
  1. Before changing the actual data file, InnoDB writes the change
     to the WAL (a sequential append-only log file on disk).
  2. Only after the WAL entry is flushed does the transaction commit.
  3. If the server crashes mid-write, on restart InnoDB replays the
     WAL to recover committed transactions and discard uncommitted ones.

This demo:
  A) Shows WAL-style logging manually (so you can see the concept).
  B) Simulates a "crash" mid-transaction and shows recovery.
  C) Uses SQLite's WAL mode (same mechanism as InnoDB's redo log).
"""

import sqlite3
import json
import os
import time

DB       = "durability_demo.db"
WAL_FILE = "demo_wal.log"       # our hand-rolled WAL for illustration


# ══════════════════════════════════════════════════════════════════════
# PART 1 — Manual WAL illustration
# ══════════════════════════════════════════════════════════════════════

class SimpleWAL:
    """
    A stripped-down Write-Ahead Log to show the concept.
    Real InnoDB uses binary redo log files, but the logic is the same.
    """

    def __init__(self, path):
        self.path = path

    def append(self, txn_id: int, operation: str, table: str, data: dict, status="PENDING"):
        entry = {
            "lsn":       int(time.time() * 1e6),   # Log Sequence Number
            "txn_id":    txn_id,
            "operation": operation,
            "table":     table,
            "data":      data,
            "status":    status,
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry["lsn"]

    def mark_committed(self, txn_id: int):
        """Update status of all entries for this txn to COMMITTED."""
        lines = []
        if os.path.exists(self.path):
            with open(self.path) as f:
                for line in f:
                    e = json.loads(line)
                    if e["txn_id"] == txn_id:
                        e["status"] = "COMMITTED"
                    lines.append(json.dumps(e))
        with open(self.path, "w") as f:
            f.write("\n".join(lines) + "\n")

    def read_all(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return [json.loads(l) for l in f if l.strip()]

    def clear(self):
        if os.path.exists(self.path):
            os.remove(self.path)


def setup_db():
    conn = sqlite3.connect(DB)
    # Enable WAL mode — SQLite's equivalent of InnoDB's redo log
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("DROP TABLE IF EXISTS orders")
    conn.execute("""
                 CREATE TABLE orders (
                                         id       INTEGER PRIMARY KEY,
                                         customer TEXT,
                                         amount   REAL,
                                         status   TEXT DEFAULT 'pending'
                 )
                 """)
    conn.commit()
    conn.close()
    print("✅ Database created with WAL journal mode\n")


# ══════════════════════════════════════════════════════════════════════
# PART 2 — Normal commit (WAL ensures durability)
# ══════════════════════════════════════════════════════════════════════

def demo_successful_commit():
    print("=" * 60)
    print("DEMO 1: Successful commit — WAL write-then-apply flow")
    print("=" * 60)

    wal = SimpleWAL(WAL_FILE)
    conn = sqlite3.connect(DB)

    txn_id = 1001
    order  = {"id": 1, "customer": "Bob", "amount": 250.0, "status": "confirmed"}

    # ── Step 1: Write to WAL FIRST (before touching data file) ──
    lsn = wal.append(txn_id, "INSERT", "orders", order)
    print(f"[WAL]  Entry written  LSN={lsn}  status=PENDING")

    # ── Step 2: Apply change to actual database ──
    conn.execute("BEGIN")
    conn.execute("INSERT INTO orders VALUES (:id, :customer, :amount, :status)", order)

    # ── Step 3: Mark WAL entry COMMITTED, then commit DB ──
    wal.mark_committed(txn_id)
    conn.commit()
    print(f"[WAL]  Entry marked   txn_id={txn_id}  status=COMMITTED")
    print(f"[DB]   Row inserted   → order #{order['id']} for {order['customer']} (${order['amount']})")

    # ── Verify ──
    row = conn.execute("SELECT * FROM orders WHERE id=1").fetchone()
    print(f"\n✅ Data persisted: {row}")
    conn.close()


# ══════════════════════════════════════════════════════════════════════
# PART 3 — Simulated crash + recovery
# ══════════════════════════════════════════════════════════════════════

def demo_crash_and_recovery():
    print("\n" + "=" * 60)
    print("DEMO 2: Simulated crash mid-transaction → WAL recovery")
    print("=" * 60)

    wal  = SimpleWAL(WAL_FILE)
    conn = sqlite3.connect(DB)

    # ── Transaction A: will COMMIT before crash ──
    txn_a = 2001
    wal.append(txn_a, "INSERT", "orders", {"id": 2, "customer": "Carol", "amount": 99.0})
    conn.execute("BEGIN")
    conn.execute("INSERT INTO orders VALUES (2, 'Carol', 99.0, 'pending')")
    wal.mark_committed(txn_a)
    conn.commit()
    print(f"[Txn {txn_a}] Committed successfully (Carol's order)")

    # ── Transaction B: will crash BEFORE committing ──
    txn_b = 2002
    wal.append(txn_b, "INSERT", "orders", {"id": 3, "customer": "Dave", "amount": 500.0})
    conn.execute("BEGIN")
    conn.execute("INSERT INTO orders VALUES (3, 'Dave', 500.0, 'pending')")
    print(f"[Txn {txn_b}] Changes written to WAL... 💥 CRASH before commit!")
    conn.close()   # ← simulates a crash (no commit called)

    # ── Recovery on restart ──
    print("\n🔄 Server restarting... scanning WAL for recovery...")
    conn = sqlite3.connect(DB)

    committed   = [e for e in wal.read_all() if e["status"] == "COMMITTED"]
    uncommitted = [e for e in wal.read_all() if e["status"] == "PENDING"]

    print(f"\n   WAL committed entries  : {len(committed)}")
    for e in committed:
        print(f"     → txn={e['txn_id']}  op={e['operation']}  data={e['data']}")

    print(f"\n   WAL uncommitted entries : {len(uncommitted)}  ← these are ROLLED BACK")
    for e in uncommitted:
        print(f"     → txn={e['txn_id']}  op={e['operation']}  data={e['data']}")
        # In InnoDB, undo log reverses these; here we just skip re-applying them
        # Dave's row may have been written to the in-memory buffer but not committed.
        # SQLite WAL mode: the uncommitted transaction is automatically discarded.

    rows = conn.execute("SELECT * FROM orders").fetchall()
    print(f"\n   Rows after recovery: {rows}")
    print("✅ Carol's order survived. Dave's (uncommitted) did NOT." if len(rows) == 2
          else f"   Row count: {len(rows)}")
    conn.close()


# ══════════════════════════════════════════════════════════════════════
# PART 4 — Show SQLite WAL files on disk (same as InnoDB redo logs)
# ══════════════════════════════════════════════════════════════════════

def demo_wal_files_on_disk():
    print("\n" + "=" * 60)
    print("DEMO 3: Physical WAL files on disk")
    print("=" * 60)

    # SQLite WAL mode creates two sidecar files:
    #   <db>.wal  — the write-ahead log
    #   <db>.shm  — shared memory for coordination
    # InnoDB writes to  ib_logfile0, ib_logfile1  (redo logs)

    for fname in [DB, DB + "-wal", DB + "-shm"]:
        exists = os.path.exists(fname)
        size   = os.path.getsize(fname) if exists else 0
        label  = {
            DB:           "Main database file",
            DB + "-wal":  "WAL log (redo log equivalent)",
            DB + "-shm":  "Shared memory header",
        }[fname]
        print(f"   {'✅' if exists else '❌'}  {fname:30s}  {size:6d} bytes   ← {label}")

    print("\n   InnoDB equivalent files in MySQL data directory:")
    print("      ib_logfile0, ib_logfile1  ← redo logs (WAL)")
    print("      ibdata1                   ← system tablespace")
    print("      *.ibd                     ← per-table data files")


# ── Main ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    setup_db()
    demo_successful_commit()
    demo_crash_and_recovery()
    demo_wal_files_on_disk()

    # Cleanup
    for f in [DB, DB + "-wal", DB + "-shm", WAL_FILE]:
        if os.path.exists(f):
            os.remove(f)
    print("\n🧹 Demo files removed.")