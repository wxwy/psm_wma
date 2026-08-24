#!/usr/bin/env python3
"""从可恢复的训练日志绘制 LIBERO 4in1 SFT loss 曲线。

日志因重启截断，现存覆盖 iter 301-404 与 2751-至今；405-450 与 2005-2750 段永久丢失
（stdout_loss_logger 只 print stdout，未落盘；tmux buffer 上限 2000 行被覆盖）。
451-2004 段的历史 raw 曲线通过数字化存档图 libero_4in1_sft_loss_latest_old.png 恢复
（该图由加 EMA 之前的旧版脚本在数据完整时生成，只有全 alpha 的 raw 点线）；
数字化用网格线标定坐标轴 + tab 颜色掩码逐列取中位数，结果缓存为 CSV，存档图不变时直接复用。
注意：libero_4in1_sft_loss_iter301-2784_archive.png 是日志截断后重画的误存文件
（451-2750 为假平线），不可作为数字化源。
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

LOG_DIR = Path("cosmos-framework/outputs/train/logs")
SOURCES = [
    LOG_DIR / "resume_libero_4in1_from_iter_000000300.log",
    LOG_DIR / "resume_libero_4in1_from_iter_000000375.log",
    LOG_DIR / "action_policy_libero_edge_all_sft.log",
]
OUT_DIR = Path("cosmos-framework/outputs/train/cosmos3_action_libero/action_sft/edge_libero_4in1")
OUT = OUT_DIR / "libero_4in1_sft_loss_latest.png"
ARCHIVE_PNG = OUT_DIR / "libero_4in1_sft_loss_latest_old.png"
CSV_AX1 = OUT_DIR / "loss_history_digitized_raw_ax1.csv"
CSV_AX2 = OUT_DIR / "loss_history_digitized_raw_ax2.csv"
HIST_LO, HIST_HI = 301, 2004  # 存档图覆盖的真实数据范围（其间 405-450 为缺口）
GAP1 = (404.5, 450.5)  # 永久丢失段 1
GAP2 = (2004.5, 2750.5)  # 永久丢失段 2（2751 起由现存日志接续）

# matplotlib 默认 tab 调色板（存档图 raw 点线颜色，全 alpha）
TAB_BLUE = (31, 119, 180)
TAB_ORANGE = (255, 127, 14)
TAB_GREEN = (44, 160, 44)

# 存档图坐标轴刻度（已用 ReadMediaFile 核对）；用于网格线标定
X_TICKS = [250, 500, 750, 1000, 1250, 1500, 1750, 2000]
AX1_Y_TICKS = [2.2, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0]  # 自上而下
AX2_Y_TICKS = [0.14, 0.12, 0.10, 0.08, 0.06, 0.04, 0.02]  # 自上而下

# ---------------------------------------------------------------- 日志解析

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


def ema(values: list[float], weight: float = 0.98) -> list[float]:
    """指数滑动平均(EMA),weight 越接近 1 越平滑。"""
    out = [values[0]]
    for v in values[1:]:
        out.append(weight * out[-1] + (1.0 - weight) * v)
    return out


# ---------------------------------------------------------------- 存档图数字化


def _cluster_1d(indices: np.ndarray, max_gap: int = 3) -> list[float]:
    """把（近似）连续的下标聚簇，返回各簇中心。"""
    centers: list[float] = []
    start = prev = int(indices[0])
    for idx in indices[1:]:
        idx = int(idx)
        if idx - prev > max_gap:
            centers.append((start + prev) / 2)
            start = idx
        prev = idx
    centers.append((start + prev) / 2)
    return centers


def _neutral_gray_mask(arr: np.ndarray) -> np.ndarray:
    """接近中性灰且明度 200-240 的像素（grid alpha=0.3 叠白底 ≈ (231,231,231)）。"""
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    mean = arr.mean(axis=2)
    return (mx - mn <= 8) & (mean >= 200) & (mean <= 240)


def _check_even_spacing(centers: list[float], what: str) -> None:
    diffs = np.diff(centers)
    if not (diffs.min() > 0 and diffs.max() / diffs.min() < 1.2):
        raise RuntimeError(f"{what} 网格线间距不是近似等差: centers={centers}")


def _calibrate(arr: np.ndarray):
    """检测网格线并拟合 像素列->iteration、像素行->value 的线性映射（两个子图）。"""
    neutral = _neutral_gray_mask(arr)
    h, w = neutral.shape

    # 水平网格线：整行出现大量灰像素
    row_centers = _cluster_1d(np.where(neutral.sum(axis=1) >= 0.4 * w)[0])
    # 按行间距把网格线分进各子图（子图内间距接近，子图间间隔明显更大）
    med = float(np.median(np.diff(row_centers)))
    groups: list[list[float]] = [[row_centers[0]]]
    for c in row_centers[1:]:
        if c - groups[-1][-1] > 1.8 * med:
            groups.append([])
        groups[-1].append(c)
    if len(groups) < 2:
        raise RuntimeError(f"水平网格线分组失败，期望 >=2 个子图组，得到 {len(groups)}: {row_centers}")
    ax1_rows, ax2_rows = groups[0], groups[1]
    if len(ax1_rows) != len(AX1_Y_TICKS) or len(ax2_rows) != len(AX2_Y_TICKS):
        raise RuntimeError(
            f"水平网格线数量不符: ax1={len(ax1_rows)}(期望{len(AX1_Y_TICKS)}), "
            f"ax2={len(ax2_rows)}(期望{len(AX2_Y_TICKS)})"
        )
    _check_even_spacing(ax1_rows, "ax1 水平")
    _check_even_spacing(ax2_rows, "ax2 水平")

    # 垂直网格线：只在 ax1 行带内统计，避开 ax3 不同的 x 刻度
    top, bot = int(ax1_rows[0]), int(ax1_rows[-1])
    band = neutral[top : bot + 1, :]
    col_centers = _cluster_1d(np.where(band.sum(axis=0) >= 0.5 * band.shape[0])[0])
    if len(col_centers) != len(X_TICKS):
        raise RuntimeError(f"垂直网格线数量不符: {len(col_centers)}(期望{len(X_TICKS)}): {col_centers}")
    _check_even_spacing(col_centers, "垂直")

    # 线性拟合 + 残差断言（防止错检网格线）
    x_coef = np.polyfit(col_centers, X_TICKS, 1)  # iter = a*col + b
    if np.max(np.abs(np.polyval(x_coef, col_centers) - np.asarray(X_TICKS))) > 2.0:
        raise RuntimeError(f"x 标定残差过大: coef={x_coef}, cols={col_centers}")
    y_coefs = []
    for rows, ticks, name in ((ax1_rows, AX1_Y_TICKS, "ax1"), (ax2_rows, AX2_Y_TICKS, "ax2")):
        coef = np.polyfit(rows, ticks, 1)  # value = a*row + b, a<0（行号向下增大）
        resid = np.max(np.abs(np.polyval(coef, rows) - np.asarray(ticks)))
        if coef[0] >= 0 or resid > 0.005 * (max(ticks) - min(ticks)):
            raise RuntimeError(f"{name} y 标定异常: coef={coef}, rows={rows}, resid={resid}")
        y_coefs.append(coef)
    print(
        f"grid calibration: vlines={len(col_centers)} spacing~{np.diff(col_centers).mean():.1f}px/250iter; "
        f"ax1 hlines={len(ax1_rows)} ax2 hlines={len(ax2_rows)}"
    )
    return x_coef, y_coefs, (top, bot), (int(groups[1][0]), int(groups[1][-1]))


def _extract_raw(
    arr: np.ndarray,
    color: tuple[int, int, int],
    row_lo: int,
    row_hi: int,
    col_lo: int,
    col_hi: int,
    x_coef: np.ndarray,
    y_coef: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """按颜色掩码逐列提取 raw 点线，每列取命中像素行的中位数，返回 (iterations, values)。"""
    dist = np.sqrt(((arr - np.asarray(color, dtype=np.float32)) ** 2).sum(axis=2))
    sat = arr.max(axis=2) - arr.min(axis=2)
    mask = (dist <= 70) & (sat >= 50)  # 排除网格灰与红区淡底色

    cols_out: list[float] = []
    vals_out: list[float] = []
    for col in range(col_lo, col_hi + 1):
        rows = np.where(mask[row_lo : row_hi + 1, col])[0]
        if rows.size == 0:
            continue
        med_row = row_lo + float(np.median(rows))
        cols_out.append(col)
        vals_out.append(float(np.polyval(y_coef, med_row)))
    if not cols_out:
        raise RuntimeError(f"颜色 {color} 未提取到任何 raw 像素")
    return np.polyval(x_coef, np.asarray(cols_out)), np.asarray(vals_out)


def _digitize_archive() -> tuple[np.ndarray, ...]:
    """数字化存档 PNG，返回 ax1/ax2 三条 raw 的 (iters, values) 并写缓存 CSV。

    缺口 405-450 在存档图里是跨缺口连线伪影，直接从结果中剔除。
    """
    arr = np.asarray(Image.open(ARCHIVE_PNG).convert("RGB"), dtype=np.float32)
    x_coef, y_coefs, ax1_band, ax2_band = _calibrate(arr)

    def col_of(it: float) -> int:
        return int(round((it - x_coef[1]) / x_coef[0]))

    col_lo, col_hi = col_of(HIST_LO - 10), col_of(HIST_HI + 10)
    grid = np.arange(HIST_LO, HIST_HI + 1)  # 插值到整数 iteration 网格
    keep = (grid <= int(GAP1[0])) | (grid >= int(GAP1[1]))  # 剔除 405-450
    grid = grid[keep]
    series: list[tuple[np.ndarray, np.ndarray]] = []
    for color, band, y_coef, name in (
        (TAB_BLUE, ax1_band, y_coefs[0], "train"),
        (TAB_ORANGE, ax2_band, y_coefs[1], "vision"),
        (TAB_GREEN, ax2_band, y_coefs[1], "action"),
    ):
        pad = int(round(1.2 * (band[1] - band[0]) / (len(AX1_Y_TICKS) - 1)))
        it, val = _extract_raw(arr, color, band[0] - pad, band[1] + pad, col_lo, col_hi, x_coef, y_coef)
        print(
            f"digitized {name}: {it.size} px columns, iter {it.min():.0f}..{it.max():.0f}, "
            f"value {val.min():.4f}..{val.max():.4f}"
        )
        series.append((grid, np.interp(grid, it, val)))

    with CSV_AX1.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iteration", "train_raw"])
        w.writerows(zip(series[0][0], series[0][1]))
    with CSV_AX2.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iteration", "vision_raw", "action_raw"])
        w.writerows(zip(series[1][0], series[1][1], series[2][1]))
    print(f"digitized cache written: {CSV_AX1}, {CSV_AX2}")
    return series[0][0], series[0][1], series[1][1], series[2][1]


def load_history() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """加载数字化历史 raw（有 CSV 缓存直接读，否则从存档 PNG 数字化）。"""
    if CSV_AX1.is_file() and CSV_AX2.is_file():
        d1 = np.genfromtxt(CSV_AX1, delimiter=",", names=True)
        d2 = np.genfromtxt(CSV_AX2, delimiter=",", names=True)
        print(f"digitized cache loaded: {CSV_AX1} ({d1.size} pts), {CSV_AX2} ({d2.size} pts)")
        return d1["iteration"], d1["train_raw"], d2["vision_raw"], d2["action_raw"]
    return _digitize_archive()


hist_it, hist_train, hist_vision, hist_action = load_history()
print(f"archived history used: {hist_it.size} pts, iter {hist_it[0]:.0f}..{hist_it[-1]:.0f}")


def _with_gaps(it: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """把历史序列嵌回完整整数网格，缺口处填 NaN 使 matplotlib 断线不跨缺口连线。"""
    full = np.arange(HIST_LO, HIST_HI + 1, dtype=float)
    out = np.full(full.shape, np.nan)
    lut = dict(zip(it.astype(int), v))
    for i, x in enumerate(full.astype(int)):
        if x in lut:
            out[i] = lut[x]
    return full, out


hist_x, hist_train_plot = _with_gaps(hist_it, hist_train)
_, hist_vision_plot = _with_gaps(hist_it, hist_vision)
_, hist_action_plot = _with_gaps(hist_it, hist_action)

# ---------------------------------------------------------------- LR 曲线

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

# ---------------------------------------------------------------- 绘图

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=False)
fig.suptitle(
    f"LIBERO 4in1 SFT (Edge-DROID warm start) — logs: iter 301-404 + 2751-{iters[-1]}; "
    "451-2004 digitized from archived PNG; 2005-2750 lost to log truncation; "
    "LR from resolved config (LambdaLinear)",
    fontsize=11,
)
for ax in (ax1, ax2):
    ax.axvspan(*GAP1, color="red", alpha=0.06)
    ax.axvspan(*GAP2, color="red", alpha=0.06)

ax1.plot(hist_x, hist_train_plot, "-", lw=1.0, color="tab:blue", alpha=0.75,
         label="train (archived raw 301-2004)", zorder=2)
ax1.plot(iters, total, ".-", ms=3, lw=0.8, color="tab:blue", alpha=0.5, label="raw")
ax1.plot(iters, ema(total), "-", lw=1.6, color="tab:blue", label="EMA(0.98)")
ax1.set_ylabel("train/loss")
ax1.legend()
ax1.grid(alpha=0.3)

ax2.plot(hist_x, hist_vision_plot, "-", lw=1.0, color="tab:orange", alpha=0.75,
         label="vision (archived raw 301-2004)", zorder=2)
ax2.plot(hist_x, hist_action_plot, "-", lw=1.0, color="tab:green", alpha=0.75,
         label="action (archived raw 301-2004)", zorder=2)
ax2.plot(iters, vision, ".-", ms=3, lw=0.8, color="tab:orange", alpha=0.5)
ax2.plot(iters, ema(vision), "-", lw=1.6, color="tab:orange", label="vision EMA(0.98)")
ax2.plot(iters, action, ".-", ms=3, lw=0.8, color="tab:green", alpha=0.5)
ax2.plot(iters, ema(action), "-", lw=1.6, color="tab:green", label="action EMA(0.98)")
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
