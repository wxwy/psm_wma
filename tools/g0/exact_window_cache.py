"""LIBERO 与 RoboCasa 共用的 exact-window VAE cache 原语。"""

from __future__ import annotations

import os
from pathlib import Path

import torch

from cosmos_framework.model.generator.vision_vae import encode_uint8_vision_item


WINDOW_FRAMES = 17
LATENT_ANCHOR_STRIDE = 4


class VisionEncoderAdapter:
    """让离线工具复用训练侧 uint8 VAE 编码契约的最小适配器。"""

    def __init__(self, tokenizer: object, device: torch.device) -> None:
        self.tokenizer_vision_gen = tokenizer
        self.tensor_kwargs_fp32 = {"device": device, "dtype": torch.float32}

    def encode(self, state: torch.Tensor) -> torch.Tensor:
        return self.tokenizer_vision_gen.encode(state)  # type: ignore[union-attr]


def to_training_uint8(video: torch.Tensor) -> torch.Tensor:
    """匹配 ``ActionBaseDataset._build_result`` 的 float 视频到 uint8 布局转换。"""
    if video.ndim != 4:
        raise ValueError(f"Expected video [T,C,H,W], got {tuple(video.shape)}")
    return (video * 255.0).clamp(0.0, 255.0).to(torch.uint8).permute(1, 0, 2, 3).contiguous()


def encode_window(video_uint8: torch.Tensor, encoder: VisionEncoderAdapter, *, device: torch.device) -> torch.Tensor:
    """经共享 ``vision_vae`` 入口编码一个独立 17 帧窗口，返回 fp32 ``[T,C,H,W]``。"""
    if video_uint8.ndim != 4 or video_uint8.shape[1] != WINDOW_FRAMES or video_uint8.dtype != torch.uint8:
        raise ValueError(f"Expected uint8 [C,{WINDOW_FRAMES},H,W], got {tuple(video_uint8.shape)} {video_uint8.dtype}")
    latent = encode_uint8_vision_item(encoder, video_uint8.unsqueeze(0).to(device))
    latent = latent.squeeze(0).permute(1, 0, 2, 3).contiguous().cpu()
    if latent.dtype != torch.float32 or not torch.isfinite(latent).all():
        raise FloatingPointError("Exact-window VAE produced non-finite or non-fp32 latent")
    return latent


def window_indices(start_frame: int) -> tuple[torch.Tensor, torch.Tensor]:
    """返回完整 17 帧窗口与五个 causal latent 锚点索引。"""
    return (
        torch.arange(start_frame, start_frame + WINDOW_FRAMES, dtype=torch.long),
        torch.arange(start_frame, start_frame + WINDOW_FRAMES, LATENT_ANCHOR_STRIDE, dtype=torch.long),
    )


def write_atomic(payload: dict[str, object], output_path: Path) -> None:
    """避免中断时留下可被 resume 误认为完整的 episode 文件。"""
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    torch.save(payload, temporary_path)
    os.replace(temporary_path, output_path)
