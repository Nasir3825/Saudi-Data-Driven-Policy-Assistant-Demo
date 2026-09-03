from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class Evidence:
    source_id: str
    title: str
    text: str
    source_name: str
    source_url: str
    as_of: str
    score: float


class EvidenceRetriever:
    """Small, inspectable TF-IDF retriever suitable for a focused prototype."""

    def __init__(self, documents: list[dict]):
        if not documents:
            raise ValueError("At least one knowledge document is required")
        self.documents = documents
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            strip_accents="unicode",
            sublinear_tf=True,
        )
        corpus = [f"{d['title']} {d['text']}" for d in documents]
        self.matrix = self.vectorizer.fit_transform(corpus)

    def search(self, query: str, top_k: int = 5) -> list[Evidence]:
        cleaned = query.strip()
        if not cleaned:
            return []
        query_vector = self.vectorizer.transform([cleaned])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        order = scores.argsort()[::-1][: max(1, min(top_k, len(self.documents)))]
        results: list[Evidence] = []
        for rank, index in enumerate(order, start=1):
            document = self.documents[int(index)]
            results.append(
                Evidence(
                    source_id=f"S{rank}",
                    title=document["title"],
                    text=document["text"],
                    source_name=document["source_name"],
                    source_url=document["source_url"],
                    as_of=document["as_of"],
                    score=float(scores[index]),
                )
            )
        return results


def format_evidence(evidence: list[Evidence]) -> str:
    return "\n\n".join(
        f"[{item.source_id}] {item.title}\n{item.text}\n"
        f"Source: {item.source_name}; as of {item.as_of}; URL: {item.source_url}"
        for item in evidence
    )
