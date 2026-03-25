from __future__ import annotations

import os
from typing import Iterable
from urllib.parse import urlparse

import pandas as pd
import streamlit as st


def clean_column_name(column_name: str) -> str:
    return (
        str(column_name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )



def normalise_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()



def normalise_name_key(value: object) -> str:
    text = normalise_text(value).lower()
    simplified = "".join(character if character.isalnum() else " " for character in text)
    return " ".join(simplified.split())



def extract_domain(value: object) -> str:
    if pd.isna(value):
        return ""
    raw = str(value).strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    domain = parsed.netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain



def split_tags(value: object) -> list[str]:
    text = normalise_text(value)
    if not text:
        return []
    for separator in ["|", ";", "/"]:
        text = text.replace(separator, ",")
    tags = [item.strip() for item in text.split(",")]
    return [tag for tag in tags if tag]



def domain_matches(domain: str, candidates: Iterable[str]) -> bool:
    for candidate in candidates:
        candidate = candidate.strip().lower()
        if not candidate:
            continue
        if domain == candidate or domain.endswith(f".{candidate}"):
            return True
    return False



def format_date(value: object) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).date().isoformat()



def coerce_positive_number(value: object, default: float = 0.0) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return default
    return max(float(numeric), 0.0)



def build_project_label(project: dict[str, object]) -> str:
    project_id = normalise_text(project.get("id"))
    project_name = normalise_text(project.get("name")) or project_id or "Unnamed project"
    project_status = normalise_text(project.get("status")).upper()
    if project_status:
        return f"{project_name} [{project_status}] ({project_id})"
    return f"{project_name} ({project_id})" if project_id else project_name



def get_secret_or_env(key: str, default: str = "") -> str:
    if key in st.secrets:
        value = st.secrets[key]
        if value is None:
            return default
        return str(value).strip()
    return os.getenv(key, default).strip()
