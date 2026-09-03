from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import DATA_DIR

REQUIRED_COLUMNS = {
    "indicator",
    "date",
    "frequency",
    "value",
    "unit",
    "source_name",
    "source_url",
    "accessed_on",
}


def load_snapshot(path: Path | None = None) -> pd.DataFrame:
    """Load and validate the verified point-in-time indicator snapshot."""
    target = path or DATA_DIR / "official_snapshot.csv"
    frame = pd.read_csv(target)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Snapshot is missing required columns: {sorted(missing)}")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["accessed_on"] = pd.to_datetime(frame["accessed_on"], errors="raise")
    frame["value"] = pd.to_numeric(frame["value"], errors="raise")
    return frame.sort_values(["indicator", "date"]).reset_index(drop=True)


def load_series(path: Path | None = None) -> pd.DataFrame:
    target = path or DATA_DIR / "official_series.csv"
    frame = pd.read_csv(target)
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["value"] = pd.to_numeric(frame["value"], errors="raise")
    return frame.sort_values(["indicator", "date"]).reset_index(drop=True)


def load_knowledge(path: Path | None = None) -> list[dict]:
    target = path or DATA_DIR / "knowledge_base.json"
    with target.open("r", encoding="utf-8") as handle:
        documents = json.load(handle)
    required = {"id", "title", "text", "source_name", "source_url", "as_of"}
    for document in documents:
        missing = required.difference(document)
        if missing:
            raise ValueError(f"Knowledge document is missing: {sorted(missing)}")
    return documents


def snapshot_documents(frame: pd.DataFrame) -> list[dict]:
    """Turn structured observations into retrievable evidence passages."""
    documents: list[dict] = []
    for index, row in frame.reset_index(drop=True).iterrows():
        date_label = row["date"].strftime("%B %Y") if row["frequency"] != "Annual" else str(row["date"].year)
        text = (
            f"{row['indicator']} was {row['value']:g} {row['unit']} in {date_label}. "
            f"Frequency: {row['frequency']}. {row.get('notes', '')}"
        ).strip()
        documents.append(
            {
                "id": f"snapshot-{index + 1}",
                "title": row["indicator"],
                "text": text,
                "source_name": row["source_name"],
                "source_url": row["source_url"],
                "as_of": row["accessed_on"].strftime("%Y-%m-%d"),
            }
        )
    return documents


def series_documents(
    frame: pd.DataFrame,
    snapshot: pd.DataFrame,
    observations_per_document: int = 80,
) -> list[dict]:
    """Turn complete indicator histories into compact retrievable documents."""
    if frame.empty:
        return []

    frequency_by_indicator = (
        snapshot.sort_values("date")
        .drop_duplicates("indicator", keep="last")
        .set_index("indicator")["frequency"]
        .to_dict()
    )
    documents: list[dict] = []
    cleaned = frame.dropna(subset=["indicator", "date", "value"]).copy()
    cleaned = cleaned.drop_duplicates(["indicator", "date"], keep="last")

    for indicator, indicator_frame in cleaned.groupby("indicator", sort=True):
        indicator_frame = indicator_frame.sort_values("date").reset_index(drop=True)
        frequency = frequency_by_indicator.get(indicator, "Historical")
        total_parts = max(1, (len(indicator_frame) + observations_per_document - 1) // observations_per_document)

        for part_number, start in enumerate(range(0, len(indicator_frame), observations_per_document), start=1):
            part = indicator_frame.iloc[start : start + observations_per_document]
            unit = str(part.iloc[-1]["unit"])
            observations = "; ".join(
                f"{format_period_label(row['date'], frequency)}: {row['value']:g} {row['unit']}"
                for _, row in part.iterrows()
            )
            first_period = format_period_label(part.iloc[0]["date"], frequency)
            last_period = format_period_label(part.iloc[-1]["date"], frequency)
            source_name = str(part.iloc[-1]["source_name"])
            source_url = str(part.iloc[-1]["source_url"])
            accessed = pd.to_datetime(part.iloc[-1]["accessed_on"], errors="coerce")
            as_of = accessed.strftime("%Y-%m-%d") if pd.notna(accessed) else last_period
            part_suffix = f" — history {part_number}/{total_parts}" if total_parts > 1 else " — complete history"
            documents.append(
                {
                    "id": f"series-{indicator.lower().replace(' ', '-')}-{part_number}",
                    "title": f"{indicator}{part_suffix}",
                    "text": (
                        f"Complete available {frequency.lower()} observations for {indicator}, "
                        f"covering {first_period} to {last_period}. Unit: {unit}. "
                        f"Observations: {observations}."
                    ),
                    "source_name": source_name,
                    "source_url": source_url,
                    "as_of": as_of,
                }
            )
    return documents


def build_evidence_documents(
    snapshot: pd.DataFrame,
    series: pd.DataFrame,
    knowledge: list[dict],
) -> list[dict]:
    """Combine definitions, full histories, and latest-only fallback indicators."""
    historical_indicators = set(series["indicator"].dropna().unique()) if not series.empty else set()
    latest_only = snapshot[~snapshot["indicator"].isin(historical_indicators)]
    return knowledge + series_documents(series, snapshot) + snapshot_documents(latest_only)


def latest_by_indicator(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[frame.groupby("indicator")["date"].idxmax()].reset_index(drop=True)


def format_period_label(date_value: object, frequency: str) -> str:
    """Return a compact reporting-period label suited to an indicator's frequency."""
    timestamp = pd.Timestamp(date_value)
    normalized_frequency = str(frequency).strip().lower()
    if normalized_frequency == "quarterly":
        quarter = ((timestamp.month - 1) // 3) + 1
        return f"Q{quarter} {timestamp.year}"
    if normalized_frequency == "monthly":
        return timestamp.strftime("%b'%Y")
    if normalized_frequency == "annual":
        return str(timestamp.year)
    return timestamp.strftime("%d %b %Y")
