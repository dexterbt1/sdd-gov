# Kickoff

Run the kickoff before any significant work. It establishes the project context that the
governance needs. The agent asks. The human decides.

## When to run

- A new project, greenfield or brownfield.
- A new cross-layer program.
- A change that touches a domain entity, an API contract, an auth boundary, or a security control.

A defect fix, a chore, a refactor, and a documentation change MAY skip the kickoff.

## How to run

0. For a raw idea, create a draft spec first: `sdd-gov/g idea "<title>"`. The kickoff closes its open questions.
1. Ask one round at a time.
2. Number every question.
3. Give a recommended answer for every question.
4. Wait for the human answer. Do not answer for the human.
5. Record each answer in the named artifact.
6. Mark each statement `Observed`, `Given`, `Assumed`, `Estimated`, `Recommended`, or `Open`.

## Round 1: Context

1. What is the product in one sentence?
2. Who is the primary user, and what job do they hire it for?
3. What outcome matters in the next 90 days?
4. What is the explicit non-goal?

## Round 2: Scope

5. What are the three to seven MVP capabilities?
6. What is planned next, but not in the MVP?
7. What existing code, document, or asset must we reuse?
8. What is the first spec number, and what is the first user story?

## Round 3: Constraints and architecture

9. What are the hard constraints: time, budget, platform, compliance, team size?
10. Is the project a single app or a monorepo?
11. Which layers exist, and which stack does each layer use?
12. Which data stores, integrations, and external services are in scope?

## Round 4: Risk and quality

13. What is the trust boundary, and what data is sensitive?
14. What are the top five risks, and what mitigates each?
15. What is the test strategy, and what is the definition of done?
16. What review cadence and evidence standard apply?

## Round 5: Process and measures

17. Which agents or people work on the project, and who reviews?
18. What documentation is required, and for whom?
19. Which metrics prove success?
20. Which assumptions are open, and who owns each?

## Output mapping

| Answer | Artifact |
| :--- | :--- |
| Rounds 1-3 | `PROJECT.md` (`context`, `goals`, `non_goals`, `layers`, `commands`, `constraints`) |
| Round 4 | `PROJECT.md` modules; `RISKS.md`; `KNOWN_ISSUES.md` |
| Round 5 | `PROJECT.md` (`collaboration`, `capabilities`); `MEMORY.md`; `WORK.md` |
| Every open decision | `DECISIONS.md` with status `proposed` |
| The first user story | `specs/0001-<feature>.md` |

## Brownfield: discover the standards

Before you write `PROJECT.md`, inspect the existing project:

- Read `README`, `AGENTS.md`, the build files, and the test layout.
- Record every discovered convention under `Standards: Observed`.
- Record every choice the team makes under `Standards: Declared`.
- Do not overwrite a discovered convention with a guess.

Then run `govern.py baseline` to grandfather the existing specs and missing tags.

## Readiness gate

The kickoff is complete only when:

- `PROJECT.md` has no `TODO` placeholder.
- Every open decision has an owner and a date.
- The MVP scope has acceptance criteria.
- The first spec exists.
- `govern.py check` passes.

Do not start implementation before this gate passes.
