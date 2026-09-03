from src.retrieval import EvidenceRetriever


def test_retriever_ranks_inflation_document_first():
    documents = [
        {"id": "1", "title": "Inflation", "text": "CPI inflation was 1.8 percent.", "source_name": "A", "source_url": "https://a.example", "as_of": "2026-01-01"},
        {"id": "2", "title": "Tourism", "text": "Tourist arrivals increased.", "source_name": "B", "source_url": "https://b.example", "as_of": "2026-01-01"},
    ]
    results = EvidenceRetriever(documents).search("What was CPI inflation?", top_k=1)
    assert results[0].title == "Inflation"
    assert results[0].source_id == "S1"


def test_empty_query_returns_no_evidence():
    documents = [{"id": "1", "title": "GDP", "text": "Real GDP", "source_name": "A", "source_url": "https://a.example", "as_of": "2026-01-01"}]
    assert EvidenceRetriever(documents).search("   ") == []

