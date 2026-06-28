# Demo — watch the gates run

A self-contained, runnable proof that the Data Steward methodology *works*, not
just reads well. It seeds a throwaway in-memory SQLite database with deliberate
data problems and runs the three governance gates for real.

**No dependencies.** Python 3 standard library only — no `pip install`, no
database server.

## Run it

Validate the dirty dataset (catches the seeded violations, exits non-zero):

```
python3 demo/run_gates.py
```

Validate a clean dataset (all gates pass):

```
python3 demo/run_gates.py --scenario clean
```

Approve and run the Gate 2 deletion test (a write action):

```
python3 demo/run_gates.py --scenario clean --approve-deletion
```

> macOS note: if you paste a command and it errors oddly, retype the quotes —
> smart quotes can replace straight quotes and break the line.

## What it demonstrates

- **Gate 1 — Data Integrity:** null required fields, orphaned records, invalid
  email formats, duplicate emails.
- **Gate 2 — Privacy & Security:** a PII column (`users.notes`) with no
  documented legal basis, plus a deletion test that is **proposed and held for
  human approval** — it only runs with `--approve-deletion`.
- **Gate 3 — Change Management:** a schema change with no rollback script and no
  impact assessment.

The clean dataset still reports **BLOCKED** until you approve the deletion test.
That pause is the whole point: the steward profiles read-only on its own, but
will not certify a consequential write without a human.

See [`sample-report.md`](sample-report.md) for captured output.

## Note on dialect

This demo uses SQLite so it runs anywhere with zero setup. The canonical
production checks in [`../scripts/validation-queries.sql`](../scripts/validation-queries.sql)
target PostgreSQL (e.g. `information_schema`, `pg_constraint`). The logic of the
three gates is identical; only the SQL dialect differs.
