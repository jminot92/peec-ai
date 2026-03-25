# PEEC Brief Builder

Streamlit app for building client briefs from the PEEC API.

## Current brief

- `Visibility trend`
  - exportable summary table
  - exportable daily chart dataset
  - downloadable PNG line chart with transparent background for slides and decks
- `Visibility snapshot`
  - date-specific bar chart
  - exportable snapshot table
  - downloadable PNG bar chart with transparent background
- `Domain types`
  - rule-based domain-type summary
  - exportable summary table
  - downloadable PNG table in the branded grid style
- `URL types`
  - rule-based URL-type summary
  - exportable summary table
  - downloadable PNG table in the branded grid style

## Structure

- `app.py`: Streamlit entry point and orchestration
- `peec_app/peec_api.py`: PEEC API client and cached fetch helpers
- `peec_app/data.py`: PEEC row shaping, ownership classification and dataset filters
- `peec_app/briefs/visibility.py`: Brief 01 logic and rendering
- `peec_app/briefs/visibility_snapshot.py`: Brief 02 logic and rendering
- `peec_app/briefs/domain_types.py`: Brief 03 logic and rendering
- `peec_app/briefs/url_types.py`: Brief 04 logic and rendering
- `peec_app/briefs/visibility_common.py`: shared competitor and palette helpers
- `peec_app/renderers/png_table.py`: PNG table export helper
- `peec_app/styles.py`: shared Streamlit styling
- `peec_app/utils.py`: shared text/domain helpers

## Required secrets

```toml
PEEC_API_KEY = "your-api-key"
```

Optional overrides:

```toml
PEEC_API_BASE_URL = "https://api.peec.ai/customer/v1"
PEEC_OWNED_DOMAINS = "example.com"
```

## Run locally

```powershell
cd "C:\Users\JackMinot\OneDrive - MEDIAWORKS UK LTD\Documents\Python Scripts\Peec_integration"
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Notes

- The app is PEEC API only.
- The app only fetches when you click `Fetch latest PEEC data`.
- Ownership is inferred from PEEC brand metadata and can be overridden with `PEEC_OWNED_DOMAINS` if needed.
