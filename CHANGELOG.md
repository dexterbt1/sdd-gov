# Changelog

All notable changes to sdd-gov are recorded here.

## 0.4.0 - 2026-11-01

- Four P2 modules: `bands`, `epic`, `metrics-export`, `matrix`.
- `govern.py reserve --size N --owner NAME` reserves a spec band.
- `next-id` skips reserved bands; `reservations.json` supports `bands`.
- `emit registry` adds an `Epic` column and `--by-epic` grouping.
- `metrics --json` and `metrics --out <path>` export metrics.
- `bands`: validates start/end, size, owner, overlaps, and reserved IDs.
- `epic`: requires an epic for specified, in-progress, and completed specs.
- `metrics-export`: guards the JSON export and detects staleness.
- `matrix`: validates the TSV registry, values, baseline, and runner hook.
- `MODULES.md`, `template/PROJECT.md`, `README`, and CI notes updated.
- Numbering adds `M-<nnnn>` for matrix rows.

## 0.3.0 - 2026-11-01

- Six P1 modules: `qa`, `provenance`, `database`, `isolation`, `api`, `security`.
- Modules are opt-in. An enabled module defaults to `report` and requires an expiry.
- `fatal` findings stay errors in both `report` and `enforce`.
- Module context adds parsed `ledgers` and the spec width.
- `doctor` reports each module's mode, expiry, and expired grace.
- Numbering is enforced:
  - `REQ`, `T`, `DEC`, and `KI` follow `id_width`.
  - `DEF`, `TP`, `RISK`, `EXC`, and `W` use four digits.
  - A legacy width is an error.
- `qa`: `DEFECTS.md` with `DEF-0001`, status, owning spec, and a resolving test.
- `provenance`: `THIRD_PARTY.md` with `TP-0001`, source, license, version, commit.
- `database`: migration, schema, and worker-parity declaration checks.
- `isolation`: scope registry and spec `scope` validation.
- `api`: OpenAPI contract inventory, `x-spec` resolution, and manifest parity.
  Requires PyYAML.
- `security`: posture level, control registry, threat model, supply-chain
  declarations, image digest, and declared scans.
- `MODULES.md` marks the shipped modules and the P2 roadmap.
- `template/PROJECT.md` gains module examples and a `checks` list.
- This is a pre-1.0 breaking change: legacy ID widths now fail.

## 0.2.0 - 2026-11-01

- Isolated install layout by default: `sdd-gov/` plus one root `AGENTS.md` pointer.
- `sdd-gov/g` and `sdd-gov/g.cmd` wrappers with no-argument usage.
- Dual-root semantics: `--root` for governance, `--project-root` for the product.
- Ideation: `govern.py idea`, the idea template, and the draft-to-specified gate.
- Module loader with `domain` enforced and `ste` optional.
- `governance/MODULES.md` roadmap for P1 and P2 modules.
- `check --changed` scopes spec checks to touched specs.
- `context` enforces `bundle_tokens` and reports truncation.
- `MEMORY.md` source-citation lint.
- `emit index`, `emit req-index`, and `emit all`.
- Path containment, cross-spec dependency cycles, and `id_width` validation.
- `doctor` reports layout, roots, worktree policy, and pointer health.
- Core roles: author, builder, reviewer, qa. The writer role is project-owned.
- Core skills: kickoff, spec, tdd, review, verification, secure-coding.
- Spec-review checklist in the reviewer role and the review skill.
- `examples/scribe/` reference for a project-owned writer role.
- No `extensions/` directory. Project additions live in the project's harness.

## 0.1.0 - 2026-11-01

- Initial package.
- 10 non-weakenable invariants.
- 5 roles: author, builder, reviewer, qa, scribe.
- 5 gates: intake, spec, build, review, qa and complete.
- 5 ledgers: specs, decisions, known issues, risks, work.
- `govern.py`: check, init, baseline, context, resume, plan, next, find, impact, deps, search, metrics, emit, doctor, upgrade, manifest, selftest.
- Modules: security, aaa, ste.
- Adapters: generic, opencode, claude, codex.
- Greenfield and brownfield examples.
