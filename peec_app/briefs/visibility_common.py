from __future__ import annotations

import pandas as pd


OWNED_COLOUR = "#E22A8A"
COMPETITOR_COLOURS = [
    "#86D8FF",
    "#59B8FF",
    "#275DAD",
    "#8F9AAD",
    "#5A8F7B",
    "#B5C4D8",
]
PREVIEW_BACKGROUND = "#07131A"


def build_competitive_rows(df: pd.DataFrame, owned_label: str) -> pd.DataFrame:
    competitive_rows = df[df["source_type"].isin(["owned", "competitor"])].copy()
    if competitive_rows.empty:
        return competitive_rows
    competitive_rows["entity"] = competitive_rows.apply(
        lambda row: owned_label
        if row["source_type"] == "owned"
        else (row["competitor"] or row["source_domain"]),
        axis=1,
    )
    competitive_rows["entity_type"] = competitive_rows["source_type"].map(
        {"owned": "owned", "competitor": "competitor"}
    )
    competitive_rows = competitive_rows[competitive_rows["entity"].astype(str).str.strip() != ""].copy()
    return competitive_rows


def competitor_options(df: pd.DataFrame, owned_label: str) -> list[str]:
    competitive_rows = build_competitive_rows(df, owned_label)
    if competitive_rows.empty:
        return []
    competitor_totals = (
        competitive_rows[competitive_rows["entity_type"] == "competitor"]
        .groupby("entity", dropna=False)["observation_weight"]
        .sum()
        .sort_values(ascending=False)
    )
    return competitor_totals.index.tolist()


def default_competitor_selection(options: list[str]) -> list[str]:
    return options[: min(5, len(options))]


def entity_order(summary_table: pd.DataFrame, owned_label: str) -> list[str]:
    if summary_table.empty:
        return []
    owned_entities = summary_table[summary_table["entity_type"] == "owned"]["entity"].tolist()
    competitor_entities = summary_table[summary_table["entity_type"] != "owned"]["entity"].tolist()
    ordered = owned_entities + competitor_entities
    if owned_label in ordered:
        ordered = [owned_label] + [entity for entity in ordered if entity != owned_label]
    return ordered


def entity_colours(entities: list[str], owned_label: str) -> dict[str, str]:
    colours: dict[str, str] = {}
    remaining_colours = COMPETITOR_COLOURS.copy()
    for entity in entities:
        if entity == owned_label:
            colours[entity] = OWNED_COLOUR
            continue
        if not remaining_colours:
            remaining_colours = COMPETITOR_COLOURS.copy()
        colours[entity] = remaining_colours.pop(0)
    return colours
