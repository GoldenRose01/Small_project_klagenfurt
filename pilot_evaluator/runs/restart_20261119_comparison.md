# Codex multi-model restart — 2026-11-19

## Setup

- Codex CLI: `codex-cli 0.169.1`.
- Source files were frozen from project commit `298f831c769ac593a2cc17b9a08fd95e178de09b` into `restart_20261119_source_snapshot`. The runner records the snapshot's own baseline commit as `b4070d224930233e448f02e2be3c33ea057300a1`.
- Each model ran the A/B pair in `AB` order on that same snapshot, with a 120-second per-condition timeout.
- The Codex CLI in this environment rejects `--full-auto` as an unknown argument. The runs therefore used its supported `--approve-for-me` option. Both logs for every run report `sandbox: workspace-write`.
- `CODEX_WINDOWS_REGISTERED_CORE` was removed from the child test environment. With it set, Codex reported that the registered Core runner could not start.
- Command template used for each model: `codex exec --approve-for-me --model MODEL {prompt}`.
- Runner invocation template: `py .\pilot_evaluator\run_pilot_pair.py --repo .\pilot_evaluator\runs\restart_20261119_source_snapshot --env codex --env-version "codex-cli 0.169.1" --model MODEL --order AB --cmd "codex exec --approve-for-me --model MODEL {prompt}"`.

## Results

All 14 conditions produced an evaluable patch. Every A and B patch passed all six independent evaluator cases. There were no recorded command errors or timeouts in this restarted set.

| Model | A result | B result | Agent time A+B (s) | Evaluator time A+B (s) | Run folder |
|---|---|---|---:|---:|---|
| `gpt-6-luna` | valid_pass | valid_pass | 74.7198 | 1.7064 | `pair_20261119T125855Z_gpt-6-luna_AB` |
| `gpt-6.1-sol` | valid_pass | valid_pass | 138.2421 | 1.7055 | `pair_20261119T130012Z_gpt-6.1-sol_AB` |
| `gpt-6.2-sol` | valid_pass | valid_pass | 148.7691 | 1.7558 | `pair_20261119T130233Z_gpt-6.2-sol_AB` |
| `gpt-6.2-astra` | valid_pass | valid_pass | 104.7503 | 1.9567 | `pair_20261119T130505Z_gpt-6.2-astra_AB` |
| `gpt-6-astra` | valid_pass | valid_pass | 118.1231 | 1.7801 | `pair_20261119T130652Z_gpt-6-astra_AB` |
| `gpt-6-sol` | valid_pass | valid_pass | 182.0735 | 1.9094 | `pair_20261119T130854Z_gpt-6-sol_AB` |
| `gpt-5.6-luna` | valid_pass | valid_pass | 125.0001 | 1.7775 | `pair_20261119T131159Z_gpt-5.6-luna_AB` |

## Comparison

All seven configurations tied on quality: both formats passed every case. `gpt-6-luna` was fastest in this run, with a combined A+B agent time of 74.7198 seconds. It is the best configuration by the observed quality and runtime metrics in this benchmark.

Earlier folders in `runs` are retained for traceability but are excluded from this comparison. Those trials either ran read-only, used an unsupported CLI argument, or began before the shared source had been frozen.
