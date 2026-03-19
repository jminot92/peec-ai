# PEEC Action Room

Streamlit app for turning PEEC AI answer data into weekly SEO/content and DPR action lists.

## What the app does

- pulls source URL data directly from the PEEC Customer API
- lets you choose one or more PEEC projects directly in the interface
- classifies rows into owned, competitor, and external influence
- weights API rows using `usage_count` so aggregated report rows behave like observations
- calculates topic-level content gaps using rule-based logic
- shows owned pages already influencing answers
- shows competitor pages influencing answers
- shows external domains shaping answers for DPR
- generates prioritised weekly actions with a priority score
- exports combined, SEO/content, and DPR action lists as CSV

## PEEC API

The app can fetch directly from the PEEC Customer API using:

- `GET /prompts`
- `GET /topics`
- `GET /tags`
- `GET /models`
- `GET /brands`
- `POST /reports/urls`

You can use either:

- a project-scoped API key
- a company API key plus `project_id`

If the key can list projects, the app shows a project multiselect in the sidebar so you can choose live and pitch projects without editing secrets.

The app uses a fixed lookback preset in the UI: `7`, `14`, or `30` days. Default is `30` days.
This keeps the fetch predictable and avoids exposing raw connection controls in the interface.

## Streamlit secrets

For Streamlit Community Cloud, add these secrets:

```toml
PEEC_API_KEY = "your-api-key"
PEEC_PROJECT_ID = "optional-project-id"
PEEC_API_BASE_URL = "https://api.peec.ai/customer/v1"
PEEC_OWNED_DOMAINS = "mediaworks.co.uk"
```

An example file is included at `.streamlit/secrets.toml.example`.

## Run locally

```powershell
cd "C:\Users\JackMinot\OneDrive - MEDIAWORKS UK LTD\Documents\Python Scripts\Peec_integration"
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Notes on the rule engine

- Content actions are prioritised by citation volume, prompt gaps, competitor share, external share, and recent momentum.
- DPR actions are prioritised by external domain influence, low owned share, competitor pressure, model breadth, and recent momentum.
- Weekly momentum compares the latest 7 days in the selected range to the previous 7 days.
- API rows are weighted by `usage_count` when available.
