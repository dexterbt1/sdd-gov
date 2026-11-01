"""QA defect ledger check."""

import re
from pathlib import Path

DEFECT_ID = re.compile(r"^DEF-\d{4}$")
STATUSES = {"open", "fixed", "verified", "closed", "accepted"}
TEST_TAG = re.compile(r"@spec:(\d{3,4})-REQ-(\d{2})")


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_table(path):
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip().startswith("|")]
    header = None
    rows = []
    for line in lines:
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell):
            continue
        if header is None:
            header = [re.sub(r"[^a-z0-9]+", "_", cell.lower()).strip("_") for cell in cells]
            continue
        if len(cells) < len(header):
            cells += [""] * (len(header) - len(cells))
        rows.append(dict(zip(header, cells)))
    return rows


def check(ctx):
    root = Path(ctx["root"])
    profile = ctx["profile"]
    specs = ctx["specs"]
    ledger_value = str(profile.get("qa_defects", "DEFECTS.md"))
    ledger = root / ledger_value
    if not ledger.exists():
        return [("fatal", ledger_value, "defect ledger not found")]

    rows = load_table(ledger)
    spec_ids = {spec["id"] for spec in specs if isinstance(spec["id"], int)}
    req_ids = {req["id"] for spec in specs for req in spec["reqs"]}
    findings = []
    seen = set()
    for row in rows:
        defect = row.get("id", "").strip()
        if not defect:
            continue
        if not DEFECT_ID.match(defect):
            findings.append((ledger_value, "invalid defect id %s" % defect))
        if defect in seen:
            findings.append((ledger_value, "duplicate defect %s" % defect))
        seen.add(defect)
        status = row.get("status", "").strip().lower()
        if status and status not in STATUSES:
            findings.append((ledger_value, "%s has invalid status %s" % (defect, status)))
        owning = row.get("spec", "").strip()
        if owning:
            try:
                if int(owning) not in spec_ids:
                    findings.append((ledger_value, "%s has unknown spec %s" % (defect, owning)))
            except ValueError:
                findings.append((ledger_value, "%s has invalid spec %s" % (defect, owning)))
        test = row.get("test", "").strip()
        if status in ("fixed", "verified"):
            if test in ("", "—", "-", "none"):
                findings.append((ledger_value, "%s has no resolving test" % defect))
            elif test == "(non-testable)":
                pass
            elif test.startswith("@spec:"):
                match = TEST_TAG.search(test)
                if not match:
                    findings.append((ledger_value, "%s has an invalid test tag" % defect))
                else:
                    req_id = "REQ-%s-%s" % (match.group(1), match.group(2))
                    if req_id not in req_ids:
                        findings.append(
                            (ledger_value, "%s test tag %s does not resolve" % (defect, req_id))
                        )
            else:
                findings.append(
                    (ledger_value, "%s test must be a @spec tag or (non-testable)" % defect)
                )

    plan_value = profile.get("qa_test_plan")
    if profile.get("qa_require_test_plan") and plan_value:
        plan = root / str(plan_value)
        if not plan.exists():
            findings.append(("fatal", str(plan_value), "test plan not found"))
        else:
            text = plan.read_text(encoding="utf-8")
            for spec in specs:
                if spec["status"] == "completed" and str(spec["id"]) not in text:
                    findings.append(
                        (str(plan_value), "completed spec %s is missing from the test plan" % spec["id"])
                    )
    return findings
