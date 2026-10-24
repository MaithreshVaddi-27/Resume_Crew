from pathlib import Path

import pytest

from resume_crew import pipeline


@pytest.mark.parametrize("output", ["No score here", "SCORE: 101", "SCORE: -1"])
def test_parse_match_score_rejects_missing_or_out_of_range_scores(output: str) -> None:
    with pytest.raises(ValueError, match="score"):
        pipeline._parse_match_score(output)


def test_parse_match_score_accepts_zero_and_one_hundred() -> None:
    assert pipeline._parse_match_score("SCORE: 0\nNOTE: low") == (0.0, "low")
    assert pipeline._parse_match_score("SCORE: 100\nNOTE: high") == (100.0, "high")


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
