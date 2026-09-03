"""Config-driven live API fetching for selected Saudi economic indicators.

Keep endpoint URLs and public query parameters in data/api_indicators.json.
Keep API keys only in environment variables or Streamlit Secrets.
"""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit, urlunsplit

import pandas as pd
import requests

from .config import DATA_DIR

REQUIRED_CONFIG_FIELDS = {
    "id",
    "indicator",
    "enabled",
    "api_type",
    "url",
    "records_path",
    "date_field",
    "value_field",
    "frequency",
    "unit",
    "source_name",
    "source_url",
}

INDICATOR_NAME_ALIASES = {
    "real gdp at constant price": "Real GDP at constant prices",
    "real gdp at constant prices": "Real GDP at constant prices",
}


class IndicatorAPIError(RuntimeError):
    """Raised when one configured indicator endpoint cannot be read safely."""


def canonical_indicator_name(name: object) -> str:
    """Map known spelling variants to one dashboard indicator name."""
    cleaned = " ".join(str(name).strip().split())
    return INDICATOR_NAME_ALIASES.get(cleaned.casefold(), cleaned)


def _canonicalize_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "indicator" in result.columns:
        result["indicator"] = result["indicator"].map(canonical_indicator_name)
    return result


def load_api_registry(path: Path | None = None) -> list[dict[str, Any]]:
    """Load and validate the editable indicator endpoint registry."""
    target = path or DATA_DIR / "api_indicators.json"
    with target.open("r", encoding="utf-8") as handle:
        registry = json.load(handle)
    if not isinstance(registry, list):
        raise ValueError("api_indicators.json must contain a JSON list")
    ids: set[str] = set()
    for entry in registry:
        missing = REQUIRED_CONFIG_FIELDS.difference(entry)
        if missing:
            raise ValueError(f"API configuration is missing fields: {sorted(missing)}")
        if entry["id"] in ids:
            raise ValueError(f"Duplicate API configuration id: {entry['id']}")
        ids.add(entry["id"])
    return registry


def _value_at(item: Any, dotted_path: str) -> Any:
    """Read a nested JSON field such as 'observation.period.value'."""
    current = item
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise IndicatorAPIError(f"Field '{dotted_path}' was not found in the API response")
        current = current[part]
    return current


def _records_at(payload: Any, dotted_path: str) -> list[dict[str, Any]]:
    if not dotted_path:
        records = payload
    else:
        records = _value_at(payload, dotted_path)
    if not isinstance(records, list):
        raise IndicatorAPIError("records_path must point to a JSON list")
    if not all(isinstance(record, dict) for record in records):
        raise IndicatorAPIError("Every API record must be a JSON object")
    return records



def _available_values(records: list[dict[str, Any]], field: str, max_values: int = 30) -> list[str]:
    """Return unique non-null values for one API field to help diagnose exact-match filters."""
    values: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        try:
            value = _value_at(record, field)
        except IndicatorAPIError:
            continue
        if value is None:
            continue
        cleaned = str(value).strip()
        if cleaned and cleaned not in values:
            values.append(cleaned)
        if len(values) >= max_values:
            break
    return values


def _returned_fields(records: list[dict[str, Any]], sample_size: int = 20) -> list[str]:
    """Return unique top-level field names from a sample of API records."""
    fields: set[str] = set()
    for record in records[:sample_size]:
        if isinstance(record, dict):
            fields.update(str(key) for key in record.keys())
    return sorted(fields)


def _headers(entry: dict[str, Any]) -> dict[str, str]:
    headers = {str(k): str(v) for k, v in entry.get("headers", {}).items()}
    for item in entry.get("secret_headers", []):
        variable = item["env"]
        secret = os.getenv(variable)
        if not secret:
            raise IndicatorAPIError(
                f"Missing secret '{variable}'. Add it to Streamlit Secrets before enabling {entry['id']}."
            )
        headers[item["name"]] = f"{item.get('prefix', '')}{secret}"
    return headers


def _fetch_records(entry: dict[str, Any], timeout: float) -> list[dict[str, Any]]:
    """Fetch one endpoint, optionally following DataSaudi limit/offset pages."""
    parsed = urlsplit(entry["url"])
    request_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query if not entry.get("pagination") else "", parsed.fragment))
    base_params = dict(parse_qsl(parsed.query, keep_blank_values=True)) if entry.get("pagination") else {}
    base_params.update(entry.get("params", {}))
    pagination = entry.get("pagination")
    all_records: list[dict[str, Any]] = []
    page = 0
    while True:
        params = dict(base_params)
        if pagination:
            page_size = int(pagination.get("page_size", 500))
            offset = page * page_size
            params[pagination.get("parameter", "limit")] = f"{page_size},{offset}"
        try:
            response = requests.get(request_url, params=params, headers=_headers(entry), timeout=timeout)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise IndicatorAPIError(f"{entry['id']} request failed: {exc}") from exc
        except ValueError as exc:
            raise IndicatorAPIError(f"{entry['id']} did not return valid JSON") from exc
        records = _records_at(payload, entry.get("records_path", ""))
        all_records.extend(records)
        if not pagination or len(records) < page_size:
            break
        page += 1
        if page >= int(pagination.get("max_pages", 100)):
            raise IndicatorAPIError(f"{entry['id']} reached max_pages before the API finished")
    return all_records


def fetch_indicator(entry: dict[str, Any], timeout: float = 30.0) -> pd.DataFrame:
    """Fetch one enabled JSON endpoint and return standardised observations.

    The endpoint can be any official JSON API. `records_path`, `date_field`, and
    `value_field` are the only mappings normally required to adapt a new API.
    """
    if not entry.get("enabled"):
        raise IndicatorAPIError(f"{entry['id']} is disabled in api_indicators.json")
    if entry.get("api_type") != "json":
        raise IndicatorAPIError("Only api_type='json' is supported by this project")
    if not entry.get("url"):
        raise IndicatorAPIError(f"Add an official endpoint URL for {entry['id']}")

    records = _fetch_records(entry, timeout)

    if not records:
        raise IndicatorAPIError(
            f"{entry['id']}: DataSaudi API returned zero records. URL: {entry.get('url')}"
        )

    record_filters = entry.get("record_filters", {}) or {}
    for field, expected in record_filters.items():
        fields_before_filter = _returned_fields(records)
        if field not in fields_before_filter:
            raise IndicatorAPIError(
                f"{entry['id']}: filter field {field!r} does not exist in the API response. "
                f"Actual returned fields: {fields_before_filter}"
            )

        available = _available_values(records, field)
        expected_normalized = str(expected).strip().casefold()

        filtered_records = [
            record
            for record in records
            if str(_value_at(record, field)).strip().casefold() == expected_normalized
        ]

        if not filtered_records:
            raise IndicatorAPIError(
                f"{entry['id']}: no observations matched filter "
                f"{field}={expected!r}. Actual values returned for {field!r}: {available}"
            )

        records = filtered_records

    returned_fields = _returned_fields(records)
    date_field = entry["date_field"]
    value_field = entry["value_field"]

    if date_field not in returned_fields:
        raise IndicatorAPIError(
            f"{entry['id']}: configured date_field {date_field!r} was not returned by the API. "
            f"Actual returned fields: {returned_fields}"
        )

    if value_field not in returned_fields:
        raise IndicatorAPIError(
            f"{entry['id']}: configured value_field {value_field!r} was not returned by the API. "
            f"Actual returned fields: {returned_fields}"
        )

    rows: list[dict[str, Any]] = []
    for record in records:
        rows.append(
            {
                "indicator": canonical_indicator_name(entry["indicator"]),
                "date": _value_at(record, entry["date_field"]),
                "frequency": entry["frequency"],
                "value": _value_at(record, entry["value_field"]),
                "unit": entry["unit"],
                "category": entry.get("category", "Other"),
                "source_name": entry["source_name"],
                "source_url": entry["source_url"],
                "accessed_on": date.today().isoformat(),
                "notes": entry.get("notes", "Live API observation."),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise IndicatorAPIError(
            f"{entry['id']} returned no observations after parsing. "
            f"Configured date_field={entry.get('date_field')!r}, "
            f"value_field={entry.get('value_field')!r}, "
            f"record_filters={entry.get('record_filters', {})!r}"
        )
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame["value"] = pd.to_numeric(frame["value"], errors="raise")
    multiplier = float(entry.get("value_multiplier", 1.0))
    frame["value"] = frame["value"] * multiplier
    aggregation = entry.get("value_aggregation")
    if aggregation:
        method = aggregation.get("method", "sum")
        if method not in {"sum", "mean", "first", "max"}:
            raise IndicatorAPIError(f"Unsupported value_aggregation method: {method}")
        group_columns = aggregation.get("group_by", ["date"])
        metadata = {
            "indicator": "first", "frequency": "first", "unit": "first", "category": "first",
            "source_name": "first", "source_url": "first", "accessed_on": "first", "notes": "first",
        }
        grouped = frame.groupby(group_columns, as_index=False).agg({"value": method, **metadata})
        frame = grouped
    frame["accessed_on"] = pd.to_datetime(frame["accessed_on"])
    return frame.sort_values("date").reset_index(drop=True)


def fetch_enabled_indicators(registry: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch every enabled indicator independently so one failed API never stops the app."""
    frames: list[pd.DataFrame] = []
    status: list[dict[str, str]] = []
    for entry in registry:
        if not entry["enabled"]:
            status.append({"id": entry["id"], "indicator": entry["indicator"], "status": "Disabled"})
            continue
        try:
            frame = fetch_indicator(entry)
        except IndicatorAPIError as exc:
            status.append({
                "id": entry["id"],
                "indicator": entry["indicator"],
                "status": f"Failed: {exc}",
            })
        except Exception as exc:
            status.append({
                "id": entry["id"],
                "indicator": entry["indicator"],
                "status": f"Failed: {type(exc).__name__}: {exc}",
            })
        else:
            frames.append(frame)
            status.append({"id": entry["id"], "indicator": entry["indicator"], "status": f"Updated: {len(frame)} rows"})
    live = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return live, pd.DataFrame(status)


def merge_live_snapshot(packaged: pd.DataFrame, live: pd.DataFrame) -> pd.DataFrame:
    """Use the latest live value per indicator and keep packaged values as fallback."""
    if live.empty:
        return _canonicalize_indicators(packaged)
    packaged = _canonicalize_indicators(packaged)
    live = _canonicalize_indicators(live)
    latest_live = live.loc[live.groupby("indicator")["date"].idxmax()]
    remaining = packaged[~packaged["indicator"].isin(latest_live["indicator"])]
    merged = pd.concat([remaining, latest_live], ignore_index=True)
    return merged.loc[merged.groupby("indicator")["date"].idxmax()].sort_values("indicator").reset_index(drop=True)


def merge_live_series(packaged: pd.DataFrame, live: pd.DataFrame) -> pd.DataFrame:
    """Replace a packaged indicator series only when its live API returns it."""
    if live.empty:
        return _canonicalize_indicators(packaged)
    packaged = _canonicalize_indicators(packaged)
    live = _canonicalize_indicators(live)
    keep = packaged[~packaged["indicator"].isin(live["indicator"])]
    series_columns = ["indicator", "date", "value", "unit", "source_name", "source_url", "accessed_on"]
    merged = pd.concat([keep, live[series_columns]], ignore_index=True)
    return merged.drop_duplicates(["indicator", "date"], keep="last").sort_values(["indicator", "date"]).reset_index(drop=True)
