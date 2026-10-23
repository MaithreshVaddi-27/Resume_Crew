"""Allow ``python -m resume_crew`` as a CLI entry point."""

from __future__ import annotations

from .cli import main


def _entry() -> int:
    main()
    return 0


if __name__ == "__main__":
    raise SystemExit(_entry())
