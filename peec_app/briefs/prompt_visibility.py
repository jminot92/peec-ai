from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass
class PromptVisibilityBrief:
    summary_table: pd.DataFrame


def _first_non_empty(series: pd.Series) -> str:
    values = [str(value).strip() for value in series.fillna("").astype(str) if str(value).strip()]
    return values[0] if values else ""


def _collect_tags(prompt_df: pd.DataFrame) -> str:
    tag_values: list[str] = []
    if "tag_list" in prompt_df.columns:
        for values in prompt_df["tag_list"]:
            if isinstance(values, list):
                tag_values.extend(str(value).strip() for value in values if str(value).strip())
    if not tag_values and "tag" in prompt_df.columns:
        tag_values.extend(
            str(value).strip()
            for value in prompt_df["tag"].fillna("").astype(str).tolist()
            if str(value).strip()
        )
    unique_tags = sorted({value for value in tag_values if value})
    return ", ".join(unique_tags)


def build_prompt_visibility_table(df: pd.DataFrame, project_name: str) -> pd.DataFrame:
    if df.empty or "prompt" not in df.columns:
        return pd.DataFrame(
            columns=[
                "Prompt",
                "Topic",
                "Tags",
                "Weighted citations",
                f"{project_name} share %",
                "Competitor share %",
                "External share %",
                f"{project_name} Present (Yes/No)",
                "Top Competitor Present",
                "Top Competitor Name",
                "Top Competitor share %",
            ]
        )

    rows: list[dict[str, object]] = []
    prompt_order = (
        df.groupby("prompt", dropna=False)["observation_weight"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    for prompt in prompt_order:
        prompt_df = df[df["prompt"] == prompt].copy()
        total_weight = float(prompt_df["observation_weight"].sum())
        owned_df = prompt_df[prompt_df["source_type"] == "owned"].copy()
        competitor_df = prompt_df[prompt_df["source_type"] == "competitor"].copy()
        external_df = prompt_df[prompt_df["source_type"] == "external"].copy()

        owned_weight = float(owned_df["observation_weight"].sum())
        competitor_weight = float(competitor_df["observation_weight"].sum())
        external_weight = float(external_df["observation_weight"].sum())

        top_competitor_name = ""
        top_competitor_share = 0.0
        if not competitor_df.empty:
            competitor_totals = (
                competitor_df.groupby("competitor", dropna=False)["observation_weight"]
                .sum()
                .sort_values(ascending=False)
            )
            competitor_totals = competitor_totals[competitor_totals.index.astype(str).str.strip() != ""]
            if not competitor_totals.empty:
                top_competitor_name = str(competitor_totals.index[0])
                top_competitor_share = (float(competitor_totals.iloc[0]) / total_weight * 100) if total_weight else 0.0

        rows.append(
            {
                "Prompt": str(prompt),
                "Topic": _first_non_empty(prompt_df["topic"]),
                "Tags": _collect_tags(prompt_df),
                "Weighted citations": round(total_weight, 1),
                f"{project_name} share %": round((owned_weight / total_weight * 100) if total_weight else 0.0, 1),
                "Competitor share %": round((competitor_weight / total_weight * 100) if total_weight else 0.0, 1),
                "External share %": round((external_weight / total_weight * 100) if total_weight else 0.0, 1),
                f"{project_name} Present (Yes/No)": "Yes" if owned_weight > 0 else "No",
                "Top Competitor Present": "Yes" if top_competitor_name else "No",
                "Top Competitor Name": top_competitor_name,
                "Top Competitor share %": round(top_competitor_share, 1),
            }
        )

    summary_table = pd.DataFrame(rows)
    if summary_table.empty:
        return summary_table

    return summary_table.sort_values(
        [f"{project_name} Present (Yes/No)", f"{project_name} share %", "Weighted citations"],
        ascending=[True, True, False],
    ).reset_index(drop=True)


def build_prompt_coverage_table(df: pd.DataFrame, project_name: str) -> pd.DataFrame:
    prompt_visibility_table = build_prompt_visibility_table(df, project_name)
    if prompt_visibility_table.empty:
        return pd.DataFrame(
            columns=[
                "Prompt",
                f"{project_name} Present (Yes/No)",
                "Top Competitor Present",
                "Top Competitor Name",
            ]
        )
    return prompt_visibility_table[
        [
            "Prompt",
            f"{project_name} Present (Yes/No)",
            "Top Competitor Present",
            "Top Competitor Name",
        ]
    ].head(50).copy()


def render_prompt_visibility_brief(df: pd.DataFrame, project_name: str) -> None:
    st.subheader("Prompt visibility")
    st.caption(
        "Prompt-level visibility table showing where the client appears, where competitors dominate, and which prompts are still uncovered."
    )

    summary_table = build_prompt_visibility_table(df, project_name)
    if summary_table.empty:
        st.info("No prompt rows are available for the current filter set.")
        return

    coverage_column = f"{project_name} Present (Yes/No)"
    client_present_count = int((summary_table[coverage_column] == "Yes").sum())
    prompt_gap_count = int((summary_table[coverage_column] == "No").sum())
    competitor_present_count = int((summary_table["Top Competitor Present"] == "Yes").sum())

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Prompts", f"{len(summary_table):,}")
    metric_2.metric(f"{project_name} present", f"{client_present_count:,}")
    metric_3.metric("Prompt gaps", f"{prompt_gap_count:,}")
    st.caption(f"Competitors are present in {competitor_present_count:,} prompts in the current filter set.")

    st.download_button(
        "Export prompt visibility CSV",
        summary_table.to_csv(index=False).encode("utf-8"),
        file_name="prompt_visibility.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.dataframe(summary_table, use_container_width=True, hide_index=True)
