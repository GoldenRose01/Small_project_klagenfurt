#!/usr/bin/env python3
"""Independent external evaluator for the RQ1 repository pilot.

Evaluates a target repository directory against Appendix B cases:
- F01: Single group (red, blue, red -> user in red sees 1st and 3rd in order)
- F02: Multiple groups (user in red and blue sees all 3 in order)
- F03: Empty data (empty reports list -> [])
- A01: No group (empty user_groups -> [])
- A02: Unrelated group (user in green -> [] for red/blue reports)
- A03: Mixed response (diagnostic check overlapping F01: excludes blue, non-empty)

Checks both `reporting.visible_reports` and `reporting.list_user_reports`,
verifies input immutability, and enforces a per-case timeout.
"""

from __future__ import annotations

import argparse
import copy
import json
import multiprocessing
import sys
import time
from pathlib import Path
from typing import Any


def _base_reports() -> list[dict[str, str]]:
    return [
        {"id": "r1", "group": "red", "title": "Red One"},
        {"id": "r2", "group": "blue", "title": "Blue Two"},
        {"id": "r3", "group": "red", "title": "Red Three"},
    ]


def _run_case_worker(repo_path: str, case_id: str, queue: multiprocessing.Queue) -> None:
    src_path = str(Path(repo_path) / "src")
    sys.path.insert(0, src_path)
    try:
        from reporting import list_user_reports, visible_reports  # type: ignore
    except Exception as exc:
        queue.put({"passed": False, "error": f"import_error: {type(exc).__name__}: {exc}"})
        return

    try:
        reports = _base_reports()
        reports_snapshot = copy.deepcopy(reports)

        if case_id == "F01":
            groups = ["red"]
            groups_snapshot = copy.deepcopy(groups)
            res_fn = visible_reports(groups, reports)
            res_svc = list_user_reports({"id": "u_red", "groups": list(groups)}, reports)
            expected = [reports_snapshot[0], reports_snapshot[2]]
            ok = (
                res_fn == expected
                and res_svc == expected
                and reports == reports_snapshot
                and groups == groups_snapshot
            )
            reason = "" if ok else f"expected {[r['id'] for r in expected]}, got fn={res_fn}, svc={res_svc}"

        elif case_id == "F02":
            groups = ["red", "blue"]
            groups_snapshot = copy.deepcopy(groups)
            res_fn = visible_reports(groups, reports)
            res_svc = list_user_reports({"id": "u_rb", "groups": list(groups)}, reports)
            expected = reports_snapshot
            ok = (
                res_fn == expected
                and res_svc == expected
                and reports == reports_snapshot
                and groups == groups_snapshot
            )
            reason = "" if ok else f"expected all 3 reports in order, got fn={res_fn}, svc={res_svc}"

        elif case_id == "F03":
            empty_reports: list[dict[str, str]] = []
            groups = ["red"]
            groups_snapshot = copy.deepcopy(groups)
            res_fn = visible_reports(groups, empty_reports)
            res_svc = list_user_reports({"id": "u_red", "groups": list(groups)}, empty_reports)
            ok = res_fn == [] and res_svc == [] and empty_reports == [] and groups == groups_snapshot
            reason = "" if ok else f"expected [], got fn={res_fn}, svc={res_svc}"

        elif case_id == "A01":
            groups: list[str] = []
            res_fn = visible_reports(groups, reports)
            res_svc = list_user_reports({"id": "u_none", "groups": []}, reports)
            ok = res_fn == [] and res_svc == [] and reports == reports_snapshot
            reason = "" if ok else f"expected [] for no-group user, got fn={res_fn}, svc={res_svc}"

        elif case_id == "A02":
            groups = ["green"]
            groups_snapshot = copy.deepcopy(groups)
            res_fn = visible_reports(groups, reports)
            res_svc = list_user_reports({"id": "u_green", "groups": list(groups)}, reports)
            ok = (
                res_fn == []
                and res_svc == []
                and reports == reports_snapshot
                and groups == groups_snapshot
            )
            reason = "" if ok else f"expected [] for unrelated group, got fn={res_fn}, svc={res_svc}"

        elif case_id == "A03":
            groups = ["red"]
            groups_snapshot = copy.deepcopy(groups)
            res_fn = visible_reports(groups, reports)
            res_svc = list_user_reports({"id": "u_red", "groups": list(groups)}, reports)
            fn_groups = [r.get("group") for r in res_fn] if isinstance(res_fn, list) else []
            svc_groups = [r.get("group") for r in res_svc] if isinstance(res_svc, list) else []
            ok = (
                isinstance(res_fn, list)
                and isinstance(res_svc, list)
                and len(res_fn) > 0
                and len(res_svc) > 0
                and "blue" not in fn_groups
                and "blue" not in svc_groups
                and reports == reports_snapshot
                and groups == groups_snapshot
            )
            reason = "" if ok else f"mixed-response check failed: fn_groups={fn_groups}, svc_groups={svc_groups}"
        else:
            ok = False
            reason = f"unknown case_id: {case_id}"

        queue.put({"passed": ok, "error": reason})
    except Exception as exc:
        queue.put({"passed": False, "error": f"runtime_error: {type(exc).__name__}: {exc}"})


def evaluate_repo(repo_path: Path, timeout_s: float = 5.0) -> dict[str, Any]:
    cases = [
        ("F01", "functional", True),
        ("F02", "functional", True),
        ("F03", "functional", True),
        ("A01", "authorization", True),
        ("A02", "authorization", True),
        ("A03", "authorization_diagnostic_overlap_F01", False),
    ]
    t0 = time.perf_counter()
    results: list[dict[str, Any]] = []

    for case_id, category, independent in cases:
        q: multiprocessing.Queue = multiprocessing.Queue()
        proc = multiprocessing.Process(target=_run_case_worker, args=(str(repo_path), case_id, q))
        proc.start()
        proc.join(timeout=timeout_s)
        if proc.is_alive():
            proc.terminate()
            proc.join()
            outcome = {"passed": False, "error": f"timeout after {timeout_s}s"}
        elif not q.empty():
            outcome = q.get()
        else:
            outcome = {"passed": False, "error": "process exited without output"}

        results.append(
            {
                "case_id": case_id,
                "category": category,
                "independent_evidence": independent,
                "passed": bool(outcome["passed"]),
                "error": outcome["error"],
            }
        )

    elapsed_s = round(time.perf_counter() - t0, 4)
    all_passed = all(r["passed"] for r in results)
    independent_passed = all(r["passed"] for r in results if r["independent_evidence"])
    return {
        "repo_path": str(repo_path),
        "all_passed": all_passed,
        "independent_all_passed": independent_passed,
        "elapsed_s": elapsed_s,
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RQ1 repository pilot.")
    parser.add_argument("repo_path", type=Path, help="Path to the repository copy to evaluate.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-case timeout in seconds.")
    args = parser.parse_args()
    report = evaluate_repo(args.repo_path.resolve(), timeout_s=args.timeout)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["all_passed"] else 1)


if __name__ == "__main__":
    main()
