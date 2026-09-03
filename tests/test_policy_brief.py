from src.policy_brief import build_markdown_brief
from src.retrieval import Evidence


def test_brief_contains_source_and_disclaimer():
    evidence = [Evidence("S1", "CPI", "CPI was 1.8%", "DataSaudi", "https://datasaudi.sa/en", "2026-08-30", 0.9)]
    brief = build_markdown_brief("Inflation?", "CPI was 1.8% [S1].", evidence)
    assert "## Sources" in brief
    assert "DataSaudi" in brief
    assert "does not replace official releases" in brief

