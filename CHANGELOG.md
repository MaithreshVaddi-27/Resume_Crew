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
- ngrok live-share support with mandatory auth guard; Gradio built-in share as fallback.
- Report input size limits and atomic write to prevent partial/corrupted history entries.

### Changed
- Provider selection is explicit: choose MLX-LM, Ollama, or Gemini, then choose that provider's model; automatic provider fallback has been removed.
- Primary action button inverted to light-on-dark for stronger affordance.
- CSS palette shifted to slightly warmer neutrals; font extracted to `--font-ui` variable.
- Footer uses semantic `<footer>` element styled via CSS rule rather than inline override.
- Settings accordion replaces per-tab model selectors; provider/model choice is global.
- Auth required when public sharing is enabled (ngrok or Gradio share).

### Fixed
- Report history loading with missing or malformed JSON gracefully skipped.
- Resume input character limit (`MAX_EXTRACTED_CHARACTERS`) enforced before LLM call.
- Stale `output/` path resolution made relative to project root via `config.OUTPUT_ROOT`.
