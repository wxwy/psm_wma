#!/usr/bin/env python3
"""在隔离进程中扫描 Wan VAE 的 CUDA 运行时上下文。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


_PROFILES = {
    "builder_baseline": {
        "allow_tf32": True,
        "cudnn_deterministic": False,
        "cudnn_benchmark": False,
        "use_deterministic_algorithms": False,
        "cublas_workspace_config": None,
    },
    "tf32_off": {
        "allow_tf32": False,
        "cudnn_deterministic": False,
        "cudnn_benchmark": False,
        "use_deterministic_algorithms": False,
        "cublas_workspace_config": None,
    },
    "cudnn_deterministic": {
        "allow_tf32": True,
        "cudnn_deterministic": True,
        "cudnn_benchmark": False,
        "use_deterministic_algorithms": True,
        "cublas_workspace_config": ":4096:8",
    },
    "cublas_workspace": {
        "allow_tf32": True,
        "cudnn_deterministic": False,
        "cudnn_benchmark": False,
        "use_deterministic_algorithms": False,
        "cublas_workspace_config": ":4096:8",
    },
    "cudnn_benchmark": {
        "allow_tf32": True,
        "cudnn_deterministic": False,
        "cudnn_benchmark": True,
        "use_deterministic_algorithms": False,
        "cublas_workspace_config": None,
    },
    "training_context": {
        "allow_tf32": False,
        "cudnn_deterministic": True,
        "cudnn_benchmark": False,
        "use_deterministic_algorithms": True,
        "cublas_workspace_config": ":4096:8",
    },
}


def _add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--episode-index", type=int, required=True)
    parser.add_argument("--start-frame", type=int, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--online-latent", type=Path, default=None)
    parser.add_argument("--expected-raw-sha256", default=None)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help="内部：运行一个 profile。")
    parser.add_argument("--profile-json", default=None, help="内部：profile JSON。")
    parser.add_argument("--output", type=Path, default=None, help="父进程汇总 JSON 输出。")
    _add_common_arguments(parser)
    args = parser.parse_args()
    if args.worker == (args.output is not None):
        parser.error("父进程必须提供 --output；worker 必须提供 --worker 且不得提供 --output。")
    if args.worker and args.profile_json is None:
        parser.error("worker requires --profile-json")
    return args


def _worker(args: argparse.Namespace) -> dict[str, Any]:
    # torch 必须在子进程里、并在 CUBLAS_WORKSPACE_CONFIG 已设置后才导入。
    import numpy as np
    import torch

    from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
    from cosmos_framework.data.generator.action.utils.transforms import VideoResize
    from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface
    from cosmos_framework.model.generator.vision_vae import (
        LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
        LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
        encode_uint8_vision_item,
    )

    profile = json.loads(args.profile_json)
    torch.backends.cudnn.allow_tf32 = profile["allow_tf32"]
    torch.backends.cuda.matmul.allow_tf32 = profile["allow_tf32"]
    torch.backends.cudnn.deterministic = profile["cudnn_deterministic"]
    torch.backends.cudnn.benchmark = profile["cudnn_benchmark"]
    torch.use_deterministic_algorithms(profile["use_deterministic_algorithms"])

    class Encoder:
        def __init__(self, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> None:
            self.tokenizer_vision_gen = tokenizer
            self.tensor_kwargs_fp32 = {"device": device, "dtype": torch.float32}

        def encode(self, state: torch.Tensor) -> torch.Tensor:
            return self.tokenizer_vision_gen.encode(state)

    device = torch.device(args.device)
    dataset = LIBEROLeRobotDataset(
        root=str(args.dataset_root),
        split="full",
        fps=20,
        chunk_length=16,
        camera_mode="concat_view",
        image_size=256,
        action_normalization=None,
    )
    row_indices = np.flatnonzero(dataset._row_episode == args.episode_index)
    if len(row_indices) == 0:
        raise ValueError(f"Unknown episode_index={args.episode_index}")
    timestamps = [float(dataset._row_timestamp[index]) for index in row_indices]
    video = dataset._load_video(dataset._episodes[args.episode_index], timestamps)
    video_uint8 = (video * 255.0).clamp(0.0, 255.0).to(torch.uint8).permute(1, 0, 2, 3).contiguous()
    video_uint8 = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)(
        {"video": video_uint8}, resolution=None
    )["video"]
    raw_uint8 = video_uint8[:, args.start_frame : args.start_frame + 17].unsqueeze(0).contiguous()
    if raw_uint8.shape[2] != 17:
        raise ValueError(f"Invalid window start={args.start_frame} for episode={args.episode_index}")
    raw_sha256 = hashlib.sha256(raw_uint8.numpy().tobytes()).hexdigest()
    if args.expected_raw_sha256 is not None and raw_sha256 != args.expected_raw_sha256:
        raise ValueError(f"raw SHA256 mismatch: expected={args.expected_raw_sha256}, got={raw_sha256}")

    cache_file = args.cache_root / "episodes" / f"episode_{args.episode_index:06d}.pt"
    cache_item = torch.load(cache_file, map_location="cpu", weights_only=True)
    cached = cache_item["windows"][str(args.start_frame)]["latent"]
    cached = cached.permute(1, 0, 2, 3).unsqueeze(0).to(device=device, dtype=torch.float32)

    tokenizer = Wan2pt2VAEInterface(
        vae_path=str(args.vae_path),
        encode_exact_durations=LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
        encode_chunk_frames=LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    )
    tokenizer.model.model.to(device)
    encoded = encode_uint8_vision_item(Encoder(tokenizer, device), raw_uint8.to(device))

    def _diff(reference: torch.Tensor) -> dict[str, float]:
        return {
            "max_abs_diff": float((encoded - reference).abs().max().item()),
            "mean_abs_diff": float((encoded - reference).abs().mean().item()),
        }

    result: dict[str, Any] = {
        "profile": profile,
        "runtime": {
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "cudnn_version": torch.backends.cudnn.version(),
            "allow_tf32": torch.backends.cudnn.allow_tf32,
            "cudnn_deterministic": torch.backends.cudnn.deterministic,
            "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
            "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
        },
        "raw_uint8": {"shape": list(raw_uint8.shape), "sha256": raw_sha256},
        "encoded_shape": list(encoded.shape),
        "cache": _diff(cached),
    }
    if args.online_latent is not None:
        online = torch.load(args.online_latent, map_location=device, weights_only=True)
        if online.ndim == 4:
            online = online.permute(1, 0, 2, 3).unsqueeze(0)
        result["training_online"] = _diff(online.to(device=device, dtype=torch.float32))
    return result


def _parent(args: argparse.Namespace) -> int:
    results: dict[str, Any] = {}
    for name, profile in _PROFILES.items():
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker",
            "--profile-json",
            json.dumps(profile, sort_keys=True),
            "--dataset-root",
            str(args.dataset_root),
            "--cache-root",
            str(args.cache_root),
            "--vae-path",
            str(args.vae_path),
            "--episode-index",
            str(args.episode_index),
            "--start-frame",
            str(args.start_frame),
            "--device",
            args.device,
        ]
        if args.online_latent is not None:
            command.extend(["--online-latent", str(args.online_latent)])
        if args.expected_raw_sha256 is not None:
            command.extend(["--expected-raw-sha256", args.expected_raw_sha256])
        environment = dict(os.environ)
        workspace = profile["cublas_workspace_config"]
        if workspace is None:
            environment.pop("CUBLAS_WORKSPACE_CONFIG", None)
        else:
            environment["CUBLAS_WORKSPACE_CONFIG"] = workspace
        completed = subprocess.run(command, capture_output=True, text=True, env=environment)
        if completed.returncode != 0:
            raise RuntimeError(f"profile={name} failed:\n{completed.stdout}\n{completed.stderr}")
        # Worker stdout may carry dataset/logger INFO lines before the JSON payload;
        # the result JSON is always the final non-empty line.
        stdout_lines = [line for line in completed.stdout.splitlines() if line.strip()]
        try:
            results[name] = json.loads(stdout_lines[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"profile={name} produced no parseable JSON:\n{completed.stdout}\n{completed.stderr}") from exc
    payload = {
        "schema_version": "vae_runtime_context_v1",
        "episode_index": args.episode_index,
        "start_frame": args.start_frame,
        "profiles": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "profiles": list(results)}, ensure_ascii=False))
    return 0


def main() -> int:
    args = _parse_args()
    if args.worker:
        print(json.dumps(_worker(args), ensure_ascii=False))
        return 0
    return _parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
