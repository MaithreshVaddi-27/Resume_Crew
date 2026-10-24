import os
from pathlib import Path

import pytest

from resume_crew import storage
from resume_crew.storage import create_run_directory, slugify, write_run_files


def test_write_run_files_removes_incomplete_run_on_failure(tmp_path: Path, monkeypatch) -> None:
    def fail_write(*_args, **_kwargs) -> int:
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", fail_write)
    with pytest.raises(OSError, match="disk full"):
        write_run_files("Jane Doe", "Engineer", {"report.md": "report"}, output_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_read_run_report_is_limited_to_direct_output_children(tmp_path: Path, monkeypatch) -> None:
    output_root = tmp_path / "output"
    run_directory = output_root / "run-1"
    run_directory.mkdir(parents=True)
    (run_directory / "report.md").write_text("synthetic report", encoding="utf-8")
    monkeypatch.setattr(storage, "OUTPUT_ROOT", output_root)

    assert storage.read_run_report(str(run_directory)) == {"report.md": "synthetic report"}

    outside_directory = tmp_path / "private"
    outside_directory.mkdir()
    (outside_directory / "secret.md").write_text("not read", encoding="utf-8")
    with pytest.raises(ValueError, match="not a report run"):
        storage.read_run_report(str(outside_directory))

    nested_directory = run_directory / "nested"
    nested_directory.mkdir()
    with pytest.raises(ValueError, match="not a report run"):
        storage.read_run_report(str(nested_directory))


def test_list_report_runs_skips_malformed_metadata(tmp_path: Path, monkeypatch) -> None:
    output_root = tmp_path / "output"
    output_root.mkdir()
    valid_run = output_root / "valid"
    valid_run.mkdir()
    (valid_run / "run_meta.json").write_text(
        '{"candidate":"Jane","job_title":"Engineer","timestamp":"20261024",'
        '"directory":"valid","score":75}',
        encoding="utf-8",
    )
    malformed_run = output_root / "malformed"
    malformed_run.mkdir()
    (malformed_run / "run_meta.json").write_text('{"score":"high"}', encoding="utf-8")
    mismatched_run = output_root / "mismatched"
    mismatched_run.mkdir()
    (mismatched_run / "run_meta.json").write_text(
        '{"candidate":"Other","job_title":"Engineer","timestamp":"20261024",'
        '"directory":"valid","score":80}',
        encoding="utf-8",
    )
    monkeypatch.setattr(storage, "OUTPUT_ROOT", output_root)

    assert [run["path"] for run in storage.list_report_runs()] == [str(valid_run)]


def test_slugify_is_filesystem_safe() -> None:
    assert slugify("A Candidate / ML & Data") == "a-candidate-ml-data"


def test_timestamp_is_human_readable(tmp_path: Path) -> None:
    """ISSUE-09: directory name must contain a readable date stamp, not a Unix epoch."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        _, timestamp = create_run_directory("Jane Doe", "Engineer")
        # Format must be YYYYMMDD_HHMMSS — all digits and one underscore.
        assert len(timestamp) == 15, f"Unexpected timestamp format: {timestamp!r}"
        assert timestamp[8] == "_", f"Expected underscore at position 8: {timestamp!r}"
        assert timestamp.replace("_", "").isdigit(), f"Non-digit chars in timestamp: {timestamp!r}"
    finally:
        os.chdir(original_cwd)


def test_auto_directory_name_contains_timestamp(tmp_path: Path) -> None:
    """Auto-generated directory slug should embed the human-readable timestamp."""
    # Run from tmp_path so the 'output/' folder lands inside tmp.
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        directory, timestamp = create_run_directory("Alice Smith", "Data Analyst")
        assert timestamp in directory.name, (
            f"Timestamp {timestamp!r} not found in dir name {directory.name!r}"
        )
    finally:
        os.chdir(original_cwd)


def test_repeat_run_gets_unique_directory(tmp_path: Path) -> None:
    """Two runs with the same candidate/role in the same second must not collide."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        first, _ = create_run_directory("Alice Smith", "Data Analyst")
        second, _ = create_run_directory("Alice Smith", "Data Analyst")
        assert first != second
        assert first.exists() and second.exists()
    finally:
        os.chdir(original_cwd)
