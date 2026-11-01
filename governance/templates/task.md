# Task template

Add a row to the `## Tasks` table in a spec.

| Field | Guidance |
| :--- | :--- |
| `ID` | `T-<spec>-<nn>`. Unique and immutable. |
| `Task` | One short action. |
| `REQ` | The requirement ID that the task implements. |
| `Depends on` | A comma-separated task ID list, or `—`. |
| `Files` | A comma-separated file or glob list. This is the write scope. |
| `Status` | `todo`, `doing`, `done`, or `blocked`. |

## Rules

- Two tasks in the same wave MUST have disjoint file scopes.
- A task with no `REQ` is not traceable.
- A task with no `Files` is not parallel-safe.
- `govern.py plan --spec <id>` prints the dependency waves.
- `govern.py next --spec <id>` prints the first runnable task.
