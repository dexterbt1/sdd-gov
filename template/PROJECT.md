---
name: Example Project
layout: single
install_layout: isolated
project_root: ..
spec_dir: specs
id_width: 4
layers: [backend, frontend]
test_globs: ["**/test_*.py", "**/*_test.py", "**/*.test.ts", "**/*.test.tsx", "**/*.test.js"]
tag_pattern: "@spec:(\\d{3,4})-REQ-(\\d{2})"
cmd_test: ""
cmd_lint: ""
capabilities: [tdd, secure-coding]
modules: []
# modules: [qa, provenance, matrix]
# qa_mode: report
# qa_expires: 2026-12-31
# provenance_mode: report
# provenance_expires: 2026-12-31
# bands_mode: report
# bands_expires: 2026-12-31
# bands_size: 10
# epic_mode: report
# epic_expires: 2026-12-31
# metrics-export_mode: report
# metrics-export_expires: 2026-12-31
# metrics_out: .local/tmp/metrics.json
# matrix_mode: report
# matrix_expires: 2026-12-31
# matrix_registry: matrix_registry.tsv
checks: []
worktrees: auto
max_parallel_builders: 2
tasks: optional
bundle_tokens: 8000
memory_max_lines: 200
spec_max_lines: 600
spec_large_max_lines: 1200
spec_hard_max_lines: 1200
project_max_lines: 300
agents_max_words: 1200
budget_overrides: []
---

# Project Profile

This file is the per-project policy. The core governance is vendored under
`governance/`. Edit this file, not the core.

## Context

- What we are building:
- Who uses it:
- The outcome that matters:

## Goals

- 

## Non-goals

- 

## Principles

- 

## Constraints

- Time:
- Budget:
- Platforms:
- Compliance:

## Layers

- `backend/`
- `frontend/`

## Collaboration

- Worktrees: `auto`
- Maximum parallel builders: `2`

## Agent map

The core defines four roles. Map your own agents to them here. This section is
free-form; the checker does not parse it.

- `author`: 
- `builder`: 
- `reviewer`: 
- `qa`: 
- project roles: 

## Builder profiles

The builder is one role. Add layer specialization with skills or harness agents.

- Frontend:
- Backend:
- Other:

## Modules

The core ships `domain` (enforced) and `ste` (optional). The P1 modules `qa`,
`provenance`, `database`, `isolation`, `api`, and `security` are shipped. The P2
modules `bands`, `epic`, `metrics-export`, and `matrix` are shipped. All are
opt-in. A module defaults to `report` and requires an expiry. See
`governance/MODULES.md` for the config keys.

- Current modules: none
- Candidate next module: 

## Checks

Stack commands run with `check --hooks`. Add one command for each line under the
`checks:` key in the frontmatter.

- 

## Standards

### Observed

Facts discovered from the existing code and documents.

- 

### Declared

Choices made by the team during the kickoff.

- 

## Metrics

- Lead time
- Rework count
- Review findings
- Traceability percentage
- Escaped defects
