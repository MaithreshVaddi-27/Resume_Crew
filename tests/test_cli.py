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


def test_cli_has_no_word_export_flag() -> None:
    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--export-docx" not in option_strings


def test_cli_forces_tracing_and_telemetry_off() -> None:
    _disable_external_tracing()
    assert os.environ["CREWAI_TRACING_ENABLED"] == "false"
    assert os.environ["CREWAI_DISABLE_TELEMETRY"] == "true"
    assert os.environ["CREWAI_DISABLE_TRACKING"] == "true"
    assert os.environ["OTEL_SDK_DISABLED"] == "true"


def test_cli_has_no_history_flag() -> None:
    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--history" not in option_strings


def test_cli_has_no_print_ollama_env_flag() -> None:
    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--print-ollama-env" not in option_strings


def test_cli_has_output_flag(tmp_path: Path) -> None:
    """The --output flag lets callers direct reports to a chosen directory."""
    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--output" in option_strings
    assert "-o" in option_strings

    # Passing --output should not error and build_parser must still construct.
    args = parser.parse_args(["--output", str(tmp_path)])
    assert args.output == str(tmp_path)
