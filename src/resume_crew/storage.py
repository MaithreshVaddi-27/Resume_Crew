"""Output directory management."""

from __future__ import annotations

import json
import math
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import OUTPUT_ROOT

META_FILENAME = "run_meta.json"


def slugify(value: str, max_length: int = 48) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:max_length].strip("-") or "unknown"


def create_run_directory(
    candidate_name: str,
    job_title: str,
    output_dir: Path | str | None = None,
) -> tuple[Path, str]:
    """Create a fresh, uniquely-named directory for a report run.

    By default the directory is created under ``output/`` (project root).
    Passing ``output_dir`` overrides that location (used by --output).
    """
    # Human-readable timestamp instead of an opaque Unix epoch number.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    slug = f"{slugify(candidate_name)}__{slugify(job_title)}__{timestamp}"
    root = Path(output_dir) if output_dir is not None else OUTPUT_ROOT
    suffix = 0
    while True:
        directory = root / (slug if suffix == 0 else f"{slug}-{suffix}")
        try:
            directory.mkdir(parents=True, exist_ok=False)
            return directory, timestamp
        except FileExistsError:
            suffix += 1


def write_run_files(
    candidate: str,
    job_title: str,
    files: dict[str, str],
    output_dir: Path | str | None = None,
    score: float | None = None,
) -> tuple[Path, str]:
    """Write a complete run before making it visible to History or users."""
    directory, timestamp = create_run_directory(candidate, job_title, output_dir)
    staging = directory.with_name(f".{directory.name}.tmp")
    try:
        staging.mkdir()
        for name, content in files.items():
            (staging / name).write_text(content, encoding="utf-8")
        if score is not None:
            write_run_meta(
                staging, candidate, job_title, score, timestamp, published_name=directory.name
            )
        staging.rename(directory)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        directory.rmdir()
        raise
    return directory, timestamp


def write_run_meta(
    directory: Path,
    candidate: str,
    job_title: str,
    score: float,
    timestamp: str,
    published_name: str | None = None,
) -> None:
    """Write a small JSON sidecar so History/trend views don't need to re-parse Markdown.

    ``published_name`` records the final (published) run directory name. When
    writes are staged under a temporary ``.name.tmp`` directory before being
    renamed into place, recording the staging name would make
    :func:`list_report_runs` reject the run because its directory-name guard
    would never match.
    """
    meta = {
        "candidate": candidate,
        "job_title": job_title,
        "score": score,
        "timestamp": timestamp,
        "directory": published_name or directory.name,
    }
    (directory / META_FILENAME).write_text(json.dumps(meta, indent=2), encoding="utf-8")


def list_report_runs(limit: int = 50) -> list[dict[str, Any]]:
    """Return metadata for past runs under output/, most recent first.

    Runs without a meta sidecar (e.g. created by an older version) are skipped
    rather than crashing the History tab.
    """
    if not OUTPUT_ROOT.is_dir():
        return []

    runs: list[dict[str, Any]] = []
    for directory in OUTPUT_ROOT.iterdir():
        if not directory.is_dir():
            continue
        meta_path = directory / META_FILENAME
        if not meta_path.is_file():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                continue
            if meta.get("directory", directory.name) != directory.name:
                continue
            if not all(
                isinstance(meta.get(key), str) for key in ("candidate", "job_title", "timestamp")
            ):
                continue
            score = meta.get("score")
            if (
                not isinstance(score, (int, float))
                or not math.isfinite(score)
                or not 0 <= score <= 100
            ):
                continue
            meta["path"] = str(directory)
            runs.append(meta)
        except (json.JSONDecodeError, OSError):
            continue

    runs.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
    return runs[:limit]


def read_run_report(directory: str) -> dict[str, str]:
    """Read Markdown files from one direct child run directory under output/."""
    path = Path(directory).resolve()
    output_root = OUTPUT_ROOT.resolve()
    if path.parent != output_root:
        raise ValueError(f"'{path}' is not a report run under '{output_root}'.")
    if not path.is_dir():
        raise NotADirectoryError(f"'{path}' is not a directory.")
    files: dict[str, str] = {}
    for md_file in sorted(path.glob("*.md")):
        files[md_file.name] = md_file.read_text(encoding="utf-8", errors="replace")
    if not files:
        raise FileNotFoundError(f"No report files found in '{path}'.")
    return files
