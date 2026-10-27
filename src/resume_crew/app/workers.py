"""Background workers and analysis functions for the Gradio UI.

Extracted from the monolithic ``app.py`` so the UI layout stays thin and the
long-running LLM pipeline logic lives in one place.
"""

from __future__ import annotations

import io
import logging
import queue
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

import gradio as gr  # noqa: E402

logger = logging.getLogger(__name__)

from resume_crew.config import MAX_EXTRACTED_CHARACTERS, load_settings  # noqa: E402
from resume_crew.document_reader import (  # noqa: E402
    SUPPORTED_DOCUMENT_EXTENSIONS,
    extract_text,
)
from resume_crew.hardware import list_ollama_models  # noqa: E402
from resume_crew.pipeline import (  # noqa: E402
    AnalysisCancelled,
    build_docx_report,
    build_llm,
    build_pdf_report,
    build_report_files,
    first_meaningful_line,
    format_resume_ranking,
    run_llm_analysis,
    run_llm_match_score,
    score_resume_path,
)
from resume_crew.scoring import (  # noqa: E402
    format_keyword_score,
    highlight_resume_matches,
    keyword_match_score,
)
from resume_crew.storage import (  # noqa: E402
    list_report_runs,
    read_run_report,
    write_run_files,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


# ponytail: one global analysis lock keeps the UI state consistent; use per-user
# job isolation only if concurrent multi-user hosting becomes a requirement.
_analysis_lock = threading.Lock()


def local_model_choices() -> tuple[list[str], str]:
    """Return installed local models, falling back to the configured Ollama model."""
    settings = load_settings()
    models = list_ollama_models(settings.ollama_base_url, settings.ollama_timeout)
    if settings.ollama_model not in models:
        models.insert(0, settings.ollama_model)
    return models, settings.ollama_model


def refresh_local_models(current: str | None) -> Any:
    """Refresh the model dropdown, preserving a still-installed selection."""
    models, default_model = local_model_choices()
    selected = current if current in models else default_model
    return gr.update(choices=models, value=selected)


EMPTY_TABS = (
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    None,
    None,
)  # score..interview, report, highlight, pdf, docx


def _get_file_path(file_obj: Any) -> str:
    """Extract a real filesystem path from a Gradio file object (Gradio 4 or 5)."""
    if file_obj is None:
        return ""
    if hasattr(file_obj, "name"):
        return str(file_obj.name)
    return str(file_obj)


def split_writer_output_safe(writer_output: str) -> tuple[str, str]:
    try:
        from resume_crew.pipeline import split_writer_output

        return split_writer_output(writer_output)
    except ValueError:
        return writer_output, ""


def _user_error(message: str, exc: Exception) -> str:
    """Log details server-side while keeping local paths and provider internals out of the UI."""
    logger.exception("%s: %s", message, exc)
    return f"❌ {message}. Check the inputs and provider settings, then try again."


# ---------------------------------------------------------------------------
# Analysis worker (runs on a background thread to avoid blocking Gradio)
# ---------------------------------------------------------------------------


def _list_resume_files(source: Path) -> list[Path]:
    """Return supported resume files in a directory, sorted by name."""
    return sorted(
        p
        for p in source.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
    )


def _run_analysis_thread(
    resume_path: str,
    job_path: str,
    provider: str,
    model: str,
    gemini_model: str,
    step_q: queue.Queue[str | None],
    result_q: queue.Queue[tuple[Any, ...]],
    cancel_event: threading.Event,
) -> None:
    """Execute the full pipeline in a worker thread and push results to queues."""
    try:
        step_q.put("📄 Reading documents...")
        resume_text = extract_text(resume_path)
        job_text = extract_text(job_path)

        step_q.put("🔢 Computing keyword match score...")
        score = keyword_match_score(resume_text, job_text)

        candidate = first_meaningful_line(resume_text, "Candidate")
        job_title = first_meaningful_line(job_text, "Target Role")

        step_q.put(f"🤖 Connecting to {provider.title()} LLM...")
        llm, resolved_provider = build_llm(provider, model, gemini_model)
        step_q.put(f"✅ Connected via {resolved_provider.title()}. Starting 4-step analysis...")

        def on_step(msg: str) -> None:
            if cancel_event.is_set():
                raise AnalysisCancelled("Analysis cancelled by user.")
            step_q.put(f"  {msg}")

        resume_profile, job_profile, gap_analysis, writer_output = run_llm_analysis(
            resume_text,
            job_text,
            llm,
            on_step=on_step,
        )
        if cancel_event.is_set():
            raise AnalysisCancelled("Analysis cancelled by user.")

        step_q.put("💾 Assembling report files...")
        files = build_report_files(
            candidate,
            job_title,
            score,
            resume_profile,
            job_profile,
            gap_analysis,
            writer_output,
        )
        if cancel_event.is_set():
            raise AnalysisCancelled("Analysis cancelled by user.")
        directory, _timestamp = write_run_files(candidate, job_title, files, score=score.score)

        step_q.put("✅ Done! Report saved locally and is ready to review.")
        result_q.put(
            (
                "ok",
                score,
                resume_profile,
                job_profile,
                gap_analysis,
                writer_output,
                str(directory),
                files,
                resume_text,
                candidate,
                job_title,
            )
        )

    except AnalysisCancelled as exc:
        step_q.put(f"🛑 {exc}")
        result_q.put(("cancelled", str(exc)))
    except Exception as exc:  # noqa: BLE001
        message = _user_error("Analysis could not be completed", exc)
        step_q.put(message)
        result_q.put(("error", message))
    finally:
        _analysis_lock.release()
        step_q.put(None)  # Sentinel — signals the generator to stop polling.


def analyze_stream(
    resume_file: Any,
    jd_file: Any,
    provider: str,
    model: str = "",
    gemini_model: str = "",
    cancel_event_state: Any = None,
) -> Iterator[Any]:
    """Generator: streams progress to the UI while a background thread runs the pipeline."""
    resume_path = _get_file_path(resume_file)
    jd_path = _get_file_path(jd_file)
    if not resume_path or not jd_path:
        yield (
            "⚠️ Please upload both a resume and a job description.",
            *EMPTY_TABS,
            cancel_event_state,
        )
        return

    if not _analysis_lock.acquire(blocking=False):
        yield (
            "⚠️ An analysis is already running. Wait for it to finish or cancel it first.",
            *EMPTY_TABS,
            cancel_event_state,
        )
        return

    cancel_event = threading.Event()
    step_q: queue.Queue[str | None] = queue.Queue()
    result_q: queue.Queue[tuple[Any, ...]] = queue.Queue()

    thread = threading.Thread(
        target=_run_analysis_thread,
        args=(
            resume_path,
            jd_path,
            provider,
            model or "",
            gemini_model or "",
            step_q,
            result_q,
            cancel_event,
        ),
        daemon=True,
    )
    thread.start()

    log_lines: list[str] = []

    while True:
        try:
            msg = step_q.get(timeout=1.0)
            if msg is None:
                break
            log_lines.append(msg)
            yield "\n".join(log_lines), *EMPTY_TABS, cancel_event
        except queue.Empty:
            yield "\n".join(log_lines) + "\n⏳ Working...", *EMPTY_TABS, cancel_event

    result = result_q.get()
    if result[0] == "cancelled":
        yield f"🛑 {result[1]}", *EMPTY_TABS, None
        return
    if result[0] == "error":
        yield str(result[1]), *EMPTY_TABS, None
        return

    (
        _,
        score,
        resume_profile,
        job_profile,
        gap_analysis,
        writer_output,
        _report_dir,
        files,
        resume_text,
        candidate,
        job_title,
    ) = result

    score_md = format_keyword_score(score)
    score_pct = score.score

    filled = int(score_pct / 5)
    bar = "█" * filled + "░" * (20 - filled)
    color_label = "🟢 Strong" if score_pct >= 65 else "🟡 Moderate" if score_pct >= 35 else "🔴 Low"
    score_banner = (
        f"## 📊 Keyword Match Score\n\n"
        f"### `{score_pct}%` — {color_label}\n\n"
        f"`{bar}` {score_pct}/100\n\n"
        f"{score_md}\n\n"
        f"---\n*Report saved locally and available in the Full report tab.*"
    )

    bullets, interview = split_writer_output_safe(writer_output)
    match_report = files["match_report.md"]
    highlight_html = highlight_resume_matches(resume_text, score)

    pdf_path = None
    docx_path = None
    try:
        pdf_bytes = build_pdf_report(files, candidate, job_title)
        pdf_path = str(Path(_report_dir) / "match_report.pdf")
        Path(pdf_path).write_bytes(pdf_bytes)
    except Exception:  # noqa: BLE001
        logger.exception("PDF export failed")
        log_lines.append("⚠️ PDF export was unavailable for this report.")

    try:
        docx_bytes = build_docx_report(files, candidate, job_title)
        docx_path = str(Path(_report_dir) / "match_report.docx")
        Path(docx_path).write_bytes(docx_bytes)
    except Exception:  # noqa: BLE001
        logger.exception("Word export failed")
        log_lines.append("⚠️ Word export was unavailable for this report.")

    yield (
        "\n".join(log_lines),
        score_banner,
        resume_profile,
        job_profile,
        gap_analysis,
        bullets,
        interview,
        match_report,
        highlight_html,
        pdf_path,
        docx_path,
        None,
    )


def cancel_analysis(cancel_event_state: threading.Event | None) -> str:
    """Signal the running analysis thread to stop at its next checkpoint."""
    if cancel_event_state is not None:
        cancel_event_state.set()
    return "🛑 Cancelling — this finishes after the current step..."


# ---------------------------------------------------------------------------
# Rank resumes
# ---------------------------------------------------------------------------


def rank_resumes_fn(
    directory_path: str,
    jd_file: Any,
    provider: str,
    model: str = "",
    gemini_model: str = "",
) -> Iterator[Any]:
    """Rank all resumes in a folder against a job description using the LLM."""
    if not directory_path or not directory_path.strip():
        yield "⚠️ Please enter a folder path containing resume files."
        return
    if jd_file is None:
        yield "⚠️ Please upload a job description file."
        return

    try:
        jd_path = _get_file_path(jd_file)
        job_text = extract_text(jd_path)
        source = Path(directory_path.strip()).expanduser().resolve()
        if not source.is_dir():
            yield "❌ The selected folder is not available on the machine running Resume_Crew."
            return

        paths = _list_resume_files(source)
        if not paths:
            yield "No supported resume files found in that directory."
            return

        llm, resolved_provider = build_llm(provider, model, gemini_model)

        yield f"🤖 Connecting to {resolved_provider.title()} LLM..."

        results = []
        for idx, path in enumerate(paths, 1):
            yield (
                f"✅ Connected via {resolved_provider.title()}.\n"
                f"📄 Scoring {idx}/{len(paths)}: {path.name}..."
            )
            results.append(score_resume_path(path, job_text, llm))
        yield format_resume_ranking(results)
    except Exception as exc:  # noqa: BLE001
        yield _user_error("Resume ranking could not be completed", exc)


# ---------------------------------------------------------------------------
# Batch analyze
# ---------------------------------------------------------------------------


def batch_analyze_fn(
    directory_path: str,
    jd_file: Any,
    provider: str,
    model: str = "",
    gemini_model: str = "",
) -> Iterator[Any]:
    """Run the FULL 4-step analysis for every resume in a folder against one JD."""
    if not directory_path or not directory_path.strip():
        yield "⚠️ Please enter a folder path containing resume files."
        return
    if jd_file is None:
        yield "⚠️ Please upload a job description file."
        return

    try:
        jd_path = _get_file_path(jd_file)
        job_text = extract_text(jd_path)
        source = Path(directory_path.strip()).expanduser().resolve()
        if not source.is_dir():
            yield "❌ The selected folder is not available on the machine running Resume_Crew."
            return

        paths = _list_resume_files(source)
        if not paths:
            yield "No supported resume files found in that directory."
            return

        llm, resolved_provider = build_llm(provider, model, gemini_model)
        job_title = first_meaningful_line(job_text, "Target Role")

        results: list[tuple[str, float | None, str]] = []
        log_lines = [f"✅ Connected via {resolved_provider.title()}."]
        for idx, path in enumerate(paths, 1):
            log_lines.append(f"📄 Full analysis {idx}/{len(paths)}: {path.name}...")
            yield "\n".join(log_lines)
            try:
                resume_text = extract_text(str(path))
                score = keyword_match_score(resume_text, job_text)
                candidate = first_meaningful_line(resume_text, path.stem)

                resume_profile, job_profile, gap_analysis, writer_output = run_llm_analysis(
                    resume_text,
                    job_text,
                    llm,
                )
                files = build_report_files(
                    candidate,
                    job_title,
                    score,
                    resume_profile,
                    job_profile,
                    gap_analysis,
                    writer_output,
                )
                directory, _timestamp = write_run_files(
                    candidate, job_title, files, score=score.score
                )

                results.append((path.name, score.score, "Saved locally"))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Batch analysis failed for %s: %s", path.name, exc)
                results.append((path.name, None, "Analysis failed — check the server log."))

        results.sort(key=lambda item: (item[1] is None, -(item[1] or 0)))
        lines = ["| Rank | Resume | Score | Status |", "|---:|---|---:|---|"]
        for idx, (name, score_val, note) in enumerate(results, 1):
            score_str = "--" if score_val is None else f"{score_val:.0f}%"
            safe_name = name.replace("|", chr(92) + "|")
            safe_note = note.replace("|", chr(92) + "|")
            lines.append(f"| {idx} | {safe_name} | {score_str} | {safe_note} |")

        log_lines.append("✅ Batch analysis complete.")
        yield "\n".join(log_lines) + "\n\n# Batch Analysis Results\n\n" + "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        yield _user_error("Batch analysis could not be completed", exc)


# ---------------------------------------------------------------------------
# Compare job descriptions
# ---------------------------------------------------------------------------


def compare_jds_fn(
    resume_file: Any,
    jd_files: list[Any],
    provider: str,
    model: str = "",
    gemini_model: str = "",
) -> Iterator[Any]:
    """Score one resume against several job descriptions to see which fits best."""
    resume_path = _get_file_path(resume_file)
    if not resume_path:
        yield "⚠️ Please upload a resume."
        return
    if not jd_files:
        yield "⚠️ Please upload one or more job description files."
        return

    try:
        resume_text = extract_text(resume_path)

        llm, resolved_provider = build_llm(provider, model, gemini_model)

        yield f"🤖 Connecting to {resolved_provider.title()} LLM..."

        jd_paths = [_get_file_path(f) for f in jd_files]
        results: list[tuple[str, float | None, str]] = []
        for idx, jd_path in enumerate(jd_paths, 1):
            name = Path(jd_path).name
            yield (
                f"✅ Connected via {resolved_provider.title()}.\n"
                f"📄 Scoring {idx}/{len(jd_paths)}: {name}..."
            )
            try:
                job_text = extract_text(jd_path)
                score, note = run_llm_match_score(resume_text, job_text, llm)
                results.append((name, score, note))
            except Exception as exc:  # noqa: BLE001
                results.append((name, None, _user_error("Job description scoring failed", exc)))

        results.sort(key=lambda item: (item[1] is None, -(item[1] or 0)))
        lines = ["| Rank | Job Description | Score | Notes |", "|---:|---|---:|---|"]
        for idx, (name, score, note) in enumerate(results, 1):  # type: ignore[assignment]
            score_str = "--" if score is None else f"{score:.0f}%"
            safe_note = (note or "").replace("|", chr(92) + "|")
            lines.append(
                f"| {idx} | {name.replace('|', chr(92) + '|')} | {score_str} | {safe_note} |"
            )

        yield "# Job Description Comparison\n\n" + "\n".join(lines)
    except Exception as exc:  # noqa: BLE001
        yield _user_error("Job comparison could not be completed", exc)


# ---------------------------------------------------------------------------
# Build resume
# ---------------------------------------------------------------------------


def build_resume_fn(
    resume_file: Any,
    notes_text: str,
    jd_file: Any,
    provider: str,
    model: str = "",
    gemini_model: str = "",
) -> Iterator[tuple[str, str, str, str | None, str | None]]:
    """Draft a tailored resume from the candidate's own material + a target JD.

    Yields (progress_markdown, resume_markdown, score_markdown, pdf_path, docx_path).
    """
    empty = ("", "", None, None)

    resume_path = _get_file_path(resume_file)
    notes = (notes_text or "").strip()
    if not resume_path and not notes:
        yield "⚠️ Upload an existing resume, add background notes, or both.", *empty
        return
    jd_path = _get_file_path(jd_file)
    if not jd_path:
        yield "⚠️ Please upload a target job description.", *empty
        return

    try:
        source_parts = []
        if resume_path:
            source_parts.append(extract_text(resume_path))
        if notes:
            source_parts.append(notes)
        source_text = "\n\n".join(source_parts)
        if len(source_text) > MAX_EXTRACTED_CHARACTERS:
            yield (
                f"⚠️ Resume and notes exceed the {MAX_EXTRACTED_CHARACTERS:,}-character limit. "
                "Shorten the source material and try again.",
                "",
                "",
                None,
                None,
            )
            return
        job_text = extract_text(jd_path)

        from resume_crew.pipeline import (  # noqa: PLC0415
            build_llm,
            first_meaningful_line,
            markdown_to_docx,
            markdown_to_pdf,
            run_resume_builder,
        )

        yield f"🤖 Connecting to {provider.title()} LLM...", "", "", None, None
        llm, resolved_provider = build_llm(provider, model, gemini_model)
        yield (
            f"✅ Connected via {resolved_provider.title()}. Drafting tailored resume...",
            "",
            "",
            None,
            None,
        )

        resume_md = run_resume_builder(source_text, job_text, llm)

        score = keyword_match_score(resume_md, job_text)
        score_md = format_keyword_score(score)

        candidate = first_meaningful_line(source_text, "Candidate")
        job_title = first_meaningful_line(job_text, "Target Role")

        directory, _timestamp = write_run_files(
            candidate,
            f"{job_title} (drafted resume)",
            {"generated_resume.md": resume_md},
            score=score.score,
        )

        pdf_path = None
        docx_path = None
        try:
            title = f"Resume — {candidate} — tailored for {job_title}"
            pdf_bytes = markdown_to_pdf(resume_md, title)
            pdf_path = str(directory / "generated_resume.pdf")
            Path(pdf_path).write_bytes(pdf_bytes)

            doc = markdown_to_docx(resume_md, title)
            buf = io.BytesIO()
            doc.save(buf)
            docx_path = str(directory / "generated_resume.docx")
            Path(docx_path).write_bytes(buf.getvalue())
        except Exception as exc:  # noqa: BLE001
            logger.exception("Resume export failed: %s", exc)
            resume_md += "\n\n---\n*⚠️ PDF/Word export was unavailable for this draft.*"

        yield (
            "✅ Draft ready — the resume and available exports are ready to review.",
            resume_md,
            score_md,
            pdf_path,
            docx_path,
        )
    except Exception as exc:  # noqa: BLE001
        yield _user_error("Resume drafting could not be completed", exc), "", "", None, None


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def refresh_history_fn() -> tuple[Any, str, Any, str]:
    """List past runs with a chart and a text summary of every score."""
    runs = list_report_runs()
    if not runs:
        return (
            gr.Dropdown(choices=[], value=None),
            "No past runs found yet — analyze a resume first.",
            None,
            "",
        )

    choices = [
        (
            f"{r.get('timestamp', '?')} — {r.get('candidate', '?')} vs {r.get('job_title', '?')} "
            f"({r.get('score', 0):.0f}%)",
            r["path"],
        )
        for r in runs
    ]

    summary = "\n".join(
        f"- **{r.get('timestamp', '?')}** — {r.get('candidate', '?')} vs "
        f"{r.get('job_title', '?')}: **{r.get('score', 0):.0f}%**"
        for r in runs
    )
    fig = None
    chart_status = ""
    try:
        import matplotlib  # noqa: PLC0415

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: PLC0415

        chrono = list(reversed(runs))
        x = list(range(1, len(chrono) + 1))
        y = [r.get("score", 0) for r in chrono]
        labels = [str(r.get("candidate", "?"))[:12] for r in chrono]

        bg, card, grid, text, accent = "#111318", "#191c22", "#3b404a", "#f0f1f3", "#83b5ed"
        fig, ax = plt.subplots(figsize=(7, 3))
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(card)
        ax.plot(x, y, marker="o", color=accent, linewidth=2)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Keyword match score (%)", color=text)
        ax.set_title("Score trend across past runs", color=text)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8, color=text)
        ax.tick_params(axis="y", colors=text)
        ax.grid(color=grid, linewidth=0.6, alpha=0.6)
        for spine in ax.spines.values():
            spine.set_color(grid)
        fig.tight_layout()
    except Exception:
        chart_status = "_Trend chart unavailable; the score summary below is still current._"

    status = f"Found {len(runs)} past run(s)."
    if chart_status:
        status += f" {chart_status}"
    return gr.Dropdown(choices=choices, value=choices[0][1]), status, fig, summary


def load_history_run_fn(selected_path: str) -> tuple[str, str, str, str, str]:
    """Load a previously saved report back into the History tab's Markdown panes."""
    if not selected_path:
        return "", "", "", "", ""
    try:
        files = read_run_report(selected_path)
        return (
            files.get("skills_gap_analysis.md", "_(not found)_"),
            files.get("resume_profile.md", "_(not found)_"),
            files.get("job_description_profile.md", "_(not found)_"),
            files.get("tailored_resume_bullets.md", "_(not found)_"),
            files.get("interview_preparation.md", "_(not found)_"),
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        return f"⚠️ {exc}", "", "", "", ""
