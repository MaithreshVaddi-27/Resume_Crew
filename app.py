"""Gradio web interface for Resume Matcher with optional ngrok live sharing."""

from __future__ import annotations

import os
import queue
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Make the package importable when running app.py directly from the project root.
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Disable CrewAI telemetry before any import of crewai touches the env.
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

import gradio as gr

from resume_crew.document_reader import SUPPORTED_DOCUMENT_EXTENSIONS, extract_text
from resume_crew.scoring import format_keyword_score, keyword_match_score
from resume_crew.storage import create_run_directory

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
/* ── Base ──────────────────────────────────────────────────────────────── */
:root {
    --bg-deep:    #0a0a14;
    --bg-card:    #12121f;
    --bg-raised:  #1a1a2e;
    --border:     #2a2a45;
    --accent:     #7c3aed;
    --accent-2:   #2563eb;
    --text:       #e2e8f0;
    --muted:      #94a3b8;
    --success:    #10b981;
    --warning:    #f59e0b;
    --danger:     #ef4444;
    --radius:     12px;
}

body, .gradio-container {
    background: var(--bg-deep) !important;
    color: var(--text) !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
}

/* ── Header ─────────────────────────────────────────────────────────────── */
#app-header {
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
    border-radius: var(--radius);
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(124,58,237,0.3);
}
#app-header h1 {
    font-size: 2rem;
    font-weight: 800;
    color: #fff !important;
    margin: 0 0 6px 0;
}
#app-header p {
    color: rgba(255,255,255,0.8) !important;
    margin: 0;
    font-size: 0.95rem;
}

/* ── Cards / Panels ──────────────────────────────────────────────────────── */
.panel-card {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
}

/* ── Inputs ──────────────────────────────────────────────────────────────── */
.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    background: var(--bg-raised) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
}
.gradio-container label span {
    color: var(--muted) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
#analyze-btn {
    background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.4) !important;
    transition: transform 0.15s, box-shadow 0.15s !important;
    cursor: pointer !important;
}
#analyze-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(124,58,237,0.55) !important;
}
#rank-btn {
    background: linear-gradient(135deg, #0891b2, #0e7490) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    box-shadow: 0 4px 20px rgba(8,145,178,0.35) !important;
    transition: transform 0.15s !important;
}
#rank-btn:hover { transform: translateY(-2px) !important; }

/* ── Progress box ─────────────────────────────────────────────────────────── */
#progress-box textarea {
    background: #0d0d1a !important;
    border: 1px solid var(--border) !important;
    color: #a5f3fc !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.85rem !important;
}

/* ── Score banner ─────────────────────────────────────────────────────────── */
#score-display {
    background: linear-gradient(135deg, var(--bg-raised), var(--bg-card)) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 20px 28px !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.gradio-container .tabs {
    border: none !important;
}
.gradio-container .tab-nav button {
    background: var(--bg-raised) !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px 8px 0 0 !important;
    font-weight: 600 !important;
    transition: background 0.15s, color 0.15s !important;
}
.gradio-container .tab-nav button.selected {
    background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
    color: #fff !important;
    border-color: transparent !important;
}

/* ── Markdown output ──────────────────────────────────────────────────────── */
.gradio-container .prose,
.gradio-container .markdown-body {
    color: var(--text) !important;
    background: transparent !important;
}
.gradio-container .prose h1,
.gradio-container .prose h2,
.gradio-container .prose h3 {
    color: #c4b5fd !important;
}
.gradio-container .prose strong { color: #a5b4fc !important; }
.gradio-container .prose code {
    background: var(--bg-raised) !important;
    color: #86efac !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
}
.gradio-container .prose table {
    border-collapse: collapse !important;
    width: 100% !important;
}
.gradio-container .prose th {
    background: var(--bg-raised) !important;
    color: #c4b5fd !important;
    padding: 8px 12px !important;
    border: 1px solid var(--border) !important;
}
.gradio-container .prose td {
    padding: 8px 12px !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}

/* ── File upload zone ─────────────────────────────────────────────────────── */
.gradio-container .upload-container,
.gradio-container .file-preview {
    background: var(--bg-raised) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    transition: border-color 0.2s !important;
}
.gradio-container .upload-container:hover {
    border-color: var(--accent) !important;
}

/* ── Scrollbars ──────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
"""

# ---------------------------------------------------------------------------
# ngrok setup
# ---------------------------------------------------------------------------

def _setup_ngrok(port: int = 7860) -> str | None:
    """Connect an ngrok tunnel if NGROK_AUTHTOKEN is present in the environment."""
    token = os.getenv("NGROK_AUTHTOKEN", "").strip()
    if not token:
        return None
    try:
        from pyngrok import conf, ngrok
        conf.get_default().auth_token = token
        tunnel = ngrok.connect(port, "http")
        url = tunnel.public_url
        print(f"\n{'='*60}")
        print(f"  🌐  Live ngrok URL: {url}")
        print(f"{'='*60}\n")
        return url
    except ImportError:
        print("[app] pyngrok is not installed. Run: pip install pyngrok")
        return None
    except Exception as exc:
        print(f"[app] ngrok setup failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Analysis worker (runs on a background thread to avoid blocking Gradio)
# ---------------------------------------------------------------------------

def _run_analysis_thread(
    resume_path: str,
    job_path: str,
    provider: str,
    step_q: "queue.Queue[str | None]",
    result_q: "queue.Queue[tuple]",
) -> None:
    """Execute the full pipeline in a worker thread and push results to queues."""
    try:
        from resume_crew.pipeline import build_llm, build_report_files, first_meaningful_line, run_llm_analysis

        step_q.put("📄 Reading documents...")
        resume_text = extract_text(resume_path)
        job_text = extract_text(job_path)

        step_q.put("🔢 Computing keyword match score...")
        score = keyword_match_score(resume_text, job_text)

        candidate = first_meaningful_line(resume_text, "Candidate")
        job_title = first_meaningful_line(job_text, "Target Role")

        step_q.put(f"🤖 Connecting to {provider.title()} LLM...")
        llm, resolved_provider = build_llm(provider)
        step_q.put(f"✅ Connected via {resolved_provider.title()}. Starting 4-step analysis...")

        def on_step(msg: str) -> None:
            step_q.put(f"  {msg}")

        resume_profile, job_profile, gap_analysis, writer_output = run_llm_analysis(
            resume_text, job_text, llm, on_step=on_step,
        )

        step_q.put("💾 Assembling report files...")
        files = build_report_files(
            candidate, job_title, score,
            resume_profile, job_profile, gap_analysis, writer_output,
        )
        directory, timestamp = create_run_directory(candidate, job_title)
        for name, content in files.items():
            (directory / name).write_text(content, encoding="utf-8")

        step_q.put(f"✅ Done! Report saved to: {directory}")
        result_q.put(("ok", score, resume_profile, job_profile, gap_analysis,
                      writer_output, str(directory)))

    except Exception as exc:  # noqa: BLE001
        step_q.put(f"❌ Error: {exc}")
        result_q.put(("error", str(exc)))
    finally:
        step_q.put(None)  # Sentinel — signals the generator to stop polling.


# ---------------------------------------------------------------------------
# Gradio event handlers
# ---------------------------------------------------------------------------

EMPTY_TABS = ("", "", "", "", "", "")


def _get_file_path(file_obj) -> str:
    """Extract a real filesystem path from a Gradio file object (Gradio 4 or 5)."""
    if file_obj is None:
        return ""
    # Gradio 4: NamedString / TemporaryFileWrapper with .name attribute.
    if hasattr(file_obj, "name"):
        return str(file_obj.name)
    # Gradio 5+: plain string path.
    return str(file_obj)


def analyze_stream(resume_file, jd_file, provider):
    """Generator: streams progress to the UI while a background thread runs the pipeline."""
    resume_path = _get_file_path(resume_file)
    jd_path = _get_file_path(jd_file)
    if not resume_path or not jd_path:
        yield "⚠️ Please upload both a resume and a job description.", *EMPTY_TABS, ""
        return

    step_q: queue.Queue[str | None] = queue.Queue()
    result_q: queue.Queue[tuple] = queue.Queue()

    thread = threading.Thread(
        target=_run_analysis_thread,
        args=(resume_path, jd_path, provider, step_q, result_q),
        daemon=True,
    )
    thread.start()

    log_lines: list[str] = []

    # Stream progress messages until the thread signals completion.
    while True:
        try:
            msg = step_q.get(timeout=1.0)
            if msg is None:
                break
            log_lines.append(msg)
            yield "\n".join(log_lines), *EMPTY_TABS, ""
        except queue.Empty:
            # No new message yet — yield a heartbeat dot to show we're alive.
            yield "\n".join(log_lines) + "\n⏳ Working...", *EMPTY_TABS, ""

    # Retrieve final result and populate all output tabs.
    result = result_q.get()
    if result[0] == "error":
        yield f"❌ Analysis failed:\n\n{result[1]}", *EMPTY_TABS, ""
        return

    _, score, resume_profile, job_profile, gap_analysis, writer_output, report_dir = result

    # Build the per-tab content.
    score_md = format_keyword_score(score)
    score_pct = score.score

    # Construct a visual score gauge using Unicode blocks.
    filled = int(score_pct / 5)       # 0–20 blocks
    bar = "█" * filled + "░" * (20 - filled)
    color_label = (
        "🟢 Strong" if score_pct >= 65
        else "🟡 Moderate" if score_pct >= 35
        else "🔴 Low"
    )
    score_banner = (
        f"## 📊 Keyword Match Score\n\n"
        f"### `{score_pct}%` — {color_label}\n\n"
        f"`{bar}` {score_pct}/100\n\n"
        f"{score_md}\n\n"
        f"---\n*Report saved to `{report_dir}`*"
    )

    # Split writer output into bullets + interview sections.
    try:
        from resume_crew.pipeline import split_writer_output
        bullets, interview = split_writer_output(writer_output)
    except ValueError:
        bullets = writer_output
        interview = ""

    match_report = (
        f"# Resume Match Report\n\n"
        f"{score_banner}\n\n---\n\n"
        f"## Resume Profile\n\n{resume_profile}\n\n---\n\n"
        f"## Job Description Profile\n\n{job_profile}\n\n---\n\n"
        f"## Skills Gap Analysis\n\n{gap_analysis}\n\n---\n\n"
        f"## Tailored Resume Bullets\n\n{bullets}\n\n---\n\n"
        f"## Interview Preparation\n\n{interview}"
    )

    yield (
        "\n".join(log_lines),   # progress log
        score_banner,           # score tab
        resume_profile,         # resume profile tab
        job_profile,            # job profile tab
        gap_analysis,           # gap analysis tab
        bullets,                # resume bullets tab
        interview,              # interview prep tab
        match_report,           # full match report tab
    )


def rank_resumes_fn(directory_path: str, jd_file, provider: str):
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
            yield f"❌ `{source}` is not a directory."
            return

        paths = sorted(
            p for p in source.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS
        )
        if not paths:
            yield "No supported resume files found in that directory."
            return

        from resume_crew.pipeline import build_llm, run_llm_match_score

        yield f"🤖 Connecting to {provider.title()} LLM..."
        llm, resolved_provider = build_llm(provider)

        results: list[tuple[str, float | None, str]] = []
        for idx, path in enumerate(paths, 1):
            yield (
                f"✅ Connected via {resolved_provider.title()}.\n"
                f"📄 Scoring {idx}/{len(paths)}: {path.name}..."
            )
            try:
                resume_text = extract_text(str(path))
                score, note = run_llm_match_score(resume_text, job_text, llm)
                results.append((path.name, score, note))
            except Exception as exc:
                results.append((path.name, None, str(exc) or "(unknown error)"))

        results.sort(key=lambda item: (item[1] is None, -(item[1] or 0)))

        lines = ["| Rank | Resume | Score | Notes |", "|---:|---|---:|---|"]
        for idx, (name, score, note) in enumerate(results, 1):
            score_str = "--" if score is None else f"{score:.0f}%"
            safe_note = (note or "").replace("|", chr(92) + "|")
            lines.append(f"| {idx} | {name.replace('|', chr(92)+'|')} | {score_str} | {safe_note} |")

        yield "# Resume Ranking\n\n" + "\n".join(lines)
    except Exception as exc:
        yield f"❌ {exc}"


# ---------------------------------------------------------------------------
# UI layout
# ---------------------------------------------------------------------------

PROVIDER_CHOICES = ["auto", "gemini", "ollama"]
# Single source of truth — stays in sync with document_reader.py automatically.
ACCEPTED_TYPES = list(SUPPORTED_DOCUMENT_EXTENSIONS)

# Gradio 6 moved `theme`/`css` from the Blocks() constructor to launch();
# passing them to Blocks() there is silently dropped (only a console warning),
# which would make the whole custom dark theme vanish on a fresh install.
# Detect the installed major version and route the params to wherever that
# version actually applies them, so styling never silently disappears.
_GRADIO_MAJOR = int(gr.__version__.split(".")[0]) if gr.__version__[:1].isdigit() else 4
_BLOCKS_STYLE_KWARGS: dict = {}
_LAUNCH_STYLE_KWARGS: dict = {}
if _GRADIO_MAJOR >= 6:
    _LAUNCH_STYLE_KWARGS = {"theme": gr.themes.Base(), "css": CUSTOM_CSS}
else:
    _BLOCKS_STYLE_KWARGS = {"theme": gr.themes.Base(), "css": CUSTOM_CSS}

with gr.Blocks(
    title="Resume Matcher",
    analytics_enabled=False,
    **_BLOCKS_STYLE_KWARGS,
) as demo:

    # ── Header ────────────────────────────────────────────────────────────
    gr.HTML("""
    <div id="app-header">
        <h1>🎯 Resume Matcher</h1>
        <p>Grounded, evidence-based resume &amp; job description analysis powered by AI</p>
    </div>
    """)

    with gr.Tabs():

        # ── Tab 1: Analyze ─────────────────────────────────────────────────
        with gr.Tab("✨ Analyze Resume"):

            with gr.Row():
                with gr.Column(scale=1):
                    resume_input = gr.File(
                        label="Resume",
                        file_types=ACCEPTED_TYPES,
                        elem_id="resume-upload",
                    )
                with gr.Column(scale=1):
                    jd_input = gr.File(
                        label="Job Description",
                        file_types=ACCEPTED_TYPES,
                        elem_id="jd-upload",
                    )

            with gr.Row():
                provider_dd = gr.Dropdown(
                    choices=PROVIDER_CHOICES,
                    value=os.getenv("LLM_PROVIDER", "auto"),
                    label="LLM Provider",
                    info="'auto' uses local Ollama if running, then Gemini",
                    scale=1,
                )
                analyze_btn = gr.Button(
                    "🚀 Analyze",
                    elem_id="analyze-btn",
                    scale=2,
                    variant="primary",
                )

            progress_box = gr.Textbox(
                label="Progress",
                lines=5,
                max_lines=12,
                interactive=False,
                elem_id="progress-box",
                placeholder="Progress will appear here once analysis starts...",
            )

            # ── Results ───────────────────────────────────────────────────
            with gr.Tabs():
                with gr.Tab("📊 Score"):
                    score_out = gr.Markdown(elem_id="score-display")
                with gr.Tab("📝 Resume Profile"):
                    resume_profile_out = gr.Markdown()
                with gr.Tab("💼 Job Profile"):
                    job_profile_out = gr.Markdown()
                with gr.Tab("🔍 Gap Analysis"):
                    gap_out = gr.Markdown()
                with gr.Tab("✏️ Resume Bullets"):
                    bullets_out = gr.Markdown()
                with gr.Tab("🎤 Interview Prep"):
                    interview_out = gr.Markdown()
                with gr.Tab("📄 Full Report"):
                    report_out = gr.Markdown()

            analyze_btn.click(
                fn=analyze_stream,
                inputs=[resume_input, jd_input, provider_dd],
                outputs=[
                    progress_box,
                    score_out,
                    resume_profile_out,
                    job_profile_out,
                    gap_out,
                    bullets_out,
                    interview_out,
                    report_out,
                ],
            )

        # ── Tab 2: Rank Resumes ────────────────────────────────────────────
        with gr.Tab("📈 Rank Resumes"):

            gr.Markdown(
                "Score every resume in a folder against a job description **using the LLM**. "
                "Each resume gets its own scoring call, so this can take a while for large folders."
            )

            with gr.Row():
                with gr.Column(scale=2):
                    dir_input = gr.Textbox(
                        label="Resume Folder Path",
                        placeholder="e.g. C:\\Users\\you\\Resumes  or  ./samples/Resumes",
                        elem_id="dir-input",
                    )
                with gr.Column(scale=1):
                    rank_jd_input = gr.File(
                        label="Job Description",
                        file_types=ACCEPTED_TYPES,
                    )

            rank_provider_dd = gr.Dropdown(
                choices=PROVIDER_CHOICES,
                value=os.getenv("LLM_PROVIDER", "auto"),
                label="LLM Provider",
                info="'auto' uses local Ollama if running, then Gemini",
            )

            rank_btn = gr.Button("📊 Rank Resumes", elem_id="rank-btn", variant="secondary")
            rank_out = gr.Markdown(label="Ranking Results")

            rank_btn.click(
                fn=rank_resumes_fn,
                inputs=[dir_input, rank_jd_input, rank_provider_dd],
                outputs=rank_out,
            )

        # ── Tab 3: Hardware Info ───────────────────────────────────────────
        with gr.Tab("🖥️ Hardware"):

            gr.Markdown("Detects your GPU, memory, and recommends an Ollama compute profile.")

            hw_btn = gr.Button("🔍 Detect Hardware", variant="secondary")
            hw_out = gr.Markdown()

            def _check_hw():
                from resume_crew.hardware import (
                    ollama_is_running, resolve_ollama_profile,
                )
                profile = resolve_ollama_profile("auto")
                hw = profile["hardware"]
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                ollama_status = "🟢 Reachable" if ollama_is_running(base_url) else "🔴 Not reachable"
                return (
                    f"## Hardware Detection\n\n"
                    f"| Property | Value |\n|---|---|\n"
                    f"| CUDA | {'✅ Available — ' + str(hw.get('cuda_name', '')) if hw['cuda'] else '❌ Not found'} |\n"
                    f"| CUDA VRAM | {hw.get('cuda_vram_gb') or 'N/A'} GB |\n"
                    f"| Apple Metal | {'✅ Available' if hw['mps'] else '❌ Not found'} |\n"
                    f"| CPU threads | {hw['cpu_threads']} |\n"
                    f"| System RAM | {hw.get('system_memory_gb') or 'Unknown'} GB |\n"
                    f"| Ollama server | {ollama_status} |\n\n"
                    f"**Recommended profile:** `{profile['name'].upper()}`  "
                    f"— Context window: `{profile['context']} tokens`"
                )

            hw_btn.click(fn=_check_hw, inputs=[], outputs=hw_out)

    # ── Footer ─────────────────────────────────────────────────────────────
    gr.HTML("""
    <div style="text-align:center;padding:20px 0 8px;color:#475569;font-size:0.8rem;">
        Resume Matcher v1.0.0 — grounded, local-first AI analysis.
        Keyword scores are not ATS simulations or hiring recommendations.
    </div>
    """)


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    PORT = int(os.getenv("GRADIO_PORT", "7860"))

    # Try ngrok first; fall back to Gradio's built-in sharing if no authtoken.
    ngrok_url = _setup_ngrok(PORT)
    use_share = (ngrok_url is None) and os.getenv("GRADIO_SHARE", "false").lower() == "true"

    print(f"\n🎯 Resume Matcher UI starting at http://localhost:{PORT}")
    if not ngrok_url:
        print("   (Set NGROK_AUTHTOKEN in .env for a live public URL)")

    demo.launch(
        server_port=PORT,
        share=use_share,
        show_error=True,
        inbrowser=True,
        **_LAUNCH_STYLE_KWARGS,
    )
