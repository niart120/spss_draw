"""build123d-based 3D skeleton model generation for SPSS tilings.

The skeleton is built additively: each tile contributes a solid block that
extends ``wall_thickness / 2`` beyond its boundary on every side, then the
interior of each tile is subtracted.  Boolean union naturally gives shared
walls the height of the *taller* neighbour.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from build123d import Part


def build_skeleton(
    size: int,
    tiles: list[tuple[int, int, int]],
    *,
    scale: float = 0.5,
    wall_thickness: float = 1.0,
    height: float = 5.0,
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


def save_model(model: Part, path: str) -> None:
    """Export *model* to STEP or STL based on file extension."""
    from build123d import export_step, export_stl

    lower = path.lower()
    if lower.endswith((".step", ".stp")):
        export_step(model, path)
    elif lower.endswith(".stl"):
        export_stl(model, path)
    else:
        raise ValueError(f"Unsupported format: {path!r}  (use .step or .stl)")
