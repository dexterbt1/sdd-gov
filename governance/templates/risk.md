# Risk template

Add one row to `RISKS.md`.

| Field | Guidance |
| :--- | :--- |
| `ID` | `RISK-<nnnn>` for a risk, `EXC-<nnnn>` for an exception. |
| `Title` | One sentence. |
| `Status` | `open`, `accepted`, `closed`, or `expired`. |
| `Owner` | A named person or role. |
| `Expires` | An ISO date for `open` or `accepted`. |
| `Rationale` | Why the risk is accepted or closed. |

## Rules

- An `open` or `accepted` row without an expiry is invalid.
- An expired exception fails the check.
- A closed risk keeps the row. Do not delete it.
- A security exception names the control and the compensating measure.
