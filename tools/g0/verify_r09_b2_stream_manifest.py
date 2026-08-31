#!/usr/bin/env python3
"""Verify structural/provenance invariants of an R09-B2 P1 stream manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path

import torch

from build_r09_b2_stream_manifest import SUITES, identity, reverse_index
from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--header", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument("--libero-root", type=Path)
    args = parser.parse_args()
    header = json.loads(args.header.read_text())
    records = [json.loads(line) for line in args.records.read_text().splitlines() if line]
    expected_count = header.get("optimizer_updates", 0) * header.get("grad_accum", 0) * header.get("max_samples_per_batch", 0)
    suites = header.get("suite_order", [])
    required = {"ordinal", "epoch", "optimizer_update", "microbatch", "sample_in_microbatch", "suite", "task_index", "episode_index", "start_frame", "dataset_flat_index"}
    arithmetic = all(
        set(record) == required
        and record["optimizer_update"] == record["microbatch"] // header["grad_accum"]
        and record["sample_in_microbatch"] == record["ordinal"] % header["max_samples_per_batch"]
        and record["microbatch"] == record["ordinal"] // header["max_samples_per_batch"]
        and record["suite"] == suites[record["microbatch"] % len(suites)]
        for record in records
    )
    cache_ok = True
    if args.cache_root is not None:
        cache_items: OrderedDict[tuple[str, int], dict] = OrderedDict()
        for record in records:
            key = (record["suite"], record["episode_index"])
            item = cache_items.get(key)
            if item is None:
                path = args.cache_root / record["suite"] / "episodes" / f"episode_{record['episode_index']:06d}.pt"
                if not path.is_file():
                    cache_ok = False
                    break
                item = torch.load(path, map_location="cpu", weights_only=True)
                cache_items[key] = item
                if len(cache_items) > 8:
                    cache_items.popitem(last=False)
            if not isinstance(item.get("windows", {}).get(str(record["start_frame"])), dict):
                cache_ok = False
                break
    index_ok = True
    if args.libero_root is not None:
        datasets = {
            suite: LIBEROLeRobotDataset(root=str(args.libero_root / suite), fps=20, chunk_length=16, image_size=256,
                                        camera_mode="concat_view", split="train", val_ratio=0.01, seed=0)
            for suite in SUITES
        }
        for record in records:
            dataset = datasets[record["suite"]]
            expected = (record["task_index"], record["episode_index"], record["start_frame"])
            if identity(dataset, record["dataset_flat_index"]) != expected or reverse_index(dataset, *expected[1:]) != record["dataset_flat_index"]:
                index_ok = False
                break
    checks = {
        "schema": header.get("schema_version") == "r09_b2_stream_manifest_v1",
        "record_hash": header.get("records_sha256") == sha256(args.records),
        "record_count": len(records) == header.get("record_count") == expected_count,
        "ordinals": [record.get("ordinal") for record in records] == list(range(len(records))),
        "ordinal_unique": len({record.get("ordinal") for record in records}) == len(records),
        "record_schema_and_packer_arithmetic": arithmetic,
        "flat_index_present": all(isinstance(record.get("dataset_flat_index"), int) for record in records),
        "single_process": header.get("world_size") == 1 and header.get("num_workers") == 0,
        "source_complete": set(header.get("source", {})) == {"root_revision", "submodule_revision", "gitlink_revision"},
        "provenance_complete": {"builder_sha256", "dataset_source_sha256", "wrapper_source_sha256", "cache_manifests"} <= set(header.get("files", {})),
        "cache_window_per_record": cache_ok,
        "flat_index_bijective": index_ok,
    }
    result = {"schema_version": "r09_b2_stream_manifest_verifier_v1", "status": "PASS" if all(checks.values()) else "FAIL",
              "checks": checks, "header": str(args.header), "records": str(args.records)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
