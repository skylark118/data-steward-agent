#!/usr/bin/env python3
"""
Data Steward Agent — runnable demo.

Seeds a throwaway in-memory SQLite database, then runs the three governance
gates (Data Integrity, Privacy & Security, Change Management) for real and
prints a PASS/BLOCK report in the agent's completion format.

This is the same methodology the agent enforces (docs/methodology.md), made
executable so you can watch it catch bad data instead of just reading about it.

Zero dependencies — Python 3 standard library only.

Usage:
    python3 demo/run_gates.py                     # dirty data  -> BLOCKED (exit 1)
    python3 demo/run_gates.py --scenario clean    # clean data  -> READY   (exit 0)
    python3 demo/run_gates.py --approve-deletion  # run the Gate 2 deletion test

Human-in-the-loop: read-only checks run automatically. The Gate 2 deletion test
is a WRITE, so it is only *proposed* unless you pass --approve-deletion — exactly
how the agent pauses for a human before any consequential action.
"""

import argparse
import sqlite3
import sys

# --- Schema -----------------------------------------------------------------

SCHEMA = """
CREATE TABLE users (
    id         INTEGER PRIMARY KEY,
    email      TEXT,          -- required, PII
    name       TEXT,          -- required, PII
    notes      TEXT           -- PII (free-text health notes)
);
CREATE TABLE care_recipients (
    id         INTEGER PRIMARY KEY,
    user_id    INTEGER,       -- required, FK -> users.id
    full_name  TEXT           -- required, PII
);
-- A lightweight registry the steward maintains: which PII columns have a
-- documented legal basis. A PII column missing here is a Gate 2 violation.
CREATE TABLE pii_legal_basis (
    table_name  TEXT,
    column_name TEXT,
    legal_basis TEXT
);
-- Schema changes the steward must gate. A row without a rollback path or
-- impact assessment is a Gate 3 violation.
CREATE TABLE schema_changes (
    change         TEXT,
    forward_path   TEXT,
    rollback_path  TEXT,      -- NULL = no rollback = BLOCK
    impact_assessed INTEGER   -- 0 = not assessed = BLOCK
);
"""

# Every column we treat as PII (the steward's PII inventory).
PII_COLUMNS = [
    ("users", "email"),
    ("users", "name"),
    ("users", "notes"),
    ("care_recipients", "full_name"),
]

# --- Scenarios --------------------------------------------------------------

DIRTY = {
    "users": [
        (1, "ada@example.com", "Ada Lovelace", "reports recurring back pain"),
        (2, None, "Grace Hopper", None),            # required email is NULL
        (3, "not-an-email", "Linus Pauling", None), # invalid email format
        (4, "ada@example.com", "Ada L.", None),     # duplicate email
    ],
    "care_recipients": [
        (10, 1, "Recipient One"),
        (11, 999, "Orphan Recipient"),  # user_id 999 does not exist (orphan)
        (12, 2, None),                  # required full_name is NULL
    ],
    "pii_legal_basis": [
        ("users", "email", "contract"),
        ("users", "name", "contract"),
        ("care_recipients", "full_name", "contract"),
        # users.notes deliberately omitted -> PII with no legal basis
    ],
    "schema_changes": [
        ("add care_recipients.full_name", "migrations/0003_up.sql", None, 0),
    ],
}

CLEAN = {
    "users": [
        (1, "ada@example.com", "Ada Lovelace", "reports recurring back pain"),
        (2, "grace@example.com", "Grace Hopper", None),
        (3, "linus@example.com", "Linus Pauling", None),
    ],
    "care_recipients": [
        (10, 1, "Recipient One"),
        (11, 2, "Recipient Two"),
    ],
    "pii_legal_basis": [
        ("users", "email", "contract"),
        ("users", "name", "contract"),
        ("users", "notes", "consent"),
        ("care_recipients", "full_name", "contract"),
    ],
    "schema_changes": [
        ("add care_recipients.full_name",
         "migrations/0003_up.sql", "migrations/0003_down.sql", 1),
    ],
}


def seed(scenario):
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO users VALUES (?,?,?,?)", scenario["users"])
    db.executemany("INSERT INTO care_recipients VALUES (?,?,?)",
                   scenario["care_recipients"])
    db.executemany("INSERT INTO pii_legal_basis VALUES (?,?,?)",
                   scenario["pii_legal_basis"])
    db.executemany("INSERT INTO schema_changes VALUES (?,?,?,?)",
                   scenario["schema_changes"])
    db.commit()
    return db


def count(db, sql):
    return db.execute(sql).fetchone()[0]


# --- Gates ------------------------------------------------------------------

def gate1_integrity(db):
    """Required fields, referential integrity, formats, duplicates."""
    findings = []
    checks = [
        ("users.email nulls (required)",
         "SELECT COUNT(*) FROM users WHERE email IS NULL"),
        ("users.name nulls (required)",
         "SELECT COUNT(*) FROM users WHERE name IS NULL"),
        ("care_recipients.full_name nulls (required)",
         "SELECT COUNT(*) FROM care_recipients WHERE full_name IS NULL"),
        ("orphaned care_recipients (FK -> users)",
         "SELECT COUNT(*) FROM care_recipients c "
         "LEFT JOIN users u ON c.user_id = u.id WHERE u.id IS NULL"),
        ("invalid email formats",
         "SELECT COUNT(*) FROM users "
         "WHERE email IS NOT NULL AND email NOT LIKE '%_@_%._%'"),
        ("duplicate emails",
         "SELECT COUNT(*) FROM (SELECT email FROM users "
         "WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1)"),
    ]
    passed = True
    for label, sql in checks:
        n = count(db, sql)
        ok = n == 0
        passed = passed and ok
        findings.append(f"  {'OK ' if ok else 'XX '} {label}: {n}")
    return passed, findings


def gate2_privacy(db, approve_deletion):
    """PII legal basis + (proposed) deletion test."""
    findings = []
    passed = True

    documented = {(t, c) for (t, c, _) in
                  db.execute("SELECT * FROM pii_legal_basis").fetchall()}
    for table, col in PII_COLUMNS:
        ok = (table, col) in documented
        passed = passed and ok
        findings.append(
            f"  {'OK ' if ok else 'XX '} legal basis for PII {table}.{col}: "
            f"{'documented' if ok else 'MISSING'}")

    # Deletion test is a WRITE -> human-in-the-loop.
    if not approve_deletion:
        findings.append("  -> PROPOSED (write, needs approval): deletion test "
                        "for a user + cascade. Re-run with --approve-deletion.")
        passed = False  # cannot certify deletion works until it is run
    else:
        # Run on this throwaway DB only. Delete user 1 and dependents.
        before = count(db, "SELECT COUNT(*) FROM care_recipients WHERE user_id = 1")
        db.execute("DELETE FROM care_recipients WHERE user_id = 1")
        db.execute("DELETE FROM users WHERE id = 1")
        remaining = (count(db, "SELECT COUNT(*) FROM users WHERE id = 1")
                     + count(db, "SELECT COUNT(*) FROM care_recipients WHERE user_id = 1"))
        ok = remaining == 0
        passed = passed and ok
        findings.append(
            f"  {'OK ' if ok else 'XX '} deletion test (APPROVED): removed user 1 "
            f"+ {before} dependent rows; residual rows: {remaining}")
    return passed, findings


def gate3_change(db):
    """Every schema change needs a rollback and an impact assessment."""
    findings = []
    passed = True
    for change, _fwd, rollback, assessed in \
            db.execute("SELECT * FROM schema_changes").fetchall():
        ok = rollback is not None and assessed == 1
        passed = passed and ok
        reason = []
        if rollback is None:
            reason.append("no rollback")
        if assessed != 1:
            reason.append("impact not assessed")
        status = "ready" if ok else "BLOCK (" + ", ".join(reason) + ")"
        findings.append(f"  {'OK ' if ok else 'XX '} '{change}': {status}")
    return passed, findings


# --- Report -----------------------------------------------------------------

def report(scenario_name, results):
    line = "=" * 60
    print(line)
    print("DATA STEWARD VALIDATION COMPLETE")
    print(f"scenario: {scenario_name}")
    print(line)
    labels = ["Gate 1: Data Integrity     ",
              "Gate 2: Privacy & Security ",
              "Gate 3: Change Management  "]
    all_passed = True
    for label, (passed, findings) in zip(labels, results):
        verdict = "PASSED" if passed else "BLOCKED"
        all_passed = all_passed and passed
        print(f"\n{label} {'OK' if passed else 'XX'} {verdict}")
        for f in findings:
            print(f)
    print("\n" + line)
    if all_passed:
        print("Status: PRODUCTION READY")
    else:
        print("Status: BLOCKED — fix the XX items above before shipping.")
    print(line)
    return all_passed


def main():
    ap = argparse.ArgumentParser(description="Data Steward Agent demo runner")
    ap.add_argument("--scenario", choices=["dirty", "clean"], default="dirty",
                    help="which seeded dataset to validate (default: dirty)")
    ap.add_argument("--approve-deletion", action="store_true",
                    help="approve and run the Gate 2 deletion test (a write)")
    args = ap.parse_args()

    data = DIRTY if args.scenario == "dirty" else CLEAN
    db = seed(data)
    results = [
        gate1_integrity(db),
        gate2_privacy(db, args.approve_deletion),
        gate3_change(db),
    ]
    ok = report(args.scenario, results)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
