# Prompting — CRAFT Framework

All agent instructions in Resume Crew live as versioned Markdown templates in `src/resume_crew/prompts/` and are rendered at runtime via `_render_prompt()` in `pipeline.py`. They are **not** inline in Python.

## CRAFT structure

| Letter | Meaning | Purpose |
|---|---|---|
| **C** | Context | Background and input assumptions (what the agent receives). |
| **R** | Role | Who the agent is and its single job. |
| **A** | Action | Concrete task and step-by-step behavior. |
| **F** | Format | Required output shape (headings, bullet syntax, sections). |
| **T** | Tone | Voice and restraint (clinical, neutral, conservative). |

## Supporting techniques

- **Negative constraints**: explicit "never invent X" statements bound fabrication risk, especially in generation tasks (writer, resume builder).
- **Few-shot grounding**: correct vs. incorrect output forms are shown so the model learns the exact bullet syntax.
- **Input isolation**: analysts receive only profiles (never raw resumes) to prevent cross-document leakage.
- **Fail-fast parsing**: `_parse_match_score` rejects missing or malformed `SCORE:` values; `_renumber_loose_questions` recovers bare question lines into a numbered list.

## Prompt files

| File | Agent | Use |
|---|---|---|
| `resume_profile.md` | Resume Evidence Analyst | Factual resume profile (Skills / Experience / Tools / Verified Achievements). |
| `job_profile.md` | Job Requirements Analyst | Factual job profile (Must-Have / Preferred / Seniority / Keywords). |
| `gap_analysis.md` | Resume Match Analyst | Strong matches / Evidence gaps / Interview risk areas. |
| `writer.md` | Grounded Resume Writer | Tailored bullets + Interview Prep Guide. |
| `scorer.md` | Resume Match Scorer | Single 0–100 score + one-sentence note. |
| `resume_builder.md` | Resume Writer | Grounded, tailored resume draft. |

## Editing prompts
1. Edit the `.md` file in `src/resume_crew/prompts/`.
2. Keep CRAFT structure + negative constraints + few-shot grounding.
3. Update `docs/`, `CHANGELOG.md`, and add tests if behavior changes.
4. Run `make test` and `make lint` before opening a PR.
