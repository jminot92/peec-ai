from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from peec_app.briefs.domain_types import classify_domain_type
from peec_app.briefs.insight_utils import format_count, format_percentage
from peec_app.renderers.copy_table import render_copy_table_button


@dataclass
class AuthorityConcentrationRiskBrief:
    summary_table: pd.DataFrame
    display_table: pd.DataFrame
    top_3_share: float
    top_5_share: float
    domains_for_half: int
    lead_domain: str


def build_authority_concentration_risk_brief(df: pd.DataFrame) -> AuthorityConcentrationRiskBrief:
    if df.empty:
        empty = pd.DataFrame()
        return AuthorityConcentrationRiskBrief(
            summary_table=empty,
            display_table=empty,
            top_3_share=0.0,
            top_5_share=0.0,
            domains_for_half=0,
            lead_domain="None",
        )

    domain_summary = (
        df.groupby(["source_domain", "source_type"], dropna=False)
        .agg(
            weighted_citations=("observation_weight", "sum"),
            prompts=("prompt", "nunique"),
            topics=("topic", "nunique"),
            models=("model", "nunique"),
        )
        .reset_index()
    )
    if domain_summary.empty:
        empty = pd.DataFrame()
        return AuthorityConcentrationRiskBrief(
            summary_table=empty,
            display_table=empty,
            top_3_share=0.0,
            top_5_share=0.0,
            domains_for_half=0,
            lead_domain="None",
        )

    total_weight = float(domain_summary["weighted_citations"].sum())
    domain_summary["share_pct"] = (
        domain_summary["weighted_citations"] / total_weight * 100
    ).fillna(0.0).round(1)
    domain_summary["domain_type"] = domain_summary.apply(
        lambda row: classify_domain_type(row["source_domain"], row["source_type"]),
        axis=1,
    )
    domain_summary = domain_summary.sort_values(
        ["share_pct", "weighted_citations", "source_domain"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    domain_summary["cumulative_share_pct"] = domain_summary["share_pct"].cumsum().round(1)

    summary_table = domain_summary.rename(
        columns={
            "source_domain": "Domain",
            "source_type": "Source type",
            "domain_type": "Domain type",
            "share_pct": "Share %",
            "cumulative_share_pct": "Cumulative share %",
            "weighted_citations": "Weighted citations",
            "prompts": "Prompts",
            "topics": "Topics",
            "models": "Models",
        }
    )[
        [
            "Domain",
            "Source type",
            "Domain type",
            "Share %",
            "Cumulative share %",
            "Weighted citations",
            "Prompts",
            "Topics",
            "Models",
        ]
    ].copy()

    display_table = summary_table.copy()
    for column in ["Share %", "Cumulative share %"]:
        display_table[column] = display_table[column].map(format_percentage)
    for column in ["Weighted citations", "Prompts", "Topics", "Models"]:
        display_table[column] = display_table[column].map(format_count)
    display_table["Source type"] = display_table["Source type"].str.title()

    top_3_share = float(summary_table.head(3)["Share %"].sum()) if not summary_table.empty else 0.0
    top_5_share = float(summary_table.head(5)["Share %"].sum()) if not summary_table.empty else 0.0
    domains_for_half = int((summary_table["Cumulative share %"] < 50).sum() + 1) if not summary_table.empty else 0
    lead_domain = str(summary_table.iloc[0]["Domain"]) if not summary_table.empty else "None"

    return AuthorityConcentrationRiskBrief(
        summary_table=summary_table,
        display_table=display_table,
        top_3_share=round(top_3_share, 1),
        top_5_share=round(top_5_share, 1),
        domains_for_half=domains_for_half,
        lead_domain=lead_domain,
    )


def render_authority_concentration_risk_brief(df: pd.DataFrame) -> None:
    st.subheader("Authority concentration risk")
    st.caption(
        "Shows whether a small number of domains are disproportionately shaping AI answers. High concentration means visibility can swing quickly if those domains change."
    )

    brief = build_authority_concentration_risk_brief(df)
    if brief.summary_table.empty:
        st.info("No domain rows are available for the current filter set.")
        return

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Top 3 domain share", f"{brief.top_3_share:.1f}%")
    metric_2.metric("Top 5 domain share", f"{brief.top_5_share:.1f}%")
    metric_3.metric("Domains driving 50%", f"{brief.domains_for_half:,}")
    metric_4.metric("Lead domain", brief.lead_domain)

    download_1, download_2 = st.columns(2)
    with download_1:
        st.download_button(
            "Export authority concentration CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name="authority_concentration_risk.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        render_copy_table_button(
            brief.display_table,
            button_label="Copy table for PowerPoint",
            key="authority-concentration-risk-table",
        )

    st.dataframe(brief.display_table, use_container_width=True, hide_index=True)
