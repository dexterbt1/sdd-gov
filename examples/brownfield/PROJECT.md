---
name: Brownfield Example
layout: single
install_layout: root
project_root: .
spec_dir: specs
id_width: 3
layers: [backend]
test_globs: ["**/test_*.py", "**/*_test.py"]
tag_pattern: "@spec:(\\d{3,4})-REQ-(\\d{2})"
cmd_test: "python3 -m pytest"
cmd_lint: ""
capabilities: [tdd]
modules: []
worktrees: auto
max_parallel_builders: 1
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

# Brownfield Example

An existing spec without a test tag. `governance/baseline.json` grandfathers it.
New drift still fails. Run:

This example uses the core from the parent repository:

```sh
python3 ../../governance/scripts/govern.py baseline
python3 ../../governance/scripts/govern.py check
```
