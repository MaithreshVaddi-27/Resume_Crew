"""Gradio web interface for Resume Crew with optional ngrok live sharing.

Layout and event wiring only. All long-running analysis logic lives in
:mod:`resume_crew.app.workers`.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Disable CrewAI telemetry before any import of crewai touches the env.
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["CREWAI_DISABLE_TRACKING"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

import gradio as gr  # noqa: E402

from resume_crew.app import workers  # noqa: E402
from resume_crew.config import load_settings  # noqa: E402
from resume_crew.document_reader import SUPPORTED_DOCUMENT_EXTENSIONS  # noqa: E402

_SETTINGS = load_settings()
PROVIDER_CHOICES = ["mlx", "ollama", "gemini"]
PRIVACY_NOTICE = (
    "Ollama and MLX keep analysis on this machine. Gemini sends extracted document text "
    "to Google. Choose the provider and model that fit this run."
)
_PROVIDER_LABELS = {
    "mlx": "MLX-LM (Apple Silicon)",
    "ollama": "Ollama (local)",
    "gemini": "Gemini (cloud)",
}
MLX_MODELS, DEFAULT_MLX_MODEL = workers.mlx_model_choices()
GEMINI_MODELS = [
    ("Gemini 3.8 Flash · recommended", "gemini/gemini-3.8-flash"),
    ("Gemini 3.6 Flash", "gemini/gemini-3.6-flash"),
    ("Gemini 3.5 Flash-Lite · fast and low cost", "gemini/gemini-3.5-flash-lite"),
    ("Gemini 3.1 Flash-Lite", "gemini/gemini-3.1-flash-lite"),
    ("Gemini 2.5 Pro · legacy", "gemini/gemini-2.5-pro"),
    ("Gemini 2.5 Flash · legacy", "gemini/gemini-2.5-flash"),
    ("Gemini 2.5 Flash-Lite · legacy", "gemini/gemini-2.5-flash-lite"),
]
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
        title="Resume Crew",
        analytics_enabled=False,
        **_BLOCKS_STYLE_KWARGS,
    ) as demo:
        # ── Header ────────────────────────────────────────────────────────────
        gr.HTML("""
        <header id="app-header">
            <div class="brand-mark" aria-hidden="true">RC</div>
            <div>
                <h1>Resume Crew</h1>
                <p>Make your experience easier to match to the role.</p>
            </div>
        </header>
        """)

        with gr.Accordion("Analysis settings", open=False, elem_id="settings-accordion"):
            with gr.Row(elem_classes=["model-toolbar"]):
                provider_dd = gr.Dropdown(
                    choices=[(_PROVIDER_LABELS[name], name) for name in PROVIDER_CHOICES],
                    value=(
                        _SETTINGS.provider
                        if _SETTINGS.provider in PROVIDER_CHOICES
                        else PROVIDER_CHOICES[0]
                    ),
                    label="Provider",
                    info="Choose MLX-LM or Ollama for local analysis, or Gemini for Google’s cloud model.",
                    scale=1,
                    elem_id="provider-select",
                )
                mlx_model_dd = gr.Dropdown(
                    choices=MLX_MODELS,
                    value=DEFAULT_MLX_MODEL,
                    label="MLX model",
                    info="Choose an MLX-LM model already downloaded on this machine.",
                    allow_custom_value=False,
                    scale=2,
                    visible=_SETTINGS.provider == "mlx",
                    elem_id="mlx-model-select",
                )
                model_dd = gr.Dropdown(
                    choices=LOCAL_MODELS,
                    value=DEFAULT_LOCAL_MODEL,
                    label="Ollama model",
                    info=(
                        "Choose an installed Ollama model. Start with a 4B model; install it "
                        "with `ollama pull gemma3:4b`."
                    ),
                    allow_custom_value=False,
                    scale=2,
                    visible=_SETTINGS.provider == "ollama",
                    elem_id="model-select",
                )
                gemini_model_dd = gr.Dropdown(
                    choices=GEMINI_MODELS,
                    value=(
                        _SETTINGS.gemini_model
                        if _SETTINGS.gemini_model in dict(GEMINI_MODELS).values()
                        else GEMINI_MODELS[0][1]
                    ),
                    label="Gemini model",
                    info=(
                        "Flash balances speed and quality; Flash-Lite is faster and cheaper; "
                        "Pro suits harder tasks."
                    ),
                    visible=_SETTINGS.provider == "gemini",
                    scale=2,
                    elem_id="gemini-model-select",
                )
                refresh_models_btn = gr.Button("Refresh models", scale=1, variant="secondary")
            provider_status = gr.Markdown(
                f"Selected provider: {_PROVIDER_LABELS.get(_SETTINGS.provider, 'MLX-LM (Apple Silicon)')}",
                elem_classes=["provider-status"],
            )
            refresh_models_btn.click(
                fn=workers.refresh_models,
                inputs=[model_dd, mlx_model_dd],
                outputs=[model_dd, mlx_model_dd],
            )

            def update_model_controls(provider: str) -> tuple[Any, Any, Any, Any]:
                return (
                    gr.update(visible=provider == "mlx"),
                    gr.update(visible=provider == "ollama"),
                    gr.update(visible=provider == "gemini"),
                    gr.update(
                        value=f"Selected provider: {_PROVIDER_LABELS.get(provider, provider)}"
                    ),
                )

            provider_dd.change(
                fn=update_model_controls,
                inputs=[provider_dd],
                outputs=[mlx_model_dd, model_dd, gemini_model_dd, provider_status],
            )
            demo.load(
                fn=update_model_controls,
                inputs=[provider_dd],
                outputs=[mlx_model_dd, model_dd, gemini_model_dd, provider_status],
            )

        with gr.Tabs(elem_classes=["workflow-tabs"]):
            # ── Tab 1: Analyze ─────────────────────────────────────────────────
            with gr.Tab("Analyze", elem_classes=["workflow-tab"]):
                gr.Markdown("## Compare a resume with a role", elem_classes=["section-heading"])
                gr.Markdown(
                    "Start with the evidence you already have. We’ll surface relevant experience, "
                    "gaps to consider, and questions to prepare for — without inventing credentials.",
                    elem_classes=["section-intro"],
                )
                gr.Markdown(
                    f"{PRIVACY_NOTICE} Choose MLX-LM or Ollama to keep documents local.",
                    elem_classes=["privacy-note"],
                )
                with gr.Row(elem_classes=["document-row"]):
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

                with gr.Row(elem_classes=["action-row"]):
                    analyze_btn = gr.Button(
                        "Analyze match",
                        elem_classes=["primary-action"],
                        scale=3,
                        variant="primary",
                    )
                    cancel_btn = gr.Button(
                        "Cancel analysis",
                        scale=1,
                        variant="stop",
                    )

                cancel_event_state = gr.State(None)

                progress_box = gr.Textbox(
                    label="Analysis progress",
                    lines=5,
                    max_lines=12,
                    interactive=False,
                    elem_id="progress-box",
                    placeholder="Choose both files, then select Analyze match.",
                )

                # ── Results ───────────────────────────────────────────────────
                gr.Markdown(
                    "## Your match report",
                    elem_classes=["result-heading"],
                )
                with gr.Tabs(elem_classes=["result-tabs"]):
                    with gr.Tab("Score"):
                        score_out = gr.Markdown(elem_id="score-display")
                    with gr.Tab("Resume profile"):
                        resume_profile_out = gr.Markdown()
                    with gr.Tab("Job profile"):
                        job_profile_out = gr.Markdown()
                    with gr.Tab("Gap analysis"):
                        gap_out = gr.Markdown()
                    with gr.Tab("Tailored bullets"):
                        bullets_out = gr.Markdown()
                    with gr.Tab("Interview prep"):
                        interview_out = gr.Markdown()
                    with gr.Tab("Resume evidence"):
                        gr.Markdown(
                            "Matched keywords highlighted directly in your resume text. "
                            "Missing keywords can't be highlighted here since they don't appear "
                            "in the resume — see the Score tab for that list."
                        )
                        highlight_out = gr.HTML()
                    with gr.Tab("Full report"):
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
                    inputs=[
                        resume_input,
                        jd_input,
                        provider_dd,
                        mlx_model_dd,
                        model_dd,
                        gemini_model_dd,
                        cancel_event_state,
                    ],
                    outputs=analyze_outputs,
                )
                cancel_btn.click(
                    fn=workers.cancel_analysis,
                    inputs=[cancel_event_state],
                    outputs=[progress_box],
                )

            # ── Tab: Build Resume ────────────────────────────────────────────────
            with gr.Tab("Build resume"):
                gr.Markdown(
                    "## Shape your experience for a specific role", elem_classes=["section-heading"]
                )
                gr.Markdown(PRIVACY_NOTICE, elem_classes=["privacy-note"])

                gr.Markdown(
                    "Add an existing resume or background notes, then upload the job description. "
                    "The draft can reorganize your experience, but it won’t add facts you haven’t provided.",
                    elem_classes=["section-intro"],
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        build_resume_input = gr.File(
                            label="Existing resume (optional)",
                            file_types=ACCEPTED_TYPES,
                        )
                        build_notes_input = gr.Textbox(
                            label="Background notes (optional)",
                            info="Add roles, dates, skills, education, or results you want the draft to use.",
                            placeholder=(
                                "Data analyst at Acme Corp, 2021–2023: built SQL dashboards and "
                                "automated weekly reports. B.Sc. Statistics, XYZ University, 2021."
                            ),
                            lines=6,
                        )
                    with gr.Column(scale=1):
                        build_jd_input = gr.File(
                            label="Target job description",
                            file_types=ACCEPTED_TYPES,
                        )

                build_btn = gr.Button(
                    "Draft resume", elem_classes=["primary-action"], variant="primary"
                )
                build_progress = gr.Markdown()

                with gr.Tabs():
                    with gr.Tab("Drafted resume"):
                        build_resume_out = gr.Markdown()
                        build_pdf_out = gr.File(label="Download resume (PDF)", interactive=False)
                        build_docx_out = gr.File(label="Download resume (Word)", interactive=False)
                    with gr.Tab("Match score"):
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
                        provider_dd,
                        mlx_model_dd,
                        model_dd,
                        gemini_model_dd,
                    ],
                    outputs=build_outputs,
                )

            # ── Tab: Rank resumes ────────────────────────────────────────────
            with gr.Tab("Rank resumes"):
                gr.Markdown(
                    "## Find the strongest fit in a folder", elem_classes=["section-heading"]
                )
                gr.Markdown(
                    "Score each resume against one job description. This is faster than a full "
                    "analysis and works best with a small folder of supported files.",
                    elem_classes=["section-intro"],
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        dir_input = gr.Textbox(
                            label="Folder containing resumes",
                            placeholder="Folder on the machine running Resume Crew, e.g. ./samples/Resumes",
                            info="This path is resolved on the machine running Resume Crew, not your browser device.",
                            elem_id="dir-input",
                        )
                    with gr.Column(scale=1):
                        rank_jd_input = gr.File(
                            label="Job Description",
                            file_types=ACCEPTED_TYPES,
                        )

                rank_btn = gr.Button(
                    "Rank resumes", elem_classes=["secondary-action"], variant="secondary"
                )
                rank_out = gr.Markdown(label="Ranking Results")

                rank_btn.click(
                    fn=workers.rank_resumes_fn,
                    inputs=[
                        dir_input,
                        rank_jd_input,
                        provider_dd,
                        mlx_model_dd,
                        model_dd,
                        gemini_model_dd,
                    ],
                    outputs=rank_out,
                )

            # ── Tab: Batch analyze ──────────────────────────────────────────────
            with gr.Tab("Batch analyze"):
                gr.Markdown("## Review a folder against one role", elem_classes=["section-heading"])
                gr.Markdown(PRIVACY_NOTICE, elem_classes=["privacy-note"])

                gr.Markdown(
                    "Run the full analysis for every resume in a folder. Each person gets a "
                    "separate saved report; larger folders take longer. For scores only, use Rank resumes.",
                    elem_classes=["section-intro"],
                )

                with gr.Row():
                    with gr.Column(scale=2):
                        batch_dir_input = gr.Textbox(
                            label="Folder containing resumes",
                            placeholder="Folder on the machine running Resume Crew, e.g. ./samples/Resumes",
                            info="This path is resolved on the machine running Resume Crew, not your browser device.",
                        )
                    with gr.Column(scale=1):
                        batch_jd_input = gr.File(
                            label="Job Description",
                            file_types=ACCEPTED_TYPES,
                        )

                batch_btn = gr.Button(
                    "Analyze folder", elem_classes=["secondary-action"], variant="secondary"
                )
                batch_out = gr.Markdown(label="Batch Results")

                batch_btn.click(
                    fn=workers.batch_analyze_fn,
                    inputs=[
                        batch_dir_input,
                        batch_jd_input,
                        provider_dd,
                        mlx_model_dd,
                        model_dd,
                        gemini_model_dd,
                    ],
                    outputs=batch_out,
                )

            # ── Tab: Compare job descriptions ──────────────────────────────────
            with gr.Tab("Compare jobs"):
                gr.Markdown(
                    "## See which role fits your experience", elem_classes=["section-heading"]
                )
                gr.Markdown(PRIVACY_NOTICE, elem_classes=["privacy-note"])

                gr.Markdown(
                    "Compare one resume with several job descriptions. Add the postings you’re "
                    "considering to see their relative keyword match scores.",
                    elem_classes=["section-intro"],
                )

                with gr.Row():
                    with gr.Column(scale=1):
                        compare_resume_input = gr.File(
                            label="Resume",
                            file_types=ACCEPTED_TYPES,
                        )
                    with gr.Column(scale=2):
                        compare_jd_inputs = gr.File(
                            label="Job descriptions (select multiple)",
                            file_types=ACCEPTED_TYPES,
                            file_count="multiple",
                        )

                compare_btn = gr.Button(
                    "Compare roles", elem_classes=["secondary-action"], variant="secondary"
                )
                compare_out = gr.Markdown(label="Comparison Results")

                compare_btn.click(
                    fn=workers.compare_jds_fn,
                    inputs=[
                        compare_resume_input,
                        compare_jd_inputs,
                        provider_dd,
                        mlx_model_dd,
                        model_dd,
                        gemini_model_dd,
                    ],
                    outputs=compare_out,
                )

            # ── Tab: More Tools ────────────────────────────────────────────────
            with gr.Tab("More tools"):
                with gr.Tabs():
                    with gr.Tab("History"):
                        gr.Markdown(
                            "Review reports from earlier runs and follow keyword scores over time.",
                            elem_classes=["section-intro"],
                        )

                        history_refresh_btn = gr.Button(
                            "Refresh history",
                            elem_classes=["secondary-action"],
                            variant="secondary",
                        )
                        history_status = gr.Markdown()
                        history_trend_plot = gr.Plot(label="Score trend")
                        history_summary = gr.Markdown(
                            label="Score summary",
                            value="Refresh history to load saved scores.",
                        )
                        history_run_dd = gr.Dropdown(label="Past runs", choices=[])

                        with gr.Tabs():
                            with gr.Tab("Gap analysis"):
                                history_gap_out = gr.Markdown()
                            with gr.Tab("Resume profile"):
                                history_resume_out = gr.Markdown()
                            with gr.Tab("Job profile"):
                                history_job_out = gr.Markdown()
                            with gr.Tab("Tailored bullets"):
                                history_bullets_out = gr.Markdown()
                            with gr.Tab("Interview prep"):
                                history_interview_out = gr.Markdown()

                        history_refresh_btn.click(
                            fn=workers.refresh_history_fn,
                            inputs=[],
                            outputs=[
                                history_run_dd,
                                history_status,
                                history_trend_plot,
                                history_summary,
                            ],
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
                            outputs=[
                                history_run_dd,
                                history_status,
                                history_trend_plot,
                                history_summary,
                            ],
                        )

                    with gr.Tab("Hardware"):
                        gr.Markdown(
                            "## Check local model readiness", elem_classes=["section-heading"]
                        )
                        gr.Markdown(
                            "See whether Ollama is reachable and review the hardware profile "
                            "available for local analysis.",
                            elem_classes=["section-intro"],
                        )

                        hw_btn = gr.Button(
                            "Check hardware", elem_classes=["secondary-action"], variant="secondary"
                        )
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
        <footer id="app-footer" style="text-align:center;padding:20px 0 8px;">
            Resume Crew v1.4.0 — grounded, local-first AI analysis.
            Keyword scores are not ATS simulations or hiring recommendations.
        </footer>
        """)

    return demo  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------


def main() -> None:
    from resume_crew.config import load_settings  # noqa: PLC0415

    settings = load_settings()
    settings.apply_telemetry_env()

    if (settings.ngrok_authtoken or settings.gradio_share) and not settings.auth:
        raise SystemExit(
            "Public sharing requires GRADIO_AUTH_USER and GRADIO_AUTH_PASS. "
            "Set both in .env or disable public sharing."
        )

    port = settings.gradio_port

    # Start Gradio before creating an external tunnel so the public endpoint
    # never points at a port that is still starting.
    token = settings.ngrok_authtoken
    demo = build_demo()
    print(f"\nResume Crew is ready at http://localhost:{port}")

    if token:
        demo.launch(
            server_port=port,
            share=False,
            show_error=True,
            inbrowser=True,
            auth=settings.auth,
            prevent_thread_lock=True,
            **_LAUNCH_STYLE_KWARGS,
        )
        try:
            from pyngrok import conf, ngrok  # noqa: PLC0415

            conf.get_default().auth_token = token
            tunnel = ngrok.connect(port, "http")
            print(f"\n{'=' * 60}")
            print(f"  🌐  Live ngrok URL: {tunnel.public_url}")
            print(f"{'=' * 60}\n")
            threading.Event().wait()
        except ImportError:
            print("[app] pyngrok is not installed. Run: pip install pyngrok")
            threading.Event().wait()
        except Exception as exc:  # noqa: BLE001
            print(f"[app] ngrok setup failed: {exc}")
            threading.Event().wait()
        return

    use_share = settings.gradio_share
    if not use_share:
        print("   Public sharing is off. Configure authenticated sharing in .env to enable it.")
    demo.launch(
        server_port=port,
        share=use_share,
        show_error=True,
        inbrowser=True,
        auth=settings.auth,
        **_LAUNCH_STYLE_KWARGS,
    )


if __name__ == "__main__":
    main()
