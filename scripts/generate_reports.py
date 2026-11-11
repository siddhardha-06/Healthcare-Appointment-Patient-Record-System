"""Build the Part-3 test reports from pytest's JUnit XML and coverage.py's JSON.

    pytest --cov=app --cov=src --cov-branch --cov-report=json:reports/coverage.json --junitxml=reports/junit.xml
    python scripts/generate_reports.py reports docs/reports

Writes: unit-test-report.md, system-validation-report.md, code-coverage-report.md, branch-coverage-report.md
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path

TEST_CASES = {  # TC ID -> (title, requirements) – from docs/requirements-registry.md
    "TC-AUTH-01": ("Login with valid and invalid credentials", "HAP-F-001"),
    "TC-AUTH-02": ("Patient is blocked from admin endpoints", "HAP-F-002, HAP-SR-004"),
    "TC-NOT-01": ("Booking confirmation and 24-hour reminder are sent", "HAP-F-050"),
    "TC-PAT-01": ("Register patient, generate MRN, edit own profile", "HAP-F-010, HAP-F-011"),
    "TC-DOC-01": ("Availability generates slots; leave blocks them", "HAP-F-021, HAP-F-022"),
    "TC-SEC-01": ("Passwords are bcrypt hashes; lockout after 5 failures", "HAP-SR-001, HAP-SR-005"),
    "TC-SEC-02": ("Expired or forged tokens rejected; no access to other patients' data", "HAP-SR-002, HAP-SR-004"),
    "TC-APT-01": ("Search free slots and book an appointment", "HAP-F-030, HAP-F-031"),
    "TC-APT-02": ("Double booking and patient overlap are prevented", "HAP-F-032"),
    "TC-APT-03": ("Reschedule/cancel window and status transitions", "HAP-F-033, HAP-F-034"),
    "TC-PERF-01": ("Load and response-time test", "HAP-NF-001, HAP-NF-002"),
    "TC-MR-01": ("Consultation saved, appointment completed, edits versioned", "HAP-F-041, HAP-F-044"),
    "TC-MR-02": ("Prescription issued; patient views it read-only and downloads PDF", "HAP-F-042, HAP-F-043"),
    "TC-MR-03": ("Doctor without care relationship is denied and the attempt is logged", "HAP-F-040, HAP-SR-004, HAP-SR-007"),
}
TC_RE = re.compile(r"test_tc_([a-z]+)_(\d{2})")


def load_junit(path: Path):
    cases = []
    for tc in ET.parse(path).getroot().iter("testcase"):
        status = "passed"
        for child in tc:
            if child.tag in ("failure", "error"):
                status = "failed"
            elif child.tag == "skipped":
                status = "skipped"
        cases.append({"file": tc.get("classname", "").replace(".", "/") + ".py", "name": tc.get("name"),
                      "time": float(tc.get("time", 0)), "status": status})
    return cases


def pct(a, b):
    return 100.0 * a / b if b else 100.0


def header(title):
    return (f"# {title}\n\n**Project:** Healthcare Appointment & Patient Record System · **Team:** 13 · "
            f"**Generated:** {datetime.now():%d-%m-%Y %H:%M}\n\n")


def unit_report(cases):
    by_file = defaultdict(list)
    for c in cases:
        by_file[c["file"]].append(c)
    total = len(cases)
    passed = sum(c["status"] == "passed" for c in cases)
    failed = [c for c in cases if c["status"] == "failed"]
    out = header("Unit Test Report")
    out += ("Unit and API-level integration tests run with **pytest** against a fresh in-memory database per test "
            "(see Test Plan §5). Every pull request runs this suite in GitHub Actions.\n\n")
    out += "| Metric | Value |\n|---|---|\n"
    out += f"| Test functions | {total} |\n| Passed | {passed} |\n| Failed | {len(failed)} |\n"
    out += f"| Skipped | {sum(c['status'] == 'skipped' for c in cases)} |\n| Pass rate | {pct(passed, total):.1f}% |\n"
    out += f"| Total run time | {sum(c['time'] for c in cases):.1f} s |\n\n"
    out += "## Results per test file\n\n| Test file | Tests | Passed | Failed | Time (s) |\n|---|---|---|---|---|\n"
    for f, items in sorted(by_file.items()):
        out += (f"| `{f}` | {len(items)} | {sum(i['status'] == 'passed' for i in items)} | "
                f"{sum(i['status'] == 'failed' for i in items)} | {sum(i['time'] for i in items):.2f} |\n")
    out += "\n## Failures\n\n" + ("None.\n" if not failed else "".join(f"- `{c['file']}::{c['name']}`\n" for c in failed))
    out += "\n## All tests\n\n| Test | Result |\n|---|---|\n"
    out += "".join(f"| `{c['file']}::{c['name']}` | {c['status']} |\n" for c in cases)
    return out


def validation_report(cases, perf_note):
    linked = defaultdict(list)
    for c in cases:
        m = TC_RE.search(c["name"])
        if m:
            linked[f"TC-{m.group(1).upper()}-{m.group(2)}"].append(c)
    out = header("System Validation Report")
    out += ("Each test case of the Test Plan is automated as one or more pytest tests named `test_tc_<id>_…`. "
            "They exercise the running FastAPI application end to end through its REST API (system level). "
            "A test case passes only if all of its automated tests pass.\n\n")
    out += "| TC ID | Title | Requirement(s) | Automated tests | Result |\n|---|---|---|---|---|\n"
    passed = 0
    for tc, (title, reqs) in TEST_CASES.items():
        tests = linked.get(tc, [])
        if tc == "TC-PERF-01":
            result, names = perf_note, "`tests/perf/locustfile.py`, `tests/perf/quick_load.py`"
        elif not tests:
            result, names = "Not automated", "–"
        else:
            ok = all(t["status"] == "passed" for t in tests)
            result, names = ("Pass" if ok else "Fail"), "<br>".join(f"`{t['name']}`" for t in tests)
        passed += result.startswith("Pass")
        out += f"| {tc} | {title} | {reqs} | {names} | {result} |\n"
    out += f"\n**{passed} of {len(TEST_CASES)} test cases passed.**\n"
    return out


def coverage_tables(cov, kind):
    rows = []
    for path, data in sorted(cov["files"].items()):
        s = data["summary"]
        if kind == "line":
            rows.append((path, s["num_statements"], s["missing_lines"], pct(s["covered_lines"], s["num_statements"])))
        else:
            rows.append((path, s.get("num_branches", 0), s.get("num_partial_branches", 0),
                         pct(s.get("covered_branches", 0), s.get("num_branches", 0))))
    return rows


def coverage_report(cov, kind):
    t = cov["totals"]
    if kind == "line":
        out = header("Code Coverage Report")
        out += ("Statement (line) coverage of the application code (`app/`, `src/`) measured with coverage.py "
                "while the full pytest suite runs. Target from HAP-NF-005: **≥ 70 %** of the service layer; "
                "the CI job fails below 70 %.\n\n")
        out += (f"| Metric | Value |\n|---|---|\n| Statements | {t['num_statements']} |\n"
                f"| Covered | {t['covered_lines']} |\n| Missed | {t['missing_lines']} |\n"
                f"| **Line coverage** | **{pct(t['covered_lines'], t['num_statements']):.1f}%** |\n"
                f"| Target met (≥ 70 %) | {'Yes' if pct(t['covered_lines'], t['num_statements']) >= 70 else 'No'} |\n\n")
        out += "## Per module\n\n| Module | Statements | Missed | Coverage |\n|---|---|---|---|\n"
    else:
        out = header("Branch Coverage Report")
        out += ("Branch coverage (every `if`/`else`, loop and early-return path taken both ways) measured with "
                "`pytest --cov-branch`. A *partial* branch was taken only one way.\n\n")
        out += (f"| Metric | Value |\n|---|---|\n| Branches | {t.get('num_branches', 0)} |\n"
                f"| Covered | {t.get('covered_branches', 0)} |\n| Partial | {t.get('num_partial_branches', 0)} |\n"
                f"| **Branch coverage** | **{pct(t.get('covered_branches', 0), t.get('num_branches', 0)):.1f}%** |\n\n")
        out += "## Per module\n\n| Module | Branches | Partial | Coverage |\n|---|---|---|---|\n"
    for path, a, b, p in coverage_tables(cov, kind):
        if a:
            out += f"| `{path}` | {a} | {b} | {p:.1f}% |\n"
    return out


def main(src: str, dst: str) -> None:
    src_p, dst_p = Path(src), Path(dst)
    dst_p.mkdir(parents=True, exist_ok=True)
    cases = load_junit(src_p / "junit.xml")
    cov = json.loads((src_p / "coverage.json").read_text())
    perf_file = src_p / "perf-summary.md"
    perf_note = perf_file.read_text().strip().splitlines()[0] if perf_file.exists() else "Run separately (see Test Plan §5)"
    (dst_p / "unit-test-report.md").write_text(unit_report(cases))
    (dst_p / "system-validation-report.md").write_text(validation_report(cases, perf_note))
    (dst_p / "code-coverage-report.md").write_text(coverage_report(cov, "line"))
    (dst_p / "branch-coverage-report.md").write_text(coverage_report(cov, "branch"))
    print("Reports written to", dst_p)


if __name__ == "__main__":
    main(*sys.argv[1:3])
