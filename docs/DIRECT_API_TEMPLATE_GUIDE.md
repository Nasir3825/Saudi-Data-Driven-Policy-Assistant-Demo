# Direct DataSaudi API Template Guide

## Why the previous CPI result was incomplete

The inflation API returns more than 2,000 rows because every month contains the General Index and multiple components. Reading only `limit=500,0` stops in December 2015. The updated API engine requests offsets `0`, `500`, `1000`, and so on until the final short page, then applies the `General Index` filter.

## Paste a DataSaudi API into the project

1. Open `data/api_direct_entry_template.json`.
2. Copy the complete object.
3. Open `data/api_indicators.json`.
4. Locate the indicator object you want to replace.
5. Paste the copied object in its place.
6. Set a unique `id` and the dashboard `indicator` name.
7. Paste the complete DataSaudi URL into `url`. You can paste the URL directly from the browser, including `cube`, `drilldowns`, `measures`, and `locale`.
8. Keep `params` as `{}` when the complete query is already in `url`.
9. Open the URL in a browser and inspect one returned record.
10. Set `date_field` and `value_field` to the exact JSON field names.
11. If one response contains multiple categories, add their exact label under `record_filters`.
12. Set `value_multiplier` using `docs/INDICATOR_CATALOG.md`.
13. Use `value_aggregation` only when mutually exclusive components must be combined.
14. Change `enabled` to `true` only after completing these fields.
15. Commit the file on GitHub, allow Streamlit to redeploy, then select **Refresh enabled APIs**.
16. Check the **API Status** and **Evidence Explorer** tabs.

## Complete CPI example

```json
{
  "id": "cpi_inflation",
  "indicator": "CPI inflation",
  "enabled": true,
  "api_type": "json",
  "url": "https://api.datasaudi.sa/tesseract/data.jsonrecords?cube=gastat_inflation&drilldowns=Month%2CMain+Division&measures=Inflation+rate&locale=en",
  "params": {},
  "headers": {"Accept": "application/json"},
  "secret_headers": [],
  "records_path": "data",
  "pagination": {"parameter": "limit", "page_size": 500, "max_pages": 100},
  "record_filters": {"Main Division": "General Index"},
  "date_field": "Month",
  "value_field": "Inflation rate",
  "value_multiplier": 1,
  "value_aggregation": null,
  "frequency": "Monthly",
  "unit": "percent YoY",
  "category": "Prices",
  "source_name": "DataSaudi / GASTAT",
  "source_url": "https://datasaudi.sa/en",
  "notes": "General Index CPI annual inflation rate; all pages are fetched before filtering."
}
```

The tested history runs from January 2013 through July 2026. The July 2026 API value is approximately `1.8273`, displayed as `1.83 percent YoY` when rounded to two decimals.

## A component example

For housing CPI, use the same URL and fields but change the filter to the exact housing label appearing in the API response:

```json
"record_filters": {
  "Main Division": "Housing, Water, Electricity, Gas and Other Fuels"
}
```

Always copy the label from the API response because category wording can change.
