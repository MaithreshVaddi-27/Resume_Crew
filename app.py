"""Backward-compatible shim: run the Gradio UI from the project root.

Delegates to :mod:`resume_crew.app.main`. Preferred entry points are
``python -m resume_crew.app.main`` or ``python app.py`` (this shim).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from resume_crew.app.main import main  # noqa: E402

if __name__ == "__main__":
    main()
