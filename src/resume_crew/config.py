"""Centralized configuration for Resume Crew.

Loads environment variables from .env (via python-dotenv, called by entry
points) and exposes typed, validated settings so that every module reads from
a single source of truth instead of calling os.getenv ad hoc.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

# Resolve the project root as the directory containing this file's parent
# package (src/resume_crew/config.py -> project root).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
OUTPUT_ROOT = PROJECT_ROOT / "output"

# Supported document extensions (kept in sync with document_reader.py).
SUPPORTED_DOCUMENT_EXTENSIONS = (".pdf", ".docx", ".txt", ".md")

# Default analysis limits.
MAX_INPUT_FILE_SIZE_MB = 15
MAX_EXTRACTED_CHARACTERS = 100_000

# Default LLM models.
DEFAULT_OLLAMA_MODEL = "gemma3:1b"
DEFAULT_MLX_MODEL = "mlx-community/Qwen3-4B-Instruct-2507-4bit"
DEFAULT_GEMINI_MODEL = "gemini/gemini-3.8-flash"

# Valid providers / hardware profiles.
VALID_PROVIDERS = ("ollama", "mlx", "gemini")
VALID_OLLAMA_PROFILES = ("auto", "cuda", "mps", "cpu")


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings."""

    provider: str
    ollama_base_url: str
    ollama_model: str
    mlx_model: str
    mlx_base_url: str
    ollama_timeout: float
    ollama_profile: str
    gemini_api_key: str | None
    gemini_model: str
    gradio_port: int
    gradio_share: bool
    gradio_auth_user: str | None
    gradio_auth_pass: str | None
    crewai_tracing: str
    crewai_disable_telemetry: str
    crewai_disable_tracking: str
    otel_sdk_disabled: str

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment, applying defaults and validation."""

        def _get(name: str, default: str = "") -> str:
            return os.getenv(name, default)

        provider = _get("LLM_PROVIDER", "mlx").strip().lower()
        if provider not in VALID_PROVIDERS:
            raise ValueError(f"LLM_PROVIDER must be one of {VALID_PROVIDERS}, got {provider!r}")

        try:
            ollama_timeout = float(_get("OLLAMA_TIMEOUT", "3.0"))
        except ValueError as exc:
            raise ValueError("OLLAMA_TIMEOUT must be a positive number of seconds.") from exc
        if not math.isfinite(ollama_timeout) or ollama_timeout <= 0:
            raise ValueError("OLLAMA_TIMEOUT must be a positive finite number of seconds.")

        try:
            gradio_port = int(_get("GRADIO_PORT", "7860"))
        except ValueError as exc:
            raise ValueError("GRADIO_PORT must be an integer from 1 to 65535.") from exc
        if not 1 <= gradio_port <= 65535:
            raise ValueError("GRADIO_PORT must be an integer from 1 to 65535.")

        ollama_profile = _get("OLLAMA_PROFILE", "auto").strip().lower()
        if ollama_profile not in VALID_OLLAMA_PROFILES:
            raise ValueError(
                f"OLLAMA_PROFILE must be one of {VALID_OLLAMA_PROFILES}, got {ollama_profile!r}"
            )

        gemini_api_key = _get("GEMINI_API_KEY") or None

        if provider == "gemini" and not gemini_api_key:
            raise ValueError("LLM_PROVIDER=gemini requires GEMINI_API_KEY to be set.")

        settings = cls(
            provider=provider,
            ollama_base_url=_get("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=_get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            mlx_model=_get("MLX_MODEL", DEFAULT_MLX_MODEL),
            mlx_base_url=_get("MLX_BASE_URL", "http://localhost:8080/v1"),
            ollama_timeout=ollama_timeout,
            ollama_profile=ollama_profile,
            gemini_api_key=gemini_api_key,
            gemini_model=_get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            gradio_port=gradio_port,
            gradio_share=_get("GRADIO_SHARE", "false").strip().lower() == "true",
            gradio_auth_user=_get("GRADIO_AUTH_USER") or None,
            gradio_auth_pass=_get("GRADIO_AUTH_PASS") or None,
            crewai_tracing=_get("CREWAI_TRACING_ENABLED", "false"),
            crewai_disable_telemetry=_get("CREWAI_DISABLE_TELEMETRY", "true"),
            crewai_disable_tracking=_get("CREWAI_DISABLE_TRACKING", "true"),
            otel_sdk_disabled=_get("OTEL_SDK_DISABLED", "true"),
        )
        settings.validate_sharing_auth()
        return settings

    def apply_telemetry_env(self) -> None:
        """Force CrewAI/OpenTelemetry telemetry off before crewai is imported."""
        os.environ["CREWAI_TRACING_ENABLED"] = self.crewai_tracing
        os.environ["CREWAI_DISABLE_TELEMETRY"] = self.crewai_disable_telemetry
        os.environ["CREWAI_DISABLE_TRACKING"] = self.crewai_disable_tracking
        os.environ["OTEL_SDK_DISABLED"] = self.otel_sdk_disabled

    @property
    def auth(self) -> tuple[str, str] | None:
        """Basic-auth credentials if both user and pass are configured."""
        if self.gradio_auth_user and self.gradio_auth_pass:
            return self.gradio_auth_user, self.gradio_auth_pass
        return None

    def validate_sharing_auth(self) -> None:
        """Require complete credentials before enabling Gradio public sharing."""
        if self.gradio_share and not self.auth:
            raise ValueError(
                "GRADIO_SHARE=true requires both GRADIO_AUTH_USER and GRADIO_AUTH_PASS."
            )


def load_settings() -> Settings:
    """Public entry point: load and return validated settings."""
    return Settings.from_env()
