# Resume_Crew

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![UI: Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)](https://www.gradio.app/)
[![LLM: Ollama%20%7C%20Gemini](https://img.shields.io/badge/LLM-Ollama%20%7C%20Gemini-8A2BE2.svg)](#requirements)

**Resume_Crew** compares a resume against a job description and produces an evidence-focused match report — no invented skills, no guessed experience. It runs entirely on your machine by default (via [Ollama](https://ollama.com)), with an optional cloud fallback to Google Gemini.

It ships two ways to use it:

- **CLI** (`main.py`) — scriptable, good for batch/automation work
- **Gradio web UI** (`app.py`) — point-and-click, with optional public sharing via ngrok

Supports **PDF, DOCX, TXT, and Markdown** inputs.

---

## Table of contents

- [What it produces](#what-it-produces)
- [Requirements](#requirements)
- [Getting an API key (optional — only for Gemini)](#getting-an-api-key-optional--only-for-gemini)
- [Installation](#installation)
  - [macOS](#macos)
  - [Windows](#windows-powershell)
  - [Linux](#linux)
- [Configuration](#configuration)
- [Usage — CLI](#usage--command-line-cli)
- [Usage — Web UI](#usage--web-ui-gradio)
- [Project layout](#project-layout)
- [Tracing and telemetry](#tracing-and-telemetry)
- [Privacy and data retention](#privacy-and-data-retention)
- [Troubleshooting](#troubleshooting)
- [Development and verification](#development-and-verification)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## What it produces

Each analysis creates a new report folder containing:

| File | Description |
|---|---|
| `match_report.md` | Combined report (all sections below, in one file) |
| `match_report.pdf` | PDF version — default download in the Gradio UI (Full Report tab) |
| `match_report.docx` | Word version — secondary download alongside the PDF |
| `resume_profile.md` | Factual candidate profile |
| `job_description_profile.md` | Job requirements profile |
| `skills_gap_analysis.md` | Strengths, evidence gaps, and interview risks |
| `tailored_resume_bullets.md` | Evidence-based bullet suggestions |
| `interview_preparation.md` | Role-specific questions and honest answer guidance |
| `run_meta.json` | Small sidecar (candidate, job title, score, timestamp) that powers the History tab |

The deterministic keyword score is a **whole-term overlap signal**, not an ATS simulation or a hiring recommendation.

## Requirements

- Python 3.10 or newer
- One LLM provider for full analysis:
  - **Ollama** (recommended) — runs locally, keeps data on your machine, no API key needed
  - **Gemini** (optional) — cloud fallback; needs an API key and sends document text to Google

Hardware diagnostics (`--check-hardware`) work with no LLM provider configured. Resume ranking uses the LLM too, so it needs a working provider just like full analysis does.

## Getting an API key (optional — only for Gemini)

You only need this if you want to use `--provider gemini`, or as a fallback when Ollama isn't running. If you're staying fully local with Ollama, skip this section.

1. Go to **[Google AI Studio → API Keys](https://aistudio.google.com/app/apikey)** and sign in with a Google account.
2. Click **Create API key**, and select or create a Google Cloud project when prompted (no billing account required for the free tier).
3. Copy the key — it starts with `AIza...`.
4. Paste it into your `.env` file as `GEMINI_API_KEY=your_key_here` (see [Configuration](#configuration) below).

Treat this key like a password: never commit it to Git, share it in chat, or paste it into client-side code. `.env` is already ignored by Git in this project.

> Optional: if you also want a **live public URL** for the Gradio app (via ngrok), grab a free authtoken at [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken) — see [Live public URL via ngrok](#live-public-url-via-ngrok).

## Installation

Clone the repository first:

```bash
git clone https://github.com/MaithreshVaddi-27/Resume_Crew
cd Resume_Crew
```

Then follow the instructions for your OS below.

### macOS

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/) or via Homebrew (`brew install python`).
2. In Terminal, from the project folder:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. For local (no API key) analysis, install [Ollama](https://ollama.com/download), open it once, then run:

   ```bash
   ollama pull gemma3:4b
   ```

Apple Silicon (M1/M2/M3/M4) is detected automatically. Check the recommended profile with:

```bash
python main.py --check-hardware
```

### Windows (PowerShell)

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/) and select **Add Python to PATH** during setup.
2. Open PowerShell in the project folder:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   py -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

   If PowerShell blocks activation with an execution-policy error, run this once in the same window, then activate again:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

3. For local (no API key) analysis, install [Ollama for Windows](https://ollama.com/download/windows), then run:

   ```powershell
   ollama pull gemma3:4b
   ```

Check hardware detection with:

```powershell
py main.py --check-hardware
```

### Linux

On Debian/Ubuntu, install Python tooling first if you don't already have it:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Then install the project:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For local (no API key) analysis, install [Ollama](https://ollama.com/download/linux) using its official install script, then pull a model:

```bash
ollama pull gemma3:4b
```

For NVIDIA systems, confirm the driver and `nvidia-smi` work **before** starting Ollama, so GPU acceleration is detected correctly. Check with:

```bash
python main.py --check-hardware
```

## Configuration

Copy the template file to create your local config:

```bash
# macOS / Linux
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

Then open `.env` and set the values you need. The most relevant settings:

```env
RESUME_PATH=./samples/Resumes/sample_resume.pdf
JD_PATH=./samples/Job_description/sample_job_description.pdf

# auto = use local Ollama when reachable, then fall back to Gemini.
LLM_PROVIDER=auto

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT=3.0        # Raise this on slow machines or WSL2
OLLAMA_PROFILE=auto       # auto detects CUDA > MPS > CPU

# Only needed for --provider gemini, or as the auto fallback.
# Get this at https://aistudio.google.com/app/apikey — see "Getting an API key" above.
GEMINI_API_KEY=
GEMINI_MODEL=gemini/gemini-3.1-flash-lite

CREWAI_TRACING_ENABLED=false
CREWAI_DISABLE_TELEMETRY=true
CREWAI_DISABLE_TRACKING=true
OTEL_SDK_DISABLED=true

GRADIO_PORT=7860
GRADIO_SHARE=false        # true = use Gradio's built-in tunnel instead of ngrok

# Optional: for a live public URL. Get a free token at
# https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTHTOKEN=your_ngrok_authtoken

# Recommended if you use NGROK_AUTHTOKEN or GRADIO_SHARE — a public URL has
# no login by default, so set both to require a username/password.
GRADIO_AUTH_USER=user
GRADIO_AUTH_PASS=user@123
```

`.env` is listed in `.gitignore` — never commit it, since it can hold API keys.

## Usage — Command Line (CLI)

Activate the virtual environment for your OS (see [Installation](#installation)) before each session, then run commands from the project root.

### Full local analysis (Ollama, no API key)

**macOS / Linux:**

```bash
python main.py \
  --resume samples/Resumes/sample_resume.pdf \
  --job-description samples/Job_description/sample_job_description.pdf \
  --provider ollama
```

**Windows PowerShell:**

```powershell
python main.py `
  --resume .\samples\Resumes\sample_resume.pdf `
  --job-description .\samples\Job_description\sample_job_description.pdf `
  --provider ollama
```

### Gemini analysis (needs an API key)

After setting `GEMINI_API_KEY` in `.env` (see [Getting an API key](#getting-an-api-key-optional--only-for-gemini)):

```bash
python main.py --resume ./my_resume.pdf --job-description ./job.docx --provider gemini
```

### Rank several resume versions with the LLM

```bash
python main.py --rank-resumes ./resume_versions --job-description ./job.docx --provider ollama
```

Each resume in the folder gets its own LLM scoring call (0–100 with a one-line note), so ranking a large folder takes proportionally longer and, on `--provider gemini`, costs one API call per file.

### Hardware and model diagnostics

```bash
python main.py --check-hardware
python main.py --check-hardware --ollama-profile mps
python main.py --version
```

## Usage — Web UI (Gradio)

Start the browser interface from the project root (same command on every OS, once your virtual environment is active):

```bash
python app.py
```

The UI opens automatically at `http://localhost:7860` and includes:

- **Analyze Resume** — upload resume + JD, pick provider, watch step-by-step progress, view results across 8 sub-tabs (Score, Resume Profile, Job Profile, Gap Analysis, Resume Bullets, Interview Prep, Resume Highlights, Full Report). Includes a **Cancel** button to stop a run between pipeline steps. The Full Report tab offers **PDF (default)** and **Word (.docx)** downloads.
- **Build Resume** — draft a resume tailored to a target job description, using *only* facts from an uploaded resume and/or freeform notes you provide. Nothing is invented: no employer, date, skill, or number appears unless it's in your source material.
- **Rank Resumes** — score a local folder of resumes against a JD, one lightweight LLM call per resume.
- **Batch Analyze** — run the *full* 4-step analysis for every resume in a folder against one JD, saving a separate report per resume.
- **Compare JDs** — score one resume against several job descriptions at once, to see which posting fits best.
- **History** — browse past saved runs, reload any report back into the tabs, and view a score-trend chart across runs.
- **Hardware** — detect GPU, RAM, and Ollama status from the browser.

### Live public URL via ngrok

1. Get a free authtoken at [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken).
2. Add it to `.env`:

   ```env
   NGROK_AUTHTOKEN=your_token_here
   ```

3. Run `python app.py`. A live public URL prints in the terminal at startup:

   ```text
   ============================================================
     🌐  Live ngrok URL: https://xxxx-xx-xx.ngrok-free.app
   ============================================================
   ```

Share this URL with anyone — no port-forwarding or VPN required.

**A public URL has no login by default** — anyone with the link can upload documents and run analysis. Set both of these in `.env` to require a username/password before the app loads:

```env
GRADIO_AUTH_USER=someuser
GRADIO_AUTH_PASS=some-strong-password
```

### Port and share settings

```env
GRADIO_PORT=7860        # Change the local port
GRADIO_SHARE=true        # Use Gradio's built-in tunnel instead of ngrok
```

## Project layout

```text
Resume_Crew/
├── src/resume_crew/          # Application package
├── tests/                    # Automated tests
├── samples/                  # Versioned demonstration documents
│   ├── Resumes/               #   sample_resume.pdf
│   └── Job_description/       #   sample_job_description.pdf
├── output/                   # Created locally for generated reports (ignored)
├── app.py                    # Gradio web UI entry point
├── main.py                   # CLI entry point (source-checkout)
├── .env.example               # Safe configuration template
└── pyproject.toml             # Package and dependency metadata
```

## Tracing and telemetry

CrewAI execution traces and telemetry are disabled by default, both in `.env.example` and in the application itself. The project passes `tracing=False` for every CrewAI task and disables CrewAI/OpenTelemetry telemetry. This keeps candidate data and execution metadata out of CrewAI's tracing services.

## Privacy and data retention

- With `--provider ollama`, resume and job text stay on the local machine, subject to your local Ollama installation.
- With `--provider gemini`, source text is sent to Google — use it only when that's acceptable.
- Reports are created in `output/` and can contain personal information. That folder is ignored by Git.
- The current version does not persist analysis history outside your own `output/` folder.

## Troubleshooting

| Problem | Resolution |
|---|---|
| `ModuleNotFoundError` on startup | Activate the project virtual environment and run `pip install -r requirements.txt`. |
| `Ollama is not reachable` | Start the Ollama application/service, run `ollama pull gemma3:4b`, then retry. Raise `OLLAMA_TIMEOUT` in `.env` if on a slow machine. |
| Gemini fallback error | Add a valid `GEMINI_API_KEY` to `.env` (see [Getting an API key](#getting-an-api-key-optional--only-for-gemini)), or use `--provider ollama`. |
| PDF has no extractable text | The PDF is likely scanned. Run OCR first, then supply the OCR result. |
| Unsupported file type | Convert the file to PDF, DOCX, TXT, or Markdown. |
| Input exceeds character limit | Split the document or remove irrelevant appendices. |
| PowerShell will not activate venv | Use the temporary execution-policy command in the [Windows installation](#windows-powershell) section. |
| Slow local analysis | Run `python main.py --check-hardware`; reduce Ollama context or use a smaller local model. |
| ngrok tunnel not created | Ensure `pyngrok` is installed (`pip install pyngrok`) and `NGROK_AUTHTOKEN` is set in `.env`. |
| Gradio port already in use | Set `GRADIO_PORT=7861` (or any free port) in `.env`. |
| `python app.py` fails with `DLL load failed... Application Control policy has blocked this file` (Windows) | A managed/corporate Windows security policy (WDAC/AppLocker) is blocking a native DLL — usually pandas, pulled in by Gradio — often because the project folder still has the "downloaded from the internet" flag. In PowerShell from the project root: `Get-ChildItem -Path .\venv -Recurse \| Unblock-File`, then retry. If it still fails, move the project out of `Downloads` to a plain local folder (e.g. `C:\Resume_Crew`), delete `venv`, and reinstall. On a company-managed device the policy may be enforced centrally — ask IT to allow Python/pandas, or run the project inside WSL2 instead. |

## Development and verification

```bash
python -m pytest -q
python -m py_compile main.py app.py src/resume_crew/*.py
python -m pip check
```

The test suite covers document validation, keyword scoring (including single-char tokens like `R`), report structure, CRLF handling, output safety, timestamp format, and hardware-setting validation. A live LLM run requires an available Ollama server or valid Gemini credentials.

## Disclaimer

This project is intended for educational, research, and learning purposes. The keyword-match score and LLM-generated output are a starting point for your own judgment — not an ATS simulation, hiring recommendation, or guarantee of job-search outcomes. Always review generated content before using it.

## License

This project is licensed under the MIT License — see [LICENSE](https://github.com/MaithreshVaddi-27/Resume_Crew/blob/main/LICENSE) for the full text.
