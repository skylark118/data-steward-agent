# Sample run — captured output

Real output from `demo/run_gates.py` (Python 3 stdlib only, no install). Regenerate any time by running the commands below.

## 1. Dirty data → BLOCKED

The steward catches deliberately seeded violations and refuses to ship.

```
$ python3 demo/run_gates.py
============================================================
DATA STEWARD VALIDATION COMPLETE
scenario: dirty
============================================================

Gate 1: Data Integrity      XX BLOCKED
  XX  users.email nulls (required): 1
  OK  users.name nulls (required): 0
  XX  care_recipients.full_name nulls (required): 1
  XX  orphaned care_recipients (FK -> users): 1
  XX  invalid email formats: 1
  XX  duplicate emails: 1

Gate 2: Privacy & Security  XX BLOCKED
  OK  legal basis for PII users.email: documented
  OK  legal basis for PII users.name: documented
  XX  legal basis for PII users.notes: MISSING
  OK  legal basis for PII care_recipients.full_name: documented
  -> PROPOSED (write, needs approval): deletion test for a user + cascade. Re-run with --approve-deletion.

Gate 3: Change Management   XX BLOCKED
  XX  'add care_recipients.full_name': BLOCK (no rollback, impact not assessed)

============================================================
Status: BLOCKED — fix the XX items above before shipping.
============================================================
(exit code: 1)
```

## 2. Clean data, deletion test approved → PRODUCTION READY

With violations fixed and a human approving the Gate 2 deletion test, all three gates pass.

```
$ python3 demo/run_gates.py --scenario clean --approve-deletion
============================================================
DATA STEWARD VALIDATION COMPLETE
scenario: clean
============================================================

Gate 1: Data Integrity      OK PASSED
  OK  users.email nulls (required): 0
  OK  users.name nulls (required): 0
  OK  care_recipients.full_name nulls (required): 0
  OK  orphaned care_recipients (FK -> users): 0
  OK  invalid email formats: 0
  OK  duplicate emails: 0

Gate 2: Privacy & Security  OK PASSED
  OK  legal basis for PII users.email: documented
  OK  legal basis for PII users.name: documented
  OK  legal basis for PII users.notes: documented
  OK  legal basis for PII care_recipients.full_name: documented
  OK  deletion test (APPROVED): removed user 1 + 1 dependent rows; residual rows: 0

Gate 3: Change Management   OK PASSED
  OK  'add care_recipients.full_name': ready

============================================================
Status: PRODUCTION READY
============================================================
(exit code: 0)
```

> Note: running `--scenario clean` *without* `--approve-deletion` still reports BLOCKED on Gate 2 — the deletion test is a write, so the steward will not certify it until a human approves. That pause is the point.
