# Architecture

Resume_Crew is a small, local-first Python package with two installed console commands—`resume-crew` and `resume-crew-ui`—sharing a common analysis core.

## Components

| Module | Responsibility |
|---|---|
| `config.py` | Centralized, validated settings (`Settings.from_env()`). Single source of truth for env vars. |
| `document_reader.py` | Safe text extraction for PDF/DOCX/TXT/MD with size, encryption, and emptiness validation. |
| `scoring.py` | Deterministic whole-term keyword overlap score; resume keyword highlighting (HTML). |
| `hardware.py` | CUDA / Apple MPS / CPU detection and Ollama profile recommendation. |
| `pipeline.py` | CrewAI agent orchestration (resume profile → job profile → gap analysis → writer) + Markdown/PDF/DOCX report assembly. Prompts rendered from `prompts/*.md` via `_render_prompt()`. |
| `storage.py` | Output directory creation, run metadata sidecars, run listing, and report rehydration. |
| `cli.py` | CLI entry (argparse) for analysis, resume ranking, and hardware checks. |
| `app/` | Gradio web UI: `main.py` (layout + wiring), `workers.py` (analysis/rank/batch/compare/build/history functions), `styles.css`. |

## Data flow (full analysis)
1. Resume + JD extracted to text (`document_reader.extract_text`).
2. Deterministic keyword score computed (`scoring.keyword_match_score`).
3. Four CrewAI agent stages run sequentially (`pipeline.run_llm_analysis`):
   - Resume Evidence Analyst → factual resume profile.
   - Job Requirements Analyst → factual job profile.
   - Resume Match Analyst → gap analysis (strong matches / evidence gaps / interview risks).
   - Grounded Resume Writer → tailored bullets + interview prep.
4. Report files are staged and atomically published under `output/<slug>` (`pipeline.build_report_files`, `storage.write_run_files`). The UI reports only that the report was saved locally; absolute filesystem paths stay server-side.
5. Optional PDF/DOCX export (`pipeline.markdown_to_pdf` / `markdown_to_docx`).

## Grounding constraint
No agent may invent facts. Every resume claim must be traceable to the source document. Prompts repeat this negative constraint deliberately because generation tasks (writer, resume builder) carry the highest fabrication risk.

## Prompts
CRAFT-structured templates live in `src/resume_crew/prompts/*.md` and are versioned separately from code.

## Output
Each run creates `output/<candidate>__<job>__<timestamp>/` containing `match_report.md`, `resume_profile.md`, `job_description_profile.md`, `skills_gap_analysis.md`, `tailored_resume_bullets.md`, `interview_preparation.md`, `run_meta.json`, plus optional `.pdf`/`.docx`.
