# Deployment

## Local (recommended)
```bash
# Create venv and install deps
make setup

# Activate
source venv/bin/activate   # macOS/Linux
# .\venv\Scripts\Activate.ps1  # Windows

# Run CLI
python main.py --resume samples/Resumes/sample_resume.pdf \
               --job-description samples/Job_description/sample_job_description.pdf \
               --provider ollama

# Run Gradio UI
python app.py
```

## Docker
```bash
docker build -t resume-crew .
docker run -p 7860:7860 --env-file .env resume-crew
```

## Docker Compose
```bash
docker compose up
```
Mounts `./output` so generated reports persist on the host.

## Environment
Copy `.env.example` to `.env` and set at minimum:
- `LLM_PROVIDER=auto` (or `ollama` / `gemini`)
- `GEMINI_API_KEY` (only if using Gemini)

`.env` is gitignored — never commit it.

## Production notes
- CrewAI telemetry is disabled by default.
- With `provider=ollama`, data stays on the local machine.
- With `provider=gemini`, source text is sent to Google — use only when acceptable.
- A public ngrok/Gradio share URL has no login by default; set `GRADIO_AUTH_USER`/`GRADIO_AUTH_PASS` to require basic auth.
