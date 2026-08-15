#!/usr/bin/env python3
"""G0-R05 tiny-overfit per-step machine-readable metrics callback."""

from __future__ import annotations

import json
import time
from pathlib import Path

import torch

from cosmos_framework.utils.callback import Callback


def _rss_kb() -> int:
    status = Path("/proc/self/status").read_text(encoding="utf-8")
    for line in status.splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return -1


def _scalar(output_batch: dict, key: str) -> tuple[float | None, bool | None]:
    value = output_batch.get(key)
    if value is None:
        return None, None
    if not isinstance(value, torch.Tensor) or value.numel() != 1:
        raise ValueError(f"Expected scalar tensor for {key}, got {type(value).__name__}")
    detached = value.detach().float()
    return float(detached.cpu()), bool(torch.isfinite(detached).all())


class R05TinyOverfitMetricsCallback(Callback):
    """Append total/action/vision losses, gradients and resource peaks as JSONL."""

    def __init__(
        self,
        output_path: str,
        validation_output_path: str | None = None,
        optimizer_type: str = "unknown",
        fused: bool = False,
    ) -> None:
        self._output_path = Path(output_path)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._validation_output_path = Path(validation_output_path) if validation_output_path else None
        if self._validation_output_path is not None:
            self._validation_output_path.parent.mkdir(parents=True, exist_ok=True)
        self._static = {"optimizer_type": optimizer_type, "fused": bool(fused)}
        self._pending: dict[str, object] = {}

    def on_training_step_start(self, model, data, iteration: int = 0) -> None:
        torch.cuda.reset_peak_memory_stats()
        self._pending = {}

    def on_before_optimizer_step(self, model, optimizer, scheduler, grad_scaler, iteration: int = 0) -> None:
        total_sq = 0.0
        finite = True
        seen = 0
        for param in model.parameters():
            if param.grad is None:
                continue
            grad = param.grad.detach()
            finite = finite and bool(torch.isfinite(grad).all())
            total_sq += float(grad.float().pow(2).sum())
            seen += 1
        self._pending = {
            "grad_norm_post_clip": total_sq**0.5,
            "grad_finite": finite,
            "grad_tensors": seen,
        }

    def on_training_step_end(self, model, data_batch, output_batch, loss, iteration: int = 0) -> None:
        total = loss.detach().float()
        action_loss, action_finite = _scalar(output_batch, "flow_matching_loss_action")
        vision_loss, vision_finite = _scalar(output_batch, "flow_matching_loss_vision")
        action_x0_mae, action_x0_mae_finite = _scalar(output_batch, "action_x0_reconstruction_mae")
        record = {
            "iteration": int(iteration),
            "total_loss": float(total.cpu()),
            "total_loss_finite": bool(torch.isfinite(total).all()),
            "action_flow_loss": action_loss,
            "action_flow_loss_finite": action_finite,
            "action_x0_reconstruction_mae": action_x0_mae,
            "action_x0_reconstruction_mae_finite": action_x0_mae_finite,
            "vision_flow_loss": vision_loss,
            "vision_flow_loss_finite": vision_finite,
            "gpu_step_peak_mib": round(torch.cuda.max_memory_allocated() / 2**20, 1),
            "rss_kb": _rss_kb(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            **self._static,
            **self._pending,
        }
        with self._output_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._pending = {}

    def on_validation_step_end(self, model, data_batch, output_batch, loss, iteration: int = 0) -> None:
        if self._validation_output_path is None:
            return
        total = loss.detach().float()
        action_loss, action_finite = _scalar(output_batch, "flow_matching_loss_action")
        vision_loss, vision_finite = _scalar(output_batch, "flow_matching_loss_vision")
        action_x0_mae, action_x0_mae_finite = _scalar(output_batch, "action_x0_reconstruction_mae")
        record = {
            "iteration": int(iteration),
            "total_loss": float(total.cpu()),
            "total_loss_finite": bool(torch.isfinite(total).all()),
            "action_flow_loss": action_loss,
            "action_flow_loss_finite": action_finite,
            "action_x0_reconstruction_mae": action_x0_mae,
            "action_x0_reconstruction_mae_finite": action_x0_mae_finite,
            "vision_flow_loss": vision_loss,
            "vision_flow_loss_finite": vision_finite,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            **self._static,
        }
        with self._validation_output_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
