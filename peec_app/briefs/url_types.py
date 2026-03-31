from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from peec_app.renderers.copy_table import render_copy_table_button
from peec_app.renderers.png_table import render_table_png


ARTICLE_KEYWORDS = [
    "blog",
    "news",
    "insights",
    "article",
    "articles",
    "resource",
    "resources",
    "learn",
    "knowledge",
]
PRODUCT_KEYWORDS = [
    "product",
    "products",
    "pricing",
    "price",
    "shop",
    "buy",
    "software",
    "platform",
    "tool",
    "tools",
    "demo",
    "plan",
]
CATEGORY_KEYWORDS = [
    "category",
    "categories",
    "collection",
    "collections",
    "services",
    "solutions",
    "industries",
    "topics",
    "topic",
    "features",
    "use cases",
    "use-cases",
]
COMPARISON_KEYWORDS = [
    "compare",
    "comparison",
    "versus",
    "alternative",
    "alternatives",
]
HOW_TO_KEYWORDS = [
    "how to",
    "how-to",
    "guide",
    "tutorial",
    "walkthrough",
    "step by step",
    "step-by-step",
    "explainer",
]
LISTICLE_KEYWORDS = [
    "best",
    "top",
    "examples",
    "ideas",
    "reasons",
    "ways",
    "tips",
    "checklist",
    "tools",
    "strategies",
    "mistakes",
]


@dataclass
class UrlTypesBrief:
    summary_table: pd.DataFrame
    display_table: pd.DataFrame
    table_png: bytes
    total_citations: float



def format_count(value: object) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return ""
    if float(numeric).is_integer():
        return f"{int(numeric):,}"
    return f"{float(numeric):,.1f}"



def format_percentage(value: object) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return ""
    return f"{float(numeric):,.1f}"



def compact_url_label(value: object, max_length: int = 44) -> str:
    raw = "" if pd.isna(value) else str(value).strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    domain = parsed.netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    path = parsed.path.rstrip("/")
    label = f"{domain}{path}" if path else domain
    if len(label) <= max_length:
        return label
    return label[: max_length - 3].rstrip("/") + "..."



def summarise_top_urls(value: object, max_urls: int = 2) -> str:
    if pd.isna(value):
        return ""
    urls = [item.strip() for item in str(value).split(" | ") if item.strip()]
    if not urls:
        return ""
    compact = [compact_url_label(url) for url in urls]
    if len(compact) <= max_urls:
        return ", ".join(compact)
    shown = ", ".join(compact[:max_urls])
    remaining = len(compact) - max_urls
    suffix = "URL" if remaining == 1 else "URLs"
    return f"{shown} +{remaining} {suffix}"



def build_url_types_display_table(summary_table: pd.DataFrame) -> pd.DataFrame:
    display_table = summary_table.copy()
    display_table["Weighted citations"] = display_table["Weighted citations"].map(format_count)
    display_table["URLs"] = display_table["URLs"].map(format_count)
    display_table["Share %"] = display_table["Share %"].map(format_percentage)
    display_table["Top URLs"] = display_table["Top URLs"].map(summarise_top_urls)
    return display_table



def _normalise_url_signals(url: str, title: str) -> tuple[str, str, list[str]]:
    raw_url = str(url or "").strip()
    if "://" not in raw_url and raw_url:
        raw_url = f"https://{raw_url}"
    parsed = urlparse(raw_url)
    path = parsed.path.lower().strip()
    slug_text = re.sub(r"[-_/]+", " ", path)
    title_text = str(title or "").lower().strip()
    path_segments = [segment for segment in path.split("/") if segment]
    return slug_text, title_text, path_segments



def classify_url_type(url: str, title: str = "") -> str:
    raw_url = str(url or "").strip()
    if not raw_url:
        return "Other"
    if "://" not in raw_url:
        raw_url = f"https://{raw_url}"
    parsed = urlparse(raw_url)
    path = parsed.path.strip()
    slug_text, title_text, path_segments = _normalise_url_signals(raw_url, title)

    if path in {"", "/"}:
        return "Homepage"

    comparison_signal = any(keyword in slug_text or keyword in title_text for keyword in COMPARISON_KEYWORDS)
    if comparison_signal or re.search(r"\bvs\b", slug_text) or re.search(r"\bvs\b", title_text):
        return "Comparison"

    if any(keyword in slug_text or keyword in title_text for keyword in HOW_TO_KEYWORDS):
        return "How-To Guide"

    is_numbered_title = bool(re.search(r"\b\d{1,2}\b", title_text))
    listicle_signal = any(keyword in slug_text or keyword in title_text for keyword in LISTICLE_KEYWORDS)
    if listicle_signal or is_numbered_title:
        return "Listicle"

    if any(keyword in slug_text or keyword in title_text for keyword in PRODUCT_KEYWORDS):
        return "Product Page"

    if any(keyword in slug_text or keyword in title_text for keyword in CATEGORY_KEYWORDS):
        return "Category Page"

    if any(keyword in slug_text or keyword in title_text for keyword in ARTICLE_KEYWORDS):
        return "Article"

    if len(path_segments) >= 2 and any(segment in {"blog", "insights", "news", "resources"} for segment in path_segments):
        return "Article"

    return "Other"



def build_url_types_brief(df: pd.DataFrame) -> UrlTypesBrief:
    if df.empty:
        return UrlTypesBrief(
            summary_table=pd.DataFrame(),
            display_table=pd.DataFrame(),
            table_png=b"",
            total_citations=0.0,
        )

    working = df.copy()
    working["url_type"] = working.apply(
        lambda row: classify_url_type(row.get("url", ""), row.get("title", "")),
        axis=1,
    )
    type_summary = (
        working.groupby("url_type", dropna=False)
        .agg(
            weighted_citations=("observation_weight", "sum"),
            urls=("url", "nunique"),
        )
        .reset_index()
    )
    if type_summary.empty:
        return UrlTypesBrief(
            summary_table=pd.DataFrame(),
            display_table=pd.DataFrame(),
            table_png=b"",
            total_citations=0.0,
        )

    top_urls = (
        working.groupby(["url_type", "url"], dropna=False)["observation_weight"]
        .sum()
        .reset_index(name="weighted_citations")
        .sort_values(["url_type", "weighted_citations"], ascending=[True, False])
    )
    top_url_labels = (
        top_urls.groupby("url_type").head(3).groupby("url_type")["url"].apply(lambda values: " | ".join(values)).to_dict()
    )

    total_citations = float(type_summary["weighted_citations"].sum())
    type_summary["share_pct"] = ((type_summary["weighted_citations"] / total_citations) * 100).round(1) if total_citations else 0.0
    type_summary["top_urls"] = type_summary["url_type"].map(top_url_labels).fillna("")

    summary_table = type_summary.sort_values(
        ["share_pct", "weighted_citations", "url_type"],
        ascending=[False, False, True],
    )
    summary_table["weighted_citations"] = summary_table["weighted_citations"].round(1)
    summary_table = summary_table.rename(
        columns={
            "url_type": "URL type",
            "share_pct": "Share %",
            "weighted_citations": "Weighted citations",
            "urls": "URLs",
            "top_urls": "Top URLs",
        }
    ).reset_index(drop=True)
    summary_table = summary_table[
        [
            "URL type",
            "Share %",
            "Weighted citations",
            "URLs",
            "Top URLs",
        ]
    ].copy()
    display_table = build_url_types_display_table(summary_table)

    table_png = render_table_png(
        display_table,
        title="URL types",
        subtitle=f"Total citations: {format_count(total_citations)}",
        max_cell_chars=40,
        transparent=True,
    )
    return UrlTypesBrief(
        summary_table=summary_table,
        display_table=display_table,
        table_png=table_png,
        total_citations=total_citations,
    )



def render_url_types_brief(df: pd.DataFrame) -> None:
    st.subheader("URL types")
    st.caption(
        "Rule-based URL classification using path and title signals. This is heuristic and intended as a working brief, not a perfect taxonomy."
    )

    brief = build_url_types_brief(df)
    if brief.summary_table.empty:
        st.info("No URL rows are available for the current filter set.")
        return

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Total weighted citations", format_count(brief.total_citations))
    metric_2.metric("URL types", str(len(brief.summary_table)))
    metric_3.metric("URLs", f"{df['url'].nunique():,}")

    if brief.table_png:
        st.markdown("**PNG Table Preview**")
        st.image(brief.table_png, use_container_width=True)

    download_1, download_2, download_3 = st.columns(3)
    with download_1:
        st.download_button(
            "Export URL types CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name="url_types_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        st.download_button(
            "Download PNG table image",
            brief.table_png,
            file_name="url_types_summary.png",
            mime="image/png",
            use_container_width=True,
        )
    with download_3:
        render_copy_table_button(
            brief.display_table,
            button_label="Copy table for PowerPoint",
            key="url-types-table",
        )

    with st.expander("View raw table data"):
        st.dataframe(brief.display_table, use_container_width=True, hide_index=True)
