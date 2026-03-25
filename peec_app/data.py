from __future__ import annotations

import numpy as np
import pandas as pd

from peec_app.utils import (
    clean_column_name,
    coerce_positive_number,
    domain_matches,
    extract_domain,
    format_date,
    normalise_name_key,
    normalise_text,
    split_tags,
)


REQUIRED_COLUMNS = [
    "topic",
    "prompt",
    "url",
    "source_domain",
    "model",
    "date",
    "competitor",
]
ALLOWED_SOURCE_TYPES = {"owned", "competitor", "external"}



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



def infer_owned_domains(
    brands: list[dict[str, object]],
    owned_domains: list[str],
    project_name: str,
) -> list[str]:
    effective_owned_domains = {
        extract_domain(domain)
        for domain in owned_domains
        if extract_domain(domain)
    }
    project_key = normalise_name_key(project_name)

    for brand in brands:
        if not isinstance(brand, dict):
            continue
        brand_name = normalise_text(brand.get("name"))
        brand_key = normalise_name_key(brand_name)
        raw_domains = brand.get("domains", [])
        if not isinstance(raw_domains, list):
            continue
        brand_domains = {
            extract_domain(raw_domain)
            for raw_domain in raw_domains
            if extract_domain(raw_domain)
        }
        if not brand_domains:
            continue

        is_explicitly_owned = any(
            domain_matches(domain, effective_owned_domains)
            for domain in brand_domains
        )
        name_matches_project = bool(project_key) and bool(brand_key) and (
            brand_key == project_key
            or brand_key.startswith(f"{project_key} ")
            or brand_key.endswith(f" {project_key}")
            or project_key.startswith(f"{brand_key} ")
            or project_key.endswith(f" {brand_key}")
        )
        if is_explicitly_owned or name_matches_project:
            effective_owned_domains.update(brand_domains)

    return sorted(effective_owned_domains)



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
    effective_owned_domains = infer_owned_domains(
        metadata.get("brands", []),
        owned_domains,
        project_name,
    )
    brand_domains = build_brand_domain_lookup(
        metadata.get("brands", []),
        effective_owned_domains,
    )

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
        tag_values: list[str] = []
        for tag in prompt_meta.get("tags", []) if isinstance(prompt_meta, dict) else []:
            if not isinstance(tag, dict):
                continue
            tag_name = tags_by_id.get(normalise_text(tag.get("id")), normalise_text(tag.get("name")))
            if tag_name:
                tag_values.append(tag_name)

        url = normalise_text(item.get("url"))
        source_domain = extract_domain(url)
        competitor = lookup_competitor(source_domain, brand_domains)
        if domain_matches(source_domain, effective_owned_domains):
            source_type = "owned"
            competitor = ""
        elif competitor:
            source_type = "competitor"
        else:
            source_type = "external"

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
                "source_type": source_type,
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
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing_columns)))

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
        "row_count": len(working),
        "dropped_rows": dropped_rows,
        "min_date": working["date"].min(),
        "max_date": working["date"].max(),
        "project_names": sorted([project for project in working["project"].unique().tolist() if project]),
    }
    return working, metadata



def apply_dataset_filters(
    df: pd.DataFrame,
    *,
    models: list[str],
    topics: list[str],
    tags: list[str],
) -> pd.DataFrame:
    filtered = df.copy()
    if models:
        filtered = filtered[filtered["model"].isin(models)]
    if topics:
        filtered = filtered[filtered["topic"].isin(topics)]
    if tags:
        filtered = filtered[
            filtered["tag_list"].apply(lambda tag_values: any(tag in tag_values for tag in tags))
        ]
    return filtered.copy()
