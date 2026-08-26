---
name: cache-builder-script-location
description: 离线 latent cache 编码脚本位于根仓 tools/g0/，不在 cosmos-framework 子模块里
metadata:
  type: reference
---

用户说"之前是单独脚本编码的，你看下历史"。

**结论**：v2 分支上的 cache 编码是独立脚本，全部位于 **`/disk/rl/psm_wma/tools/g0/`**（根仓，非子模块）。我之前只在子模块 grep 搜 examples/scripts，所以漏了。

**核心脚本**：

| 文件 | 作用 |
|---|---|
| `tools/g0/exact_window_cache.py` | 17 帧 shared VAE 编码 helper（同一份契约供在线 guard 与离线 builder 用） |
| `tools/g0/build_cosmos_libero_latent_dataset.py` | LIBERO 离线 cache builder（`--windowed` 走 exact_window_v1 schema；4in1 4 suite 全量已用它跑过） |
| `tools/g0/build_cosmos_robocasa_latent_dataset.py` | RoboCasa 多根 atomic/composite 构建（用户决定暂缓） |
| `tools/g0/build_cosmos_rgb_latent_cache.py` | 旧 R12 单 episode latent builder（已 deprecated，对 exact_window_v1 发 `FutureWarning`） |
| `tools/g0/launch_parallel_cache_build.sh` | 4 suite 并行构建入口（4×5 shard） |
| `tools/g0/merge_latent_cache_shards.py` | 多 shard 合并 manifest |

**libero_90 编码**：直接复用 `build_cosmos_libero_latent_dataset.py --windowed --suite libero_90`。前提是 `LIBERO_LeRobot_v3/libero_90` 已在 v3.0 布局（`meta/tasks.parquet` + `meta/episodes/` + `data/chunk-*/file-*.parquet`），否则 loader 报 `FileNotFoundError`。

**契约历史**（避免再次踩坑）：
- builder 必须先 `(video*255).clamp().to(uint8)` 再 `VideoResize`，与在线训练 `_build_result()` 路径一致（float 域 vs uint8 域 bicubic 会差 0.11）
- builder 不要传 `encode_exact_durations=[17]`，让 VAE 走默认 causal padding，否则与在线差 0.03
- 训练 recipe 显式 `[trainer.cudnn] benchmark=false`，否则与 builder 进程 autotune 选择不同 → latent 偏 0.03

**已交付 4in1 cache**：`/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1/{libero_spatial,libero_object,libero_goal,libero_10}` = 432/454/428/379 episodes、246,377 窗口、54GB（Kimi 执行，Codex 审查）。