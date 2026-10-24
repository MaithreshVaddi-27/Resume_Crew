# Resume_Crew — Engineering Review Report

**Reviewed by:** Senior Engineering (ponytail mode — lazy/simplification-first lens applied)
**Project:** Resume_Crew — grounded, local-first resume-to-job-description analysis
**Version:** 1.4.0 (`src/resume_crew/__init__.py`)
**Branch reviewed:** `feat/local-model-selector-ui` (up to date with `origin`)
**Review date:** 2026-10-24
**Scope:** Complete file-surface review of all 43 tracked source/config/doc/test files

---

## Executive Summary

Resume_Crew is a **production-grade, local-first Python application** for its stated scope. The codebase is clean, well-structured, defensive by design, and passes every verification tool:

| Check | Command | Result |
|-------|---------|--------|
| Lint | `ruff check src tests` | ✅ All checks passed |
| Format | `ruff format --check src tests` | ✅ 26 files already formatted |
| Types | `mypy --config-file pyproject.toml src` | ✅ No issues in 13 source files |
| Tests | `python -m pytest` | ✅ 48 passed, 1 skipped |
| Compile | `python -m py_compile` (all modules) | ✅ OK |

No bugs, security defects, or correctness issues were found during this review. The project is **ready for production use within its stated scope** (local-first, personal tool; not multi-user hosting).

**Git state:** Working tree clean. No uncommitted changes. Nothing to commit or push at this time.

---

## Complete File Surface Reviewed (43 files)

### Entry points
| File | Role |
|------|------|
| `main.py` | CLI entry point (source-checkout shim; adds `src/` to path) |
| `app.py` | Gradio UI entry point (source-checkout shim) |
| `src/resume_crew/__main__.py` | `python -m resume_crew` CLI entry |

### Package core (`src/resume_crew/`)
| File | Role |
|------|------|
| `__init__.py` | Package marker, `__version__ = "1.4.0"` |
| `cli.py` | Argparse CLI: analysis, resume ranking, hardware check |
| `config.py` | Centralized `Settings.from_env()` with validation |
| `document_reader.py` | Safe PDF/DOCX/TXT/MD extraction (size, encryption, char-limit validation) |
| `hardware.py` | CUDA/MPS/CPU detection, Ollama profile recommendation |
| `pipeline.py` | CrewAI 4-stage orchestration + Markdown/PDF/DOCX report assembly |
| `scoring.py` | Deterministic whole-term keyword overlap + HTML highlighting |
| `storage.py` | Atomic run writes, metadata sidecars, path-traversal protection |

### Gradio UI (`src/resume_crew/app/`)
| File | Role |
|------|------|
| `__init__.py` | Package marker (docstring only) |
| `main.py` | Layout + event wiring; auth guard for public sharing |
| `workers.py` | Background analysis, rank, batch, compare, build, history workers |
| `styles.css` | Dark-theme design system, responsive, reduced-motion support |

### Versioned CRAFT prompts (`src/resume_crew/prompts/`)
| File | Agent | Purpose |
|------|-------|---------|
| `__init__.py` | — | `load_prompt()` disk-based template loader |
| `resume_profile.md` | Resume Evidence Analyst | Factual resume profile (Skills/Experience/Tools/Verified Achievements) |
| `job_profile.md` | Job Requirements Analyst | Factual job profile (Must-Have/Preferred/Seniority/Keywords) |
| `gap_analysis.md` | Resume Match Analyst | Strong matches / evidence gaps / interview risks |
| `writer.md` | Grounded Resume Writer | Tailored bullets + Interview Prep Guide |
| `scorer.md` | Resume Match Scorer | Single 0–100 score + one-sentence note |
| `resume_builder.md` | Resume Writer | Grounded tailored resume draft |

### Tests (`tests/`)
| File | Coverage |
|------|----------|
| `test_cli.py` | Settings validation, parser flags, tracing/telemetry off |
| `test_document_reader.py` | PDF char-limit, UTF-8 replacement, unsupported ext, empty file, missing file |
| `test_hardware.py` | Ollama model parsing (valid + malformed payload), profile validation |
| `test_ranking.py` | Score parsing (missing/out-of-range), error formatting, table escaping |
| `test_reports.py` | Writer output split (CRLF, level-3 headings, spacing), malformed rejection, PDF/DOCX export |
| `test_scoring.py` | Whole-term matching, single-char `R`, tuple fields, HTML escaping |
| `test_storage.py` | Atomic write failure cleanup, path traversal rejection, malformed metadata skip, slugify, timestamp format, unique dirs |

### Config / CI / Ops
| File | Role |
|------|------|
| `.env.example` | Safe configuration template (never committed) |
| `.gitignore` | Ignores `.env`, caches, `output/`, `dist/`, `.DS_Store`, `.taste-skill/` |
| `.pre-commit-config.yaml` | ruff + ruff-format hooks |
| `.github/workflows/ci.yml` | Python 3.10 CI: install, ruff check, ruff format, mypy, pytest |
| `Makefile` | `setup`, `test`, `lint`, `fmt`, `typecheck`, `ui`, `cli`, `clean` |
| `pyproject.toml` | Package metadata, ruff/mypy/pytest config, console script entry point |
| `Dockerfile` | Python 3.10-slim image, system deps, telemetry env |
| `docker-compose.yml` | Service definition with `./output` volume mount |

### Docs
| File | Role |
|------|------|
| `README.md` | Full user guide: install, configure, CLI, UI, privacy, troubleshooting |
| `AGENTS.md` | AI agent operating instructions (lint/typecheck/test before finish) |
| `CLAUDE.md` | Claude Code session context (where things live, CRAFT conventions) |
| `CHANGELOG.md` | 1.4.0 release notes + Unreleased section |
| `AUDIT_REPORT.md` | Engineering audit (resolved + remaining review items) |
| `docs/architecture.md` | Component map + data flow + grounding constraint |
| `docs/api.md` | Public API surface per module |
| `docs/deployment.md` | Local / Docker / Compose deployment + privacy + public access |
| `docs/prompting/craft-framework.md` | CRAFT structure + editing guidelines |

### Samples
| File | Role |
|------|------|
| `samples/Resumes/sample_resume.pdf` | Demo resume |
| `samples/Job_description/sample_job_description.pdf` | Demo job description |

---

## Detailed Module-by-Module Assessment

### 1. `config.py` — Centralized, validated settings ✅

**Strengths:**
- Single source of truth (`Settings.from_env()`); no ad-hoc `os.getenv` in new code.
- Validates `LLM_PROVIDER` against `("auto", "ollama", "gemini")`.
- Validates `OLLAMA_TIMEOUT` is positive and finite.
- Validates `GRADIO_PORT` is integer 1–65535.
- Validates `OLLAMA_PROFILE` against `("auto", "cuda", "mps", "cpu")`.
- Requires `GEMINI_API_KEY` when provider is `gemini` (fail-fast).
- `apply_telemetry_env()` forces CrewAI/OpenTelemetry off before any import.
- `auth` property returns credentials tuple only when both user and pass are set.

**Ponytail observations:** None requiring action. Clean, minimal, correct.

---

### 2. `document_reader.py` — Safe text extraction ✅

**Strengths:**
- File existence, is-file, and 15 MB size limit validation before reading.
- Password-protected PDF detection (`decrypt("") == 0` → error).
- Incremental character-limit enforcement across PDF pages (stops early at ~100k chars).
- Empty/whitespace-only text rejection ("may require OCR").
- UTF-8 with error replacement (no crashes on invalid bytes).
- Unsupported extension rejection with clear message.
- `pypdf` logger raised to ERROR to avoid benign xref warnings on stderr.

**Ponytail observations:** The compressed file-size ceiling does not independently bound memory inside a single page extraction — documented in `AUDIT_REPORT.md` as a known limitation, not a bug.

---

### 3. `scoring.py` — Deterministic keyword overlap ✅

**Strengths:**
- Whole-term matching (not substring) — captures `R`, `C++`, `C#`, `node.js`.
- `TOKEN_PATTERN` uses `*` (zero-or-more) so single-char tokens like `R` are captured (fix for ISSUE-17).
- Stopword filtering excludes common English words.
- `matched`/`missing` are tuples (frozen dataclass consistency — fix for BUG-06).
- `highlight_resume_matches` HTML-escapes output (XSS prevention) and uses the same tokenizer as scoring (avoids `\b` boundary failure on symbol-ending tokens like `c++`).

**Ponytail observations:** None. Well-tested (7 tests).

---

### 4. `hardware.py` — Ollama diagnostics + device detection ✅

**Strengths:**
- `ollama_is_running()`: urllib GET to `/api/tags`, catches `URLError`/`OSError`/`TimeoutError`, returns bool.
- `list_ollama_models()`: parses JSON, handles malformed payloads (`models: null`, non-list, missing names) → empty list.
- Cross-platform memory detection (Darwin `sysctl`, Windows ctypes, Linux `os.sysconf`).
- CUDA via `nvidia-smi`; picks GPU with most VRAM.
- MPS detection for Apple Silicon.
- `resolve_ollama_profile()`: context size recommendations by device (8192 vs 4096 vs 2048).
- `print_profile()`: human-readable CLI output.

**Ponytail observations:** `ollama_is_running` and `list_ollama_models` duplicate URL construction and error handling. Could consolidate into a private `_fetch_json()` helper, but this is a 15–25 line simplification candidate, not a defect.

---

### 5. `pipeline.py` — CrewAI orchestration + report assembly ✅

**Strengths:**
- `AnalysisCancelled` exception for clean cancellation signaling.
- `build_llm()`: provider selection (auto/ollama/gemini), model validation against installed Ollama models, Gemini key requirement, telemetry applied before import.
- `_run_single_task_with_retry()`: 3 attempts with 5s pause between transient failures.
- `_parse_match_score()`: rejects missing or out-of-range (>100) scores; failed ranks stay distinct from numeric scores (fix for malformed-score finding).
- `split_writer_output()`: handles `##`/`###` headings, CRLF, flexible spacing; `_renumber_loose_questions()` safety net recovers bare question lines.
- `build_report_files()`: assembles 6 Markdown files + combined `match_report.md`.
- `markdown_to_docx()` / `markdown_to_pdf()`: handle `#`–`####` headings, bullets, numbered lists, `**bold**`, `---` rules; PDF uses Latin-1-safe char replacements (no emoji, no TTF bundling).
- `build_docx_report()` / `build_pdf_report()`: return bytes for Gradio download.
- CrewAI tracing disabled per-task (`tracing=False`, `set_suppress_tracing_messages(True)`).

**Ponytail observations:** Cancellation takes effect between pipeline stages, not during a model call or retry sleep. True in-call cancellation depends on provider support. Documented accurately; not a defect.

---

### 6. `storage.py` — Output directory management ✅

**Strengths:**
- `slugify()`: NFKD normalization, ASCII-only, filesystem-safe, 48 char max.
- `create_run_directory()`: human-readable timestamp (`YYYYMMDD_HHMMSS`), atomic `mkdir(exist_ok=False)`, collision retry with `-N` suffix.
- `write_run_files()`: stages to `.{name}.tmp` dir, writes all files + meta, atomic `rename()`, cleanup (`shutil.rmtree` staging + `rmdir` directory) on `BaseException` failure — no partial/corrupted runs visible.
- `write_run_meta()`: JSON sidecar (candidate, job_title, score, timestamp, directory).
- `list_report_runs()`: most-recent-first, skips missing/malformed meta, validates score 0–100 finite, requires directory name match.
- `read_run_report()`: enforces `path.parent == OUTPUT_ROOT` (no path traversal), reads direct children only.

**Ponytail observations:** Not a guarantee against abrupt machine/storage failure during filesystem publication — documented limitation. Not a defect.

---

### 7. `cli.py` — Command-line interface ✅

**Strengths:**
- `_disable_external_tracing()`: forces telemetry off before CrewAI import.
- Flags: `--resume`, `--job-description`/`--jd`, `--provider`, `--output`/`-o`, `--rank-resumes`, `--check-hardware`, `--ollama-profile`, `--version`.
- `_run_analysis()`: extracts text, computes keyword score, builds LLM, runs 4-stage pipeline with step callback, writes atomic run files.
- `_rank_resumes()`: scores every resume in a folder against one JD.
- Error handling: catches `FileNotFoundError`, `FileExistsError`, `NotADirectoryError`, `OSError`, `RuntimeError`, `ValueError` → `parser.exit(1, ...)`.
- No `--export-docx`, `--history`, or `--print-ollama-env` flags (tests assert their absence intentionally).

**Ponytail observations:** None requiring action.

---

### 8. `workers.py` — Gradio background workers ✅

**Strengths:**
- `analyze_stream()`: background thread + queue-based progress streaming; cancel event; EMPTY_TABS placeholder sync asserted against output count.
- Cancellation between stages via `on_step` callback checking `cancel_event`.
- PDF/DOCX export failures caught per-format (one failure doesn't break the other); warnings appended to progress log.
- `rank_resumes_fn()`: folder enumeration, per-resume LLM scoring, sorted table.
- `batch_analyze_fn()`: full 4-step analysis per resume, per-run report, isolated error handling (one resume failure doesn't abort the batch).
- `compare_jds_fn()`: one resume vs multiple JDs, per-JD scoring, sorted table.
- `build_resume_fn()`: combined source length check (`MAX_EXTRACTED_CHARACTERS`) before LLM setup; grounded resume builder; PDF/DOCX export; failure appended to resume MD rather than crashing.
- `refresh_history_fn()` / `load_history_run_fn()`: score trend chart (matplotlib Agg), path-traversal-safe rehydration.

**Ponytail observations:** Resume enumeration + sorting + Markdown pipe escaping is repeated in `rank_resumes_fn` and `batch_analyze_fn`. Output semantics differ enough (table columns) that a shared helper would be marginal. Simplification candidate only.

---

### 9. `app/main.py` — Gradio UI layout ✅

**Strengths:**
- Telemetry disabled before any import (belt-and-suspenders with `config.py`).
- Gradio 4 vs 6 theme/css kwarg routing detected by major version.
- Provider dropdown toggles Ollama model vs Gemini model visibility.
- Refresh models button calls `workers.refresh_local_models()`.
- `analyze_outputs` count asserted against `analyze_stream()` yield count (1 + len(EMPTY_TABS) + 1) — prevents silent mismatch.
- `build_outputs` count asserted against `build_resume_fn()` yield count (5).
- Public sharing guard: exits if `(ngrok_authtoken or gradio_share)` and no `settings.auth`.
- Footer includes disclaimer: keyword scores are not ATS/hiring recommendations.

**Ponytail observations:** `LOCAL_MODELS, DEFAULT_LOCAL_MODEL = workers.local_model_choices()` is evaluated at import time (blocks briefly on Ollama call). Acceptable for a desktop UI; not a defect.

---

### 10. `styles.css` — Design system ✅

**Strengths:**
- Dark theme with CSS custom properties (`--bg-page`, `--bg-card`, `--accent`, etc.).
- Responsive media query (`max-width: 640px`).
- `prefers-reduced-motion` respected.
- Focus-visible outlines (3px accent) for accessibility.
- `<mark>` tags forced readable in dark mode.
- Scrollbar styling.
- No layout-shift-prone absolute positioning.

**Ponytail observations:** None. Clean, purposeful CSS.

---

### 11. CRAFT Prompt Templates ✅

All six prompts follow the CRAFT framework (Context / Role / Action / Format / Tone) plus negative constraints and few-shot grounding:

- **Negative constraints:** "Never infer, complete, assume, or invent employers, dates, skills, degrees, certifications, or metrics" — repeated in resume_profile, job_profile, gap_analysis, writer, and resume_builder prompts.
- **Few-shot grounding:** Correct vs incorrect bullet form shown (`- **Languages:** Used Python...` vs `- **Languages:** Python, Java, C++`).
- **Input isolation:** Analysts receive only profiles, never raw resumes, preventing cross-document leakage.
- **Fail-fast parsing:** `_parse_match_score` rejects malformed scores; `_renumber_loose_questions` recovers bare questions.

**Ponytail observations:** None. The prompt framework is correctly implemented per `AGENTS.md` and `docs/prompting/craft-framework.md`.

---

## Verification Deep-Dive

### Test inventory (48 passed, 1 skipped)

| Test file | Tests | Focus |
|-----------|-------|-------|
| `test_cli.py` | 8 | Settings validation, parser flags, telemetry off |
| `test_document_reader.py` | 5 | PDF char-limit, UTF-8, unsupported ext, empty file, missing file |
| `test_hardware.py` | 5 | Ollama model parsing (valid + malformed), profile validation |
| `test_ranking.py` | 4 | Score parsing, error formatting, table escaping |
| `test_reports.py` | 11 | Writer split (CRLF, level-3, spacing), malformed rejection, PDF/DOCX |
| `test_scoring.py` | 7 | Whole-term matching, single-char `R`, tuples, HTML escaping |
| `test_storage.py` | 8 | Atomic write cleanup, path traversal, malformed metadata, slugify, timestamp, unique dirs |

### Static analysis
- `ruff check src tests` — 0 findings
- `ruff format --check src tests` — 26 files formatted, 0 changes needed
- `mypy --config-file pyproject.toml src` — 0 issues in 13 source files
- `python -m py_compile` on all `.py` files — 0 errors
- `python -c "import resume_crew"` — works when installed (module not on path from repo root without install, which is expected; entry points `main.py`/`app.py` add `src/` to path)

### CI (`docs/deployment.md` + `.github/workflows/ci.yml`)
- Python 3.10 on ubuntu-latest
- Installs `.[dev]` (pytest, ruff, mypy)
- Runs ruff check, ruff format check, mypy, pytest

---

## Remaining Review Items (from `AUDIT_REPORT.md` + this review)

These are **candidates, not defects**. None block production use.

| # | Item | Location | Severity | Recommendation |
|---|------|----------|----------|----------------|
| 1 | Cancellation between stages only, not mid-model-call | `pipeline.py`, `workers.py` | Low | Document boundary accurately (already done); true in-call cancellation requires provider support. |
| 2 | Resume enumeration duplicated in rank + batch | `workers.py` | Very Low | Optional shared helper; output semantics differ enough that it's not urgent. |
| 3 | Ollama HTTP handling duplicated | `hardware.py` | Very Low | Optional `_fetch_json()` helper; 15–25 line simplification. |
| 4 | Shared storage, no per-user isolation | `storage.py`, `app/main.py` | Low | Documented as personal/local use; basic auth ≠ multi-user authorization. Do not position as multi-tenant. |
| 5 | Hardware profile is advice only | `hardware.py` | Very Low | Label as advice (already done in audit) or connect to actual Ollama run configuration. |
| 6 | Compose `version: "3.9"` obsolete | `docker-compose.yml` | Very Low | Remove field; modern Compose Spec ignores it. |
| 7 | `app/__init__.py` exports only module name | `app/__init__.py` | Very Low | Remove `__all__` unless wildcard imports intended. |
| 8 | Import-time `sys.path` mutation duplicated | `workers.py`, `main.py`, `app.py` | Low | Prefer installed package entry points; keep checkout shim only. |

Estimated complexity reduction from ponytail candidates: **15–25 lines, 0 dependencies.**

---

## Security Posture

| Control | Status | Location |
|---------|--------|----------|
| Input validation at trust boundaries | ✅ | `document_reader.py` (size, extension, encryption, emptiness, char-limit) |
| Path traversal protection | ✅ | `storage.read_run_report` (parent == OUTPUT_ROOT) |
| Atomic writes / no partial runs | ✅ | `storage.write_run_files` (staging + rename + cleanup) |
| HTML escaping / XSS prevention | ✅ | `scoring.highlight_resume_matches` |
| Public sharing auth guard | ✅ | `app/main.py` (exits without both GRADIO_AUTH_USER/PASS) |
| Telemetry/tracing disabled by default | ✅ | `config.py`, `app/main.py`, `cli.py`, `pipeline.py` |
| CrewAI tracing per-task off | ✅ | `pipeline.py` (`tracing=False`) |
| `.env` gitignored | ✅ | `.gitignore` |
| Grounding / no-invention constraints | ✅ | All 6 CRAFT prompts + README disclaimer |

---

## Production Readiness Verdict

**Resume_Crew is production-ready for its stated scope:** a local-first, personal resume-to-job-description analysis tool with CLI and Gradio UI, Ollama primary / Gemini fallback, PDF/DOCX export, history, and authenticated optional public sharing.

**Not recommended for:** multi-user hosting, SaaS deployment, or as an ATS/hiring decision system (documented in README disclaimer and deployment.md).

---

## Recommended Next Steps (optional)

1. If you want to apply ponytail simplifications: remove `version: "3.9"` from `docker-compose.yml`, optionally consolidate Ollama HTTP handling in `hardware.py`.
2. If expanding to multi-user: add per-user storage isolation, retention/deletion policy, and deployment secret management (per `AUDIT_REPORT.md` Phase 3).
3. If claiming scoring accuracy: evaluate keyword overlap + LLM ranking against labeled examples before tuning prompts (per `AUDIT_REPORT.md`).

---

**End of report.** No changes were made to the codebase; working tree remains clean. Nothing committed or pushed.