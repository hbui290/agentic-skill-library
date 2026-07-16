from skill_registry.text import jaccard, tokenize


def test_tokenize_is_lowercase_ascii_and_deterministic():
    assert tokenize("PDF / Code-Review v2") == {"pdf", "code", "review", "v2"}


def test_jaccard_handles_empty_sets():
    assert jaccard(set(), set()) == 0.0
    assert jaccard({"pdf"}, set()) == 0.0


def test_jaccard_reports_overlap():
    assert jaccard({"code", "review"}, {"review", "security"}) == 1 / 3
