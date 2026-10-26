# PSM-WMA V3 Matched No-TTT — workers 数量不属于训练 Resume Identity

**日期：2026-10-26。候选分支 `v3-nottt-worker-agnostic-resume-20261026`。未合并 V3、未完成独立 CPU/真实 DCP/CUDA 验收、禁止直接变更运行中的训练。**

## 用户最终冻结要求（取代 Issue #5 早前错误的“跨 Worker Checkpoint 迁移”假设）

`NOTTT_LOADER_WORKERS` 可在 0/1/2/4/8 之间选取，**包括相同 No-TTT Job 的 Fresh→Resume 和两次 Resume 之间切换**。worker count、prefetch factor、persistent flag、timeout 是 **CPU DataLoader 的运行时执行参数**，不是 optimizer、模型、scheduler、GA/RNG、sample stream/frontier/checkpoint 的持久训练语义，因此不得以“旧新 nw 不同”为由阻止正确 Resume。

此约定 **只适用于 Matched No-TTT world4 GA4 B8 T16**，不改变 G1、Local-TTT 的线程 `--num-workers` 语义，也不代表原生 Cosmos 官方 DataLoader 的 worker 参数已经自动接入 Matched No-TTT；后者仍由 Codex 的真正 spawn CPU DataLoader adapter 处理。

## 代码契约

- Root `scripts/train_v3_matched_no_ttt_4gpu.sh`: `nw=0/1/2/4/8` 默认0，**原 Job name 始终** `no_ttt_packed128_droid_fresh_30k_world4_ga4`；保留 `--num-workers 0`（不同控制面），新增 `--no-ttt-loader-workers` 参数只在 nw>0 出现。不得再强制新 `_mpwN` namespace。
- Child `cosmos_framework/utils/no_ttt_loader_profile.py`: 只验证 worker 合法值与 world4/GA4/B8/T16/NoTTT Job 范围，不比较旧 nw。
- Child `examples/psm_wma_robocasa_corrected_phase5.py`: `no_ttt_cpu_loader` 不再加入 `training_identity`、`config_digest` 与原 Job `v3_job_identity.json`。在新 launch/telemetry 中记录 **nw>0 的 CPU Loader runtime profile**，旧 nw0 的快照格式不增加字段。硬性模型、优化器、数据/cache/index、seed、rank/world/GA、配置 digest、canonical config 校验不变。
- Child `cosmos_framework/trainer/matched_no_ttt.py`: `NoTTTFrontierCallback` 对全部 nw 写入与原正式 workers0 兼容的 `psm_v3_matched_no_ttt_frontier_v1`，精确保存 rank/seed/world/B/GA/T、source/cache/config、Frontier 与 committed iteration，不写 loader profile。恢复时不忽略、修改或“迁移”任何旧 Frontier 状态；所有硬校验仍 fail closed。
- 新 Loader 的 CPU spawn、缓存/RNG、ordered segment、parent Transform、model/optimizer/DCP 操作路径保持独立。不得把未完成的后台队列状态写进 Checkpoint，失败时回到最新完整 committed checkpoint。

## 启动：现有 nw=0 Job 从最后 Checkpoint 改用 nw=8 继续（**验收通过后再执行**）

沿用已经设置好的 `OUTPUT_ROOT SOURCE_ROOT CACHE_ROOT DATASET_INDEX_ROOT EDGE_POLICY_CHECKPOINT WAN_VAE_PATH BASE_CHECKPOINT_PATH` 及原训练 Python 环境、原世界规模与 GPU 4–7。必须保持 Job 名称和所有训练配置不变：

```bash
NOTTT_LOADER_WORKERS=8 \
NOTTT_PREFETCH_FACTOR=1 \
NOTTT_PERSISTENT_WORKERS=1 \
NOTTT_LOADER_TIMEOUT_S=120 \
JOB_NAME=no_ttt_packed128_droid_fresh_30k_world4_ga4 \
bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 30000
```

- `resume` 从 **同 Job** 的 `checkpoints/latest_checkpoint.txt` 获取真实迭代，加载完整 model/optim/scheduler/trainer + `dataloader/rank_0..3.pkl`，不是 Fresh DROID model-only、不是新 Job、不是再额外训练30000。
- `nw=8` × 4 Trainer ranks = 最多32 CPU Worker 进程；prefetch1 先行验证 RAM/IO、step-wall。增加 nw 不保证速度更快。
- **不允许在仍运行的旧 Job 上同时启动 Resume**；旧训练运行状态未知，先经 DS 的隔离复核/真实 DCP Gate，再安排受控停止和恢复。

## 最小必要验收，禁止过度重复

1. **合成 CPU，身份 + 历史兼容：** 原 `nw0` Job 的正式语义 digest/Frontier 对新 `nw8` 不变；旧 nw0 状态→新 nw8 恢复、其它组合 `8→0`/`2→8`；四逻辑 rank、full/terminal、next consumer/transform/RNG/weighted loss/grad/optim/frontier parity；改 rank、seed、model/data/config/Frontier 必须拒绝。复用已验收的 B1 历史证据，不重跑与本改动无关的601条用例。
2. **DS_PRO 独立 CPU:** clean detached exact Root/Child+Gitlink、相关测试及原始 JUnit、静态 checks。
3. **目标环境真实 DCP/CUDA Gate:** 在**隔离保护**的真实 Checkpoint/输出目录上加载 old nw0 DCP 用 nw8 恢复一小段，核对 optimizer/scheduler/CUDA RNG/rank Frontier、resume iteration与精确下个 batch；不碰原 Job。只有此 Gate 通过，才能启动生产级 Resume。

早前 Issue #5“必须迁移 Checkpoint”表述被用户新决定**否决**。这里不实现 Checkpoint converter，不重写旧 identity，不放宽模型/数据/优化器/Frontier 硬校验。旧候选 `_mpwN` 专用 Job/格式如果已生成 checkpoint，须单独审查兼容性；当前活动正式 Job 是 workers0。
