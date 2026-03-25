from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

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
    markdown_file_name: str
    bundle_file_name: str
    excel_files: dict[str, bytes]
    bundle_zip: bytes



def load_prompt_markdown() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()



def format_filter_values(values: list[str]) -> str:
    return ", ".join(values) if values else "All"



def dataframe_to_csv_block(dataframe: pd.DataFrame, max_rows: int = 12) -> str:
    if dataframe.empty:
        return "No rows"
    return dataframe.head(max_rows).to_csv(index=False).strip()



def dataframe_to_excel_bytes(dataframe: pd.DataFrame, sheet_name: str) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name[:31] or "Data")
    return buffer.getvalue()



def build_bundle_zip(
    markdown: str,
    markdown_file_name: str,
    excel_files: dict[str, bytes],
) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(markdown_file_name, markdown.encode("utf-8"))
        for file_name, file_bytes in excel_files.items():
            archive.writestr(file_name, file_bytes)
    return buffer.getvalue()



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
    markdown_file_name = f"{safe_project}-slide-brief-package.md"
    excel_files = {
        f"{safe_project}-filtered-peec-rows.xlsx": dataframe_to_excel_bytes(df, "Filtered rows"),
        f"{safe_project}-visibility-trend-summary.xlsx": dataframe_to_excel_bytes(
            visibility_brief.summary_table,
            "Visibility trend",
        ),
        f"{safe_project}-visibility-trend-chart-data.xlsx": dataframe_to_excel_bytes(
            visibility_brief.chart_data,
            "Visibility chart data",
        ),
        f"{safe_project}-visibility-snapshot-summary.xlsx": dataframe_to_excel_bytes(
            snapshot_brief.summary_table if snapshot_brief is not None else pd.DataFrame(),
            "Visibility snapshot",
        ),
        f"{safe_project}-domain-types-summary.xlsx": dataframe_to_excel_bytes(
            domain_brief.summary_table,
            "Domain types",
        ),
        f"{safe_project}-url-types-summary.xlsx": dataframe_to_excel_bytes(
            url_brief.summary_table,
            "URL types",
        ),
    }
    bundle_file_name = f"{safe_project}-claude-package.zip"
    bundle_zip = build_bundle_zip(context, markdown_file_name, excel_files)
    return SlideBriefPackage(
        markdown=context,
        markdown_file_name=markdown_file_name,
        bundle_file_name=bundle_file_name,
        excel_files=excel_files,
        bundle_zip=bundle_zip,
    )



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
        "Download a Claude-ready package with the markdown brief plus Excel files for the filtered dataset and current visibility, domain and URL summaries."
    )

    package = build_slide_brief_package(
        df,
        project_name=project_name,
        window=window,
        selected_models=selected_models,
        selected_topics=selected_topics,
        selected_tags=selected_tags,
    )

    download_1, download_2 = st.columns(2)
    with download_1:
        st.download_button(
            "Download full Claude package",
            package.bundle_zip,
            file_name=package.bundle_file_name,
            mime="application/zip",
            use_container_width=True,
        )
    with download_2:
        st.download_button(
            "Download markdown only",
            package.markdown.encode("utf-8"),
            file_name=package.markdown_file_name,
            mime="text/markdown",
            use_container_width=True,
        )

    with st.expander("Files included in the package"):
        file_list = [package.markdown_file_name, *package.excel_files.keys()]
        st.markdown("\n".join(f"- `{file_name}`" for file_name in file_list))

    st.text_area(
        "Markdown package",
        value=package.markdown,
        height=680,
    )
