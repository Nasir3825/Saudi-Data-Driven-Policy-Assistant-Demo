from __future__ import annotations

from datetime import datetime, timezone

from .retrieval import Evidence


def build_markdown_brief(
    question: str,
    answer: str,
    evidence: list[Evidence],
    response_mode: str = "Policy brief",
) -> str:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if response_mode == "Detailed policy analysis":
        document_title = "Saudi Data-Driven Policy Assistant — Detailed Policy Analysis"
        analysis_heading = "Detailed analysis"
    else:
        document_title = "Saudi Data-Driven Policy Assistant — Policy Brief"
        analysis_heading = "Policy brief"

    sources = "\n".join(
        f"- [{item.source_id}] [{item.title}]({item.source_url}) — "
        f"{item.source_name}, as of {item.as_of}"
        for item in evidence
    )

    return f"""# {document_title}

**Question:** {question}

**Response format:** {response_mode}

**Generated:** {generated}

## {analysis_heading}

{answer}

## Sources

{sources}

## Responsible-use note

This prototype supports evidence-based analysis and policy options. It does not replace official releases, expert review, or policy approval. Verify figures against the linked source before external use.
"""