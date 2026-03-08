"""Bouwkamp code decoder and tiling validator."""

from __future__ import annotations

import numpy as np


def bouwkamp_to_tiles(
    size: int,
    code: list[list[int]],
) -> list[tuple[int, int, int]]:
    """Convert a Bouwkamp code to (x, y, side) tile coordinates.

    Uses a "skyline" algorithm with bottom-left origin (y increases upward).

    Parameters
    ----------
    size:
        Side length of the outer square.
    code:
        Bouwkamp code as a list of groups; each group is a list of square sizes
        listed left-to-right.

    Returns
    -------
    List of ``(x, y, side)`` tuples – bottom-left corner and side length.
    """
    tiles: list[tuple[int, int, int]] = []

    # Segments stored as list of [y, x_left, x_right].
    # Start: the whole bottom edge.
    segments: list[list[int]] = [[0, 0, size]]

    def merge_segments(segs: list[list[int]]) -> list[list[int]]:
        """Merge horizontally adjacent segments sharing the same y."""
        if not segs:
            return segs
        segs.sort()
        merged: list[list[int]] = [segs[0][:]]
        for y, xl, xr in segs[1:]:
            if y == merged[-1][0] and xl == merged[-1][2]:
                merged[-1][2] = xr  # extend right
            else:
                merged.append([y, xl, xr])
        return merged

    for group in code:
        group_width = sum(group)

        # Find the minimum y and collect all segments at that level.
        min_y = min(s[0] for s in segments)
        at_min: list[list[int]] = [s for s in segments if s[0] == min_y]
        rest:   list[list[int]] = [s for s in segments if s[0] != min_y]

        # Sort by x_left and pick a contiguous run that matches group_width.
        at_min.sort(key=lambda s: s[1])
        chosen: list[list[int]] = []
        acc = 0
        x_start = at_min[0][1]
        for seg in at_min:
            if acc == 0:
                x_start = seg[1]
            acc += seg[2] - seg[1]
            chosen.append(seg)
            if acc == group_width:
                break
        if acc != group_width:
            raise ValueError(
                f"Bouwkamp group {group} (sum={group_width}) does not fit "
                f"any contiguous run at y={min_y}; available widths: "
                f"{[s[2]-s[1] for s in at_min]}"
            )

        # The unused segments at min_y stay in the pool.
        unused_at_min = [s for s in at_min if s not in chosen]

        # Place tiles left-to-right within the chosen x-range.
        x = x_start
        new_tops: list[list[int]] = []
        for side in group:
            tiles.append((x, min_y, side))
            new_tops.append([min_y + side, x, x + side])
            x += side

        segments = merge_segments(rest + unused_at_min + new_tops)

    return tiles


def validate(size: int, tiles: list[tuple[int, int, int]]) -> None:
    """Raise ``ValueError`` if the tiling is invalid."""
    sides = [s for _, _, s in tiles]

    # Distinct sizes
    if len(sides) != len(set(sides)):
        raise ValueError(f"Duplicate side lengths: {sorted(sides)}")

    # All within bounds
    for x, y, s in tiles:
        if x < 0 or y < 0 or x + s > size or y + s > size:
            raise ValueError(
                f"Tile ({x},{y},{s}) exceeds the {size}×{size} boundary"
            )

    # Area sum
    total_area = sum(s * s for _, _, s in tiles)
    if total_area != size * size:
        raise ValueError(
            f"Area mismatch: sum of tile areas = {total_area}, "
            f"expected {size}×{size} = {size*size}"
        )

    # No overlaps – check on a pixel grid (feasible for size=112)
    grid = np.zeros((size, size), dtype=np.int8)
    for x, y, s in tiles:
        grid[y : y + s, x : x + s] += 1
    if grid.max() > 1:
        raise ValueError("Overlapping tiles detected")
    if grid.min() < 1:
        raise ValueError("Gaps in tiling detected")
