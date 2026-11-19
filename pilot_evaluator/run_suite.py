#!/usr/bin/env python3
"""Single-command multi-model runner for the RQ1 repository pilot.

Runs an A-B (alternating AB / BA) pair for each specified model in sequence,
collects all patches/evaluator results, and writes a unified suite_summary.md
and suite_results.json.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_pilot_pair import DEFAULT_PILOT_REPO, RUNS_DIR, _git_head, _run_single

DEFAULT_MODELS = [
    "gemini-4-hydrogen-high",
    "gemini-4-argon-high",
    "gemini-4-neon-high",
    "Claude Opus 5.5 (Thinking)",
]


def _detect_version(env: str) -> str:
    exe = "agy" if env == "antigravity" else env
    try:
        res = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return "unrecorded"


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RQ1 A-B pairs across multiple models.")
    parser.add_argument("--repo", type=Path, default=DEFAULT_PILOT_REPO, help="Path to frozen pilot_repo.")
    parser.add_argument("--env", default="antigravity", help="Agent environment (antigravity, codex).")
    parser.add_argument("--env-version", default="", help="Optional CLI version override.")
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="Comma-separated list of exact model identifiers.",
    )
    parser.add_argument("--timeout", type=int, default=120, help="Per-run agent timeout in seconds.")
    parser.add_argument("--cmd", default="", help="Optional command template with {model} and {prompt}.")
    parser.add_argument("--dry-run", action="store_true", help="Verify suite without calling an external CLI.")
    args = parser.parse_args()

    repo = args.repo.resolve()
    starting_commit = _git_head(repo)
    env_version = args.env_version or ("dry-run" if args.dry_run else _detect_version(args.env))
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    cmd_template = args.cmd
    if not cmd_template:
        if args.env == "antigravity":
            cmd_template = 'agy -p {prompt} --model "{model}" --dangerously-skip-permissions'
        elif args.env == "codex":
            cmd_template = 'codex exec --full-auto --model "{model}" {prompt}'
        else:
            raise ValueError(f"Unsupported --env {args.env} without --cmd")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suite_dir = RUNS_DIR / f"suite_{stamp}"
    suite_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    for idx, model in enumerate(models):
        order = "AB" if idx % 2 == 0 else "BA"
        model_dir = suite_dir / f"{idx + 1:02d}_{_slug(model)}_{order}"
        model_dir.mkdir(parents=True, exist_ok=True)

        run_args = SimpleNamespace(
            repo=repo,
            env=args.env,
            env_version=env_version,
            model=model,
            order=order,
            timeout=args.timeout,
            cmd=cmd_template,
            dry_run=args.dry_run,
        )
        print(f"[{idx + 1}/{len(models)}] Running {model} (order {order})...")
        for pos, cond in enumerate(list(order), start=1):
            rec = _run_single(cond, pos, model_dir, run_args, starting_commit)
            all_records.append(rec)

    (suite_dir / "suite_results.json").write_text(json.dumps(all_records, indent=2), encoding="utf-8")

    lines = [
        f"# Suite Summary ({suite_dir.name})",
        "",
        f"- Starting commit: `{starting_commit}`",
        f"- Environment: `{args.env}` (`{env_version}`)",
        f"- Dry run: `{args.dry_run}`",
        "",
        "| Model | Order | Format | Classification | Independent Pass | Agent (s) | Eval (s) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in all_records:
        cfg = r["configuration"]
        ident = r["identification"]
        out = r["outcomes"]
        lines.append(
            f"| {cfg['exact_model']} | {cfg['settings']['order']} | {ident['format']} "
            f"| {out['trial_classification']} | {out['independent_all_passed']} "
            f"| {out['elapsed_agent_s']} | {out['elapsed_evaluator_s']} |"
        )
    summary_path = suite_dir / "suite_summary.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nSuite complete. Unified summary: {summary_path}")


if __name__ == "__main__":
    main()
