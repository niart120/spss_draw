"""CLI entry points for 2D drawing and 3D model generation."""

from __future__ import annotations

import argparse
import sys

from spss_draw.bouwkamp import bouwkamp_to_tiles, validate
from spss_draw.coloring import four_color
from spss_draw.data import DUIJVESTIJN_BOUWKAMP, DUIJVESTIJN_SIZE
from spss_draw.draw_2d import (
    EDGE_COLOR,
    EDGE_WIDTH,
    OUTER_EDGE_COLOR,
    OUTER_EDGE_WIDTH,
    normalize_color,
)
from spss_draw.transforms import transform_tiles


# ── Shared helpers ───────────────────────────────────────────────────────

def _prepare_tiles(
    rotate: int = 0,
    flip_h: bool = False,
    flip_v: bool = False,
) -> tuple[int, list[tuple[int, int, int]]]:
    """Decode, validate, and transform the Duijvestijn SPSS tiles."""
    size = DUIJVESTIJN_SIZE
    tiles = bouwkamp_to_tiles(size, DUIJVESTIJN_BOUWKAMP)
    try:
        validate(size, tiles)
    except ValueError as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    tiles = transform_tiles(size, tiles, rotate=rotate,
                            flip_h=flip_h, flip_v=flip_v)
    return size, tiles


def _add_transform_args(parser: argparse.ArgumentParser) -> None:
    """Add --rotate / --flip-h / --flip-v to *parser*."""
    parser.add_argument(
        "--rotate", type=int, default=0, choices=[0, 90, 180, 270],
        metavar="{0,90,180,270}",
        help="Clockwise rotation in degrees (default: 0)",
    )
    parser.add_argument(
        "--flip-h", action="store_true",
        help="Flip horizontally (mirror left-right)",
    )
    parser.add_argument(
        "--flip-v", action="store_true",
        help="Flip vertically (mirror top-bottom)",
    )


# ── 2D CLI ───────────────────────────────────────────────────────────────

def main_2d() -> None:
    """CLI entry point for 2D drawing (matplotlib)."""
    from spss_draw.draw_2d import PALETTE, draw

    parser = argparse.ArgumentParser(
        description="Draw the Duijvestijn order-21 SPSS.",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE",
        help="Save image to FILE instead of displaying it (e.g. spss.png)",
    )
    parser.add_argument(
        "--dpi", type=float, default=150,
        help="Resolution for saved image (default: 150)",
    )
    parser.add_argument(
        "--edge-color", default=EDGE_COLOR,
        help=f"Tile border color (default: {EDGE_COLOR!r})",
    )
    parser.add_argument(
        "--edge-width", type=float, default=EDGE_WIDTH,
        help=f"Tile border width (default: {EDGE_WIDTH})",
    )
    parser.add_argument(
        "--outer-edge-color", default=OUTER_EDGE_COLOR,
        help=f"Outer border color (default: {OUTER_EDGE_COLOR!r})",
    )
    parser.add_argument(
        "--outer-edge-width", type=float, default=OUTER_EDGE_WIDTH,
        help=f"Outer border width (default: {OUTER_EDGE_WIDTH})",
    )
    parser.add_argument(
        "--palette", nargs=4, metavar="COLOR",
        help="4 colors for tile fills (hex or name)",
    )
    _add_transform_args(parser)
    args = parser.parse_args()

    palette = (
        [normalize_color(c) for c in args.palette] if args.palette else PALETTE
    )
    size, tiles = _prepare_tiles(
        rotate=args.rotate, flip_h=args.flip_h, flip_v=args.flip_v,
    )
    indices = four_color(tiles)

    print(f"Validation passed: {len(tiles)} tiles, size {size}×{size}")
    print("Color assignments (tile side → palette index):")
    for (x, y, s), ci in sorted(zip(tiles, indices), key=lambda t: t[0][2]):
        print(f"  side={s:3d}  palette[{ci}] = {palette[ci]}")

    draw(
        size,
        tiles,
        color_indices=indices,
        palette=palette,
        edge_color=normalize_color(args.edge_color),
        edge_width=args.edge_width,
        outer_edge_color=normalize_color(args.outer_edge_color),
        outer_edge_width=args.outer_edge_width,
        output_path=args.output,
        dpi=args.dpi,
    )


# ── 3D CLI ───────────────────────────────────────────────────────────────

def main_3d() -> None:
    """CLI entry point for 3D skeleton model generation (build123d)."""
    parser = argparse.ArgumentParser(
        description="Generate a 3D skeleton model of the Duijvestijn SPSS.",
    )
    parser.add_argument(
        "-o", "--output", metavar="FILE", default="spss_skeleton.step",
        help="Output path (.step or .stl) (default: spss_skeleton.step)",
    )
    parser.add_argument(
        "--scale", type=float, default=0.5,
        help="mm per tile unit; 0.5 → 56 mm total (default: 0.5)",
    )
    parser.add_argument(
        "--wall-thickness", type=float, default=1.0,
        help="Wall thickness in mm (default: 1.0)",
    )
    parser.add_argument(
        "--height", type=float, default=1.0,
        help="Extrusion height in mm (default: 1.0)",
    )
    parser.add_argument(
        "--base-thickness", type=float, default=0.0,
        help="Solid base thickness in mm; 0 = pure skeleton (default: 0)",
    )
    parser.add_argument(
        "--height-multiplier", type=float, default=0.0,
        help="Per-tile height scaling: wall_h = height + tile_side * scale * MULT. "
             "0 = uniform height (default: 0). Try 0.05–1.0 for varying relief.",
    )
    _add_transform_args(parser)
    args = parser.parse_args()

    size, tiles = _prepare_tiles(
        rotate=args.rotate, flip_h=args.flip_h, flip_v=args.flip_v,
    )
    print(f"Tiles: {len(tiles)}, size {size}×{size}")
    print(f"Scale: {args.scale} mm/unit → {size * args.scale:.1f} mm total")
    print(f"Wall: {args.wall_thickness} mm, Height: {args.height} mm", end="")
    if args.height_multiplier > 0:
        from spss_draw.data import DUIJVESTIJN_SIZE
        max_s = max(s for _, _, s in tiles)
        min_s = min(s for _, _, s in tiles)
        h_min = args.height + min_s * args.scale * args.height_multiplier
        h_max = args.height + max_s * args.scale * args.height_multiplier
        print(f", height-multiplier: {args.height_multiplier} "
              f"(range {h_min:.1f}–{h_max:.1f} mm)")
    elif args.base_thickness > 0:
        print(f", Base: {args.base_thickness} mm")
    else:
        print(" (pure skeleton)")

    from spss_draw.draw_3d import build_skeleton, save_model

    model = build_skeleton(
        size,
        tiles,
        scale=args.scale,
        wall_thickness=args.wall_thickness,
        height=args.height,
        height_multiplier=args.height_multiplier,
        base_thickness=args.base_thickness,
    )
    save_model(model, args.output)
    print(f"Saved to {args.output}")
