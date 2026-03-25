from __future__ import annotations

from io import BytesIO
from textwrap import shorten

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd


BACKGROUND = "#171B34"
HEADER = "#E22A8A"
GRID = "#3A4067"
TEXT = "#FFFFFF"
MUTED = "#C7CAE3"



def _prepare_text(value: object, max_chars: int) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.replace("\n", " ").strip()
    if not text:
        return ""
    return shorten(text, width=max_chars, placeholder="...")



def render_table_png(
    dataframe: pd.DataFrame,
    *,
    title: str = "",
    subtitle: str = "",
    max_cell_chars: int = 28,
) -> bytes:
    if dataframe.empty:
        return b""

    display_df = dataframe.copy()
    for column in display_df.columns:
        display_df[column] = display_df[column].map(lambda value: _prepare_text(value, max_cell_chars))

    headers = [str(column) for column in display_df.columns]
    rows = display_df.astype(str).values.tolist()

    width_units = []
    for index, header in enumerate(headers):
        cell_lengths = [len(header)] + [len(row[index]) for row in rows]
        width_units.append(max(cell_lengths) + 4)
    total_units = float(sum(width_units))
    column_widths = [unit / total_units for unit in width_units]

    row_count = len(rows)
    row_height = 0.42
    header_height = 0.48
    title_height = 0.56 if title else 0.0
    subtitle_height = 0.34 if subtitle else 0.0
    total_height = title_height + subtitle_height + header_height + (row_count * row_height) + 0.28
    figure_width = max(8.5, min(16.0, total_units * 0.14))

    figure, axis = plt.subplots(figsize=(figure_width, total_height), dpi=220)
    figure.patch.set_facecolor(BACKGROUND)
    axis.set_facecolor(BACKGROUND)
    axis.set_xlim(0, 1)
    axis.set_ylim(0, total_height)
    axis.axis("off")

    y_cursor = total_height - 0.18
    if title:
        axis.text(0.02, y_cursor, title, color=TEXT, fontsize=16, fontweight="bold", va="top", ha="left")
        y_cursor -= title_height
    if subtitle:
        axis.text(0.02, y_cursor + 0.04, subtitle, color=MUTED, fontsize=10, va="top", ha="left")
        y_cursor -= subtitle_height

    header_y = y_cursor - header_height
    x_cursor = 0.02
    usable_width = 0.96
    for header, width in zip(headers, column_widths):
        cell_width = usable_width * width
        axis.add_patch(Rectangle((x_cursor, header_y), cell_width, header_height, facecolor=HEADER, edgecolor=GRID, linewidth=0.8))
        axis.text(
            x_cursor + 0.012,
            header_y + (header_height / 2),
            header,
            color=TEXT,
            fontsize=10,
            fontweight="bold",
            va="center",
            ha="left",
        )
        x_cursor += cell_width

    current_y = header_y
    for row in rows:
        current_y -= row_height
        x_cursor = 0.02
        for value, width in zip(row, column_widths):
            cell_width = usable_width * width
            axis.add_patch(Rectangle((x_cursor, current_y), cell_width, row_height, facecolor=BACKGROUND, edgecolor=GRID, linewidth=0.8))
            axis.text(
                x_cursor + 0.012,
                current_y + (row_height / 2),
                value,
                color=TEXT,
                fontsize=9,
                va="center",
                ha="left",
            )
            x_cursor += cell_width

    figure.tight_layout(pad=0)
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=220, facecolor=BACKGROUND, bbox_inches="tight", pad_inches=0.08)
    plt.close(figure)
    return buffer.getvalue()
