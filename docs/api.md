# API Reference

Resume Crew is a Python package. Public surface below.

## `resume_crew.config`

`Settings.from_env() -> Settings`
: Build validated runtime settings from environment variables.

`load_settings() -> Settings`
: Public entry point returning a `Settings` instance.

`resume_crew.config.OUTPUT_ROOT` (`Path`)
: The application output directory (`output/` within the project).

## `resume_crew.document_reader`

`extract_text(file_path: str) -> str`
: Extract validated text from a PDF, DOCX, TXT, or Markdown file. Raises `ValueError`/`FileNotFoundError` on invalid input.

`SUPPORTED_DOCUMENT_EXTENSIONS` (`tuple[str, ...]`)
: `(".pdf", ".docx", ".txt", ".md")`

## `resume_crew.scoring`

`keyword_match_score(resume_text, job_description_text) -> KeywordMatch`
: Whole-term keyword overlap score. Returns `KeywordMatch(score, matched, missing, total_keywords)`.

`highlight_resume_matches(resume_text, match) -> str`
: HTML with matched keywords wrapped in `<mark>`.

`format_keyword_score(match) -> str`
: Human-readable score summary with matched/missing chips.

## `resume_crew.pipeline`

`build_llm(provider: str | None = None) -> tuple[LLM, str]`
: Select MLX-LM, Ollama, or Gemini based on the configured provider.

`run_llm_analysis(resume_text, job_description_text, llm, on_step=None) -> tuple[str, str, str, str]`
: Run the 4-stage agent pipeline (resume profile, job profile, gap analysis, writer output).

`run_llm_match_score(resume_text, job_description_text, llm) -> tuple[float, str]`
: Lightweight single-call LLM score for ranking many resumes.

`run_resume_builder(source_text, job_description_text, llm) -> str`
: Draft a grounded, tailored resume using only source-material facts.

`build_report_files(candidate, job_title, score, resume_profile, job_profile, gap_analysis, writer_output) -> dict[str, str]`
: Assemble all report Markdown files.

`markdown_to_pdf(markdown_text, title) -> bytes` / `markdown_to_docx(markdown_text, title) -> Document`
: Export helpers.

`split_writer_output(text) -> tuple[str, str]`
: Split writer output into bullets and interview-prep sections.

## `resume_crew.storage`

`create_run_directory(candidate_name, job_title, output_dir=None) -> tuple[Path, str]`
: Create a uniquely-named run directory under `output/`.

`write_run_meta(directory, candidate, job_title, score, timestamp, published_name=None) -> None`
: Write `run_meta.json` sidecar. ``published_name`` records the final published run
  directory name (used when writes are staged under a temporary directory before
  being renamed into place).

`list_report_runs(limit=50) -> list[dict]`
: List past runs most-recent-first.

`read_run_report(directory) -> dict[str, str]`
: Rehydrate all Markdown files for a past run. The directory must be a direct child of `OUTPUT_ROOT`; traversal paths are rejected.

## `resume_crew.cli`

`main() -> None`
: CLI entry point. Flags: `--resume`, `--job-description`/`--jd`, `--provider`, `--output`/`-o`, `--rank-resumes`, `--check-hardware`, `--ollama-profile`, `--version`.
