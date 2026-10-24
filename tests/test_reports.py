import pytest

from resume_crew import pipeline
from resume_crew.app import workers
from resume_crew.pipeline import split_writer_output


def test_splits_expected_sections() -> None:
    bullets, guide = split_writer_output(
        "## Tailored Resume Bullets\n- A\n\n## Interview Prep Guide\n1. Q"
    )
    assert bullets == "- A"
    assert guide == "1. Q"


def test_rejects_malformed_writer_output() -> None:
    with pytest.raises(ValueError, match="invalid"):
        split_writer_output("Some advice")


def test_resume_builder_rejects_oversized_combined_source(monkeypatch) -> None:
    monkeypatch.setattr(workers, "MAX_EXTRACTED_CHARACTERS", 10)
    monkeypatch.setattr(
        workers, "_get_file_path", lambda file_obj: "resume.txt" if file_obj else ""
    )
    monkeypatch.setattr(workers, "extract_text", lambda _path: "123456")
    monkeypatch.setattr(
        pipeline,
        "build_llm",
        lambda *_args: (_ for _ in ()).throw(AssertionError("LLM must not be called")),
    )

    outputs = list(workers.build_resume_fn("resume.txt", "12345", "job.txt", "ollama"))

    assert len(outputs) == 1
    assert "exceed the 10-character limit" in outputs[0][0]
    assert outputs[0][1:] == ("", "", None, None)


def test_word_export_is_not_part_of_the_pipeline_module() -> None:
    import resume_crew.pipeline as pipeline

    assert not hasattr(pipeline, "export_docx")


def test_splits_with_crlf_line_endings() -> None:
    """BUG-05: CRLF line endings from some LLMs must not break section parsing."""
    text = (
        "## Tailored Resume Bullets\r\n- Bullet one\r\n\r\n## Interview Prep Guide\r\n1. Question"
    )
    bullets, guide = split_writer_output(text)
    assert "Bullet one" in bullets
    assert "Question" in guide


def test_splits_with_level_three_headings() -> None:
    """BUG-05: ### headings (level 3) must be accepted, not just ##."""
    text = "### Tailored Resume Bullets\n- B\n\n### Interview Prep Guide\n1. Q"
    bullets, guide = split_writer_output(text)
    assert bullets == "- B"
    assert guide == "1. Q"


def test_splits_with_spaced_heading_words() -> None:
    """BUG-05: extra whitespace inside heading text should still match."""
    text = "##  Tailored  Resume  Bullets \n- B\n\n##  Interview  Prep  Guide \n1. Q"
    bullets, guide = split_writer_output(text)
    assert "B" in bullets
    assert "Q" in guide
