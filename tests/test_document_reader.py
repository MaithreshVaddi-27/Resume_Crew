import sys
import types
from pathlib import Path

import pytest

from resume_crew import document_reader
from resume_crew.document_reader import extract_text


def test_pdf_extraction_stops_at_character_limit(tmp_path: Path, monkeypatch) -> None:
    extracted_pages = 0

    class Page:
        def extract_text(self) -> str:
            nonlocal extracted_pages
            extracted_pages += 1
            return "x" * 10

    class Reader:
        is_encrypted = False
        pages = [Page(), Page(), Page()]

    monkeypatch.setitem(
        sys.modules, "pypdf", types.SimpleNamespace(PdfReader=lambda *_args: Reader())
    )
    monkeypatch.setitem(
        sys.modules,
        "pypdf.errors",
        types.SimpleNamespace(PdfReadError=Exception),
    )
    monkeypatch.setattr(document_reader, "MAX_EXTRACTED_CHARACTERS", 15)
    path = tmp_path / "resume.pdf"
    path.write_bytes(b"synthetic")
    with pytest.raises(ValueError, match="analysis limit"):
        extract_text(str(path))
    assert extracted_pages == 2


def test_extract_text_replaces_invalid_utf8(tmp_path: Path) -> None:
    source = tmp_path / "resume.txt"
    source.write_bytes(b"Candidate \xff Name")
    assert "Candidate" in extract_text(str(source))


def test_rejects_unsupported_extension(tmp_path: Path) -> None:
    source = tmp_path / "resume.exe"
    source.write_text("not supported")
    with pytest.raises(ValueError, match="Unsupported"):
        extract_text(str(source))


def test_rejects_empty_file(tmp_path: Path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text("   \n\t  ")
    with pytest.raises(ValueError, match="No extractable text"):
        extract_text(str(source))


def test_rejects_non_existent_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="File not found"):
        extract_text(str(tmp_path / "does_not_exist.pdf"))
