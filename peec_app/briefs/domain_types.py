from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from peec_app.renderers.png_table import render_table_png


UGC_DOMAINS = {
    "reddit.com",
    "quora.com",
    "stackexchange.com",
    "stackoverflow.com",
    "medium.com",
    "discord.com",
    "tiktok.com",
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "x.com",
    "twitter.com",
    "pinterest.com",
}
REFERENCE_DOMAINS = {
    "wikipedia.org",
    "wikidata.org",
    "britannica.com",
    "dictionary.com",
    "merriam-webster.com",
    "cambridge.org",
    "investopedia.com",
    "fandom.com",
}
EDITORIAL_DOMAINS = {
    "bbc.com",
    "theguardian.com",
    "nytimes.com",
    "wsj.com",
    "forbes.com",
    "searchengineland.com",
    "searchenginejournal.com",
    "businessinsider.com",
    "reuters.com",
    "ft.com",
}
REFERENCE_KEYWORDS = ["wiki", "dictionary", "glossary", "reference", "encyclopedia"]
EDITORIAL_KEYWORDS = ["news", "journal", "magazine", "press", "media", "times", "post", "herald", "tribune", "observer", "chronicle", "gazette"]
INSTITUTIONAL_KEYWORDS = ["gov", "government", "university", "college", "institute", "academy", "nhs", "council", "association", "society", "foundation", "charity"]
INSTITUTIONAL_SUFFIXES = [".gov", ".gov.uk", ".edu", ".ac.uk", ".nhs.uk", ".org.uk"]


@dataclass
class DomainTypesBrief:
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


def summarise_top_domains(value: object, max_domains: int = 2) -> str:
    if pd.isna(value):
        return ""
    domains = [item.strip() for item in str(value).split(",") if item.strip()]
    if not domains:
        return ""
    if len(domains) <= max_domains:
        return ", ".join(domains)
    shown = ", ".join(domains[:max_domains])
    remaining = len(domains) - max_domains
    suffix = "domain" if remaining == 1 else "domains"
    return f"{shown} +{remaining} {suffix}"


def build_domain_types_display_table(summary_table: pd.DataFrame) -> pd.DataFrame:
    display_table = summary_table.copy()
    display_table["Weighted citations"] = display_table["Weighted citations"].map(format_count)
    display_table["Domains"] = display_table["Domains"].map(format_count)
    display_table["Share %"] = display_table["Share %"].map(format_percentage)
    display_table["Top domains"] = display_table["Top domains"].map(
        summarise_top_domains
    )
    return display_table



def classify_domain_type(source_domain: str, source_type: str) -> str:
    domain = str(source_domain or "").lower().strip()
    source = str(source_type or "").lower().strip()
    if source == "owned":
        return "You"
    if source == "competitor":
        return "Competitor"
    if not domain:
        return "Other"
    if any(domain == candidate or domain.endswith(f".{candidate}") for candidate in UGC_DOMAINS):
        return "UGC"
    if any(domain == candidate or domain.endswith(f".{candidate}") for candidate in REFERENCE_DOMAINS):
        return "Reference"
    if any(domain == candidate or domain.endswith(f".{candidate}") for candidate in EDITORIAL_DOMAINS):
        return "Editorial"
    if any(keyword in domain for keyword in REFERENCE_KEYWORDS):
        return "Reference"
    if any(domain.endswith(suffix) for suffix in INSTITUTIONAL_SUFFIXES):
        return "Institutional"
    if any(keyword in domain for keyword in INSTITUTIONAL_KEYWORDS):
        return "Institutional"
    if any(keyword in domain for keyword in EDITORIAL_KEYWORDS):
        return "Editorial"
    if any(domain.endswith(suffix) for suffix in [".org", ".ngo"]):
        return "Institutional"
    if domain:
        return "Corporate"
    return "Other"



def build_domain_types_brief(df: pd.DataFrame) -> DomainTypesBrief:
    if df.empty:
        return DomainTypesBrief(
            summary_table=pd.DataFrame(),
            display_table=pd.DataFrame(),
            table_png=b"",
            total_citations=0.0,
        )

    working = df.copy()
    working["domain_type"] = working.apply(
        lambda row: classify_domain_type(row.get("source_domain", ""), row.get("source_type", "")),
        axis=1,
    )
    type_summary = (
        working.groupby("domain_type", dropna=False)
        .agg(
            weighted_citations=("observation_weight", "sum"),
            domains=("source_domain", "nunique"),
        )
        .reset_index()
    )
    if type_summary.empty:
        return DomainTypesBrief(
            summary_table=pd.DataFrame(),
            display_table=pd.DataFrame(),
            table_png=b"",
            total_citations=0.0,
        )

    top_domains = (
        working.groupby(["domain_type", "source_domain"], dropna=False)["observation_weight"]
        .sum()
        .reset_index(name="weighted_citations")
        .sort_values(["domain_type", "weighted_citations"], ascending=[True, False])
    )
    top_domain_labels = (
        top_domains.groupby("domain_type").head(3).groupby("domain_type")["source_domain"].apply(lambda values: ", ".join(values)).to_dict()
    )

    total_citations = float(type_summary["weighted_citations"].sum())
    type_summary["share_pct"] = ((type_summary["weighted_citations"] / total_citations) * 100).round(1) if total_citations else 0.0
    type_summary["top_domains"] = type_summary["domain_type"].map(top_domain_labels).fillna("")

    summary_table = type_summary.sort_values(
        ["share_pct", "weighted_citations", "domain_type"],
        ascending=[False, False, True],
    )
    summary_table["weighted_citations"] = summary_table["weighted_citations"].round(1)
    summary_table = summary_table.rename(
        columns={
            "domain_type": "Domain type",
            "share_pct": "Share %",
            "weighted_citations": "Weighted citations",
            "domains": "Domains",
            "top_domains": "Top domains",
        }
    ).reset_index(drop=True)
    summary_table = summary_table[
        [
            "Domain type",
            "Share %",
            "Weighted citations",
            "Domains",
            "Top domains",
        ]
    ].copy()
    display_table = build_domain_types_display_table(summary_table)

    table_png = render_table_png(
        display_table,
        title="Domain types",
        subtitle=f"Total citations: {format_count(total_citations)}",
        max_cell_chars=38,
        transparent=True,
    )
    return DomainTypesBrief(
        summary_table=summary_table,
        display_table=display_table,
        table_png=table_png,
        total_citations=total_citations,
    )



def render_domain_types_brief(df: pd.DataFrame) -> None:
    st.subheader("Domain types")
    st.caption(
        "Rule-based grouping of cited domains into PEEC-style source buckets. This is heuristic and intended as a working brief, not a perfect taxonomy."
    )

    brief = build_domain_types_brief(df)
    if brief.summary_table.empty:
        st.info("No domain rows are available for the current filter set.")
        return

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Total weighted citations", format_count(brief.total_citations))
    metric_2.metric("Domain types", str(len(brief.summary_table)))
    metric_3.metric("Domains", f"{df['source_domain'].nunique():,}")

    if brief.table_png:
        st.markdown("**PNG Table Preview**")
        st.image(brief.table_png, use_container_width=True)

    download_1, download_2 = st.columns(2)
    with download_1:
        st.download_button(
            "Export domain types CSV",
            brief.summary_table.to_csv(index=False).encode("utf-8"),
            file_name="domain_types_summary.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_2:
        st.download_button(
            "Download PNG table image",
            brief.table_png,
            file_name="domain_types_summary.png",
            mime="image/png",
            use_container_width=True,
        )

    with st.expander("View raw table data"):
        st.dataframe(brief.display_table, use_container_width=True, hide_index=True)
