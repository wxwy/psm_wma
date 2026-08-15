#!/usr/bin/env python3
"""G0-R04 正式验收：每步机器可读指标回调（JSONL）。

通过 CLI 注入 trainer.callbacks，不改 Cosmos 配置：
  +trainer.callbacks.r04_step_metrics._target_=tools.g0.r04_step_metrics.StepMetricsCallback
  +trainer.callbacks.r04_step_metrics.output_path=<jsonl 路径>
  +trainer.callbacks.r04_step_metrics.optimizer_type=AdamW
  +trainer.callbacks.r04_step_metrics.fused=false
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import torch

from cosmos_framework.utils.callback import Callback


def _rss_kb() -> int:
    with open("/proc/self/status", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    return -1


class StepMetricsCallback(Callback):
    """每步追加一行 JSONL：iteration/loss/grad_norm/finite/GPU 峰值/RSS。"""

    def __init__(self, output_path: str, optimizer_type: str = "unknown", fused: str = "unknown") -> None:
        self._output_path = Path(output_path)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._static = {"optimizer_type": optimizer_type, "fused": fused}
        self._pending: dict[str, object] = {}

    def on_training_step_start(self, model, data, iteration: int = 0) -> None:
        torch.cuda.reset_peak_memory_stats()
        self._pending = {}

    def on_before_optimizer_step(self, model, optimizer, scheduler, grad_scaler, iteration: int = 0) -> None:
        # 本回调在 callback dict 中位于 grad_clip 之后，测得的是 clip 后的全局 grad norm。
        total_sq = 0.0
        finite = True
        seen = 0
        for param in model.parameters():
            if param.grad is None:
                continue
            grad = param.grad.detach()
            if not torch.isfinite(grad).all():
                finite = False
            total_sq += float(grad.float().pow(2).sum())
            seen += 1
        self._pending = {
            "grad_norm_post_clip": total_sq**0.5,
            "grad_finite": finite,
            "grad_tensors": seen,
        }

    def on_training_step_end(self, model, data_batch, output_batch, loss, iteration: int = 0) -> None:
        loss_value = float(loss.detach().float().cpu())
        record = {
            "iteration": int(iteration),
            "loss": loss_value,
            "loss_finite": bool(torch.isfinite(loss.detach()).all()),
            "gpu_step_peak_mib": round(torch.cuda.max_memory_allocated() / 2**20, 1),
            "rss_kb": _rss_kb(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            **self._static,
            **self._pending,
        }
        with self._output_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._pending = {}
