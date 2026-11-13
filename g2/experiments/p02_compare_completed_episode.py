"""Old v1 published Episode vs independently generated P2 v2 output.

No changes to either original dataset. Counts actual final RGB pixel differences,
per-state SG source bindings and v2 reference integrity.
"""

from pathlib import Path
import gzip
import json
import hashlib
import collections
import numpy as np
from PIL import Image
from g2.offline.scene_view_event_index import resolve_indexed_png
from g2.offline.scene_view_index_package import validate_indexed_episode


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare(baseline, candidate):
    old = Path(baseline).resolve(strict=True)
    new = Path(candidate).resolve(strict=True)
    a = json.loads((old / "episode_manifest.json").read_text())
    b = json.loads((new / "episode_manifest.json").read_text())
    assert a["schema"] == "g2_atomic_compact_6views_v1"
    assert b["schema"] == "g2_atomic_compact_6views_v2"
    assert validate_indexed_episode(new) == len(b["states"])
    assert (
        a["source_fingerprint"] == b["source_fingerprint"]
        and a["episode_id"] == b["episode_id"]
        and [x["frame"] for x in a["states"]] == [x["frame"] for x in b["states"]]
    )
    counts = collections.Counter()
    worst = []
    for i, (a_state, b_state) in enumerate(zip(a["states"], b["states"])):
        assert a_state["frame"] == b_state["frame"]
        fn = f"state_{i:06d}_frame_{a_state['frame']:06d}"
        oldroot = old / fn
        newroot = new / fn
        with gzip.open(oldroot / "scene_graph.json.gz", "rb") as f:
            oldgraph = json.loads(f.read())
        with gzip.open(newroot / "scene_graph.json.gz", "rb") as f:
            newgraph = json.loads(f.read())
        assert oldgraph["frame_id"] == newgraph["frame_id"] == a_state["frame"]
        assert oldgraph.get("source_sha256") == newgraph.get("source_sha256")
        counts["sg_frames_valid"] += 1
        if oldgraph == newgraph:
            counts["sg_content_equal"] += 1
        else:
            counts["sg_content_differs"] += 1
        all_paths = set(b_state["view_pngs"]) | set(b_state["view_refs"])
        if all_paths != set(a_state["view_pngs"]):
            counts["view_set_differs"] += 1
            continue
        for rel in a_state["view_pngs"]:
            original = oldroot / rel
            chosen = resolve_indexed_png(b["states"], i, rel, new)
            counts["compared_views"] += 1
            if rel in b_state["view_refs"]:
                counts["reused_views"] += 1
            else:
                counts["physical_views"] += 1
            if sha(original) == sha(chosen):
                counts["png_exact"] += 1
                continue
            oldpixels = np.asarray(Image.open(original).convert("RGB"))
            newpixels = np.asarray(Image.open(chosen).convert("RGB"))
            if oldpixels.shape != newpixels.shape:
                raise ValueError("different view dimensions")
            d = int(np.any(oldpixels != newpixels, axis=2).sum())
            counts["png_different"] += 1
            counts["pixel_differences"] += d
            worst.append(
                dict(
                    state=i,
                    frame=a_state["frame"],
                    path=rel,
                    pixels=d,
                    dimensions=(oldpixels.shape[1], oldpixels.shape[0]),
                )
            )
    return dict(
        counts=counts,
        worst=sorted(worst, key=lambda x: -x["pixels"])[:18],
        baseline_states=len(a["states"]),
        v2_states=len(b["states"]),
        v2_schema=b["schema"],
    )


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--optimized", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    assert not args.report.exists()
    out = compare(args.baseline, args.optimized)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(out, default=dict, sort_keys=True, indent=2) + "\n"
    )
    print(
        "P2_PUBLISHED_EPISODE_COMPARE", json.dumps(out, default=dict)[:4400], flush=True
    )
