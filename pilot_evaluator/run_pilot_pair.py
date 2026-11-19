#!/usr/bin/env python3
"""Turnkey runner for an A-B pair on the RQ1 repository pilot.

Creates two isolated clean copies of pilot_repo from the frozen commit,
executes the configured agent command (or dry-run check) in AB or BA order,
captures git diff patches, runs the independent evaluator, and writes
Appendix C JSON records plus a Markdown summary.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from evaluate import evaluate_repo

DEFAULT_PILOT_REPO = SCRIPT_DIR.parent / "pilot_repo"
PROMPTS_DIR = SCRIPT_DIR / "prompts"
RUNS_DIR = SCRIPT_DIR / "runs"


def _git_head(repo: Path) -> str:
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _git_diff(repo: Path) -> str:
    subprocess.run(["git", "add", "-N", "."], cwd=repo, check=False)
    res = subprocess.run(
        ["git", "diff", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout


def _run_single(
    condition: str,
    pair_position: int,
    run_dir: Path,
    args: argparse.Namespace,
    starting_commit: str,
) -> dict[str, Any]:
    prompt_file = (
        PROMPTS_DIR / "prompt_A_prose.txt"
        if condition == "A"
        else PROMPTS_DIR / "prompt_B_structured.txt"
    )
    prompt_text = prompt_file.read_text(encoding="utf-8")

    work_repo = run_dir / f"repo_{condition}"
    shutil.copytree(args.repo, work_repo)

    patch_file = run_dir / f"patch_{condition}.diff"
    eval_file = run_dir / f"eval_{condition}.json"
    log_file = run_dir / f"agent_{condition}.log"

    trial_classification = "infrastructure_failure"
    error_desc: str | None = None
    elapsed_agent_s: float | None = None

    if args.dry_run:
        # Dry-run verifies harness isolation, diff capture, and evaluator without an external LLM CLI.
        trial_classification = "no_patch"
        elapsed_agent_s = 0.0
        log_file.write_text("DRY RUN: no external agent CLI invoked.\n", encoding="utf-8")
    else:
        cmd_template = args.cmd
        if not cmd_template:
            if args.env == "codex":
                cmd_template = f"codex exec --model {args.model} {{prompt}}"
            elif args.env == "antigravity":
                cmd_template = f"antigravity chat --model {args.model} {{prompt}}"
            else:
                raise ValueError(f"Unsupported --env {args.env} without --cmd")

        cmd = cmd_template.replace("{prompt}", json.dumps(prompt_text))
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=work_repo,
                capture_output=True,
                text=True,
                timeout=args.timeout,
            )
            elapsed_agent_s = round(time.perf_counter() - t0, 4)
            log_file.write_text(
                f"EXIT: {proc.returncode}\n--- STDOUT ---\n{proc.stdout}\n--- STDERR ---\n{proc.stderr}\n",
                encoding="utf-8",
            )
            if proc.returncode != 0:
                error_desc = f"agent exited with code {proc.returncode}"
        except subprocess.TimeoutExpired:
            elapsed_agent_s = round(time.perf_counter() - t0, 4)
            error_desc = f"agent timed out after {args.timeout}s"
            log_file.write_text(f"TIMEOUT after {args.timeout}s\n", encoding="utf-8")
        except Exception as exc:
            elapsed_agent_s = round(time.perf_counter() - t0, 4)
            error_desc = f"infrastructure error: {type(exc).__name__}: {exc}"
            log_file.write_text(f"ERROR: {error_desc}\n", encoding="utf-8")

    patch_text = _git_diff(work_repo)
    patch_file.write_text(patch_text, encoding="utf-8")

    eval_result = evaluate_repo(work_repo, timeout_s=5.0)
    eval_file.write_text(json.dumps(eval_result, indent=2), encoding="utf-8")

    if not args.dry_run:
        if error_desc and not patch_text.strip():
            trial_classification = "infrastructure_failure" if "infrastructure" in error_desc else "no_patch"
        elif not patch_text.strip():
            trial_classification = "no_patch"
        elif eval_result["independent_all_passed"]:
            trial_classification = "valid_pass"
        else:
            trial_classification = "valid_fail"

    record: dict[str, Any] = {
        "identification": {
            "run_id": f"{run_dir.name}_{condition}",
            "task_id": "repo_pilot_v1",
            "starting_commit": starting_commit,
            "format": condition,
            "pair_position": pair_position,
        },
        "configuration": {
            "environment": args.env,
            "environment_version": args.env_version or "unrecorded",
            "exact_model": args.model,
            "settings": {"order": args.order, "dry_run": args.dry_run},
            "time_limit_s": args.timeout,
            "date_iso": datetime.now(timezone.utc).isoformat(),
        },
        "artifacts": {
            "prompt_file": str(prompt_file),
            "patch_file": str(patch_file),
            "agent_log_file": str(log_file),
            "evaluator_output_file": str(eval_file),
        },
        "outcomes": {
            "trial_classification": trial_classification,
            "cases": {c["case_id"]: c["passed"] for c in eval_result["cases"]},
            "independent_all_passed": eval_result["independent_all_passed"],
            "all_passed": eval_result["all_passed"],
            "elapsed_agent_s": elapsed_agent_s,
            "elapsed_evaluator_s": eval_result["elapsed_s"],
        },
        "anomalies": {
            "error_description": error_desc,
            "patch_evaluable": bool(patch_text.strip()),
            "included_in_analysis": trial_classification in {"valid_pass", "valid_fail", "no_patch"},
        },
    }
    (run_dir / f"record_{condition}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an A-B pair on pilot_repo.")
    parser.add_argument("--repo", type=Path, default=DEFAULT_PILOT_REPO, help="Path to frozen pilot_repo.")
    parser.add_argument("--env", default="codex", help="Agent environment name (e.g., codex, antigravity).")
    parser.add_argument("--env-version", default="", help="Exact CLI/IDE version string.")
    parser.add_argument("--model", default="unspecified", help="Exact model identifier.")
    parser.add_argument("--order", choices=["AB", "BA"], default="AB", help="Execution order.")
    parser.add_argument("--timeout", type=int, default=120, help="Agent timeout in seconds.")
    parser.add_argument("--cmd", default="", help="Optional custom command template containing {prompt}.")
    parser.add_argument("--dry-run", action="store_true", help="Verify harness without calling an external CLI.")
    args = parser.parse_args()
    args.repo = args.repo.resolve()

    if not args.dry_run and args.model == "unspecified":
        print("Error: --model must be explicitly specified for real runs.", file=sys.stderr)
        sys.exit(2)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RUNS_DIR / f"pair_{stamp}_{args.order}"
    run_dir.mkdir(parents=True, exist_ok=True)

    starting_commit = _git_head(args.repo)
    records = []
    for idx, cond in enumerate(list(args.order), start=1):
        records.append(_run_single(cond, idx, run_dir, args, starting_commit))

    summary_lines = [
        f"# Pair Summary ({run_dir.name})",
        "",
        f"- Starting commit: `{starting_commit}`",
        f"- Environment: `{args.env}` (`{args.env_version or 'unrecorded'}`)",
        f"- Model: `{args.model}`",
        f"- Order: `{args.order}`",
        f"- Dry run: `{args.dry_run}`",
        "",
        "| Format | Pos | Classification | Independent Pass | Agent (s) | Eval (s) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in records:
        o = r["outcomes"]
        summary_lines.append(
            f"| {r['identification']['format']} | {r['identification']['pair_position']} "
            f"| {o['trial_classification']} | {o['independent_all_passed']} "
            f"| {o['elapsed_agent_s']} | {o['elapsed_evaluator_s']} |"
        )
    summary_path = run_dir / "summary.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Pair complete. Summary written to {summary_path}")


if __name__ == "__main__":
    main()
