# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: OpenMDW-1.1
"""Teacher-forced E2 probe callback.

On the first (and only) training step, re-run model.training_step twice with
identical RNG seeds: once with the real batch and once with vision blacked out.
Log action_x0_reconstruction_mae and flow_matching_loss_action for both, plus
sigma_action, to quantify whether the one-step velocity prediction uses vision.
"""
from __future__ import annotations

import json
from pathlib import Path

import torch

from cosmos_framework.utils.callback import Callback


class TeacherForcedProbeCallback(Callback):
    def __init__(self, output_path: str) -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self.output_path, "w")
        self._done = False

    def on_training_step_end(self, model, data_batch, output_batch, loss, iteration: int = 0) -> None:
        if self._done:
            return
        self._done = True
        video_key = model.input_video_key
        image_key = model.input_image_key
        key = video_key if video_key in data_batch else image_key
        if key not in data_batch:
            print(f"[E2] WARNING: neither {video_key} nor {image_key} in data_batch; skipping black-vision run")
            return

        model.eval()
        seed = iteration
        with torch.no_grad():
            # Real batch with deterministic seed
            torch.manual_seed(seed)
            real_out, _ = model.training_step(data_batch, iteration)

            # Black-vision batch: zero the media tensor(s)
            black_batch = {}
            for k, v in data_batch.items():
                if k == key and isinstance(v, list):
                    black_batch[k] = []
                    for item in v:
                        if isinstance(item, torch.Tensor):
                            black_batch[k].append(torch.zeros_like(item))
                        elif isinstance(item, list):
                            black_batch[k].append([torch.zeros_like(t) for t in item])
                        else:
                            black_batch[k].append(item)
                else:
                    black_batch[k] = v

            torch.manual_seed(seed)
            black_out, _ = model.training_step(black_batch, iteration)

        sigma = real_out.get("sigma_action")
        sigma_val = float(sigma.item()) if torch.is_tensor(sigma) else None
        row = {
            "iteration": iteration,
            "seed": seed,
            "media_key": key,
            "real_action_x0_mae": float(real_out.get("action_x0_reconstruction_mae", 0)),
            "black_action_x0_mae": float(black_out.get("action_x0_reconstruction_mae", 0)),
            "delta_action_x0_mae": float(real_out.get("action_x0_reconstruction_mae", 0))
            - float(black_out.get("action_x0_reconstruction_mae", 0)),
            "real_fm_loss_action": float(real_out.get("flow_matching_loss_action", 0)),
            "black_fm_loss_action": float(black_out.get("flow_matching_loss_action", 0)),
            "sigma_action": sigma_val,
        }
        self._handle.write(json.dumps(row) + "\n")
        self._handle.flush()
        print("[E2] " + json.dumps(row, indent=2))

    def __del__(self):
        if hasattr(self, "_handle") and self._handle:
            self._handle.close()
