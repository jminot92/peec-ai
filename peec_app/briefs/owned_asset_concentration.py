from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from peec_app.briefs.insight_utils import format_count, format_percentage
from peec_app.briefs.url_types import compact_url_label
from peec_app.renderers.copy_table import render_copy_table_button


@dataclass
class OwnedAssetConcentrationBrief:
    summary_table: pd.DataFrame
    display_table: pd.DataFrame
    top_1_share: float
    top_3_share: float
    urls_for_half: int
    owned_urls: int


def _first_non_empty(values: pd.Series) -> str:
    for value in values.fillna("").astype(str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return ""


def build_owned_asset_concentration_brief(df: pd.DataFrame) -> OwnedAssetConcentrationBrief:
    owned_df = df[df["source_type"] == "owned"].copy()
    if owned_df.empty:
        empty = pd.DataFrame()
        return OwnedAssetConcentrationBrief(
            summary_table=empty,
            display_table=empty,
            top_1_share=0.0,
            top_3_share=0.0,
            urls_for_half=0,
            owned_urls=0,
        )

    summary_table = (
        owned_df.groupby("url", dropna=False)
        .agg(
            title=("title", _first_non_empty),
            source_domain=("source_domain", _first_non_empty),
            weighted_citations=("observation_weight", "sum"),
            prompts=("prompt", "nunique"),
            topics=("topic", "nunique"),
            models=("model", "nunique"),
        )
        .reset_index()
        .rename(columns={"url": "Owned URL"})
    )
    total_owned_weight = float(summary_table["weighted_citations"].sum())
    summary_table["Page"] = summary_table["Owned URL"].map(compact_url_label)
    summary_table["Title"] = summary_table["title"].where(summary_table["title"].str.strip() != "", summary_table["Page"])
    summary_table["Share of owned %"] = (
        summary_table["weighted_citations"] / total_owned_weight * 100
    ).fillna(0.0).round(1)
    summary_table = summary_table.sort_values(
        ["Share of owned %", "weighted_citations", "Owned URL"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    summary_table["Cumulative share %"] = summary_table["Share of owned %"].cumsum().round(1)
    summary_table = summary_table.rename(
        columns={
            "weighted_citations": "Weighted citations",
            "prompts": "Prompts",
            "topics": "Topics",
            "models": "Models",
        }
    )[
        [
            "Page",
            "Title",
            "Owned URL",
            "Share of owned %",
            "Cumulative share %",
            "Weighted citations",
            "Prompts",
            "Topics",
            "Models",
        ]
    ].copy()

    display_table = summary_table.drop(columns=["Owned URL"]).copy()
    for column in ["Share of owned %", "Cumulative share %"]:
        display_table[column] = display_table[column].map(format_percentage)
    for column in ["Weighted citations", "Prompts", "Topics", "Models"]:
        display_table[column] = display_table[column].map(format_count)

    top_1_share = float(summary_table.head(1)["Share of owned %"].sum()) if not summary_table.empty else 0.0
    top_3_share = float(summary_table.head(3)["Share of owned %"].sum()) if not summary_table.empty else 0.0
    urls_for_half = int((summary_table["Cumulative share %"] < 50).sum() + 1) if not summary_table.empty else 0

    return OwnedAssetConcentrationBrief(
        summary_table=summary_table,
        display_table=display_table,
        top_1_share=round(top_1_share, 1),
        top_3_share=round(top_3_share, 1),
        urls_for_half=urls_for_half,
        owned_urls=int(summary_table["Page"].nunique()),
    )


def render_owned_asset_concentration_brief(df: pd.DataFrame) -> None:
    st.subheader("Owned asset concentration")
    st.caption(
        "Shows whether the client's AI-cited presence is overly reliant on a small number of owned pages. High concentration means visibility is fragile and hard to scale."
    )

    brief = build_owned_asset_concentration_brief(df)
    if brief.summary_table.empty:
        st.info("No owned cited URLs are available for the current filter set.")
        return

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Top page share", f"{brief.top_1_share:.1f}%")
    metric_2.metric("Top 3 page share", f"{brief.top_3_share:.1f}%")
    metric_3.metric("Pages driving 50%", f"{brief.urls_for_half:,}")
    metric_4.metric("Owned pages cited", f"{brief.owned_urls:,}")

    download_1, download_2 = st.columns(2)
    with download_1:
        st.download_button(
            "Export owned asset concentration CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name="owned_asset_concentration.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        render_copy_table_button(
            brief.display_table,
            button_label="Copy table for PowerPoint",
            key="owned-asset-concentration-table",
        )

    st.dataframe(brief.display_table, use_container_width=True, hide_index=True)
