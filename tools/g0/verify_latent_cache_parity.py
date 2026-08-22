#!/usr/bin/env python3
"""以在线 VAE probe 保存的 uint8/latent 对验证离线编码契约。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface
from cosmos_framework.model.generator.vision_vae import (
    LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
    encode_uint8_vision_item,
)


class _VisionEncoderAdapter:
    def __init__(self, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> None:
        self.tokenizer_vision_gen = tokenizer
        self.tensor_kwargs_fp32 = {"device": device, "dtype": torch.float32}

    def encode(self, state: torch.Tensor) -> torch.Tensor:
        return self.tokenizer_vision_gen.encode(state)

def _encode_concat_view(raw_uint8: torch.Tensor, encoder: _VisionEncoderAdapter, device: torch.device) -> torch.Tensor:
    if raw_uint8.dtype != torch.uint8 or raw_uint8.ndim not in (4, 5):
        raise ValueError(f"Expected uint8 [C,T,H,W] or [B,C,T,H,W], got {tuple(raw_uint8.shape)} {raw_uint8.dtype}")
    if raw_uint8.ndim == 4:
        raw_uint8 = raw_uint8.unsqueeze(0)
    return encode_uint8_vision_item(encoder, raw_uint8.to(device)).float().cpu()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--atol", type=float, default=1e-6)
    args = parser.parse_args()
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA is required when --device starts with cuda")

    device = torch.device(args.device)
    tokenizer = Wan2pt2VAEInterface(
        vae_path=str(args.vae_path),
        encode_exact_durations=LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
        encode_chunk_frames=LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    )
    tokenizer.model.model.to(device).eval()
    encoder = _VisionEncoderAdapter(tokenizer, device)
    rows: list[dict[str, object]] = []
    for sample_dir in sorted(args.probe_root.glob("rank_*/sample_*")):
        meta_path = sample_dir / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
        raw_uint8 = torch.load(sample_dir / "raw_uint8.pt", map_location="cpu", weights_only=True)
        online_latent = torch.load(sample_dir / "online_latent.pt", map_location="cpu", weights_only=True).float()
        with torch.inference_mode():
            offline_latent = _encode_concat_view(raw_uint8, encoder, device)
        shape_match = tuple(offline_latent.shape) == tuple(online_latent.shape)
        dtype_match = offline_latent.dtype == online_latent.dtype
        finite = bool(torch.isfinite(offline_latent).all() and torch.isfinite(online_latent).all())
        max_abs_diff = float((offline_latent - online_latent).abs().max()) if shape_match else float("inf")
        rows.append(
            {
                "sample": str(sample_dir),
                "cache_key": {
                    "suite": meta.get("suite"),
                    "task_id": meta.get("task_id"),
                    "episode_index": meta.get("episode_index"),
                    "start_frame": meta.get("start_frame"),
                },
                "shape_match": shape_match,
                "dtype_match": dtype_match,
                "finite": finite,
                "max_abs_diff": max_abs_diff,
                "pass": shape_match and dtype_match and finite and max_abs_diff <= args.atol,
            }
        )
    result = {
        "schema_version": "online_vae_probe_parity_v1",
        "probe_root": str(args.probe_root),
        "atol": args.atol,
        "vae_compute_dtype": str(tokenizer.dtype),
        "encode_exact_durations": LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
        "encode_chunk_frames": LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
        "sample_count": len(rows),
        "max_abs_diff": max((float(row["max_abs_diff"]) for row in rows), default=None),
        "status": "PASS" if rows and all(bool(row["pass"]) for row in rows) else "FAIL",
        "samples": rows,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "sample_count", "max_abs_diff")}, ensure_ascii=False))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
