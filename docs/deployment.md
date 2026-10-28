# Deployment

## Local (recommended)

On Apple Silicon, MLX-LM is the preferred local provider. Ollama remains available on macOS, Windows, and Linux.

Install the package in a virtual environment:

```bash
make setup
source venv/bin/activate   # macOS/Linux
# .\venv\Scripts\Activate.ps1  # Windows PowerShell
```

Prefer the installed entry points:

```bash
resume-crew --resume samples/Resumes/sample_resume.pdf \
            --job-description samples/Job_description/sample_job_description.pdf \
            --provider ollama
resume-crew-ui
```

The installed `resume-crew` and `resume-crew-ui` commands are the supported entry points.

## Docker
```bash
docker build -t resume-crew .
docker run -p 7860:7860 --env-file .env resume-crew
```

## Docker Compose
```bash
docker compose up
```
Mounts `./output` so generated reports persist on the host. The mounted directory can contain personal information and should not be exposed publicly.

## Environment
Copy `.env.example` to `.env` and set at minimum:
- `LLM_PROVIDER=mlx` (recommended on Apple Silicon), `ollama`, or `gemini`
- For MLX-LM, run `mlx_lm.manage --scan`, set `MLX_MODEL` to a cached model ID, and start `mlx_lm.server --model "$MLX_MODEL"` before launching Resume Crew.
- For Ollama, run `ollama list` to confirm the selected `OLLAMA_MODEL` is installed before launching Resume Crew.
- `GEMINI_API_KEY` (only if using Gemini)

`.env` is gitignored — never commit it.

## Privacy and public access
- CrewAI telemetry is disabled by default.
- With `provider=mlx` or `provider=ollama`, prompts stay on the local machine, subject to your local server setup. With `provider=gemini`, extracted document text is sent to Google.
- Reports are stored under `output/`; protect that directory because it can contain personal information. The UI intentionally keeps absolute server paths out of normal success and error messages.
- When `GRADIO_SHARE=true`, both `GRADIO_AUTH_USER` and `GRADIO_AUTH_PASS` are required. The app exits before enabling the Gradio public tunnel if either is missing. Use a unique strong password and keep the URL private.
- This app uses one shared local report folder and is intended for personal/local use, not multi-user hosting. Basic authentication does not isolate users or their reports.
