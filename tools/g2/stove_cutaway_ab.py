#!/usr/bin/env python3
"""Isolated, read-only RoboCasa G2 stove overhead-occlusion diagnostic.

Draws matched source-MuJoCo Visual Geom orthographic top-down crops from
four fixed, source-backed episodes. Both panels share identical camera,
material samples, pixel grid and G2 exact GPU raster. The ONLY A/B change is
excluding visual Geoms whose entire world-space bounding box is above the
stove's top surface + a configurable vertical margin.

These are DIAGNOSTIC patches, not published G2 views and not SG/training data.
No source, model asset, production PNG, SG, work, or V3 file is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import tempfile

DEFAULT_PLAN = Path(
    "/mnt/data1/data_v2_0617/robocasa365_v3_flat/.g2_atomic_9126_plan_20261113"
)
DEFAULT_EPISODES = (2104, 2119, 2103, 2101)  # Layout 2, 4, 7, 9.


def find_episode(plan: Path, episode_id: int) -> dict:
    batch = plan / f"batch_{episode_id // 100:03}.json"
    records = json.loads(batch.read_text(encoding="utf-8"))["episodes"]
    matches = [record for record in records if record["episode_id"] == episode_id]
    if len(matches) != 1:
        raise RuntimeError(f"Episode {episode_id} is not uniquely in the immutable plan")
    return matches[0]


def render_episode(row: dict, out: Path, *, gpu: int, margin: float, padding: float) -> dict:
    import mujoco
    import numpy as np
    from PIL import Image
    from g2.offline.atomic_6views_source import DEFAULT_ASSET_ROOTS, rebind_xml
    from g2.sim.source_geometry import effective_rgba, load_model
    from g2.sim.prescan import geom_surface_mesh, geometry_type_names, analytic_surface
    from g2.sim.material_resolver import MaterialResolver
    from g2.views.exact_compute import get_engine

    raw = row["original"]
    model_path = Path(raw["model.xml.gz"]).resolve(strict=True)
    states_path = Path(raw["states.npz"]).resolve(strict=True)
    if not out.parent.is_dir():
        raise RuntimeError("A/B output parent was not prepared")
    with tempfile.TemporaryDirectory(prefix="g2_stove_source_") as tmp:
        rebased = Path(tmp) / "scene_rebased.xml"
        rebased.write_bytes(rebind_xml(model_path)[0])
        model, _ = load_model(rebased, DEFAULT_ASSET_ROOTS)
        with np.load(states_path, allow_pickle=False) as archive:
            initial = np.asarray(archive["states"][0], dtype=np.float64)
        need = mujoco.mj_stateSize(model, mujoco.mjtState.mjSTATE_FULLPHYSICS)
        if len(initial) != need:
            raise RuntimeError("Original state width does not match the source model")
        data = mujoco.MjData(model)
        mujoco.mj_setState(model, data, initial, mujoco.mjtState.mjSTATE_FULLPHYSICS)
        mujoco.mj_forward(model, data)

        names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g) or f"geom_{g}"
                 for g in range(model.ngeom)]
        kinds = geometry_type_names()

        def geom_mesh(g):
            kind = kinds.get(int(model.geom_type[g]))
            if kind not in {"box", "sphere", "ellipsoid", "capsule", "cylinder", "mesh"}:
                return None
            vertices, faces = geom_surface_mesh(model, g, kind)
            if not len(vertices) or not len(faces):
                return None
            vertices = np.asarray(vertices, dtype=np.float64)
            faces = np.asarray(faces, dtype=np.int32)
            world = vertices @ np.asarray(data.geom_xmat[g]).reshape(3, 3).T + data.geom_xpos[g]
            return kind, vertices, faces, world, world.min(axis=0), world.max(axis=0)

        # The name prefix selects an A/B *target crop* only; it does not decide
        # which surfaces are removed from the cutaway. That is purely geometry.
        stove_ids = [g for g, name in enumerate(names)
                     if name.startswith("stovetop_main_group_")
                     and model.geom_group[g] == 1
                     and int(model.geom_type[g]) == int(mujoco.mjtGeom.mjGEOM_MESH)
                     and float(effective_rgba(model, g)[3]) > 0.999]
        if not stove_ids:
            raise RuntimeError(f"Episode {row['episode_id']} has no source visual stovetop mesh")
        stove_parts = {g: geom_mesh(g) for g in stove_ids}
        stove_parts = {g: value for g, value in stove_parts.items() if value is not None}
        crop_lo = np.min([m[4] for m in stove_parts.values()], axis=0)
        crop_hi = np.max([m[5] for m in stove_parts.values()], axis=0)
        worktop_top_z = float(crop_hi[2])
        cut_height = worktop_top_z + margin
        # Full and cutaway share EXACTLY the same output crop and depth range.
        xmin, ymin = crop_lo[:2] - padding
        xmax, ymax = crop_hi[:2] + padding
        selected = {}
        removed = []
        for g, name in enumerate(names):
            if (model.geom_group[g] != 1
                    or name.startswith(("robot0_", "mobilebase0_", "gripper0_"))
                    or float(effective_rgba(model, g)[3]) < 1 - 1e-7):
                continue  # Opaque Visual Geoms only; both A/B use this rule.
            radius = float(model.geom_rbound[g])
            center = np.asarray(data.geom_xpos[g], dtype=float)
            if radius > 0 and np.isfinite(radius):
                if (center[0] + radius < xmin or center[0] - radius > xmax
                        or center[1] + radius < ymin or center[1] - radius > ymax):
                    continue
            entry = geom_mesh(g)
            if entry is None:
                continue
            kind, vertices, faces, world, lo, hi = entry
            if hi[0] < xmin or lo[0] > xmax or hi[1] < ymin or lo[1] > ymax:
                continue
            selected[g] = entry
            if lo[2] > cut_height:
                removed.append(g)
        if not selected:
            raise RuntimeError("No visual meshes intersect the crop")
        # The original source has several structural backing planes; keep
        # them in both A/B unless they are wholly above the cut plane.
        depth_lo = min(float(v[4][2]) for v in selected.values()) - 0.01
        depth_hi = max(float(v[5][2]) for v in selected.values()) + 0.01
        bounds_lo = np.array([xmin, ymin, depth_lo], dtype=float)
        bounds_hi = np.array([xmax, ymax, depth_hi], dtype=float)
        resolver = MaterialResolver(model, source_sha256=None, lazy_texel_decode=True)
        outputs = []
        info = {}
        for mode in ("original", "cutaway"):
            retained = [g for g in selected if mode == "original" or g not in removed]
            triangles = [(g, selected[g][3], selected[g][2]) for g in retained]
            if not triangles:
                raise RuntimeError(f"All source geometry was removed in {mode}")
            # Returns original source-Geom and source-face identities per hit.
            hits = get_engine().draw_hits(triangles, set(retained),
                                          bounds_lo, bounds_hi, "floor_top", 0.01)
            geometry, depth, owner, (width, height), metrics, face_ids, weights, ambiguous = hits
            rgb = np.full((height, width, 3), 255, dtype=np.uint8)
            invalid_count = 0
            for g in sorted(set(owner[geometry].tolist())):
                kind, local, faces, _, _, _ = selected[g]
                keep = geometry & (owner == g)
                source_faces = face_ids[keep]
                bary = weights[keep]
                points = np.einsum("bi,bij->bj", bary, local[faces[source_faces]])
                if kind != "mesh":
                    points = analytic_surface(points, kind, model.geom_size[g], source_faces)
                sample = resolver.sample(g, kind, source_faces, bary, local_points=points)
                color = np.rint(np.clip(sample.rgb_compat, 0, 1) * 255).astype(np.uint8)
                if np.any(~sample.color_valid):
                    invalid_count += int(np.count_nonzero(~sample.color_valid))
                    color[~sample.color_valid] = (210, 64, 210)
                rgb[keep] = color
            image_path = out / f"{mode}.png"
            Image.fromarray(rgb).save(image_path)
            visible_ids, visible_counts = np.unique(owner[geometry], return_counts=True)
            visibility = {names[int(g)]: int(n) for g, n in zip(visible_ids, visible_counts)}
            info[mode] = {
                "visible_by_geom": visibility,
                "pixels_stovetop": sum(v for k, v in visibility.items()
                                       if k.startswith("stovetop_main_group_")),
                "pixels_knobs": sum(v for k, v in visibility.items()
                                    if k.startswith("stovetop_main_group_") and "knob" in k),
                "pixels_overhead": sum(v for k, v in visibility.items()
                                       if k.startswith("hood_")),
                "invalid_color_pixels": invalid_count,
                "dimensions_wh": [width, height],
                "geometry_pixels": int(geometry.sum()),
                "render_metrics": {k: v for k, v in metrics.items()
                                   if isinstance(v, (int, float, str, bool))},
            }
            outputs.append(rgb)
        assert outputs[0].shape == outputs[1].shape
        h, w, _ = outputs[0].shape
        comparison = np.full((h, 2 * w + 8, 3), 237, dtype=np.uint8)
        comparison[:, :w] = outputs[0]
        comparison[:, w + 8:] = outputs[1]
        Image.fromarray(comparison).save(out / "comparison.png")
        return {
            "episode_id": row["episode_id"], "task_class": row["task_class"],
            "layout_id": row["layout_id"], "source_xml_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
            "source_state_row_sha256": hashlib.sha256(initial.tobytes()).hexdigest(),
            "gpu": gpu, "meters_per_pixel": 0.01,
            "cut_rule": "remove entire opaque visual geom if min(world_Z) > source_stovetop_max_Z + margin",
            "stove_top_z_m": worktop_top_z, "vertical_margin_m": margin,
            "cut_height_m": cut_height, "crop_padding_m": padding,
            "removed_visual_geoms": [names[g] for g in removed],
            "total_source_visual_geoms_in_crop": len(selected),
            "original": info["original"], "cutaway": info["cutaway"],
            "scene_graph_modified": False, "original_assets_modified": False,
            "production_output_modified": False, "comparison_type": "source-visual-geometry-diagnostic-not-published-F27",
        }


def write_index(output: Path, results: list[dict], errors: list[dict]) -> None:
    parts = ["<!doctype html><html lang='zh-CN'><meta charset='utf-8'>",
             "<meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>G2 Stove Cutaway A/B</title>",
             "<style>body{font:15px system-ui;background:#f4f6f8;color:#253243;margin:2rem auto;padding:0 1rem;max-width:1350px}h2{margin-top:2rem}.panel{background:white;padding:1.2rem;border-radius:12px;margin-bottom:1rem;box-shadow:0 2px 10px #0001}img{width:100%;height:auto;image-rendering:auto}.stats{display:flex;flex-wrap:wrap;gap:1rem}code{font-size:.9em}summary{cursor:pointer}</style>",
             "<h1>G2 炉灶俯视剖切 A/B（独立诊断）</h1>",
             "<p>两侧均由原始 MuJoCo Visual Mesh + 原始材质在同一 1 cm/pixel 正交俯视相机中重渲染。左：完整遮挡；右：仅移除整体位于灶面上方阈值之上的 Visual Geom。"
             "没有改动原始模型、正式六视图、SG 或生产任务。这不是正式 F27 全屋输出的数值等价复验。</p>"]
    for item in results:
        ep = item["episode_id"]
        a, b = item["original"], item["cutaway"]
        removed = ", ".join(item["removed_visual_geoms"][:20])
        parts += [f"<section class='panel'><h2>Layout {item['layout_id']} · EP {ep:06d}</h2>",
                  f"<div class='stats'><span>阈值：{item['cut_height_m']:.2f}m</span><span>灶面像素：{a['pixels_stovetop']} → {b['pixels_stovetop']}</span>",
                  f"<span>高位遮挡像素：{a['pixels_overhead']} → {b['pixels_overhead']}</span>",
                  f"<span>已排除 Visual Geom 数：{len(item['removed_visual_geoms'])}</span></div>",
                  f"<p>左：原版 &nbsp; &nbsp; 右：几何剖切版</p><img loading='lazy' src='ep_{ep:06d}/comparison.png' alt='Source Visual Geometry A/B'>",
                  f"<details><summary>剖切列表及原始记录</summary><p><code>{html.escape(removed)}</code></p><a href='ep_{ep:06d}/report.json'>report.json</a></details>"]
        if item.get("published_floor_top_relative_path"):
            path = html.escape(item["published_floor_top_relative_path"], quote=True)
            parts += [f"<details><summary>正式生产原版 Floor Top（上下文参考）</summary><img loading='lazy' src='{path}'></details>"]
        parts.append("</section>")
    if errors:
        parts += ["<h2>失败项（未掩盖）</h2><pre>", html.escape(json.dumps(errors,ensure_ascii=False,indent=2)),"</pre>"]
    parts.append("</html>")
    (output / "index.html").write_text("\n".join(parts), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--episodes", type=int, nargs="+", default=DEFAULT_EPISODES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gpu", type=int, required=True,
                        help="One explicitly selected GPU; do not occupy another task's exclusive card")
    parser.add_argument("--vertical-margin-m", type=float, default=0.25)
    parser.add_argument("--padding-m", type=float, default=0.18)
    args = parser.parse_args()
    if not (0.05 <= args.vertical_margin_m <= 0.8 and 0.05 <= args.padding_m <= 0.5):
        parser.error("vertical margin or padding outside safe diagnostic bounds")
    if not (len(args.episodes) <= 16 and len(set(args.episodes)) == len(args.episodes)):
        parser.error("up to 16 distinct episodes per diagnostic run")
    output = args.output.expanduser().absolute()
    if output.exists() or output.is_symlink():
        parser.error(f"output must not exist; refusing overwrite: {output}")
    for forbidden in (Path.cwd(), args.plan.resolve(strict=True),
                      Path("/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views")):
        if output == forbidden or output in forbidden.parents or forbidden in output.parents:
            parser.error("output overlaps source, plan, working checkout or formal production data")
    os.environ["MUJOCO_GL"] = "egl"
    os.environ["PYOPENGL_PLATFORM"] = "egl"
    os.environ["MUJOCO_EGL_DEVICE_ID"] = str(args.gpu)
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    output.mkdir(parents=True)
    results, errors = [], []
    for episode_id in args.episodes:
        ep_dir = output / f"ep_{episode_id:06d}"
        ep_dir.mkdir()
        try:
            row = find_episode(args.plan, episode_id)
            record = render_episode(row, ep_dir, gpu=args.gpu,
                                    margin=args.vertical_margin_m,
                                    padding=args.padding_m)
            published = (Path("/mnt/data1/data_v2_0617/robocasa365_v3_flat/")
                         / "robocasa365-target-atomic-6views" / "tasks"
                         / row["task_class"] / "episodes" / f"episode_{episode_id:06d}"
                         / "state_000000_frame_000000" / "sixview" / "floor_top.png")
            if published.is_file() and not published.is_symlink():
                record["published_floor_top_relative_path"] = os.path.relpath(
                    published, start=output)
            (ep_dir / "report.json").write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            results.append(record)
            print("CUTAWAY_EP_PASS", episode_id, "layout", record["layout_id"],
                  "stove_pixels", record["original"]["pixels_stovetop"],
                  "->", record["cutaway"]["pixels_stovetop"], flush=True)
        except Exception as exc:
            errors.append({"episode_id":episode_id,"error":str(exc),"type":type(exc).__name__})
            print("CUTAWAY_EP_FAILED", episode_id, type(exc).__name__, str(exc), flush=True)
    write_index(output, results, errors)
    (output / "summary.json").write_text(json.dumps(
        {"schema":"g2_stove_cutaway_ab_diagnostic_v1", "attempted":len(args.episodes),
         "passed":len(results), "errors":errors, "results":results},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        from g2.views.exact_compute import close_engine
        close_engine()
    except Exception:
        pass
    print("CUTAWAY_PREVIEW",output / "index.html",flush=True)
    return 0 if not errors and len(results) == len(args.episodes) else 2


if __name__ == "__main__":
    raise SystemExit(main())
