"""Read-only F27 baseline vs opt-in P0+P1 and v2 indexed package evidence.

Production-safe: no mutation of source, base output, candidate, or dataset.
Numerical and pixel quality differences are counted, never silently ignored.
"""

from __future__ import annotations

import collections
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from g2.offline.scene_view_event_index import resolve_indexed_png
from g2.offline.scene_view_index_package import validate_indexed_episode


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare(base, candidate, package):
    base = Path(base).resolve(strict=True)
    cand = Path(candidate).resolve(strict=True)
    pkg = Path(package).resolve(strict=True)
    a = json.loads((base / "episode_receipt.json").read_text())
    b = json.loads((cand / "episode_receipt.json").read_text())
    doc = json.loads((pkg / "episode_manifest.json").read_text())
    original = json.loads((pkg / "COMPLETE.json").read_text())
    assert validate_indexed_episode(pkg) == len(doc["states"])
    assert a["complete"] and b["complete"] and doc["complete"] and original["complete"]
    assert a["spatial_state_count"] == b["spatial_state_count"] == doc["state_count"]
    assert a["source_inputs_sha256"] == b["source_inputs_sha256"]
    assert (
        a["robot_pose_marker_appearance_sha256"]
        == b["robot_pose_marker_appearance_sha256"]
    )
    counts = collections.Counter()
    by_direction = collections.Counter()
    mismatches = []
    for i, row in enumerate(doc["states"]):
        source = base / f"state_{i:06d}_frame_{row['frame']:06d}"
        cand_state = cand / f"state_{i:06d}_frame_{row['frame']:06d}"
        source_dc = json.loads((source / "direct_color_views.json").read_text())
        cand_dc = json.loads((cand_state / "direct_color_views.json").read_text())
        assert (
            source_dc["scene_id"] == cand_dc["scene_id"]
            and source_dc["frame_id"] == cand_dc["frame_id"]
        )
        assert (
            len(source_dc["views"])
            == len(cand_dc["views"])
            == a["states"][i]["view_count"]
        )
        assert b["states"][i]["scene_event_mode"] == row["update_mode"]
        if b.get("sim_direct_material") is True:
            assert b.get("native_color_voxel_stage_removed") is True
            assert b["states"][i]["native_color_sha256"] is None
            assert isinstance(b["states"][i]["direct_material_state_sha256"], str)
            assert len(b["states"][i]["direct_material_state_sha256"]) == 64
        else:
            assert (
                b["states"][i]["native_color_sha256"]
                == a["states"][i]["native_color_sha256"]
            )
        assert b["states"][i]["scene_keyframe_state"] == row["scene_keyframe_state"]
        assert b["states"][i]["frame"] == row["frame"]
        with gzip.open(
            pkg / f"state_{i:06d}_frame_{row['frame']:06d}" / row["scene_graph"], "rb"
        ) as f:
            sg = f.read()
        assert hashlib.sha256(sg).hexdigest() == _sha(source / "scene_graph.json")
        assert hashlib.sha256(sg).hexdigest() == _sha(cand_state / "scene_graph.json")
        counts["sg_current_frame_equal"] += 1
        for view in source_dc["views"]:
            rel = view["rgb_file"]
            original_img = source / rel
            cached_img = resolve_indexed_png(doc["states"], i, rel, pkg)
            assert original_img.is_file() and cached_img.is_file()
            counts["images_compared"] += 1
            if rel in row["view_refs"]:
                counts["ref_view_pairs"] += 1
            else:
                counts["materialized_image_pairs"] += 1
            if _sha(original_img) == _sha(cached_img):
                counts["png_exact"] += 1
                continue
            a_px = np.asarray(Image.open(original_img).convert("RGB"))
            b_px = np.asarray(Image.open(cached_img).convert("RGB"))
            if a_px.shape != b_px.shape:
                raise AssertionError(f"image dimensions changed state={i} view={rel}")
            pixels = int(np.count_nonzero(np.any(a_px != b_px, axis=2)))
            total = a_px.shape[0] * a_px.shape[1]
            counts["png_different"] += 1
            counts["pixels_different"] += pixels
            counts["pixels_compared"] += total
            by_direction[rel] += pixels
            mismatches.append(
                dict(
                    state=i,
                    frame=row["frame"],
                    view=rel,
                    mode=row["update_mode"],
                    pixels=pixels,
                    image_pixels=total,
                    percentage=round(100 * pixels / total, 6),
                )
            )
    for i, row in enumerate(doc["states"]):
        if row["update_mode"] != "FULL":
            continue
        state = f"state_{i:06d}_frame_{row['frame']:06d}"
        aa = base / state / "g2_original_gpu"
        bb = cand / state / "g2_original_gpu"
        files = sorted(aa.rglob("geometry.npz"))
        assert files
        for src in files:
            rel = src.relative_to(aa)
            with np.load(src) as left, np.load(bb / rel) as right:
                assert set(left.files) == set(right.files)
                for key in left.files:
                    assert np.array_equal(left[key], right[key], equal_nan=True), (
                        i,
                        str(rel),
                        key,
                    )
                    counts["full_keyframe_npz_arrays_exact"] += 1
    return {
        "baseline_f27_s": a["actual_wall_s"],
        "optimized_f27_s": b["actual_wall_s"],
        "f27_speedup": round(a["actual_wall_s"] / b["actual_wall_s"], 4),
        "baseline_states": a["spatial_state_count"],
        "optimized_full_states": b["scene_full_render_states"],
        "optimized_arrow_only": b["scene_arrow_only_states"],
        "optimized_reuse_all": b["scene_reuse_all_states"],
        "counts": dict(counts),
        "mismatch_by_view": dict(by_direction),
        "largest_mismatches": sorted(mismatches, key=lambda z: -z["pixels"])[:20],
    }


def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--optimized", type=Path, required=True)
    p.add_argument("--package", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    opts = p.parse_args()
    assert not opts.report.exists()
    report = compare(opts.baseline, opts.optimized, opts.package)
    opts.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        "F27_P0_P1_INDEX_A_B_SUMMARY",
        json.dumps(report, ensure_ascii=False)[:3800],
        flush=True,
    )
    print("F27_P0_P1_INDEX_A_B_COMPLETE", opts.report, flush=True)


if __name__ == "__main__":
    main()
