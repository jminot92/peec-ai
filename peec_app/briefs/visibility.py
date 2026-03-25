from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import matplotlib.dates as mdates
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
class VisibilityBrief:
    summary_table: pd.DataFrame
    chart_data: pd.DataFrame
    competitor_options: list[str]
    preview_chart_png: bytes
    export_chart_png: bytes



def build_visibility_brief(
    df: pd.DataFrame,
    owned_label: str,
    selected_competitors: list[str],
) -> VisibilityBrief:
    competitive_rows = build_competitive_rows(df, owned_label)
    options = competitor_options(df, owned_label)
    if competitive_rows.empty:
        return VisibilityBrief(
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

    daily_visibility = (
        competitive_rows.groupby(["date", "entity", "entity_type"], dropna=False)["observation_weight"]
        .sum()
        .reset_index(name="weighted_mentions")
        .sort_values(["date", "weighted_mentions"], ascending=[True, False])
    )
    if daily_visibility.empty:
        return VisibilityBrief(
            summary_table=pd.DataFrame(),
            chart_data=pd.DataFrame(),
            competitor_options=options,
            preview_chart_png=b"",
            export_chart_png=b"",
        )

    daily_visibility["daily_total_weight"] = daily_visibility.groupby("date")["weighted_mentions"].transform("sum")
    daily_visibility["visibility_share"] = (
        daily_visibility["weighted_mentions"] / daily_visibility["daily_total_weight"]
    ).fillna(0.0)
    daily_visibility["visibility_pct"] = (daily_visibility["visibility_share"] * 100).round(1)

    entity_totals = (
        competitive_rows.groupby(["entity", "entity_type"], dropna=False)
        .agg(
            weighted_mentions=("observation_weight", "sum"),
            prompts_covered=("prompt", "nunique"),
            urls_cited=("url", "nunique"),
            days_visible=("date", "nunique"),
            first_seen=("date", "min"),
            last_seen=("date", "max"),
        )
        .reset_index()
    )
    total_mentions = float(entity_totals["weighted_mentions"].sum())
    entity_totals["visibility_share"] = entity_totals["weighted_mentions"] / total_mentions if total_mentions else 0.0
    entity_totals["visibility_pct"] = (entity_totals["visibility_share"] * 100).round(1)

    average_daily = (
        daily_visibility.groupby("entity", dropna=False)["visibility_share"]
        .mean()
        .rename("avg_daily_visibility_share")
        .reset_index()
    )
    average_daily["avg_daily_visibility_pct"] = (average_daily["avg_daily_visibility_share"] * 100).round(1)

    latest_date = daily_visibility["date"].max()
    latest_daily = (
        daily_visibility[daily_visibility["date"] == latest_date][["entity", "visibility_share"]]
        .rename(columns={"visibility_share": "latest_visibility_share"})
        .copy()
    )
    latest_daily["latest_visibility_pct"] = (latest_daily["latest_visibility_share"] * 100).round(1)

    summary_table = entity_totals.merge(
        average_daily[["entity", "avg_daily_visibility_pct"]],
        on="entity",
        how="left",
    ).merge(
        latest_daily[["entity", "latest_visibility_pct"]],
        on="entity",
        how="left",
    )
    summary_table["first_seen"] = pd.to_datetime(summary_table["first_seen"]).dt.date.astype(str)
    summary_table["last_seen"] = pd.to_datetime(summary_table["last_seen"]).dt.date.astype(str)
    summary_table["visibility_pct"] = summary_table["visibility_pct"].round(1)
    summary_table["avg_daily_visibility_pct"] = summary_table["avg_daily_visibility_pct"].fillna(0.0).round(1)
    summary_table["latest_visibility_pct"] = summary_table["latest_visibility_pct"].fillna(0.0).round(1)

    summary_table["sort_group"] = summary_table["entity_type"].map({"owned": 0, "competitor": 1}).fillna(2)
    summary_table = summary_table.sort_values(
        ["sort_group", "visibility_pct", "weighted_mentions"],
        ascending=[True, False, False],
    ).drop(columns=["visibility_share", "sort_group"])
    summary_table = summary_table[
        [
            "entity",
            "entity_type",
            "visibility_pct",
            "avg_daily_visibility_pct",
            "latest_visibility_pct",
            "weighted_mentions",
            "prompts_covered",
            "urls_cited",
            "days_visible",
            "first_seen",
            "last_seen",
        ]
    ].reset_index(drop=True)

    chart_data = daily_visibility[
        [
            "date",
            "entity",
            "entity_type",
            "weighted_mentions",
            "daily_total_weight",
            "visibility_share",
            "visibility_pct",
        ]
    ].copy()
    chart_data = chart_data.sort_values(["date", "entity"]).reset_index(drop=True)

    preview_chart_png = build_visibility_chart_png(
        chart_data,
        summary_table,
        owned_label,
        transparent=False,
    )
    export_chart_png = build_visibility_chart_png(
        chart_data,
        summary_table,
        owned_label,
        transparent=True,
    )

    return VisibilityBrief(
        summary_table=summary_table,
        chart_data=chart_data,
        competitor_options=options,
        preview_chart_png=preview_chart_png,
        export_chart_png=export_chart_png,
    )



def build_visibility_chart_png(
    chart_data: pd.DataFrame,
    summary_table: pd.DataFrame,
    owned_label: str,
    *,
    transparent: bool,
) -> bytes:
    if chart_data.empty or summary_table.empty:
        return b""

    ordered_entities = entity_order(summary_table, owned_label)
    colours = entity_colours(ordered_entities, owned_label)
    figure, axis = plt.subplots(figsize=(14, 6), dpi=220)
    background = "none" if transparent else PREVIEW_BACKGROUND
    figure.patch.set_facecolor(background)
    axis.set_facecolor(background)

    for entity in ordered_entities:
        entity_rows = chart_data[chart_data["entity"] == entity].sort_values("date")
        if entity_rows.empty:
            continue
        axis.plot(
            entity_rows["date"],
            entity_rows["visibility_share"],
            color=colours[entity],
            linewidth=3.2 if entity == owned_label else 2.4,
            label=entity,
            solid_capstyle="round",
        )

    axis.tick_params(axis="x", colors="white", labelsize=10)
    axis.tick_params(axis="y", colors="white", labelsize=10)
    axis.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: "0" if abs(value) < 0.0001 else f"{value:.02f}".rstrip("0").rstrip("."))
    )
    axis.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=8, maxticks=18))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
    for label in axis.get_xticklabels():
        label.set_rotation(90)
        label.set_horizontalalignment("center")
        label.set_color("white")
    for label in axis.get_yticklabels():
        label.set_color("white")

    axis.grid(axis="y", color=(1, 1, 1, 0.32), linewidth=0.8)
    axis.grid(axis="x", visible=False)
    for spine in axis.spines.values():
        spine.set_visible(False)

    ymax = float(chart_data["visibility_share"].max()) if not chart_data.empty else 0.0
    axis.set_ylim(0, max(ymax * 1.15, 0.05))
    axis.set_xlim(chart_data["date"].min(), chart_data["date"].max())
    axis.set_xlabel("")
    axis.set_ylabel("")

    legend = axis.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.08),
        ncol=min(4, max(len(ordered_entities), 1)),
        frameon=False,
        fontsize=10,
    )
    for text in legend.get_texts():
        text.set_color("white")

    figure.tight_layout()
    buffer = BytesIO()
    figure.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
        dpi=220,
        transparent=transparent,
        pad_inches=0.2,
    )
    plt.close(figure)
    return buffer.getvalue()



def render_visibility_brief(df: pd.DataFrame, owned_label: str) -> None:
    st.subheader("Visibility vs competitors")
    st.caption(
        "Weighted visibility is based on PEEC observation weight within the selected project, date window, model, topic and tag filters."
    )

    options = competitor_options(df, owned_label)
    default_selection = default_competitor_selection(options)
    selected_competitors = st.multiselect(
        "Competitors to include",
        options=options,
        default=default_selection,
        help="Defaults to the top five competitors by weighted mentions. Add or remove brands to change the table and chart.",
    )

    brief = build_visibility_brief(df, owned_label, selected_competitors)
    if brief.summary_table.empty:
        st.info("No owned or competitor rows are available for the current filter set.")
        return

    owned_row = brief.summary_table[brief.summary_table["entity_type"] == "owned"]
    owned_visibility = float(owned_row["visibility_pct"].iloc[0]) if not owned_row.empty else 0.0
    competitor_rows = brief.summary_table[brief.summary_table["entity_type"] == "competitor"]
    lead_competitor = competitor_rows.iloc[0]["entity"] if not competitor_rows.empty else "None"
    lead_competitor_visibility = float(competitor_rows.iloc[0]["visibility_pct"]) if not competitor_rows.empty else 0.0

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Owned visibility", f"{owned_visibility:.1f}%")
    metric_2.metric(
        "Lead competitor",
        lead_competitor,
        f"{lead_competitor_visibility:.1f}%" if lead_competitor != "None" else None,
    )
    metric_3.metric("Competitors shown", str(len(selected_competitors) or len(options)))

    if brief.preview_chart_png:
        st.image(brief.preview_chart_png, use_container_width=True)

    download_1, download_2, download_3 = st.columns(3)
    with download_1:
        st.download_button(
            "Export summary CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name="visibility_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        st.download_button(
            "Export chart data CSV",
            brief.chart_data.to_csv(index=False).encode("utf-8"),
            file_name="visibility_timeseries.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_3:
        st.download_button(
            "Download PNG chart",
            brief.export_chart_png,
            file_name="visibility_chart.png",
            mime="image/png",
            use_container_width=True,
        )

    display_table = brief.summary_table.rename(
        columns={
            "entity": "Entity",
            "entity_type": "Type",
            "visibility_pct": "Visibility %",
            "avg_daily_visibility_pct": "Avg daily visibility %",
            "latest_visibility_pct": "Latest visibility %",
            "weighted_mentions": "Weighted mentions",
            "prompts_covered": "Prompts covered",
            "urls_cited": "URLs cited",
            "days_visible": "Days visible",
            "first_seen": "First seen",
            "last_seen": "Last seen",
        }
    )
    st.dataframe(display_table, use_container_width=True, hide_index=True)
