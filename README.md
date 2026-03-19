# PEEC Action Room

Streamlit app for turning PEEC AI answer data into weekly SEO/content and DPR action lists.

## What the app does

- ingests PEEC data by topic, prompt, URL, source domain, model, date and competitor
- classifies rows into owned, competitor and external influence
- calculates topic-level content gaps using rule-based logic
- shows owned pages already influencing answers
- shows competitor pages influencing answers
- shows external domains shaping answers for DPR
- generates prioritised weekly actions with a priority score
- exports combined, SEO/content and DPR action lists as CSV

## Required columns

- `topic`
- `prompt`
- `url`
- `source_domain`
- `model`
- `date`
- `competitor`

## Optional columns

- `tag`
- `source_type`
- `answer_rank`

If `source_type` is not supplied, the app derives it with this logic:

- domain matches the owned domain list -> `owned`
- competitor is populated -> `competitor`
- otherwise -> `external`

## Run locally

```powershell
cd "C:\Users\JackMinot\OneDrive - MEDIAWORKS UK LTD\Documents\Python Scripts\Peec_integration"
python -m pip install -r requirements.txt
streamlit run app.py
```

## Notes on the rule engine

- Content actions are prioritised by citation volume, prompt gaps, competitor share, external share and recent momentum.
- DPR actions are prioritised by external domain influence, low owned share, competitor pressure, model breadth and recent momentum.
- Weekly momentum compares the latest 7 days in the selected range to the previous 7 days.
