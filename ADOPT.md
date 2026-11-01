# Adopt sdd-gov

This file is for an AI coding agent. Follow it exactly. Do not improvise.

## The instruction

The human says:

> Adopt the governance at `https://github.com/<org>/sdd-gov` at tag `v0.4.0`. Read
> `ADOPT.md` and follow it exactly. Do not copy a file it does not name. Ask before
> overwriting anything that exists.

## Step 0: Confirm

1. Confirm the repository URL.
2. Confirm the tag or commit. Use a tag, not `main`.
3. Confirm that you may write to the project. If not, stop.

## Step 1: Fetch

Clone the pinned tag into the project temp area:

```sh
git clone --depth 1 --branch <tag> <repo-url> .local/tmp/sdd-gov
```

Do not pipe a remote script to a shell. Do not run a file from the clone before you
read it.

## Step 2: Verify

1. Read `.local/tmp/sdd-gov/sdd-gov.json`.
2. Confirm the `version` and the `ref`.
3. Verify each `sha256` in the manifest against the file.
4. If a checksum does not match, stop and report it.

The manifest covers `governance/`, `template/`, and the root documents. It is the
install manifest, not a full repository inventory.

## Step 3: Detect the project state

- **Greenfield:** no `sdd-gov/`, no root `AGENTS.md`, and no ledger files.
- **Brownfield:** any of those files exists.

If the project already has a governance system, stop and ask the human whether to
merge or replace. Do not overwrite.

## Step 4: Install

The default layout is isolated:

```sh
python3 .local/tmp/sdd-gov/governance/scripts/govern.py init --from .local/tmp/sdd-gov
```

This creates:

- `<project-root>/sdd-gov/` with the core, specs, ledgers, `g`, `g.cmd`, and `README.md`.
- `<project-root>/AGENTS.md` with one pointer to `sdd-gov/AGENTS.md`.

If the project already has a root `AGENTS.md`, pass `--merge-agents` to add the
sdd-gov block, or `--force` to replace it. Without either, `init` refuses and
prints the block to add.

For a root layout instead of the isolated layout:

```sh
python3 .local/tmp/sdd-gov/governance/scripts/govern.py init --layout root --from .local/tmp/sdd-gov
```

For a brownfield project, run:

```sh
sdd-gov/g baseline
```

This grandfathers the existing specs and missing tags. New drift still fails.

## Step 5: Kickoff

Run the interview in `sdd-gov/governance/KICKOFF.md`. Write the answers into:

- `sdd-gov/PROJECT.md`
- `sdd-gov/DECISIONS.md`
- `sdd-gov/RISKS.md` when the security module is active
- `sdd-gov/WORK.md`
- `sdd-gov/specs/0001-<feature>.md`

## Step 6: Verify

```sh
sdd-gov/g check --budget
```

Report the exact result. If the check fails, fix the named finding. Do not weaken
the check.

## Optional: enable a module

Read `sdd-gov/governance/MODULES.md`. Add the module to `modules` in
`sdd-gov/PROJECT.md`, set `<name>_mode: report` and `<name>_expires`, then run
`sdd-gov/g check --budget`.

## Step 7: Stop

Do not start implementation until the kickoff readiness gate passes:

- `sdd-gov/PROJECT.md` has no placeholder.
- Every open decision has an owner and a date.
- The MVP scope has acceptance criteria.
- The first spec exists.
- `sdd-gov/g check --budget` passes.

Report the first spec to author and the first runnable task.

## Discovery

The root `AGENTS.md` pointer, `sdd-gov/README.md`, and `sdd-gov/g` with no arguments
all point to the same place. An agent new to the project starts at the root
`AGENTS.md`.

## Safety

- Pin a tag or a commit.
- Verify the manifest checksums.
- Do not run an unread script.
- Do not overwrite a file without confirmation.
- Do not write outside the active worktree.
- Keep temporary files under `.local/tmp/`.
- Do not edit `sdd-gov/governance/`. Upgrade it instead.

## Upgrade later

```sh
git clone --depth 1 --branch <new-tag> <repo-url> .local/tmp/sdd-gov-next
sdd-gov/g doctor --upstream .local/tmp/sdd-gov-next
sdd-gov/g upgrade --from .local/tmp/sdd-gov-next
sdd-gov/g check --budget
```

An upgrade replaces `governance/` only. It never touches `specs/`, the ledgers,
`PROJECT.md`, the root pointer, `g`, or `g.cmd`.
