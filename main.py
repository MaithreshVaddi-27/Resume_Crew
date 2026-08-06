"""Compatibility entry point for Resume Matcher.

Run ``python main.py`` from a source checkout, or install the package and run
``resume-matcher``.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from resume_crew.cli import main


if __name__ == "__main__":
    main()
