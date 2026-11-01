#!/usr/bin/env python3
"""sdd-gov: a small, fail-closed governance engine for spec-driven work.

The engine is intentionally stdlib-only. It reads Markdown specs and ledgers,
validates traceability, and generates derived views. It never rewrites product
code and never runs a project hook unless the caller asks for it.
"""

from __future__ import annotations

import argparse
import contextlib
import fnmatch
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frontmatter  # noqa: E402

SPEC_STATUSES = {
    "draft",
    "specified",
    "in_progress",
    "completed",
    "superseded",
    "planned",
    "reserved",
}
TASK_STATUSES = {"todo", "doing", "done", "blocked"}
DECISION_STATUSES = {"proposed", "accepted", "superseded", "rejected"}
ISSUE_STATUSES = {"open", "scheduled", "in_progress", "done", "accepted"}
RISK_STATUSES = {"open", "accepted", "closed", "expired"}
WORK_STATUSES = {"now", "next", "later", "blocked", "done"}

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    ".local",
    "coverage-out",
    "__pycache__",
    ".pytest_cache",
    ".playwright-cli",
    ".mypy_cache",
    ".ruff_cache",
}

DEFAULTS = {
    "name": "Example Project",
    "layout": "single",
    "install_layout": "root",
    "project_root": ".",
    "core_dir": "governance",
    "spec_dir": "specs",
    "id_width": 4,
    "layers": [],
    "test_globs": [
        "**/test_*.py",
        "**/*_test.py",
        "**/*.test.ts",
        "**/*.test.tsx",
        "**/*.test.js",
        "**/*_test.go",
        "**/*Test.java",
    ],
    "tag_pattern": r"@spec:(\d{3,4})-REQ-(\d{2})",
    "capabilities": ["tdd"],
    "modules": [],
    "worktrees": "auto",
    "max_parallel_builders": 2,
    "tasks": "optional",
    "bundle_tokens": 8000,
    "memory_max_lines": 200,
    "spec_max_lines": 600,
    "spec_large_max_lines": 1200,
    "spec_hard_max_lines": 1200,
    "project_max_lines": 300,
    "agents_max_words": 1200,
    "pointer_max_lines": 40,
    "budget_overrides": [],
}

REQ_HEADING = re.compile(r"^#{2,4}\s+`?(REQ-(\d{3,4})-(\d{2}))`?\s*:?\s*(.*)$")
SPEC_FILE = re.compile(r"^(\d{3,4})[_-].*\.md$")
TASK_ID = re.compile(r"^T-(\d{3,4})-(\d{2})$")
DECISION_ID = re.compile(r"^DEC-(\d{3,4})-(\d{2})$")
ISSUE_ID = re.compile(r"^KI-(\d{3,4})-(\d{2})$")
RISK_ID = re.compile(r"^(?:RISK|EXC)-\d{4}$")
WORK_ID = re.compile(r"^W-\d{4}$")


def today():
    return date.today().isoformat()


def rel(path, root):
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except ValueError:
        return str(path)


def issue(errors, path, message):
    errors.append("%s: %s" % (path, message))


def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_project(root):
    profile = dict(DEFAULTS)
    project = Path(root) / "PROJECT.md"
    if project.exists():
        data, _body, _errors = frontmatter.read(project)
        for key, value in data.items():
            profile[key] = value
    return profile


def split_row(line):
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    cells = []
    for cell in text.split("|"):
        cell = cell.strip()
        if cell.startswith("`") and cell.endswith("`") and len(cell) >= 2:
            cell = cell[1:-1].strip()
        cells.append(cell)
    return cells


def normalize_header(value):
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def is_separator(cells):
    return bool(cells) and all(
        re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell != ""
    )


def parse_table(lines):
    rows = []
    header = None
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = split_row(line)
        if not cells:
            continue
        if is_separator(cells):
            continue
        if header is None:
            header = [normalize_header(cell) for cell in cells]
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def parse_reqs(body):
    reqs = []
    for line in body.splitlines():
        match = REQ_HEADING.match(line.strip())
        if not match:
            continue
        title = match.group(4).strip()
        reqs.append(
            {
                "id": match.group(1),
                "spec": int(match.group(2)),
                "spec_part": match.group(2),
                "req_part": match.group(3),
                "number": match.group(3),
                "title": title,
                "non_testable": "(non-testable)" in title.lower(),
            }
        )
    return reqs


def parse_tasks(body):
    lines = body.splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^##\s+Tasks\s*$", line.strip(), re.IGNORECASE):
            start = index + 1
            break
    if start is None:
        return []
    table = []
    for line in lines[start:]:
        if line.strip().startswith("|"):
            table.append(line)
        elif table:
            break
    return parse_table(table)


def load_specs(root):
    root = Path(root)
    profile = load_project(root)
    spec_dir = root / str(profile["spec_dir"])
    specs = []
    if not spec_dir.exists():
        return specs
    for path in sorted(spec_dir.glob("*.md")):
        if path.name.startswith("_"):
            continue
        data, body, errors = frontmatter.read(path)
        spec = {
            "path": path,
            "rel": rel(path, root),
            "fm": data,
            "body": body,
            "errors": errors,
            "lines": len(read_text(path).splitlines()),
        }
        spec["id"] = data.get("id")
        spec["status"] = data.get("status")
        spec["reqs"] = parse_reqs(body)
        spec["tasks"] = parse_tasks(body)
        specs.append(spec)
    return specs


def load_ledger(root, name):
    path = Path(root) / name
    if not path.exists():
        return [], []
    lines = [line for line in read_text(path).splitlines() if line.strip().startswith("|")]
    return parse_table(lines), []


def scan_tags(root, profile, project_root=None):
    root = Path(root)
    scan_root = Path(project_root).resolve() if project_root else root
    pattern = profile.get("tag_pattern") or DEFAULTS["tag_pattern"]
    try:
        regex = re.compile(pattern)
    except re.error:
        regex = re.compile(DEFAULTS["tag_pattern"])
    tags = set()
    seen = set()
    globs = as_list(profile.get("test_globs")) or DEFAULTS["test_globs"]
    for glob in globs:
        for path in scan_root.rglob(str(glob)):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            try:
                relative = path.relative_to(scan_root)
            except ValueError:
                relative = path
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            if path.suffix.lower() not in {
                ".py",
                ".js",
                ".jsx",
                ".ts",
                ".tsx",
                ".go",
                ".rs",
                ".java",
                ".kt",
                ".rb",
                ".php",
                ".cs",
                ".swift",
            }:
                continue
            text = read_text(path)
            for match in regex.finditer(text):
                try:
                    spec_number = match.group(1)
                    req_number = match.group(2)
                except IndexError:
                    continue
                tags.add((int(spec_number), "REQ-%s-%s" % (spec_number, req_number)))
    return tags


def resolve_project_root(root, profile, value=None):
    raw = value if value is not None else profile.get("project_root", ".")
    path = Path(str(raw))
    if not path.is_absolute():
        path = Path(root) / path
    return path.resolve()


def changed_files(project_root):
    project_root = Path(project_root)
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    others = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    if others.returncode == 0:
        files += [line.strip() for line in others.stdout.splitlines() if line.strip()]
    return files


MEMORY_ENTRY = re.compile(r"^- \[\d{4}-\d{2}-\d{2}\] .+ Source: .+$")


def lint_memory(root, errors):
    path = Path(root) / "MEMORY.md"
    if not path.exists():
        return
    for number, line in enumerate(read_text(path).splitlines(), 1):
        text = line.strip()
        if not text or text.startswith(("#", "<!--", ">")):
            continue
        if not text.startswith("- "):
            continue
        if not MEMORY_ENTRY.match(text):
            errors.append("MEMORY.md:%d: entry needs '[YYYY-MM-DD]' and 'Source: ...'" % number)


ABS_PATH = re.compile(r"(?<![A-Za-z0-9])(/(?:Users|home|var|tmp|opt|etc|mnt|srv)/[^\s`\"')]+)")
WIN_PATH = re.compile(r"\b[A-Za-z]:\\[^\s`\"')]+")
PARENT_PATH = re.compile(r"(?:^|[\s(])\.\./")


def check_paths(root, errors, warnings):
    root = Path(root)
    targets = list((root / "specs").glob("*.md"))
    targets += [
        root / name
        for name in ("DECISIONS.md", "KNOWN_ISSUES.md", "RISKS.md", "WORK.md", "MEMORY.md")
    ]
    for path in targets:
        if not path.exists():
            continue
        rel_path = path.relative_to(root)
        for number, line in enumerate(read_text(path).splitlines(), 1):
            for match in ABS_PATH.finditer(line):
                errors.append("%s:%d: absolute path %s" % (rel_path, number, match.group(1)))
            for match in WIN_PATH.finditer(line):
                errors.append("%s:%d: absolute path %s" % (rel_path, number, match.group(0)))
            if PARENT_PATH.search(line):
                warnings.append("%s:%d: parent-relative path" % (rel_path, number))


def check_spec_cycles(specs, errors):
    by_id = {spec["id"]: spec for spec in specs if isinstance(spec["id"], int)}
    visiting = set()
    visited = set()

    def visit(node, stack):
        if node in visiting:
            cycle = stack[stack.index(node) :] + [node]
            errors.append(
                "specs: dependency cycle: %s"
                % " -> ".join(str(item) for item in cycle)
            )
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in as_list(by_id[node]["fm"].get("depends_on")):
            try:
                dep_id = int(dep)
            except (TypeError, ValueError):
                continue
            if dep_id in by_id:
                visit(dep_id, stack + [node])
        visiting.discard(node)
        visited.add(node)

    for spec_id in by_id:
        visit(spec_id, [])


def load_modules(root, project_root, profile, specs, tags, changed, errors, warnings):
    names = as_list(profile.get("modules"))
    if not names:
        return
    root = Path(root)
    ledgers = {
        "decisions": load_ledger(root, "DECISIONS.md")[0],
        "issues": load_ledger(root, "KNOWN_ISSUES.md")[0],
        "risks": load_ledger(root, "RISKS.md")[0],
        "work": load_ledger(root, "WORK.md")[0],
    }
    for raw_name in names:
        name = str(raw_name).strip()
        if not name:
            continue
        core_dir = root / str(profile.get("core_dir", "governance"))
        check_file = core_dir / "modules.d" / name / "check.py"
        if not check_file.exists():
            errors.append("modules: %s: check.py not found" % name)
            continue
        mode = str(profile.get("%s_mode" % name, "report")).lower()
        if mode not in ("off", "report", "enforce"):
            errors.append("PROJECT.md: %s_mode must be off, report, or enforce" % name)
            continue
        if mode == "off":
            continue
        if mode == "report":
            expires = profile.get("%s_expires" % name)
            if not expires:
                errors.append(
                    "PROJECT.md: %s_mode is report; %s_expires is required"
                    % (name, name)
                )
            else:
                check_expiry(expires, "PROJECT.md: %s_expires" % name, errors)
        try:
            module_spec = importlib.util.spec_from_file_location(
                "sdd_gov_module_%s" % name, check_file
            )
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            errors.append("modules: %s: cannot load: %s" % (name, exc))
            continue
        ctx = {
            "root": root,
            "project_root": Path(project_root),
            "profile": profile,
            "specs": specs,
            "tags": tags,
            "changed": changed,
            "ledgers": ledgers,
            "spec_width": int(profile.get("id_width", 4) or 4),
        }
        try:
            findings = module.check(ctx) or []
        except Exception as exc:  # noqa: BLE001
            errors.append("modules: %s: check failed: %s" % (name, exc))
            continue
        for finding in findings:
            severity = "error"
            path = name
            message = ""
            if isinstance(finding, (list, tuple)) and len(finding) >= 3:
                severity, path, message = finding[0], finding[1], finding[2]
            elif isinstance(finding, (list, tuple)) and len(finding) == 2:
                path, message = finding
            else:
                message = str(finding)
            severity = str(severity).lower()
            if severity not in ("fatal", "error", "warning", "info"):
                severity = "error"
            if severity == "fatal":
                target = errors
            elif mode == "report" or severity in ("warning", "info"):
                target = warnings
            else:
                target = errors
            target.append("%s: %s" % (path, message))


def bundle_tokens(bundle):
    return len(json.dumps(bundle, ensure_ascii=False)) // 4 + 1


def truncate_bundle(bundle, budget):
    budget = int(budget)
    dropped = []
    if bundle_tokens(bundle) > budget:
        for key in ("decisions", "issues"):
            if bundle_tokens(bundle) <= budget:
                break
            for item in bundle.get(key, []):
                dropped.append("%s:%s" % (key, item))
            bundle[key] = []
    if bundle_tokens(bundle) > budget:
        files = bundle.get("files", [])
        if files:
            dropped.extend("file:%s" % item for item in files)
            bundle["files"] = []
    if bundle_tokens(bundle) > budget:
        for req in bundle.get("requirements", []):
            if "title" in req:
                req["title"] = req["title"][:60]
        if bundle_tokens(bundle) > budget:
            bundle["requirements"] = [
                {"id": req.get("id"), "ref": req.get("ref")}
                for req in bundle.get("requirements", [])
            ]
    bundle["truncated"] = bool(dropped) or bundle_tokens(bundle) > budget
    bundle["dropped"] = dropped
    bundle["budget_tokens"] = budget
    return bundle


POINTER_START = "<!-- sdd-gov:start -->"
POINTER_END = "<!-- sdd-gov:end -->"


def root_pointer_block():
    return "\n".join(
        [
            POINTER_START,
            "This project uses sdd-gov. Read `sdd-gov/AGENTS.md`.",
            "Run `sdd-gov/g check --budget`.",
            "Specs and ledgers live under `sdd-gov/`.",
            "Write temporary files under `.local/tmp/`.",
            POINTER_END,
        ]
    )


def install_pointer(project_root, merge=False, force=False):
    path = Path(project_root) / "AGENTS.md"
    block = root_pointer_block()
    if not path.exists():
        write_text(path, block + "\n")
        return True
    text = read_text(path)
    if POINTER_START in text and POINTER_END in text:
        return True
    if merge or force:
        write_text(path, text.rstrip() + "\n\n" + block + "\n")
        return True
    return False


def ensure_gitignore(project_root, entries):
    path = Path(project_root) / ".gitignore"
    text = read_text(path) if path.exists() else ""
    lines = {line.strip() for line in text.splitlines()}
    missing = [entry for entry in entries if entry not in lines]
    if not missing:
        return
    separator = "" if not text.strip() else ("\n" if text.endswith("\n") else "\n\n")
    write_text(
        path,
        text.rstrip() + separator + "# sdd-gov\n" + "\n".join(missing) + "\n",
    )


def path_matches(pattern, path):
    pattern = pattern.strip().strip("`")
    path = path.strip()
    if not pattern:
        return False
    if pattern.endswith("/**"):
        return path == pattern[:-3] or path.startswith(pattern[:-2])
    if fnmatch.fnmatch(path, pattern):
        return True
    if fnmatch.fnmatch(Path(path).name, pattern):
        return True
    return False


def spec_touches(spec, changed_path):
    for pattern in as_list(spec["fm"].get("touches")):
        if path_matches(str(pattern), changed_path):
            return True
    for task in spec["tasks"]:
        for path in as_list(task.get("files")):
            for part in str(path).split(","):
                if path_matches(part, changed_path):
                    return True
    return False


def load_baseline(root):
    path = Path(root) / "governance" / "baseline.json"
    if not path.exists():
        return None
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        return {"__invalid__": True}


def baseline_sets(baseline):
    if not baseline or baseline.get("__invalid__"):
        return set(), set()
    specs = set()
    for value in baseline.get("grandfathered_specs", []):
        try:
            specs.add(int(value))
        except (TypeError, ValueError):
            pass
    missing = set(str(value) for value in baseline.get("allowed_missing", []))
    return specs, missing


def check_expiry(value, label, errors):
    if not value or str(value).strip() in ("", "—", "-", "none"):
        return
    try:
        expires = date.fromisoformat(str(value).strip())
    except ValueError:
        errors.append("%s: invalid expiry date %r" % (label, value))
        return
    if expires < date.today():
        errors.append("%s: expired on %s" % (label, expires.isoformat()))


def validate_ledgers(root, profile, errors):
    decisions, _ = load_ledger(root, "DECISIONS.md")
    issues, _ = load_ledger(root, "KNOWN_ISSUES.md")
    risks, _ = load_ledger(root, "RISKS.md")
    work, _ = load_ledger(root, "WORK.md")
    width = int(profile.get("id_width", 4) or 4)

    decision_ids = set()
    for index, row in enumerate(decisions, 2):
        decision_id = row.get("id", "").strip()
        if not decision_id:
            continue
        match = DECISION_ID.match(decision_id)
        if not match:
            errors.append("DECISIONS.md: row %d: invalid id %r" % (index, decision_id))
        elif len(match.group(1)) != width:
            errors.append(
                "DECISIONS.md: %s: spec part must use %d digits" % (decision_id, width)
            )
        if decision_id in decision_ids:
            errors.append("DECISIONS.md: duplicate id %s" % decision_id)
        decision_ids.add(decision_id)
        status = row.get("status", "").strip().lower()
        if status and status not in DECISION_STATUSES:
            errors.append("DECISIONS.md: %s: invalid status %r" % (decision_id, status))
        supersedes = row.get("supersedes", "").strip()
        if supersedes and supersedes not in ("—", "-", "none") and supersedes not in decision_ids:
            if DECISION_ID.match(supersedes):
                errors.append("DECISIONS.md: %s: unknown supersedes %s" % (decision_id, supersedes))

    issue_ids = set()
    for index, row in enumerate(issues, 2):
        issue_id = row.get("id", "").strip()
        if not issue_id:
            continue
        match = ISSUE_ID.match(issue_id)
        if not match:
            errors.append("KNOWN_ISSUES.md: row %d: invalid id %r" % (index, issue_id))
        elif len(match.group(1)) != width:
            errors.append(
                "KNOWN_ISSUES.md: %s: spec part must use %d digits" % (issue_id, width)
            )
        if issue_id in issue_ids:
            errors.append("KNOWN_ISSUES.md: duplicate id %s" % issue_id)
        issue_ids.add(issue_id)
        status = row.get("status", "").strip().lower()
        if status and status not in ISSUE_STATUSES:
            errors.append("KNOWN_ISSUES.md: %s: invalid status %r" % (issue_id, status))

    risk_ids = set()
    for index, row in enumerate(risks, 2):
        risk_id = row.get("id", "").strip()
        if not risk_id:
            continue
        if not RISK_ID.match(risk_id):
            errors.append("RISKS.md: row %d: invalid id %r" % (index, risk_id))
        if risk_id in risk_ids:
            errors.append("RISKS.md: duplicate id %s" % risk_id)
        risk_ids.add(risk_id)
        status = row.get("status", "").strip().lower()
        if status and status not in RISK_STATUSES:
            errors.append("RISKS.md: %s: invalid status %r" % (risk_id, status))
        if status in ("accepted", "open"):
            check_expiry(row.get("expires"), "RISKS.md: %s" % risk_id, errors)

    work_ids = set()
    for index, row in enumerate(work, 2):
        work_id = row.get("id", "").strip()
        if not work_id:
            continue
        if not WORK_ID.match(work_id):
            errors.append("WORK.md: row %d: invalid id %r" % (index, work_id))
        if work_id in work_ids:
            errors.append("WORK.md: duplicate id %s" % work_id)
        work_ids.add(work_id)
        status = row.get("status", "").strip().lower()
        if status and status not in WORK_STATUSES:
            errors.append("WORK.md: %s: invalid status %r" % (work_id, status))

    return decision_ids, issue_ids, risk_ids


def task_waves(tasks, errors, path):
    by_id = {}
    for task in tasks:
        task_id = task.get("id", "").strip()
        if not task_id:
            continue
        if task_id in by_id:
            errors.append("%s: duplicate task id %s" % (path, task_id))
        by_id[task_id] = task
    for task in tasks:
        task_id = task.get("id", "").strip()
        status = task.get("status", "").strip().lower()
        if status and status not in TASK_STATUSES:
            errors.append("%s: task %s: invalid status %r" % (path, task_id, status))
        for dep in split_deps(task.get("depends_on")):
            if dep not in by_id:
                errors.append("%s: task %s: unknown dependency %s" % (path, task_id, dep))
            if dep == task_id:
                errors.append("%s: task %s: depends on itself" % (path, task_id))

    remaining = set(by_id)
    done = set()
    waves = []
    while remaining:
        wave = [
            task_id
            for task_id in remaining
            if all(dep in done for dep in split_deps(by_id[task_id].get("depends_on")))
        ]
        if not wave:
            errors.append("%s: task dependency cycle" % path)
            break
        waves.append(sorted(wave))
        remaining -= set(wave)
        done |= set(wave)

    for wave in waves:
        owners = {}
        for task_id in wave:
            task = by_id[task_id]
            for value in as_list(task.get("files")):
                for file_path in str(value).split(","):
                    file_path = file_path.strip().strip("`")
                    if not file_path:
                        continue
                    if file_path in owners and owners[file_path] != task_id:
                        errors.append(
                            "%s: scope conflict in one wave: %s and %s both write %s"
                            % (path, owners[file_path], task_id, file_path)
                        )
                    owners[file_path] = task_id
    return waves, by_id


def split_deps(value):
    value = str(value or "").strip()
    if value in ("", "—", "-", "none", "None"):
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def budget_limit(spec, profile, overrides):
    limit = int(profile.get("spec_hard_max_lines", 1200))
    if str(spec["fm"].get("size", "")).lower() == "large":
        limit = max(limit, int(profile.get("spec_large_max_lines", 1200)))
    override = overrides.get(spec["rel"])
    if override:
        limit = max(limit, int(override["max"]))
    return limit


def parse_overrides(profile, errors):
    overrides = {}
    for raw in as_list(profile.get("budget_overrides")):
        text = str(raw)
        parts = text.split(":")
        if len(parts) < 3:
            errors.append("PROJECT.md: invalid budget override %r" % text)
            continue
        path, maximum, expires = parts[0], parts[1], parts[2]
        try:
            maximum_int = int(maximum)
        except ValueError:
            errors.append("PROJECT.md: invalid budget override limit %r" % maximum)
            continue
        if expires and expires not in ("—", "-", "none"):
            try:
                if date.fromisoformat(expires) < date.today():
                    errors.append("PROJECT.md: budget override for %s expired on %s" % (path, expires))
            except ValueError:
                errors.append("PROJECT.md: invalid override expiry %r" % expires)
        overrides[path] = {"max": maximum_int, "expires": expires}
    return overrides


def run_check(
    root,
    project_root=None,
    budget=False,
    hooks=False,
    changed=False,
    changed_files_list=None,
):
    root = Path(root).resolve()
    errors = []
    warnings = []
    profile = load_project(root)
    spec_width = int(profile.get("id_width", 4) or 4)
    if project_root is None:
        project_root = resolve_project_root(root, profile)
    else:
        project_root = Path(project_root).resolve()
    specs = load_specs(root)
    tags = scan_tags(root, profile, project_root)
    baseline = load_baseline(root)
    grandfathered, allowed_missing = baseline_sets(baseline)
    overrides = parse_overrides(profile, errors)
    changed_set = None
    if changed:
        files = (
            changed_files_list
            if changed_files_list is not None
            else changed_files(project_root)
        )
        if files is None:
            warnings.append("check: --changed needs a git repository; running a full check")
        else:
            changed_set = set(files)

    if baseline and baseline.get("__invalid__"):
        errors.append("governance/baseline.json: invalid JSON")
    if baseline and baseline.get("expires"):
        check_expiry(baseline.get("expires"), "governance/baseline.json", errors)

    # Always-loaded memory budgets.
    agents = root / "AGENTS.md"
    if agents.exists():
        words = len(re.findall(r"\S+", read_text(agents)))
        if words > int(profile.get("agents_max_words", 1200)):
            errors.append(
                "AGENTS.md: %d words exceeds budget %s"
                % (words, profile.get("agents_max_words"))
            )
    project = root / "PROJECT.md"
    if project.exists():
        lines = len(read_text(project).splitlines())
        if lines > int(profile.get("project_max_lines", 300)):
            errors.append(
                "PROJECT.md: %d lines exceeds budget %s"
                % (lines, profile.get("project_max_lines"))
            )
    memory = root / "MEMORY.md"
    if memory.exists():
        lines = len(read_text(memory).splitlines())
        if lines > int(profile.get("memory_max_lines", 200)):
            errors.append(
                "MEMORY.md: %d lines exceeds budget %s"
                % (lines, profile.get("memory_max_lines"))
            )

    # Specs.
    ids = {}
    for spec in specs:
        path = spec["rel"]
        for error in spec["errors"]:
            errors.append("%s: %s" % (path, error))
        match = SPEC_FILE.match(Path(path).name)
        if not match:
            errors.append("%s: filename must be <id><sep><slug>.md" % path)
        else:
            if len(match.group(1)) != spec_width:
                errors.append("%s: filename id must use %d digits" % (path, spec_width))
        spec_id = spec["id"]
        if not isinstance(spec_id, int):
            errors.append("%s: frontmatter id must be an integer" % path)
        else:
            if spec_id in ids:
                errors.append("%s: duplicate spec id %s" % (path, spec_id))
            ids[spec_id] = spec
            if match and int(match.group(1)) != spec_id:
                errors.append("%s: filename id does not match frontmatter id %s" % (path, spec_id))
        status = spec["status"]
        if status not in SPEC_STATUSES:
            errors.append("%s: invalid status %r" % (path, status))
        if not str(spec["fm"].get("title", "")).strip():
            errors.append("%s: missing title" % path)

        if status in ("specified", "in_progress", "completed"):
            if not spec["reqs"]:
                errors.append(
                    "%s: status %s needs at least one requirement" % (path, status)
                )
            if re.search(r"^##\s+Open Questions\s*$", spec["body"], re.MULTILINE) and re.search(
                r"^\s*-\s*\[ \]", spec["body"], re.MULTILINE
            ):
                errors.append("%s: status %s has an open question" % (path, status))

        if changed_set is not None:
            if not any(spec_touches(spec, file_path) for file_path in changed_set):
                continue

        layers = as_list(spec["fm"].get("layer"))
        allowed_layers = as_list(profile.get("layers"))
        if allowed_layers:
            for layer in layers:
                if str(layer) not in [str(item) for item in allowed_layers]:
                    errors.append("%s: unknown layer %r" % (path, layer))
        for dep in as_list(spec["fm"].get("depends_on")):
            try:
                dep_int = int(dep)
            except (TypeError, ValueError):
                errors.append("%s: invalid depends_on %r" % (path, dep))
                continue
            if dep_int == spec_id:
                errors.append("%s: depends on itself" % path)

        req_ids = set()
        for req in spec["reqs"]:
            if req["id"] in req_ids:
                errors.append("%s: duplicate requirement %s" % (path, req["id"]))
            req_ids.add(req["id"])
            if len(req.get("spec_part", "")) != spec_width:
                errors.append(
                    "%s: %s spec part must use %d digits"
                    % (path, req["id"], spec_width)
                )
            if req["spec"] != spec_id:
                errors.append(
                    "%s: requirement %s does not match spec id %s"
                    % (path, req["id"], spec_id)
                )

        for task in spec["tasks"]:
            task_id = str(task.get("id", "")).strip()
            if not task_id:
                continue
            task_match = TASK_ID.match(task_id)
            if not task_match:
                errors.append("%s: task %s: invalid id" % (path, task_id))
            elif len(task_match.group(1)) != spec_width:
                errors.append(
                    "%s: task %s: spec part must use %d digits"
                    % (path, task_id, spec_width)
                )

        waves, _by_id = task_waves(spec["tasks"], errors, path)

        if status == "completed":
            for req in spec["reqs"]:
                if req["non_testable"]:
                    continue
                if spec_id in grandfathered or req["id"] in allowed_missing:
                    continue
                if (spec_id, req["id"]) not in tags:
                    errors.append("%s: %s has no @spec tag" % (path, req["id"]))

        limit = budget_limit(spec, profile, overrides)
        if spec["lines"] > limit:
            errors.append("%s: %d lines exceeds budget %d" % (path, spec["lines"], limit))
        elif spec["lines"] > int(profile.get("spec_max_lines", 600)) and not (
            spec["rel"] in overrides or str(spec["fm"].get("size", "")).lower() == "large"
        ):
            message = "%s: %d lines exceeds the standard budget %s" % (
                path,
                spec["lines"],
                profile.get("spec_max_lines"),
            )
            if budget:
                errors.append(message)
            else:
                warnings.append(message)

    for spec in specs:
        spec_id = spec["id"]
        for dep in as_list(spec["fm"].get("depends_on")):
            try:
                dep_int = int(dep)
            except (TypeError, ValueError):
                continue
            if dep_int not in ids:
                errors.append("%s: unknown depends_on spec %s" % (spec["rel"], dep))

    decision_ids, issue_ids, _risk_ids = validate_ledgers(root, profile, errors)
    for spec in specs:
        for ref in as_list(spec["fm"].get("decision_refs")):
            if str(ref) not in decision_ids:
                errors.append("%s: unknown decision_ref %s" % (spec["rel"], ref))
        for ref in as_list(spec["fm"].get("issue_refs")):
            if str(ref) not in issue_ids:
                errors.append("%s: unknown issue_ref %s" % (spec["rel"], ref))

    lint_memory(root, errors)
    check_paths(root, errors, warnings)
    check_spec_cycles(specs, errors)
    load_modules(root, project_root, profile, specs, tags, changed_set, errors, warnings)

    # Optional project hooks.
    if hooks:
        for raw in as_list(profile.get("checks")):
            command = str(raw)
            if not command:
                continue
            result = subprocess.run(command, shell=True, cwd=str(project_root))
            if result.returncode != 0:
                errors.append("project hook failed (%d): %s" % (result.returncode, command))

    return errors, warnings, specs, tags, profile


def cmd_check(args):
    root = Path(args.root)
    profile = load_project(root)
    project_root = resolve_project_root(
        root, profile, getattr(args, "project_root", None)
    )
    errors, warnings, _specs, _tags, _profile = run_check(
        root,
        project_root=project_root,
        budget=args.budget,
        hooks=args.hooks,
        changed=args.changed,
    )
    for warning in warnings:
        print("warning: %s" % warning)
    for error in errors:
        print("error: %s" % error)
    if errors:
        print("check: failed (%d errors, %d warnings)" % (len(errors), len(warnings)))
        return 1
    print("check: ok (%d warnings)" % len(warnings))
    return 0


def cmd_fmt(args):
    root = Path(args.root)
    count = 0
    for path in sorted((root / load_project(root)["spec_dir"]).glob("*.md")):
        data, body, errors = frontmatter.read(path)
        if errors or not data:
            continue
        write_text(path, frontmatter.dump(data, body))
        count += 1
    print("fmt: normalized %d specs" % count)
    return 0


def load_reservations(root):
    path = Path(root) / "governance" / "reservations.json"
    if not path.exists():
        return {"reserved": [], "bands": [], "updated": today()}
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        data = {}
    data.setdefault("reserved", [])
    data.setdefault("bands", [])
    return data


def save_reservations(root, data):
    data["updated"] = today()
    write_text(
        Path(root) / "governance" / "reservations.json",
        json.dumps(data, indent=2) + "\n",
    )


def highest_spec_number(root, data):
    specs = load_specs(root)
    highest = max([spec["id"] for spec in specs if isinstance(spec["id"], int)] or [0])
    for value in data.get("reserved", []):
        try:
            highest = max(highest, int(value))
        except (TypeError, ValueError):
            pass
    for band in data.get("bands", []):
        if isinstance(band, dict):
            try:
                highest = max(highest, int(band.get("end", 0)))
            except (TypeError, ValueError):
                pass
    return highest


def cmd_next_id(args):
    root = Path(args.root)
    data = load_reservations(root)
    next_id = highest_spec_number(root, data) + 1
    if args.reserve:
        data["reserved"].append(next_id)
        save_reservations(root, data)
        print("reserved: %d" % next_id)
    else:
        print(next_id)
    return 0


def cmd_reserve(args):
    root = Path(args.root)
    data = load_reservations(root)
    start = highest_spec_number(root, data) + 1
    size = max(1, int(args.size))
    end = start + size - 1
    data["bands"].append(
        {"start": start, "end": end, "owner": args.owner or "unassigned"}
    )
    save_reservations(root, data)
    print("reserved band: %d-%d" % (start, end))
    return 0


def cmd_baseline(args):
    root = Path(args.root)
    profile = load_project(root)
    specs = load_specs(root)
    tags = scan_tags(root, profile)
    grandfathered = sorted(
        spec["id"] for spec in specs if spec["status"] == "completed" and isinstance(spec["id"], int)
    )
    missing = []
    for spec in specs:
        if spec["status"] != "completed":
            continue
        for req in spec["reqs"]:
            if req["non_testable"]:
                continue
            if (spec["id"], req["id"]) not in tags:
                missing.append(req["id"])
    data = {
        "version": 1,
        "created": today(),
        "expires": (date.today() + timedelta(days=180)).isoformat(),
        "grandfathered_specs": grandfathered,
        "allowed_missing": sorted(set(missing)),
    }
    write_text(Path(args.out) if args.out else root / "governance" / "baseline.json", json.dumps(data, indent=2) + "\n")
    print(
        "baseline: %d specs grandfathered, %d missing tags allowed, expires %s"
        % (len(grandfathered), len(set(missing)), data["expires"])
    )
    return 0


def find_spec(specs, spec_id):
    for spec in specs:
        if spec["id"] == spec_id:
            return spec
    return None


def cmd_supersede(args):
    root = Path(args.root)
    specs = load_specs(root)
    old = find_spec(specs, int(args.old))
    new = find_spec(specs, int(args.new))
    if not old or not new:
        print("supersede: both specs must exist")
        return 1
    old["fm"]["status"] = "superseded"
    old["fm"]["superseded_by"] = int(args.new)
    write_text(old["path"], frontmatter.dump(old["fm"], old["body"]))
    print("supersede: %s -> %s" % (args.old, args.new))
    return 0


def cmd_doctor(args):
    root = Path(args.root)
    errors = []
    version_path = root / "governance" / "VERSION"
    version = read_text(version_path).strip() if version_path.exists() else "unknown"
    print("sdd-gov version: %s" % version)
    manifest_path = root / "sdd-gov.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(read_text(manifest_path))
            if manifest.get("version") and manifest.get("version") != version:
                errors.append(
                    "sdd-gov.json version %s does not match governance/VERSION %s"
                    % (manifest.get("version"), version)
                )
        except json.JSONDecodeError:
            errors.append("sdd-gov.json is not valid JSON")
    baseline = load_baseline(root)
    if baseline and baseline.get("__invalid__"):
        errors.append("governance/baseline.json is not valid JSON")
    if baseline and baseline.get("expires"):
        check_expiry(baseline.get("expires"), "governance/baseline.json", errors)
    profile = load_project(root)
    project_root = resolve_project_root(
        root, profile, getattr(args, "project_root", None)
    )
    layout = str(profile.get("install_layout", "root"))
    print("install layout: %s" % layout)
    print("governance root: %s" % root)
    print("project root: %s" % project_root)
    print(
        "worktrees: %s (max parallel builders: %s)"
        % (
            profile.get("worktrees", "auto"),
            profile.get("max_parallel_builders", 2),
        )
    )
    if layout == "isolated":
        pointer = root.parent / "AGENTS.md"
        if not pointer.exists():
            errors.append("root AGENTS.md pointer is missing at %s" % pointer)
        elif POINTER_START not in read_text(pointer):
            errors.append("root AGENTS.md has no sdd-gov block")
    if (
        str(profile.get("worktrees", "auto")) == "required"
        and (project_root / ".git").is_dir()
    ):
        print("warning: worktrees is required but this looks like the main worktree")
    modules = as_list(profile.get("modules"))
    if modules:
        print("modules:")
        for raw_name in modules:
            name = str(raw_name)
            mode = str(profile.get("%s_mode" % name, "report")).lower()
            expires = profile.get("%s_expires" % name)
            print("  %s: mode=%s expires=%s" % (name, mode, expires or "—"))
            if mode == "report" and expires:
                check_expiry(expires, "PROJECT.md: %s_expires" % name, errors)
    else:
        print("modules: none")
    parse_overrides(profile, errors)
    index = root / "specs" / "index.json"
    if index.exists():
        index_time = index.stat().st_mtime
        spec_dir = root / str(profile["spec_dir"])
        stale = [
            path
            for path in spec_dir.glob("*.md")
            if path.stat().st_mtime > index_time
        ]
        if stale:
            print("warning: specs/index.json is stale (%d newer specs)" % len(stale))
    if args.upstream:
        upstream = Path(args.upstream) / "sdd-gov.json"
        if upstream.exists():
            try:
                data = json.loads(read_text(upstream))
                print("upstream version: %s" % data.get("version", "unknown"))
            except json.JSONDecodeError:
                errors.append("upstream sdd-gov.json is not valid JSON")
        else:
            errors.append("upstream path has no sdd-gov.json")
    for error in errors:
        print("error: %s" % error)
    if errors:
        return 1
    print("doctor: ok")
    return 0


def cmd_emit(args):
    root = Path(args.root)
    profile = load_project(root)
    project_root = resolve_project_root(
        root, profile, getattr(args, "project_root", None)
    )
    specs = load_specs(root)
    tags = scan_tags(root, profile, project_root)
    if args.kind in ("index", "all"):
        entries = []
        for spec in specs:
            entries.append(
                {
                    "id": spec["id"],
                    "file": spec["rel"],
                    "title": spec["fm"].get("title", ""),
                    "status": spec["status"],
                    "layer": as_list(spec["fm"].get("layer")),
                    "epic": spec["fm"].get("epic"),
                    "updated": spec["fm"].get("updated"),
                    "touches": as_list(spec["fm"].get("touches")),
                }
            )
        out = root / str(profile["spec_dir"]) / "index.json"
        write_text(out, json.dumps(entries, indent=2) + "\n")
        print("index: %s" % out.relative_to(root))
    if args.kind in ("req-index", "all"):
        req_entries = []
        for spec in specs:
            for req in spec["reqs"]:
                req_entries.append(
                    {
                        "id": req["id"],
                        "spec": spec["id"],
                        "title": req["title"],
                        "status": spec["status"],
                        "non_testable": req["non_testable"],
                        "tagged": req["non_testable"]
                        or (spec["id"], req["id"]) in tags,
                    }
                )
        out = root / str(profile["spec_dir"]) / "req_index.json"
        write_text(out, json.dumps(req_entries, indent=2) + "\n")
        print("req-index: %s" % out.relative_to(root))
    if args.kind == "registry":
        width = int(profile.get("id_width", 4) or 4)

        def print_header():
            print("| Number | File | Title | Epic | Status | Layer |")
            print("| :--- | :--- | :--- | :--- | :--- | :--- |")

        def print_spec(spec):
            layers = ", ".join(str(item) for item in as_list(spec["fm"].get("layer")))
            number = (
                str(spec["id"]).zfill(width) if isinstance(spec["id"], int) else "?"
            )
            print(
                "| %s | %s | %s | %s | %s | %s |"
                % (
                    number,
                    spec["rel"],
                    spec["fm"].get("title", ""),
                    spec["fm"].get("epic") or "—",
                    spec["status"],
                    layers,
                )
            )

        if getattr(args, "by_epic", False):
            groups = {}
            for spec in specs:
                groups.setdefault(str(spec["fm"].get("epic") or "—"), []).append(spec)
            for epic in sorted(groups):
                print("## Epic %s" % epic)
                print_header()
                for spec in groups[epic]:
                    print_spec(spec)
                print()
        else:
            print_header()
            for spec in specs:
                print_spec(spec)
    elif args.kind == "traceability":
        print("| Spec | Requirement | Title | Tagged |")
        print("| :--- | :--- | :--- | :--- |")
        for spec in specs:
            for req in spec["reqs"]:
                tagged = req["non_testable"] or (spec["id"], req["id"]) in tags
                print(
                    "| %s | %s | %s | %s |"
                    % (spec["id"], req["id"], req["title"], "yes" if tagged else "no")
                )
    elif args.kind == "release-notes":
        groups = {}
        for spec in specs:
            if spec["status"] != "completed":
                continue
            updated = str(spec["fm"].get("updated") or spec["fm"].get("created") or "unknown")
            groups.setdefault(updated[:7], []).append(spec)
        for month in sorted(groups, reverse=True):
            print("## %s" % month)
            for spec in sorted(groups[month], key=lambda item: item["id"]):
                print("- %s: %s" % (spec["id"], spec["fm"].get("title", "")))
            print()
    return 0


def cmd_metrics(args):
    root = Path(args.root)
    profile = load_project(root)
    project_root = resolve_project_root(
        root, profile, getattr(args, "project_root", None)
    )
    specs = load_specs(root)
    tags = scan_tags(root, profile, project_root)
    decisions, _ = load_ledger(root, "DECISIONS.md")
    issues, _ = load_ledger(root, "KNOWN_ISSUES.md")
    risks, _ = load_ledger(root, "RISKS.md")
    reqs = [req for spec in specs for req in spec["reqs"]]
    tagged = [
        req
        for spec in specs
        for req in spec["reqs"]
        if req["non_testable"] or (spec["id"], req["id"]) in tags
    ]
    completed = [spec for spec in specs if spec["status"] == "completed"]
    lead_times = []
    for spec in completed:
        try:
            created = date.fromisoformat(str(spec["fm"].get("created")))
            updated = date.fromisoformat(str(spec["fm"].get("updated")))
            lead_times.append((updated - created).days)
        except (ValueError, TypeError):
            pass
    metrics = {
        "generated": today(),
        "specs": len(specs),
        "completed": len(completed),
        "requirements": len(reqs),
        "traceability": round(100.0 * len(tagged) / len(reqs), 1) if reqs else 100.0,
        "decisions": len(decisions),
        "known_issues_open": len(
            [row for row in issues if row.get("status") in ("open", "scheduled", "in_progress")]
        ),
        "risks_open": len(
            [row for row in risks if row.get("status") in ("open", "accepted")]
        ),
        "lead_time_days_avg": round(sum(lead_times) / len(lead_times), 1)
        if lead_times
        else 0.0,
    }
    if getattr(args, "out", None):
        target = (project_root / str(args.out)).resolve()
        root_resolved = project_root.resolve()
        if not (target == root_resolved or root_resolved in target.parents):
            print("metrics: --out must stay inside the project root")
            return 1
        write_text(target, json.dumps(metrics, indent=2) + "\n")
        print("metrics: %s" % target.relative_to(root_resolved))
    if getattr(args, "json", False):
        print(json.dumps(metrics, indent=2))
    else:
        for key, value in metrics.items():
            if key == "traceability":
                print("traceability: %.1f%%" % value)
            elif key == "lead_time_days_avg":
                print("lead_time_days_avg: %.1f" % value)
            else:
                print("%s: %s" % (key, value))
    return 0


def cmd_context(args):
    root = Path(args.root)
    specs = load_specs(root)
    match = TASK_ID.match(args.task)
    if not match:
        print("context: task id must look like T-001-01")
        return 1
    spec_id = int(match.group(1))
    spec = find_spec(specs, spec_id)
    if not spec:
        print("context: spec %s not found" % spec_id)
        return 1
    task = next((item for item in spec["tasks"] if item.get("id") == args.task), None)
    if not task:
        print("context: task %s not found" % args.task)
        return 1
    req_id = task.get("req", "")
    req = next((item for item in spec["reqs"] if item["id"] == req_id), None)
    profile = load_project(root)
    bundle = {
        "spec": spec_id,
        "status": spec["status"],
        "task": {
            "id": task.get("id"),
            "title": task.get("task", ""),
            "depends_on": split_deps(task.get("depends_on")),
            "status": task.get("status", ""),
        },
        "requirements": (
            [{"id": req["id"], "title": req["title"], "ref": "%s#%s" % (spec["rel"], req["id"].lower())}]
            if req
            else []
        ),
        "decisions": as_list(spec["fm"].get("decision_refs")),
        "issues": as_list(spec["fm"].get("issue_refs")),
        "files": [part.strip() for part in str(task.get("files", "")).split(",") if part.strip()],
    }
    budget = args.max_tokens or int(profile.get("bundle_tokens", 8000))
    bundle = truncate_bundle(bundle, budget)
    if args.json:
        print(json.dumps(bundle, indent=2))
    else:
        print("Spec %s (%s)" % (spec_id, spec["status"]))
        print("Task %s: %s" % (bundle["task"]["id"], bundle["task"]["title"]))
        for item in bundle["requirements"]:
            print("Requirement %s: %s" % (item["id"], item.get("title", "")))
        if bundle["files"]:
            print("Files: %s" % ", ".join(bundle["files"]))
        if bundle.get("truncated"):
            print("truncated to %s tokens: %s" % (budget, ", ".join(bundle.get("dropped", []))))
    return 0


def cmd_show(args):
    root = Path(args.root)
    specs = load_specs(root)
    spec = find_spec(specs, int(args.spec))
    if not spec:
        print("show: spec not found")
        return 1
    if not args.req:
        print(spec["path"].read_text(encoding="utf-8"))
        return 0
    lines = spec["body"].splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^#{2,4}\s+`?%s`?" % re.escape(args.req), line.strip()):
            start = index
            break
    if start is None:
        print("show: requirement not found")
        return 1
    for line in lines[start:]:
        if line.startswith("### ") and not line.strip().startswith("### `%s`" % args.req):
            break
        print(line)
    return 0


def cmd_find(args):
    root = Path(args.root)
    specs = load_specs(root)
    for spec in specs:
        if spec_touches(spec, args.file):
            print("%s\t%s\t%s" % (spec["id"], spec["status"], spec["rel"]))
    return 0


def cmd_impact(args):
    root = Path(args.root)
    profile = load_project(root)
    project_root = resolve_project_root(
        root, profile, getattr(args, "project_root", None)
    )
    changed = []
    if args.changed:
        files = changed_files(project_root)
        if files is None:
            print("impact: not a git repository or no HEAD")
            return 1
        changed = files
    else:
        changed = [item.strip() for item in args.files.split(",") if item.strip()]
    specs = load_specs(root)
    for spec in specs:
        for path in changed:
            if spec_touches(spec, path):
                print("%s\t%s\t%s" % (spec["id"], path, spec["rel"]))
                break
    return 0


def cmd_deps(args):
    root = Path(args.root)
    specs = load_specs(root)
    by_id = {spec["id"]: spec for spec in specs if isinstance(spec["id"], int)}
    seen = set()
    queue = [(int(args.spec), 0)]
    while queue:
        spec_id, depth = queue.pop(0)
        if spec_id in seen or depth > args.depth:
            continue
        seen.add(spec_id)
        print(spec_id)
        spec = by_id.get(spec_id)
        if not spec:
            continue
        for dep in as_list(spec["fm"].get("depends_on")):
            try:
                queue.append((int(dep), depth + 1))
            except (TypeError, ValueError):
                pass
    return 0


def cmd_search(args):
    root = Path(args.root)
    specs = load_specs(root)
    needle = args.query.lower()
    for spec in specs:
        title = str(spec["fm"].get("title", ""))
        if needle in title.lower():
            print("%s\t%s\t%s" % (spec["id"], title, spec["rel"]))
        for req in spec["reqs"]:
            if needle in req["title"].lower():
                print("%s\t%s\t%s\t%s" % (spec["id"], req["id"], req["title"], spec["rel"]))
    return 0


def cmd_plan(args):
    root = Path(args.root)
    specs = load_specs(root)
    spec = find_spec(specs, int(args.spec))
    if not spec:
        print("plan: spec not found")
        return 1
    errors = []
    waves, by_id = task_waves(spec["tasks"], errors, spec["rel"])
    for error in errors:
        print("error: %s" % error)
    for index, wave in enumerate(waves, 1):
        print("wave %d: %s" % (index, ", ".join(wave)))
    return 1 if errors else 0


def cmd_next(args):
    root = Path(args.root)
    specs = load_specs(root)
    spec = find_spec(specs, int(args.spec))
    if not spec:
        print("next: spec not found")
        return 1
    done = {
        task.get("id")
        for task in spec["tasks"]
        if str(task.get("status", "")).lower() == "done"
    }
    for task in spec["tasks"]:
        if str(task.get("status", "")).lower() != "todo":
            continue
        if all(dep in done for dep in split_deps(task.get("depends_on"))):
            print("%s\t%s" % (task.get("id"), task.get("task", "")))
            return 0
    print("next: no runnable task")
    return 0


def cmd_resume(args):
    root = Path(args.root)
    specs = load_specs(root)
    spec = find_spec(specs, int(args.spec))
    if not spec:
        print("resume: spec not found")
        return 1
    print("spec: %s (%s)" % (spec["id"], spec["status"]))
    for status in ("doing", "todo", "blocked", "done"):
        tasks = [task for task in spec["tasks"] if str(task.get("status", "")).lower() == status]
        if tasks:
            print("%s: %s" % (status, ", ".join(str(task.get("id")) for task in tasks)))
    decisions, _ = load_ledger(root, "DECISIONS.md")
    issues, _ = load_ledger(root, "KNOWN_ISSUES.md")
    spec_id = str(spec["id"])
    for row in decisions:
        if str(row.get("owning_spec", "")).strip() == spec_id:
            print("decision: %s (%s)" % (row.get("id"), row.get("status")))
    for row in issues:
        if str(row.get("owning_spec", "")).strip() == spec_id:
            print("issue: %s (%s)" % (row.get("id"), row.get("status")))
    return 0


def cmd_converge(args):
    root = Path(args.root)
    profile = load_project(root)
    project_root = resolve_project_root(
        root, profile, getattr(args, "project_root", None)
    )
    errors, warnings, specs, _tags, _profile = run_check(
        root, project_root=project_root, budget=True
    )
    for warning in warnings:
        print("warning: %s" % warning)
    for error in errors:
        print("error: %s" % error)
    spec = find_spec(specs, int(args.spec))
    if spec:
        if spec["status"] != "completed":
            print("converge: spec %s is %s, not completed" % (spec["id"], spec["status"]))
            errors.append("not completed")
        open_tasks = [
            task for task in spec["tasks"] if str(task.get("status", "")).lower() != "done"
        ]
        if open_tasks:
            print("converge: %d tasks are not done" % len(open_tasks))
            errors.append("open tasks")
    if errors:
        print("converge: not converged")
        return 1
    print("converge: ok")
    return 0


def copy_tree(source, target, ignore_names=()):
    source = Path(source)
    target = Path(target)
    for path in source.rglob("*"):
        if any(part in ignore_names or part == "__pycache__" for part in path.parts):
            continue
        if path.is_dir():
            continue
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def cmd_idea(args):
    root = Path(args.root)
    profile = load_project(root)
    specs = load_specs(root)
    highest = max([spec["id"] for spec in specs if isinstance(spec["id"], int)] or [0])
    next_id = highest + 1
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")[:60] or "idea"
    width = int(profile.get("id_width", 4) or 4)
    filename = "%0*d-%s.md" % (width, next_id, slug)
    path = root / str(profile["spec_dir"]) / filename
    if path.exists():
        print("idea: %s already exists" % path)
        return 1
    core_dir = root / str(profile.get("core_dir", "governance"))
    template = read_text(core_dir / "templates" / "idea.md")
    layers = as_list(profile.get("layers")) or ["backend"]
    template = (
        template.replace("{{ID}}", str(next_id))
        .replace("{{ID_PADDED}}", str(next_id).zfill(width))
        .replace("{{TITLE}}", args.title)
        .replace("{{LAYER}}", str(layers[0]))
        .replace("{{DATE}}", today())
    )
    write_text(path, template)
    print(path.relative_to(root))
    return 0


def cmd_init(args):
    project_root = Path(args.root).resolve()
    source = (
        Path(args.source).resolve()
        if args.source
        else Path(__file__).resolve().parents[2]
    )
    if not (source / "governance" / "scripts" / "govern.py").exists():
        print("init: source does not look like sdd-gov")
        return 1
    layout = str(args.layout or "isolated").lower()
    if layout not in ("isolated", "root"):
        print("init: --layout must be isolated or root")
        return 1
    install_root = (
        project_root / (args.dir or "sdd-gov") if layout == "isolated" else project_root
    )
    if install_root.exists() and any(install_root.iterdir()) and not args.force:
        print("init: %s is not empty; use --force" % install_root)
        return 1
    pointer = project_root / "AGENTS.md"
    if (
        layout == "isolated"
        and pointer.exists()
        and not (args.merge_agents or args.force)
        and POINTER_START not in read_text(pointer)
    ):
        print("init: root AGENTS.md exists; use --merge-agents or --force")
        return 1

    project_root.mkdir(parents=True, exist_ok=True)
    install_root.mkdir(parents=True, exist_ok=True)
    copy_tree(
        source / "governance",
        install_root / "governance",
        ignore_names={"baseline.json", "reservations.json"},
    )
    for name in (
        "AGENTS.md",
        "PROJECT.md",
        "MEMORY.md",
        "DECISIONS.md",
        "KNOWN_ISSUES.md",
        "RISKS.md",
        "WORK.md",
        "README.md",
        ".gitignore",
        "g",
        "g.cmd",
    ):
        source_file = source / "template" / name
        if not source_file.exists():
            continue
        destination = install_root / name
        if destination.exists() and not args.force:
            print("init: skipping existing %s" % name)
            continue
        shutil.copy2(source_file, destination)
    g_wrapper = install_root / "g"
    if g_wrapper.exists():
        g_wrapper.chmod(0o755)
    ensure_gitignore(
        project_root,
        [".local/"]
        if layout == "isolated"
        else [".local/", "specs/index.json", "specs/req_index.json"],
    )

    spec_dir = install_root / "specs"
    spec_dir.mkdir(exist_ok=True)
    project_name = args.project_name or project_root.name or "Example Project"
    project_path = install_root / "PROJECT.md"
    if project_path.exists():
        data, body, _errors = frontmatter.read(project_path)
        data["name"] = project_name
        data["install_layout"] = layout
        data["project_root"] = ".." if layout == "isolated" else "."
        write_text(project_path, frontmatter.dump(data, body))

    seed = spec_dir / "0001-example-feature.md"
    if not seed.exists() or args.force:
        template = read_text(source / "governance" / "templates" / "spec.md")
        template = (
            template.replace("{{ID}}", "1")
            .replace("{{ID_PADDED}}", "0001")
            .replace("{{TITLE}}", "Example feature")
            .replace("{{EPIC}}", "1")
            .replace("{{OWNER}}", "author")
            .replace("{{LAYER}}", "backend")
            .replace("{{STATUS}}", "draft")
            .replace("{{DATE}}", today())
        )
        write_text(seed, template)

    if layout == "isolated":
        if not install_pointer(
            project_root, merge=args.merge_agents, force=args.force
        ):
            print("init: root AGENTS.md exists; add the sdd-gov block or pass --merge-agents")
            return 1

    print("init: created %s" % install_root)
    if layout == "isolated":
        print("next: read sdd-gov/README.md and sdd-gov/AGENTS.md")
        print("next: run the kickoff interview in sdd-gov/governance/KICKOFF.md")
        print("next: sdd-gov/g check --budget")
    else:
        print("next: run the kickoff interview in governance/KICKOFF.md")
        print("next: python3 governance/scripts/govern.py check")
    return 0


def cmd_upgrade(args):
    target = Path(args.root).resolve()
    source = Path(args.source).resolve()
    if not (source / "governance" / "scripts" / "govern.py").exists():
        print("upgrade: source does not look like sdd-gov")
        return 1
    if not (target / "governance").exists():
        print("upgrade: target has no governance directory; run init first")
        return 1
    copy_tree(
        source / "governance",
        target / "governance",
        ignore_names={"baseline.json", "reservations.json"},
    )
    print("upgrade: governance updated from %s" % source)
    return 0


def cmd_manifest(args):
    root = Path(args.root).resolve()
    entries = []
    for base in ("governance", "template"):
        base_path = root / base
        if not base_path.exists():
            continue
        for path in sorted(base_path.rglob("*")):
            if not path.is_file():
                continue
            if any(part == "__pycache__" or part.endswith(".pyc") for part in path.parts):
                continue
            if path.name in ("baseline.json", "reservations.json"):
                continue
            relative = str(path.relative_to(root))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append({"path": relative, "sha256": digest})
    for name in ("ADOPT.md", "AGENTS.md", "README.md", "LICENSE", "VERSION", "CHANGELOG.md"):
        path = root / name
        if path.exists():
            entries.append(
                {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            )
    version = read_text(root / "VERSION").strip() or "0.1.0"
    manifest = {
        "name": "sdd-gov",
        "version": version,
        "ref": "v%s" % version,
        "python": ">=3.9",
        "install": {
            "core": "governance/",
            "template": "template/",
            "entry": "governance/scripts/govern.py",
        },
        "files": entries,
    }
    write_text(root / "sdd-gov.json", json.dumps(manifest, indent=2) + "\n")
    print("manifest: %d files at version %s" % (len(entries), version))
    return 0


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def copy_fixture(source, target):
    copy_tree(source, target, ignore_names=set())
    project = Path(target) / "PROJECT.md"
    if project.exists():
        core = (Path(source).parent.parent / "governance").resolve()
        text = read_text(project).replace(
            "core_dir: ../../governance", "core_dir: %s" % core
        )
        write_text(project, text)


def cmd_selftest(args):
    source = Path(__file__).resolve().parents[2]
    passed = 0
    failed = 0

    def run(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print("ok   %s" % name)
            passed += 1
        except AssertionError as error:
            print("fail %s: %s" % (name, error))
            failed += 1

    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        greenfield = temp / "greenfield"
        copy_fixture(source / "examples" / "greenfield", greenfield)

        def fresh_check():
            errors, _warnings, _specs, _tags, _profile = run_check(greenfield)
            assert not errors, "; ".join(errors[:5])

        run("greenfield passes", fresh_check)

        def broken_tag():
            work = temp / "broken-tag"
            copy_fixture(greenfield, work)
            test = work / "tests" / "test_greet.py"
            write_text(
                test,
                read_text(test)
                .replace("@spec:0001-REQ-01", "")
                .replace("@spec:0001-REQ-02", ""),
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert errors, "missing tags were not detected"

        run("missing tags fail", broken_tag)

        def duplicate_key():
            work = temp / "duplicate-key"
            copy_fixture(greenfield, work)
            spec = work / "specs" / "0001-example-feature.md"
            text = read_text(spec)
            text = text.replace("status: completed", "status: completed\nstatus: completed", 1)
            write_text(spec, text)
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("duplicate key" in error for error in errors), "duplicate key was not detected"

        run("duplicate frontmatter key fails", duplicate_key)

        def cycle():
            work = temp / "cycle"
            copy_fixture(greenfield, work)
            spec = work / "specs" / "0001-example-feature.md"
            text = read_text(spec).replace(
                "| T-0001-02 | Add the greeting test | REQ-0001-02 | T-0001-01 | tests/test_greet.py | done |",
                "| T-0001-02 | Add the greeting test | REQ-0001-02 | T-0001-02 | tests/test_greet.py | done |",
            )
            write_text(spec, text)
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("cycle" in error for error in errors), "cycle was not detected"

        run("task cycle fails", cycle)

        def overlap():
            work = temp / "overlap"
            copy_fixture(greenfield, work)
            spec = work / "specs" / "0001-example-feature.md"
            text = read_text(spec)
            text = text.replace(
                "| T-0001-02 | Add the greeting test | REQ-0001-02 | T-0001-01 | tests/test_greet.py | done |",
                "| T-0001-02 | Add the greeting test | REQ-0001-02 | — | src/greet.py | todo |\n| T-0001-04 | Add another test | REQ-0001-02 | — | src/greet.py | todo |",
            )
            write_text(spec, text)
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("scope conflict" in error for error in errors), "scope conflict was not detected"

        run("task scope conflict fails", overlap)

        def init_flow():
            target = temp / "adopted"
            code = cmd_init(
                argparse.Namespace(
                    root=str(target),
                    source=str(source),
                    project_name="Adopted",
                    force=False,
                    layout="root",
                    dir="sdd-gov",
                    merge_agents=False,
                )
            )
            assert code == 0, "init returned %s" % code
            assert (target / "AGENTS.md").exists(), "AGENTS.md missing"
            assert (target / "PROJECT.md").exists(), "PROJECT.md missing"
            assert (target / "governance" / "scripts" / "govern.py").exists(), "govern.py missing"
            errors, _warnings, _specs, _tags, _profile = run_check(target)
            assert not errors, "; ".join(errors[:5])

        run("init into a fresh target", init_flow)

        def isolated_init():
            target = temp / "isolated"
            code = cmd_init(
                argparse.Namespace(
                    root=str(target),
                    source=str(source),
                    project_name="Isolated",
                    force=False,
                    layout="isolated",
                    dir="sdd-gov",
                    merge_agents=False,
                )
            )
            assert code == 0, "init returned %s" % code
            assert (target / "AGENTS.md").exists(), "root pointer missing"
            assert (target / "sdd-gov" / "AGENTS.md").exists(), "law missing"
            assert (target / "sdd-gov" / "g").exists(), "wrapper missing"
            assert (target / "sdd-gov" / "README.md").exists(), "README missing"
            errors, _warnings, _specs, _tags, _profile = run_check(target / "sdd-gov")
            assert not errors, "; ".join(errors[:5])
            result = subprocess.run(
                ["sh", str(target / "sdd-gov" / "g"), "check", "--budget"],
                cwd=str(target),
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, result.stdout + result.stderr

        run("isolated init and wrapper", isolated_init)

        def merge_agents():
            target = temp / "merge"
            target.mkdir()
            write_text(target / "AGENTS.md", "# Existing\n")
            code = cmd_init(
                argparse.Namespace(
                    root=str(target),
                    source=str(source),
                    project_name="Merged",
                    force=False,
                    layout="isolated",
                    dir="sdd-gov",
                    merge_agents=True,
                )
            )
            assert code == 0, "init returned %s" % code
            text = read_text(target / "AGENTS.md")
            assert POINTER_START in text and "# Existing" in text

        run("root AGENTS.md merge", merge_agents)

        def idea_gate():
            work = temp / "idea"
            copy_fixture(greenfield, work)
            code = cmd_idea(argparse.Namespace(title="Offline sync", root=str(work)))
            assert code == 0, "idea returned %s" % code
            spec = work / "specs" / "0002-offline-sync.md"
            assert spec.exists(), "idea spec missing"
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            write_text(spec, read_text(spec).replace("status: draft", "status: specified"))
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("needs at least one requirement" in error for error in errors)

        run("idea draft gate", idea_gate)

        def domain_fail():
            work = temp / "domain-fail"
            copy_fixture(greenfield, work)
            (work / "contracts" / "domain" / "entities.json").unlink()
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("domain registry not found" in error for error in errors)

        run("domain module fails", domain_fail)

        def ste_check():
            work = temp / "ste"
            copy_fixture(greenfield, work)
            project = work / "PROJECT.md"
            text = read_text(project).replace("modules: [domain]", "modules: [domain, ste]")
            text = text.replace(
                "domain_registry: contracts/domain/entities.json",
                "domain_registry: contracts/domain/entities.json\nste_mode: enforce",
            )
            write_text(project, text)
            spec = work / "specs" / "0001-example-feature.md"
            write_text(spec, read_text(spec) + "\n- We don't support this.\n")
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("contraction" in error for error in errors)

        run("ste module fails", ste_check)

        def changed_scope():
            work = temp / "changed"
            copy_fixture(greenfield, work)
            test = work / "tests" / "test_greet.py"
            write_text(
                test,
                read_text(test)
                .replace("@spec:0001-REQ-01", "")
                .replace("@spec:0001-REQ-02", ""),
            )
            errors, _warnings, _specs, _tags, _profile = run_check(
                work, changed=True, changed_files_list=["docs/readme.md"]
            )
            assert not errors, "; ".join(errors[:5])
            errors, _warnings, _specs, _tags, _profile = run_check(
                work, changed=True, changed_files_list=["src/greet.py"]
            )
            assert errors, "the affected spec was not checked"

        run("changed scoping", changed_scope)

        def context_budget():
            bundle = {
                "spec": 1,
                "status": "completed",
                "task": {"id": "T-1-01", "title": "x", "depends_on": [], "status": "todo"},
                "requirements": [
                    {"id": "REQ-1-01", "title": "word " * 80, "ref": "x"}
                ],
                "decisions": ["DEC-0001-01"],
                "issues": ["KI-0001-01"],
                "files": ["a", "b"],
            }
            out = truncate_bundle(bundle, 10)
            assert out["truncated"] is True
            assert out["requirements"][0]["id"] == "REQ-1-01"

        run("context budget truncates", context_budget)

        def memory_lint():
            work = temp / "memory"
            copy_fixture(greenfield, work)
            write_text(work / "MEMORY.md", read_text(work / "MEMORY.md") + "- bad line\n")
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("Source" in error for error in errors)

        run("memory source lint", memory_lint)

        def index_emit():
            work = temp / "index"
            copy_fixture(greenfield, work)
            code = cmd_emit(
                argparse.Namespace(kind="all", root=str(work), project_root=None)
            )
            assert code == 0, "emit returned %s" % code
            index = json.loads(read_text(work / "specs" / "index.json"))
            req_index = json.loads(read_text(work / "specs" / "req_index.json"))
            assert index and req_index

        run("index emit", index_emit)

        def path_check():
            work = temp / "paths"
            copy_fixture(greenfield, work)
            spec = work / "specs" / "0001-example-feature.md"
            write_text(spec, read_text(spec) + "\nSee /tmp/secret.\n")
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("absolute path" in error for error in errors)

        run("path containment fails", path_check)

        def spec_cycle():
            work = temp / "spec-cycle"
            copy_fixture(greenfield, work)
            spec1 = work / "specs" / "0001-example-feature.md"
            write_text(
                spec1,
                read_text(spec1).replace("depends_on: []", "depends_on: [2]", 1),
            )
            spec2 = work / "specs" / "0002-second.md"
            write_text(
                spec2,
                "---\n"
                "id: 2\n"
                "title: Second\n"
                "status: draft\n"
                "layer: [backend]\n"
                "owner: author\n"
                "created: 2026-01-01\n"
                "updated: 2026-01-01\n"
                "depends_on: [1]\n"
                "---\n\n# Second\n",
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("dependency cycle" in error for error in errors)

        run("spec dependency cycle fails", spec_cycle)

        def id_width():
            work = temp / "id-width"
            copy_fixture(greenfield, work)
            project = work / "PROJECT.md"
            write_text(project, read_text(project).replace("id_width: 4", "id_width: 3"))
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("filename id must use 3 digits" in error for error in errors)

        run("id width fails", id_width)

        def enable_module(work, name, mode="enforce", config=None):
            project = work / "PROJECT.md"
            text = read_text(project)
            if "modules: [domain]" in text:
                text = text.replace("modules: [domain]", "modules: [domain, %s]" % name, 1)
            elif "modules: []" in text:
                text = text.replace("modules: []", "modules: [%s]" % name, 1)
            else:
                text = text.replace("modules: [", "modules: [%s, " % name, 1)
            lines = ["%s_mode: %s" % (name, mode)]
            if mode == "report":
                lines.append("%s_expires: 2099-12-31" % name)
            for key, value in (config or {}).items():
                lines.append("%s: %s" % (key, value))
            anchor = "domain_registry: contracts/domain/entities.json"
            if anchor in text:
                text = text.replace(anchor, anchor + "\n" + "\n".join(lines), 1)
            else:
                text = text.replace(
                    "budget_overrides: []", "\n".join(lines) + "\nbudget_overrides: []", 1
                )
            write_text(project, text)

        def legacy_dec():
            work = temp / "legacy-dec"
            copy_fixture(greenfield, work)
            path = work / "DECISIONS.md"
            write_text(path, read_text(path).replace("DEC-0001-01", "DEC-001-01"))
            spec = work / "specs" / "0001-example-feature.md"
            write_text(spec, read_text(spec).replace("DEC-0001-01", "DEC-001-01"))
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("spec part must use 4 digits" in error for error in errors)

        run("legacy DEC width fails", legacy_dec)

        def legacy_global():
            work = temp / "legacy-global"
            copy_fixture(greenfield, work)
            risks = work / "RISKS.md"
            write_text(risks, read_text(risks).replace("RISK-0001", "RISK-01"))
            work_file = work / "WORK.md"
            write_text(work_file, read_text(work_file).replace("W-0001", "W-01"))
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("invalid id" in error for error in errors)

        run("legacy global width fails", legacy_global)

        def qa_check():
            work = temp / "qa"
            copy_fixture(greenfield, work)
            write_text(
                work / "DEFECTS.md",
                "| ID | Title | Status | Spec | Test |\n"
                "| :--- | :--- | :--- | :--- | :--- |\n"
                "| DEF-0001 | Broken greeting | fixed | 1 | @spec:0001-REQ-01 |\n",
            )
            enable_module(
                work, "qa", "enforce", {"qa_defects": "DEFECTS.md"}
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            write_text(
                work / "DEFECTS.md",
                "| ID | Title | Status | Spec | Test |\n"
                "| :--- | :--- | :--- | :--- | :--- |\n"
                "| DEF-0001 | Broken greeting | fixed | 1 | — |\n",
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("resolving test" in error for error in errors)

        run("qa module", qa_check)

        def provenance_check():
            work = temp / "provenance"
            copy_fixture(greenfield, work)
            write_text(
                work / "THIRD_PARTY.md",
                "| ID | Name | Kind | Source | Version | Commit | License | Scope |\n"
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
                "| TP-0001 | example-skill | skill | https://example.com/skill | 1.0.0 | abc123 | MIT | vendored |\n",
            )
            enable_module(
                work,
                "provenance",
                "enforce",
                {"provenance_ledger": "THIRD_PARTY.md"},
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            write_text(
                work / "THIRD_PARTY.md",
                read_text(work / "THIRD_PARTY.md").replace("| MIT |", "|  |"),
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("missing license" in error for error in errors)

        run("provenance module", provenance_check)

        def database_check():
            fail = temp / "database-fail"
            copy_fixture(greenfield, fail)
            enable_module(fail, "database", "enforce")
            errors, _warnings, _specs, _tags, _profile = run_check(fail)
            assert any("db_migration_check is required" in error for error in errors)

            work = temp / "database"
            copy_fixture(greenfield, work)
            enable_module(
                work,
                "database",
                "enforce",
                {
                    "db_migration_check": '"alembic check"',
                    "checks": '["alembic check"]',
                },
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])

        run("database module", database_check)

        def isolation_check():
            work = temp / "isolation"
            copy_fixture(greenfield, work)
            (work / "isolation").mkdir()
            write_text(
                work / "isolation" / "scopes.json",
                '{"tables":[{"table":"users","scope":"global"}]}\n',
            )
            enable_module(
                work,
                "isolation",
                "enforce",
                {"isolation_registry": "isolation/scopes.json"},
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            write_text(
                work / "isolation" / "scopes.json",
                '{"tables":[{"table":"users","scope":"tenant"}]}\n',
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("invalid scope" in error for error in errors)

        run("isolation module", isolation_check)

        def api_check():
            try:
                import yaml  # noqa: F401
                has_yaml = True
            except ImportError:
                has_yaml = False
            work = temp / "api"
            copy_fixture(greenfield, work)
            enable_module(
                work, "api", "enforce", {"api_contract_dir": "contracts/api"}
            )
            if not has_yaml:
                errors, _warnings, _specs, _tags, _profile = run_check(work)
                assert any("PyYAML is required" in error for error in errors)
                return
            (work / "contracts" / "api").mkdir(parents=True)
            contract = work / "contracts" / "api" / "core.yaml"
            write_text(
                contract,
                "openapi: 3.0.0\n"
                "info: {title: Example, version: '1'}\n"
                "paths:\n"
                "  /greet:\n"
                "    get:\n"
                "      operationId: greet\n"
                "      x-spec: REQ-0001-01\n"
                "      responses:\n"
                "        '200': {description: ok}\n",
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            write_text(contract, read_text(contract).replace("      x-spec: REQ-0001-01\n", ""))
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("has no x-spec" in error for error in errors)

        run("api module", api_check)

        def security_check():
            work = temp / "security"
            copy_fixture(greenfield, work)
            spec = work / "specs" / "0001-example-feature.md"
            write_text(spec, read_text(spec).replace("trust_boundary: false", "trust_boundary: true"))
            enable_module(work, "security", "enforce")
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("Threat Model" in error for error in errors)
            write_text(
                spec,
                read_text(spec)
                + "\n## Threat Model\n\n- None.\n\n## Security Impact\n\n- None.\n",
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])

        run("security module", security_check)

        def report_mode():
            work = temp / "report"
            copy_fixture(greenfield, work)
            spec = work / "specs" / "0001-example-feature.md"
            write_text(spec, read_text(spec).replace("trust_boundary: false", "trust_boundary: true"))
            enable_module(work, "security", "report")
            errors, warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            assert any("Threat Model" in warning for warning in warnings)

        run("report mode warns", report_mode)

        def fatal_in_report():
            work = temp / "fatal-report"
            copy_fixture(greenfield, work)
            enable_module(work, "qa", "report")
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("defect ledger not found" in error for error in errors)

        run("fatal stays an error in report", fatal_in_report)

        def bands_check():
            work = temp / "bands"
            copy_fixture(greenfield, work)
            (work / "governance").mkdir(exist_ok=True)
            write_text(
                work / "governance" / "reservations.json",
                json.dumps(
                    {
                        "reserved": [],
                        "bands": [{"start": 10, "end": 19, "owner": "team"}],
                    }
                ),
            )
            enable_module(work, "bands", "enforce")
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            write_text(
                work / "governance" / "reservations.json",
                json.dumps(
                    {
                        "reserved": [],
                        "bands": [
                            {"start": 10, "end": 19, "owner": "team"},
                            {"start": 15, "end": 24, "owner": "other"},
                        ],
                    }
                ),
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("overlaps" in error for error in errors)

        run("bands module", bands_check)

        def epic_check():
            work = temp / "epic"
            copy_fixture(greenfield, work)
            spec = work / "specs" / "0001-example-feature.md"
            write_text(spec, read_text(spec).replace("epic: 1", "epic:"))
            enable_module(work, "epic", "enforce")
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("missing epic" in error for error in errors)
            write_text(spec, read_text(spec).replace("epic:", "epic: 1", 1))
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])

        run("epic module", epic_check)

        def metrics_export_check():
            work = temp / "metrics-export"
            copy_fixture(greenfield, work)
            enable_module(
                work,
                "metrics-export",
                "enforce",
                {"metrics_out": ".local/tmp/metrics.json"},
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("metrics export not found" in error for error in errors)
            code = cmd_metrics(
                argparse.Namespace(
                    root=str(work),
                    project_root=None,
                    json=False,
                    out=".local/tmp/metrics.json",
                )
            )
            assert code == 0, "metrics returned %s" % code
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            metrics_path = work / ".local" / "tmp" / "metrics.json"
            old = metrics_path.stat().st_mtime - 3600
            os.utime(metrics_path, (old, old))
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("stale" in error for error in errors)

        run("metrics-export module", metrics_export_check)

        def matrix_check():
            work = temp / "matrix"
            copy_fixture(greenfield, work)
            write_text(
                work / "matrix_registry.tsv",
                "id\taxis\tvalues\tbaseline\nM-0001\tprovider\taws,github\taws\n",
            )
            enable_module(
                work, "matrix", "enforce", {"matrix_registry": "matrix_registry.tsv"}
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert not errors, "; ".join(errors[:5])
            write_text(
                work / "matrix_registry.tsv",
                "id\taxis\tvalues\tbaseline\nM-0001\tprovider\taws,github\tazure\n",
            )
            errors, _warnings, _specs, _tags, _profile = run_check(work)
            assert any("baseline" in error for error in errors)

        run("matrix module", matrix_check)

        def reserve_check():
            work = temp / "reserve"
            copy_fixture(greenfield, work)
            code = cmd_reserve(
                argparse.Namespace(root=str(work), size=10, owner="team")
            )
            assert code == 0, "reserve returned %s" % code
            data = json.loads(read_text(work / "governance" / "reservations.json"))
            band = data["bands"][0]
            assert band["start"] == 2 and band["end"] == 11 and band["owner"] == "team"

        run("reserve command", reserve_check)

        def emit_epic():
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = cmd_emit(
                    argparse.Namespace(
                        kind="registry",
                        root=str(greenfield),
                        project_root=None,
                        by_epic=True,
                    )
                )
            assert code == 0, "emit returned %s" % code
            assert "## Epic 1" in output.getvalue()

        run("emit by epic", emit_epic)

    print("selftest: %d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


def cmd_hooks(args):
    root = Path(args.root)
    profile = load_project(root)
    project_root = resolve_project_root(
        root, profile, getattr(args, "project_root", None)
    )
    for raw in as_list(profile.get("checks")):
        command = str(raw)
        if not command:
            continue
        print("run: %s" % command)
        result = subprocess.run(command, shell=True, cwd=str(project_root))
        if result.returncode != 0:
            print("hook failed (%d): %s" % (result.returncode, command))
            return result.returncode
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="govern.py", description="sdd-gov governance engine")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check")
    check.add_argument("--root", default=".")
    check.add_argument("--project-root", dest="project_root")
    check.add_argument("--changed", action="store_true")
    check.add_argument("--budget", action="store_true")
    check.add_argument("--hooks", action="store_true")
    check.set_defaults(func=cmd_check)

    fmt = sub.add_parser("fmt")
    fmt.add_argument("--root", default=".")
    fmt.set_defaults(func=cmd_fmt)

    next_id = sub.add_parser("next-id")
    next_id.add_argument("--root", default=".")
    next_id.add_argument("--reserve", action="store_true")
    next_id.set_defaults(func=cmd_next_id)

    reserve = sub.add_parser("reserve")
    reserve.add_argument("--size", type=int, default=10)
    reserve.add_argument("--owner", default="unassigned")
    reserve.add_argument("--root", default=".")
    reserve.set_defaults(func=cmd_reserve)

    baseline = sub.add_parser("baseline")
    baseline.add_argument("--root", default=".")
    baseline.add_argument("--out")
    baseline.set_defaults(func=cmd_baseline)

    supersede = sub.add_parser("supersede")
    supersede.add_argument("old")
    supersede.add_argument("new")
    supersede.add_argument("--root", default=".")
    supersede.set_defaults(func=cmd_supersede)

    doctor = sub.add_parser("doctor")
    doctor.add_argument("--root", default=".")
    doctor.add_argument("--project-root", dest="project_root")
    doctor.add_argument("--upstream")
    doctor.set_defaults(func=cmd_doctor)

    emit = sub.add_parser("emit")
    emit.add_argument(
        "kind",
        choices=["registry", "traceability", "release-notes", "index", "req-index", "all"],
    )
    emit.add_argument("--root", default=".")
    emit.add_argument("--project-root", dest="project_root")
    emit.add_argument("--by-epic", action="store_true")
    emit.set_defaults(func=cmd_emit)

    metrics = sub.add_parser("metrics")
    metrics.add_argument("--root", default=".")
    metrics.add_argument("--project-root", dest="project_root")
    metrics.add_argument("--json", action="store_true")
    metrics.add_argument("--out")
    metrics.set_defaults(func=cmd_metrics)

    context = sub.add_parser("context")
    context.add_argument("--task", required=True)
    context.add_argument("--root", default=".")
    context.add_argument("--project-root", dest="project_root")
    context.add_argument("--max-tokens", type=int)
    context.add_argument("--json", action="store_true")
    context.set_defaults(func=cmd_context)

    show = sub.add_parser("show")
    show.add_argument("spec")
    show.add_argument("--req")
    show.add_argument("--root", default=".")
    show.set_defaults(func=cmd_show)

    find = sub.add_parser("find")
    find.add_argument("--file", required=True)
    find.add_argument("--root", default=".")
    find.set_defaults(func=cmd_find)

    impact = sub.add_parser("impact")
    impact.add_argument("--changed", action="store_true")
    impact.add_argument("--files", default="")
    impact.add_argument("--root", default=".")
    impact.add_argument("--project-root", dest="project_root")
    impact.set_defaults(func=cmd_impact)

    deps = sub.add_parser("deps")
    deps.add_argument("spec")
    deps.add_argument("--depth", type=int, default=2)
    deps.add_argument("--root", default=".")
    deps.set_defaults(func=cmd_deps)

    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--root", default=".")
    search.set_defaults(func=cmd_search)

    plan = sub.add_parser("plan")
    plan.add_argument("--spec", required=True)
    plan.add_argument("--root", default=".")
    plan.set_defaults(func=cmd_plan)

    next_task = sub.add_parser("next")
    next_task.add_argument("--spec", required=True)
    next_task.add_argument("--root", default=".")
    next_task.set_defaults(func=cmd_next)

    resume = sub.add_parser("resume")
    resume.add_argument("--spec", required=True)
    resume.add_argument("--root", default=".")
    resume.set_defaults(func=cmd_resume)

    converge = sub.add_parser("converge")
    converge.add_argument("--spec", required=True)
    converge.add_argument("--root", default=".")
    converge.add_argument("--project-root", dest="project_root")
    converge.set_defaults(func=cmd_converge)

    idea = sub.add_parser("idea")
    idea.add_argument("title")
    idea.add_argument("--root", default=".")
    idea.set_defaults(func=cmd_idea)

    init = sub.add_parser("init")
    init.add_argument("--root", default=".")
    init.add_argument("--from", dest="source")
    init.add_argument("--project-name")
    init.add_argument("--layout", choices=["isolated", "root"], default="isolated")
    init.add_argument("--dir", default="sdd-gov")
    init.add_argument("--merge-agents", action="store_true")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    upgrade = sub.add_parser("upgrade")
    upgrade.add_argument("--root", default=".")
    upgrade.add_argument("--from", dest="source", required=True)
    upgrade.set_defaults(func=cmd_upgrade)

    manifest = sub.add_parser("manifest")
    manifest.add_argument("--root", default=".")
    manifest.set_defaults(func=cmd_manifest)

    selftest = sub.add_parser("selftest")
    selftest.add_argument("--root", default=".")
    selftest.set_defaults(func=cmd_selftest)

    hooks = sub.add_parser("hooks")
    hooks.add_argument("--root", default=".")
    hooks.add_argument("--project-root", dest="project_root")
    hooks.set_defaults(func=cmd_hooks)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
