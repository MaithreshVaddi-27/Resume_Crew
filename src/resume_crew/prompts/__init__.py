"""Versioned prompt store for Resume Crew agents.

Each prompt follows the CRAFT framework:

- **C**ontext — background and input assumptions
- **R**ole — who the agent is
- **A**ction — the concrete task
- **F**ormat — required output shape
- **T**one — voice and restraint

Plus negative constraints and few-shot grounding where fabrication risk is
high. Prompts are loaded from disk at runtime so they can be versioned,
A/B tested, and edited without touching Python code.
"""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    """Load a prompt template by filename (without .md extension)."""
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


__all__ = ["load_prompt"]
