from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import streamlit as st

from peec_app.briefs.visibility_common import (
    PREVIEW_BACKGROUND,
    build_competitive_rows,
    competitor_options,
    default_competitor_selection,
    entity_colours,
    entity_order,
)


@dataclass
class VisibilitySnapshotBrief:
    summary_table: pd.DataFrame
    chart_data: pd.DataFrame
    competitor_options: list[str]
    preview_chart_png: bytes
    export_chart_png: bytes


def available_snapshot_dates(df: pd.DataFrame, owned_label: str) -> list[pd.Timestamp]:
    competitive_rows = build_competitive_rows(df, owned_label)
    if competitive_rows.empty:
        return []
    dates = (
        pd.to_datetime(competitive_rows["date"], errors="coerce")
        .dropna()
        .sort_values()
        .dt.normalize()
        .unique()
        .tolist()
    )
    return [pd.Timestamp(value).normalize() for value in dates]


def build_visibility_snapshot_brief(
    df: pd.DataFrame,
    owned_label: str,
    selected_competitors: list[str],
    snapshot_date: pd.Timestamp,
) -> VisibilitySnapshotBrief:
    competitive_rows = build_competitive_rows(df, owned_label)
    options = competitor_options(df, owned_label)
    if competitive_rows.empty:
        return VisibilitySnapshotBrief(
            summary_table=pd.DataFrame(),
            chart_data=pd.DataFrame(),
            competitor_options=options,
            preview_chart_png=b"",
            export_chart_png=b"",
        )

    if selected_competitors:
        competitive_rows = competitive_rows[
            (competitive_rows["entity_type"] == "owned")
            | (competitive_rows["entity"].isin(selected_competitors))
        ].copy()

    snapshot_rows = competitive_rows[
        pd.to_datetime(competitive_rows["date"], errors="coerce").dt.normalize() == snapshot_date.normalize()
    ].copy()
    if snapshot_rows.empty:
        return VisibilitySnapshotBrief(
            summary_table=pd.DataFrame(),
            chart_data=pd.DataFrame(),
            competitor_options=options,
            preview_chart_png=b"",
            export_chart_png=b"",
        )

    summary_table = (
        snapshot_rows.groupby(["entity", "entity_type"], dropna=False)
        .agg(
            weighted_mentions=("observation_weight", "sum"),
            prompts_covered=("prompt", "nunique"),
            urls_cited=("url", "nunique"),
        )
        .reset_index()
    )
    total_mentions = float(summary_table["weighted_mentions"].sum())
    summary_table["visibility_share"] = summary_table["weighted_mentions"] / total_mentions if total_mentions else 0.0
    summary_table["visibility_pct"] = (summary_table["visibility_share"] * 100).round(1)
    summary_table["snapshot_date"] = snapshot_date.date().isoformat()
    summary_table["sort_group"] = summary_table["entity_type"].map({"owned": 0, "competitor": 1}).fillna(2)
    summary_table = summary_table.sort_values(
        ["sort_group", "visibility_pct", "weighted_mentions"],
        ascending=[True, False, False],
    ).drop(columns=["visibility_share", "sort_group"])
    summary_table = summary_table[
        [
            "snapshot_date",
            "entity",
            "entity_type",
            "visibility_pct",
            "weighted_mentions",
            "prompts_covered",
            "urls_cited",
        ]
    ].reset_index(drop=True)

    chart_data = summary_table.rename(
        columns={
            "snapshot_date": "date",
            "entity": "entity",
            "entity_type": "entity_type",
            "visibility_pct": "visibility_pct",
            "weighted_mentions": "weighted_mentions",
            "prompts_covered": "prompts_covered",
            "urls_cited": "urls_cited",
        }
    ).copy()

    preview_chart_png = build_visibility_snapshot_chart_png(
        chart_data,
        owned_label,
        transparent=False,
    )
    export_chart_png = build_visibility_snapshot_chart_png(
        chart_data,
        owned_label,
        transparent=True,
    )

    return VisibilitySnapshotBrief(
        summary_table=summary_table,
        chart_data=chart_data,
        competitor_options=options,
        preview_chart_png=preview_chart_png,
        export_chart_png=export_chart_png,
    )


def build_visibility_snapshot_chart_png(
    chart_data: pd.DataFrame,
    owned_label: str,
    *,
    transparent: bool,
) -> bytes:
    if chart_data.empty:
        return b""

    ordered_entities = entity_order(chart_data.rename(columns={"entity_type": "entity_type"}), owned_label)
    colours = entity_colours(ordered_entities, owned_label)

    figure, axis = plt.subplots(figsize=(13.5, 5.8), dpi=220)
    background = "none" if transparent else PREVIEW_BACKGROUND
    figure.patch.set_facecolor(background)
    axis.set_facecolor(background)

    x_positions = list(range(len(ordered_entities)))
    heights = []
    bar_colours = []
    for entity in ordered_entities:
        entity_row = chart_data[chart_data["entity"] == entity]
        if entity_row.empty:
            continue
        heights.append(float(entity_row["visibility_pct"].iloc[0]) / 100.0)
        bar_colours.append(colours[entity])

    axis.bar(
        x_positions,
        heights,
        color=bar_colours,
        width=0.6,
        edgecolor="none",
        zorder=3,
    )

    axis.tick_params(axis="x", colors="white", labelsize=10, length=0)
    axis.tick_params(axis="y", colors="white", labelsize=10)
    axis.set_xticks(x_positions)
    axis.set_xticklabels(ordered_entities, rotation=20, ha="right", color="white")
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0%}"))
    axis.grid(axis="y", color=(1, 1, 1, 0.28), linewidth=0.8, zorder=0)
    axis.grid(axis="x", visible=False)
    for spine in axis.spines.values():
        spine.set_visible(False)

    ymax = max(heights) if heights else 0.0
    axis.set_ylim(0, max(ymax * 1.18, 0.05))
    axis.set_xlabel("")
    axis.set_ylabel("")

    for index, height in enumerate(heights):
        axis.text(
            index,
            height + max(ymax * 0.025, 0.005),
            f"{height:.1%}",
            ha="center",
            va="bottom",
            color="white",
            fontsize=10,
            fontweight="bold",
        )

    figure.tight_layout()
    buffer = BytesIO()
    figure.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
        dpi=220,
        transparent=transparent,
        pad_inches=0.25,
    )
    plt.close(figure)
    return buffer.getvalue()


def render_visibility_snapshot_brief(df: pd.DataFrame, owned_label: str) -> None:
    st.subheader("Visibility snapshot")
    st.caption(
        "Pick a single date to compare owned brand visibility against competitors for that day only."
    )

    options = competitor_options(df, owned_label)
    default_selection = default_competitor_selection(options)
    selector_col, date_col = st.columns([1.4, 1])
    with selector_col:
        selected_competitors = st.multiselect(
            "Competitors to include",
            options=options,
            default=default_selection,
            key="snapshot_competitors",
            help="Defaults to the top five competitors by weighted mentions in the current filter set.",
        )

    available_dates = available_snapshot_dates(df, owned_label)
    if not available_dates:
        st.info("No owned or competitor rows are available for the current filter set.")
        return

    latest_date = available_dates[-1]
    with date_col:
        selected_date = st.selectbox(
            "Snapshot date",
            options=available_dates,
            index=len(available_dates) - 1,
            format_func=lambda value: pd.Timestamp(value).strftime("%d %b %Y"),
            key="snapshot_date",
        )

    brief = build_visibility_snapshot_brief(
        df,
        owned_label,
        selected_competitors,
        pd.Timestamp(selected_date),
    )
    if brief.summary_table.empty:
        st.info("No owned or competitor rows were available for the selected date.")
        return

    owned_row = brief.summary_table[brief.summary_table["entity_type"] == "owned"]
    owned_visibility = float(owned_row["visibility_pct"].iloc[0]) if not owned_row.empty else 0.0
    competitor_rows = brief.summary_table[brief.summary_table["entity_type"] == "competitor"]
    lead_competitor = competitor_rows.iloc[0]["entity"] if not competitor_rows.empty else "None"
    lead_competitor_visibility = float(competitor_rows.iloc[0]["visibility_pct"]) if not competitor_rows.empty else 0.0

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Snapshot date", pd.Timestamp(selected_date).strftime("%d %b %Y"))
    metric_2.metric("Owned visibility", f"{owned_visibility:.1f}%")
    metric_3.metric(
        "Lead competitor",
        lead_competitor,
        f"{lead_competitor_visibility:.1f}%" if lead_competitor != "None" else None,
    )

    if brief.preview_chart_png:
        st.image(brief.preview_chart_png, use_container_width=True)

    download_1, download_2, download_3 = st.columns(3)
    with download_1:
        st.download_button(
            "Export snapshot CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name=f"visibility_snapshot_{pd.Timestamp(selected_date).date().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        st.download_button(
            "Export chart data CSV",
            brief.chart_data.to_csv(index=False).encode("utf-8"),
            file_name=f"visibility_snapshot_chart_data_{pd.Timestamp(selected_date).date().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_3:
        st.download_button(
            "Download PNG chart",
            brief.export_chart_png,
            file_name=f"visibility_snapshot_{pd.Timestamp(selected_date).date().isoformat()}.png",
            mime="image/png",
            use_container_width=True,
        )

    display_table = brief.summary_table.rename(
        columns={
            "snapshot_date": "Date",
            "entity": "Entity",
            "entity_type": "Type",
            "visibility_pct": "Visibility %",
            "weighted_mentions": "Weighted mentions",
            "prompts_covered": "Prompts covered",
            "urls_cited": "URLs cited",
        }
    )
    st.dataframe(display_table, use_container_width=True, hide_index=True)
