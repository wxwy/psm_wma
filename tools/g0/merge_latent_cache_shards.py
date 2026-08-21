#!/usr/bin/env python3
"""Merge sharded exact-window latent cache manifests into the final manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    shard_paths = sorted(args.output_root.glob("dataset_manifest_shard_*.json"))
    if not shard_paths:
        raise FileNotFoundError(f"No shard manifests found in {args.output_root}")

    manifests = []
    for path in shard_paths:
        manifests.append(json.loads(path.read_text(encoding="utf-8")))

    base = manifests[0]
    all_rows = []
    for manifest in manifests:
        all_rows.extend(manifest.get("episodes", []))

    # Deduplicate by episode_index (in case of resume overlap).
    seen = {}
    for row in all_rows:
        seen[int(row["episode_index"])] = row
    rows = [seen[k] for k in sorted(seen)]

    merged = dict(base)
    merged.pop("episode_shard", None)
    merged.pop("num_shards", None)
    merged["episode_count"] = len(rows)
    merged["window_count"] = sum(int(row["window_count"]) for row in rows)
    merged["episodes"] = rows

    out_path = args.output_root / "dataset_manifest.json"
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Validate a sample of episode files exist and are finite.
    episodes_dir = args.output_root / "episodes"
    sample_rows = rows[:: max(1, len(rows) // 10)]
    for row in sample_rows:
        ep_path = Path(row["episode_path"])
        if not ep_path.is_file():
            raise FileNotFoundError(f"Missing episode file: {ep_path}")
        data = torch.load(ep_path, map_location="cpu", weights_only=True)
        for window in data["windows"].values():
            if not torch.isfinite(window["latent"]).all():
                raise FloatingPointError(f"Non-finite latent in {ep_path}")

    print(json.dumps({"output_root": str(args.output_root), "manifest": str(out_path), "episode_count": len(rows), "window_count": merged["window_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
