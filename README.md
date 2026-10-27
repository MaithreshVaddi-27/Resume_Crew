# Resume Crew

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![UI: Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)](https://www.gradio.app/)
[![LLM: MLX-LM | Ollama | Gemini](https://img.shields.io/badge/LLM-MLX--LM%20%7C%20Ollama%20%7C%20Gemini-8A2BE2.svg)](#requirements)
[![MLX-LM](https://img.shields.io/badge/MLX--LM-Apple%20Silicon-green.svg?logo=apple)](https://github.com/ml-explore/mlx-lm)
[![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-purple.svg)](https://ollama.com/)
[![CrewAI](https://img.shields.io/badge/Agent%20framework-CrewAI-blue.svg)](https://docs.crewai.com/)
[![Pyngrok](https://img.shields.io/badge/Tunneling-pyngrok-lightgrey.svg)](https://github.com/alexdeleon/pyngrok)
[![Tests](https://img.shields.io/badge/tests-56%20passed-brightgreen.svg)](#development-and-verification)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-success.svg)](https://github.com/MaithreshVaddi-27/Resume_Crew/actions)

**Resume Crew** compares a resume against a job description and produces an evidence-focused match report — no invented skills, no guessed experience. Choose MLX-LM or Ollama for local analysis, or Gemini when you are comfortable sending extracted document text to Google.

**Maintainer:** Maithresh Vaddi

It ships two ways to use it:

- **CLI** (`resume-crew`) — scriptable, good for batch/automation work
- **Gradio web UI** (`resume-crew-ui`) — point-and-click, with optional public sharing via ngrok

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

- Python 3.12 or newer
- One LLM provider for full analysis:
  - **MLX-LM** (recommended on Apple Silicon) — runs locally through its OpenAI-compatible server
  - **Ollama** — runs locally, keeps data on your machine, no API key needed
  - **Gemini** (optional) — cloud analysis; needs an API key and sends document text to Google

Hardware diagnostics (`--check-hardware`) work with no LLM provider configured. Resume ranking uses the LLM too, so it needs a working provider just like full analysis does.

## Getting an API key (optional — only for Gemini)

You only need this if you want to use `--provider gemini`. If you are using MLX-LM or Ollama locally, skip this section.

1. Go to **[Google AI Studio → API Keys](https://aistudio.google.com/app/apikey)** and sign in with a Google account.
2. Click **Create API key**, and select or create a Google Cloud project when prompted (no billing account required for the free tier).
3. Copy the key — it starts with `AIza...`.
4. Paste it into your `.env` file as `GEMINI_API_KEY=your_key_here` (see [Configuration](#configuration) below).

Treat this key like a password: never commit it to Git, share it in chat, or paste it into client-side code. `.env` is already ignored by Git in this project.

> Optional: if you need a **public URL** for the Gradio app, ngrok requires an authtoken and both app-login credentials. See [Authenticated public sharing](#authenticated-public-sharing) for setup and privacy requirements.

## Installation

Clone the repository first:

```bash
git clone https://github.com/MaithreshVaddi-27/Resume_Crew
cd Resume_Crew
```

Then follow the instructions for your OS below.

### macOS

1. Install Python 3.12+ from [python.org](https://www.python.org/downloads/) or via Homebrew (`brew install python`).
2. In Terminal, from the project folder:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install --upgrade pip
   pip install .
   ```

3. For local analysis on Apple Silicon, install Homebrew if needed, then install pipx and MLX-LM:

   ```bash
   brew install pipx cmake
   pipx ensurepath
   pipx install mlx-lm
   mlx_lm.manage --scan
   ```

   Resume Crew lists only MLX-LM models found by `mlx_lm.manage --scan`; choose one in the
   Analysis settings panel, then start the server with the selected model:

   ```bash
   mlx_lm.server --model <installed-model-id>
   ```

   Keep that server running on its default port (`8080`). Resume Crew connects to it through `MLX_BASE_URL`.

4. Alternatively, install [Ollama](https://ollama.com/download), open it once, then run:

   ```bash
   ollama pull gemma3:1b
   ```

Apple Silicon (M1/M2/M3/M4) is detected automatically. Check the recommended profile with:

```bash
resume-crew --check-hardware
```

### Windows (PowerShell)

1. Install Python 3.12+ from [python.org](https://www.python.org/downloads/) and select **Add Python to PATH** during setup.
2. Open PowerShell in the project folder:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   py -m pip install --upgrade pip
   pip install .
   ```

   If PowerShell blocks activation with an execution-policy error, run this once in the same window, then activate again:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

3. For local (no API key) analysis, install [Ollama for Windows](https://ollama.com/download/windows), then run:

   ```powershell
   ollama pull gemma3:1b
   ```

Check hardware detection with:

```powershell
.\venv\Scripts\resume-crew.exe --check-hardware
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
pip install .
```

For local (no API key) analysis, install [Ollama](https://ollama.com/download/linux) using its official install script, then pull a model:

```bash
ollama pull gemma3:1b
```

For NVIDIA systems, confirm the driver and `nvidia-smi` work **before** starting Ollama, so GPU acceleration is detected correctly. Check with:

```bash
resume-crew --check-hardware
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

# Choose exactly one provider for each run: mlx, ollama, or gemini.
LLM_PROVIDER=mlx

# MLX-LM OpenAI-compatible server
MLX_BASE_URL=http://localhost:8080/v1
# Choose an ID shown by `mlx_lm.manage --scan`.
MLX_MODEL=mlx-community/Qwen3-4B-Instruct-2507-4bit

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:1b
OLLAMA_TIMEOUT=3.0        # Raise this on slow machines or WSL2
OLLAMA_PROFILE=auto       # auto detects CUDA > MPS > CPU

# Required when using --provider gemini.
# Get this at https://aistudio.google.com/app/apikey — see "Getting an API key" above.
GEMINI_API_KEY=
GEMINI_MODEL=gemini/gemini-3.8-flash

CREWAI_TRACING_ENABLED=false
CREWAI_DISABLE_TELEMETRY=true
CREWAI_DISABLE_TRACKING=true
OTEL_SDK_DISABLED=true

GRADIO_PORT=7860
GRADIO_SHARE=false        # true = use Gradio's built-in tunnel instead of ngrok

# Optional: for a live public URL. Get a free token at
# https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTHTOKEN=

# Recommended if you use NGROK_AUTHTOKEN or GRADIO_SHARE — a public URL has
# no login by default, so set both to require a username/password.
GRADIO_AUTH_USER=replace_with_a_username
GRADIO_AUTH_PASS=replace_with_a_strong_password
```

`.env` is listed in `.gitignore` — never commit it, since it can hold API keys.

## Usage — Command Line (CLI)

Activate the virtual environment for your OS (see [Installation](#installation)) before each session, then run commands from the project root.

### Full local analysis with MLX-LM (Apple Silicon)

Start the MLX-LM server first with an installed model selected in the UI:

```bash
mlx_lm.server --model <installed-model-id>
```

Then run Resume Crew in another terminal:

```bash
resume-crew \
  --resume samples/Resumes/sample_resume.pdf \
  --job-description samples/Job_description/sample_job_description.pdf \
  --provider mlx
```

### Full local analysis with Ollama (no API key)

**macOS / Linux:**

```bash
resume-crew \
  --resume samples/Resumes/sample_resume.pdf \
  --job-description samples/Job_description/sample_job_description.pdf \
  --provider ollama
```

**Windows PowerShell:**

```powershell
resume-crew `
  --resume .\samples\Resumes\sample_resume.pdf `
  --job-description .\samples\Job_description\sample_job_description.pdf `
  --provider ollama
```

### Gemini analysis (needs an API key)

After setting `GEMINI_API_KEY` in `.env` (see [Getting an API key](#getting-an-api-key-optional--only-for-gemini)):

```bash
resume-crew --resume ./my_resume.pdf --job-description ./job.docx --provider gemini
```

### Rank several resume versions with the LLM

```bash
resume-crew --rank-resumes ./resume_versions --job-description ./job.docx --provider ollama
```

Each resume in the folder gets its own LLM scoring call (0–100 with a one-line note), so ranking a large folder takes proportionally longer and, on `--provider gemini`, costs one API call per file.

### Hardware and model diagnostics

```bash
resume-crew --check-hardware
resume-crew --check-hardware --ollama-profile mps
resume-crew --version
```

## Usage — Web UI (Gradio)

Start the browser interface once your virtual environment is active:

```bash
resume-crew-ui
```

Use the installed console commands from the activated virtual environment; no source-checkout import shim is required.

The UI opens automatically at `http://localhost:7860` and includes:

- **Analyze** — upload a resume and job description, choose a provider, and review the match report. Results include Score, Resume Profile, Job Profile, Gap Analysis, Tailored Bullets, Interview Prep, Resume Evidence, and Full Report. Cancel stops analysis between pipeline stages; the Full Report tab offers PDF and Word downloads. Generated reports remain local; the UI does not display server filesystem paths.
- **Build Resume** — draft a resume tailored to a target job description, using *only* facts from an uploaded resume and/or freeform notes you provide. Nothing is invented: no employer, date, skill, or number appears unless it's in your source material.
- **Rank Resumes** — score a local folder of resumes against a JD, one lightweight LLM call per resume.
- **Batch Analyze** — run the *full* 4-step analysis for every resume in a folder against one JD, saving a separate report per resume.
- **Compare JDs** — score one resume against several job descriptions at once, to see which posting fits best.
- **History** — browse past saved runs, reload any report back into the tabs, and view a score-trend chart across runs.
- **Hardware** — detect GPU, RAM, and Ollama status from the browser.

### Authenticated public sharing

Public tunnels expose the app to anyone who can reach the URL. Resume files, notes, and generated reports may contain sensitive personal information. Resume Crew therefore refuses to start ngrok or Gradio sharing unless both credentials are set.

1. For ngrok, get an authtoken at [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken).
2. Add the tunnel option and credentials to `.env`:

   ```env
   NGROK_AUTHTOKEN=your_token_here
   GRADIO_AUTH_USER=choose_a_username
   GRADIO_AUTH_PASS=replace_with_a_strong_password
   ```

3. Run `resume-crew-ui`. The URL prints in the terminal after tunnel setup. Keep it and the credentials private; use a unique, strong password.

To use Gradio's built-in tunnel instead, set `GRADIO_SHARE=true` and keep both auth values configured. To run locally only, leave `GRADIO_SHARE=false` and `NGROK_AUTHTOKEN` empty.

### Port and share settings

```env
GRADIO_PORT=7860        # Change the local port
GRADIO_SHARE=false      # Public Gradio tunnel (requires both auth values)
```

## Project layout

```text
Resume Crew/
├── src/resume_crew/          # Application package and console entry points
├── tests/                    # Automated tests
├── samples/                  # Versioned demonstration documents
│   ├── Resumes/               #   sample_resume.pdf
│   └── Job_description/       #   sample_job_description.pdf
├── output/                   # Created locally for generated reports (ignored)
├── .env.example              # Safe configuration template
└── pyproject.toml             # Package and dependency metadata
```

## Tracing and telemetry

CrewAI execution traces and telemetry are disabled by default, both in `.env.example` and in the application itself. The project passes `tracing=False` for every CrewAI task and disables CrewAI/OpenTelemetry telemetry. This keeps candidate data and execution metadata out of CrewAI's tracing services.

## Privacy and data retention

- With `--provider mlx`, resume and job text stay on the local machine, subject to your MLX-LM server.
- With `--provider ollama`, resume and job text stay on the local machine, subject to your local Ollama installation.
- With `--provider gemini`, source text is sent to Google — use it only when that's acceptable.
- Reports are created in `output/` and can contain personal information. That folder is ignored by Git.
- History reads saved reports and score metadata from the local `output/` folder. The app does not send that history to a separate storage service.

## Troubleshooting

| Problem | Resolution |
|---|---|
| `ModuleNotFoundError` on startup | Activate the project virtual environment and run `pip install .`. |
| `Ollama is not reachable` | Start the Ollama application/service, run `ollama pull gemma3:1b`, then retry. Raise `OLLAMA_TIMEOUT` in `.env` if on a slow machine. |
| Gemini configuration error | Add a valid `GEMINI_API_KEY` to `.env` (see [Getting an API key](#getting-an-api-key-optional--only-for-gemini)) before selecting `--provider gemini`. |
| PDF has no extractable text | The PDF is likely scanned. Run OCR first, then supply the OCR result. |
| Unsupported file type | Convert the file to PDF, DOCX, TXT, or Markdown. |
| Input exceeds character limit | Split the document or remove irrelevant appendices. |
| PowerShell will not activate venv | Use the temporary execution-policy command in the [Windows installation](#windows-powershell) section. |
| Slow local analysis | Run `resume-crew --check-hardware`; reduce Ollama context or use a smaller local model. |
| ngrok tunnel not created | Ensure `pyngrok` is installed (`pip install pyngrok`) and `NGROK_AUTHTOKEN` is set in `.env`. |
| Gradio port already in use | Set `GRADIO_PORT=7861` (or any free port) in `.env`. |
| `resume-crew-ui` fails with `DLL load failed... Application Control policy has blocked this file` (Windows) | A managed/corporate Windows security policy (WDAC/AppLocker) is blocking a native DLL — usually pandas, pulled in by Gradio — often because the project folder still has the "downloaded from the internet" flag. In PowerShell from the project root: `Get-ChildItem -Path .\venv -Recurse \| Unblock-File`, then retry. If it still fails, move the project out of `Downloads` to a plain local folder (e.g. `C:\Resume Crew`), delete `venv`, and reinstall. On a company-managed device the policy may be enforced centrally — ask IT to allow Python/pandas, or run the project inside WSL2 instead. |

## Development and verification

Install development tools with `pip install -e '.[dev]'`.

```bash
python -m pytest --cov=src --cov-report=term-missing
python -m compileall -q src
python -m pip check
```

The test suite covers document validation, keyword scoring (including single-character tokens like `R`), report structure, CRLF handling, output safety, timestamp format, and hardware-setting validation. A live LLM run requires a running MLX-LM or Ollama server, or valid Gemini credentials.

Coverage is reported on every CI run via `pytest --cov=src --cov-report=term-missing`.

## Disclaimer

This project is intended for educational, research, and learning purposes. The keyword-match score and LLM-generated output are a starting point for your own judgment — not an ATS simulation, hiring recommendation, or guarantee of job-search outcomes. Always review generated content before using it.

## License

This project is licensed under the MIT License — see [LICENSE](https://github.com/MaithreshVaddi-27/Resume_Crew/blob/main/LICENSE) for the full text.

It ships two ways to use it:

- **CLI** (`resume-crew`) — scriptable, good for batch/automation work
- **Gradio web UI** (`resume-crew-ui`) — point-and-click, with optional public sharing via ngrok

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

- Python 3.12 or newer
- One LLM provider for full analysis:
  - **MLX-LM** (recommended on Apple Silicon) — runs locally through its OpenAI-compatible server
  - **Ollama** — runs locally, keeps data on your machine, no API key needed
  - **Gemini** (optional) — cloud analysis; needs an API key and sends document text to Google

Hardware diagnostics (`--check-hardware`) work with no LLM provider configured. Resume ranking uses the LLM too, so it needs a working provider just like full analysis does.

## Getting an API key (optional — only for Gemini)

You only need this if you want to use `--provider gemini`. If you are using MLX-LM or Ollama locally, skip this section.

1. Go to **[Google AI Studio → API Keys](https://aistudio.google.com/app/apikey)** and sign in with a Google account.
2. Click **Create API key**, and select or create a Google Cloud project when prompted (no billing account required for the free tier).
3. Copy the key — it starts with `AIza...`.
4. Paste it into your `.env` file as `GEMINI_API_KEY=your_key_here` (see [Configuration](#configuration) below).

Treat this key like a password: never commit it to Git, share it in chat, or paste it into client-side code. `.env` is already ignored by Git in this project.

> Optional: if you need a **public URL** for the Gradio app, ngrok requires an authtoken and both app-login credentials. See [Authenticated public sharing](#authenticated-public-sharing) for setup and privacy requirements.

## Installation

Clone the repository first:

```bash
git clone https://github.com/MaithreshVaddi-27/Resume_Crew
cd Resume_Crew
```

Then follow the instructions for your OS below.

### macOS

1. Install Python 3.12+ from [python.org](https://www.python.org/downloads/) or via Homebrew (`brew install python`).
2. In Terminal, from the project folder:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install --upgrade pip
   pip install .
   ```

3. For local analysis on Apple Silicon, install Homebrew if needed, then install pipx and MLX-LM:

   ```bash
   brew install pipx cmake
   pipx ensurepath
   pipx install mlx-lm
   mlx_lm.manage --scan
   ```

   Resume Crew lists only MLX-LM models found by `mlx_lm.manage --scan`; choose one in the
   Analysis settings panel, then start the server with the selected model:

   ```bash
   mlx_lm.server --model <installed-model-id>
   ```

   Keep that server running on its default port (`8080`). Resume Crew connects to it through `MLX_BASE_URL`.

4. Alternatively, install [Ollama](https://ollama.com/download), open it once, then run:

   ```bash
   ollama pull gemma3:4b
   ```

Apple Silicon (M1/M2/M3/M4) is detected automatically. Check the recommended profile with:

```bash
resume-crew --check-hardware
```

### Windows (PowerShell)

1. Install Python 3.12+ from [python.org](https://www.python.org/downloads/) and select **Add Python to PATH** during setup.
2. Open PowerShell in the project folder:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   py -m pip install --upgrade pip
   pip install .
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
.\venv\Scripts\resume-crew.exe --check-hardware
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
pip install .
```

For local (no API key) analysis, install [Ollama](https://ollama.com/download/linux) using its official install script, then pull a model:

```bash
ollama pull gemma3:4b
```

For NVIDIA systems, confirm the driver and `nvidia-smi` work **before** starting Ollama, so GPU acceleration is detected correctly. Check with:

```bash
resume-crew --check-hardware
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

# Choose exactly one provider for each run: mlx, ollama, or gemini.
LLM_PROVIDER=mlx

# MLX-LM OpenAI-compatible server
MLX_BASE_URL=http://localhost:8080/v1
# Choose an ID shown by `mlx_lm.manage --scan`.
MLX_MODEL=mlx-community/Qwen3-4B-Instruct-2507-4bit

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_TIMEOUT=3.0        # Raise this on slow machines or WSL2
OLLAMA_PROFILE=auto       # auto detects CUDA > MPS > CPU

# Required when using --provider gemini.
# Get this at https://aistudio.google.com/app/apikey — see "Getting an API key" above.
GEMINI_API_KEY=
GEMINI_MODEL=gemini/gemini-3.8-flash

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
GRADIO_AUTH_USER=replace_with_a_username
GRADIO_AUTH_PASS=replace_with_a_strong_password
```

`.env` is listed in `.gitignore` — never commit it, since it can hold API keys.

## Usage — Command Line (CLI)

Activate the virtual environment for your OS (see [Installation](#installation)) before each session, then run commands from the project root.

### Full local analysis with MLX-LM (Apple Silicon)

Start the MLX-LM server first with an installed model selected in the UI:

```bash
mlx_lm.server --model <installed-model-id>
```

Then run Resume Crew in another terminal:

```bash
resume-crew \
  --resume samples/Resumes/sample_resume.pdf \
  --job-description samples/Job_description/sample_job_description.pdf \
  --provider mlx
```

### Full local analysis with Ollama (no API key)

**macOS / Linux:**

```bash
resume-crew \
  --resume samples/Resumes/sample_resume.pdf \
  --job-description samples/Job_description/sample_job_description.pdf \
  --provider ollama
```

**Windows PowerShell:**

```powershell
resume-crew `
  --resume .\samples\Resumes\sample_resume.pdf `
  --job-description .\samples\Job_description\sample_job_description.pdf `
  --provider ollama
```

### Gemini analysis (needs an API key)

After setting `GEMINI_API_KEY` in `.env` (see [Getting an API key](#getting-an-api-key-optional--only-for-gemini)):

```bash
resume-crew --resume ./my_resume.pdf --job-description ./job.docx --provider gemini
```

### Rank several resume versions with the LLM

```bash
resume-crew --rank-resumes ./resume_versions --job-description ./job.docx --provider ollama
```

Each resume in the folder gets its own LLM scoring call (0–100 with a one-line note), so ranking a large folder takes proportionally longer and, on `--provider gemini`, costs one API call per file.

### Hardware and model diagnostics

```bash
resume-crew --check-hardware
resume-crew --check-hardware --ollama-profile mps
resume-crew --version
```

## Usage — Web UI (Gradio)

Start the browser interface once your virtual environment is active:

```bash
resume-crew-ui
```

Use the installed console commands from the activated virtual environment; no source-checkout import shim is required.

The UI opens automatically at `http://localhost:7860` and includes:

- **Analyze** — upload a resume and job description, choose a provider, and review the match report. Results include Score, Resume Profile, Job Profile, Gap Analysis, Tailored Bullets, Interview Prep, Resume Evidence, and Full Report. Cancel stops analysis between pipeline stages; the Full Report tab offers PDF and Word downloads. Generated reports remain local; the UI does not display server filesystem paths.
- **Build Resume** — draft a resume tailored to a target job description, using *only* facts from an uploaded resume and/or freeform notes you provide. Nothing is invented: no employer, date, skill, or number appears unless it's in your source material.
- **Rank Resumes** — score a local folder of resumes against a JD, one lightweight LLM call per resume.
- **Batch Analyze** — run the *full* 4-step analysis for every resume in a folder against one JD, saving a separate report per resume.
- **Compare JDs** — score one resume against several job descriptions at once, to see which posting fits best.
- **History** — browse past saved runs, reload any report back into the tabs, and view a score-trend chart across runs.
- **Hardware** — detect GPU, RAM, and Ollama status from the browser.

### Authenticated public sharing

Public tunnels expose the app to anyone who can reach the URL. Resume files, notes, and generated reports may contain sensitive personal information. Resume Crew therefore refuses to start ngrok or Gradio sharing unless both credentials are set.

1. For ngrok, get an authtoken at [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken).
2. Add the tunnel option and credentials to `.env`:

   ```env
   NGROK_AUTHTOKEN=your_token_here
   GRADIO_AUTH_USER=choose_a_username
   GRADIO_AUTH_PASS=replace_with_a_strong_password
   ```

3. Run `resume-crew-ui`. The URL prints in the terminal after tunnel setup. Keep it and the credentials private; use a unique, strong password.

To use Gradio's built-in tunnel instead, set `GRADIO_SHARE=true` and keep both auth values configured. To run locally only, leave `GRADIO_SHARE=false` and `NGROK_AUTHTOKEN` empty.

### Port and share settings

```env
GRADIO_PORT=7860        # Change the local port
GRADIO_SHARE=false      # Public Gradio tunnel (requires both auth values)
```

## Project layout

```text
Resume Crew/
├── src/resume_crew/          # Application package and console entry points
├── tests/                    # Automated tests
├── samples/                  # Versioned demonstration documents
│   ├── Resumes/               #   sample_resume.pdf
│   └── Job_description/       #   sample_job_description.pdf
├── output/                   # Created locally for generated reports (ignored)
├── .env.example              # Safe configuration template
└── pyproject.toml             # Package and dependency metadata
```

## Tracing and telemetry

CrewAI execution traces and telemetry are disabled by default, both in `.env.example` and in the application itself. The project passes `tracing=False` for every CrewAI task and disables CrewAI/OpenTelemetry telemetry. This keeps candidate data and execution metadata out of CrewAI's tracing services.

## Privacy and data retention

- With `--provider mlx`, resume and job text stay on the local machine, subject to your MLX-LM server.
- With `--provider ollama`, resume and job text stay on the local machine, subject to your local Ollama installation.
- With `--provider gemini`, source text is sent to Google — use it only when that's acceptable.
- Reports are created in `output/` and can contain personal information. That folder is ignored by Git.
- History reads saved reports and score metadata from the local `output/` folder. The app does not send that history to a separate storage service.

## Troubleshooting

| Problem | Resolution |
|---|---|
| `ModuleNotFoundError` on startup | Activate the project virtual environment and run `pip install .`. |
| `Ollama is not reachable` | Start the Ollama application/service, run `ollama pull gemma3:4b`, then retry. Raise `OLLAMA_TIMEOUT` in `.env` if on a slow machine. |
| Gemini configuration error | Add a valid `GEMINI_API_KEY` to `.env` (see [Getting an API key](#getting-an-api-key-optional--only-for-gemini)) before selecting `--provider gemini`. |
| PDF has no extractable text | The PDF is likely scanned. Run OCR first, then supply the OCR result. |
| Unsupported file type | Convert the file to PDF, DOCX, TXT, or Markdown. |
| Input exceeds character limit | Split the document or remove irrelevant appendices. |
| PowerShell will not activate venv | Use the temporary execution-policy command in the [Windows installation](#windows-powershell) section. |
| Slow local analysis | Run `resume-crew --check-hardware`; reduce Ollama context or use a smaller local model. |
| ngrok tunnel not created | Ensure `pyngrok` is installed (`pip install pyngrok`) and `NGROK_AUTHTOKEN` is set in `.env`. |
| Gradio port already in use | Set `GRADIO_PORT=7861` (or any free port) in `.env`. |
| `resume-crew-ui` fails with `DLL load failed... Application Control policy has blocked this file` (Windows) | A managed/corporate Windows security policy (WDAC/AppLocker) is blocking a native DLL — usually pandas, pulled in by Gradio — often because the project folder still has the "downloaded from the internet" flag. In PowerShell from the project root: `Get-ChildItem -Path .\venv -Recurse \| Unblock-File`, then retry. If it still fails, move the project out of `Downloads` to a plain local folder (e.g. `C:\Resume Crew`), delete `venv`, and reinstall. On a company-managed device the policy may be enforced centrally — ask IT to allow Python/pandas, or run the project inside WSL2 instead. |

## Development and verification

Install development tools with `pip install -e '.[dev]'`.

```bash
python -m pytest --cov=src --cov-report=term-missing
python -m compileall -q src
python -m pip check
```

The test suite covers document validation, keyword scoring (including single-character tokens like `R`), report structure, CRLF handling, output safety, timestamp format, and hardware-setting validation. A live LLM run requires a running MLX-LM or Ollama server, or valid Gemini credentials.

Coverage is reported on every CI run via `pytest --cov=src --cov-report=term-missing`.

## Disclaimer

This project is intended for educational, research, and learning purposes. The keyword-match score and LLM-generated output are a starting point for your own judgment — not an ATS simulation, hiring recommendation, or guarantee of job-search outcomes. Always review generated content before using it.

## License

This project is licensed under the MIT License — see [LICENSE](https://github.com/MaithreshVaddi-27/Resume_Crew/blob/main/LICENSE) for the full text.
