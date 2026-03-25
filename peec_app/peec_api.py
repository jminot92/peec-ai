from __future__ import annotations

import time

import requests
import streamlit as st


PEEC_API_BASE_URL = "https://api.peec.ai/customer/v1"
DEFAULT_API_PAGE_SIZE = 1000
MAX_API_ROWS = 20000


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

        for _ in range(4):
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
