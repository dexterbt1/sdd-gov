---
name: Greenfield Example
layout: single
install_layout: root
project_root: .
core_dir: ../../governance
spec_dir: specs
id_width: 4
layers: [backend, frontend]
test_globs: ["**/test_*.py", "**/*_test.py"]
tag_pattern: "@spec:(\\d{3,4})-REQ-(\\d{2})"
cmd_test: "python3 -m pytest"
cmd_lint: ""
capabilities: [tdd, secure-coding]
modules: [domain]
domain_mode: enforce
domain_registry: contracts/domain/entities.json
worktrees: auto
max_parallel_builders: 1
tasks: required
bundle_tokens: 8000
memory_max_lines: 200
spec_max_lines: 600
spec_large_max_lines: 1200
spec_hard_max_lines: 1200
project_max_lines: 300
agents_max_words: 1200
budget_overrides: []
---

# Greenfield Example

A complete, passing example. Run:

This example uses the core from the parent repository:

```sh
python3 ../../governance/scripts/govern.py check
python3 ../../governance/scripts/govern.py plan --spec 1
python3 ../../governance/scripts/govern.py context --task T-0001-02
```
