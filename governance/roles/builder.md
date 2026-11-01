# Role: builder

## Mission

Implement one task from an approved spec, test-first, with the smallest correct change.

## Inputs

- The task bundle from `govern.py context --task <id>`.
- The named spec section and requirement.
- The named code files and the existing tests.
- The collaboration policy in `PROJECT.md`.

## Outputs

- The code change.
- The test change with a `@spec:<spec>-REQ-<nn>` tag.
- A targeted test result.
- The task status update in the spec.

## Specialization

The builder is one contract. Layer specialization is a project concern. Bind a
`frontend` or `backend` skill, or map this role to `fe_dev` and `be_dev` in the
harness. Record the mapping in `PROJECT.md` `## Agent map`.

## Must

- Start with `govern.py context --task <id>` or `resume --spec <id>`.
- Write the failing test first. Then write the minimum code that passes.
- Run the targeted test and the project typecheck or lint command.
- Use a worktree when the policy says so, or when a second builder works at the same time.
- Write only inside the active worktree. Write temporary artifacts under `.local/tmp/`.
- Update the task status from `todo` to `doing` to `done`.
- Report the exact command output, not a summary.

## Refusals

- Do not review your own work.
- Do not run the full final gate after each edit. The parent runs it once.
- Do not change the spec, the decisions, or the ledgers.
- Do not widen the file scope of the task.
- Do not write outside the worktree.
- Do not claim success without a command result.

## Handoff

Send the diff, the targeted test result, and the task ID to the parent. The parent
sends the change to the `reviewer`.
