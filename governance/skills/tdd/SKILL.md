---
name: tdd
description: Implement one spec task test-first with a red-green-refactor loop and a targeted test run.
---

# Test-driven development

Use this skill for a code change in a project that binds the `tdd` capability.

## Method

1. Read the task bundle from `govern.py context --task <id>`.
2. Write a failing test. Run it. Confirm the failure for the expected reason.
3. Write the minimum code that passes.
4. Run the targeted test. Confirm the pass.
5. Refactor without a behavior change. Run the test again.
6. Update the task status to `done`.

## Rules

- Do not write code before the test.
- Do not delete a test to make the suite pass.
- Do not widen the file scope.
- Do not run the full final gate after each edit. Run the targeted test only.
- Report the exact command and the exact output.
- Keep the change small enough to review.
