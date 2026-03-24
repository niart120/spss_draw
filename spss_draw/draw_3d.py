"""build123d-based 3D skeleton model generation for SPSS tilings.

The skeleton is built additively: each tile contributes a solid block that
extends ``wall_thickness / 2`` beyond its boundary on every side, then the
interior of each tile is subtracted.  Boolean union naturally gives shared
walls the height of the *taller* neighbour.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from spss_draw.coloring import build_adjacency

if TYPE_CHECKING:
    from build123d import Compound, Part, Shape


def build_skeleton(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    wall_thickness: float = 1.0,
    height: float = 1.0,
    height_multiplier: float = 0.0,
    base_thickness: float = 0.0,
) -> Part:
    """Build a skeleton frame 3D model from SPSS tiles.

    Parameters
    ----------
    size:
        Side length of the outer SPSS square (in tile units).
    tiles:
        List of ``(x, y, side)`` tuples.
    scale:
        Millimetres per tile unit.  ``0.5`` → 112 units = 56 mm.
    wall_thickness:
        Thickness of each wall (the edges between tiles) in mm.
    height:
        Base extrusion height of the skeleton in mm.  When
        ``height_multiplier > 0`` this becomes the *minimum* height (for
        the smallest tile); taller tiles are scaled up from there.
    height_multiplier:
        When > 0, each tile's wall height is
        ``height + tile_side * scale * height_multiplier``.  Setting this
        to a large value (e.g. 1.0) creates dramatic topography; small
        values (e.g. 0.05) give a subtle relief.  ``0`` disables variable
        height and every wall has the same ``height``.
    base_thickness:
        If > 0, keep a thin solid base of this thickness (mm) at the bottom
        so that all walls remain connected.  ``0`` produces a pure skeleton.

    Returns
    -------
    A build123d ``Part`` ready for export.
    """
    from build123d import Align, Box, BuildPart, Locations, Mode

    S = size * scale
    half_S = S / 2

    def _tile_h(s: int) -> float:
        if height_multiplier > 0:
            return height + s * scale * height_multiplier
        return height

    # Z-align: bottom face sits at the Locations z-coordinate.
    Z_ALIGN = (Align.CENTER, Align.CENTER, Align.MIN)

    with BuildPart() as part:
        # ── Phase 1: Add per-tile solid blocks ───────────────────────
        # Each block is (s*scale + wt) wide, extending wt/2 beyond the
        # tile boundary on every side.  For internal edges both tiles
        # contribute wt/2 each → total wall = wt.  For outer edges the
        # block extends wt/2 outside the nominal square.
        # Where two tiles share an edge the taller block governs the
        # shared-wall height via boolean union.
        for x, y, s in tiles:
            th = _tile_h(s)
            full = s * scale + wall_thickness
            cx = (x + s / 2) * scale - half_S
            cy = (y + s / 2) * scale - half_S
            with Locations([(cx, cy, 0)]):
                Box(full, full, th, align=Z_ALIGN)

        # ── Phase 2: Hollow tile interiors ───────────────────────────
        for x, y, s in tiles:
            th = _tile_h(s)
            cut = s * scale - wall_thickness
            if cut <= 0:
                continue  # tile too small to hollow
            cx = (x + s / 2) * scale - half_S
            cy = (y + s / 2) * scale - half_S

            if 0 < base_thickness < th:
                with Locations([(cx, cy, base_thickness)]):
                    Box(cut, cut, th - base_thickness + 0.01,
                        align=Z_ALIGN, mode=Mode.SUBTRACT)
            else:
                with Locations([(cx, cy, -0.01)]):
                    Box(cut, cut, th + 0.02,
                        align=Z_ALIGN, mode=Mode.SUBTRACT)

    return part.part


# ── Wall-segment enumeration ─────────────────────────────────────────────

def _compute_wall_segments(
    size: int,
    tiles: list[tuple[int, int, int]],
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Return all wall segments as ``((x1, y1), (x2, y2))`` in tile units.

    Includes both internal edges (shared between adjacent tiles) and
    outer-boundary edges.
    """
    segments: list[tuple[tuple[int, int], tuple[int, int]]] = []
    n = len(tiles)

    # Internal edges
    for i in range(n):
        xi, yi, si = tiles[i]
        for j in range(i + 1, n):
            xj, yj, sj = tiles[j]
            # Shared vertical edge
            if xi + si == xj:
                y_lo = max(yi, yj)
                y_hi = min(yi + si, yj + sj)
                if y_hi > y_lo:
                    segments.append(((xi + si, y_lo), (xi + si, y_hi)))
            elif xj + sj == xi:
                y_lo = max(yi, yj)
                y_hi = min(yi + si, yj + sj)
                if y_hi > y_lo:
                    segments.append(((xi, y_lo), (xi, y_hi)))
            # Shared horizontal edge
            if yi + si == yj:
                x_lo = max(xi, xj)
                x_hi = min(xi + si, xj + sj)
                if x_hi > x_lo:
                    segments.append(((x_lo, yi + si), (x_hi, yi + si)))
            elif yj + sj == yi:
                x_lo = max(xi, xj)
                x_hi = min(xi + si, xj + sj)
                if x_hi > x_lo:
                    segments.append(((x_lo, yi), (x_hi, yi)))

    # Outer boundary edges
    for x, y, s in tiles:
        if x == 0:
            segments.append(((0, y), (0, y + s)))
        if x + s == size:
            segments.append(((size, y), (size, y + s)))
        if y == 0:
            segments.append(((x, 0), (x + s, 0)))
        if y + s == size:
            segments.append(((x, y + s), (x + s, y + s)))

    return segments


def build_skeleton_round(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    wall_radius: float = 0.5,
) -> "Compound":
    """Build a rounded skeleton frame using cylinders and spheres.

    Each wall segment becomes a horizontal cylinder, and every junction
    point (tile corner) gets a sphere.  The radius is shared between
    wall thickness and height, giving a naturally rounded cross-section.

    Individual shapes are collected into a :class:`Compound` rather than
    fused via ``BuildPart`` to avoid OCCT boolean-union instability with
    many disjoint primitives.

    Parameters
    ----------
    scale:
        Millimetres per tile unit.
    wall_radius:
        Radius of wall cylinders and junction spheres in mm.
        The resulting wall thickness (diameter) and height are both
        ``2 * wall_radius``.
    """
    from build123d import (
        Compound,
        Cylinder,
        Location,
        Pos,
        Sphere,
        Vector,
    )

    S = size * scale
    half_S = S / 2
    r = wall_radius

    segments = _compute_wall_segments(size, tiles)

    # Unique junction points (tile corners)
    corners: set[tuple[int, int]] = set()
    for x, y, s in tiles:
        corners.update(((x, y), (x + s, y), (x, y + s), (x + s, y + s)))

    z_axis = Vector(0, 0, 1)
    shapes = []

    # ── Junction spheres ─────────────────────────────────────────────
    for cx_t, cy_t in corners:
        cx = cx_t * scale - half_S
        cy = cy_t * scale - half_S
        shapes.append(Pos(cx, cy, r) * Sphere(r))

    # ── Wall cylinders ───────────────────────────────────────────────
    for (x1_t, y1_t), (x2_t, y2_t) in segments:
        x1 = x1_t * scale - half_S
        y1 = y1_t * scale - half_S
        x2 = x2_t * scale - half_S
        y2 = y2_t * scale - half_S

        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1e-9:
            continue

        direction = Vector(dx, dy, 0).normalized()
        dot = z_axis.dot(direction)
        rot_axis = z_axis.cross(direction)
        angle = math.degrees(math.acos(max(-1.0, min(1.0, dot))))

        loc = Location((mx, my, r)) * Location(
            (0, 0, 0),
            (rot_axis.X, rot_axis.Y, rot_axis.Z),
            angle,
        )
        shapes.append(loc * Cylinder(r, length))

    return Compound(children=shapes)


def save_model(
    model: "Shape",
    path: str,
    *,
    tolerance: float = 0.01,
    angular_tolerance: float = 5.0,
) -> None:
    """Export *model* to STEP or STL based on file extension."""
    from build123d import export_step, export_stl

    lower = path.lower()
    if lower.endswith((".step", ".stp")):
        export_step(model, path)
    elif lower.endswith(".stl"):
        export_stl(
            model, path,
            tolerance=tolerance,
            angular_tolerance=angular_tolerance,
        )
    else:
        raise ValueError(f"Unsupported format: {path!r}  (use .step or .stl)")


# ── Dual graph (Ball-and-Stick) ──────────────────────────────────────────

def build_dual(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    node_radius: float = 1.0,
    edge_radius: float = 0.5,
    height_multiplier: float = 1.0,
) -> Part:
    """Build a ball-and-stick 3D dual graph from SPSS tiles.

    Each tile's conceptual cube has height ``side * scale * height_multiplier``.
    The node (sphere) is placed at the cube's centroid.  Adjacent nodes are
    connected by cylinders.

    When *height_multiplier* is 0 all nodes sit at Z = *node_radius*
    (flat graph — Plan A).

    Parameters
    ----------
    scale:
        Millimetres per tile unit.
    node_radius:
        Radius of node spheres in mm.
    edge_radius:
        Radius of edge cylinders in mm.
    height_multiplier:
        Z-height factor.  ``1.0`` treats each tile as a cube (side = height).
        ``0`` produces a flat graph.
    """
    from build123d import (
        BuildPart,
        Cylinder,
        Location,
        Locations,
        Sphere,
        Vector,
    )

    S = size * scale
    half_S = S / 2

    # ── compute 3D node positions ────────────────────────────────────
    nodes_3d: list[tuple[float, float, float]] = []
    for x, y, s in tiles:
        cx = (x + s / 2) * scale - half_S
        cy = (y + s / 2) * scale - half_S
        if height_multiplier > 0:
            cz = max(node_radius, s * scale * height_multiplier / 2)
        else:
            cz = node_radius
        nodes_3d.append((cx, cy, cz))

    # ── adjacency edges (unique pairs) ───────────────────────────────
    adj = build_adjacency(tiles)
    edge_pairs: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for i, neighbours in adj.items():
        for j in neighbours:
            key = (min(i, j), max(i, j))
            if key not in seen:
                seen.add(key)
                edge_pairs.append(key)

    # ── build model ──────────────────────────────────────────────────
    with BuildPart() as part:
        # Nodes
        for cx, cy, cz in nodes_3d:
            with Locations([(cx, cy, cz)]):
                Sphere(node_radius)

        # Edges
        for i, j in edge_pairs:
            p1 = Vector(*nodes_3d[i])
            p2 = Vector(*nodes_3d[j])
            mid = (p1 + p2) * 0.5
            diff = p2 - p1
            length = diff.length

            # Build a Z-aligned cylinder and rotate it into place
            direction = diff.normalized()
            z_axis = Vector(0, 0, 1)
            dot = z_axis.dot(direction)

            if abs(dot - 1.0) < 1e-9:
                # Already aligned with Z
                loc = Location(mid, (0, 0, 0))
            elif abs(dot + 1.0) < 1e-9:
                # Anti-parallel to Z — rotate 180° around X
                loc = Location(mid, (180, 0, 0))
            else:
                rot_axis = z_axis.cross(direction)
                angle = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
                # Location from axis-angle: rotate around rot_axis at mid
                loc = Location(mid) * Location(
                    (0, 0, 0),
                    (rot_axis.X, rot_axis.Y, rot_axis.Z),
                    angle,
                )

            with Locations([loc]):
                Cylinder(edge_radius, length)

    return part.part
