# Decision template

Add one row to `DECISIONS.md`.

| Field | Guidance |
| :--- | :--- |
| `ID` | `DEC-<spec>-<nn>`. Unique and immutable. |
| `Date` | The date the human accepted the decision. |
| `Status` | `proposed`, `accepted`, `superseded`, or `rejected`. |
| `Decision` | One sentence. State the choice, not the debate. |
| `Owning spec` | The spec number. |
| `Supersedes` | The earlier decision ID, or `—`. |

## Rules

- Record the decision before the code.
- A human accepts the decision.
- A changed decision is a new row or a status update. Do not delete the old row.
- Do not create a second decision log.

## Example

| ID | Date | Status | Decision | Owning spec | Supersedes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| DEC-0001-01 | 2026-01-01 | accepted | Use a simple greeting string. | 1 | — |
