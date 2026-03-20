"""Matplotlib-based 2D drawing of SPSS tilings."""

from __future__ import annotations

import re

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from spss_draw.coloring import build_adjacency, four_color

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


# ── Default dual-graph visual settings ───────────────────────────────────

NODE_COLOR: str = "#E15759"
NODE_EDGE_COLOR: str = "white"
NODE_EDGE_WIDTH: float = 1.5
NODE_SIZE: float = 6.0
NODE_AMPLIFY: float = 0.0
GRAPH_EDGE_COLOR: str = "#333333"
GRAPH_EDGE_WIDTH: float = 1.5
TILE_ALPHA: float = 0.25


def draw_dual(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    title: str = "SPSS Dual Graph",
    palette: list[str] | None = None,
    color_indices: list[int] | None = None,
    edge_color: str = EDGE_COLOR,
    edge_width: float = EDGE_WIDTH,
    outer_edge_color: str = OUTER_EDGE_COLOR,
    outer_edge_width: float = OUTER_EDGE_WIDTH,
    node_color: str = NODE_COLOR,
    node_edge_color: str = NODE_EDGE_COLOR,
    node_edge_width: float = NODE_EDGE_WIDTH,
    node_size: float = NODE_SIZE,
    node_amplify: float = NODE_AMPLIFY,
    graph_edge_color: str = GRAPH_EDGE_COLOR,
    graph_edge_width: float = GRAPH_EDGE_WIDTH,
    show_background: bool = True,
    tile_alpha: float = TILE_ALPHA,
    output_path: str | None = None,
    dpi: float = 150,
) -> None:
    """Draw the dual graph of the SPSS tiling.

    Each tile becomes a node placed at its center; adjacent tiles are
    connected by edges.

    *node_size* sets the base marker radius (in points).  When
    *node_amplify* > 0 the radius is additionally scaled by each tile's
    side length: ``radius = node_size + side / max_side * node_amplify``.
    """
    if palette is None:
        palette = PALETTE
    indices = list(color_indices) if color_indices else four_color(tiles)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── background tiling (faded) ────────────────────────────────────
    if show_background:
        for (x, y, s), ci in zip(tiles, indices):
            colour = palette[ci % len(palette)]
            rect = mpatches.FancyBboxPatch(
                (x, y), s, s,
                boxstyle="square,pad=0",
                linewidth=edge_width,
                edgecolor=edge_color,
                facecolor=colour,
                alpha=tile_alpha,
            )
            ax.add_patch(rect)

    border = mpatches.Rectangle(
        (0, 0), size, size,
        linewidth=outer_edge_width,
        edgecolor=outer_edge_color,
        facecolor="none",
    )
    ax.add_patch(border)

    # ── dual graph ───────────────────────────────────────────────────
    centers = [(x + s / 2, y + s / 2) for x, y, s in tiles]
    adj = build_adjacency(tiles)

    # Draw edges
    drawn: set[tuple[int, int]] = set()
    for i, neighbours in adj.items():
        for j in neighbours:
            key = (min(i, j), max(i, j))
            if key not in drawn:
                drawn.add(key)
                cx1, cy1 = centers[i]
                cx2, cy2 = centers[j]
                ax.plot(
                    [cx1, cx2], [cy1, cy2],
                    color=graph_edge_color,
                    linewidth=graph_edge_width,
                    zorder=2,
                )

    # Draw nodes
    sides = [s for _, _, s in tiles]
    max_side = max(sides)
    for (cx, cy), s in zip(centers, sides):
        ms = node_size + (s / max_side) * node_amplify
        ax.plot(
            cx, cy, "o",
            markersize=ms,
            color=node_color,
            markeredgecolor=node_edge_color,
            markeredgewidth=node_edge_width,
            zorder=3,
        )

    plt.tight_layout()
    if output_path:
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
        print(f"Saved to {output_path}")
    else:
        plt.show()
