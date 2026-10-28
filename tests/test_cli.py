import os
from pathlib import Path

import pytest

from resume_crew.cli import _disable_external_tracing, build_parser
from resume_crew.config import Settings


@pytest.mark.parametrize(
    "setting, value",
    [
        ("OLLAMA_TIMEOUT", "0"),
        ("OLLAMA_TIMEOUT", "nan"),
        ("GRADIO_PORT", "0"),
        ("GRADIO_PORT", "65536"),
    ],
)
def test_settings_reject_invalid_numeric_ranges(monkeypatch, setting: str, value: str) -> None:
    monkeypatch.setenv(setting, value)
    with pytest.raises(ValueError):
        Settings.from_env()


@pytest.mark.parametrize(
    ("username", "password"),
    [(None, None), ("resume-user", None), (None, "strong-password")],
)
def test_gradio_share_requires_both_auth_values(
    monkeypatch, username: str | None, password: str | None
) -> None:
    monkeypatch.setenv("GRADIO_SHARE", "true")
    if username is None:
        monkeypatch.delenv("GRADIO_AUTH_USER", raising=False)
    else:
        monkeypatch.setenv("GRADIO_AUTH_USER", username)
    if password is None:
        monkeypatch.delenv("GRADIO_AUTH_PASS", raising=False)
    else:
        monkeypatch.setenv("GRADIO_AUTH_PASS", password)

    with pytest.raises(ValueError, match="requires both GRADIO_AUTH_USER and GRADIO_AUTH_PASS"):
        Settings.from_env()


def test_gradio_share_accepts_both_auth_values(monkeypatch) -> None:
    monkeypatch.setenv("GRADIO_SHARE", "true")
    monkeypatch.setenv("GRADIO_AUTH_USER", "resume-user")
    monkeypatch.setenv("GRADIO_AUTH_PASS", "strong-password")

    settings = Settings.from_env()

    assert settings.auth == ("resume-user", "strong-password")


def test_cli_forces_tracing_and_telemetry_off() -> None:
    _disable_external_tracing()
    assert os.environ["CREWAI_TRACING_ENABLED"] == "false"
    assert os.environ["CREWAI_DISABLE_TELEMETRY"] == "true"
    assert os.environ["CREWAI_DISABLE_TRACKING"] == "true"
    assert os.environ["OTEL_SDK_DISABLED"] == "true"


@pytest.mark.parametrize("flag", ["--export-docx", "--history", "--print-ollama-env"])
def test_cli_has_no_removed_flags(flag: str) -> None:
    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert flag not in option_strings


def test_cli_has_output_flag(tmp_path: Path) -> None:
    """The --output flag lets callers direct reports to a chosen directory."""
    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--output" in option_strings
    assert "-o" in option_strings

    # Passing --output should not error and build_parser must still construct.
    args = parser.parse_args(["--output", str(tmp_path)])
    assert args.output == str(tmp_path)


def test_cli_check_hardware_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["--check-hardware"])
    assert args.check_hardware is True


def test_cli_rank_resumes_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["--rank-resumes", "./resumes", "--jd", "./job.pdf"])
    assert args.rank_resumes == "./resumes"
    assert args.job_description == "./job.pdf"
