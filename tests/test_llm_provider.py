"""Tests for LLM provider selection in pipeline.build_llm."""

import pytest

from resume_crew.pipeline import build_llm


def test_build_mlx_constructs_openai_compatible_client(monkeypatch):
    """MLX provider should build a client pointed at the local server without network."""
    monkeypatch.setenv("LLM_PROVIDER", "mlx")
    monkeypatch.setenv("MLX_BASE_URL", "http://localhost:8080/v1")
    monkeypatch.setenv("MLX_MODEL", "mlx-community/Qwen3-4B-Instruct-2507-4bit")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    llm, provider = build_llm(provider="mlx")

    assert provider == "mlx"
    assert llm.base_url == "http://localhost:8080/v1"
    assert llm.api_key == "mlx-local"


def test_build_ollama_without_server_raises_clear_error(monkeypatch):
    """Ollama should fail fast with an actionable message when the server is down."""
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "gemma3:4b")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="Ollama is not reachable"):
        build_llm(provider="ollama")


def test_build_gemini_without_api_key_raises_clear_error(monkeypatch):
    """Gemini should fail fast asking for GEMINI_API_KEY when none is set."""
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_MODEL", "gemini/gemini-3.8-flash")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="requires GEMINI_API_KEY"):
        build_llm(provider="gemini")


def test_build_gemini_with_api_key_constructs_client(monkeypatch):
    """Gemini should build a client when an API key is present."""
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setenv("GEMINI_MODEL", "gemini/gemini-3.8-flash")

    llm, provider = build_llm(provider="gemini")

    assert provider == "gemini"
    assert llm.model == "gemini-3.8-flash"
    assert llm.api_key == "test-key-123"


def test_build_llm_defaults_to_settings_provider(monkeypatch):
    """With no provider argument, build_llm falls back to settings.provider."""
    monkeypatch.setenv("LLM_PROVIDER", "mlx")
    monkeypatch.setenv("MLX_BASE_URL", "http://localhost:8080/v1")
    monkeypatch.setenv("MLX_MODEL", "mlx-community/Qwen3-4B-Instruct-2507-4bit")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    llm, provider = build_llm()

    assert provider == "mlx"
