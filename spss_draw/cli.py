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
    from spss_draw.draw_2d import PALETTE, draw, draw_dual

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
    parser.add_argument(
        "--dual", action="store_true",
        help="Draw the dual graph (nodes at tile centres, edges for adjacency)",
    )
    parser.add_argument(
        "--no-background", action="store_true",
        help="(dual mode) Hide the background tiling",
    )
    parser.add_argument(
        "--node-size", type=float, default=6.0,
        help="(dual mode) Base node marker size in points (default: 6.0)",
    )
    parser.add_argument(
        "--node-amplify", type=float, default=0.0,
        help="(dual mode) Additional size proportional to tile side; "
             "0 = uniform nodes (default: 0)",
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

    common_kw = dict(
        color_indices=indices,
        palette=palette,
        edge_color=normalize_color(args.edge_color),
        edge_width=args.edge_width,
        outer_edge_color=normalize_color(args.outer_edge_color),
        outer_edge_width=args.outer_edge_width,
        output_path=args.output,
        dpi=args.dpi,
    )

    if args.dual:
        draw_dual(
            size,
            tiles,
            show_background=not args.no_background,
            node_size=args.node_size,
            node_amplify=args.node_amplify,
            **common_kw,
        )
    else:
        draw(
            size,
            tiles,
            **common_kw,
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

    # ── skeleton mode options ────────────────────────────────────────
    parser.add_argument(
        "--wall-thickness", type=float, default=1.0,
        help="Wall thickness in mm (default: 1.0)",
    )
    parser.add_argument(
        "--outer-wall-thickness", type=float, default=None,
        help="Outer boundary wall thickness in mm; "
             "defaults to --wall-thickness if omitted",
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
        help="Per-tile height scaling. "
             "Skeleton: wall_h = height + side*scale*MULT. "
             "Dual: cube Z-height factor (default: 0).",
    )

    # ── round skeleton mode ──────────────────────────────────────────
    parser.add_argument(
        "--round", action="store_true",
        help="Use cylinder-based rounded skeleton (wall_thickness == height)",
    )

    # ── dual mode options ────────────────────────────────────────────
    parser.add_argument(
        "--dual", action="store_true",
        help="Generate a ball-and-stick dual graph instead of a skeleton",
    )
    parser.add_argument(
        "--node-radius", type=float, default=1.0,
        help="(dual) Node sphere radius in mm (default: 1.0)",
    )
    parser.add_argument(
        "--edge-radius", type=float, default=0.5,
        help="(dual) Edge cylinder radius in mm (default: 0.5)",
    )

    # ── infill mode options ──────────────────────────────────────────
    parser.add_argument(
        "--infill", choices=["relief", "engraved"], default=None,
        help="Infill mode: 'relief' (raised tiles on both faces) or "
             "'engraved' (carved tiles on both faces). "
             "Mutually exclusive with --round / --dual.",
    )
    parser.add_argument(
        "--relief-depth", type=float, default=0.3,
        help="(infill relief) Relief height per face in mm (default: 0.3)",
    )
    parser.add_argument(
        "--carve-depth", type=float, default=0.5,
        help="(infill engraved) Carve depth per face in mm; "
             "clamped to 45%% of base-thickness (default: 0.5)",
    )
    parser.add_argument(
        "--groove-width", type=float, default=None,
        help="(infill) Groove / ridge width between tiles in mm "
             "(default: 0.3 for relief, 0.5 for engraved)",
    )
    parser.add_argument(
        "--fillet-radius", type=float, default=0.0,
        help="(infill) Fillet radius for rounding edges in mm; "
             "0 = sharp edges. Auto-clamped to safe max (default: 0)",
    )

    _add_transform_args(parser)

    # ── STL tessellation options ──────────────────────────────────────
    parser.add_argument(
        "--stl-tolerance", type=float, default=0.01,
        help="STL linear deflection in mm (default: 0.01). "
             "Lower = finer mesh, higher = fewer polygons.",
    )
    parser.add_argument(
        "--stl-angular-tolerance", type=float, default=5.0,
        help="STL angular deflection in degrees (default: 5). "
             "Lower = finer mesh, higher = fewer polygons.",
    )

    args = parser.parse_args()

    # ── mutual exclusion check ───────────────────────────────────────
    mode_flags = []
    if args.dual:
        mode_flags.append("--dual")
    if getattr(args, "round"):
        mode_flags.append("--round")
    if args.infill:
        mode_flags.append(f"--infill {args.infill}")
    if len(mode_flags) > 1:
        parser.error(
            f"Mutually exclusive options used together: {', '.join(mode_flags)}"
        )

    size, tiles = _prepare_tiles(
        rotate=args.rotate, flip_h=args.flip_h, flip_v=args.flip_v,
    )
    print(f"Tiles: {len(tiles)}, size {size}×{size}")
    print(f"Scale: {args.scale} mm/unit → {size * args.scale:.1f} mm total")

    from spss_draw.draw_3d import save_model

    if args.infill == "relief":
        from spss_draw.draw_3d import build_infill_relief

        bt = args.base_thickness if args.base_thickness > 0 else 0.6
        gw = args.groove_width if args.groove_width is not None else 0.3
        fr = args.fillet_radius
        print(f"Infill relief: base={bt} mm, "
              f"relief_depth={args.relief_depth} mm, "
              f"groove={gw} mm"
              f"{f', fillet={fr} mm' if fr > 0 else ''}")

        model = build_infill_relief(
            size,
            tiles,
            scale=args.scale,
            base_thickness=bt,
            relief_depth=args.relief_depth,
            groove_width=gw,
            fillet_radius=fr,
        )
    elif args.infill == "engraved":
        from spss_draw.draw_3d import build_infill_engraved

        bt = args.base_thickness if args.base_thickness > 0 else 1.5
        gw = args.groove_width if args.groove_width is not None else 0.5
        max_depth = 0.45 * bt
        effective_depth = args.carve_depth
        if effective_depth > max_depth:
            print(f"WARNING: --carve-depth {effective_depth} mm exceeds 45% "
                  f"of base-thickness ({max_depth:.2f} mm). "
                  f"Clamped to {max_depth:.2f} mm.",
                  file=sys.stderr)
            effective_depth = max_depth

        fr = args.fillet_radius
        print(f"Infill engraved: base={bt} mm, "
              f"carve_depth={effective_depth:.2f} mm, "
              f"groove={gw} mm"
              f"{f', fillet={fr} mm' if fr > 0 else ''}")

        model = build_infill_engraved(
            size,
            tiles,
            scale=args.scale,
            base_thickness=bt,
            carve_depth=effective_depth,
            groove_width=gw,
            fillet_radius=fr,
        )
    elif args.dual:
        from spss_draw.draw_3d import build_dual

        print(f"Dual mode: node_r={args.node_radius} mm, "
              f"edge_r={args.edge_radius} mm, "
              f"height_multiplier={args.height_multiplier}")
        if args.height_multiplier > 0:
            max_s = max(s for _, _, s in tiles)
            min_s = min(s for _, _, s in tiles)
            z_min = min_s * args.scale * args.height_multiplier / 2
            z_max = max_s * args.scale * args.height_multiplier / 2
            print(f"  Node Z range: {z_min:.1f}–{z_max:.1f} mm")
        else:
            print("  Flat graph (all nodes at same Z)")

        model = build_dual(
            size,
            tiles,
            scale=args.scale,
            node_radius=args.node_radius,
            edge_radius=args.edge_radius,
            height_multiplier=args.height_multiplier,
        )
    elif getattr(args, "round"):
        from spss_draw.draw_3d import build_skeleton_round

        wall_radius = args.wall_thickness / 2
        owt = args.outer_wall_thickness
        outer_wall_radius = owt / 2 if owt is not None else None
        print(f"Round skeleton: wall_radius={wall_radius:.2f} mm "
              f"(diameter={args.wall_thickness:.2f} mm)")
        if owt is not None:
            print(f"  Outer wall: radius={outer_wall_radius:.2f} mm "
                  f"(diameter={owt:.2f} mm)")

        model = build_skeleton_round(
            size,
            tiles,
            scale=args.scale,
            wall_radius=wall_radius,
            outer_wall_radius=outer_wall_radius,
        )
    else:
        from spss_draw.draw_3d import build_skeleton

        print(f"Wall: {args.wall_thickness} mm, Height: {args.height} mm",
              end="")
        if args.height_multiplier > 0:
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

        model = build_skeleton(
            size,
            tiles,
            scale=args.scale,
            wall_thickness=args.wall_thickness,
            outer_wall_thickness=args.outer_wall_thickness,
            height=args.height,
            height_multiplier=args.height_multiplier,
            base_thickness=args.base_thickness,
        )

    save_model(
        model, args.output,
        tolerance=args.stl_tolerance,
        angular_tolerance=args.stl_angular_tolerance,
    )
    print(f"Saved to {args.output}")
