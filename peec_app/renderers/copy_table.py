from __future__ import annotations

import html
import json

import pandas as pd
import streamlit.components.v1 as components


def _dataframe_to_tsv(dataframe: pd.DataFrame) -> str:
    return dataframe.to_csv(index=False, sep="\t")


def _dataframe_to_html_table(dataframe: pd.DataFrame) -> str:
    header_cells = "".join(
        f"""
        <th style="
          border:1px solid #ffffff;
          padding:8px 10px;
          text-align:left;
          font-family:Arial, sans-serif;
          font-size:11pt;
          font-weight:700;
          color:#ffffff;
          background:#e22a8a;
          white-space:nowrap;
        ">{html.escape(str(column))}</th>
        """
        for column in dataframe.columns
    )
    body_rows: list[str] = []
    for _, row in dataframe.fillna("").iterrows():
        cells = "".join(
            f"""
            <td style="
              border:1px solid #ffffff;
              padding:8px 10px;
              text-align:left;
              font-family:Arial, sans-serif;
              font-size:10.5pt;
              color:#ffffff;
              background:#1a1f3d;
              vertical-align:top;
            ">{html.escape(str(value))}</td>
            """
            for value in row.tolist()
        )
        body_rows.append(f"<tr>{cells}</tr>")
    body_html = "".join(body_rows)
    return f"""
    <table style="
      border-collapse:collapse;
      border-spacing:0;
      background:#1a1f3d;
      color:#ffffff;
    ">
      <thead>
        <tr>{header_cells}</tr>
      </thead>
      <tbody>
        {body_html}
      </tbody>
    </table>
    """


def render_copy_table_button(
    dataframe: pd.DataFrame,
    *,
    button_label: str,
    key: str,
) -> None:
    table_text = _dataframe_to_tsv(dataframe)
    table_html = _dataframe_to_html_table(dataframe)
    escaped_label = html.escape(button_label)
    escaped_key = html.escape(key)
    text_payload = json.dumps(table_text)
    html_payload = json.dumps(table_html)
    html_block = f"""
    <div style="display:flex;align-items:center;gap:10px;">
      <button
        id="copy-btn-{escaped_key}"
        style="
          background:#11212e;
          color:#ffffff;
          border:1px solid rgba(255,255,255,0.18);
          border-radius:10px;
          padding:0.55rem 0.9rem;
          font-size:0.95rem;
          cursor:pointer;
          width:100%;
        "
      >
        {escaped_label}
      </button>
      <span id="copy-status-{escaped_key}" style="color:#d4dae3;font-size:0.85rem;"></span>
    </div>
    <script>
      const textToCopy = {text_payload};
      const htmlToCopy = {html_payload};
      const button = document.getElementById("copy-btn-{escaped_key}");
      const status = document.getElementById("copy-status-{escaped_key}");

      async function copyText() {{
        try {{
          if (window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {{
            const clipboardItem = new ClipboardItem({{
              "text/html": new Blob([htmlToCopy], {{ type: "text/html" }}),
              "text/plain": new Blob([textToCopy], {{ type: "text/plain" }})
            }});
            await navigator.clipboard.write([clipboardItem]);
            status.textContent = "HTML table copied";
          }} else if (navigator.clipboard && navigator.clipboard.writeText) {{
            await navigator.clipboard.writeText(textToCopy);
            status.textContent = "Plain text copied";
          }} else {{
            throw new Error("Clipboard API unavailable");
          }}
        }} catch (error) {{
          const fallback = document.createElement("textarea");
          fallback.value = textToCopy;
          document.body.appendChild(fallback);
          fallback.select();
          document.execCommand("copy");
          document.body.removeChild(fallback);
          status.textContent = "Plain text copied";
        }}
        setTimeout(() => {{
          status.textContent = "";
        }}, 2200);
      }}

      button.addEventListener("click", copyText);
    </script>
    """
    components.html(html_block, height=54)
