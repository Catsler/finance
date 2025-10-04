# Repository Guidelines

## Project Structure & Module Organization
- `scripts/` contains runnable workflows such as `phase6d_backtest.py`, `phase6d_review_2023.py`, and `check_stock_data.py`; treat them as the approved entry points for analytics.
- `utils/` holds shared helpers (for example `io.py`), so extend these modules instead of duplicating serialization or caching logic inside scripts.
- `results/` is the single source for generated artifacts—store outputs as `phase<stage>_<description>.<ext>` (e.g., `results/phase6d_2023_review.csv`) and avoid shadow directories like `results_v1.0-final_backup/`.
- `notebooks/` supports exploratory work; keep heavy exports in `results/` and reference them with relative paths.
- Repository state is tracked via `config.yaml`, `stock_pool.yaml`, and `TODO.md`; update them whenever data sources, plans, or execution status change.

## Build, Test, and Development Commands
- `python scripts/phase6d_backtest.py` refreshes the three-year benchmark comparison and overwrites the corresponding files under `results/`.
- `python scripts/phase6d_backtest.py --year <YYYY>` reruns a single-year slice to validate edits before scaling up.
- `python scripts/check_stock_data.py --auto-fallback` audits symbol coverage and logs substitutions in `results/phase6e_final_symbols.json`.
- `python scripts/generate_stock_pool_yaml.py --plan A` rebuilds the default allocation; use `--plan B` for the aggressive pool.
- `python test_environment.py` confirms dependencies and AKShare credentials before starting long jobs.

## Coding Style & Naming Conventions
- Follow PEP 8: four-space indentation, snake_case variables and functions, PascalCase classes, and UPPER_SNAKE constants.
- Prefer type hints, short intent-focused docstrings, and f-strings for formatting; match script names to the artifacts they emit (`phase6d_*`, `generate_*`).

## Testing Guidelines
- After logic changes, rerun the relevant backtest command and inspect regenerated `results/phase6d_<year>_*.csv` files for regressions.
- Add regressions tests under `tests/` (create if absent) or extend `test_environment.py` using pytest-style `test_*` functions.

## Commit & Pull Request Guidelines
- Write imperative commit subjects under 72 characters (for example, `Refine phase8 guardrails`), and group unrelated work into separate commits.
- PRs should summarize intent, note verification commands, attach or link key artifacts (e.g., `results/phase8_2021_review.csv`), and reference issues or TODO items when applicable.

## Security & Configuration Tips
- Store credentials outside the repo; reference local `.env` files via `config.yaml` entries rather than committing secrets.
- Keep backups local or use Git tags instead of committing bulky archives; add transient paths like `results_v1.0-final_backup/` to `.gitignore` when needed.
