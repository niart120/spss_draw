"""Matplotlib-based 2D drawing of SPSS tilings."""

from __future__ import annotations

import re

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from spss_draw.coloring import four_color

# ── Default visual settings ──────────────────────────────────────────────

PALETTE: list[str] = [
    "#4E79A7",  # blue
    "#F28E2B",  # orange
    "#59A14F",  # green
    "#E15759",  # red
]

EDGE_COLOR: str = "white"
EDGE_WIDTH: float = 1.5
OUTER_EDGE_COLOR: str = "black"
OUTER_EDGE_WIDTH: float = 2.5


# ── Helpers ──────────────────────────────────────────────────────────────

def normalize_color(s: str) -> str:
    """Normalize a color string to a form matplotlib accepts.

    Bare 3- or 6-digit hex strings (e.g. ``4E79A7``) are prefixed with ``#``.
    """
    if re.fullmatch(r"[0-9a-fA-F]{3}|[0-9a-fA-F]{6}", s):
        return f"#{s}"
    return s


# ── Drawing ──────────────────────────────────────────────────────────────

def draw(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    title: str = "Simple Perfect Squared Square",
    palette: list[str] | None = None,
    color_indices: list[int] | None = None,
    edge_color: str = EDGE_COLOR,
    edge_width: float = EDGE_WIDTH,
    outer_edge_color: str = OUTER_EDGE_COLOR,
    outer_edge_width: float = OUTER_EDGE_WIDTH,
    output_path: str | None = None,
    dpi: float = 150,
) -> None:
    """Draw the SPSS using matplotlib."""
    if palette is None:
        palette = PALETTE
    indices = list(color_indices) if color_indices else four_color(tiles)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.set_aspect("equal")
    ax.axis("off")

    for (x, y, s), ci in zip(tiles, indices):
        colour = palette[ci % len(palette)]
        rect = mpatches.FancyBboxPatch(
            (x, y),
            s,
            s,
            boxstyle="square,pad=0",
            linewidth=edge_width,
            edgecolor=edge_color,
            facecolor=colour,
        )
        ax.add_patch(rect)

    border = mpatches.Rectangle(
        (0, 0),
        size,
        size,
        linewidth=outer_edge_width,
        edgecolor=outer_edge_color,
        facecolor="none",
    )
    ax.add_patch(border)

    plt.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
        print(f"Saved to {output_path}")
    else:
        plt.show()
