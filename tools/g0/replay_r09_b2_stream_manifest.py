#!/usr/bin/env python3
"""CPU-only requested-to-observed replay for an R09-B2 P1 manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from cosmos_framework.data.generator.action.datasets.action_sft_dataset import get_action_libero_sft_dataset


IDENTITY_KEYS = ("ordinal", "epoch", "suite", "task_index", "episode_index", "start_frame", "dataset_flat_index")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_replay_match(requested: list[dict], observed: list[dict]) -> bool:
    """Require exact requested order and identities; no set-wise equivalence."""
    return requested == observed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--libero-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    requested = [json.loads(line) for line in (args.manifest_root / "records.jsonl").read_text().splitlines() if line]
    suites = json.loads((args.manifest_root / "header.json").read_text())["suite_order"]
    observed = []
    for suite in suites:
        dataset = get_action_libero_sft_dataset(
            root=str(args.libero_root / suite), fps=20, chunk_length=16, image_size=256,
            camera_mode="concat_view", split="train", val_ratio=0.01, seed=0,
            latent_cache_root=str(args.cache_root / suite), latent_cache_verify_ratio=0.0,
            stream_manifest_path=str(args.manifest_root / "suites" / f"{suite}.jsonl"),
            stream_manifest_suite=suite,
        )
        for sample in dataset:
            observed.append({
                "ordinal": int(sample["b2_stream_ordinal"].item()),
                "epoch": int(sample["b2_stream_epoch"].item()),
                "suite": suite,
                "task_index": int(sample["task_index"].item()),
                "episode_index": int(sample["episode_index"].item()),
                "start_frame": int(sample["start_frame"].item()),
                "dataset_flat_index": int(sample["b2_dataset_flat_index"].item()),
            })
    observed.sort(key=lambda record: record["ordinal"])
    requested_identity = [{key: record[key] for key in IDENTITY_KEYS} for record in requested]
    passed = exact_replay_match(requested_identity, observed)
    result = {
        "schema_version": "r09_b2_stream_manifest_replay_v1",
        "status": "PASS" if passed else "FAIL",
        "requested_count": len(requested_identity),
        "observed_count": len(observed),
        "requested_sha256": sha256(args.manifest_root / "records.jsonl"),
        "requested": requested_identity,
        "observed": observed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "requested_count": len(requested_identity), "observed_count": len(observed)}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
