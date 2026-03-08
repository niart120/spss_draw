"""build123d-based 3D skeleton model generation for SPSS tilings.

The skeleton is constructed by extruding the full square as a solid block and
then subtracting the interior of every tile, leaving only the wall edges as a
wireframe-like structure.
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
    from build123d import Box, BuildPart, Locations, Mode

    S = size * scale
    # Make the outer box slightly larger so outer walls equal wall_thickness.
    outer = S + wall_thickness

    # When height_multiplier is active the outer block must be tall enough
    # to cover the tallest tile wall.
    max_side = max(s for _, _, s in tiles)
    max_height = (
        height + max_side * scale * height_multiplier
        if height_multiplier > 0
        else height
    )

    with BuildPart() as part:
        # Solid block tall enough for the tallest wall
        Box(outer, outer, max_height)

        for x, y, s in tiles:
            cut_side = s * scale - wall_thickness
            if cut_side <= 0:
                continue

            # Per-tile wall height when multiplier is active
            tile_height = (
                height + s * scale * height_multiplier
                if height_multiplier > 0
                else height
            )

            # Tile centre relative to model origin
            cx = (x + s / 2) * scale - S / 2
            cy = (y + s / 2) * scale - S / 2

            # Cut away everything above this tile's wall height first
            if height_multiplier > 0 and tile_height < max_height:
                trim_h = max_height - tile_height
                trim_z = tile_height + trim_h / 2
                with Locations([(cx, cy, trim_z)]):
                    Box(cut_side + wall_thickness, cut_side + wall_thickness,
                        trim_h + 0.02, mode=Mode.SUBTRACT)

            if 0 < base_thickness < tile_height:
                cut_h = tile_height - base_thickness
                cz = base_thickness / 2
            else:
                cut_h = tile_height + 0.02  # ensure clean through-cut
                cz = 0.0

            with Locations([(cx, cy, cz)]):
                Box(cut_side, cut_side, cut_h, mode=Mode.SUBTRACT)

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
