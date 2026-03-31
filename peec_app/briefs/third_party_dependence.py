from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from peec_app.briefs.insight_utils import format_count, format_percentage, percentage_band
from peec_app.renderers.copy_table import render_copy_table_button


@dataclass
class ThirdPartyDependenceBrief:
    summary_table: pd.DataFrame
    display_table: pd.DataFrame
    overall_owned_share: float
    overall_competitor_share: float
    overall_external_share: float
    overall_third_party_share: float


def _build_source_share_pivot(df: pd.DataFrame, group_column: str) -> pd.DataFrame:
    summary = (
        df.groupby([group_column, "source_type"], dropna=False)["observation_weight"]
        .sum()
        .reset_index(name="weighted_citations")
    )
    if summary.empty:
        return pd.DataFrame()
    pivot = summary.pivot_table(
        index=group_column,
        columns="source_type",
        values="weighted_citations",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()
    for column in ["owned", "competitor", "external"]:
        if column not in pivot.columns:
            pivot[column] = 0.0
    pivot["weighted_citations"] = pivot[["owned", "competitor", "external"]].sum(axis=1)
    pivot["owned_share_pct"] = (
        pivot["owned"] / pivot["weighted_citations"] * 100
    ).fillna(0.0).round(1)
    pivot["competitor_share_pct"] = (
        pivot["competitor"] / pivot["weighted_citations"] * 100
    ).fillna(0.0).round(1)
    pivot["external_share_pct"] = (
        pivot["external"] / pivot["weighted_citations"] * 100
    ).fillna(0.0).round(1)
    pivot["third_party_dependence_pct"] = (
        pivot["competitor_share_pct"] + pivot["external_share_pct"]
    ).round(1)
    return pivot


def build_third_party_dependence_brief(df: pd.DataFrame) -> ThirdPartyDependenceBrief:
    if df.empty:
        return ThirdPartyDependenceBrief(
            summary_table=pd.DataFrame(),
            display_table=pd.DataFrame(),
            overall_owned_share=0.0,
            overall_competitor_share=0.0,
            overall_external_share=0.0,
            overall_third_party_share=0.0,
        )

    working = df.copy()
    topic_pivot = _build_source_share_pivot(working, "topic")
    if topic_pivot.empty:
        return ThirdPartyDependenceBrief(
            summary_table=pd.DataFrame(),
            display_table=pd.DataFrame(),
            overall_owned_share=0.0,
            overall_competitor_share=0.0,
            overall_external_share=0.0,
            overall_third_party_share=0.0,
        )

    lead_external = (
        working[working["source_type"] == "external"]
        .groupby(["topic", "source_domain"], dropna=False)["observation_weight"]
        .sum()
        .reset_index(name="weighted_citations")
        .sort_values(["topic", "weighted_citations"], ascending=[True, False])
        .drop_duplicates(subset=["topic"])
        .rename(columns={"source_domain": "Lead external domain"})
    )
    lead_competitor = (
        working[working["source_type"] == "competitor"]
        .assign(competitor_label=lambda data: data["competitor"].where(data["competitor"].str.strip() != "", data["source_domain"]))
        .groupby(["topic", "competitor_label"], dropna=False)["observation_weight"]
        .sum()
        .reset_index(name="weighted_citations")
        .sort_values(["topic", "weighted_citations"], ascending=[True, False])
        .drop_duplicates(subset=["topic"])
        .rename(columns={"competitor_label": "Lead competitor"})
    )

    summary_table = (
        topic_pivot.merge(
            lead_competitor[["topic", "Lead competitor"]],
            on="topic",
            how="left",
        )
        .merge(
            lead_external[["topic", "Lead external domain"]],
            on="topic",
            how="left",
        )
        .rename(
            columns={
                "topic": "Topic",
                "weighted_citations": "Weighted citations",
                "owned_share_pct": "Owned share %",
                "competitor_share_pct": "Competitor share %",
                "external_share_pct": "External share %",
                "third_party_dependence_pct": "Third-party dependence %",
            }
        )
    )
    summary_table["Risk"] = summary_table["Third-party dependence %"].map(percentage_band)
    summary_table = summary_table[
        [
            "Topic",
            "Third-party dependence %",
            "Owned share %",
            "Competitor share %",
            "External share %",
            "Weighted citations",
            "Lead competitor",
            "Lead external domain",
            "Risk",
        ]
    ].sort_values(
        ["Third-party dependence %", "Weighted citations", "Topic"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    summary_table[["Lead competitor", "Lead external domain"]] = summary_table[
        ["Lead competitor", "Lead external domain"]
    ].fillna("")

    display_table = summary_table.copy()
    for column in [
        "Third-party dependence %",
        "Owned share %",
        "Competitor share %",
        "External share %",
    ]:
        display_table[column] = display_table[column].map(format_percentage)
    display_table["Weighted citations"] = display_table["Weighted citations"].map(format_count)

    total_weight = float(working["observation_weight"].sum())
    overall_owned = float(working.loc[working["source_type"] == "owned", "observation_weight"].sum())
    overall_competitor = float(working.loc[working["source_type"] == "competitor", "observation_weight"].sum())
    overall_external = float(working.loc[working["source_type"] == "external", "observation_weight"].sum())
    overall_owned_share = (overall_owned / total_weight * 100) if total_weight else 0.0
    overall_competitor_share = (overall_competitor / total_weight * 100) if total_weight else 0.0
    overall_external_share = (overall_external / total_weight * 100) if total_weight else 0.0

    return ThirdPartyDependenceBrief(
        summary_table=summary_table,
        display_table=display_table,
        overall_owned_share=round(overall_owned_share, 1),
        overall_competitor_share=round(overall_competitor_share, 1),
        overall_external_share=round(overall_external_share, 1),
        overall_third_party_share=round(overall_competitor_share + overall_external_share, 1),
    )


def render_third_party_dependence_brief(df: pd.DataFrame) -> None:
    st.subheader("Third-party dependence")
    st.caption(
        "Shows how much AI answer influence comes from non-owned sources. High dependence means the conversation is being shaped away from the client's own domain."
    )

    brief = build_third_party_dependence_brief(df)
    if brief.summary_table.empty:
        st.info("No source rows are available for the current filter set.")
        return

    high_risk_topics = int((brief.summary_table["Third-party dependence %"] >= 80).sum())
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Third-party dependence", f"{brief.overall_third_party_share:.1f}%")
    metric_2.metric("Owned share", f"{brief.overall_owned_share:.1f}%")
    metric_3.metric("External share", f"{brief.overall_external_share:.1f}%")
    metric_4.metric("High-risk topics", f"{high_risk_topics:,}")

    download_1, download_2 = st.columns(2)
    with download_1:
        st.download_button(
            "Export third-party dependence CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name="third_party_dependence.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        render_copy_table_button(
            brief.display_table,
            button_label="Copy table for PowerPoint",
            key="third-party-dependence-table",
        )

    st.dataframe(brief.display_table, use_container_width=True, hide_index=True)
