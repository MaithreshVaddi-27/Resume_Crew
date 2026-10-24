# Changelog

All notable changes to Resume_Crew are documented here.

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
- Fragile `sys.path` import hacks (kept only as a last-resort shim).
- Broad `except Exception` catch-alls narrowed where practical.

## [Unreleased]
### Planned
- Expanded test coverage (pipeline, app, conftest fixtures).
