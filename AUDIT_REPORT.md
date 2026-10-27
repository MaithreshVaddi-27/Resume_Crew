# Resume_Crew — Engineering Audit

**Original audit date:** 2026-10-24
**Follow-up status:** Includes verified local follow-up changes after `bb831c4`; not all changes are committed.
**Scope:** Whole tracked project; manual source review plus regression and static checks.
**Assumption:** Local-first personal tool; public multi-user deployment remains out of scope.

## Executive summary

The project has a cohesive purpose and a sensible separation between CLI, Gradio workers, deterministic scoring, document extraction, storage, and LLM workflows. The original critical findings have since been addressed: public tunnels require authentication, malformed model scores are rejected, and report writes are staged before publication. Follow-up review also added a size limit for combined resume text and freeform notes in Build Resume, preventing that UI path from bypassing the extracted-text limit. This report records verified changes and remaining review items; it is not a certification of production readiness.

## Resolved findings

1. **Unauthenticated public UI exposure — fixed.** `src/resume_crew/app/main.py` exits before opening ngrok or Gradio sharing unless both `GRADIO_AUTH_USER` and `GRADIO_AUTH_PASS` are configured. Local-only launch remains available without credentials. Public sharing still uses a shared local report store and is not suitable for multi-user hosting; see `docs/deployment.md`.
2. **Malformed LLM scores treated as real scores — fixed.** `src/resume_crew/pipeline.py::_parse_match_score` rejects missing and out-of-range scores; failed rank results remain distinct from numeric scores.
3. **Partial report writes — fixed for caught write failures.** `src/resume_crew/storage.py::write_run_files` stages files and metadata, then publishes the completed run. Its cleanup path removes the staging and reserved run directories if a write fails. This is not a guarantee against abrupt machine or storage failure during filesystem publication.
4. **Combined resume and notes exceeded the document text limit — fixed.** `src/resume_crew/app/workers.py::build_resume_fn` checks combined source length before LLM setup and returns a clear limit message.
5. **History accepted arbitrary local report paths — fixed.** `src/resume_crew/storage.py::read_run_report` now reads only direct child directories under `OUTPUT_ROOT`; the History worker displays a warning for rejected paths. The run list skips malformed metadata and requires the stored directory name to match its containing folder.

## Remaining review items

- Cancellation takes effect between pipeline stages, not during a model call or retry sleep (`src/resume_crew/pipeline.py`, `src/resume_crew/app/workers.py`). The UI should continue to describe this boundary accurately; true in-call cancellation would depend on provider support.
- Numeric configuration validation is implemented: `OLLAMA_TIMEOUT` must be positive and finite, and `GRADIO_PORT` must be within 1–65535 (`src/resume_crew/config.py`).
- Ollama model-list parsing handles malformed JSON shapes by returning an empty list, with focused regression coverage (`src/resume_crew/hardware.py`).
- PDF extraction enforces the character ceiling incrementally across pages (`src/resume_crew/document_reader.py`); the compressed file-size ceiling does not independently bound memory used inside a single page extraction.
- Run directories use atomic `mkdir` with collision retry (`src/resume_crew/storage.py`).
- Public tunnels require authentication, but the UI still has shared storage and no per-user isolation. Do not treat basic authentication as multi-user authorization.

## Quality and operations

- Focused regression coverage now exercises score parsing, malformed Ollama payloads, config boundaries, interrupted writes, concurrent run creation, oversized notes, and incremental PDF limits across the test suite.
- CI currently targets Python 3.10. Add other supported Python versions and package install/build smoke checks if compatibility across that range becomes a release requirement.
- Review batch/ranking output formatting and accessible error presentation during the remaining UI audit.
- Privacy boundaries are documented in the README and deployment guide: Ollama is local, Gemini receives extracted text, reports stay in the local output directory, and public tunnels require credentials.
- Optional dependency groups remain a packaging choice; split them only if minimal CLI installation is an explicit requirement.

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

- Manually traced the tracked CLI, UI worker, config/provider selection, document extraction, score parsing, report storage, history, deployment, and prompt flows.
- Regression suite: 40 tests passed, including synthetic coverage for the Build Resume source limit, History path restriction, and malformed run metadata. This full run followed the latest changes.
- Ruff lint and formatting, Python compilation, and `git diff --check` passed on the current working tree.
- The public tunnel guard was manually exercised for unauthenticated sharing refusal and local-only startup. No public tunnel was opened.
- Type checking was not rerun as part of this follow-up; an earlier run was blocked by missing third-party stubs and incompatible installed NumPy stubs. No dependencies were installed.
- This remains a local-first review, not a complete security certification or validation of multi-user production deployment.

## Repo-wide audit — 2026-10-27

### Current status — 2026-10-27

- **Completed:** cancellation publication race, duplicate Analyze guard, server-local folder-path guidance, mobile settings layout, validated settings-driven UI initialization, accessible History score summaries, and ngrok startup ordering.
- **Open:** upload-based folder workflows, immediate provider-call cancellation, public-tunnel startup ordering, user-safe error mapping, and removal/documentation of checkout `sys.path` shims.
- **Verification:** 51 tests passed, 1 skipped; Ruff, formatting, compilation, and `git diff --check` passed; Brave DevTools desktop/mobile checks passed with no console warnings or errors.
- **Review limitation:** delegated final diff reviews could not run because the configured sub-agent provider returned `401 authentication_failed`; findings below were verified directly.

### Ranked findings

1. **P1 — Repeated Analyze clicks can start duplicate concurrent runs.** The Analyze action stays available while `analyze_stream()` starts a daemon worker, so multiple expensive LLM pipelines can update the same result components and publish separate reports. Disable the initiating action while running and restore it on every terminal yield. `src/resume_crew/app/main.py:168-179,247-263`; `src/resume_crew/app/workers.py:216-234`.

2. **P1 — Folder workflows depend on the server filesystem.** Rank and Batch Analyze accept a path in a browser textbox; a remote user’s local path is not the machine running Resume_Crew. Make the UI explicitly say “folder on the machine running Resume_Crew,” or replace the path input with uploaded files. `src/resume_crew/app/main.py:350-359,385-393`; `src/resume_crew/app/workers.py:350-355,399-404`.

3. **P1 — Cancel is cooperative, not immediate.** Cancellation cannot interrupt an in-flight provider call or retry sleep. A final checkpoint was added before report publication, preventing a cancel received during report assembly from publishing a run, but the UI should continue to describe cancellation as stopping after the current step. `src/resume_crew/app/workers.py:144-170,320-324`.

4. **P2 — ngrok is connected before Gradio starts listening — fixed.** The ngrok branch now starts Gradio with `prevent_thread_lock=True`, then creates the tunnel against the listening port and keeps the process alive. Local-only and built-in Gradio sharing paths remain unchanged. `src/resume_crew/app/main.py:603-649`.

5. **P2 — Root UI shim still mutates `sys.path`.** `app.py` is checkout-friendly but conflicts with the project rule against `sys.path.insert` hacks and behaves differently from an installed package. Add a proper installed entry point or document the shim as an intentional source-checkout compatibility path. `app.py:9-14`; `pyproject.toml:29-30`.

6. **P2 — Settings controls can display values different from validated runtime settings.** The UI reads raw environment values while workers use normalized `Settings`; an invalid or non-listed Gemini model can appear selected even though runtime settings resolve separately. Initialize controls from one validated settings object and normalize values against dropdown choices. `src/resume_crew/app/main.py:76-115`; `src/resume_crew/app/workers.py:56-69`.

7. **P3 — History trend failure is silent and the plot has no textual data alternative — fixed.** History now exposes every saved run and score as Markdown, and reports when the chart cannot be rendered instead of silently showing an empty plot. `src/resume_crew/app/workers.py:644-704`; `src/resume_crew/app/main.py:477-486,499-529`.

8. **P3 — Mobile settings toolbar is likely to overflow.** Three dropdowns and a button remain in one row at the mobile breakpoint. Stack the toolbar controls and make Refresh models full width on narrow screens. `src/resume_crew/app/main.py:77-117`; `src/resume_crew/app/styles.css:239-246`.

9. **P3 — UI errors expose raw exception details and server paths.** Worker error strings are sent directly to Markdown, which can reveal local paths or provider internals when the app is shared. Log detailed exceptions server-side and return short actionable user messages. `src/resume_crew/app/workers.py:187-192,249-254,372-373,454-455,511-512,619-620`.

### Applied fix

- Added a final cancellation checkpoint immediately before `write_run_files()`. A cancellation received after report assembly now exits without publishing a report. `src/resume_crew/app/workers.py:168-169`.

### Manual verification

- Existing UI at `http://localhost:7860/` loaded successfully in Brave DevTools.
- History loaded three saved runs and rendered the score trend.
- Hardware → Check hardware rendered the detection table and reported MPS availability, 8 CPU threads, 8.0 GB RAM, and Ollama unreachable.
- Browser console had no warning/error messages.
- A second launch attempt correctly failed with an actionable occupied-port error because port `7860` was already in use; no code change was made for this environment condition.

### Automated verification

- `python -m pytest`: **51 passed, 1 skipped**.
- `ruff check src tests`: **passed**.
- `ruff format --check src tests`: **passed**.
- `python -m compileall -q src app.py main.py`: **passed**.
- `git diff --check`: **passed**.

## Fix pass — 2026-10-27

### Completed

- **Duplicate Analyze guard:** Added a single non-blocking process-local lock around the full Analyze workflow. A second request now returns a clear message instead of launching another LLM thread; the lock is released from the worker's `finally` path. `src/resume_crew/app/workers.py:56-58,194-202,224-230`.
- **Cancellation publication race:** Kept the final cancellation checkpoint immediately before report publication so a cancellation during report assembly does not create a saved run. `src/resume_crew/app/workers.py:173-175`.
- **Folder-path clarity:** Rank and Batch Analyze now state that paths are resolved on the machine running Resume_Crew, which avoids misleading remote-browser expectations without replacing the established local workflow. `src/resume_crew/app/main.py:350-356,385-393`.
- **Mobile settings layout:** Settings controls now occupy separate full-width rows below 640px, preventing the provider/model/refresh toolbar from overflowing narrow screens. `src/resume_crew/app/styles.css:239-247`.

### Remaining

The lock intentionally limits concurrent analysis to one process-wide job. Per-user queues/storage isolation, upload-based folder workflows, immediate provider-call cancellation, public-tunnel startup ordering, and user-safe error mapping remain follow-up work. The lock is a local-first guard, not multi-user authorization.
