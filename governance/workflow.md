# Workflow

Five gates. Each gate has an input, an action, an exit criterion, and a check.

## G0: Intake

**Input:** a request, an idea, or a defect.

**Action:** decide whether the work needs a spec. Run the kickoff interview for a new project. Run the decision interview when the work touches a domain entity, an API contract, an auth boundary, or a security control.

**Exit:** the project has a `PROJECT.md`, or the change has an owning spec.

**Check:** `govern.py check` passes on the current state.

## Draft and ideation

A raw idea becomes a draft spec:

```sh
sdd-gov/g idea "Offline sync"
```

A draft has `Problem`, `Options`, `Open Questions`, `Assumptions`, and
`Recommendation`. It may have zero requirements. Promotion to `specified` requires:

- Every open question is closed or has an owner.
- At least one requirement exists.
- The decision ledger records each material choice.

## G1: Spec

**Input:** the confirmed decisions.

**Action:** the `author` writes the spec with a user story, the scope, the requirements, the acceptance criteria, and the tasks. Each requirement uses an RFC 2119 level. Each task links a requirement and a file scope.

**Exit:** the spec status is `specified`; a fresh `reviewer` returns `PASS` or an accepted `PASS WITH FINDINGS`.

**Check:** `govern.py check --spec <path>`; spec review.

## G2: Build

**Input:** an approved spec and a runnable task.

**Action:** the `builder` starts with `govern.py context --task <id>`, writes the test first, writes the minimum code, and runs the targeted test. The builder uses a worktree when the collaboration policy requires one.

**Exit:** the task is done; the targeted tests pass.

**Check:** `govern.py check --changed`; the targeted test command.

## G3: Review

**Input:** the integrated diff and the targeted tests.

**Action:** a fresh `reviewer` reads the review packet, the named spec sections, and the changed files. The reviewer checks requirement coverage, test tags, scope, and security claims. The reviewer is read-only.

**Exit:** `PASS` or an accepted `PASS WITH FINDINGS`; no blocker remains.

**Check:** review packet; one review plus one re-review.

## G4: QA and complete

**Input:** the reviewed change.

**Action:** the `qa` role runs the live pass and the full test suite. The parent runs the final gate. The author updates the spec status and the ledgers.

**Exit:** the final gate passes; the QA pass passes; the spec status is `completed`.

**Check:** `govern.py converge --spec <id>`; `govern.py check --budget`.

## Definition of done

- The spec status is `completed`.
- Every requirement has a test tag or `(non-testable)`.
- Every decision is recorded.
- Every deferred limitation has a `KI` row.
- Every accepted risk has an owner and an expiry.
- The targeted gate and the final gate pass.
- The docs change when the change is user-facing.

## Round cap

A phase allows one review plus one re-review. A new blocker permits one final targeted re-review. A non-blocking finding MUST NOT trigger a new round.

## The decision interview

Run this before a new feature spec or a cross-layer change. Ask the whole frontier in one round with numbered questions and a recommended answer. Record the answers in the spec and `DECISIONS.md`.

1. What problem does this solve, and for whom?
2. What is in scope and out of scope?
3. Which existing entities, contracts, or documents does it touch?
4. Which decision is irreversible now, and which is deferrable?
5. What is the failure mode, and what is the blast radius?
6. What is the trust boundary, and what data is sensitive?
7. How will we verify it?
8. What must stay true after the change?

## Retrieval protocol

1. For structured facts, call `govern.py`.
2. For normative text, read the named spec section.
3. For implementation, read the named code file.
4. Do not load the full corpus.
5. After a compaction, run `govern.py resume --spec <id>` or `context --task <id>` again.

## Spec size

- Standard: 600 lines.
- Large: 1,200 lines with `size: large`.
- Hard ceiling: 1,200 lines.
- An override requires an owner, a reason, and an expiry in `PROJECT.md`.
- Split when the spec contains two or more independent user stories, spans two or more layers with no shared contract, or crosses the hard ceiling.
