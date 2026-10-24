from resume_crew.scoring import keyword_match_score


def test_keyword_score_uses_whole_terms() -> None:
    result = keyword_match_score("We are ongoing with a maintainer.", "Go AI")
    assert result.score == 0.0


def test_keyword_score_matches_normalized_terms() -> None:
    result = keyword_match_score("Python, SQL and data analysis", "Python SQL data")
    assert result.score == 100.0


def test_single_char_r_is_captured_as_token() -> None:
    """ISSUE-17: single-char uppercase `R` must now be extractable as a keyword."""
    result = keyword_match_score(
        "Proficient in R and Python for statistical analysis", "R Python SAS"
    )
    # R and Python should both match; SAS should not.
    assert "r" in result.matched
    assert "python" in result.matched
    assert "sas" in result.missing


def test_keyword_match_fields_are_tuples() -> None:
    """BUG-06: matched and missing must be tuples (frozen dataclass consistency)."""
    result = keyword_match_score("Python developer", "Python Java SQL")
    assert isinstance(result.matched, tuple)
    assert isinstance(result.missing, tuple)


def test_highlight_resume_matches_escapes_html_and_wraps_marks() -> None:
    from resume_crew.scoring import highlight_resume_matches

    match = keyword_match_score("Expert in Python and <script>alert(1)</script>", "Python")
    html = highlight_resume_matches("Expert in Python and <script>alert(1)</script>", match)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<mark" in html
    assert "Python</mark>" in html


def test_format_keyword_score_renders_summary() -> None:
    from resume_crew.scoring import format_keyword_score

    match = keyword_match_score("Python engineer", "Python SQL Docker")
    summary = format_keyword_score(match)
    assert "**Score:**" in summary
    assert "`python`" in summary
    assert "`sql`" in summary
