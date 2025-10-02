# Repository Guidelines

## Project Structure & Module Organization
- `scripts/` hosts executable workflows such as `phase6d_backtest.py`, `check_stock_data.py`, and `generate_stock_pool_yaml.py`. Treat this directory as the primary entry point for analytics and pipeline jobs.
- `utils/` contains shared helpers (for example, `io.py` for caching and JSON metadata). Extend these utilities rather than duplicating logic in scripts.
- `results/` is the canonical output location for logs, CSVs, and JSON reports. Follow the convention `phase<stage>_<description>.<ext>` (e.g., `phase6d_2023_review.csv`).
- `notebooks/` stores exploratory dashboards. Keep heavy exports in `results/` and reference them via relative paths inside notebooks.
- Configuration and status tracking live in `config.yaml`, `stock_pool.yaml`, and `TODO.md`; update these when adjusting data sources or execution plans.

## Build, Test, and Development Commands
- `python scripts/phase6d_backtest.py` — runs the three-year validation workflow and refreshes comparison artifacts under `results/`.
- `python scripts/phase6d_backtest.py --year <YYYY>` — reruns a single-year slice (useful after modifying selection logic).
- `python scripts/phase6d_review_2023.py` — generates monthly holdings diagnostics and summary notes for 2023.
- `python scripts/check_stock_data.py [--auto-fallback]` — audits data availability for expanded pools; with the flag it applies predefined substitutions and records them in `results/phase6e_final_symbols.json`.
- `python scripts/generate_stock_pool_yaml.py --plan A` — rebuilds `stock_pool.yaml`; switch to `--plan B` for the aggressive allocation.
- `python test_environment.py` — sanity check that dependencies and AKShare access remain functional.

## Coding Style & Naming Conventions
- Follow PEP 8: four-space indentation, snake_case for functions and variables, PascalCase for classes, and UPPER_SNAKE for module constants.
- Prefer type hints and concise docstrings explaining intent; use f-strings for formatting.
- Name scripts with action-oriented prefixes (`phase6d_*`, `generate_*`), and mirror artifact names after their producing script.

## Testing Guidelines
- After any logic change, rerun the relevant yearly backtest command and inspect regenerated files in `results/`.
- Store diagnosis outputs with the pattern `phase6d_<year>_*.csv` and review them before committing.
- Add unit tests under `tests/` (create the directory if absent) or extend `test_environment.py`; use pytest-compatible `test_*` function signatures.

## Commit & Pull Request Guidelines
- Write imperative commit subjects under 72 characters (e.g., `Remove Sharpe ratio placeholder`). Group unrelated updates into separate commits when feasible.
- PR descriptions should include: a concise summary, verification notes (commands run or artifact links), and any follow-up tasks. Link issues when applicable.
- Attach or reference generated outputs (for example, `results/phase6d_2023_review.csv`) so reviewers can validate analysis without re-running workflows.
