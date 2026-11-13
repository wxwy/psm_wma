#!/usr/bin/env python3
"""Read-only original RoboCasa v2 -> independent v3 AB: exact SG/PNG equality."""

from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

from g2.offline.scene_graph_compact_v3 import (
    convert_v2_to_v3,
    resolve_scene_graph,
    validate_sg_indexed_episode,
)
from g2.offline.scene_view_event_index import resolve_indexed_png
from g2.offline.scene_view_index_package import validate_indexed_episode


def allocated_size(root):
    return sum(
        p.stat().st_blocks * 512
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink()
    )


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(ep, source_root, output_root):
    src = source_root / f"episode_{ep:06d}"
    dest = output_root / f"episode_{ep:06d}_v3"
    if dest.exists() or dest.is_symlink():
        raise RuntimeError("refusing overwrite " + str(dest))
    before = allocated_size(src)
    start = time.perf_counter()
    source_states = validate_indexed_episode(src)
    doc, stats = convert_v2_to_v3(src, dest)
    elapsed = time.perf_counter() - start
    assert validate_sg_indexed_episode(dest) == source_states
    original = json.loads((src / "episode_manifest.json").read_text())
    assert original["source_fingerprint"] == doc["source_fingerprint"]
    graph_equal = views_equal = 0
    for i, row in enumerate(original["states"]):
        folder = src / f"state_{i:06d}_frame_{row['frame']:06d}"
        with gzip.open(folder / "scene_graph.json.gz", "rt") as f:
            old = json.load(f)
        assert resolve_scene_graph(dest, i, doc) == old, ("SG mismatch", ep, i)
        graph_equal += 1
        all_views = set(row["view_pngs"]) | set(row.get("view_refs", {}))
        new_views = set(doc["states"][i]["view_pngs"]) | set(
            doc["states"][i]["view_refs"]
        )
        assert all_views == new_views
        for path in all_views:
            old_png = resolve_indexed_png(original["states"], i, path, src)
            new_png = resolve_indexed_png(doc["states"], i, path, dest)
            assert sha(old_png) == sha(new_png), ("PNG mismatch", ep, i, path)
            views_equal += 1
    after = allocated_size(dest)
    return {
        "episode_id": ep,
        "v2_states": source_states,
        "sg_exact": graph_equal,
        "views_byte_exact": views_equal,
        "v2_allocated_bytes": before,
        "v3_allocated_bytes": after,
        "saved_bytes": before - after,
        "saved_percent": round((1 - after / before) * 100, 2),
        "convert_seconds": round(elapsed, 3),
        "sg_keyframes": stats["sg_keyframes"],
        "sg_deltas": stats["sg_deltas"],
        "png_physical": stats["physical_pngs"],
        "png_refs": stats["image_refs"],
        "sg_modes": dict(
            Counter(
                "KEYFRAME" if r.get("scene_graph") else "DELTA" for r in doc["states"]
            )
        ),
        "viewer_source_mode": "source_v2_exact",
        "robot_policy": doc["robot_motion_reference_policy"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--episodes", default="211,215,217,219,222,368,380,404")
    args = ap.parse_args()
    if args.out.exists():
        raise RuntimeError("output root must not exist")
    args.out.mkdir(parents=True)
    records = []
    for ep in [int(v) for v in args.episodes.split(",")]:
        result = run(ep, args.src, args.out)
        records.append(result)
        print("P3_REAL_AB_PASS", result, flush=True)
    summary = {
        "schema": "g2_sg_v3_exact_ab_20261113",
        "episode_count": len(records),
        "total_states": sum(r["v2_states"] for r in records),
        "total_sg_exact": sum(r["sg_exact"] for r in records),
        "total_view_png_exact": sum(r["views_byte_exact"] for r in records),
        "v2_bytes": sum(r["v2_allocated_bytes"] for r in records),
        "v3_bytes": sum(r["v3_allocated_bytes"] for r in records),
        "sg_keyframes": sum(r["sg_keyframes"] for r in records),
        "sg_deltas": sum(r["sg_deltas"] for r in records),
        "physical_pngs": sum(r["png_physical"] for r in records),
        "referenced_pngs": sum(r["png_refs"] for r in records),
        "ab": records,
    }
    summary["saved_percent"] = round(
        100 * (1 - summary["v3_bytes"] / summary["v2_bytes"]), 2
    )
    (args.out / "AB_RESULT.json").write_text(json.dumps(summary, indent=2))
    print(
        "P3_REAL_COMPLETE_SG_AND_PNG_STRICT_AB_PASS",
        {k: v for k, v in summary.items() if k != "ab"},
        flush=True,
    )


if __name__ == "__main__":
    main()
