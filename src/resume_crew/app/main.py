"""Gradio web interface for Resume_Crew with optional ngrok live sharing.

Layout and event wiring only. All long-running analysis logic lives in
:mod:`resume_crew.app.workers`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Make the package importable when running this module directly from the
# project root (``python src/resume_crew/app/main.py``).
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

# Disable CrewAI telemetry before any import of crewai touches the env.
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

import gradio as gr  # noqa: E402

from resume_crew.app import workers  # noqa: E402
from resume_crew.document_reader import SUPPORTED_DOCUMENT_EXTENSIONS  # noqa: E402

PROVIDER_CHOICES = ["auto", "ollama", "gemini"]
ACCEPTED_TYPES = list(SUPPORTED_DOCUMENT_EXTENSIONS)
LOCAL_MODELS, DEFAULT_LOCAL_MODEL = workers.local_model_choices()

_CSS_PATH = Path(__file__).resolve().parent / "styles.css"
_CUSTOM_CSS = _CSS_PATH.read_text(encoding="utf-8") if _CSS_PATH.is_file() else ""

# Gradio 6 moved theme/css from Blocks() constructor to launch(); detect the
# installed major version and route the params to wherever they apply.
_GRADIO_MAJOR = int(gr.__version__.split(".")[0]) if gr.__version__[:1].isdigit() else 4
_BLOCKS_STYLE_KWARGS: dict[str, Any] = {}
_LAUNCH_STYLE_KWARGS: dict[str, Any] = {}
if _GRADIO_MAJOR >= 6:
    _LAUNCH_STYLE_KWARGS = {"theme": gr.themes.Base(), "css": _CUSTOM_CSS}
else:
    _BLOCKS_STYLE_KWARGS = {"theme": gr.themes.Base(), "css": _CUSTOM_CSS}


def build_demo() -> gr.Blocks:
    with gr.Blocks(
        title="Resume_Crew",
        analytics_enabled=False,
        **_BLOCKS_STYLE_KWARGS,
    ) as demo:
        # ── Header ────────────────────────────────────────────────────────────
        gr.HTML("""
        <div id="app-header">
            <h1>🎯 Resume_Crew</h1>
            <p>Grounded, evidence-based resume &amp; job description analysis powered by AI</p>
        </div>
        """)

        with gr.Row(elem_classes=["model-toolbar"]):
            model_dd = gr.Dropdown(
                choices=LOCAL_MODELS,
                value=DEFAULT_LOCAL_MODEL,
                label="Local Ollama Model",
                info="Installed models from your local Ollama server",
                allow_custom_value=False,
                scale=4,
                elem_id="model-select",
            )
            refresh_models_btn = gr.Button("↻ Refresh models", scale=1, variant="secondary")
        refresh_models_btn.click(
            fn=workers.refresh_local_models,
            inputs=[model_dd],
            outputs=[model_dd],
        )

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
                    cancel_btn = gr.Button(
                        "🛑 Cancel",
                        scale=1,
                        variant="stop",
                    )

                cancel_event_state = gr.State(None)

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
                    with gr.Tab("🖍️ Resume Highlights"):
                        gr.Markdown(
                            "Matched keywords highlighted directly in your resume text. "
                            "Missing keywords can't be highlighted here since they don't appear "
                            "in the resume — see the Score tab for that list."
                        )
                        highlight_out = gr.HTML()
                    with gr.Tab("📄 Full Report"):
                        report_out = gr.Markdown()
                        pdf_file_out = gr.File(
                            label="⬇️ Download Full Report (PDF)", interactive=False
                        )
                        docx_file_out = gr.File(
                            label="⬇️ Download as Word (.docx)", interactive=False
                        )

                analyze_outputs = [
                    progress_box,
                    score_out,
                    resume_profile_out,
                    job_profile_out,
                    gap_out,
                    bullets_out,
                    interview_out,
                    report_out,
                    highlight_out,
                    pdf_file_out,
                    docx_file_out,
                    cancel_event_state,
                ]
                _expected_output_count = 1 + len(workers.EMPTY_TABS) + 1
                assert len(analyze_outputs) == _expected_output_count, (
                    f"analyze_outputs has {len(analyze_outputs)} components but "
                    f"analyze_stream() yields {_expected_output_count} values — "
                    "update EMPTY_TABS and every yield in analyze_stream to match."
                )

                analyze_btn.click(
                    fn=workers.analyze_stream,
                    inputs=[resume_input, jd_input, provider_dd, model_dd, cancel_event_state],
                    outputs=analyze_outputs,
                )
                cancel_btn.click(
                    fn=workers.cancel_analysis,
                    inputs=[cancel_event_state],
                    outputs=[progress_box],
                )

            # ── Tab: Build Resume ────────────────────────────────────────────────
            with gr.Tab("✨ Build Resume"):
                gr.Markdown(
                    "Draft a resume **tailored to a target job** — reordered and phrased "
                    "for relevance, but built **only from facts you provide**. Nothing is "
                    "invented: no employer, date, skill, or number appears unless it's in "
                    "your uploaded resume or notes below."
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        build_resume_input = gr.File(
                            label="Existing Resume (optional if you fill in notes below)",
                            file_types=ACCEPTED_TYPES,
                        )
                        build_notes_input = gr.Textbox(
                            label="Background Notes (optional if you upload a resume above)",
                            placeholder=(
                                "e.g. Worked as a data analyst at Acme Corp 2021-2023: built "
                                "SQL dashboards, automated weekly reports. B.Sc. Statistics, "
                                "XYZ University, 2021. Skills: Python, SQL, Excel, Tableau."
                            ),
                            lines=6,
                        )
                    with gr.Column(scale=1):
                        build_jd_input = gr.File(
                            label="Target Job Description",
                            file_types=ACCEPTED_TYPES,
                        )

                build_provider_dd = gr.Dropdown(
                    choices=PROVIDER_CHOICES,
                    value=os.getenv("LLM_PROVIDER", "auto"),
                    label="LLM Provider",
                    info="'auto' uses local Ollama if running, then Gemini",
                )

                build_btn = gr.Button("✨ Draft Resume", elem_id="analyze-btn", variant="primary")
                build_progress = gr.Markdown()

                with gr.Tabs():
                    with gr.Tab("📝 Drafted Resume"):
                        build_resume_out = gr.Markdown()
                        build_pdf_out = gr.File(label="⬇️ Download Resume (PDF)", interactive=False)
                        build_docx_out = gr.File(
                            label="⬇️ Download Resume (.docx)", interactive=False
                        )
                    with gr.Tab("📊 Match Score vs Target Job"):
                        build_score_out = gr.Markdown()

                build_outputs = [
                    build_progress,
                    build_resume_out,
                    build_score_out,
                    build_pdf_out,
                    build_docx_out,
                ]
                assert len(build_outputs) == 5, (
                    f"build_outputs has {len(build_outputs)} components but "
                    "build_resume_fn() yields 5 values — keep them in sync."
                )

                build_btn.click(
                    fn=workers.build_resume_fn,
                    inputs=[
                        build_resume_input,
                        build_notes_input,
                        build_jd_input,
                        build_provider_dd,
                        model_dd,
                    ],
                    outputs=build_outputs,
                )

            # ── Tab: Rank Resumes ────────────────────────────────────────────
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
                    fn=workers.rank_resumes_fn,
                    inputs=[dir_input, rank_jd_input, rank_provider_dd, model_dd],
                    outputs=rank_out,
                )

            # ── Tab: Batch Analyze ──────────────────────────────────────────────
            with gr.Tab("📦 Batch Analyze"):
                gr.Markdown(
                    "Run the **full 4-step analysis** (profiles, gap analysis, bullets, interview "
                    "prep) for every resume in a folder against one job description — a separate "
                    "saved report per resume. Slower than Rank Resumes since every resume gets the "
                    "complete pipeline, not just a quick score."
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        batch_dir_input = gr.Textbox(
                            label="Resume Folder Path",
                            placeholder="e.g. C:\\Users\\you\\Resumes  or  ./samples/Resumes",
                        )
                    with gr.Column(scale=1):
                        batch_jd_input = gr.File(
                            label="Job Description",
                            file_types=ACCEPTED_TYPES,
                        )

                batch_provider_dd = gr.Dropdown(
                    choices=PROVIDER_CHOICES,
                    value=os.getenv("LLM_PROVIDER", "auto"),
                    label="LLM Provider",
                    info="'auto' uses local Ollama if running, then Gemini",
                )

                batch_btn = gr.Button("📦 Batch Analyze", variant="secondary")
                batch_out = gr.Markdown(label="Batch Results")

                batch_btn.click(
                    fn=workers.batch_analyze_fn,
                    inputs=[batch_dir_input, batch_jd_input, batch_provider_dd, model_dd],
                    outputs=batch_out,
                )

            # ── Tab: Compare Job Descriptions ──────────────────────────────────
            with gr.Tab("📑 Compare JDs"):
                gr.Markdown(
                    "Score **one resume** against **several job descriptions** at once, to see "
                    "which posting it fits best — the mirror image of Rank Resumes."
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        compare_resume_input = gr.File(
                            label="Resume",
                            file_types=ACCEPTED_TYPES,
                        )
                    with gr.Column(scale=2):
                        compare_jd_inputs = gr.File(
                            label="Job Descriptions (select multiple)",
                            file_types=ACCEPTED_TYPES,
                            file_count="multiple",
                        )

                compare_provider_dd = gr.Dropdown(
                    choices=PROVIDER_CHOICES,
                    value=os.getenv("LLM_PROVIDER", "auto"),
                    label="LLM Provider",
                    info="'auto' uses local Ollama if running, then Gemini",
                )

                compare_btn = gr.Button("📑 Compare", variant="secondary")
                compare_out = gr.Markdown(label="Comparison Results")

                compare_btn.click(
                    fn=workers.compare_jds_fn,
                    inputs=[
                        compare_resume_input,
                        compare_jd_inputs,
                        compare_provider_dd,
                        model_dd,
                    ],
                    outputs=compare_out,
                )

            # ── Tab: More Tools ────────────────────────────────────────────────
            with gr.Tab("🧰 More Tools"):
                with gr.Tabs():
                    with gr.Tab("🕘 History"):
                        gr.Markdown(
                            "Browse past analysis runs saved under `output/` and see your score trend."
                        )

                        history_refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
                        history_status = gr.Markdown()
                        history_trend_plot = gr.Plot(label="Score trend")
                        history_run_dd = gr.Dropdown(label="Past runs", choices=[])

                        with gr.Tabs():
                            with gr.Tab("🔍 Gap Analysis"):
                                history_gap_out = gr.Markdown()
                            with gr.Tab("📝 Resume Profile"):
                                history_resume_out = gr.Markdown()
                            with gr.Tab("💼 Job Profile"):
                                history_job_out = gr.Markdown()
                            with gr.Tab("✏️ Resume Bullets"):
                                history_bullets_out = gr.Markdown()
                            with gr.Tab("🎤 Interview Prep"):
                                history_interview_out = gr.Markdown()

                        history_refresh_btn.click(
                            fn=workers.refresh_history_fn,
                            inputs=[],
                            outputs=[history_run_dd, history_status, history_trend_plot],
                        )
                        history_run_dd.change(
                            fn=workers.load_history_run_fn,
                            inputs=[history_run_dd],
                            outputs=[
                                history_gap_out,
                                history_resume_out,
                                history_job_out,
                                history_bullets_out,
                                history_interview_out,
                            ],
                        )
                        demo.load(
                            fn=workers.refresh_history_fn,
                            inputs=[],
                            outputs=[history_run_dd, history_status, history_trend_plot],
                        )

                    with gr.Tab("🖥️ Hardware"):
                        gr.Markdown(
                            "Detects your GPU, memory, and recommends an Ollama compute profile."
                        )

                        hw_btn = gr.Button("🔍 Detect Hardware", variant="secondary")
                        hw_out = gr.Markdown()

                        def _check_hw() -> str:
                            from resume_crew.hardware import (  # noqa: PLC0415
                                ollama_is_running,
                                resolve_ollama_profile,
                            )

                            profile = resolve_ollama_profile("auto")
                            hw = profile["hardware"]
                            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                            ollama_status = (
                                "🟢 Reachable"
                                if ollama_is_running(base_url)
                                else "🔴 Not reachable"
                            )
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
            Resume_Crew v1.4.0 — grounded, local-first AI analysis.
            Keyword scores are not ATS simulations or hiring recommendations.
        </div>
        """)

    return demo


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------


def main() -> None:
    from resume_crew.config import load_settings  # noqa: PLC0415

    settings = load_settings()
    settings.apply_telemetry_env()

    PORT = int(os.getenv("GRADIO_PORT", str(settings.gradio_port)))

    # Try ngrok first; fall back to Gradio's built-in sharing if no authtoken.
    ngrok_url = None
    token = os.getenv("NGROK_AUTHTOKEN", "").strip()
    if token:
        try:
            from pyngrok import conf, ngrok  # noqa: PLC0415

            conf.get_default().auth_token = token
            tunnel = ngrok.connect(PORT, "http")
            ngrok_url = tunnel.public_url
            print(f"\n{'=' * 60}")
            print(f"  🌐  Live ngrok URL: {ngrok_url}")
            print(f"{'=' * 60}\n")
        except ImportError:
            print("[app] pyngrok is not installed. Run: pip install pyngrok")
        except Exception as exc:  # noqa: BLE001
            print(f"[app] ngrok setup failed: {exc}")

    use_share = (ngrok_url is None) and os.getenv("GRADIO_SHARE", "false").lower() == "true"

    auth_user = os.getenv("GRADIO_AUTH_USER", "").strip()
    auth_pass = os.getenv("GRADIO_AUTH_PASS", "").strip()
    auth = (auth_user, auth_pass) if auth_user and auth_pass else None
    if (ngrok_url or use_share) and not auth:
        print(
            "   ⚠️  Sharing publicly with no login — set GRADIO_AUTH_USER/GRADIO_AUTH_PASS "
            "in .env to require a password."
        )

    demo = build_demo()
    print(f"\n🎯 Resume_Crew UI starting at http://localhost:{PORT}")
    if not ngrok_url:
        print("   (Set NGROK_AUTHTOKEN in .env for a live public URL)")

    demo.launch(
        server_port=PORT,
        share=use_share,
        show_error=True,
        inbrowser=True,
        auth=auth,
        **_LAUNCH_STYLE_KWARGS,
    )


if __name__ == "__main__":
    main()
