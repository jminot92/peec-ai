# PEEC Action Room

Streamlit app for exploring PEEC AI answer data while the next insight layer is being rebuilt.

## What the app does

- pulls source URL data directly from the PEEC Customer API
- lets you choose one or more PEEC projects directly in the interface
- classifies rows into owned, competitor, and external influence
- weights API rows using `usage_count` so aggregated report rows behave like observations
- shows a baseline PEEC workspace with filters, source mix, top domains, and raw filtered rows
- exports the currently filtered PEEC dataset as CSV

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

The app supports these fetch windows in the UI:

- `7` days
- `14` days
- `30` days
- `60` days
- `90` days
- custom date range

Start narrow and use the custom range only when you need a broader audit.

## Streamlit secrets

For Streamlit Community Cloud, add these secrets:

```toml
PEEC_API_KEY = "your-api-key"
PEEC_PROJECT_ID = "optional-project-id"
PEEC_API_BASE_URL = "https://api.peec.ai/customer/v1"
PEEC_OWNED_DOMAINS = "mediaworks.co.uk"
```

`PEEC_OWNED_DOMAINS` is optional and is now configured through secrets only, not through the sidebar.

An example file is included at `.streamlit/secrets.toml.example`.

## Run locally

```powershell
cd "C:\Users\JackMinot\OneDrive - MEDIAWORKS UK LTD\Documents\Python Scripts\Peec_integration"
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Current state

- The previous weekly action and tabbed insight layer has been removed.
- The app is currently a baseline PEEC data workspace so new insight modules can be added one by one.
- API rows are weighted by `usage_count` when available.
