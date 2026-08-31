#!/usr/bin/env python3
"""Build the CPU-only, ordered LIBERO window stream for R09-B2 P1."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Iterator
from pathlib import Path

import torch

from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset


SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parquet_index_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((root / "data").glob("chunk-*/file-*.parquet")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(sha256(path).encode())
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def shuffled_indices(dataset: LIBEROLeRobotDataset, seed: int) -> Iterator[tuple[int, int]]:
    blocks = dataset.get_shuffle_blocks()
    epoch = 0
    while True:
        generator = torch.Generator().manual_seed(seed + epoch)
        for block in torch.randperm(len(blocks), generator=generator).tolist():
            start, length = blocks[block]
            for index in range(start, start + length):
                yield epoch, index
        epoch += 1


def identity(dataset: LIBEROLeRobotDataset, index: int) -> tuple[int, int, int]:
    import numpy as np

    episode_slot = int(np.searchsorted(dataset._valid_cum, index, side="right"))
    previous = int(dataset._valid_cum[episode_slot - 1]) if episode_slot else 0
    start = int(dataset._ep_starts[episode_slot]) + (index - previous)
    return int(dataset._row_task[start]), int(dataset._ep_vals[episode_slot]), start - int(dataset._ep_starts[episode_slot])


def reverse_index(dataset: LIBEROLeRobotDataset, episode_index: int, start_frame: int) -> int:
    matches = (dataset._ep_vals == episode_index).nonzero()[0]
    if len(matches) != 1:
        raise ValueError(f"episode_index={episode_index} is not unique in selected dataset")
    slot = int(matches[0])
    previous = int(dataset._valid_cum[slot - 1]) if slot else 0
    index = previous + start_frame
    if index < previous or index >= int(dataset._valid_cum[slot]):
        raise ValueError(f"episode={episode_index} start_frame={start_frame} is outside valid windows")
    return index


def cache_exists(cache_root: Path, episode_index: int, start_frame: int) -> bool:
    episode_path = cache_root / "episodes" / f"episode_{episode_index:06d}.pt"
    if not episode_path.is_file():
        return False
    item = torch.load(episode_path, map_location="cpu", weights_only=True)
    return isinstance(item.get("windows", {}).get(str(start_frame)), dict)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--libero-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--optimizer-updates", type=int, default=100)
    parser.add_argument("--grad-accum", type=int, required=True)
    parser.add_argument("--max-samples-per-batch", type=int, required=True)
    parser.add_argument("--shuffle-seed", type=int, default=42)
    args = parser.parse_args()
    if min(args.optimizer_updates, args.grad_accum, args.max_samples_per_batch) <= 0:
        raise ValueError("optimizer-updates, grad-accum and max-samples-per-batch must be positive")

    root, libero_root, cache_root = args.root.resolve(), args.libero_root.resolve(), args.cache_root.resolve()
    datasets = {
        suite: LIBEROLeRobotDataset(
            root=str(libero_root / suite), fps=20, chunk_length=16, image_size=256,
            camera_mode="concat_view", split="train", val_ratio=0.01, seed=0,
            latent_cache_root=str(cache_root / suite), latent_cache_verify_ratio=0.0,
        )
        for suite in SUITES
    }
    streams = {suite: shuffled_indices(dataset, args.shuffle_seed) for suite, dataset in datasets.items()}
    total_microbatches = args.optimizer_updates * args.grad_accum
    expected_count = total_microbatches * args.max_samples_per_batch
    records: list[dict[str, int | str]] = []
    for microbatch in range(total_microbatches):
        suite = SUITES[microbatch % len(SUITES)]
        dataset = datasets[suite]
        for sample_in_microbatch in range(args.max_samples_per_batch):
            epoch, flat_index = next(streams[suite])
            task_index, episode_index, start_frame = identity(dataset, flat_index)
            if reverse_index(dataset, episode_index, start_frame) != flat_index:
                raise ValueError(f"non-bijective flat index for {suite} index={flat_index}")
            if not cache_exists(cache_root / suite, episode_index, start_frame):
                raise FileNotFoundError(f"missing cache window {suite}/{episode_index}/{start_frame}")
            records.append({"ordinal": len(records), "epoch": epoch, "optimizer_update": microbatch // args.grad_accum,
                            "microbatch": microbatch, "sample_in_microbatch": sample_in_microbatch,
                            "suite": suite, "task_index": task_index, "episode_index": episode_index,
                            "start_frame": start_frame, "dataset_flat_index": flat_index})
    if len(records) != expected_count:
        raise AssertionError(f"record count mismatch expected={expected_count}, actual={len(records)}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    records_path = args.output_dir / "records.jsonl"
    records_path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")
    suite_records_dir = args.output_dir / "suites"
    suite_records_dir.mkdir(exist_ok=True)
    suite_record_sha256 = {}
    for suite in SUITES:
        suite_path = suite_records_dir / f"{suite}.jsonl"
        suite_path.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records if record["suite"] == suite),
            encoding="utf-8",
        )
        suite_record_sha256[suite] = sha256(suite_path)
    header = {"schema_version": "r09_b2_stream_manifest_v1", "record_count": len(records),
              "records_sha256": sha256(records_path), "suite_order": list(SUITES), "shuffle_seed": args.shuffle_seed,
              "world_size": 1, "num_workers": 0, "optimizer_updates": args.optimizer_updates,
              "grad_accum": args.grad_accum, "max_samples_per_batch": args.max_samples_per_batch,
              "source": {"root_revision": git(root, "rev-parse", "HEAD"),
                         "submodule_revision": git(root / "cosmos-framework", "rev-parse", "HEAD"),
                         "gitlink_revision": git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2]},
              "files": {"builder_sha256": sha256(Path(__file__).resolve()),
                        "verifier_sha256": sha256(Path(__file__).with_name("verify_r09_b2_stream_manifest.py")),
                        "dataset_source_sha256": sha256(root / "cosmos-framework/cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py"),
                        "wrapper_source_sha256": sha256(root / "cosmos-framework/cosmos_framework/data/generator/action/datasets/action_sft_dataset.py"),
                        "recipe_toml_sha256": sha256(root / "cosmos-framework/examples/toml/sft_config/action_policy_libero_edge_all.toml"),
                        "dataset_info_sha256": {suite: sha256(libero_root / suite / "meta/info.json") for suite in SUITES},
                        "dataset_parquet_index_sha256": {suite: parquet_index_sha256(libero_root / suite) for suite in SUITES},
                        "cache_manifests": {suite: sha256(cache_root / suite / "dataset_manifest.json") for suite in SUITES},
                        "suite_record_sha256": suite_record_sha256}}
    (args.output_dir / "header.json").write_text(json.dumps(header, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "record_count": len(records), "records_sha256": header["records_sha256"]}))


if __name__ == "__main__":
    main()
