# Reporting Pilot Repository

Small synthetic Python project used to evaluate authorization-rule changes on a shared codebase.

## Structure

- `src/reporting/models.py`: Data helpers for users and reports.
- `src/reporting/policy.py`: Visibility filtering policy (`visible_reports`).
- `src/reporting/service.py`: Public entry point (`list_user_reports`).
- `src/reporting/sample_data.py`: Synthetic sample records illustrating the data format.
- `tests/test_smoke.py`: Baseline smoke tests.

## Running baseline checks

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
