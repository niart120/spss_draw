"""Adjacency graph construction and four-coloring for SPSS tiles."""

from __future__ import annotations


def build_adjacency(tiles: list[tuple[int, int, int]]) -> dict[int, set[int]]:
    """Return adjacency dict: index → set of adjacent tile indices.

    Two tiles are adjacent when they share a non-zero-length edge segment.
    """
    n = len(tiles)
    adj: dict[int, set[int]] = {i: set() for i in range(n)}
    for i in range(n):
        x1, y1, s1 = tiles[i]
        for j in range(i + 1, n):
            x2, y2, s2 = tiles[j]
            # Shared vertical edge
            if x1 + s1 == x2 or x2 + s2 == x1:
                if min(y1 + s1, y2 + s2) - max(y1, y2) > 0:
                    adj[i].add(j)
                    adj[j].add(i)
            # Shared horizontal edge
            if y1 + s1 == y2 or y2 + s2 == y1:
                if min(x1 + s1, x2 + s2) - max(x1, x2) > 0:
                    adj[i].add(j)
                    adj[j].add(i)
    return adj


def four_color(
    tiles: list[tuple[int, int, int]], n_colors: int = 4
) -> list[int]:
    """Assign a color index (0 … n_colors-1) to each tile.

    Uses backtracking with a degree-descending variable ordering, which
    guarantees a valid coloring for planar graphs of this size.
    """
    n = len(tiles)
    adj = build_adjacency(tiles)

    # Order vertices by descending degree for better pruning
    order = sorted(range(n), key=lambda i: len(adj[i]), reverse=True)

    colors = [-1] * n

    def backtrack(step: int) -> bool:
        if step == n:
            return True
        i = order[step]
        used = {colors[j] for j in adj[i] if colors[j] != -1}
        for c in range(n_colors):
            if c not in used:
                colors[i] = c
                if backtrack(step + 1):
                    return True
                colors[i] = -1
        return False

    if not backtrack(0):
        # Fallback: shouldn't happen for planar graphs with 4 colors
        for i in range(n):
            colors[i] = i % n_colors
    return colors
