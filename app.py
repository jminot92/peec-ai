from __future__ import annotations

from dataclasses import dataclass
import os
import time
from typing import Iterable
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests
import streamlit as st


PEEC_API_BASE_URL = "https://api.peec.ai/customer/v1"
REQUIRED_COLUMNS = [
    "topic",
    "prompt",
    "url",
    "source_domain",
    "model",
    "date",
    "competitor",
]
OPTIONAL_RANK_COLUMNS = ["answer_rank", "rank", "position"]
ALLOWED_SOURCE_TYPES = {"owned", "competitor", "external"}
DEFAULT_API_FETCH_DAYS = 30
DEFAULT_API_PAGE_SIZE = 1000
MAX_API_ROWS = 20000


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
            --peec-bg: #f6f2ea;
            --peec-panel: rgba(255, 255, 255, 0.82);
            --peec-panel-strong: rgba(255, 252, 247, 0.94);
            --peec-card: rgba(255, 255, 255, 0.9);
            --peec-ink: #13262f;
            --peec-muted: #53656d;
            --peec-accent: #d94f30;
            --peec-accent-soft: #f7c9bd;
            --peec-mint: #5a8f7b;
            --peec-sand: #e9d7af;
            --peec-line: rgba(19, 38, 47, 0.1);
            --peec-shadow: rgba(19, 38, 47, 0.08);
            --peec-chip-bg: rgba(19, 38, 47, 0.06);
            --peec-score-bg: rgba(90, 143, 123, 0.13);
            --peec-score-ink: #2e5a49;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --peec-bg: #0f171b;
                --peec-panel: rgba(20, 29, 35, 0.82);
                --peec-panel-strong: rgba(24, 34, 40, 0.94);
                --peec-card: rgba(16, 24, 30, 0.92);
                --peec-ink: #eef3f5;
                --peec-muted: #a8b7be;
                --peec-accent-soft: rgba(217, 79, 48, 0.18);
                --peec-sand: rgba(233, 215, 175, 0.16);
                --peec-line: rgba(238, 243, 245, 0.1);
                --peec-shadow: rgba(0, 0, 0, 0.32);
                --peec-chip-bg: rgba(238, 243, 245, 0.08);
                --peec-score-bg: rgba(90, 143, 123, 0.22);
                --peec-score-ink: #cde6db;
            }
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(217, 79, 48, 0.16), transparent 24%),
                radial-gradient(circle at bottom left, rgba(90, 143, 123, 0.2), transparent 26%),
                linear-gradient(180deg, color-mix(in srgb, var(--peec-bg) 92%, white 8%) 0%, var(--peec-bg) 100%);
            color: var(--peec-ink);
            font-family: "IBM Plex Sans", sans-serif;
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.03em;
            color: var(--peec-ink);
        }

        .hero-panel {
            background: linear-gradient(135deg, var(--peec-panel-strong), var(--peec-panel));
            border: 1px solid var(--peec-line);
            border-radius: 24px;
            padding: 1.4rem 1.5rem 1.2rem 1.5rem;
            box-shadow: 0 18px 40px var(--peec-shadow);
            margin-bottom: 1rem;
        }

        .section-panel {
            background: var(--peec-panel);
            border: 1px solid var(--peec-line);
            border-radius: 20px;
            padding: 1rem 1rem 0.8rem 1rem;
            box-shadow: 0 12px 30px color-mix(in srgb, var(--peec-shadow) 70%, transparent);
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.8rem;
        }

        .chip {
            border-radius: 999px;
            padding: 0.32rem 0.72rem;
            font-size: 0.82rem;
            font-weight: 600;
            background: var(--peec-chip-bg);
            color: var(--peec-ink);
        }

        .chip-accent {
            background: var(--peec-accent-soft);
            color: var(--peec-accent);
        }

        .action-card {
            background: var(--peec-card);
            border: 1px solid var(--peec-line);
            border-radius: 18px;
            padding: 1rem;
            min-height: 196px;
        }

        .action-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--peec-muted);
            margin-bottom: 0.35rem;
        }

        .action-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.12rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }

        .action-score {
            display: inline-block;
            padding: 0.24rem 0.55rem;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.84rem;
            background: var(--peec-score-bg);
            color: var(--peec-score-ink);
        }

        [data-testid="stMetric"] {
            background: var(--peec-card);
            border: 1px solid var(--peec-line);
            border-radius: 18px;
            padding: 0.8rem 0.9rem;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"],
        [data-testid="stMetricDeltaDescription"] {
            color: var(--peec-ink) !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--peec-panel-strong), var(--peec-panel));
            border-right: 1px solid var(--peec-line);
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .stMarkdown {
            color: var(--peec-ink) !important;
        }

        [data-baseweb="tab-list"] button {
            color: var(--peec-muted) !important;
        }

        [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: var(--peec-accent) !important;
        }

        [data-baseweb="tab-highlight"] {
            background-color: var(--peec-accent) !important;
        }

        [data-baseweb="tab-border"] {
            background-color: var(--peec-line) !important;
        }

        .small-note {
            color: var(--peec-muted);
            font-size: 0.9rem;
        }

        @media (max-width: 900px) {
            .hero-panel {
                padding: 1.05rem;
            }
            .action-card {
                min-height: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def to_percentage(series: pd.Series) -> pd.Series:
    return (series * 100).round(1)


def score_band(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def first_valid(series: pd.Series) -> str:
    values = [str(value) for value in series.dropna().astype(str) if str(value).strip()]
    return values[0] if values else ""


def build_project_label(project: dict[str, object]) -> str:
    project_id = normalise_text(project.get("id"))
    project_name = normalise_text(project.get("name")) or project_id or "Unnamed project"
    project_status = normalise_text(project.get("status")).upper()
    if project_status:
        return f"{project_name} [{project_status}] ({project_id})"
    return f"{project_name} ({project_id})" if project_id else project_name


def top_weighted_value(df: pd.DataFrame, value_column: str) -> str:
    if df.empty:
        return ""
    weights = (
        df.groupby(value_column, dropna=True)["observation_weight"]
        .sum()
        .sort_values(ascending=False)
    )
    return str(weights.index[0]) if not weights.empty else ""


def get_secret_or_env(key: str, default: str = "") -> str:
    if key in st.secrets:
        value = st.secrets[key]
        if value is None:
            return default
        return str(value).strip()
    return os.getenv(key, default).strip()


def format_date(value: object) -> str:
    if pd.isna(value):
        return ""
    return pd.Timestamp(value).date().isoformat()


def coerce_positive_number(value: object, default: float = 0.0) -> float:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return default
    return max(float(numeric), 0.0)


class PeecApiClient:
    def __init__(self, api_key: str, base_url: str = PEEC_API_BASE_URL, timeout: int = 30) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, object] | None = None,
        json_payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if not self.api_key:
            raise ValueError("A PEEC API key is required.")

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }
        url = f"{self.base_url}/{path.lstrip('/')}"

        for attempt in range(4):
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_payload,
                timeout=self.timeout,
            )
            if response.status_code != 429:
                break
            reset_after = int(response.headers.get("X-RateLimit-Reset", "1"))
            time.sleep(max(reset_after, 1))

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            message = response.text.strip() or str(exc)
            raise RuntimeError(f"PEEC API request failed: {message}") from exc

        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("PEEC API returned an unexpected response.")
        return payload

    def _with_project(self, project_id: str | None, params: dict[str, object] | None = None) -> dict[str, object]:
        merged = dict(params or {})
        if project_id:
            merged["project_id"] = project_id
        return merged

    def _paginate(
        self,
        path: str,
        *,
        method: str = "GET",
        project_id: str | None = None,
        params: dict[str, object] | None = None,
        json_payload: dict[str, object] | None = None,
        page_size: int = DEFAULT_API_PAGE_SIZE,
        max_rows: int = MAX_API_ROWS,
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        offset = 0

        while offset < max_rows:
            if method == "GET":
                page_params = self._with_project(
                    project_id,
                    {
                        **(params or {}),
                        "limit": page_size,
                        "offset": offset,
                    },
                )
                payload = self._request(method, path, params=page_params)
            else:
                body = {
                    **(json_payload or {}),
                    "limit": page_size,
                    "offset": offset,
                }
                if project_id:
                    body["project_id"] = project_id
                payload = self._request(method, path, json_payload=body)

            batch = payload.get("data", [])
            if not isinstance(batch, list):
                raise RuntimeError("PEEC API returned an unexpected page payload.")
            rows.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size

        return rows

    def get_projects(self) -> list[dict[str, object]]:
        return self._paginate("projects", max_rows=1000)

    def get_models(self, project_id: str | None = None) -> list[dict[str, object]]:
        return self._paginate("models", project_id=project_id, max_rows=1000)

    def get_prompts(self, project_id: str | None = None) -> list[dict[str, object]]:
        return self._paginate("prompts", project_id=project_id, max_rows=10000)

    def get_topics(self, project_id: str | None = None) -> list[dict[str, object]]:
        return self._paginate("topics", project_id=project_id, max_rows=5000)

    def get_tags(self, project_id: str | None = None) -> list[dict[str, object]]:
        return self._paginate("tags", project_id=project_id, max_rows=5000)

    def get_brands(self, project_id: str | None = None) -> list[dict[str, object]]:
        return self._paginate("brands", project_id=project_id, max_rows=5000)

    def get_urls_report(
        self,
        *,
        project_id: str | None,
        start_date: str,
        end_date: str,
        page_size: int = DEFAULT_API_PAGE_SIZE,
        max_rows: int = MAX_API_ROWS,
    ) -> list[dict[str, object]]:
        return self._paginate(
            "reports/urls",
            method="POST",
            project_id=project_id,
            json_payload={
                "start_date": start_date,
                "end_date": end_date,
                "dimensions": ["prompt_id", "model_id", "date"],
            },
            page_size=page_size,
            max_rows=max_rows,
        )


def build_brand_domain_lookup(
    brands: list[dict[str, object]],
    owned_domains: list[str],
) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for brand in brands:
        brand_name = normalise_text(brand.get("name") if isinstance(brand, dict) else "")
        domains = brand.get("domains", []) if isinstance(brand, dict) else []
        if not brand_name or not isinstance(domains, list):
            continue
        for raw_domain in domains:
            domain = extract_domain(raw_domain)
            if not domain or domain_matches(domain, owned_domains):
                continue
            lookup[domain] = brand_name
    return lookup


def lookup_competitor(domain: str, brand_domains: dict[str, str]) -> str:
    if domain in brand_domains:
        return brand_domains[domain]
    for candidate, brand_name in brand_domains.items():
        if domain_matches(domain, [candidate]):
            return brand_name
    return ""

@st.cache_data(ttl=900, show_spinner=False)
def fetch_peec_projects(api_key: str, base_url: str) -> list[dict[str, object]]:
    client = PeecApiClient(api_key=api_key, base_url=base_url)
    return client.get_projects()


@st.cache_data(ttl=900, show_spinner=False)
def fetch_peec_metadata(
    api_key: str,
    base_url: str,
    project_id: str | None,
) -> dict[str, list[dict[str, object]]]:
    client = PeecApiClient(api_key=api_key, base_url=base_url)
    return {
        "prompts": client.get_prompts(project_id=project_id),
        "topics": client.get_topics(project_id=project_id),
        "tags": client.get_tags(project_id=project_id),
        "models": client.get_models(project_id=project_id),
        "brands": client.get_brands(project_id=project_id),
    }


@st.cache_data(ttl=900, show_spinner=False)
def fetch_peec_report_rows(
    api_key: str,
    base_url: str,
    project_id: str | None,
    start_date: str,
    end_date: str,
    page_size: int,
    max_rows: int,
) -> list[dict[str, object]]:
    client = PeecApiClient(api_key=api_key, base_url=base_url)
    return client.get_urls_report(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        page_size=page_size,
        max_rows=max_rows,
    )


def build_dataframe_from_peec_api(
    api_rows: list[dict[str, object]],
    metadata: dict[str, list[dict[str, object]]],
    owned_domains: list[str],
    project_id: str | None = None,
    project_name: str = "",
    project_status: str = "",
) -> pd.DataFrame:
    prompts_by_id = {
        prompt["id"]: prompt
        for prompt in metadata.get("prompts", [])
        if isinstance(prompt, dict) and prompt.get("id")
    }
    topics_by_id = {
        topic["id"]: normalise_text(topic.get("name"))
        for topic in metadata.get("topics", [])
        if isinstance(topic, dict) and topic.get("id")
    }
    tags_by_id = {
        tag["id"]: normalise_text(tag.get("name"))
        for tag in metadata.get("tags", [])
        if isinstance(tag, dict) and tag.get("id")
    }
    brand_domains = build_brand_domain_lookup(metadata.get("brands", []), owned_domains)

    rows: list[dict[str, object]] = []
    for item in api_rows:
        if not isinstance(item, dict):
            continue
        prompt_ref = item.get("prompt", {})
        model_ref = item.get("model", {})
        prompt_id = normalise_text(prompt_ref.get("id") if isinstance(prompt_ref, dict) else "")
        model_id = normalise_text(model_ref.get("id") if isinstance(model_ref, dict) else "")
        prompt_meta = prompts_by_id.get(prompt_id, {})
        topic_meta = prompt_meta.get("topic", {}) if isinstance(prompt_meta, dict) else {}
        topic_id = normalise_text(topic_meta.get("id") if isinstance(topic_meta, dict) else "")
        prompt_messages = prompt_meta.get("messages", []) if isinstance(prompt_meta, dict) else []
        prompt_content = ""
        if isinstance(prompt_messages, list):
            for message in prompt_messages:
                if not isinstance(message, dict):
                    continue
                prompt_content = normalise_text(message.get("content"))
                if prompt_content:
                    break
        tag_values = []
        for tag in prompt_meta.get("tags", []) if isinstance(prompt_meta, dict) else []:
            if not isinstance(tag, dict):
                continue
            tag_name = tags_by_id.get(normalise_text(tag.get("id")), normalise_text(tag.get("name")))
            if tag_name:
                tag_values.append(tag_name)

        url = normalise_text(item.get("url"))
        source_domain = extract_domain(url)
        competitor = lookup_competitor(source_domain, brand_domains)

        rows.append(
            {
                "project": project_name or project_id or "Current project",
                "project_id": project_id or "",
                "project_status": project_status,
                "topic": topics_by_id.get(topic_id, normalise_text(topic_meta.get("name") if isinstance(topic_meta, dict) else "")),
                "prompt": prompt_content
                or normalise_text(prompt_meta.get("query") or prompt_meta.get("name") or prompt_meta.get("prompt")),
                "url": url,
                "source_domain": source_domain,
                "model": model_id,
                "date": format_date(item.get("date")),
                "competitor": competitor,
                "tag": " | ".join(sorted(set(tag_values))),
                "usage_count": coerce_positive_number(item.get("usage_count"), default=1.0),
                "citation_count": coerce_positive_number(item.get("citation_count"), default=0.0),
                "retrievals": coerce_positive_number(item.get("retrievals"), default=0.0),
                "citation_rate": coerce_positive_number(item.get("citation_rate"), default=0.0),
                "title": normalise_text(item.get("title")),
            }
        )

    return pd.DataFrame(rows)


def normalise_peec_data(
    df: pd.DataFrame,
    owned_domains: list[str],
) -> tuple[pd.DataFrame, dict[str, object]]:
    working = df.copy()
    working.columns = [clean_column_name(column) for column in working.columns]

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in working.columns]
    if missing_columns:
        raise ValueError(
            "Missing required columns: " + ", ".join(sorted(missing_columns))
        )

    if "tag" not in working.columns:
        working["tag"] = ""
    if "source_type" not in working.columns:
        working["source_type"] = ""
    if "project" not in working.columns:
        working["project"] = ""
    if "project_status" not in working.columns:
        working["project_status"] = ""
    if "observation_weight" not in working.columns:
        if "usage_count" in working.columns:
            working["observation_weight"] = pd.to_numeric(working["usage_count"], errors="coerce")
        elif "citation_count" in working.columns:
            working["observation_weight"] = pd.to_numeric(working["citation_count"], errors="coerce")
        elif "retrievals" in working.columns:
            working["observation_weight"] = pd.to_numeric(working["retrievals"], errors="coerce")
        else:
            working["observation_weight"] = 1.0

    working["topic"] = working["topic"].map(normalise_text)
    working["prompt"] = working["prompt"].map(normalise_text)
    working["url"] = working["url"].map(normalise_text)
    working["model"] = working["model"].map(normalise_text)
    working["competitor"] = working["competitor"].map(normalise_text)
    working["tag"] = working["tag"].map(normalise_text)
    working["project"] = working["project"].map(normalise_text)
    working["project_status"] = working["project_status"].map(normalise_text)
    working["source_domain"] = (
        working["source_domain"].map(normalise_text).str.lower().str.replace("www.", "", regex=False)
    )
    working["source_domain"] = working["source_domain"].where(
        working["source_domain"] != "",
        working["url"].map(extract_domain),
    )

    rank_column = next(
        (column for column in OPTIONAL_RANK_COLUMNS if column in working.columns),
        None,
    )
    working["influence_weight"] = 1.0
    if rank_column:
        ranks = pd.to_numeric(working[rank_column], errors="coerce").clip(lower=1, upper=10)
        working["influence_weight"] = (
            1.15 - ((ranks.fillna(2.5) - 1) * 0.08)
        ).clip(lower=0.35, upper=1.15)

    working["date"] = pd.to_datetime(working["date"], errors="coerce").dt.normalize()

    derived_source_type = np.select(
        [
            working["source_domain"].map(lambda value: domain_matches(value, owned_domains)),
            working["competitor"].str.strip() != "",
        ],
        ["owned", "competitor"],
        default="external",
    )
    existing_source_type = (
        working["source_type"]
        .map(normalise_text)
        .str.lower()
        .replace({"press": "external", "publisher": "external"})
    )
    working["source_type"] = np.where(
        existing_source_type.isin(ALLOWED_SOURCE_TYPES),
        existing_source_type,
        derived_source_type,
    )
    working["tag_list"] = working["tag"].apply(split_tags)
    working["observation_weight"] = (
        pd.to_numeric(working["observation_weight"], errors="coerce").fillna(1.0).clip(lower=0.0)
    )
    working["observation_weight"] = working["observation_weight"].where(
        working["observation_weight"] > 0,
        1.0,
    )

    before_rows = len(working)
    working = working.dropna(subset=["date"])
    working = working[
        (working["topic"] != "")
        & (working["prompt"] != "")
        & (working["url"] != "")
        & (working["source_domain"] != "")
        & (working["model"] != "")
    ].copy()
    dropped_rows = before_rows - len(working)

    metadata = {
        "dropped_rows": dropped_rows,
        "date_min": working["date"].min() if not working.empty else None,
        "date_max": working["date"].max() if not working.empty else None,
        "total_observations": float(working["observation_weight"].sum()) if not working.empty else 0.0,
    }
    return working, metadata


def apply_filters(
    df: pd.DataFrame,
    date_range: tuple[pd.Timestamp, pd.Timestamp],
    projects: list[str],
    models: list[str],
    topic_or_tags: list[str],
    competitors: list[str],
    source_types: list[str],
) -> pd.DataFrame:
    filtered = df.copy()
    start_date, end_date = date_range
    filtered = filtered[
        (filtered["date"] >= pd.Timestamp(start_date))
        & (filtered["date"] <= pd.Timestamp(end_date))
    ]

    if projects:
        filtered = filtered[filtered["project"].isin(projects)]

    if models:
        filtered = filtered[filtered["model"].isin(models)]

    if topic_or_tags:
        topic_set = set(topic_or_tags)
        filtered = filtered[
            filtered["topic"].isin(topic_set)
            | filtered["tag_list"].apply(lambda tags: bool(topic_set.intersection(tags)))
        ]

    if competitors:
        filtered = filtered[
            (filtered["source_type"] != "competitor")
            | filtered["competitor"].isin(competitors)
        ]

    if source_types:
        filtered = filtered[filtered["source_type"].isin(source_types)]

    return filtered


def compute_trends(df: pd.DataFrame, group_fields: list[str]) -> pd.DataFrame:
    latest_date = df["date"].max()
    current_start = latest_date - pd.Timedelta(days=6)
    previous_start = current_start - pd.Timedelta(days=7)

    current_window = df[df["date"] >= current_start]
    previous_window = df[
        (df["date"] < current_start) & (df["date"] >= previous_start)
    ]

    current_counts = (
        current_window.groupby(group_fields)
        ["observation_weight"]
        .sum()
        .rename("current_week_mentions")
        .reset_index()
    )
    previous_counts = (
        previous_window.groupby(group_fields)
        ["observation_weight"]
        .sum()
        .rename("previous_week_mentions")
        .reset_index()
    )

    merged = current_counts.merge(previous_counts, on=group_fields, how="outer").fillna(0)
    merged["current_week_mentions"] = merged["current_week_mentions"].round(1)
    merged["previous_week_mentions"] = merged["previous_week_mentions"].round(1)
    merged["trend_ratio"] = np.where(
        merged["previous_week_mentions"] > 0,
        (merged["current_week_mentions"] - merged["previous_week_mentions"])
        / merged["previous_week_mentions"],
        np.where(merged["current_week_mentions"] > 0, 1.0, 0.0),
    )
    merged["trend_ratio"] = merged["trend_ratio"].clip(lower=-1.0, upper=1.5)
    return merged


def build_topic_summary(df: pd.DataFrame) -> pd.DataFrame:
    prompt_coverage = (
        df.groupby(["topic", "prompt"])
        .agg(
            prompt_mentions=("observation_weight", "sum"),
            prompt_owned_hits=(
                "observation_weight",
                lambda series: float(series[df.loc[series.index, "source_type"] == "owned"].sum()),
            ),
        )
        .reset_index()
    )
    prompt_rollup = (
        prompt_coverage.groupby("topic")
        .agg(
            prompts=("prompt", "nunique"),
            prompt_gaps=("prompt_owned_hits", lambda series: int((series == 0).sum())),
        )
        .reset_index()
    )

    summary = (
        df.groupby("topic")
        .agg(
            citations=("observation_weight", "sum"),
            weighted_mentions=("influence_weight", lambda series: float((series * df.loc[series.index, "observation_weight"]).sum())),
            models=("model", "nunique"),
            owned_citations=(
                "observation_weight",
                lambda series: float(series[df.loc[series.index, "source_type"] == "owned"].sum()),
            ),
            competitor_citations=(
                "observation_weight",
                lambda series: float(series[df.loc[series.index, "source_type"] == "competitor"].sum()),
            ),
            external_citations=(
                "observation_weight",
                lambda series: float(series[df.loc[series.index, "source_type"] == "external"].sum()),
            ),
            last_seen=("date", "max"),
        )
        .reset_index()
    )
    summary = summary.merge(prompt_rollup, on="topic", how="left")
    trends = compute_trends(df, ["topic"])
    summary = summary.merge(trends, on="topic", how="left")
    summary = summary.fillna(
        {
            "prompts": 0,
            "prompt_gaps": 0,
            "current_week_mentions": 0,
            "previous_week_mentions": 0,
            "trend_ratio": 0,
        }
    )

    summary["owned_share"] = summary["owned_citations"] / summary["citations"]
    summary["competitor_share"] = summary["competitor_citations"] / summary["citations"]
    summary["external_share"] = summary["external_citations"] / summary["citations"]
    summary["gap_prompt_ratio"] = np.where(
        summary["prompts"] > 0,
        summary["prompt_gaps"] / summary["prompts"],
        0,
    )

    owned_targets = (
        df[df["source_type"] == "owned"]
        .groupby("topic")
        .agg(
            target_owned_url=("url", lambda series: top_weighted_value(df.loc[series.index], "url")),
            target_owned_domain=("source_domain", lambda series: top_weighted_value(df.loc[series.index], "source_domain")),
        )
        .reset_index()
    )
    top_competitor = (
        df[df["source_type"] == "competitor"]
        .groupby("topic")
        .agg(
            lead_competitor=("competitor", lambda series: top_weighted_value(df.loc[series.index], "competitor")),
            lead_competitor_url=("url", lambda series: top_weighted_value(df.loc[series.index], "url")),
        )
        .reset_index()
    )
    summary = summary.merge(owned_targets, on="topic", how="left")
    summary = summary.merge(top_competitor, on="topic", how="left")
    return summary.sort_values(
        ["gap_prompt_ratio", "citations", "competitor_share"],
        ascending=[False, False, False],
    )


def build_owned_pages(df: pd.DataFrame) -> pd.DataFrame:
    owned_rows = df[df["source_type"] == "owned"].copy()
    if owned_rows.empty:
        return pd.DataFrame()

    pages = (
        owned_rows.groupby(["url", "source_domain"])
        .agg(
            influenced_topics=("topic", "nunique"),
            prompts_covered=("prompt", "nunique"),
            citations=("observation_weight", "sum"),
            models=("model", "nunique"),
            latest_mention=("date", "max"),
            topics=("topic", lambda series: ", ".join(sorted(series.unique())[:4])),
        )
        .reset_index()
        .sort_values(["citations", "prompts_covered"], ascending=[False, False])
    )
    pages["suggested_move"] = np.where(
        pages["influenced_topics"] > 1,
        "Protect this page and strengthen internal links from related topic hubs.",
        "Refresh this page with missing prompt variants and fresher evidence.",
    )
    return pages


def build_competitor_pages(df: pd.DataFrame) -> pd.DataFrame:
    competitor_rows = df[df["source_type"] == "competitor"].copy()
    if competitor_rows.empty:
        return pd.DataFrame()

    pages = (
        competitor_rows.groupby(["competitor", "url", "source_domain"])
        .agg(
            influenced_topics=("topic", "nunique"),
            prompts_covered=("prompt", "nunique"),
            citations=("observation_weight", "sum"),
            models=("model", "nunique"),
            latest_mention=("date", "max"),
            topics=("topic", lambda series: ", ".join(sorted(series.unique())[:4])),
        )
        .reset_index()
        .sort_values(["citations", "prompts_covered"], ascending=[False, False])
    )
    pages["threat_note"] = (
        "Competitor page is shaping multiple prompts and should be benchmarked for structure, entities, and proof."
    )
    return pages


def build_external_domains(df: pd.DataFrame) -> pd.DataFrame:
    external_rows = df[df["source_type"] == "external"].copy()
    if external_rows.empty:
        return pd.DataFrame()

    domains = (
        external_rows.groupby("source_domain")
        .agg(
            influenced_topics=("topic", "nunique"),
            citations=("observation_weight", "sum"),
            prompts_covered=("prompt", "nunique"),
            models=("model", "nunique"),
            latest_mention=("date", "max"),
            topics=("topic", lambda series: ", ".join(sorted(series.unique())[:4])),
        )
        .reset_index()
        .sort_values(["citations", "prompts_covered"], ascending=[False, False])
    )
    domains["dpr_angle"] = np.where(
        domains["influenced_topics"] > 1,
        "Relationship-build: this domain influences multiple topics.",
        "Pitch targeted expert commentary around the lead topic.",
    )
    return domains


def build_content_actions(topic_summary: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "team",
        "topic",
        "opportunity_type",
        "target",
        "priority_score",
        "priority_band",
        "recommendation",
        "why_now",
        "current_week_mentions",
        "previous_week_mentions",
        "lead_competitor",
        "lead_competitor_url",
        "target_owned_url",
    ]
    if topic_summary.empty:
        return pd.DataFrame(columns=columns)

    max_citations = max(topic_summary["citations"].max(), 1)
    actions: list[dict[str, object]] = []

    for row in topic_summary.itertuples(index=False):
        if row.owned_citations == 0 and row.citations >= 2:
            opportunity_type = "Create net-new page"
            recommendation = (
                f"Build a dedicated page or topic hub for '{row.topic}' and target the uncovered prompt cluster."
            )
            target = "Net new asset"
        elif row.owned_share < 0.35 and (row.competitor_share >= 0.25 or row.external_share >= 0.25):
            opportunity_type = "Close ownership gap"
            recommendation = (
                f"Expand or rewrite the owned page for '{row.topic}' so it can replace competitor and publisher citations in the answer mix."
            )
            target = row.target_owned_url or "Existing page review"
        elif row.gap_prompt_ratio >= 0.33:
            opportunity_type = "Expand prompt coverage"
            recommendation = (
                f"Add missing subtopics, FAQs, examples, and proof points so the owned page covers more '{row.topic}' prompts."
            )
            target = row.target_owned_url or "Leading owned page"
        elif row.owned_share >= 0.45 and row.trend_ratio < 0 and row.competitor_share >= 0.2:
            opportunity_type = "Defend existing winner"
            recommendation = (
                f"Refresh the leading owned page for '{row.topic}' before competitor pressure grows."
            )
            target = row.target_owned_url or "Leading owned page"
        else:
            continue

        volume_component = (row.citations / max_citations) * 28
        gap_component = max(row.gap_prompt_ratio, 0.2 if row.owned_share < 0.35 else 0) * 28
        competitor_component = row.competitor_share * 20
        external_component = row.external_share * 10
        trend_component = max(row.trend_ratio, 0) * 14
        priority_score = int(
            min(100, round(volume_component + gap_component + competitor_component + external_component + trend_component))
        )

        why_now = (
            f"{row.prompt_gaps} of {row.prompts} prompts lack owned influence; "
            f"competitors control {row.competitor_share:.0%} and external sources control {row.external_share:.0%}."
        )

        actions.append(
            {
                "team": "SEO / Content",
                "topic": row.topic,
                "opportunity_type": opportunity_type,
                "target": target,
                "priority_score": priority_score,
                "priority_band": score_band(priority_score),
                "recommendation": recommendation,
                "why_now": why_now,
                "current_week_mentions": row.current_week_mentions,
                "previous_week_mentions": row.previous_week_mentions,
                "lead_competitor": row.lead_competitor or "",
                "lead_competitor_url": row.lead_competitor_url or "",
                "target_owned_url": row.target_owned_url or "",
            }
        )

    if not actions:
        return pd.DataFrame(columns=columns)

    return (
        pd.DataFrame(actions, columns=columns)
        .sort_values(["priority_score", "current_week_mentions"], ascending=[False, False])
        .reset_index(drop=True)
    )



def build_dpr_actions(topic_summary: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "team",
        "topic",
        "opportunity_type",
        "target",
        "priority_score",
        "priority_band",
        "recommendation",
        "why_now",
        "current_week_mentions",
        "previous_week_mentions",
        "prompts_covered",
    ]
    external_rows = df[df["source_type"] == "external"].copy()
    if external_rows.empty or topic_summary.empty:
        return pd.DataFrame(columns=columns)

    grouped = (
        external_rows.groupby(["topic", "source_domain"])
        .agg(
            citations=("observation_weight", "sum"),
            prompts_covered=("prompt", "nunique"),
            models=("model", "nunique"),
            latest_mention=("date", "max"),
        )
        .reset_index()
        .sort_values(["topic", "citations", "prompts_covered", "models"], ascending=[True, False, False, False])
    )
    grouped["topic_domain_rank"] = grouped.groupby("topic").cumcount() + 1
    grouped = grouped.merge(
        topic_summary[
            [
                "topic",
                "owned_share",
                "competitor_share",
                "external_share",
                "gap_prompt_ratio",
                "current_week_mentions",
                "previous_week_mentions",
                "trend_ratio",
            ]
        ],
        on="topic",
        how="left",
    )

    max_domain_citations = max(grouped["citations"].max(), 1)
    max_models = max(grouped["models"].max(), 1)

    actions: list[dict[str, object]] = []
    for row in grouped.itertuples(index=False):
        if row.topic_domain_rank > 2 and row.external_share < 0.3:
            continue

        if row.owned_share < 0.25:
            opportunity_type = "Earn third-party proof"
            recommendation = (
                f"Pitch {row.source_domain} with original insight or expert commentary for '{row.topic}'."
            )
        elif row.competitor_share >= 0.3:
            opportunity_type = "Counter competitor narrative"
            recommendation = (
                f"Use DPR to seed independent coverage on {row.source_domain} that challenges competitor framing for '{row.topic}'."
            )
        else:
            opportunity_type = "Reinforce topic authority"
            recommendation = (
                f"Secure a supporting citation or expert quote on {row.source_domain} to strengthen '{row.topic}'."
            )

        volume_component = (row.citations / max_domain_citations) * 26
        gap_component = row.external_share * 18
        ownership_component = (1 - row.owned_share) * 20
        competitor_component = row.competitor_share * 14
        model_component = (row.models / max_models) * 8
        trend_component = max(row.trend_ratio, 0) * 8
        rank_component = 6 if row.topic_domain_rank == 1 else 0
        priority_score = int(
            min(
                100,
                round(
                    volume_component
                    + gap_component
                    + ownership_component
                    + competitor_component
                    + model_component
                    + trend_component
                    + rank_component
                ),
            )
        )

        why_now = (
            f"{row.source_domain} influences {row.citations} answers for this topic; "
            f"owned share is {row.owned_share:.0%} while external influence is {row.external_share:.0%}."
        )

        actions.append(
            {
                "team": "DPR",
                "topic": row.topic,
                "opportunity_type": opportunity_type,
                "target": row.source_domain,
                "priority_score": priority_score,
                "priority_band": score_band(priority_score),
                "recommendation": recommendation,
                "why_now": why_now,
                "current_week_mentions": row.current_week_mentions,
                "previous_week_mentions": row.previous_week_mentions,
                "prompts_covered": row.prompts_covered,
            }
        )

    if not actions:
        return pd.DataFrame(columns=columns)

    return (
        pd.DataFrame(actions, columns=columns)
        .sort_values(["priority_score", "current_week_mentions"], ascending=[False, False])
        .reset_index(drop=True)
    )


@dataclass
class InsightBundle:
    topic_summary: pd.DataFrame
    owned_pages: pd.DataFrame
    competitor_pages: pd.DataFrame
    external_domains: pd.DataFrame
    content_actions: pd.DataFrame
    dpr_actions: pd.DataFrame
    all_actions: pd.DataFrame


def build_insight_bundle(df: pd.DataFrame) -> InsightBundle:
    topic_summary = build_topic_summary(df)
    owned_pages = build_owned_pages(df)
    competitor_pages = build_competitor_pages(df)
    external_domains = build_external_domains(df)
    content_actions = build_content_actions(topic_summary)
    dpr_actions = build_dpr_actions(topic_summary, df)
    action_frames = [frame for frame in [content_actions, dpr_actions] if not frame.empty]
    if action_frames:
        all_actions = (
            pd.concat(action_frames, ignore_index=True)
            .sort_values(["priority_score", "team"], ascending=[False, True])
            .reset_index(drop=True)
        )
    else:
        all_actions = pd.DataFrame()
    return InsightBundle(
        topic_summary=topic_summary,
        owned_pages=owned_pages,
        competitor_pages=competitor_pages,
        external_domains=external_domains,
        content_actions=content_actions,
        dpr_actions=dpr_actions,
        all_actions=all_actions,
    )



def display_intro() -> None:
    st.markdown(
        """
        <div class="hero-panel">
            <div class="action-kicker">PEEC Action Room</div>
            <h1 style="margin-bottom: 0.4rem;">Turn AI answer influence into weekly SEO and DPR actions</h1>
            <div class="small-note">
                Pull PEEC data from the API or upload exports, classify owned and external influence, and generate weekly action lists with rule-based scoring.
            </div>
            <div class="chip-row">
                <span class="chip chip-accent">Not a passive dashboard</span>
                <span class="chip">Topic gaps</span>
                <span class="chip">Owned influence</span>
                <span class="chip">Competitor pressure</span>
                <span class="chip">DPR targeting</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_schema_help() -> None:
    st.markdown(
        """
        <div class="section-panel">
            <h3>PEEC API setup</h3>
            <p class="small-note">
                Add <code>PEEC_API_KEY</code> to Streamlit secrets, then choose one or more PEEC projects in the sidebar.
                The app fetches PEEC URL reports plus prompt, topic, tag, brand, and model metadata and turns them into action-led insights.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_cards(actions: pd.DataFrame) -> None:
    if actions.empty:
        st.info("No actions were triggered for the current filters.")
        return

    top_actions = actions.head(3)
    columns = st.columns(len(top_actions))
    for column, action in zip(columns, top_actions.itertuples(index=False)):
        with column:
            st.markdown(
                f"""
                <div class="action-card">
                    <div class="action-kicker">{action.team}</div>
                    <div class="action-title">{action.topic}</div>
                    <p><strong>{action.opportunity_type}</strong></p>
                    <p>{action.recommendation}</p>
                    <p><span class="action-score">Priority {action.priority_score}</span></p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def dataframe_with_exports(label: str, dataframe: pd.DataFrame, filename: str) -> None:
    st.dataframe(dataframe, use_container_width=True, hide_index=True)
    st.download_button(
        f"Export {label}",
        dataframe.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="PEEC Action Room",
        page_icon="A",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()
    display_intro()

    default_owned_domains = get_secret_or_env("PEEC_OWNED_DOMAINS", "mediaworks.co.uk")
    default_api_key = get_secret_or_env("PEEC_API_KEY")
    default_api_base_url = get_secret_or_env("PEEC_API_BASE_URL", PEEC_API_BASE_URL)
    default_project_id = get_secret_or_env("PEEC_PROJECT_ID")
    today = pd.Timestamp.utcnow().date()

    source_df = None
    source_name = "PEEC API"

    with st.sidebar:
        st.header("Data setup")
        owned_domains = [extract_domain(domain) for domain in default_owned_domains.split(",")]
        owned_domains = [domain for domain in owned_domains if domain]

        if not default_api_key:
            st.error("Add `PEEC_API_KEY` to Streamlit secrets to use this app.")
            display_schema_help()
            st.stop()

        default_project_ids = [
            project_id.strip()
            for project_id in default_project_id.replace("\n", ",").split(",")
            if project_id.strip()
        ]
        project_lookup: dict[str, dict[str, str]] = {}

        try:
            projects = fetch_peec_projects(default_api_key, default_api_base_url)
        except Exception as error:
            st.error(str(error))
            st.stop()

        for project in projects:
            if not isinstance(project, dict):
                continue
            project_id = normalise_text(project.get("id"))
            project_name = normalise_text(project.get("name")) or project_id
            project_status = normalise_text(project.get("status"))
            if project_id:
                label = build_project_label(
                    {"id": project_id, "name": project_name, "status": project_status}
                )
                project_lookup[label] = {
                    "id": project_id,
                    "name": project_name,
                    "status": project_status,
                }

        sorted_project_labels = sorted(project_lookup.keys(), key=lambda value: value.lower())
        default_labels = [
            label
            for label in sorted_project_labels
            for project in [project_lookup[label]]
            if project["id"] in default_project_ids
        ]
        if not default_labels and len(project_lookup) == 1:
            default_labels = sorted_project_labels
        if not default_labels and sorted_project_labels:
            default_labels = sorted_project_labels[:1]

        selected_project_labels = st.multiselect(
            "Projects",
            options=sorted_project_labels,
            default=default_labels,
            help="Choose one or more PEEC projects to combine in the same action room.",
        )
        selected_projects = [project_lookup[label] for label in selected_project_labels]

        lookback_option = st.selectbox(
            "Lookback window",
            options=["Last 7 days", "Last 14 days", "Last 30 days", "Last 60 days", "Last 90 days", "Custom range"],
            index=2,
            help="Start with a shorter window for weekly actions. Use a custom range only when you need a broader audit.",
        )
        if lookback_option == "Custom range":
            custom_dates = st.date_input(
                "Custom fetch range",
                value=(
                    (pd.Timestamp(today) - pd.Timedelta(days=DEFAULT_API_FETCH_DAYS - 1)).date(),
                    today,
                ),
                max_value=today,
                help="Use the narrowest range that answers the question to keep API usage predictable.",
            )
            if not isinstance(custom_dates, tuple) or len(custom_dates) != 2:
                custom_dates = (
                    (pd.Timestamp(today) - pd.Timedelta(days=DEFAULT_API_FETCH_DAYS - 1)).date(),
                    today,
                )
            fetch_dates = custom_dates
        else:
            lookback_days = int(lookback_option.split()[1])
            fetch_start = (pd.Timestamp(today) - pd.Timedelta(days=lookback_days - 1)).date()
            fetch_dates = (fetch_start, today)
        fetch_api = st.button("Fetch latest PEEC data", use_container_width=True)

        st.caption("The app fetches metadata plus a capped URLs report per selected project. PEEC documents a limit of 200 requests per minute per project.")

        if fetch_api:
            if not selected_projects:
                st.error("Select at least one project to fetch.")
            else:
                try:
                    with st.spinner("Loading report data from PEEC API..."):
                        project_frames: list[pd.DataFrame] = []
                        loaded_project_names: list[str] = []
                        loaded_rows = 0
                        for project in selected_projects:
                            project_id = project.get("id")
                            project_name = normalise_text(project.get("name"))
                            project_status = normalise_text(project.get("status"))
                            metadata = fetch_peec_metadata(default_api_key, default_api_base_url, project_id)
                            api_rows = fetch_peec_report_rows(
                                api_key=default_api_key,
                                base_url=default_api_base_url,
                                project_id=project_id,
                                start_date=fetch_dates[0].isoformat(),
                                end_date=fetch_dates[1].isoformat(),
                                page_size=DEFAULT_API_PAGE_SIZE,
                                max_rows=MAX_API_ROWS,
                            )
                            api_df = build_dataframe_from_peec_api(
                                api_rows,
                                metadata,
                                owned_domains,
                                project_id=project_id,
                                project_name=project_name,
                                project_status=project_status,
                            )
                            project_frames.append(api_df)
                            loaded_project_names.append(project_name or str(project_id or "Current project"))
                            loaded_rows += len(api_df)
                        api_df = pd.concat(project_frames, ignore_index=True) if project_frames else pd.DataFrame()
                    st.session_state["peec_api_df"] = api_df
                    st.session_state["peec_api_source_name"] = (
                        f"PEEC API ({len(loaded_project_names)} projects)"
                        if len(loaded_project_names) > 1
                        else f"PEEC API ({loaded_project_names[0]})"
                    )
                    st.session_state["peec_api_window"] = (
                        fetch_dates[0].isoformat(),
                        fetch_dates[1].isoformat(),
                    )
                    st.session_state["peec_api_loaded_rows"] = loaded_rows
                    st.session_state["peec_api_projects"] = loaded_project_names
                except Exception as error:
                    st.error(str(error))

        if "peec_api_df" in st.session_state:
            source_df = st.session_state["peec_api_df"]
            source_name = st.session_state.get("peec_api_source_name", "PEEC API")
            fetch_window = st.session_state.get("peec_api_window", ("", ""))
            loaded_rows = st.session_state.get("peec_api_loaded_rows", 0)
            loaded_project_names = st.session_state.get("peec_api_projects", [])
            st.caption(
                f"Loaded {loaded_rows:,} report rows from {fetch_window[0]} to {fetch_window[1]}."
            )
            if loaded_project_names:
                project_preview = ", ".join(loaded_project_names[:3])
                if len(loaded_project_names) > 3:
                    project_preview += f" +{len(loaded_project_names) - 3} more"
                st.caption(f"Projects loaded: {project_preview}")

    if source_df is None:
        display_schema_help()
        st.stop()

    try:
        peec_df, metadata = normalise_peec_data(source_df, owned_domains)
    except ValueError as error:
        st.error(str(error))
        display_schema_help()
        st.stop()

    if peec_df.empty:
        st.warning("The uploaded data did not contain valid rows after normalisation.")
        st.stop()

    with st.sidebar:
        st.header("Filters")
        min_date = metadata["date_min"].date()
        max_date = metadata["date_max"].date()
        selected_dates = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if not isinstance(selected_dates, tuple) or len(selected_dates) != 2:
            selected_dates = (min_date, max_date)

        project_options = sorted([value for value in peec_df["project"].dropna().unique().tolist() if value])
        selected_projects = []
        if project_options:
            selected_projects = st.multiselect("Project", project_options, default=project_options)

        model_options = sorted(peec_df["model"].dropna().unique().tolist())
        selected_models = st.multiselect("Model", model_options, default=model_options)

        tag_options = sorted({value for tags in peec_df["tag_list"] for value in tags})
        topic_or_tag_options = sorted(set(peec_df["topic"].tolist()) | set(tag_options))
        selected_topics = st.multiselect("Topic / tag", topic_or_tag_options)

        competitor_options = sorted(
            [value for value in peec_df["competitor"].dropna().unique().tolist() if value]
        )
        selected_competitors = st.multiselect("Competitor", competitor_options)

        source_type_options = ["owned", "competitor", "external"]
        selected_source_types = st.multiselect(
            "Source type",
            source_type_options,
            default=source_type_options,
        )

    filtered_df = apply_filters(
        peec_df,
        (pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1])),
        selected_projects,
        selected_models,
        selected_topics,
        selected_competitors,
        selected_source_types,
    )

    if filtered_df.empty:
        st.warning("No rows match the current filters.")
        st.stop()

    insights = build_insight_bundle(filtered_df)
    topic_summary = insights.topic_summary
    owned_pages = insights.owned_pages
    competitor_pages = insights.competitor_pages
    external_domains = insights.external_domains
    content_actions = insights.content_actions
    dpr_actions = insights.dpr_actions
    all_actions = insights.all_actions

    latest_date = filtered_df["date"].max().date()
    earliest_date = filtered_df["date"].min().date()
    action_window = f"{earliest_date.isoformat()} to {latest_date.isoformat()}"

    total_weight = max(filtered_df["observation_weight"].sum(), 1.0)
    project_count = filtered_df["project"].replace("", pd.NA).dropna().nunique()
    top_owned_share = (
        filtered_df.loc[filtered_df["source_type"] == "owned", "observation_weight"].sum() / total_weight
    )
    top_competitor_share = (
        filtered_df.loc[filtered_df["source_type"] == "competitor", "observation_weight"].sum() / total_weight
    )
    top_external_share = (
        filtered_df.loc[filtered_df["source_type"] == "external", "observation_weight"].sum() / total_weight
    )

    st.caption(
        f"Using `{source_name}`. Window: {action_window}. "
        f"Dropped rows during normalisation: {metadata['dropped_rows']}."
    )
    if project_count > 1:
        st.info("Actions are currently aggregated across multiple selected projects. Use the Project filter to isolate a single client or compare a smaller set.")

    metric_columns = st.columns(6)
    metric_columns[0].metric("Topics in play", f"{topic_summary['topic'].nunique()}")
    metric_columns[1].metric("Projects", f"{project_count or 1}")
    metric_columns[2].metric("Owned influence share", f"{top_owned_share:.0%}")
    metric_columns[3].metric("Competitor share", f"{top_competitor_share:.0%}")
    metric_columns[4].metric("External share", f"{top_external_share:.0%}")
    metric_columns[5].metric("Observations", f"{int(round(total_weight)):,}")

    tabs = st.tabs(
        [
            "Weekly Actions",
            "Content Gaps",
            "Influence Map",
            "Exports",
        ]
    )

    with tabs[0]:
        st.subheader("Priority queue")
        render_action_cards(all_actions)
        if not all_actions.empty:
            st.dataframe(
                all_actions[
                    [
                        "team",
                        "topic",
                        "opportunity_type",
                        "target",
                        "priority_score",
                        "priority_band",
                        "recommendation",
                        "why_now",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "priority_score": st.column_config.ProgressColumn(
                        "Priority",
                        min_value=0,
                        max_value=100,
                        format="%d",
                    ),
                },
            )

        team_columns = st.columns(2)
        with team_columns[0]:
            st.markdown("#### SEO / Content actions")
            if content_actions.empty:
                st.info("No content actions triggered.")
            else:
                st.dataframe(
                    content_actions[
                        [
                            "topic",
                            "opportunity_type",
                            "target",
                            "priority_score",
                            "recommendation",
                            "why_now",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "priority_score": st.column_config.ProgressColumn(
                            "Priority",
                            min_value=0,
                            max_value=100,
                            format="%d",
                        )
                    },
                )

        with team_columns[1]:
            st.markdown("#### DPR actions")
            if dpr_actions.empty:
                st.info("No DPR actions triggered.")
            else:
                st.dataframe(
                    dpr_actions[
                        [
                            "topic",
                            "opportunity_type",
                            "target",
                            "priority_score",
                            "recommendation",
                            "why_now",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "priority_score": st.column_config.ProgressColumn(
                            "Priority",
                            min_value=0,
                            max_value=100,
                            format="%d",
                        )
                    },
                )

    with tabs[1]:
        st.subheader("Topic-level content gaps")
        content_gap_view = topic_summary.copy()
        content_gap_view["owned_share"] = to_percentage(content_gap_view["owned_share"])
        content_gap_view["competitor_share"] = to_percentage(content_gap_view["competitor_share"])
        content_gap_view["external_share"] = to_percentage(content_gap_view["external_share"])
        content_gap_view["gap_prompt_ratio"] = to_percentage(content_gap_view["gap_prompt_ratio"])
        st.dataframe(
            content_gap_view[
                [
                    "topic",
                    "citations",
                    "prompts",
                    "prompt_gaps",
                    "gap_prompt_ratio",
                    "owned_share",
                    "competitor_share",
                    "external_share",
                    "target_owned_url",
                    "lead_competitor",
                    "lead_competitor_url",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(
            topic_summary.set_index("topic")[
                ["owned_citations", "competitor_citations", "external_citations"]
            ]
        )

    with tabs[2]:
        st.subheader("Owned pages already influencing answers")
        if owned_pages.empty:
            st.info("No owned pages were identified. Check the owned domain list in the sidebar.")
        else:
            st.dataframe(
                owned_pages,
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("Competitor pages influencing answers")
        if competitor_pages.empty:
            st.info("No competitor pages were detected for the current filters.")
        else:
            st.dataframe(
                competitor_pages,
                use_container_width=True,
                hide_index=True,
            )

        st.subheader("External domains shaping answers for DPR")
        if external_domains.empty:
            st.info("No external domains were detected for the current filters.")
        else:
            st.dataframe(
                external_domains,
                use_container_width=True,
                hide_index=True,
            )

    with tabs[3]:
        st.subheader("Export action lists")
        if all_actions.empty:
            st.info("No actions are available for export.")
        else:
            export_columns = st.columns(3)
            with export_columns[0]:
                dataframe_with_exports(
                    "combined action list",
                    all_actions,
                    "peec_weekly_actions.csv",
                )
            with export_columns[1]:
                if content_actions.empty:
                    st.info("No SEO / Content actions to export.")
                else:
                    dataframe_with_exports(
                        "SEO / Content actions",
                        content_actions,
                        "peec_content_actions.csv",
                    )
            with export_columns[2]:
                if dpr_actions.empty:
                    st.info("No DPR actions to export.")
                else:
                    dataframe_with_exports(
                        "DPR actions",
                        dpr_actions,
                        "peec_dpr_actions.csv",
                    )


if __name__ == "__main__":
    main()
