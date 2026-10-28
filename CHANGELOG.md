# Changelog

All notable changes to Resume Crew are documented here.

## [1.4.0] — 2026-10-23
### Added
- Gradio web UI with seven workflows: Analyze, Build Resume, Rank Resumes, Batch Analyze, Compare JDs, History, and Hardware.
- Cancel support for long-running analysis runs.
- PDF (.pdf) and Word (.docx) report exports.
- Hardware detection (CUDA / Apple MPS / CPU) with Ollama profile recommendation.
- Deterministic keyword scoring with whole-term matching (captures `R`, `C++`, `C#`, `node.js`).
- CrewAI telemetry disabled by default.

### Changed
- Split monolithic `app.py` into `src/resume_crew/app/` package (layout + workers + CSS).
- Centralized configuration in `src/resume_crew/config.py`.
- Versioned CRAFT prompt templates in `src/resume_crew/prompts/`.
- Added `--output` CLI flag; `output/` root now resolves to project root.
- Added `__main__.py` for `python -m resume_crew`.

### Fixed
- CWD-dependent output directory (was `Path("output")` relative to CWD).
- Removed checkout-only import shims; installed console commands are now the supported entry points.
- Broad `except Exception` catch-alls narrowed where practical.

## [Unreleased]
### Added
- Local model selector UI: per-session Ollama model dropdown with Refresh button.
- Gemini model selector exposed as a separate dropdown; toggles with provider choice.
- Resume ranking tab: score all resumes in a folder against one JD.
- Batch analyze tab: full per-resume reports for every file in a folder.
- Compare jobs tab: score one resume against multiple JD files simultaneously.
- Cancel button for long-running analysis with graceful `AnalysisCancelled` signal.
- PDF and Word (.docx) download buttons on the Full Report tab.
- History tab with score trend chart and per-run section viewer.
- Hardware check tab: Ollama reachability, CUDA/MPS/CPU profile, and model recommendation.
- Authenticated Gradio built-in public sharing, requiring both username and password.
- Report input size limits and atomic write to prevent partial/corrupted history entries.
- `tests/test_llm_provider.py`: build_llm coverage for MLX, Ollama, and Gemini providers.
- CI test coverage reporting via `pytest --cov=src --cov-report=term-missing`.

### Changed
- Provider selection is explicit: choose MLX-LM, Ollama, or Gemini, then choose that provider's model; automatic provider fallback has been removed.
- Primary action button inverted to light-on-dark for stronger affordance.
- CSS palette shifted to slightly warmer neutrals; font extracted to `--font-ui` variable.
- Footer uses semantic `<footer>` element styled via CSS rule rather than inline override.
- Settings accordion replaces per-tab model selectors; provider/model choice is global.
- Auth required when Gradio public sharing is enabled.
- `make lint`, `make test`, `make typecheck`, CI: Python target aligned to 3.12 (ruff `target-version`, CI `python-version`).
- CLI default provider in `make cli` changed from ollama to mlx (matches `LLM_PROVIDER` default).
- CLI `main()` gained a catch-all `Exception` handler so unexpected errors exit cleanly instead of tracebacking.

### Fixed
- Report history loading with missing or malformed JSON gracefully skipped.
- Resume input character limit (`MAX_EXTRACTED_CHARACTERS`) enforced before LLM call.
- Stale `output/` path resolution made relative to project root via `config.OUTPUT_ROOT`.
- Ruff `S603`/`S607` noqa split onto separate lines so ruff `0.9.0` (CI) and `0.16.6` (local) both pass.
