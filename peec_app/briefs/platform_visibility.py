from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from peec_app.briefs.visibility_common import COMPETITOR_COLOURS, OWNED_COLOUR, PREVIEW_BACKGROUND


PLATFORM_COLOURS = [
    OWNED_COLOUR,
    COMPETITOR_COLOURS[0],
    COMPETITOR_COLOURS[2],
    COMPETITOR_COLOURS[3],
    COMPETITOR_COLOURS[1],
    COMPETITOR_COLOURS[4],
    COMPETITOR_COLOURS[5],
]


@dataclass
class PlatformVisibilityBrief:
    summary_table: pd.DataFrame
    chart_data: pd.DataFrame
    preview_chart_png: bytes
    export_chart_png: bytes


def build_platform_visibility_brief(df: pd.DataFrame, owned_label: str) -> PlatformVisibilityBrief:
    if df.empty or "model" not in df.columns:
        return PlatformVisibilityBrief(
            summary_table=pd.DataFrame(),
            chart_data=pd.DataFrame(),
            preview_chart_png=b"",
            export_chart_png=b"",
        )

    working = df.copy()
    working["model"] = working["model"].fillna("").astype(str).str.strip()
    working = working[working["model"] != ""].copy()
    if working.empty:
        return PlatformVisibilityBrief(
            summary_table=pd.DataFrame(),
            chart_data=pd.DataFrame(),
            preview_chart_png=b"",
            export_chart_png=b"",
        )

    rows: list[dict[str, object]] = []
    model_order = (
        working.groupby("model", dropna=False)["observation_weight"]
        .sum()
        .sort_values(ascending=False)
        .index.tolist()
    )

    for model in model_order:
        model_df = working[working["model"] == model].copy()
        total_weight = float(model_df["observation_weight"].sum())
        owned_df = model_df[model_df["source_type"] == "owned"].copy()
        competitor_df = model_df[model_df["source_type"] == "competitor"].copy()
        external_df = model_df[model_df["source_type"] == "external"].copy()

        owned_weight = float(owned_df["observation_weight"].sum())
        competitor_weight = float(competitor_df["observation_weight"].sum())
        external_weight = float(external_df["observation_weight"].sum())

        lead_competitor = ""
        lead_competitor_share = 0.0
        if not competitor_df.empty:
            competitor_totals = (
                competitor_df.groupby("competitor", dropna=False)["observation_weight"]
                .sum()
                .sort_values(ascending=False)
            )
            competitor_totals = competitor_totals[competitor_totals.index.astype(str).str.strip() != ""]
            if not competitor_totals.empty:
                lead_competitor = str(competitor_totals.index[0])
                lead_competitor_share = (float(competitor_totals.iloc[0]) / total_weight * 100) if total_weight else 0.0

        rows.append(
            {
                "Platform": model,
                f"{owned_label} share %": round((owned_weight / total_weight * 100) if total_weight else 0.0, 1),
                "Competitor share %": round((competitor_weight / total_weight * 100) if total_weight else 0.0, 1),
                "External share %": round((external_weight / total_weight * 100) if total_weight else 0.0, 1),
                "Weighted citations": round(total_weight, 1),
                "Prompts": int(model_df["prompt"].nunique()),
                "Owned URLs": int(owned_df["url"].nunique()),
                "Lead competitor": lead_competitor,
                "Lead competitor share %": round(lead_competitor_share, 1),
            }
        )

    summary_table = pd.DataFrame(rows)
    if summary_table.empty:
        return PlatformVisibilityBrief(
            summary_table=pd.DataFrame(),
            chart_data=pd.DataFrame(),
            preview_chart_png=b"",
            export_chart_png=b"",
        )

    summary_table = summary_table.sort_values(
        [f"{owned_label} share %", "Weighted citations", "Platform"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    best_share = float(summary_table[f"{owned_label} share %"].max()) if not summary_table.empty else 0.0
    summary_table["Gap to best platform %"] = (
        best_share - summary_table[f"{owned_label} share %"]
    ).round(1)
    summary_table = summary_table[
        [
            "Platform",
            f"{owned_label} share %",
            "Competitor share %",
            "External share %",
            "Gap to best platform %",
            "Weighted citations",
            "Prompts",
            "Owned URLs",
            "Lead competitor",
            "Lead competitor share %",
        ]
    ].copy()

    chart_data = summary_table[
        [
            "Platform",
            f"{owned_label} share %",
            "Competitor share %",
            "External share %",
        ]
    ].copy()
    preview_chart_png = build_platform_visibility_chart_png(chart_data, owned_label, transparent=False)
    export_chart_png = build_platform_visibility_chart_png(chart_data, owned_label, transparent=True)

    return PlatformVisibilityBrief(
        summary_table=summary_table,
        chart_data=chart_data,
        preview_chart_png=preview_chart_png,
        export_chart_png=export_chart_png,
    )


def build_platform_visibility_chart_png(
    chart_data: pd.DataFrame,
    owned_label: str,
    *,
    transparent: bool,
) -> bytes:
    if chart_data.empty:
        return b""

    platforms = chart_data["Platform"].tolist()
    values = chart_data[f"{owned_label} share %"].tolist()
    colours = [PLATFORM_COLOURS[index % len(PLATFORM_COLOURS)] for index, _ in enumerate(platforms)]

    figure, axis = plt.subplots(figsize=(13.5, 5.8), dpi=220)
    background = "none" if transparent else PREVIEW_BACKGROUND
    figure.patch.set_facecolor(background)
    axis.set_facecolor(background)

    positions = list(range(len(platforms)))
    bars = axis.bar(positions, values, color=colours, width=0.62, edgecolor="none", zorder=3)

    axis.tick_params(axis="x", colors="white", labelsize=10, length=0)
    axis.tick_params(axis="y", colors="white", labelsize=10)
    axis.set_xticks(positions)
    axis.set_xticklabels(platforms, rotation=20, ha="right", color="white")
    axis.grid(axis="y", color=(1, 1, 1, 0.28), linewidth=0.8, zorder=0)
    axis.grid(axis="x", visible=False)
    for spine in axis.spines.values():
        spine.set_visible(False)

    ymax = max(values) if values else 0.0
    axis.set_ylim(0, max(ymax * 1.18, 5))
    axis.set_xlabel("")
    axis.set_ylabel("")

    for bar, value in zip(bars, values):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            float(value) + max(ymax * 0.03, 0.8),
            f"{float(value):.1f}%",
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


def render_platform_visibility_brief(df: pd.DataFrame, owned_label: str) -> None:
    st.subheader("Platform visibility")
    st.caption(
        "Compare owned citation share across AI platforms. Leave the global model filter blank if you want a true cross-platform view."
    )

    brief = build_platform_visibility_brief(df, owned_label)
    if brief.summary_table.empty:
        st.info("No model rows are available for the current filter set.")
        return

    owned_share_column = f"{owned_label} share %"
    best_row = brief.summary_table.iloc[0]
    weakest_row = brief.summary_table.sort_values(owned_share_column, ascending=True).iloc[0]
    spread = float(best_row[owned_share_column]) - float(weakest_row[owned_share_column])

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Best platform", str(best_row["Platform"]), f"{float(best_row[owned_share_column]):.1f}%")
    metric_2.metric("Weakest platform", str(weakest_row["Platform"]), f"{float(weakest_row[owned_share_column]):.1f}%")
    metric_3.metric("Platform spread", f"{spread:.1f} pts")

    if brief.summary_table["Platform"].nunique() == 1:
        st.caption("Only one platform is in the current filter set, so this view is not showing a cross-platform comparison.")

    if brief.preview_chart_png:
        st.image(brief.preview_chart_png, use_container_width=True)

    download_1, download_2, download_3 = st.columns(3)
    with download_1:
        st.download_button(
            "Export platform visibility CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name="platform_visibility_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        st.download_button(
            "Export chart data CSV",
            brief.chart_data.to_csv(index=False).encode("utf-8"),
            file_name="platform_visibility_chart_data.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_3:
        st.download_button(
            "Download PNG chart",
            brief.export_chart_png,
            file_name="platform_visibility_chart.png",
            mime="image/png",
            use_container_width=True,
        )

    st.dataframe(brief.summary_table, use_container_width=True, hide_index=True)
