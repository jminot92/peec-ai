from __future__ import annotations

import pandas as pd


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


def percentage_band(
    value: object,
    *,
    severe: float = 80.0,
    high: float = 60.0,
    medium: float = 40.0,
) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return ""
    numeric = float(numeric)
    if numeric >= severe:
        return "Severe"
    if numeric >= high:
        return "High"
    if numeric >= medium:
        return "Medium"
    return "Low"


def top_labels(values: pd.Series, max_items: int = 2, separator: str = ", ") -> str:
    labels = [str(value).strip() for value in values.fillna("").astype(str) if str(value).strip()]
    unique_labels = []
    seen: set[str] = set()
    for label in labels:
        if label in seen:
            continue
        unique_labels.append(label)
        seen.add(label)
    if not unique_labels:
        return ""
    if len(unique_labels) <= max_items:
        return separator.join(unique_labels)
    shown = separator.join(unique_labels[:max_items])
    remaining = len(unique_labels) - max_items
    suffix = "item" if remaining == 1 else "items"
    return f"{shown} +{remaining} {suffix}"
