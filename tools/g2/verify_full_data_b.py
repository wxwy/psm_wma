"""Independent DATA_B full-corpus audit: 9,126 episodes, safe mmap + SHA.

Checks every saved episode file/complete receipt against immutable G1 row counts,
source binding and source-base recipe; no simulation, producer or GPU needed.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import torch

from g2.data.episode_state import digest, episode_path, json_load, require_regular
from g2.data.pose5 import Pose5Recipe


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-b-root", type=Path, required=True)
    p.add_argument("--g1-verified-index", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    root = args.data_b_root
    manifest = root / "manifest.json"
    require_regular(manifest)
    complete = root / "CORPUS_COMPLETE.json"
    require_regular(complete)
    body = json_load(manifest)
    marker = json_load(complete)
    receipt = json_load(args.g1_verified_index / "receipt.json")
    recipe = Pose5Recipe().recipe_id
    if (
        marker.get("schema") != "g2_data_b_corpus_complete_v1"
        or marker.get("complete") is not True
        or marker.get("training_ready") is not False
        or marker.get("manifest_sha256") != digest(manifest)
        or marker.get("recipe_id") != recipe
        or body["pose5_recipe_id"] != recipe
        or body["source_binding_digest"] != receipt["source_binding_digest"]
        or body.get("training_ready") is not False
    ):
        raise RuntimeError("DATA_B corpus/recipe/receipt changed")
    binds = {(r["task_class"], r["episode_index"]): r for r in receipt["bindings"]}
    if len(binds) != 9126 or len(body["episodes"]) != len(binds):
        raise RuntimeError("DATA_B full 9126 completeness mismatch")
    if sum(e["frames"] for e in body["episodes"]) != receipt["absolute_row_count"]:
        raise RuntimeError("DATA_B original source frame total mismatch")
    keys = set()
    stats = defaultdict(lambda: {"episodes": 0, "original_frames": 0})
    for counter, entry in enumerate(body["episodes"], 1):
        task, ep = entry["task_class"], entry["episode_index"]
        key = task, ep
        if key in keys or key not in binds:
            raise RuntimeError("duplicate/unknown source episode")
        keys.add(key)
        row = binds[key]
        if (
            entry["frames"] != row["length"]
            or row["window_count"] != row["length"] - 16
        ):
            raise RuntimeError("DATA_B/G1 source episode length or horizon differs")
        folder = episode_path(root, task, ep)
        pt = folder / "state15.pt"
        done = folder / "COMPLETE.json"
        require_regular(pt)
        require_regular(done)
        ch = json_load(done)
        if (
            ch["complete"] is not True
            or ch["state15_sha256"] != entry["sha256"]
            or ch["state15_sha256"] != digest(pt)
            or ch["source_binding_digest"] != receipt["source_binding_digest"]
            or ch["recipe_id"] != recipe
            or ch["frame_count"] != row["length"]
            or ch["task_class"] != task
            or ch["episode_index"] != ep
        ):
            raise RuntimeError("DATA_B episode source/sha/receipt mismatch")
        content = torch.load(pt, map_location="cpu", weights_only=True, mmap=True)
        state = content["state15"]
        meta = content["metadata"]
        if (
            state.shape != (row["length"], 15)
            or state.dtype != torch.float32
            or not bool(torch.isfinite(state).all())
            or meta["source_range"]
            != [row["dataset_from_index"], row["dataset_to_index"]]
            or meta["source_binding_digest"] != receipt["source_binding_digest"]
            or meta["recipe_id"] != recipe
        ):
            raise RuntimeError("DATA_B tensor/meta source mismatch")
        stats[task]["episodes"] += 1
        stats[task]["original_frames"] += row["length"]
        if counter % 1000 == 0:
            print("DATA_B_AUDIT_PROGRESS", counter, "/", len(binds), flush=True)
    if keys != set(binds):
        raise RuntimeError("DATA_B missing verified G1 source episodes")
    report = {
        "schema": "g2_data_b_independent_full_corpus_audit_v1",
        "status": "PASS_FULL_DATA_B_CORPUS",
        "training_ready": False,
        "episodes": len(keys),
        "state15_frames": receipt["absolute_row_count"],
        "state15_dim": 15,
        "dtype": "float32",
        "tasks": dict(sorted(stats.items())),
        "recipe_id": recipe,
        "g1_source_binding_digest": receipt["source_binding_digest"],
        "manifest_sha256": digest(manifest),
        "audit_scope": "all 9126 owned episode SHA/metadata/mmap tensor finite+shape, G1 original row mapping; no actual trainer or scene preview",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(
        "DATA_B_INDEPENDENT_ALL_PASS",
        report["episodes"],
        "frames",
        report["state15_frames"],
        "tasks",
        len(report["tasks"]),
        flush=True,
    )


if __name__ == "__main__":
    main()
