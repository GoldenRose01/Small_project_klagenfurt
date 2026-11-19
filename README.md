# Instruction Structure and Compliance in AI-Generated Code (`RQ1` Pilot)

Experimental repository and evaluation harness for the elective research project (Specialisation in Artificial Intelligence and Cybersecurity, University of Klagenfurt).

## Research Question (`RQ1`)

> Holding specification content constant, does presenting requirements in explicit labeled sections (**Condition B — Structured**) change the proportion of code changes that pass all functional and authorization checks compared to a single prose paragraph (**Condition A — Prose**)?

## Repository Structure

The target codebase and the external evaluator are kept strictly separated so the coding agent under test cannot inspect the evaluation suite or reference solution:

- `pilot_repo/`: Minimal synthetic Python project (`reporting` package) with `visible_reports(user_groups, reports)`, `list_user_reports(user, reports)`, synthetic sample data, and baseline smoke tests (`tests/test_smoke.py`).
- `pilot_evaluator/`:
  - `prompts/prompt_A_prose.txt` & `prompts/prompt_B_structured.txt`: Frozen paired prompts built from the exact same sentences in identical order.
  - `evaluate.py`: Independent external evaluator checking `F01–F03` (functional, order preservation, input immutability) and `A01–A03` (group-based authorization; `A03` tracked as diagnostic overlap with `F01`).
  - `validate_evaluator.py`: Appendix D control validation against the starting commit, a blanket-denial baseline (`return []`), and a reference solution.
  - `run_pilot_pair.py`: Runs a single isolated `AB` or `BA` pair and writes Appendix C JSON records + `summary.md`.
  - `run_suite.py`: Single-command multi-model runner alternating `AB`/`BA` order and generating `suite_summary.md`.
  - `runs/`: Archived trial artifacts, patches, logs, and evaluation outputs.

## Quick Start

1. **Validate the external evaluator (Appendix D):**

   ```bash
   python3 pilot_evaluator/validate_evaluator.py
   ```

2. **Dry-run the harness (no external agent CLI required):**

   ```bash
   python3 pilot_evaluator/run_pilot_pair.py --dry-run
   ```

3. **Run an A–B pair with Codex CLI:**

   ```bash
   python3 pilot_evaluator/run_pilot_pair.py --env codex --env-version "0.169.1" --model "gpt-6.1-sol" --order AB
   ```

4. **Run a multi-model suite in Google Antigravity (`agy`, alternating `AB` / `BA`):**

   ```bash
   python3 pilot_evaluator/run_suite.py --env antigravity --models "gemini-4-neon-high,claude-opus-5-5-high,claude-sonnet-5-5-high"
   ```

## Preliminary Repository Pilot Results

All **29 valid runs** across both environments (**22/22** in OpenAI Codex, **7/7** in Google Antigravity) passed all six functional and authorization checks (`F01–F03`, `A01–A03`).

### OpenAI Codex (`codex-cli 0.169.1`)

- **Initial pilot** (`--full-auto`, `AB` order, `8/8 valid_pass`): `codex_pilot_01_gpt-6.2-sol_AB` through `codex_pilot_04_gpt-6-astra_AB`.
- **Frozen-snapshot restart** (`--approve-for-me`, `AB` order, `14/14 valid_pass`): `codex_restart_01_gpt-6-luna_AB` through `codex_restart_07_gpt-5.6-luna_AB` (see [`pilot_evaluator/runs/restart_20261119_comparison.md`](pilot_evaluator/runs/restart_20261119_comparison.md)).

| Series / Model | Order | A — Prose | B — Structured | Elapsed A (s) | Elapsed B (s) |
| :--- | :--- | :--- | :--- | ---: | ---: |
| Pilot: `gpt-6.2-sol` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 685.09 | 98.99 |
| Pilot: `gpt-6.2-astra` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 75.39 | 78.11 |
| Pilot: `gpt-6.1-sol` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 100.40 | 115.22 |
| Pilot: `gpt-6-astra` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 106.08 | 119.23 |
| Restart: `gpt-6-luna` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 39.79 | 34.93 |
| Restart: `gpt-6.1-sol` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 62.63 | 75.61 |
| Restart: `gpt-6.2-sol` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 69.46 | 79.31 |
| Restart: `gpt-6.2-astra` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 46.02 | 58.73 |
| Restart: `gpt-6-astra` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 58.35 | 59.78 |
| Restart: `gpt-6-sol` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 103.12 | 78.95 |
| Restart: `gpt-5.6-luna` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 57.07 | 67.93 |

### Google Antigravity (`agy 1.5.12`)

Archived in [`pilot_evaluator/runs/antigravity_suite_20261119/`](pilot_evaluator/runs/antigravity_suite_20261119/suite_summary.md) (`7/7` valid runs passed; `no_patch` runs caused by CLI model-routing errors, HTTP 503 capacity limits, or 120 s timeout are excluded from the valid denominator).

| Model | Order | A — Prose | B — Structured | Elapsed A (s) | Elapsed B (s) |
| :--- | :--- | :--- | :--- | ---: | ---: |
| `gemini-4-neon-high` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 150.60 | 250.71 |
| `claude-opus-5-5-high` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 74.89 | 72.18 |
| `claude-sonnet-5-5-high` | BA | `valid_pass` (6/6) | `valid_pass` (6/6) | 45.47 | 41.73 |
| `gemini-3.8-flash-high` | BA | `valid_pass` (6/6) | Infra fail (`no_patch`) | 364.35 | 8.33 |

- **Technical feasibility:** Confirmed (`29/29 valid_pass` across both environments and both prompt formats).
- **Next step:** Introduce a more discriminating multi-file / multi-constraint task (adapted from security-oriented benchmarks such as **SALLM** or **SecCodePLT**) to overcome the single-file ceiling effect.

