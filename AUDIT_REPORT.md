# Resume_Crew — Ponytail Review

**Date:** 2026-10-23
**Scope:** Entire repository; complexity findings implemented and verified with tests.

## Changes

- Replaced the stale 436-line audit with this concise report.
- Centralized resume scoring/error handling and Markdown ranking output in `pipeline.py`; CLI and Gradio retain their own progress reporting.
- Removed duplicate dependency manifests. `pyproject.toml` is authoritative; installation consumers now use `pip install .` or `pip install -e '.[dev]'`. Added the previously missing optional `pyngrok` dependency and aligned Gradio's minimum version.
- Removed redundant mypy and pytest pre-commit hooks; CI remains the full verification gate.

## Verification

- `python -m pytest`: 25 passed.
- `ruff check src tests`, `ruff format --check src tests`, Python compilation, `python -m pip check`, and `git diff --check`: passed.
- Sample PDF extraction through an isolated environment with `pypdf`: succeeded for both bundled documents (resume: 2,064 chars; job description: 2,908 chars).
- Gradio browser: UI loaded and rank tab rendered; submitting sample resume folder + JD surfaced `No module named 'pypdf'` in the app environment. That dependency is declared in project metadata but is absent from this machine's global Python environment. Could not complete an interactive LLM ranking because the app process could not be restarted on occupied port 7860.
- Ollama: local server starts; detected installed `gemma3:1b` and `qwen3:1.7b`. CLI hardware check reports Ollama reachable. A model-backed ranking run was not completed in the installed app environment.
- `uv build`: built sdist and wheel successfully; verified prompt Markdown files are included in both.
- `pip install --dry-run --no-deps --break-system-packages --no-build-isolation .`: package metadata prepared successfully.
- `mypy --config-file pyproject.toml src`: blocked by missing installed dependencies/stubs (`pyngrok`, `matplotlib`, `pypdf`, `fpdf2`) and an installed NumPy stub requiring Python 3.12+ while project config targets 3.10.
