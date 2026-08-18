# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: OpenMDW-1.1

"""G0-R06 open-loop expert replay (contract diagnostic).

Feed ground-truth dataset frames (as stored, i.e. the training distribution) to
the policy server and compare the predicted 16-step action chunks against the
expert actions from the parquet. Unlike closed-loop eval, the state never drifts
off the expert trajectory, so this directly measures whether the policy outputs
the right actions given the right observations.

Usage (server must already run with the checkpoint under test):

    python tools/g0/r06_open_loop_replay.py \
        --server_url http://localhost:8001 \
        --episode_parquet .../data/chunk-000/episode_000000.parquet \
        --video_root .../videos/chunk-000 \
        --output_dir artifacts/g0/r06/open_loop_iter800 \
        --stride 4

Outputs: replay.json (per-dim metrics), curves PNG, predictions npz.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_COSMOS = "/gemini/code/psm_wma/cosmos-framework"
for p in ("/gemini/code/psm_wma/.r06_sim_pkgs", _COSMOS):
    if p not in sys.path:
        sys.path.insert(0, p)

from cosmos_framework.simulation.libero.closed_loop_eval import (  # noqa: E402
    ActionEnvironmentClient,
    _framewise_action_to_delta,  # private API, pinned to cosmos-framework commit; re-check on refactor
)

DEFAULT_INSTRUCTION = (
    "put the white mug on the left plate and put the yellow and white mug on the right plate"
)


def _decode_video(path: Path) -> np.ndarray:
    import imageio.v2 as imageio

    return np.stack([f for f in imageio.get_reader(str(path))])  # (T,H,W,3) uint8


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server_url", default="http://localhost:8001")
    ap.add_argument("--episode_parquet", required=True)
    ap.add_argument("--video_root", required=True, help="chunk dir containing observation.images.*")
    ap.add_argument("--output_dir", required=True)
    ap.add_argument("--instruction", default=DEFAULT_INSTRUCTION)
    ap.add_argument("--image_size", type=int, default=256)
    ap.add_argument("--stride", type=int, default=4, help="predict every N expert frames")
    ap.add_argument("--chunk", type=int, default=16)
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    import pyarrow.parquet as pq

    stem = Path(args.episode_parquet).stem  # episode_000000
    tbl = pq.read_table(args.episode_parquet)
    expert = np.stack(tbl.column("action").to_pylist()).astype(np.float64)  # (T,7)
    T = expert.shape[0]
    img = _decode_video(Path(args.video_root) / "observation.images.image" / f"{stem}.mp4")
    wrist = _decode_video(Path(args.video_root) / "observation.images.wrist_image" / f"{stem}.mp4")
    assert img.shape[0] == T and wrist.shape[0] == T, (img.shape, wrist.shape, T)

    client = ActionEnvironmentClient(
        server_url=args.server_url,
        domain_name="libero",
        prompt=args.instruction,
        image_size=args.image_size,
        timeout=300.0,
    )
    info = client.get_info()
    print("[replay] server:", info.get("checkpoint", "?"))

    ts = list(range(0, T - args.chunk, args.stride))
    preds: list[np.ndarray] = []  # each (16,7) after rot6d->rotvec
    for k, t in enumerate(ts):
        concat = client.concatenate_images([img[t], wrist[t]])  # uint8 (256,512,3)
        result = client.predict(concat)
        chunk = np.asarray(result.get("action", []), dtype=np.float64)  # (16,10)
        if chunk.size == 0:
            raise RuntimeError(f"empty action at t={t}")
        assert chunk.shape == (args.chunk, 10), f"unexpected chunk shape {chunk.shape} at t={t}"
        conv = np.stack([_framewise_action_to_delta(chunk[i], "6d") for i in range(args.chunk)])
        preds.append(conv)
        if k % 10 == 0:
            print(f"[replay] {k}/{len(ts)} t={t}")

    preds_np = np.stack(preds)  # (N,16,7)
    np.savez(out_dir / "predictions.npz", ts=np.array(ts), preds=preds_np, expert=expert)

    # ---- metrics ----
    # first-step action: pred[k,0] vs expert[t]
    first = preds_np[:, 0, :]  # (N,7)
    gt0 = expert[np.array(ts)]  # (N,7)
    # full-chunk: pred[k,i] vs expert[t+i]
    err_by_h = []
    for h in range(args.chunk):
        gt_h = expert[np.array(ts) + h]
        err_by_h.append(np.abs(preds_np[:, h, :] - gt_h).mean(axis=0))
    err_by_h = np.array(err_by_h)  # (16,7)

    def corr(a: np.ndarray, b: np.ndarray) -> float:
        if a.std() < 1e-9 or b.std() < 1e-9:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    dim_names = ["dx", "dy", "dz", "drx", "dry", "drz", "gripper"]
    per_dim = {}
    for d_i, name in enumerate(dim_names):
        per_dim[name] = {
            "mae_first_step": float(np.abs(first[:, d_i] - gt0[:, d_i]).mean()),
            "corr_first_step": corr(first[:, d_i], gt0[:, d_i]),
            "expert_std": float(gt0[:, d_i].std()),
            "pred_std": float(first[:, d_i].std()),
        }
    grip_pred_bin = (first[:, 6] > 0.5).astype(int)
    grip_acc = float((grip_pred_bin == gt0[:, 6].astype(int)).mean())
    grip_acc_by_h = []
    for h in range(args.chunk):
        gt_h = expert[np.array(ts) + h, 6].astype(int)
        grip_acc_by_h.append(float(((preds_np[:, h, 6] > 0.5).astype(int) == gt_h).mean()))

    summary = {
        "checkpoint": info.get("checkpoint", ""),
        "episode": stem,
        "instruction": args.instruction,
        "num_queries": len(ts),
        "stride": args.stride,
        # WAM contract: only latent slot 0 (first frame) is the clean condition;
        # the server repeats the single frame 17x but positions 1-16 are generated.
        "input_construction": "single real frame -> server repeats x17 (wam condition_frame_indexes_vision=[0])",
        "per_dim": per_dim,
        "gripper_first_step_acc": grip_acc,
        "gripper_acc_by_horizon": [round(v, 3) for v in grip_acc_by_h],
        "err_by_horizon_mean": err_by_h.mean(axis=1).round(4).tolist(),
        "expert_speed_mean": float(np.linalg.norm(expert[:, :3], axis=1).mean()),
        "pred_first_step_speed_mean": float(np.linalg.norm(first[:, :3], axis=1).mean()),
    }
    (out_dir / "replay.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2)[:1500])

    # ---- curves ----
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=False)
    x = np.array(ts)
    for d_i, name in enumerate(["dx", "dy", "dz"]):
        ax = axes[d_i]
        ax.plot(x, gt0[:, d_i], label="expert", color="tab:blue")
        ax.plot(x, first[:, d_i], label="model(first step)", color="tab:red", alpha=0.8)
        ax.set_ylabel(name)
        ax.legend(loc="upper right")
        ax.grid(alpha=0.3)
    axes[3].step(x, gt0[:, 6], label="expert gripper", color="tab:blue")
    axes[3].plot(x, first[:, 6], label="model gripper(raw)", color="tab:red", alpha=0.8)
    axes[3].set_ylabel("gripper")
    axes[3].legend(loc="upper right")
    axes[3].grid(alpha=0.3)
    fig.suptitle(f"open-loop replay {stem} | {Path(str(info.get('checkpoint',''))).parent.name}")
    fig.tight_layout()
    fig.savefig(out_dir / "curves.png", dpi=110)
    print("[replay] wrote", out_dir / "curves.png")


if __name__ == "__main__":
    main()
