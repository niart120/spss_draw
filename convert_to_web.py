#!/usr/bin/env python3
"""Convert STL models in model/ to GLB + USDZ for web viewing & iPhone AR.

Usage:
    uv sync --extra web
    uv run convert_to_web.py

Or without modifying the venv:
    uv run --extra web convert_to_web.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import trimesh


# ---- human-readable label from filename ----
_LABEL_MAP: dict[str, str] = {
    "spss_skeleton_flat": "Skeleton (flat)",
    "spss_skeleton_multi": "Skeleton (multi-height)",
    "spss_thin": "Skeleton (thin wall)",
    "round_large_fixed": "Round skeleton",
    "dual_flat": "Dual graph (flat)",
}


def _make_label(stem: str) -> str:
    """Return a display label for *stem*, using the map or auto-generating."""
    if stem in _LABEL_MAP:
        return _LABEL_MAP[stem]
    # e.g. "spss_s1.2" → "Spss s1.2", "dual_s1.2" → "Dual s1.2"
    # Detect prefix for category
    if stem.startswith("dual"):
        category = "Dual graph"
    elif stem.startswith("round"):
        category = "Round skeleton"
    elif stem.startswith("spss"):
        category = "Skeleton"
    else:
        category = stem.replace("_", " ").capitalize()
        return category

    # Extract the trailing parameter part (e.g. "s1.2")
    m = re.search(r"(?:spss_|dual_|round_)(.+)", stem)
    detail = m.group(1).replace("_", " ") if m else ""
    return f"{category} ({detail})" if detail else category


# ---- USDZ export via OpenUSD (usd-core) ----

def _export_usdz(mesh: trimesh.Trimesh, path: Path) -> bool:
    """Export *mesh* as USDZ. Returns True on success."""
    try:
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdUtils, Vt
    except ImportError:
        return False

    tmp_usdc = path.with_suffix(".usdc")
    stage = Usd.Stage.CreateNew(str(tmp_usdc))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 0.001)  # mm

    mesh_prim = UsdGeom.Mesh.Define(stage, "/Model/Mesh")
    mesh_prim.GetPointsAttr().Set(
        Vt.Vec3fArray([Gf.Vec3f(*v) for v in mesh.vertices])
    )
    mesh_prim.GetFaceVertexCountsAttr().Set(
        Vt.IntArray([3] * len(mesh.faces))
    )
    mesh_prim.GetFaceVertexIndicesAttr().Set(
        Vt.IntArray(mesh.faces.flatten().tolist())
    )
    if mesh.vertex_normals is not None and len(mesh.vertex_normals) > 0:
        mesh_prim.GetNormalsAttr().Set(
            Vt.Vec3fArray([Gf.Vec3f(*n) for n in mesh.vertex_normals])
        )
        mesh_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)

    # Simple grey material so the model renders on iOS
    mat = UsdShade.Material.Define(stage, "/Model/Material")
    shader = UsdShade.Shader.Define(stage, "/Model/Material/PBRShader")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.7, 0.7, 0.7)
    )
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.1)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.6)
    mat.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    UsdShade.MaterialBindingAPI(mesh_prim).Bind(mat)

    stage.SetDefaultPrim(stage.GetPrimAtPath("/Model"))
    stage.GetRootLayer().Save()

    UsdUtils.CreateNewUsdzPackage(Sdf.AssetPath(str(tmp_usdc)), str(path))
    tmp_usdc.unlink(missing_ok=True)
    return True


def main() -> None:
    model_dir = Path("model")
    base_dir = Path("docs/models")
    glb_dir = base_dir / "glb"
    usdz_dir = base_dir / "usdz"
    glb_dir.mkdir(parents=True, exist_ok=True)
    usdz_dir.mkdir(parents=True, exist_ok=True)

    stl_files = sorted(model_dir.glob("*.stl"))
    if not stl_files:
        print("No STL files found in model/")
        return

    # Check USDZ support availability once
    try:
        from pxr import Usd as _  # noqa: F401
        has_usd = True
        print("  usd-core detected — USDZ export enabled\n")
    except ImportError:
        has_usd = False
        print("  usd-core not found — skipping USDZ (install with: pip install usd-core)\n")

    manifest: list[dict[str, str]] = []

    for stl_path in stl_files:
        stem = stl_path.stem
        mesh = trimesh.load(stl_path)

        # GLB
        glb_name = f"{stem}.glb"
        glb_path = glb_dir / glb_name
        print(f"  {stl_path} -> {glb_path}")
        mesh.export(glb_path, file_type="glb")

        entry: dict[str, str] = {"file": f"glb/{glb_name}", "label": _make_label(stem)}

        # USDZ
        if has_usd:
            usdz_name = f"{stem}.usdz"
            usdz_path = usdz_dir / usdz_name
            if _export_usdz(mesh, usdz_path):
                print(f"  {stl_path} -> {usdz_path}")
                entry["usdz"] = f"usdz/{usdz_name}"
            else:
                print(f"  ⚠ USDZ export failed for {stem}")

        manifest.append(entry)

    # Write manifest for the web gallery
    manifest_path = base_dir / "models.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\n  Manifest written to {manifest_path}")

    print(f"\nDone — {len(stl_files)} models converted to {base_dir}/")


if __name__ == "__main__":
    main()
