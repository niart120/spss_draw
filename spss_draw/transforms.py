"""Geometric transforms for SPSS tile coordinates."""

from __future__ import annotations


def transform_tiles(
    size: int,
    tiles: list[tuple[int, int, int]],
    rotate: int = 0,
    flip_h: bool = False,
    flip_v: bool = False,
) -> list[tuple[int, int, int]]:
    """Apply rotation and/or flip to tile coordinates.

    Transformations are applied in order: rotate → flip_h → flip_v.

    Parameters
    ----------
    size:
        Side length of the outer square (unchanged by transforms).
    tiles:
        List of ``(x, y, side)`` tuples with bottom-left origin.
    rotate:
        Clockwise rotation in degrees; must be 0, 90, 180, or 270.
    flip_h:
        Mirror left-to-right (around the vertical centre axis).
    flip_v:
        Mirror top-to-bottom (around the horizontal centre axis).
    """
    result = list(tiles)

    for _ in range((rotate // 90) % 4):
        # 90° clockwise: (x, y, s) → (size-y-s, x, s)
        result = [(size - y - s, x, s) for x, y, s in result]

    if flip_h:
        result = [(size - x - s, y, s) for x, y, s in result]

    if flip_v:
        result = [(x, size - y - s, s) for x, y, s in result]

    return result
