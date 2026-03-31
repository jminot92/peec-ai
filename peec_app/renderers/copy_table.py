from __future__ import annotations

import html
import json

import pandas as pd
import streamlit.components.v1 as components


def render_copy_table_button(
    dataframe: pd.DataFrame,
    *,
    button_label: str,
    key: str,
) -> None:
    table_text = dataframe.to_csv(index=False, sep="\t")
    escaped_label = html.escape(button_label)
    escaped_key = html.escape(key)
    text_payload = json.dumps(table_text)
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
      const button = document.getElementById("copy-btn-{escaped_key}");
      const status = document.getElementById("copy-status-{escaped_key}");

      async function copyText() {{
        try {{
          await navigator.clipboard.writeText(textToCopy);
          status.textContent = "Copied";
        }} catch (error) {{
          const fallback = document.createElement("textarea");
          fallback.value = textToCopy;
          document.body.appendChild(fallback);
          fallback.select();
          document.execCommand("copy");
          document.body.removeChild(fallback);
          status.textContent = "Copied";
        }}
        setTimeout(() => {{
          status.textContent = "";
        }}, 2000);
      }}

      button.addEventListener("click", copyText);
    </script>
    """
    components.html(html_block, height=50)
