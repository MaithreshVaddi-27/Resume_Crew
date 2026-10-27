# Contributing to Resume Crew

Thanks for contributing! Please follow these guidelines.

**Maintainer:** Maithresh Vaddi

## Setup
```bash
git clone https://github.com/MaithreshVaddi-27/Resume_Crew
cd Resume_Crew
make setup          # creates venv and installs runtime + dev deps
pre-commit install  # optional: run ruff on each commit
```

## Making changes
1. Create a branch: `git checkout -b <your-change>`.
2. Make your change. New agent instructions go in `src/resume_crew/prompts/*.md` (CRAFT format).
3. Add or update tests in `tests/`.
4. Run verification: `make lint`, `make typecheck`, `make test`.
5. Open a pull request against `main`.

## Pull request checklist
- [ ] Tests pass (`python -m pytest`).
- [ ] Lint is clean (`ruff check src tests`).
- [ ] Format is clean (`ruff format --check src tests`).
- [ ] Types check (`mypy --config-file pyproject.toml src`).
- [ ] `CHANGELOG.md` updated if user-facing behavior changed.
- [ ] No secrets or `.env` content committed.

## Code style
- Python 3.10+, type annotations, `from __future__ import annotations`.
- Ruff config lives in `pyproject.toml` (`[tool.ruff]`).
- Line length 100; docstrings on public modules/functions.

## Conduct
Be respectful and constructive. This project values grounded, honest output over impressive-sounding fabrication — the same standard applies to contributions.
