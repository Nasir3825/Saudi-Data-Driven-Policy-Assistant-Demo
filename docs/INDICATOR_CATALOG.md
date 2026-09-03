# Indicator Catalogue and Required Calculations

Use this catalogue when completing `data/api_indicators.json`. Paste a complete DataSaudi `data.jsonrecords` URL into `url`; leave `params` empty. Field and filter names must exactly match the returned JSON.

| # | ID | Display name | Frequency | Dashboard unit | Calculation / rule |
|---:|---|---|---|---|---|
| 1 | `real_gdp_constant` | Real GDP at constant prices | Quarterly | SAR trillion | DataSaudi GDP in million SAR × `0.000001`; filter the confirmed total GDP activity |
| 2 | `real_gdp_oil` | Real GDP oil activities | Quarterly | SAR trillion | Million SAR × `0.000001`; exact oil-activities filter |
| 3 | `real_gdp_non_oil` | Real GDP non-oil activities | Quarterly | SAR trillion | Million SAR × `0.000001`; exact non-oil-activities filter |
| 4 | `cpi_inflation` | CPI inflation | Monthly | percent YoY | Use measure `Inflation rate`; filter `Main Division = General Index`; no multiplier |
| 5 | `housing_cpi_inflation` | Housing CPI inflation | Monthly | percent YoY | Use `Inflation rate`; filter exact housing division; no multiplier |
| 6 | `wpi_inflation` | WPI inflation | Monthly | percent YoY | Use `Wholesale Price Index Growth`; filter the confirmed general category |
| 7 | `producer_price_index` | Producer Price Index | Monthly | index points | Use `Producer Price Index`; filter confirmed total activity if the response is disaggregated |
| 8 | `industrial_production_growth` | Industrial Production Index monthly growth | Monthly | percent MoM | Use the monthly-change measure; filter confirmed total activity |
| 9 | `pmi` | Purchasing Managers' Index | Monthly | index points | Direct value; no calculation |
| 10 | `business_confidence` | Business Confidence Index | Monthly | index points | Filter confirmed overall/total sector; no multiplier |
| 11 | `merchandise_exports` | Merchandise exports | Monthly | SAR billion | DataSaudi million SAR × `0.001` |
| 12 | `merchandise_imports` | Merchandise imports | Monthly | SAR billion | DataSaudi million SAR × `0.001` |
| 13 | `merchandise_trade_balance` | Merchandise trade balance | Monthly | SAR billion | DataSaudi million SAR × `0.001`; or exports minus imports if no balance measure exists |
| 14 | `saudi_unemployment` | Saudi unemployment rate | Quarterly | percent | Filter `Nationality = Saudi`; no multiplier |
| 15 | `overall_unemployment` | Overall unemployment rate | Quarterly | percent | Use the confirmed total-nationality record; do not average Saudi/non-Saudi rates |
| 16 | `total_population` | Total population | Annual | people | Prefer a total measure queried only by year; otherwise sum mutually exclusive components once |
| 17 | `total_tourists` | Total tourists | Annual | million tourists | Thousand tourists × `0.001`; prefer total tourist-type record or sum inbound + domestic once |
| 18 | `inbound_tourists` | Inbound tourists | Annual | million tourists | Thousand tourists × `0.001`; filter exact inbound tourist type |
| 19 | `domestic_tourists` | Domestic tourists | Annual | million tourists | Thousand tourists × `0.001`; filter exact domestic tourist type |
| 20 | `tourism_direct_gdp` | Tourism direct contribution to GDP | Annual | percent of GDP | Decimal ratio × `100`; do not multiply if API already returns percentage points |
| 21 | `fdi_inflows` | Foreign direct investment inflows | Quarterly/Annual | SAR billion | Million SAR × `0.001`; use total sector or aggregate mutually exclusive sectors |
| 22 | `current_account_balance` | Current-account balance | Quarterly | SAR billion | Million SAR × `0.001`; direct balance measure |
| 23 | `reserve_assets` | Reserve assets | Quarterly | SAR billion | Million SAR × `0.001`; use total reserve assets |
| 24 | `labour_force_participation` | Labour-force participation rate | Quarterly | percent | Use total population group or required Saudi group; no averaging of subgroup rates |
| 25 | `non_oil_exports` | Non-oil exports | Monthly | SAR billion | Million SAR × `0.001`; direct non-oil export measure |
| 26 | `tourism_expenditure` | Tourism expenditure | Annual | SAR billion | Million SAR × `0.001`; specify inbound, domestic or total consistently |
| 27 | `oil_production_or_exports` | Oil production or oil-export value | Monthly | million barrels/day or SAR billion | Do not mix volume and value; value in million SAR × `0.001` |
| 28 | `government_revenue_expenditure` | Government revenue / expenditure | Quarterly/Annual | SAR billion | Million SAR × `0.001`; keep revenue and expenditure as separate entries if both are required |

## Multiplier reference

| Source unit | Dashboard unit | `value_multiplier` |
|---|---|---:|
| Million SAR | SAR billion | `0.001` |
| Million SAR | SAR trillion | `0.000001` |
| Thousand tourists | Million tourists | `0.001` |
| Decimal ratio | Percent | `100` |
| Same source and dashboard unit | Same unit | `1` |

## Aggregation rules

- Prefer a published total record over summing components.
- Sum only mutually exclusive categories.
- Never sum a total together with its components.
- Never average subgroup unemployment, inflation or participation rates unless official weights are available.
- For trade balance, prefer the official balance measure; otherwise calculate exports minus imports using matching periods and units.
