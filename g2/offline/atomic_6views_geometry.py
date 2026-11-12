"""Derive a finite source-bound G2 navigation grid from official MuJoCo geometry.

No hardcoded Layout ID or prerecorded Layout1/10 scene. The TEST_ONLY known
volume is an approximation around the original finite floor slabs; it is not
silently promoted to certified real-camera free space.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from g2.io import ContractError
from g2.sim.source_geometry import load_model, apply_state
from g2.sim.prescan import geom_surface_mesh, geometry_type_names

SCHEMA = "g2_atomic_geometry_bound_navigation_v1"


def grid_from_source(model, state, metadata, *, resolution=.1, margin_m=.25,
                     max_voxels=10_000_000):
    import mujoco
    if not 0 < resolution <= 1 or margin_m < 0:
        raise ContractError("invalid full-map geometry raster configuration")
    if not isinstance(metadata, dict) or metadata.get("schema") != "nav_sg_gt_metadata_v1":
        raise ContractError("actual official scene classification is required")
    kinds = geometry_type_names()
    bboxes = []
    floors = []
    walls = []
    for i in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i) or f"geom_{i}"
        role = metadata.get("geoms", {}).get(name)
        if (not isinstance(role, dict) or role.get("include") is False
                or not (model.geom_contype[i] or model.geom_conaffinity[i])):
            continue
        kind = kinds.get(int(model.geom_type[i]))
        if kind not in ("box", "sphere", "ellipsoid", "capsule", "cylinder", "mesh"):
            raise ContractError("nonfinite selected geom: " + name)
        vertices, _ = geom_surface_mesh(model, i, kind)
        world = vertices @ state.geom_xmat[i].reshape(3, 3).T + state.geom_xpos[i]
        if world.size == 0 or not np.isfinite(world).all():
            raise ContractError("invalid GT world geometry " + name)
        lo, hi = world.min(axis=0), world.max(axis=0)
        bboxes.append((lo, hi))
        if role.get("kind") == "floor":
            floors.append((lo, hi))
        if role.get("kind") == "wall":
            walls.append((lo, hi))
    if not bboxes or not floors or not walls:
        raise ContractError("official finite floor/wall/objects must exist in full map")
    all_lo = np.minimum.reduce([p[0] for p in bboxes])
    all_hi = np.maximum.reduce([p[1] for p in bboxes])
    extent_lo = np.floor((all_lo - margin_m) / resolution) * resolution
    extent_hi = np.ceil((all_hi + margin_m) / resolution) * resolution
    dims = np.maximum(1, np.rint((extent_hi - extent_lo) / resolution).astype(int))
    if int(np.prod(dims,dtype=object)) > max_voxels:
        raise ContractError("actual full scene exceeds nav 10cm voxel resource budget")
    # At least one source floor must contribute finite, nondegenerate XY area.
    # This is a declared oracle free-region approximation, never sensor evidence.
    floor_top = min(p[1][2] for p in floors)
    wall_top = max(p[1][2] for p in walls)
    if not np.isfinite([floor_top, wall_top]).all() or wall_top <= floor_top+.25:
        raise ContractError("floor/wall source geometry has no usable room height")
    regions = []
    for lo,hi in floors:
        lower = [float(lo[0]), float(lo[1]), float(floor_top+.1)]
        upper = [float(hi[0]), float(hi[1]), float(wall_top)]
        if all(b>a for a,b in zip(lower,upper)):
            regions.append({"type":"box", "min":lower, "max":upper})
    if not regions:
        raise ContractError("no finite official floor projected free-space support")
    known = {
        "schema": "nav_sg_known_region_v1",
        "provenance": "NOT CERTIFIED: TEST_ONLY per-episode source floor XY "
                      "extrusion to source wall height; may include enclosed solids",
        "regions": regions,
    }
    report = {
        "schema": SCHEMA,
        "grid": {"dims": dims.tolist(), "origin": extent_lo.tolist(),
                 "resolution": float(resolution)},
        "known_region": known,
        "bounding_geometry_count": len(bboxes),
        "original_floor_geom_count": len(floors),
        "original_wall_geom_count": len(walls),
        "voxel_count": int(np.prod(dims)),
        "known_free_space_is_test_only": True,
        "training_ready": False,
    }
    return report


def build(model_xml, original_states, native_metadata, output, *,
          asset_roots=("/mnt/data1/data_v2_0617/robocasa_repo",
                       "/mnt/data1/data_v2_0617/robosuite_repo")):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ContractError("grid plan output already exists")
    model, _ = load_model(model_xml, asset_roots)
    data, state = apply_state(model, original_states, 0, "mujoco_fullphysics")
    source = json.loads(Path(native_metadata).read_text(encoding="utf-8"))
    report = grid_from_source(model, data, source)
    report["scene_id"] = source["scene_id"]
    report["frame_zero_source_row_sha256"] = state["row_sha256"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    for name, value in (("grid_plan.json", report),
                        ("known_region.json", report["known_region"])):
        with (output / name).open("x",encoding="utf-8") as f:
            json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)
            f.write("\n")
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-xml",required=True)
    p.add_argument("--states",required=True)
    p.add_argument("--metadata",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args(argv)
    report=build(args.model_xml,args.states,args.metadata,args.output)
    print(json.dumps({"scene_id":report["scene_id"],"grid":report["grid"],
                      "known_free_space_is_test_only":True},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
