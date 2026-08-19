# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: OpenMDW-1.1
"""G0-R06 latent-cache z0..z4 相邻差异探针。

验证用户假设「训练数据编码把 z1-4 压平成 z0（z0 z1-4 差别不大）」。

对 LIBERO exact-window latent cache 里全部 episode 的每个窗口，统计 5 个
latent（z0..z4，shape [5,48,16,32]，source_frame_indices=[0,4,8,12,16]）的
相邻 MAE。判据：若 MAE 接近 0（复制），则编码压平实锤；若 MAE 相对 latent
自身 std 显著（如 >30%），则数据编码正常、坍缩另有来源。

产物：artifacts/g0/r06/latent_cache_z_probe_summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

ROOT = Path(
    "/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_exact_window_v1/episodes"
)
OUT_JSON = Path("/gemini/code/psm_wma/artifacts/g0/r06/latent_cache_z_probe_summary.json")


def main() -> int:
    eps = sorted(ROOT.glob("episode_*.pt"))
    print(f"episodes: {len(eps)}")

    all_adj: list[list[float]] = []
    all_z0z4: list[float] = []
    all_std: list[float] = []
    n_windows = 0

    for ep in eps:
        item = torch.load(ep, map_location="cpu", weights_only=False)
        for w in item["windows"].values():
            z = w["latent"].float()  # [5,48,16,32]
            if z.ndim != 4 or z.shape[0] != 5:
                continue
            n_windows += 1
            all_std.append(z.std().item())
            all_adj.append([(z[i] - z[i + 1]).abs().mean().item() for i in range(4)])
            all_z0z4.append((z[0] - z[4]).abs().mean().item())

    adj = np.array(all_adj)  # [N,4]
    z0z4 = np.array(all_z0z4)
    std = np.array(all_std)

    print(f"windows: {n_windows}")
    print(f"latent std: mean={std.mean():.4f} median={np.median(std):.4f}")
    print()
    print("相邻 latent MAE 分布 (z_i vs z_{i+1}):")
    for i, lbl in enumerate(["z0-z1", "z1-z2", "z2-z3", "z3-z4"]):
        a = adj[:, i]
        print(
            f"  {lbl}: mean={a.mean():.5f} median={np.median(a):.5f} "
            f"p90={np.percentile(a, 90):.5f} min={a.min():.5f} max={a.max():.5f}"
        )
    print()
    print(
        "z0-z4 (首尾) MAE: mean={:.5f} median={:.5f} p90={:.5f}".format(
            z0z4.mean(), np.median(z0z4), np.percentile(z0z4, 90)
        )
    )
    rel = adj[:, 0] / std
    print(
        f"z0-z1 MAE / latent_std: mean={rel.mean():.4f} "
        f"median={np.median(rel):.4f} p90={np.percentile(rel, 90):.4f}"
    )
    print(f"z0-z1 MAE < 1e-4 的窗口占比: {(adj[:, 0] < 1e-4).mean() * 100:.2f}%")
    print(f"z0-z1 MAE < 1e-3 的窗口占比: {(adj[:, 0] < 1e-3).mean() * 100:.2f}%")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(
            {
                "windows": n_windows,
                "adj_mae_mean": adj.mean(0).tolist(),
                "adj_mae_median": np.median(adj, 0).tolist(),
                "z0z4_mae_mean": float(z0z4.mean()),
                "latent_std_mean": float(std.mean()),
                "rel_z0z1_over_std_mean": float(rel.mean()),
                "frac_z0z1_lt_1e-3": float((adj[:, 0] < 1e-3).mean()),
            },
            indent=2,
        )
    )
    print(f"\nwrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
