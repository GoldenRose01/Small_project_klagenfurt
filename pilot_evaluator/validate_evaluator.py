#!/usr/bin/env python3
"""Validate the external evaluator per Appendix D of the research proposal.

Verifies three control conditions on temporary copies of pilot_repo:
1. Starting commit -> must FAIL at least one new check.
2. Blanket-denial implementation (always returns []) -> must PASS A01/A02/F03 and FAIL F01/F02/A03.
3. Reference implementation -> must PASS all checks (F01-F03, A01-A03).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from evaluate import evaluate_repo

PILOT_REPO = Path("/home/antigravity/pilot_repo")

BLANKET_DENIAL_POLICY = '''"""Visibility policy (blanket-denial control)."""

from collections.abc import Iterable
from .models import Report


def visible_reports(user_groups: Iterable[str], reports: list[Report]) -> list[Report]:
    return []
'''

REFERENCE_POLICY = '''"""Visibility policy (reference solution)."""

from collections.abc import Iterable
from .models import Report


def visible_reports(user_groups: Iterable[str], reports: list[Report]) -> list[Report]:
    allowed = set(user_groups)
    if not allowed:
        return []
    return [dict(report) for report in reports if report.get("group") in allowed]
'''


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # 1. Starting commit
        start_copy = tmp_path / "starting"
        shutil.copytree(PILOT_REPO, start_copy)
        res_start = evaluate_repo(start_copy)
        assert not res_start["all_passed"], "Starting commit unexpectedly passed all checks!"
        print("[OK] Starting commit failed as expected:", [c["case_id"] for c in res_start["cases"] if not c["passed"]])

        # 2. Blanket denial
        denial_copy = tmp_path / "blanket_denial"
        shutil.copytree(PILOT_REPO, denial_copy)
        (denial_copy / "src" / "reporting" / "policy.py").write_text(BLANKET_DENIAL_POLICY)
        res_denial = evaluate_repo(denial_copy)
        denial_map = {c["case_id"]: c["passed"] for c in res_denial["cases"]}
        assert denial_map["A01"] and denial_map["A02"] and denial_map["F03"]
        assert not denial_map["F01"] and not denial_map["F02"] and not denial_map["A03"]
        print("[OK] Blanket-denial control passed A01/A02/F03 and failed F01/F02/A03 as expected.")

        # 3. Reference solution
        ref_copy = tmp_path / "reference"
        shutil.copytree(PILOT_REPO, ref_copy)
        (ref_copy / "src" / "reporting" / "policy.py").write_text(REFERENCE_POLICY)
        res_ref = evaluate_repo(ref_copy)
        assert res_ref["all_passed"], f"Reference solution failed: {res_ref}"
        print("[OK] Reference solution passed all 6 checks (F01-F03, A01-A03).")


if __name__ == "__main__":
    main()
