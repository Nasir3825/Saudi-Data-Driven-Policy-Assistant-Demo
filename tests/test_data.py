import pandas as pd

from src.data import build_evidence_documents, format_period_label, load_snapshot


def test_snapshot_schema_and_values():
    frame = load_snapshot()
    assert not frame.empty
    assert frame["value"].notna().all()
    assert frame["source_url"].str.startswith("https://").all()
    assert frame["indicator"].nunique() >= 10


def test_period_labels_follow_indicator_frequency():
    assert format_period_label(pd.Timestamp("2026-03-31"), "Quarterly") == "Q1 2026"
    assert format_period_label(pd.Timestamp("2026-07-31"), "Monthly") == "Jul'2026"
    assert format_period_label(pd.Timestamp("2025-12-31"), "Annual") == "2025"


def test_historical_series_is_added_to_assistant_evidence():
    snapshot = pd.DataFrame(
        [
            {
                "indicator": "CPI inflation",
                "date": pd.Timestamp("2026-02-28"),
                "frequency": "Monthly",
                "value": 2.0,
                "unit": "percent YoY",
                "source_name": "DataSaudi",
                "source_url": "https://datasaudi.sa/en",
                "accessed_on": pd.Timestamp("2026-09-02"),
                "notes": "Latest value",
            }
        ]
    )
    series = pd.DataFrame(
        [
            {"indicator": "CPI inflation", "date": pd.Timestamp("2026-01-31"), "value": 1.8, "unit": "percent YoY", "source_name": "DataSaudi", "source_url": "https://datasaudi.sa/en", "accessed_on": pd.Timestamp("2026-09-02")},
            {"indicator": "CPI inflation", "date": pd.Timestamp("2026-02-28"), "value": 2.0, "unit": "percent YoY", "source_name": "DataSaudi", "source_url": "https://datasaudi.sa/en", "accessed_on": pd.Timestamp("2026-09-02")},
        ]
    )

    documents = build_evidence_documents(snapshot, series, [])

    assert len(documents) == 1
    assert "Jan'2026: 1.8 percent YoY" in documents[0]["text"]
    assert "Feb'2026: 2 percent YoY" in documents[0]["text"]
