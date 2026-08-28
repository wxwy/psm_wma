#!/usr/bin/env python3
"""R08 Gate-0：检验 Wan exact-window latent 的 z0 是否依赖未来 suffix。

对每个选中的 LIBERO anchor，构造两个合法的 17 帧输入：A 使用原始窗口，B
保留 A 的首帧、替换其余 16 帧。两条输入均经当前训练的 concat/uint8/resize/VAE
契约重新编码；只比较 temporal latent index 0。该工具不读取 cache latent，也不
修改数据合同或模型。
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np
import torch

from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.data.generator.action.utils.transforms import VideoResize
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface
from cosmos_framework.model.generator.vision_vae import (
    LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
)
from exact_window_cache import WINDOW_FRAMES, VisionEncoderAdapter, encode_window, to_training_uint8


SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")


def _git_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _tensor_sha256(value: torch.Tensor) -> str:
    value = value.detach().cpu().contiguous()
    return hashlib.sha256(value.numpy().tobytes()).hexdigest()


def _summary(a: torch.Tensor, b: torch.Tensor) -> dict[str, object]:
    if a.shape != b.shape:
        raise ValueError(f"z0 shape mismatch: {tuple(a.shape)} != {tuple(b.shape)}")
    difference = a - b
    l2 = float(torch.linalg.vector_norm(difference))
    reference_l2 = float(torch.linalg.vector_norm(a))
    return {
        "shape": list(a.shape),
        "dtype": str(a.dtype),
        "sha256_a": _tensor_sha256(a),
        "sha256_b": _tensor_sha256(b),
        "bitwise_equal": bool(torch.equal(a, b)),
        "max_abs": float(difference.abs().max()),
        "l2": l2,
        "relative_l2": l2 / max(reference_l2, torch.finfo(a.dtype).tiny),
        "finite": bool(torch.isfinite(a).all() and torch.isfinite(b).all()),
    }


def _episode_rows(dataset: LIBEROLeRobotDataset, episode_index: int) -> np.ndarray:
    rows = np.flatnonzero(dataset._row_episode == episode_index)
    if rows.size < WINDOW_FRAMES:
        raise ValueError(f"episode {episode_index} has only {rows.size} frames")
    return rows


def _select_anchors(dataset: LIBEROLeRobotDataset, anchors_per_mod: int) -> list[dict[str, int]]:
    """每 suite 每个 start % 4 选足 anchors，优先分散 episode/task。"""
    candidates: dict[int, list[dict[str, int]]] = defaultdict(list)
    for episode_index in (int(value) for value in dataset._ep_vals):
        rows = _episode_rows(dataset, episode_index)
        task_index = int(dataset._row_task[rows[0]])
        max_start = int(rows.size - WINDOW_FRAMES)
        for start_frame in range(max_start + 1):
            candidates[start_frame % 4].append(
                {"episode_index": episode_index, "task_index": task_index, "start_frame": start_frame}
            )

    selected: list[dict[str, int]] = []
    for remainder in range(4):
        by_episode: dict[int, list[dict[str, int]]] = defaultdict(list)
        for candidate in candidates[remainder]:
            by_episode[candidate["episode_index"]].append(candidate)
        chosen: list[dict[str, int]] = []
        for episode_index in sorted(by_episode):
            if len(chosen) == anchors_per_mod:
                break
            chosen.append(by_episode[episode_index][0])
        if len(chosen) != anchors_per_mod:
            raise RuntimeError(
                f"Cannot select {anchors_per_mod} anchors for start_frame % 4 == {remainder}; got {len(chosen)}"
            )
        selected.extend(chosen)
    return selected


def _different_suffix_start(frame_count: int, anchor_start: int) -> int:
    """返回不同于 anchor 的、仍有 17 帧有效窗口起点。"""
    maximum = frame_count - WINDOW_FRAMES
    for candidate in (maximum, 0, anchor_start + 1, anchor_start - 1):
        if 0 <= candidate <= maximum and candidate != anchor_start:
            return candidate
    raise RuntimeError(f"No alternate valid suffix for start={anchor_start}, frame_count={frame_count}")


def _make_pair(video_uint8: torch.Tensor, anchor_start: int) -> tuple[torch.Tensor, torch.Tensor, int]:
    """从一个 episode 构造 first-frame bitwise 相同、suffix 不同的 A/B。"""
    if video_uint8.ndim != 4 or video_uint8.dtype != torch.uint8:
        raise ValueError("Expected uint8 [C,T,H,W]")
    alternate_start = _different_suffix_start(int(video_uint8.shape[1]), anchor_start)
    a = video_uint8[:, anchor_start : anchor_start + WINDOW_FRAMES].contiguous()
    alternate = video_uint8[:, alternate_start : alternate_start + WINDOW_FRAMES]
    b = torch.cat((a[:, :1], alternate[:, 1:]), dim=1).contiguous()
    if not torch.equal(a[:, :1], b[:, :1]):
        raise AssertionError("Gate-0 construction changed the first frame")
    if torch.equal(a[:, 1:], b[:, 1:]):
        raise RuntimeError(
            f"Alternate suffix is pixel-identical for anchor={anchor_start}, alternate={alternate_start}; choose another anchor"
        )
    return a, b, alternate_start


def _load_episode_video(dataset: LIBEROLeRobotDataset, episode_index: int, resize: VideoResize) -> torch.Tensor:
    rows = _episode_rows(dataset, episode_index)
    timestamps = [float(dataset._row_timestamp[row]) for row in rows]
    video = dataset._load_video(dataset._episodes[episode_index], timestamps)
    video_uint8 = to_training_uint8(video)
    return resize({"video": video_uint8}, resolution=None)["video"]


def _run_suite(
    dataset_root: Path,
    tokenizer: Wan2pt2VAEInterface,
    device: torch.device,
    anchors_per_mod: int,
) -> tuple[list[dict[str, object]], list[dict[str, torch.Tensor]]]:
    dataset = LIBEROLeRobotDataset(
        root=str(dataset_root), split="full", fps=20, chunk_length=16, camera_mode="concat_view", image_size=256,
        action_normalization=None,
    )
    anchors = _select_anchors(dataset, anchors_per_mod)
    resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)
    encoder = VisionEncoderAdapter(tokenizer, device)
    videos: dict[int, torch.Tensor] = {}
    records: list[dict[str, object]] = []
    sidecar: list[dict[str, torch.Tensor]] = []
    for ordinal, anchor in enumerate(anchors):
        episode_index = anchor["episode_index"]
        video_uint8 = videos.get(episode_index)
        if video_uint8 is None:
            video_uint8 = _load_episode_video(dataset, episode_index, resize)
            videos[episode_index] = video_uint8
        a, b, alternate_start = _make_pair(video_uint8, anchor["start_frame"])
        z0_a = encode_window(a, encoder, device=device)[0]
        z0_b = encode_window(b, encoder, device=device)[0]
        metrics = _summary(z0_a, z0_b)
        record = {
            "suite": dataset_root.name,
            "ordinal": ordinal,
            **anchor,
            "alternate_suffix_start_frame": alternate_start,
            "first_frame_bitwise_equal": True,
            "suffix_pixel_bitwise_different": True,
            "z0": metrics,
        }
        records.append(record)
        sidecar.append({"z0_a": z0_a, "z0_b": z0_b})
        print(
            f"[{dataset_root.name}] {ordinal + 1}/{len(anchors)} ep={episode_index} "
            f"start={anchor['start_frame']} max_abs={metrics['max_abs']:.3e}",
            flush=True,
        )
    return records, sidecar


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True, help="包含四个 libero_* suite 的根目录")
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, default=None, help="默认与 --output 同名 .pt；独立审查前不得删除")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--anchors-per-mod", type=int, default=4)
    parser.add_argument("--atol", type=float, default=1e-6)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.anchors_per_mod < 4:
        raise ValueError("R08 Gate-0 requires --anchors-per-mod >= 4")
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the Wan z0 suffix-invariance diagnostic")

    root = Path(__file__).resolve().parents[2]
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device(args.device)
    tokenizer = Wan2pt2VAEInterface(
        vae_path=str(args.vae_path),
        encode_exact_durations=LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
        encode_chunk_frames=LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    )
    tokenizer.model.model.to(device).eval()
    all_records: list[dict[str, object]] = []
    all_sidecar: list[dict[str, torch.Tensor]] = []
    for suite in SUITES:
        records, sidecar = _run_suite(args.dataset_root / suite, tokenizer, device, args.anchors_per_mod)
        all_records.extend(records)
        all_sidecar.extend(sidecar)

    status = "PASS" if all(float(record["z0"]["max_abs"]) <= args.atol for record in all_records) else "FAIL"
    sidecar_path = args.sidecar or args.output.with_suffix(".pt")
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"schema_version": "r08_z0_suffix_invariance_sidecar_v1", "pairs": all_sidecar}, sidecar_path)
    sidecar_sha256 = hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
    result = {
        "schema_version": "r08_z0_suffix_invariance_v1",
        "status": status,
        "scope": "Gate-0 diagnostic only; no cache latent read, history/model mutation, training, or R09 backend",
        "atol": args.atol,
        "anchor_count": len(all_records),
        "coverage": {"suites": list(SUITES), "start_frame_mod4": [0, 1, 2, 3], "anchors_per_suite_mod": args.anchors_per_mod},
        "vae_contract": {
            "input": "concat_view -> to_training_uint8 -> VideoResize(resolution=None) -> Wan2pt2VAEInterface.encode",
            "window_frames": WINDOW_FRAMES,
            "compute_dtype": str(tokenizer.dtype),
            "encode_exact_durations": LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
            "encode_chunk_frames": LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
            "comparison": "only latent temporal index 0 (z0)",
        },
        "sidecar": {"path": str(sidecar_path), "sha256": sidecar_sha256, "retention": "retain until independent Gate-0 review closes"},
        "records": all_records,
        "provenance": {
            "root_commit": _git_commit(root),
            "submodule_commit": _git_commit(root / "cosmos-framework"),
            "dataset_root": str(args.dataset_root),
            "vae_path": str(args.vae_path),
            "argv": sys.argv,
            "seed": args.seed,
            "device": str(device),
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "hostname": socket.gethostname(),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "anchor_count": len(all_records), "output": str(args.output)}, ensure_ascii=False))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
