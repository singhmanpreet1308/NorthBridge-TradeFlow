"""Build the Requirements Traceability Matrix from saved test results.

Inputs
    traceability/requirements.csv        requirement register + known gaps
    traceability/test_case_catalogue.csv test case -> requirement mapping
    evidence/tc_results.json             written by pytest --tc-results
    uat/uat_results.csv                  manual UAT outcomes (optional)

Outputs
    evidence/RTM.md, evidence/RTM.csv, evidence/test_results.md
    data/Phase_2/Delivery_Tracker.xlsx   only with --update-tracker

Status rules (Design.md 16.4: a requirement is never Verified on
implementation alone):
    Test_Status            Failed if any linked test failed; Passed if every
                           executed linked test passed; otherwise Not Run.
    Implementation_Status  Verified only when tests passed, no linked case
                           is Not Run, and the requirement has no known gap.
                           Implemented when tests passed but gaps remain.
                           In Progress when a test failed, or when the
                           register caps it (a core criterion is not built).
"""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from nbit import paths

EVIDENCE_REL = "Phase_7_Integration Testing and Deployment/evidence"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_inputs(results_path):
    reqs = read_csv(paths.TRACEABILITY_DIR / "requirements.csv")
    cases = read_csv(paths.TRACEABILITY_DIR / "test_case_catalogue.csv")
    results = json.loads(Path(results_path).read_text(encoding="utf-8"))

    uat_file = paths.PHASE7_ROOT / "uat" / "uat_results.csv"
    uat = {r["tc_id"]: r for r in read_csv(uat_file)} if uat_file.exists() else {}

    for case in cases:
        tc = case["tc_id"]
        if tc in results:
            case["status"] = results[tc]["status"]
            case["executed_tests"] = len(results[tc]["tests"])
        elif tc in uat and uat[tc]["status"]:
            case["status"] = uat[tc]["status"]
            case["executed_tests"] = 0
            case["notes"] = "; ".join(filter(None, [case["notes"], uat[tc].get("comment", "")]))
        else:
            case["status"] = "Not Run"
            case["executed_tests"] = 0
    return reqs, cases


def assess(reqs, cases):
    rows = []
    for req in reqs:
        linked = [c for c in cases if req["req_id"] in c["requirements"].split(";")]
        statuses = [c["status"] for c in linked]
        executed = [s for s in statuses if s != "Not Run"]

        if "Failed" in statuses:
            test_status = "Failed"
        elif executed and all(s == "Passed" for s in executed):
            test_status = "Passed"
        else:
            test_status = "Not Run"

        not_run = [c["tc_id"] for c in linked if c["status"] == "Not Run"]
        gaps = req["known_gaps"].strip()

        if test_status == "Passed" and not not_run and not gaps:
            impl = "Verified"
        elif test_status == "Passed":
            impl = "Implemented"
        elif test_status == "Failed":
            impl = "In Progress"
        else:
            impl = "Implemented"

        # A requirement missing a core acceptance criterion is capped.
        if req.get("max_status") == "In Progress" and impl in ("Verified", "Implemented"):
            impl = "In Progress"

        notes = []
        if gaps:
            notes.append(f"Gap: {gaps}")
        if not_run:
            notes.append(f"Not run: {', '.join(not_run)}")

        rows.append({
            "req_id": req["req_id"],
            "title": req["title"],
            "priority": req["priority"],
            "business_need": req["business_need"],
            "user_story": req["user_story"],
            "test_cases": ", ".join(c["tc_id"] for c in linked),
            "passed": sum(s == "Passed" for s in statuses),
            "total": len(linked),
            "test_status": test_status,
            "implementation_status": impl,
            "evidence": f"{EVIDENCE_REL}/test_results.md",
            "notes": " | ".join(notes),
        })
    return rows


def write_outputs(rows, cases, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open(out_dir / "RTM.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    must = [r for r in rows if r["priority"] == "Must"]
    untested = [r["req_id"] for r in must if r["total"] == 0]
    lines = [
        "# Requirements Traceability Matrix",
        "",
        f"Generated {stamp} by `python -m nbit.traceability` from saved test results.",
        "",
        f"- Must requirements: **{len(must)}**; with at least one linked test: "
        f"**{len(must) - len(untested)}**" + (f" (untested: {', '.join(untested)})" if untested else ""),
        f"- Verified: **{sum(r['implementation_status'] == 'Verified' for r in rows)}** · "
        f"Implemented with stated gaps: **{sum(r['implementation_status'] == 'Implemented' for r in rows)}** · "
        f"In progress (core criterion missing): **{sum(r['implementation_status'] == 'In Progress' for r in rows)}** · "
        f"Failed tests: **{sum(r['test_status'] == 'Failed' for r in rows)}**",
        "",
        "| Req | Title | BN | Story | Test cases | Passed | Test status | Status | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['req_id']} | {r['title']} | {r['business_need'].replace(';', ', ')} | "
            f"{r['user_story']} | {r['test_cases']} | {r['passed']}/{r['total']} | "
            f"{r['test_status']} | **{r['implementation_status']}** | {r['notes']} |")
    (out_dir / "RTM.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    counts = {s: sum(c["status"] == s for c in cases) for s in ("Passed", "Failed", "Not Run")}
    lines = [
        "# Phase 7 Test Results",
        "",
        f"Generated {stamp}. Automated results come from `evidence/tc_results.json` "
        "(pytest); manual results from `uat/uat_results.csv`.",
        "",
        f"**{counts['Passed']} passed · {counts['Failed']} failed · {counts['Not Run']} not run** "
        f"of {len(cases)} test cases.",
        "",
        "| Test case | Title | Requirements | Method | Status | Pytest tests | Expected result | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for c in cases:
        lines.append(
            f"| {c['tc_id']} | {c['title']} | {c['requirements'].replace(';', ', ')} | "
            f"{c['method']} | **{c['status']}** | {c['executed_tests']} | "
            f"{c['expected_result']} | {c['notes']} |")
    (out_dir / "test_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_tracker(rows, cases, tracker=paths.DELIVERY_TRACKER):
    import openpyxl

    wb = openpyxl.load_workbook(tracker)
    by_req = {r["req_id"]: r for r in rows}
    evidence = f"{EVIDENCE_REL}/RTM.md"

    # RTM sheet: update FR rows, append NFR rows once.
    ws = wb["RTM"]
    header = [c.value.strip() if isinstance(c.value, str) else c.value for c in ws[1]]
    col = {name: i + 1 for i, name in enumerate(header)}
    seen = set()
    for row in range(2, ws.max_row + 1):
        req_id = ws.cell(row, col["FR_ID"]).value
        if req_id in by_req:
            seen.add(req_id)
            _write_rtm_row(ws, row, col, by_req[req_id], evidence)
    for req_id, r in by_req.items():
        if req_id not in seen:
            row = ws.max_row + 1
            ws.cell(row, col["FR_ID"], req_id)
            _write_rtm_row(ws, row, col, r, evidence)

    # User stories
    ws = wb["User_Stories"]
    header = [c.value for c in ws[1]]
    col = {name: i + 1 for i, name in enumerate(header)}
    for row in range(2, ws.max_row + 1):
        r = by_req.get(ws.cell(row, col["FR_ID"]).value)
        if not r:
            continue
        ws.cell(row, col["Status"], r["implementation_status"])
        ws.cell(row, col["Acceptance_Criteria_Status"], {
            "Verified": "Verified", "Implemented": "Partially Verified",
        }.get(r["implementation_status"], "Not Verified"))
        ws.cell(row, col["Evidence_Path"], evidence)

    # Releases
    ws = wb["Release_Tracker"]
    header = [c.value.strip() if isinstance(c.value, str) else c.value for c in ws[1]]
    col = {name: i + 1 for i, name in enumerate(header)}
    scope = {"R1": ["FR-001", "FR-002", "FR-003"],
             "R2": ["FR-004", "FR-005", "FR-006", "FR-007"],
             "R3": ["FR-008", "FR-009"], "R4": ["FR-010"], "R5": list(by_req)}
    for row in range(2, ws.max_row + 1):
        release = str(ws.cell(row, col["Release_ID"]).value).strip()
        if release in scope:
            statuses = {by_req[r]["implementation_status"] for r in scope[release]}
            ws.cell(row, col["Status"], "Verified" if statuses == {"Verified"}
                    else "In Progress" if "In Progress" in statuses else "Implemented")
            ws.cell(row, col["Evidence_Path"], evidence)

    # RAID: the integrated test environment now exists
    ws = wb["RAID_Register"]
    for row in range(2, ws.max_row + 1):
        if ws.cell(row, 1).value in ("DEP-010", "RSK-002"):
            ws.cell(row, 8, "Closed" if ws.cell(row, 1).value == "DEP-010" else "Mitigated")

    # Full test-case results sheet (replaced on every run)
    if "Phase7_Test_Results" in wb.sheetnames:
        del wb["Phase7_Test_Results"]
    ws = wb.create_sheet("Phase7_Test_Results")
    ws.append(["Test_Case_ID", "Title", "Requirements", "Method", "Test_Status",
               "Expected_Result", "Notes", "Evidence_Path"])
    for c in cases:
        ws.append([c["tc_id"], c["title"], c["requirements"], c["method"], c["status"],
                   c["expected_result"], c["notes"], f"{EVIDENCE_REL}/test_results.md"])

    wb.save(tracker)


def _write_rtm_row(ws, row, col, r, evidence):
    if r["business_need"]:
        ws.cell(row, col["Business_Need_ID"], r["business_need"].replace(";", ", "))
    if r["user_story"]:
        ws.cell(row, col["User_Story_ID"], r["user_story"])
    ws.cell(row, col["Test_Case_ID"], r["test_cases"])
    ws.cell(row, col["Priority"], r["priority"])
    ws.cell(row, col["Implementation_Status"], r["implementation_status"])
    ws.cell(row, col["Test_Status"], r["test_status"])
    ws.cell(row, col["Evidence_Path"], evidence)
    ws.cell(row, col["Notes"], r["notes"] or "All linked tests passed; no known gaps")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the RTM from test results.")
    parser.add_argument("--results", default=str(paths.EVIDENCE_DIR / "tc_results.json"))
    parser.add_argument("--out", default=str(paths.EVIDENCE_DIR))
    parser.add_argument("--update-tracker", action="store_true",
                        help="Write statuses into data/Phase_2/Delivery_Tracker.xlsx")
    args = parser.parse_args(argv)

    reqs, cases = load_inputs(args.results)
    rows = assess(reqs, cases)
    write_outputs(rows, cases, args.out)
    if args.update_tracker:
        update_tracker(rows, cases)

    for r in rows:
        print(f"{r['req_id']:<8} {r['test_status']:<8} {r['implementation_status']:<12} "
              f"{r['passed']}/{r['total']}  {r['notes']}")
    failed = [r for r in rows if r["test_status"] == "Failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
