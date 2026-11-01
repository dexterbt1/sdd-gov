# Known issue template

Add one row to `KNOWN_ISSUES.md`.

| Field | Guidance |
| :--- | :--- |
| `ID` | `KI-<spec>-<nn>`. Unique and immutable. |
| `Title` | One sentence that names the gap. |
| `Class` | `SECURITY`, `HARDENING`, `SCALE`, `INTEGRATION`, `UX`, `FEATURE`, or `DOCS`. |
| `Status` | `open`, `scheduled`, `in_progress`, `done`, or `accepted`. |
| `Pickup` | `item NNN`, `spec NNN`, or `none`. |
| `Owning spec` | The spec number. |

## Rules

- The spec links the ID. Do not restate the text in the spec.
- An `accepted` issue needs a rationale in the owning spec.
- A `done` issue names the resolving spec in the spec row.
