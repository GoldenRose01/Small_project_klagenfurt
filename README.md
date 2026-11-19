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

4. **Run a multi-model suite (alternating `AB` / `BA`):**

   ```bash
   python3 pilot_evaluator/run_suite.py --env codex --models "gpt-6.2-sol,gpt-6.2-astra,gpt-6.1-sol,gpt-6-astra"
   ```

## Preliminary Repository Pilot Results (`codex-cli 0.169.1`)

| Model | Order | A — Prose | B — Structured | Elapsed A (s) | Elapsed B (s) |
| :--- | :--- | :--- | :--- | ---: | ---: |
| `gpt-6.2-sol` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 685.09 | 98.99 |
| `gpt-6.2-astra` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 75.39 | 78.11 |
| `gpt-6.1-sol` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 100.40 | 115.22 |
| `gpt-6-astra` | AB | `valid_pass` (6/6) | `valid_pass` (6/6) | 106.08 | 119.23 |

- **Technical feasibility:** Confirmed (`8/8 valid_pass` across all functional and authorization checks).
- **Excluded runs:** Earlier runs blocked by `read-only` sandbox defaults, Windows/AppContainer write restrictions (including `gpt-6-luna`), or missing local `agy` CLI are retained in `pilot_evaluator/runs/` and excluded from the valid denominator per Appendix D.
- **Next step:** Alternate `BA` order and introduce a more discriminating multi-file / multi-constraint task (adapted from security-oriented benchmarks such as **SALLM** or **SecCodePLT**) to address the observed ceiling effect.
