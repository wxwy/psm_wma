#!/usr/bin/env python3
"""Compare fixed-weight R07 Normal/Zero/Shuffle sensitivity captures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import torch


INVARIANT_KEYS = (
    "x0_vision",
    "xt_vision",
    "sigma_vision_schedule",
    "sigma_vision_effective",
    "x0_action",
    "xt_action",
    "sigma_action_effective",
    "text_ids",
    "text_indexes",
    "vision_indexes",
    "action_indexes",
    "split_lens",
    "attn_modes",
    "position_ids",
)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_tensors(path: Path) -> dict:
    return torch.load(path, map_location="cpu", weights_only=True)


def tensor_bytes(tensor: torch.Tensor) -> bytes:
    value = tensor.detach().contiguous().cpu()
    return value.view(torch.uint16).numpy().tobytes() if value.dtype is torch.bfloat16 else value.numpy().tobytes()


def tensor_list_hash(tensors: list[torch.Tensor | None]) -> str:
    digest = hashlib.sha256()
    for tensor in tensors:
        if tensor is None:
            digest.update(b"<none>")
        else:
            digest.update(str(tuple(tensor.shape)).encode())
            digest.update(str(tensor.dtype).encode())
            digest.update(tensor_bytes(tensor))
    return digest.hexdigest()


def difference(reference: list[torch.Tensor | None], candidate: list[torch.Tensor | None]) -> dict[str, float | int | str]:
    if len(reference) != len(candidate):
        raise ValueError(f"tensor list length mismatch: {len(reference)} != {len(candidate)}")
    square_sum = 0.0
    reference_square_sum = 0.0
    max_abs = 0.0
    changed = 0
    for left, right in zip(reference, candidate, strict=True):
        if left is None or right is None:
            if left is not right:
                changed += 1
            continue
        if left.shape != right.shape:
            raise ValueError(f"tensor shape mismatch: {tuple(left.shape)} != {tuple(right.shape)}")
        delta = left.float() - right.float()
        changed += int(bool(torch.any(delta != 0).item()))
        square_sum += float(torch.sum(delta.square()).item())
        reference_square_sum += float(torch.sum(left.float().square()).item())
        max_abs = max(max_abs, float(delta.abs().max().item()) if delta.numel() else 0.0)
    l2 = square_sum**0.5
    reference_l2 = reference_square_sum**0.5
    return {
        "sha256_reference": tensor_list_hash(reference),
        "sha256_candidate": tensor_list_hash(candidate),
        "changed_items": changed,
        "max_abs_diff": max_abs,
        "l2_diff": l2,
        "relative_l2_diff": l2 / reference_l2 if reference_l2 else l2,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for mode in ("normal", "zero", "shuffle"):
        parser.add_argument(f"--{mode}-json", type=Path, required=True)
        parser.add_argument(f"--{mode}-tensors", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    summaries = {mode: load_json(getattr(args, f"{mode}_json")) for mode in ("normal", "zero", "shuffle")}
    tensors = {mode: load_tensors(getattr(args, f"{mode}_tensors")) for mode in ("normal", "zero", "shuffle")}
    schema_pass = all(summary.get("schema_version") == "r07_no_memory_parity_v1" for summary in summaries.values())
    tensor_schema_pass = all(tensor.get("schema_version") == "r07_sensitivity_tensors_v1" for tensor in tensors.values())
    invariant_exact = {
        key: summaries["normal"].get(key) == summaries["zero"].get(key) == summaries["shuffle"].get(key)
        for key in INVARIANT_KEYS
    }
    pairs = {"normal_vs_zero": "zero", "normal_vs_shuffle": "shuffle"}
    metrics = {
        pair: {
            "local_memory": difference(tensors["normal"]["local_memory"], tensors[mode]["local_memory"]),
            "preds_vision": difference(tensors["normal"]["preds_vision"], tensors[mode]["preds_vision"]),
            "preds_action": difference(tensors["normal"]["preds_action"], tensors[mode]["preds_action"]),
        }
        for pair, mode in pairs.items()
    }
    present_local_count = sum(tensor is not None for tensor in tensors["normal"]["local_memory"])
    sensitivity_pass = all(
        metrics[pair][field]["l2_diff"] > 0.0
        for pair in pairs
        for field in ("preds_vision", "preds_action")
    )
    payload_pass = (
        metrics["normal_vs_zero"]["local_memory"]["l2_diff"] > 0.0
        and present_local_count >= 2
        and metrics["normal_vs_shuffle"]["local_memory"]["changed_items"] > 0
    )
    status = "PASS" if schema_pass and tensor_schema_pass and all(invariant_exact.values()) and payload_pass and sensitivity_pass else "FAIL"
    result = {
        "schema_version": "r07_fixed_weight_sensitivity_v1",
        "status": status,
        "schema_pass": schema_pass,
        "tensor_schema_pass": tensor_schema_pass,
        "invariant_exact": invariant_exact,
        "shuffle_present_local_count": present_local_count,
        "payload_pass": payload_pass,
        "sensitivity_pass": sensitivity_pass,
        "metrics": metrics,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"R07 fixed-weight sensitivity: {status}")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
