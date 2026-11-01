# Module: ste

## Purpose

Keep specifications and documentation short, active, and unambiguous.

## Enable

Add `ste` to `modules` in `PROJECT.md`. Bind the `ste` check as a project hook:

```yaml
checks:
  - "python3 governance/modules.d/ste/lint_ste.py ."
```

## What it adds

- A contraction check.
- A sentence-length check: 20 words for a procedural step, 25 words for descriptive text.
- An active-voice reminder.
- A list of vague verbs to replace: `handle`, `manage`, `process`, `deal with`, `support`.

## Check

`lint_ste.py` prints one finding per line and exits 1 on a finding. It checks Markdown only.

## Rules

- Write "do not", "cannot", and "is not". Do not use a contraction.
- Start a step with a verb.
- Put the condition before the instruction.
- One sentence states one idea.
- Use a term in one way only.
