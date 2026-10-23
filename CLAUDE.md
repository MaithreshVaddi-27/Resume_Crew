# Resume_Crew — CLAUDE.md

Working context for Claude Code sessions on this repo.

## What this project does
Compares a resume against a job description and produces an evidence-focused match report (keyword score, resume profile, job profile, gap analysis, tailored bullets, interview prep). Runs locally via Ollama with optional Gemini fallback. Ships a CLI and a Gradio web UI.

## How to run
```bash
# CLI
python main.py --resume samples/Resumes/sample_resume.pdf \
               --job-description samples/Job_description/sample_job_description.pdf \
               --provider ollama

# Gradio UI
python app.py

# Tests
python -m pytest

# Lint / format / type
ruff check src tests
ruff format --check src tests
mypy --config-file pyproject.toml src
```

## Where things live
- `src/resume_crew/` — package (cli, config, document_reader, hardware, pipeline, scoring, storage, app/, prompts/)
- `src/resume_crew/prompts/*.md` — CRAFT agent prompt templates (load via `resume_crew.prompts.load_prompt`)
- `src/resume_crew/app/` — Gradio UI (main.py layout, workers.py logic, styles.css)
- `tests/` — pytest suite
- `docs/` — architecture, API, deployment, prompting docs

## Prompting conventions used here
- **CRAFT** (Context / Role / Action / Format / Tone) for every agent prompt.
- **Negative constraints** ("never invent X") bound fabrication risk.
- **Few-shot grounding** shows correct vs incorrect output form.
- Prompts are rendered with `_render_prompt()` in `pipeline.py`.

## Do NOT
- Do not add `sys.path.insert` hacks.
- Do not hardcode `Path("output")` — use `config.OUTPUT_ROOT`.
- Do not put new agent instructions inline in Python — add a `.md` in `prompts/`.
- Do not commit `.env` or anything in `output/`.
