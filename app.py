from __future__ import annotations

import pandas as pd
import streamlit as st

from peec_app.briefs.domain_types import render_domain_types_brief
from peec_app.briefs.visibility import render_visibility_brief
from peec_app.briefs.visibility_snapshot import render_visibility_snapshot_brief
from peec_app.data import apply_dataset_filters, build_dataframe_from_peec_api, normalise_peec_data
from peec_app.peec_api import (
    DEFAULT_API_PAGE_SIZE,
    MAX_API_ROWS,
    PEEC_API_BASE_URL,
    fetch_peec_metadata,
    fetch_peec_projects,
    fetch_peec_report_rows,
)
from peec_app.styles import inject_styles, render_intro, render_placeholder_brief
from peec_app.utils import build_project_label, extract_domain, get_secret_or_env, normalise_text


LOOKBACK_OPTIONS = [
    "Last 14 days",
    "Last 30 days",
    "Last 60 days",
    "Last 90 days",
    "Last 180 days",
    "Last 365 days",
    "Custom range",
]



def resolve_fetch_dates(option: str, today: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    if option == "Custom range":
        return today - pd.Timedelta(days=89), today
    lookback_days = int(option.split()[1])
    return today - pd.Timedelta(days=lookback_days - 1), today



def main() -> None:
    st.set_page_config(
        page_title="PEEC Brief Builder",
        page_icon="A",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()
    render_intro()

    api_key = get_secret_or_env("PEEC_API_KEY")
    api_base_url = get_secret_or_env("PEEC_API_BASE_URL", PEEC_API_BASE_URL)
    configured_owned_domains = [
        extract_domain(domain)
        for domain in get_secret_or_env("PEEC_OWNED_DOMAINS").replace("\n", ",").split(",")
        if extract_domain(domain)
    ]
    today = pd.Timestamp.utcnow().normalize()

    if not api_key:
        st.error("Add `PEEC_API_KEY` to Streamlit secrets before using the app.")
        st.stop()

    try:
        projects = fetch_peec_projects(api_key, api_base_url)
    except Exception as error:
        st.error(str(error))
        st.stop()

    project_lookup: dict[str, dict[str, str]] = {}
    for project in projects:
        if not isinstance(project, dict):
            continue
        project_id = normalise_text(project.get("id"))
        project_name = normalise_text(project.get("name")) or project_id
        project_status = normalise_text(project.get("status"))
        if not project_id:
            continue
        label = build_project_label({"id": project_id, "name": project_name, "status": project_status})
        project_lookup[label] = {
            "id": project_id,
            "name": project_name,
            "status": project_status,
        }

    sorted_project_labels = sorted(project_lookup.keys(), key=lambda value: value.lower())
    if not sorted_project_labels:
        st.error("No PEEC projects were returned for this API key.")
        st.stop()

    with st.sidebar:
        st.header("PEEC connection")
        selected_project_label = st.selectbox("Project", options=sorted_project_labels, index=0)
        selected_project = project_lookup[selected_project_label]

        lookback_option = st.selectbox(
            "Fetch range",
            options=LOOKBACK_OPTIONS,
            index=3,
            help="The app only calls PEEC when you click fetch. Start with a shorter range, then widen it if you need a bigger trend view.",
        )
        default_start, default_end = resolve_fetch_dates(lookback_option, today)
        if lookback_option == "Custom range":
            custom_dates = st.date_input(
                "Custom range",
                value=(default_start.date(), default_end.date()),
                max_value=today.date(),
            )
            if not isinstance(custom_dates, tuple) or len(custom_dates) != 2:
                custom_dates = (default_start.date(), default_end.date())
            fetch_start = pd.Timestamp(custom_dates[0]).normalize()
            fetch_end = pd.Timestamp(custom_dates[1]).normalize()
        else:
            fetch_start, fetch_end = default_start, default_end

        fetch_clicked = st.button("Fetch latest PEEC data", use_container_width=True)
        st.caption("The fetch is capped and only runs on demand. PEEC documents 200 requests per minute per project.")

        if fetch_clicked:
            try:
                with st.spinner("Loading PEEC metadata and URLs report..."):
                    metadata = fetch_peec_metadata(api_key, api_base_url, selected_project["id"])
                    api_rows = fetch_peec_report_rows(
                        api_key=api_key,
                        base_url=api_base_url,
                        project_id=selected_project["id"],
                        start_date=fetch_start.date().isoformat(),
                        end_date=fetch_end.date().isoformat(),
                        page_size=DEFAULT_API_PAGE_SIZE,
                        max_rows=MAX_API_ROWS,
                    )
                    source_df = build_dataframe_from_peec_api(
                        api_rows,
                        metadata,
                        configured_owned_domains,
                        project_id=selected_project["id"],
                        project_name=selected_project["name"],
                        project_status=selected_project["status"],
                    )
                    peec_df, dataset_meta = normalise_peec_data(source_df, configured_owned_domains)
                st.session_state["peec_df"] = peec_df
                st.session_state["dataset_meta"] = dataset_meta
                st.session_state["loaded_project"] = selected_project
                st.session_state["loaded_window"] = (
                    fetch_start.date().isoformat(),
                    fetch_end.date().isoformat(),
                )
            except Exception as error:
                st.error(str(error))

    if "peec_df" not in st.session_state:
        st.info("Choose a project and fetch a PEEC window to build the first brief.")
        st.stop()

    peec_df = st.session_state["peec_df"]
    dataset_meta = st.session_state.get("dataset_meta", {})
    loaded_project = st.session_state.get("loaded_project", {"name": "Owned brand"})
    loaded_window = st.session_state.get("loaded_window", ("", ""))

    if peec_df.empty:
        st.warning("The selected PEEC range returned no usable rows.")
        st.stop()

    with st.sidebar:
        st.header("Analysis filters")
        model_options = sorted(peec_df["model"].dropna().unique().tolist())
        topic_options = sorted(peec_df["topic"].dropna().unique().tolist())
        tag_options = sorted({tag for tags in peec_df["tag_list"] for tag in tags})

        selected_models = st.multiselect(
            "Models",
            options=model_options,
            default=[],
            help="Leave blank to include every model in the fetched window.",
        )
        selected_topics = st.multiselect(
            "Topics",
            options=topic_options,
            default=[],
            help="Leave blank to include every topic.",
        )
        selected_tags = st.multiselect(
            "Tags",
            options=tag_options,
            default=[],
            help="Leave blank to include every tag.",
        )

    filtered_df = apply_dataset_filters(
        peec_df,
        models=selected_models,
        topics=selected_topics,
        tags=selected_tags,
    )

    info_1, info_2, info_3, info_4 = st.columns(4)
    info_1.metric("Project", loaded_project.get("name", ""))
    info_2.metric("Rows", f"{len(filtered_df):,}")
    info_3.metric("Prompts", f"{filtered_df['prompt'].nunique():,}")
    info_4.metric("Window", f"{loaded_window[0]} to {loaded_window[1]}")
    st.caption(
        f"Loaded {dataset_meta.get('row_count', 0):,} usable PEEC rows. Dropped during normalisation: {dataset_meta.get('dropped_rows', 0):,}."
    )

    if filtered_df.empty:
        st.warning("The current model/topic/tag filters removed every row.")
        st.stop()

    visibility_tab, snapshot_tab, domain_types_tab, brief_four_tab = st.tabs(
        [
            "Visibility trend",
            "Visibility snapshot",
            "Domain types",
            "Brief 04",
        ]
    )

    with visibility_tab:
        render_visibility_brief(filtered_df, loaded_project.get("name", "Owned brand"))

    with snapshot_tab:
        render_visibility_snapshot_brief(filtered_df, loaded_project.get("name", "Owned brand"))

    with domain_types_tab:
        render_domain_types_brief(filtered_df)

    with brief_four_tab:
        render_placeholder_brief(
            "Content action brief",
            "Use this slot for the next brief after we decide the exact questions it should answer.",
        )


if __name__ == "__main__":
    main()
