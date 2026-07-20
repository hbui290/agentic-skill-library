import pytest

from skill_registry.runtime import search_skills


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("youtube transcript", {"youtube-transcript", "youtube-full"}),
        ("technical documentation", {"docs-architect", "wiki-page-writer"}),
        ("pdf", {"pdf-official"}),
        (
            "spreadsheet",
            {"calc", "office-productivity", "googlesheets-automation"},
        ),
        (
            "code review",
            {"code-review-checklist", "code-review-excellence", "differential-review"},
        ),
        ("azure blob storage", {"azure-blob-storage"}),
        ("react performance optimization", {"react-best-practices"}),
        ("postgres read only queries", {"postgres-readonly-queries"}),
        ("api endpoint design", {"api-endpoint-builder", "api-designer"}),
        ("github pull request review", {"address-github-comments", "github"}),
        ("seo audit", {"seo-audit", "seo"}),
        ("saas pricing strategy", {"pricing", "pricing-strategy"}),
        ("youtube video summary", {"youtube-notetaker", "ingest-youtube"}),
        ("data visualization dashboard", {"dashboard-design"}),
        ("web research scraping", {"web-scraper", "efficient-web-research"}),
        ("typescript debugging", {"debugging-strategies", "debugging-toolkit"}),
        ("docker deployment", {"docker-expert", "deployment-engineer"}),
        ("email marketing copy", {"email-sequence", "copywriting"}),
        ("database migration", {"database-migration"}),
        ("incident response", {"incident-response-incident-response"}),
        ("accessibility ui review", {"ui-review", "ui-a11y"}),
        ("unit test pytest", {"pytest-skill", "unit-testing-test-generate"}),
        ("technical writing", {"documentation", "scientific-writing"}),
    ],
)
def test_fixed_query_has_expected_skill_in_top_five(repo_root, query, expected):
    matches = search_skills(repo_root, query, limit=5)["matches"]
    assert expected.intersection(candidate["load_name"] for candidate in matches)


@pytest.mark.parametrize(
    ("query", "canonical", "legacy"),
    [
        ("docx", "docx-official", "docx"),
        ("pdf", "pdf-official", "pdf"),
        ("pptx", "pptx-official", "pptx"),
        ("xlsx", "xlsx-official", "xlsx"),
    ],
)
def test_exact_office_duplicates_only_return_canonical(repo_root, query, canonical, legacy):
    matches = search_skills(repo_root, query, limit=50)["matches"]
    names = {candidate["load_name"] for candidate in matches}
    assert canonical in names
    assert legacy not in names
