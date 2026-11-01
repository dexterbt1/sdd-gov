# Module: qa

## Purpose

Track defects in one ledger and require a reproducing check before a defect closes.

## Enable

```yaml
modules: [qa]
qa_mode: report
qa_expires: 2026-12-31
qa_defects: DEFECTS.md
```

## Defect ledger

| ID | Title | Status | Spec | Test |
| :--- | :--- | :--- | :--- | :--- |
| DEF-0001 | Broken greeting | fixed | 1 | `@spec:0001-REQ-01` |

- `ID` is `DEF-<nnnn>`.
- `Status` is `open`, `fixed`, `verified`, `closed`, or `accepted`.
- `Spec` is the owning spec number.
- `Test` is a `@spec:<spec>-REQ-<nn>` tag or `(non-testable)`.
- A `fixed` or `verified` defect MUST have a resolving test.

## Optional test plan

Set `qa_test_plan: TEST_PLAN.md` and `qa_require_test_plan: true` to require every
completed spec to appear in the plan.

## Check

- A missing ledger is `fatal`.
- An invalid ID, a duplicate, an invalid status, or an unknown spec is an error.
- A closed defect without a resolving test is an error.
