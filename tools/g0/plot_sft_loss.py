#!/usr/bin/env python3
"""从可恢复的训练日志绘制 LIBERO 4in1 SFT loss 曲线。

日志因重启截断，仅覆盖 iter 301-404 与 451+；405-450 段永久丢失。
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

LOG_DIR = Path("cosmos-framework/outputs/train/logs")
SOURCES = [
    LOG_DIR / "resume_libero_4in1_from_iter_000000300.log",
    LOG_DIR / "resume_libero_4in1_from_iter_000000375.log",
    LOG_DIR / "action_policy_libero_edge_all_sft.log",
]
OUT = Path("cosmos-framework/outputs/train/cosmos3_action_libero/action_sft/edge_libero_4in1/libero_4in1_sft_loss_latest.png")

pattern = re.compile(
    r"iteration=(\d+) \| train/loss=([\d.]+) \| flow_matching_loss_vision=([\d.]+) \| flow_matching_loss_action=([\d.]+)"
)

points: dict[int, tuple[float, float, float]] = {}
for source in SOURCES:
    if not source.is_file():
        continue
    for line in source.open("r", errors="replace"):
        m = pattern.search(line)
        if m:
            points[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))

iters = sorted(points)
total = [points[i][0] for i in iters]
vision = [points[i][1] for i in iters]
action = [points[i][2] for i in iters]
print(f"points={len(iters)} range={iters[0]}..{iters[-1]}")

# LR 曲线：解析配置（运行保存的 config.yaml）为 LambdaLinear，lr=5e-5，
# 适配器组（action2llm/llm2action/action_modality_embed）乘 5 = 2.5e-4。
# warmup: f=(f_max-f_start)/200*n+f_start; 之后 f=(16000-n)/(16000-200)。
BASE_LR, ADAPTER_MULT = 5.0e-05, 5.0
WARM_UP, CYCLE, F_START, F_MAX = 200, 16000, 1.0e-06, 1.0


def lr_multiplier(n: int) -> float:
    if n < WARM_UP:
        return (F_MAX - F_START) / WARM_UP * n + F_START
    return F_MAX * (CYCLE - n) / (CYCLE - WARM_UP)


lr_x = list(range(0, 5001))
lr_base = [BASE_LR * lr_multiplier(n) for n in lr_x]
lr_adapter = [BASE_LR * ADAPTER_MULT * lr_multiplier(n) for n in lr_x]

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=False)
fig.suptitle(
    f"LIBERO 4in1 SFT (Edge-DROID warm start) — recoverable logs: iter 301-404 + 451-{iters[-1]}; "
    "gap 405-450 lost to log truncation; LR from resolved config (LambdaLinear)",
    fontsize=11,
)
for ax in (ax1, ax2):
    ax.axvspan(404.5, 450.5, color="red", alpha=0.06)

ax1.plot(iters, total, ".-", ms=3, lw=0.8, color="tab:blue")
ax1.set_ylabel("train/loss")
ax1.grid(alpha=0.3)

ax2.plot(iters, vision, ".-", ms=3, lw=0.8, color="tab:orange", label="vision")
ax2.plot(iters, action, ".-", ms=3, lw=0.8, color="tab:green", label="action")
ax2.set_ylabel("flow matching")
ax2.set_xlabel("iteration")
ax2.legend()
ax2.grid(alpha=0.3)

ax3.plot(lr_x, lr_base, lw=1.2, color="tab:purple", label="base lr (5e-5 peak)")
ax3.plot(lr_x, lr_adapter, lw=1.2, color="tab:red", label="action adapters lr (2.5e-4 peak)")
ax3.axvline(iters[-1], color="gray", ls="--", lw=1, label=f"current iter {iters[-1]}")
ax3.set_ylabel("learning rate")
ax3.set_xlabel("iteration")
ax3.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
ax3.legend()
ax3.grid(alpha=0.3)

fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=110)
print(f"saved {OUT}")
