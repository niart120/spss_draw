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
    outer_wall_thickness: float | None = None,
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
    owt = outer_wall_thickness if outer_wall_thickness is not None else wall_thickness
    half_wt = wall_thickness / 2
    outer_half_wt = owt / 2

    def _tile_h(s: int) -> float:
        if height_multiplier > 0:
            return height + s * scale * height_multiplier
        return height

    # Z-align: bottom face sits at the Locations z-coordinate.
    Z_ALIGN = (Align.CENTER, Align.CENTER, Align.MIN)

    with BuildPart() as part:
        # ── Phase 1: Add per-tile solid blocks ───────────────────────
        # Each block extends half the wall thickness beyond the tile
        # boundary on every side.  Boundary sides use outer_half_wt,
        # internal sides use half_wt.
        for x, y, s in tiles:
            th = _tile_h(s)
            lo = outer_half_wt if x == 0 else half_wt
            ro = outer_half_wt if x + s == size else half_wt
            bo = outer_half_wt if y == 0 else half_wt
            to_ = outer_half_wt if y + s == size else half_wt
            bx1 = x * scale - lo
            bx2 = (x + s) * scale + ro
            by1 = y * scale - bo
            by2 = (y + s) * scale + to_
            w = bx2 - bx1
            d = by2 - by1
            cx = (bx1 + bx2) / 2 - half_S
            cy = (by1 + by2) / 2 - half_S
            with Locations([(cx, cy, 0)]):
                Box(w, d, th, align=Z_ALIGN)

        # ── Phase 2: Hollow tile interiors ───────────────────────────
        for x, y, s in tiles:
            th = _tile_h(s)
            lo = outer_half_wt if x == 0 else half_wt
            ro = outer_half_wt if x + s == size else half_wt
            bo = outer_half_wt if y == 0 else half_wt
            to_ = outer_half_wt if y + s == size else half_wt
            cut_w = s * scale - lo - ro
            cut_d = s * scale - bo - to_
            if cut_w <= 0 or cut_d <= 0:
                continue  # tile too small to hollow
            cx = (x * scale + lo + (x + s) * scale - ro) / 2 - half_S
            cy = (y * scale + bo + (y + s) * scale - to_) / 2 - half_S

            if 0 < base_thickness < th:
                with Locations([(cx, cy, base_thickness)]):
                    Box(cut_w, cut_d, th - base_thickness + 0.01,
                        align=Z_ALIGN, mode=Mode.SUBTRACT)
            else:
                with Locations([(cx, cy, -0.01)]):
                    Box(cut_w, cut_d, th + 0.02,
                        align=Z_ALIGN, mode=Mode.SUBTRACT)

    return part.part


# ── Wall-segment enumeration ─────────────────────────────────────────────

def _compute_wall_segments(
    size: int,
    tiles: list[tuple[int, int, int]],
) -> tuple:
    """Return wall segments as ``((x1, y1), (x2, y2))`` in tile units.

    Returns ``(internal_segments, outer_segments)`` where *internal* are
    shared edges between adjacent tiles and *outer* lie on the boundary.
    """
    internal: list[tuple[tuple[int, int], tuple[int, int]]] = []
    outer: list[tuple[tuple[int, int], tuple[int, int]]] = []
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
                    internal.append(((xi + si, y_lo), (xi + si, y_hi)))
            elif xj + sj == xi:
                y_lo = max(yi, yj)
                y_hi = min(yi + si, yj + sj)
                if y_hi > y_lo:
                    internal.append(((xi, y_lo), (xi, y_hi)))
            # Shared horizontal edge
            if yi + si == yj:
                x_lo = max(xi, xj)
                x_hi = min(xi + si, xj + sj)
                if x_hi > x_lo:
                    internal.append(((x_lo, yi + si), (x_hi, yi + si)))
            elif yj + sj == yi:
                x_lo = max(xi, xj)
                x_hi = min(xi + si, xj + sj)
                if x_hi > x_lo:
                    internal.append(((x_lo, yi), (x_hi, yi)))

    # Outer boundary edges
    for x, y, s in tiles:
        if x == 0:
            outer.append(((0, y), (0, y + s)))
        if x + s == size:
            outer.append(((size, y), (size, y + s)))
        if y == 0:
            outer.append(((x, 0), (x + s, 0)))
        if y + s == size:
            outer.append(((x, y + s), (x + s, y + s)))

    return internal, outer


def build_skeleton_round(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    wall_radius: float = 0.5,
    outer_wall_radius: float | None = None,
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
        Radius of internal wall cylinders and junction spheres in mm.
        The resulting wall thickness (diameter) and height are both
        ``2 * wall_radius``.
    outer_wall_radius:
        Radius for outer-boundary wall cylinders and boundary junction
        spheres.  ``None`` falls back to *wall_radius*.
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
    r_out = outer_wall_radius if outer_wall_radius is not None else r

    internal_segs, outer_segs = _compute_wall_segments(size, tiles)

    # Unique junction points (tile corners)
    corners: set[tuple[int, int]] = set()
    for x, y, s in tiles:
        corners.update(((x, y), (x + s, y), (x, y + s), (x + s, y + s)))

    # Identify boundary corners for outer radius
    boundary_corners: set[tuple[int, int]] = set()
    for cx_t, cy_t in corners:
        if cx_t == 0 or cx_t == size or cy_t == 0 or cy_t == size:
            boundary_corners.add((cx_t, cy_t))

    z_axis = Vector(0, 0, 1)
    shapes = []

    # ── Junction spheres ─────────────────────────────────────────────
    for cx_t, cy_t in corners:
        cr = r_out if (cx_t, cy_t) in boundary_corners else r
        cx = cx_t * scale - half_S
        cy = cy_t * scale - half_S
        shapes.append(Pos(cx, cy, cr) * Sphere(cr))

    # ── Wall cylinders ───────────────────────────────────────────────
    for segs, seg_r in [(internal_segs, r), (outer_segs, r_out)]:
        for (x1_t, y1_t), (x2_t, y2_t) in segs:
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

            loc = Location((mx, my, seg_r)) * Location(
                (0, 0, 0),
                (rot_axis.X, rot_axis.Y, rot_axis.Z),
                angle,
            )
            shapes.append(loc * Cylinder(seg_r, length))

    return Compound(children=shapes)


def build_infill_relief(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    base_thickness: float = 0.6,
    relief_depth: float = 0.3,
    groove_width: float = 0.5,
    fillet_radius: float = 0.0,
) -> "Part | Compound":
    """Build a double-sided relief model from SPSS tiles.

    A solid base plate with uniform-height tile blocks protruding from
    **both** the top and bottom faces.  Tiles are separated by grooves
    of *groove_width* so the SPSS pattern is visible.

    Parameters
    ----------
    size:
        Side length of the outer SPSS square (in tile units).
    tiles:
        List of ``(x, y, side)`` tuples.
    scale:
        Millimetres per tile unit.
    base_thickness:
        Thickness of the central base plate in mm.
    relief_depth:
        Height of each tile block above/below the base surface (mm).
    groove_width:
        Width of the groove between adjacent tiles (mm).
    fillet_radius:
        Radius for rounding exposed edges of each tile block (mm).
        ``0`` disables filleting.  Automatically clamped to a safe max.
    """
    from build123d import Align, Axis, Box, BuildPart, Compound, Locations, Pos

    S = size * scale
    half_S = S / 2
    half_bt = base_thickness / 2

    Z_ALIGN_UP = (Align.CENTER, Align.CENTER, Align.MIN)
    Z_ALIGN_DOWN = (Align.CENTER, Align.CENTER, Align.MAX)

    if fillet_radius > 0:
        from build123d import fillet as bd_fillet

        # Clamp fillet radius — compute minimum tile block dimension
        # accounting for wider margins on boundary edges.
        gw2 = groove_width / 2
        min_block = float('inf')
        for xb, yb, sb in tiles:
            _ml = groove_width if xb == 0 else gw2
            _mr = groove_width if xb + sb == size else gw2
            _mb = groove_width if yb == 0 else gw2
            _mt = groove_width if yb + sb == size else gw2
            min_block = min(min_block, sb * scale - _ml - _mr,
                            sb * scale - _mb - _mt)
        max_r = min(min_block / 2, relief_depth, groove_width / 2) * 0.95
        r = min(fillet_radius, max_r)
        if r < 1e-6:
            r = 0

        shapes: list = []

        # Base plate (rounded corners when fillet enabled)
        from build123d import BuildPart as _BP, BuildSketch, Plane, RectangleRounded, extrude
        with _BP() as _base:
            with BuildSketch(Plane.XY.offset(-half_bt)):
                RectangleRounded(S, S, radius=r)
            extrude(amount=base_thickness)
        shapes.append(_base.part)

        for x, y, s in tiles:
            ml = groove_width if x == 0 else gw2
            mr = groove_width if x + s == size else gw2
            mb = groove_width if y == 0 else gw2
            mt = groove_width if y + s == size else gw2
            tw = s * scale - ml - mr
            th = s * scale - mb - mt
            if tw <= 0 or th <= 0:
                continue
            cx = x * scale - half_S + ml + tw / 2
            cy = y * scale - half_S + mb + th / 2

            # Top block — fillet the top 4 edges
            block = Box(tw, th, relief_depth)
            if r > 0:
                top_edges = block.edges().sort_by(Axis.Z)[-4:]
                block = bd_fillet(top_edges, radius=r)
            shapes.append(
                Pos(cx, cy, half_bt + relief_depth / 2) * block
            )

            # Bottom block — fillet the bottom 4 edges
            block = Box(tw, th, relief_depth)
            if r > 0:
                bot_edges = block.edges().sort_by(Axis.Z)[:4]
                block = bd_fillet(bot_edges, radius=r)
            shapes.append(
                Pos(cx, cy, -(half_bt + relief_depth / 2)) * block
            )

        return Compound(children=shapes)

    # Non-fillet path: proper boolean union via BuildPart
    gw2 = groove_width / 2
    with BuildPart() as part:
        with Locations([(0, 0, -half_bt)]):
            Box(S, S, base_thickness, align=Z_ALIGN_UP)

        for x, y, s in tiles:
            ml = groove_width if x == 0 else gw2
            mr = groove_width if x + s == size else gw2
            mb = groove_width if y == 0 else gw2
            mt = groove_width if y + s == size else gw2
            tw = s * scale - ml - mr
            th = s * scale - mb - mt
            if tw <= 0 or th <= 0:
                continue
            cx = x * scale - half_S + ml + tw / 2
            cy = y * scale - half_S + mb + th / 2

            with Locations([(cx, cy, half_bt)]):
                Box(tw, th, relief_depth, align=Z_ALIGN_UP)

            with Locations([(cx, cy, -half_bt)]):
                Box(tw, th, relief_depth, align=Z_ALIGN_DOWN)

    return part.part


def build_infill_engraved(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    base_thickness: float = 1.0,
    carve_depth: float = 0.3,
    groove_width: float = 0.5,
    fillet_radius: float = 0.0,
) -> "Part | Compound":
    """Build a double-sided engraved model from SPSS tiles.

    A solid slab with each tile's interior carved to a uniform depth from
    **both** the top and bottom faces, leaving ridges at tile boundaries.

    The carve depth is clamped to 45% of *base_thickness* so the two
    sides never meet (at most 90% total material removed; 10% remains).

    When *fillet_radius* > 0, horizontal cylinders and spheres are placed
    along the ridge tops (both faces) to give a smooth rounded profile,
    similar to the approach used in ``build_skeleton_round``.

    Parameters
    ----------
    size:
        Side length of the outer SPSS square (in tile units).
    tiles:
        List of ``(x, y, side)`` tuples.
    scale:
        Millimetres per tile unit.
    base_thickness:
        Thickness of the slab in mm.
    carve_depth:
        Depth to carve from each face (mm).  Clamped to
        ``0.45 * base_thickness``.
    groove_width:
        Width of the ridges left between tiles (mm).
    fillet_radius:
        Radius for rounding the ridge tops (mm).  Clamped to
        ``groove_width / 2``.  ``0`` disables rounding.
    """
    from build123d import Align, Box, BuildPart, Locations, Mode

    max_depth = 0.45 * base_thickness
    if carve_depth > max_depth:
        carve_depth = max_depth

    S = size * scale
    half_S = S / 2
    half_bt = base_thickness / 2

    Z_ALIGN_UP = (Align.CENTER, Align.CENTER, Align.MIN)
    Z_ALIGN_DOWN = (Align.CENTER, Align.CENTER, Align.MAX)

    # Ridge rounding radius — always match the ridge half-width so
    # the cylinder/sphere caps sit flush with the ridge surface.
    r = 0.0
    if fillet_radius > 0:
        r = groove_width / 2

    with BuildPart() as part:
        # ── Solid slab (centred at Z=0) ──────────────────────────────
        if r > 0:
            # Rounded-corner slab so outer edges are smooth
            from build123d import BuildSketch, Plane, RectangleRounded, extrude
            with BuildSketch(Plane.XY.offset(-half_bt)):
                RectangleRounded(S, S, radius=r)
            extrude(amount=base_thickness)
        else:
            with Locations([(0, 0, -half_bt)]):
                Box(S, S, base_thickness, align=Z_ALIGN_UP)

        # ── Carve each tile from both faces (sharp) ─────────────────
        gw2 = groove_width / 2
        for x, y, s in tiles:
            ml = groove_width if x == 0 else gw2
            mr = groove_width if x + s == size else gw2
            mb = groove_width if y == 0 else gw2
            mt = groove_width if y + s == size else gw2
            tw = s * scale - ml - mr
            th = s * scale - mb - mt
            if tw <= 0 or th <= 0:
                continue
            cx = x * scale - half_S + ml + tw / 2
            cy = y * scale - half_S + mb + th / 2

            with Locations([(cx, cy, half_bt - carve_depth)]):
                Box(tw, th, carve_depth + 0.01,
                    align=Z_ALIGN_UP, mode=Mode.SUBTRACT)

            with Locations([(cx, cy, -half_bt + carve_depth)]):
                Box(tw, th, carve_depth + 0.01,
                    align=Z_ALIGN_DOWN, mode=Mode.SUBTRACT)

    carved = part.part

    if r <= 0:
        return carved

    # ── Add rounded ridge caps using cylinders and spheres ───────────
    # This places geometry ON TOP of the ridges (at both slab surfaces)
    # to smooth the sharp 90° edges into a rounded profile.
    from build123d import (
        Compound,
        Cylinder,
        Location,
        Pos,
        Sphere,
        Vector,
    )

    internal_segs, outer_segs = _compute_wall_segments(size, tiles)

    # Collect all corner points
    corners: set[tuple[int, int]] = set()
    for x, y, s in tiles:
        corners.update(((x, y), (x + s, y), (x, y + s), (x + s, y + s)))

    z_axis = Vector(0, 0, 1)
    shapes: list = [carved]

    # Helper: tile-unit coord → mm.  Boundary coords (0 or size) are
    # shifted inward by groove_width/2 so caps sit on the outer ridge
    # centre rather than at the slab edge.
    gw2 = groove_width / 2

    def _to_mm(v: int) -> float:
        mm = v * scale - half_S
        if v == 0:
            return mm + gw2
        if v == size:
            return mm - gw2
        return mm

    for face_z in [half_bt, -half_bt]:
        # ── Junction spheres on ALL ridge intersections ──────────────
        for cx_t, cy_t in corners:
            shapes.append(
                Pos(_to_mm(cx_t), _to_mm(cy_t), face_z) * Sphere(r)
            )

        # ── Cylinders along ALL ridges (internal + outer) ────────────
        for segs in [internal_segs, outer_segs]:
            for (x1_t, y1_t), (x2_t, y2_t) in segs:
                x1, y1 = _to_mm(x1_t), _to_mm(y1_t)
                x2, y2 = _to_mm(x2_t), _to_mm(y2_t)

                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx * dx + dy * dy)
                if length < 1e-9:
                    continue

                direction = Vector(dx, dy, 0).normalized()
                dot = z_axis.dot(direction)
                rot_axis = z_axis.cross(direction)
                angle = math.degrees(math.acos(max(-1.0, min(1.0, dot))))

                loc = Location((mx, my, face_z)) * Location(
                    (0, 0, 0),
                    (rot_axis.X, rot_axis.Y, rot_axis.Z),
                    angle,
                )
                shapes.append(loc * Cylinder(r, length))

    return Compound(children=shapes)


# ── Pendant ring helpers ─────────────────────────────────────────────────

def _add_pendant_rings(
    base_model: "Shape",
    slab_size: float,
    total_height: float,
    *,
    corner_positions: list[tuple[float, float, float]],
    ring_hole_diameter: float = 2.0,
    ring_wall: float = 0.8,
    groove_width: float = 0.5,
    fillet_radius: float = 0.0,
) -> "Compound":
    """Add reinforced chain-ring lugs at specified corners of *base_model*.

    Each lug is a cylinder (with through-hole) placed at 45° outward from
    the corner, with a bridge for strength.  Lugs are built as separate
    solids and assembled via ``Compound`` to avoid boolean interference.

    Parameters
    ----------
    base_model:
        The infill model (relief or engraved) to augment.
    slab_size:
        Side length of the square slab in mm.
    total_height:
        Total height of the slab (including relief/carve) in mm.
    corner_positions:
        List of ``(corner_x_mm, corner_y_mm, angle_degrees)`` for each
        lug.  *angle* is the outward diagonal direction (e.g. 45° for
        top-right).
    ring_hole_diameter:
        Diameter of the chain hole in mm.
    ring_wall:
        Wall thickness around the hole in mm.
    fillet_radius:
        Reserved for future use.
    """
    from build123d import (
        Align,
        BuildPart,
        Compound,
        Cylinder,
        Locations,
        Mode,
    )

    hole_r = ring_hole_diameter / 2
    outer_r = hole_r + ring_wall

    # Lug centre offset from slab corner along diagonal.
    # outer_r minus groove_width keeps the lug overlapping the slab's
    # outer wall by groove_width, adapting to the groove setting.
    offset = outer_r - groove_width
    diag = offset / math.sqrt(2)

    lug_parts: list = []
    for corner_x, corner_y, ang in corner_positions:
        rad = math.radians(ang)
        cx = corner_x + math.cos(rad) * diag
        cy = corner_y + math.sin(rad) * diag

        with BuildPart() as lug:
            with Locations([(cx, cy, -total_height / 2)]):
                Cylinder(
                    outer_r, total_height,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            with Locations([(cx, cy, -total_height / 2 - 0.01)]):
                Cylinder(
                    hole_r, total_height + 0.02,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )
        lug_parts.append(lug.part)

    children = [base_model] + lug_parts
    return Compound(children=children)


def _find_largest_tile_corner(
    size: int,
    tiles: list[tuple[int, int, int]],
    scale: float,
) -> tuple[float, float, float]:
    """Return ``(corner_x_mm, corner_y_mm, angle)`` for the slab corner
    closest to the largest tile's centre."""
    half_S = size * scale / 2

    # Find the largest tile
    largest = max(tiles, key=lambda t: t[2])
    x, y, s = largest
    # Tile centre in mm (slab-centred coords)
    tcx = (x + s / 2) * scale - half_S
    tcy = (y + s / 2) * scale - half_S

    # Pick the nearest slab corner
    slab_corners = [
        (+half_S, +half_S, 45),
        (-half_S, +half_S, 135),
        (-half_S, -half_S, 225),
        (+half_S, -half_S, 315),
    ]

    best = min(
        slab_corners,
        key=lambda c: (c[0] - tcx) ** 2 + (c[1] - tcy) ** 2,
    )
    return best


def build_pendant_relief(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    base_thickness: float = 0.6,
    relief_depth: float = 0.3,
    groove_width: float = 0.3,
    fillet_radius: float = 0.0,
    ring_hole_diameter: float = 2.0,
    ring_wall: float = 0.8,
) -> "Compound":
    """Build a pendant-style relief model with a chain-ring lug at the
    corner nearest to the largest tile."""
    base = build_infill_relief(
        size, tiles,
        scale=scale,
        base_thickness=base_thickness,
        relief_depth=relief_depth,
        groove_width=groove_width,
        fillet_radius=fillet_radius,
    )
    S = size * scale
    total_h = base_thickness + 2 * relief_depth
    corner = _find_largest_tile_corner(size, tiles, scale)
    return _add_pendant_rings(
        base, S, total_h,
        corner_positions=[corner],
        ring_hole_diameter=ring_hole_diameter,
        ring_wall=ring_wall,
        groove_width=groove_width,
        fillet_radius=fillet_radius,
    )


def build_pendant_engraved(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    base_thickness: float = 1.0,
    carve_depth: float = 0.3,
    groove_width: float = 0.5,
    fillet_radius: float = 0.0,
    ring_hole_diameter: float = 2.0,
    ring_wall: float = 0.8,
) -> "Compound":
    """Build a pendant-style engraved model with a chain-ring lug at the
    corner nearest to the largest tile."""
    base = build_infill_engraved(
        size, tiles,
        scale=scale,
        base_thickness=base_thickness,
        carve_depth=carve_depth,
        groove_width=groove_width,
        fillet_radius=fillet_radius,
    )
    S = size * scale
    total_h = base_thickness
    corner = _find_largest_tile_corner(size, tiles, scale)
    return _add_pendant_rings(
        base, S, total_h,
        corner_positions=[corner],
        ring_hole_diameter=ring_hole_diameter,
        ring_wall=ring_wall,
        groove_width=groove_width,
        fillet_radius=fillet_radius,
    )


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
