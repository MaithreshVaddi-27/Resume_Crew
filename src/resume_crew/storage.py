"""Output directory management."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path


def slugify(value: str, max_length: int = 48) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w\s-]", "", normalized).strip().lower()
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:max_length].strip("-") or "unknown"


def create_run_directory(candidate_name: str, job_title: str) -> tuple[Path, str]:
    """Create a fresh, uniquely-named directory under output/ for a report run."""
    # Human-readable timestamp instead of an opaque Unix epoch number.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    slug = f"{slugify(candidate_name)}__{slugify(job_title)}__{timestamp}"
    directory = Path("output") / slug
    suffix = 1
    while directory.exists():
        suffix += 1
        directory = Path("output") / f"{slug}-{suffix}"

    directory.mkdir(parents=True, exist_ok=False)
    return directory, timestamp
