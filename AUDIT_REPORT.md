# Resume_Crew — Engineering Audit

**Date:** 2026-10-24
**Scope:** Whole tracked project; read-only source review plus attempted automated verification.
**Assumption:** Local-first personal tool; public deployment changes the priorities.

## Executive summary

The project has a cohesive purpose and a sensible separation between CLI, Gradio workers, deterministic scoring, document extraction, storage, and LLM workflows. Highest-risk findings: public UI sharing does not require authentication, malformed model scores silently become zero, and interrupted report writes can leave incomplete run directories. No fix was applied: this audit followed the Ponytail skill's explicit read-only boundary. A critical fix pass remains necessary after the deployment/privacy assumptions are confirmed.

## Phase 0 — Critical

1. **Public UI exposure is unauthenticated by default.** `src/resume_crew/app/main.py` can launch ngrok or Gradio sharing when enabled but only prints a warning if credentials are absent. Resume files/notes contain sensitive personal data. Require authentication before public sharing or require explicit opt-in to unauthenticated exposure. **Not fixed.** Decide whether public sharing is a supported use case.
2. **Malformed LLM scores are silently ranked as 0%.** `src/resume_crew/pipeline.py::_parse_match_score` assigns `0.0` if `SCORE:` is missing. This hides model contract failures as genuine low scores. Reject malformed outputs and represent failed scoring separately. **Not fixed.**
3. **Report output can be partially persisted.** CLI/UI create the final run directory and write files directly. Disk errors or process termination can leave partial reports; UI metadata is written afterward. Write to a temporary directory and atomically publish on success, or clean up failed writes. **Not fixed.**

## Phase 1 — High priority

- Validate numeric configuration ranges, not just parseability: `OLLAMA_TIMEOUT` currently accepts zero, negative, or non-finite values; `GRADIO_PORT` can be outside valid port range (`src/resume_crew/config.py`).
- Validate Ollama JSON structure in addition to JSON syntax; a valid but unexpected payload can raise in `list_ollama_models` (`src/resume_crew/hardware.py`).
- Enforce extracted-text caps incrementally while reading PDFs. The compressed file-size limit does not bound decompressed text or memory (`src/resume_crew/document_reader.py`).
- Make run-directory creation race-safe by handling `FileExistsError` from atomic `mkdir` rather than checking `exists()` first (`src/resume_crew/storage.py`).
- Bound the combined resume + free-form notes before sending it to an LLM (`src/resume_crew/app/workers.py::build_resume_fn`).
- Cancellation currently takes effect between pipeline stages, not during model calls or retry sleeps (`src/resume_crew/pipeline.py`, `src/resume_crew/app/workers.py`). Clarify this limitation in the UI or support cancellable provider calls.

## Phase 2 — Quality and operations

- Add focused regression coverage for score parsing failures, malformed Ollama payloads, config boundaries, interrupted writes, concurrent run creation, oversized notes, and incremental PDF limits.
- Expand CI from Python 3.10 to the actual supported-version range and add package build/install smoke checks.
- Keep failures visually distinct from low scores in batch/ranking views; error strings currently share the score-note presentation.
- Document privacy boundaries prominently: Ollama is local; Gemini receives document text; public tunnels expose the UI.
- Consider optional dependency groups for UI, plots, exports, and ngrok only if minimal CLI installs are a real requirement; update install docs in the same change.

## Phase 3 — Upgrades and downgrades

- **Team/public use:** add mandatory auth, per-user storage isolation, retention/deletion policy, and deployment secret management before positioning as multi-user.
- **Scoring quality:** evaluate both keyword overlap and LLM ranking against labeled examples before tuning prompts or claiming fit accuracy; these scores are not hiring decisions.
- **Downgrade unused workflows:** rank, batch analyze, compare, build, and history each add maintenance surface. Remove only after usage or product-owner confirmation.
- **Hardware profile:** recommendations currently report context sizes but do not configure Ollama. Label as advice only or connect it to actual run configuration.

## Ponytail complexity findings (read-only)

- `yagni:` Remove import-time `sys.path` mutation in `workers.py`; direct-launch path manipulation is duplicated in app entry points. Prefer installed package entry points, retaining only a required checkout shim. [src/resume_crew/app/workers.py:20-34]
- `shrink:` Batch analysis repeats resume enumeration, score sorting, and Markdown escaping; reuse shared helpers where output semantics match. [src/resume_crew/app/workers.py:396-480]
- `stdlib:` `ollama_is_running` and `list_ollama_models` duplicate URL request/error handling; stdlib feature is `urllib.request.urlopen`. Consolidate only if it shrinks the shared handling. [src/resume_crew/hardware.py:14-43]
- `yagni:` `src/resume_crew/app/__init__.py` exports only the `main` module name; remove `__all__` unless wildcard imports are intentionally supported. [src/resume_crew/app/__init__.py:5]
- `native:` Remove obsolete Compose `version: "3.9"`; modern Docker Compose uses the Compose Specification and ignores this field. [docker-compose.yml:1]

Estimated complexity reduction: **15–25 lines; 0 dependencies**. Findings are candidates, not applied changes.

## Verification and limitations

- Reviewed tracked inventory and major execution paths: pipeline, document extraction, scoring, storage, settings, hardware, UI workers/layout, CLI, packaging, tests, and CI.
- `python -m pytest` was attempted but blocked by the session Bash safety hook/classifier; no test result is claimed.
- No project code changed. The active Ponytail review explicitly prohibits changes and excludes correctness/security, so critical fixes are documented for a separate implementation pass.
- Clarification needed: is this strictly local/personal, or should the audit treat public multi-user deployment as a target? The report uses local-first as its baseline.
