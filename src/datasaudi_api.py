from __future__ import annotations

from typing import Any

import requests

BASE_URL = "https://api.datasaudi.sa/tesseract"
RESERVED = {"cube", "locale", "drilldowns", "measures", "limit"}


class DataSaudiAPIError(RuntimeError):
    pass


def list_cubes(timeout: float = 30.0) -> list[dict[str, Any]]:
    response = requests.get(f"{BASE_URL}/cubes", params={"locale": "en"}, timeout=timeout)
    response.raise_for_status()
    return response.json().get("cubes", [])


def query_cube(
    cube: str,
    drilldowns: list[str],
    measures: list[str],
    *,
    locale: str = "en",
    limit: int = 100,
    offset: int = 0,
    filters: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """Query a validated DataSaudi Tesseract cube using leaf-level names."""
    if not cube or not drilldowns or not measures:
        raise ValueError("cube, drilldowns, and measures are required")
    params: dict[str, str] = {
        "cube": cube,
        "locale": locale,
        "drilldowns": ",".join(drilldowns),
        "measures": ",".join(measures),
        "limit": f"{limit},{offset}",
    }
    for level, member in (filters or {}).items():
        if level in RESERVED:
            raise ValueError(f"Filter level conflicts with a reserved parameter: {level}")
        params[level] = str(member)
    try:
        response = requests.get(f"{BASE_URL}/data.jsonrecords", params=params, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DataSaudiAPIError(f"DataSaudi request failed: {exc}") from exc
    return response.json().get("data", [])

