---
name: product-docs
description: Write customer-facing product documentation in the second person and the present tense, with scanning structure and verified links.
---

# Product documentation

Use this skill for a customer-facing page, a how-to, a reference page, or a release note.

This skill is a project extension. The core does not ship it.

## Method

1. Name the reader and the task.
2. State the task before the explanation.
3. Use the second person and the present tense.
4. Use a short step for each action. Start with a verb.
5. Put the condition before the instruction.
6. Add a code sample only when it is runnable or exact.
7. Verify every internal link and every code sample.
8. Remove internal terms, internal references, and RFC 2119 keywords from the rendered page.

## Structure

- A one-sentence purpose.
- A prerequisite list.
- Numbered steps.
- A verification step.
- A next-step link.

## Rules

- Do not invent behavior that the spec does not state.
- Do not copy an internal limitation without a product decision.
- Do not edit a spec, a contract, a route, or a model. Raise a defect instead.
