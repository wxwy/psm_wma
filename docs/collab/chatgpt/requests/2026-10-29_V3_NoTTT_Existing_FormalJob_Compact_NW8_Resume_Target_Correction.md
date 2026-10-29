# Owner 目标纠正 — 原正式 No-TTT Job 的 Compact + DataLoader workers Resume

- 日期：2026-10-29；性质：Owner intent clarification / docs-only；**非正式GPU执行授权**。
- **唯一目标 Job**：`no_ttt_packed128_droid_fresh_30k_world4_ga4`。Owner 报告当前正式任务已训练到 iter7600+ 且仍在运行。不得在运行中启动第二个同 Job Resume、停机、覆盖 identity/checkpoint，亦不得把独立 Fresh10 Job 当成目标续训任务。
- **原错误提案撤销**：`2026-10-29_V3_NoTTT_Compact_FreshJob_Resume30k_Proposal.md` 的独立新 Job →30k 方向与 Owner 最新目标冲突，状态 `SUPERSEDED_NOT_AUTHORIZED`。原文保留审计，不再交 DS 执行。

## 事实与参数

- `NOTTT_LOADER_WORKERS` 才是真正的 No-TTT DataLoader spawn worker 数，合法 `0/1/2/4/8`，4 Rank 下 `nw8=32` worker 进程；launcher 的 `--num-workers 0` 是另一控制面，不代表 No-TTT DataLoader worker0。
- **Compact Fresh10 全部 `NOTTT_LOADER_WORKERS=0`**；GPU Paired Harness v2 不通过生产多-worker DataLoader；不能声称测试过最终组合。
- 原正式 No-TTT 性能日志历史窗口：nw0 iter101–590 的 Step Wall median 33.1s；nw8 iter701–1590 为32.2s，约1.03×，其数据等待减少但 host hidden work 增加。**当前 iter7600+ 的 worker 数未直接从实时日志核验**，DS 应只读检查当下进程/launch/telemetry，不能仅凭历史窗口断言仍是8。
- **建议目标候选为 `NOTTT_LOADER_WORKERS=8`**，配 `NOTTT_PREFETCH_FACTOR=1`、`NOTTT_PERSISTENT_WORKERS=1`、`NOTTT_LOADER_TIMEOUT_S=120`，以便优先对齐原 Job 的已有 nw8 历史；但 Compact 后最佳速度未知，不提前宣称 nw8 优于 nw0/nw4。这是推荐的**验收目标配置**，不是已批准的原 Job 热切换。
- Compact 目标开关 `PSM_V3_COMPACT_CACHED_VIDEO=1`；No-TTT world4 配置 `FSDP2/GA4/B8/T16` 与 `max_iter=30000, warmup=500, save_iter=100` 保持。

## 唯一后续执行路线（尚未获运行授权）

1. 原正式 Job 保持继续运行；DS 仅只读取得其当前 `NOTTT_LOADER_WORKERS`、实际运行版本、最近完整 Checkpoint 和训练健康信息，不干扰活进程。
2. 原 Compact CPU Parity 及数值结果原样保留：CPU CLOSED，严格 GPU 梯度 `FAIL_PARITY`、参照重复性不达阈值，Compact 特异性归因 `INCONCLUSIVE`。不要求重跑这些旧实验。将 `Compact=1 + nw8` 的真正生产 Loader/模型路径和原 Job 恢复路径作为尚未覆盖的验证范围。
3. 若能在隔离副本以完整原 Job Checkpoint 验证 `Compact0→1` 与适用的 nw 变化、严格身份/optimizer/scheduler/rank-local frontier/RNG/下一 committed step，则汇总结果供 Owner 决定正式切换；隔离副本必须保持合法 checkpoint/namespace 语义，不能修改原 Job identity 绕过校验。如果无法隔离，只报告阻塞，不擅停原 Job。
4. **仅在 Owner 明确批准**且原训练已在完整提交边界合法结束后，在**同 Job 名和原 namespace**执行 `resume 30000`。绝对不能 fresh、使用独立 Fresh10 namespace、从旧 checkpoint 回滚，或在原任务仍运行时并行 resume。保留旧 Job 同完整模型/优化器/调度器/4 Rank 数据 sidecar。恢复成功的首个 optimizer commit 必须是实际已提交迭代+1，未完成不得声称成功。

未来拟启用的参数（**仅说明，当前不能执行**）：

```bash
export JOB_NAME=no_ttt_packed128_droid_fresh_30k_world4_ga4
export PSM_V3_COMPACT_CACHED_VIDEO=1
export NOTTT_LOADER_WORKERS=8
export NOTTT_PREFETCH_FACTOR=1
export NOTTT_PERSISTENT_WORKERS=1
export NOTTT_LOADER_TIMEOUT_S=120
# 经Owner正式放行、原Job已合法退出且完整环境配置齐全后才可调用：
# bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 30000
```

- 旧正式 Job 当前迭代数和 nw 值由 DS 实时日志决定；本文件不制造“已经切换”或“已获30k授权”的事实。此前 Fresh10 的单步均值 20.32s 不是 `nw8 + Compact1` 的性能基准。
