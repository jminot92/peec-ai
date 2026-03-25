from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from peec_app.briefs.domain_types import build_domain_types_brief
from peec_app.briefs.url_types import build_url_types_brief
from peec_app.briefs.visibility import build_visibility_brief
from peec_app.briefs.visibility_common import competitor_options, default_competitor_selection
from peec_app.briefs.visibility_snapshot import available_snapshot_dates, build_visibility_snapshot_brief


PROMPT_PATH = Path(__file__).with_name("prompt.md")


@dataclass
class SlideBriefPackage:
    markdown: str
    file_name: str



def load_prompt_markdown() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()



def format_filter_values(values: list[str]) -> str:
    return ", ".join(values) if values else "All"



def dataframe_to_csv_block(dataframe: pd.DataFrame, max_rows: int = 12) -> str:
    if dataframe.empty:
        return "No rows"
    return dataframe.head(max_rows).to_csv(index=False).strip()



def build_slide_brief_package(
    df: pd.DataFrame,
    *,
    project_name: str,
    window: tuple[str, str],
    selected_models: list[str],
    selected_topics: list[str],
    selected_tags: list[str],
) -> SlideBriefPackage:
    competitors = competitor_options(df, project_name)
    selected_competitors = default_competitor_selection(competitors)
    visibility_brief = build_visibility_brief(df, project_name, selected_competitors)

    snapshot_dates = available_snapshot_dates(df, project_name)
    latest_snapshot = snapshot_dates[-1] if snapshot_dates else None
    snapshot_brief = (
        build_visibility_snapshot_brief(df, project_name, selected_competitors, latest_snapshot)
        if latest_snapshot is not None
        else None
    )
    domain_brief = build_domain_types_brief(df)
    url_brief = build_url_types_brief(df)

    prompt_markdown = load_prompt_markdown()
    context = f"""# Claude Slide Brief Package

## Instructions For Claude
{prompt_markdown}

## Working Context
- Project: {project_name}
- Window: {window[0]} to {window[1]}
- Rows in current filtered dataset: {len(df):,}
- Prompts in current filtered dataset: {df['prompt'].nunique():,}
- Models filter: {format_filter_values(selected_models)}
- Topics filter: {format_filter_values(selected_topics)}
- Tags filter: {format_filter_values(selected_tags)}
- Competitors used for visibility tables: {format_filter_values(selected_competitors)}
- Latest snapshot date: {latest_snapshot.date().isoformat() if latest_snapshot is not None else 'None'}

## AI Visibility Trend Summary
```csv
{dataframe_to_csv_block(visibility_brief.summary_table)}
```

## AI Visibility Trend Chart Data
```csv
{dataframe_to_csv_block(visibility_brief.chart_data, max_rows=40)}
```

## AI Visibility Snapshot Summary
```csv
{dataframe_to_csv_block(snapshot_brief.summary_table if snapshot_brief is not None else pd.DataFrame())}
```

## Domain Types Summary
```csv
{dataframe_to_csv_block(domain_brief.summary_table)}
```

## URL Types Summary
```csv
{dataframe_to_csv_block(url_brief.summary_table)}
```
"""

    safe_project = "-".join(project_name.lower().split()) or "project"
    file_name = f"{safe_project}-slide-brief-package.md"
    return SlideBriefPackage(markdown=context, file_name=file_name)



def render_slide_brief_package(
    df: pd.DataFrame,
    *,
    project_name: str,
    window: tuple[str, str],
    selected_models: list[str],
    selected_topics: list[str],
    selected_tags: list[str],
) -> None:
    st.subheader("Slide brief package")
    st.caption(
        "Download a markdown package for Claude. It contains the prompt instructions plus the current visibility, domain and URL tables from the app."
    )

    package = build_slide_brief_package(
        df,
        project_name=project_name,
        window=window,
        selected_models=selected_models,
        selected_topics=selected_topics,
        selected_tags=selected_tags,
    )

    st.download_button(
        "Download markdown package",
        package.markdown.encode("utf-8"),
        file_name=package.file_name,
        mime="text/markdown",
        use_container_width=True,
    )
    st.text_area(
        "Markdown package",
        value=package.markdown,
        height=680,
    )
