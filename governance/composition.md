# Composition

sdd-gov owns a small core. The project owns its agent topology.

| Surface | Owner | Job |
| :--- | :--- | :--- |
| Role | Core | Who does the work |
| Capability | Core | A method bound to a role |
| Module | Core | An optional governance area with a check |
| Skill | Project | A project-supplied instruction pack |
| Hook | Project | A command with exit-code semantics |

## The minimal-opinion contract

The core owns:

- The 10 invariants.
- The 5 gates.
- The 5 ledgers.
- Traceability and retrieval.
- The module loader.

The project owns:

- The stack, the layers, and the commands.
- The agents and the role mapping.
- The documentation and the skill packs.
- The modules it enables.
- The CI and the deployment.

The seam is the upgrade boundary. `govern.py upgrade` replaces `governance/` only.
Every other file is project-owned and survives an upgrade. `PROJECT.md` is
free-form; the core reads the keys it needs and ignores the rest.

## Core roles

The core ships four roles: `author`, `builder`, `reviewer`, `qa`. A role contract
lives in `governance/roles/`.

A project MAY add a role in its own harness. It MUST record the mapping in
`PROJECT.md` under `## Agent map`. The core does not parse that section.

The `builder` is one contract. A project specializes it with layer skills or
separate harness agents, for example `fe_dev` and `be_dev`. The `reviewer` has
`SPEC_REVIEW` and `IMPLEMENTATION_REVIEW` modes. A project MAY map them to one
agent or two.

## Capabilities

The core ships six capabilities:

- `kickoff`: the project interview.
- `spec`: the requirement and task authoring method.
- `tdd`: the red-green-refactor loop.
- `review`: the spec and implementation review method.
- `verification`: the evidence discipline.
- `secure-coding`: the security checklist.

A capability binds to a role in `PROJECT.md` under `capabilities`. A capability
MUST NOT invoke a role. A role MAY recommend a handoff. The orchestrator invokes
the next role.

## Modules

A module is opt-in. It adds a check and may add configuration keys. It is declared
in `PROJECT.md` under `modules`.

- `domain`: the entity registry check. Enforced.
- `ste`: the Simplified Technical English check. Optional.
- `qa`, `provenance`, `database`, `isolation`, `api`, `security`: shipped P1 modules. Opt-in.
- `bands`, `epic`, `metrics-export`, `matrix`: shipped P2 modules. Opt-in.

A module MUST NOT weaken an invariant. A module MUST fail closed when its check
cannot run. A newly enabled module defaults to `report` and requires an expiry. A
`fatal` finding blocks in both `report` and `enforce`.

## Skills and project roles

A skill is a folder with a `SKILL.md` file and a YAML frontmatter with `name` and
`description`. It uses progressive disclosure: the agent sees the name and
description first, and the body only when the task matches.

The core does not prescribe where a project puts its skills, roles, or docs. Put
them where your harness expects them, and record the mapping in `PROJECT.md`. The
core does not own your agent topology.

## Adding a module

1. Add `governance/modules.d/<name>/module.md` and `check.py`.
2. Implement `def check(ctx) -> list[Finding]`.
3. Document the config keys and the default mode.
4. Add a selftest fixture.
5. Run `govern.py check`.

## The non-weakenable rule

A composition MAY add a rule. It MUST NOT disable traceability, independent review,
fail-closed gates, or worktree containment.
