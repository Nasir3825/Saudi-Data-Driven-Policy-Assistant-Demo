from types import SimpleNamespace

from src.indicator_api import fetch_indicator, load_api_registry


def test_registry_has_one_entry_for_each_selected_indicator():
    registry = load_api_registry()
    assert len(registry) == 20
    assert all(item["enabled"] for item in registry)


def test_fetch_indicator_maps_a_generic_json_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": [{"period": "2026-07-31", "value": "1.8"}]}

    monkeypatch.setattr("src.indicator_api.requests.get", lambda *args, **kwargs: FakeResponse())
    entry = {
        "id": "cpi_inflation",
        "indicator": "CPI inflation",
        "enabled": True,
        "api_type": "json",
        "url": "https://example.gov/api/cpi",
        "records_path": "data",
        "date_field": "period",
        "value_field": "value",
        "frequency": "Monthly",
        "unit": "percent YoY",
        "category": "Prices",
        "source_name": "Example official source",
        "source_url": "https://example.gov/cpi",
    }
    frame = fetch_indicator(entry)
    assert frame.loc[0, "indicator"] == "CPI inflation"
    assert frame.loc[0, "value"] == 1.8
