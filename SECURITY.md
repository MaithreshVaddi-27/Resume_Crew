# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in Resume Crew, please report it privately:

- **Email**: maithreshvaddi16@gmail.com
- **Subject**: `[SECURITY] Resume Crew — <short description>`

Please do not open a public GitHub issue for security vulnerabilities.

## Scope

In scope:
- Document extraction and parsing (PDF, DOCX, TXT, MD)
- LLM provider configuration and API key handling
- Output directory and report file writing
- Gradio UI and public-share authentication
- Dependency vulnerabilities

Out of scope:
- Vulnerabilities in third-party LLM providers (Ollama, MLX-LM, Gemini)
- Vulnerabilities in upstream dependencies (CrewAI, Gradio, pypdf, etc.)

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.4.x   | ✅        |
| < 1.4   | ❌        |

## Security practices

- `.env` is gitignored — never commit API keys.
- Telemetry is disabled by default (CrewAI, OpenTelemetry).
- Report files are written under `output/` which is gitignored.
- The UI does not expose server filesystem paths in success/error messages.
- Gradio public sharing requires both `GRADIO_AUTH_USER` and `GRADIO_AUTH_PASS`.