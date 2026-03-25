from __future__ import annotations

import streamlit as st



def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
            --peec-bg: #f6f2ea;
            --peec-panel: rgba(255, 255, 255, 0.84);
            --peec-panel-strong: rgba(255, 252, 247, 0.94);
            --peec-card: rgba(255, 255, 255, 0.92);
            --peec-ink: #13262f;
            --peec-muted: #53656d;
            --peec-accent: #d94f30;
            --peec-accent-soft: #f7c9bd;
            --peec-line: rgba(19, 38, 47, 0.1);
            --peec-shadow: rgba(19, 38, 47, 0.08);
            --peec-chart-bg: #07131a;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --peec-bg: #0f171b;
                --peec-panel: rgba(20, 29, 35, 0.84);
                --peec-panel-strong: rgba(24, 34, 40, 0.94);
                --peec-card: rgba(16, 24, 30, 0.92);
                --peec-ink: #eef3f5;
                --peec-muted: #a8b7be;
                --peec-accent-soft: rgba(217, 79, 48, 0.18);
                --peec-line: rgba(238, 243, 245, 0.1);
                --peec-shadow: rgba(0, 0, 0, 0.32);
                --peec-chart-bg: #07131a;
            }
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(217, 79, 48, 0.16), transparent 24%),
                radial-gradient(circle at bottom left, rgba(90, 143, 123, 0.18), transparent 26%),
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
            background: rgba(19, 38, 47, 0.06);
            color: var(--peec-ink);
        }

        .chip-accent {
            background: var(--peec-accent-soft);
            color: var(--peec-accent);
        }

        .placeholder-panel {
            background: var(--peec-card);
            border: 1px solid var(--peec-line);
            border-radius: 20px;
            padding: 1rem 1.1rem;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--peec-panel-strong), var(--peec-panel));
            border-right: 1px solid var(--peec-line);
        }

        [data-testid="stMetric"] {
            background: var(--peec-card);
            border: 1px solid var(--peec-line);
            border-radius: 18px;
            padding: 0.8rem 0.9rem;
        }

        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"] {
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

        .small-note {
            color: var(--peec-muted);
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def render_intro() -> None:
    st.markdown(
        """
        <div class="hero-panel">
            <div style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; color:#7d6d62; font-weight:700;">PEEC Brief Builder</div>
            <h1 style="margin:0.4rem 0 0.5rem 0;">Build client briefs from PEEC data, one module at a time</h1>
            <p style="margin:0; color:var(--peec-muted); max-width:900px;">
                The app stays connected to PEEC, but each insight now lives in its own Python file so briefs can be built and edited independently.
            </p>
            <div class="chip-row">
                <span class="chip chip-accent">Brief 01: Visibility trend</span>
                <span class="chip chip-accent">Brief 02: Visibility snapshot</span>
                <span class="chip chip-accent">Brief 03: Domain types</span>
                <span class="chip chip-accent">Brief 04: URL types</span>
                <span class="chip chip-accent">Brief 05: Slide package</span>
                <span class="chip">PEEC API only</span>
                <span class="chip">Exportable table</span>
                <span class="chip">PNG chart output</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_placeholder_brief(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="placeholder-panel">
            <div style="font-size:0.82rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--peec-muted); font-weight:700;">Next brief</div>
            <h3 style="margin:0.35rem 0 0.4rem 0;">{title}</h3>
            <p style="margin:0; color:var(--peec-muted);">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
