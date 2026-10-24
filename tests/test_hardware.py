import pytest

from resume_crew.hardware import list_ollama_models, resolve_ollama_profile


def test_list_ollama_models_reads_model_names(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self) -> bytes:
            return b'{"models":[{"name":"qwen3:1.7b"},{"name":"gemma3:1b"}]}'

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: Response())
    assert list_ollama_models("http://localhost:11434") == ["gemma3:1b", "qwen3:1.7b"]


def test_list_ollama_models_handles_unexpected_payload(monkeypatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self) -> bytes:
            return b'{"models": null}'

    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: Response())
    assert list_ollama_models("http://localhost:11434") == []


def test_invalid_profile_is_rejected() -> None:
    with pytest.raises(ValueError, match="auto, cuda, mps, or cpu"):
        resolve_ollama_profile("invalid")


def test_auto_profile_returns_valid_device() -> None:
    profile = resolve_ollama_profile("auto")
    assert profile["name"] in {"cuda", "mps", "cpu"}
    assert profile["context"] > 0


def test_cpu_profile_returns_cpu() -> None:
    profile = resolve_ollama_profile("cpu")
    assert profile["name"] == "cpu"
