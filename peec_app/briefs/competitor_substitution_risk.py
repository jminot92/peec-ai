from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from peec_app.briefs.insight_utils import format_count, format_percentage, percentage_band, top_labels
from peec_app.briefs.prompt_visibility import build_prompt_visibility_table
from peec_app.renderers.copy_table import render_copy_table_button


@dataclass
class CompetitorSubstitutionRiskBrief:
    summary_table: pd.DataFrame
    display_table: pd.DataFrame
    risky_prompt_table: pd.DataFrame
    risky_prompt_display_table: pd.DataFrame
    substitution_prompts: int
    exposed_topics: int
    lead_competitor: str


def build_competitor_substitution_risk_brief(
    df: pd.DataFrame,
    project_name: str,
) -> CompetitorSubstitutionRiskBrief:
    prompt_table = build_prompt_visibility_table(df, project_name)
    coverage_column = f"{project_name} Present (Yes/No)"

    if prompt_table.empty:
        empty = pd.DataFrame()
        return CompetitorSubstitutionRiskBrief(
            summary_table=empty,
            display_table=empty,
            risky_prompt_table=empty,
            risky_prompt_display_table=empty,
            substitution_prompts=0,
            exposed_topics=0,
            lead_competitor="None",
        )

    risky_prompts = prompt_table[
        (prompt_table[coverage_column] == "No")
        & (prompt_table["Top Competitor Present"] == "Yes")
    ].copy()

    if risky_prompts.empty:
        empty_summary = pd.DataFrame(
            columns=[
                "Topic",
                "Substitution prompts",
                "Total prompts",
                "Substitution rate %",
                "Weighted citations",
                "Lead competitor",
                "Sample uncovered prompts",
                "Risk",
            ]
        )
        return CompetitorSubstitutionRiskBrief(
            summary_table=empty_summary,
            display_table=empty_summary.copy(),
            risky_prompt_table=risky_prompts,
            risky_prompt_display_table=risky_prompts,
            substitution_prompts=0,
            exposed_topics=0,
            lead_competitor="None",
        )

    topic_totals = (
        prompt_table.groupby("Topic", dropna=False)
        .agg(
            total_prompts=("Prompt", "nunique"),
            weighted_citations=("Weighted citations", "sum"),
        )
        .reset_index()
    )
    risky_by_topic = (
        risky_prompts.groupby("Topic", dropna=False)
        .agg(
            substitution_prompts=("Prompt", "nunique"),
            risky_weighted_citations=("Weighted citations", "sum"),
            sample_uncovered_prompts=("Prompt", lambda values: top_labels(pd.Series(values), max_items=2, separator=" | ")),
        )
        .reset_index()
    )
    lead_competitors = (
        risky_prompts.groupby(["Topic", "Top Competitor Name"], dropna=False)["Weighted citations"]
        .sum()
        .reset_index(name="weighted_citations")
        .sort_values(["Topic", "weighted_citations"], ascending=[True, False])
        .drop_duplicates(subset=["Topic"])
        .rename(columns={"Top Competitor Name": "Lead competitor"})
    )

    summary_table = topic_totals.merge(risky_by_topic, on="Topic", how="inner").merge(
        lead_competitors[["Topic", "Lead competitor"]],
        on="Topic",
        how="left",
    )
    summary_table["Substitution rate %"] = (
        summary_table["substitution_prompts"] / summary_table["total_prompts"] * 100
    ).fillna(0.0).round(1)
    summary_table["Risk"] = summary_table["Substitution rate %"].map(
        lambda value: percentage_band(value, severe=60.0, high=40.0, medium=20.0)
    )
    summary_table = summary_table.rename(
        columns={
            "total_prompts": "Total prompts",
            "weighted_citations": "Weighted citations",
            "substitution_prompts": "Substitution prompts",
            "sample_uncovered_prompts": "Sample uncovered prompts",
        }
    )[
        [
            "Topic",
            "Substitution prompts",
            "Total prompts",
            "Substitution rate %",
            "Weighted citations",
            "Lead competitor",
            "Sample uncovered prompts",
            "Risk",
        ]
    ].sort_values(
        ["Substitution rate %", "Substitution prompts", "Weighted citations"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    display_table = summary_table.copy()
    display_table["Substitution prompts"] = display_table["Substitution prompts"].map(format_count)
    display_table["Total prompts"] = display_table["Total prompts"].map(format_count)
    display_table["Weighted citations"] = display_table["Weighted citations"].map(format_count)
    display_table["Substitution rate %"] = display_table["Substitution rate %"].map(format_percentage)

    risky_prompt_table = risky_prompts[
        [
            "Prompt",
            "Topic",
            "Tags",
            "Weighted citations",
            "Competitor share %",
            "External share %",
            "Top Competitor Name",
            "Top Competitor share %",
        ]
    ].sort_values(
        ["Competitor share %", "Weighted citations"],
        ascending=[False, False],
    ).reset_index(drop=True)
    risky_prompt_display_table = risky_prompt_table.copy()
    for column in [
        "Weighted citations",
        "Competitor share %",
        "External share %",
        "Top Competitor share %",
    ]:
        formatter = format_count if column == "Weighted citations" else format_percentage
        risky_prompt_display_table[column] = risky_prompt_display_table[column].map(formatter)

    lead_competitor = (
        risky_prompts.groupby("Top Competitor Name", dropna=False)["Weighted citations"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    return CompetitorSubstitutionRiskBrief(
        summary_table=summary_table,
        display_table=display_table,
        risky_prompt_table=risky_prompt_table,
        risky_prompt_display_table=risky_prompt_display_table,
        substitution_prompts=int(risky_prompt_table["Prompt"].nunique()),
        exposed_topics=int(summary_table["Topic"].nunique()),
        lead_competitor=lead_competitor[0] if lead_competitor else "None",
    )


def render_competitor_substitution_risk_brief(df: pd.DataFrame, project_name: str) -> None:
    st.subheader("Competitor substitution risk")
    st.caption(
        "Highlights topics where competitors appear in prompts and the client does not. This is the clearest signal that AI is choosing another brand for the conversation."
    )

    brief = build_competitor_substitution_risk_brief(df, project_name)
    if brief.risky_prompt_table.empty:
        st.info("No competitor substitution prompts were detected in the current filter set.")
        return

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Substitution prompts", f"{brief.substitution_prompts:,}")
    metric_2.metric("Exposed topics", f"{brief.exposed_topics:,}")
    metric_3.metric("Lead substituting competitor", brief.lead_competitor)

    download_1, download_2, download_3 = st.columns(3)
    with download_1:
        st.download_button(
            "Export topic summary CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name="competitor_substitution_risk_topics.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        st.download_button(
            "Export risky prompts CSV",
            brief.risky_prompt_table.to_csv(index=False).encode("utf-8"),
            file_name="competitor_substitution_risk_prompts.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_3:
        render_copy_table_button(
            brief.display_table,
            button_label="Copy table for PowerPoint",
            key="competitor-substitution-risk-table",
        )

    st.dataframe(brief.display_table, use_container_width=True, hide_index=True)

    with st.expander("View exposed prompts"):
        st.dataframe(brief.risky_prompt_display_table, use_container_width=True, hide_index=True)
