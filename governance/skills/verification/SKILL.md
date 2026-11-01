---
name: verification
description: Verify a change against the real artifact and report exact evidence, never a self-report.
---

# Verification discipline

Use this skill before you declare a task done, and for every QA pass.

## Method

1. State the claim you will verify.
2. Name the real artifact: the file, the command, the request, or the screen.
3. Run the smallest check that can falsify the claim.
4. Record the exact command and the exact output.
5. If the check fails, report the failure. Do not soften it.
6. If you cannot run the check, say so. Do not claim success.

## Rules

- A passing unit test does not prove an integrated behavior.
- A summary does not prove a file content.
- A self-report does not prove a result.
- Keep evidence inside the worktree under `.local/tmp/`.
- Distinguish `verified`, `partial`, and `unverified` in every report.
