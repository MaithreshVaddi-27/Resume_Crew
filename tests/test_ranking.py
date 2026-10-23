from pathlib import Path

from resume_crew import pipeline


def test_score_resume_path_converts_errors_and_formats_sorted_table(monkeypatch) -> None:
    monkeypatch.setattr(pipeline, "extract_text", lambda path: Path(path).name)

    def score(text: str, *_args: object) -> tuple[float, str]:
        if text == "broken.md":
            raise RuntimeError
        return 78.0, "Strong match"

    monkeypatch.setattr(pipeline, "run_llm_match_score", score)

    high = pipeline.score_resume_path(Path("A|resume.pdf"), "job", object())
    low = pipeline.score_resume_path(Path("broken.md"), "job", object())

    report = pipeline.format_resume_ranking([low, high])
    assert "| 1 | A\\|resume.pdf | 78% | Strong match |" in report
    assert "| 2 | broken.md | -- | (unknown error) |" in report
