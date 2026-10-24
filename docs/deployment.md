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

## Privacy and public access
- CrewAI telemetry is disabled by default.
- With `provider=ollama`, prompts stay on the local machine, subject to your Ollama setup. With `provider=gemini`, extracted document text is sent to Google.
- Reports are stored under `output/`; protect that directory because it can contain personal information.
- Public ngrok and Gradio share tunnels require both `GRADIO_AUTH_USER` and `GRADIO_AUTH_PASS`. The app exits before opening a tunnel if either is missing. Use a unique strong password and keep the URL private.
- This app uses one shared local report folder and is intended for personal/local use, not multi-user hosting. Basic authentication does not isolate users or their reports.
