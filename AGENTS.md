# Resume_Crew — AGENTS.md

This file tells AI agents how to work in this repo. Read it before making changes.

## Project
Resume_Crew — grounded, local-first resume-to-job-description analysis.
- CLI: `python main.py` (or `python -m resume_crew.cli`)
- Gradio UI: `python app.py` (or `python -m resume_crew.app.main`)
- Package: `src/resume_crew/`
- Version: 1.4.0 (`src/resume_crew/__init__.py`)

## Key conventions
- **Python 3.10+**. Type annotations preferred; `from __future__ import annotations` on every module.
- **No `sys.path` hacks in package code.** For source-checkout launches, `app.py` adds `src` to the import path.
- **Config is centralized** in `src/resume_crew/config.py` (`Settings.from_env()`). Do not call `os.getenv` ad hoc in new code — read from `load_settings()`.
- **Prompts are versioned CRAFT templates** in `src/resume_crew/prompts/*.md`. New agent instructions go there, not inline in Python.
- **Output root** is `resume_crew.config.OUTPUT_ROOT` (project root / `output`). Do not use `Path("output")` relative to CWD.
- **Tests** live in `tests/`; run with `python -m pytest` or `make test`.
- **Lint/format/type**: `ruff`, `ruff format`, `mypy` (`make lint`, `make fmt`, `make typecheck`).

## Folder layout (summary)
```
src/resume_crew/          cli.py, config.py, document_reader.py, hardware.py,
                          pipeline.py, scoring.py, storage.py,
                          app/            main.py, workers.py, styles.css
                          prompts/        resume_profile.md, job_profile.md,
                                          gap_analysis.md, writer.md, scorer.md,
                                          resume_builder.md
tests/                    test_*.py
docs/                     architecture.md, api.md, deployment.md, prompting/
samples/                  Resumes/, Job_description/
```

## CRAFT prompt framework
Every agent prompt follows CRAFT: **C**ontext, **R**ole, **A**ction, **F**ormat, **T**one — plus negative constraints and few-shot grounding. Edit prompts in `src/resume_crew/prompts/`; they are rendered via `_render_prompt()` in `pipeline.py`.

## Safety rules (never simplify away)
- Input validation at trust boundaries (file size, extension, encryption).
- Error handling that prevents silent data loss (no swallowed exceptions without logging).
- No invented resume facts — the "grounded" constraint is the product's core value.
- Telemetry/opt-out env vars stay off by default.

## Before you finish
- Run `make lint` and `make typecheck`.
- Run `make test`.
- If you changed prompts or behavior, update `docs/` and `CHANGELOG.md`.
