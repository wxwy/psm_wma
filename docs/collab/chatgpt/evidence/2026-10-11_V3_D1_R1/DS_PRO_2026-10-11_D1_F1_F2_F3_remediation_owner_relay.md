# DS_PRO — V3 D1 R1 F1/F2/F3 定向 CPU 整改：Owner-relayed Evidence

**DS report date:** 2026-10-11
**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e` / **Child+Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`。
**Previous Gate:** `C1_RESTORE_PASS / C1_CLOSED`.
**Authority:** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_targeted_parallel_CPU_remediation_authorization_444c232b_e9b8a41.md`.
**Source/provenance:** 用户转交的 DS_PRO 97 行汇总报告，附带对 DS 主机 `/tmp` 设计文档与骨架的引用；GPT **未直接读取**这些 DS /tmp 文档、脚本或监控原始 JSON。因此本文保留 DS 自评 PASS，并通过独立 Review 划分已支持/未支持的结论。

## 1. 执行范围

DS 声明 F1/F2/F3 全部 CPU-only 并行，无 GPU/torchrun/DCP Load/Forward/Backward/Optimizer Step/DCP Save/Fresh/Formal Resume/生产代码改动，原正式 `formal_verified_index_30k` STOPPED；临时 Evidence 根 `/tmp/ds_pro_v3_d1_r1/{f1,f2,f3}/`。

冻结配置：world8、T16、B8、GA2、K4、Hpred16、raw15、left_wrist、use_state、num_workers0、max_iter30000、warmup500、save_iter100；Config Digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`。

## 2. F1 — Same-job Shadow 路径修复（DS verdict PASS）

- 确认此前两个新 Job 仅设置 `load_path=<shadow iter800>` 但没有各自的 `save_dirname/latest_checkpoint.txt`，会走 `warm_start=True`，不满足 Local Same-job 恢复。
- 修正采用**同一个已在 C1 验证的 Shadow Root** `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/` + `job.name=formal_verified_index_30k_shadow`，其 `checkpoints/latest_checkpoint.txt` → `iter_000000800`。参考/优化两次顺序启动、分别独立 Python/torchrun 进程和 /tmp 日志路径，每次重新严格载入相同 iter800 的全部 model/optim/scheduler/trainer/dataloader/RNG/Local State。明确允许仅在 Shadow 内写 config.pkl/yaml，不可写 Shadow DCP 或原 Formal Job。
- C1 已有 8/8 ranks source `warm_start=False`、full keys 和 `n_diffs=0` 的前验 Evidence；本轮仅静态方案，不额外 DCP Load。

## 3. F2 — Memory budget 口径修复（DS verdict PASS）

- 旧 D1 R1 以“每 rank 53.9 GB”混淆 GPU 全局已用、DCP 8 rank 磁盘 shard 合计和本进程内存，DS 明确撤回。
- 更正 DCP model shards **合计**约 13,486,462,029 bytes（每 rank≈1,685,807,754B ≈1.57GiB）；optim shards **合计**约 11,399,340,240B（每 rank≈1,424,917,530B ≈1.33GiB）。磁盘 shard 大小本身**不等于** torch CUDA allocator 驻留内存。
- C1 `nvidia-smi` 整卡基础 used=45,580–47,263MiB（其他 `robotwin_server`），Load-only 全局 used 峰值 52,051–53,819MiB；DS 逐卡配对差分估算 own-job 增量约 6,470–6,556MiB。**这是 NVML device-level difference estimate，不是实际 `max_memory_allocated/reserved` 测值**。
- F/B 新增约 4–7GiB/rank 是模型/梯度/activation 组件估算，不是测量；推断 single-window 约 10.5–13.5GiB/rank，历史 `SESSION.md:660` 报某 soak 12.281GiB/device（只作其他上下文参考，不是这次同一外部工作负载条件的直接基线）。
- DS 推荐启动 GPU free≥25,000MiB、单进程 reserved>24GiB 和整卡 global used>78,000MiB 报警/停止，并行每100ms GPU 监控；这些阈值属于**提议的保守试验限额，不代表无 OOM 保证**。DS 同时提及 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`，未经验证冻结作业之前是否使用，不能自动添加到 D1。

## 4. F3 — 无 Optimizer Step 的生产调用点与静态 Harness（DS verdict PASS）

- DS 正确追踪 `GroupedLocalMemoryTrainer.training_step` 最后 GA member 会进入 `window.finish` 并最终调用 optimizer/scheduler step。为证明 pre-step parity，拟用外部 Harness 调 `GroupedLocalMemoryWindow.begin() → run_member(GA0) → run_member(GA1) → capture → abort()`，不调用生产 `training_step` 最后成员或 `finish`。
- `run_member` 本身使用真实 `ExactWindowSegmentProducer`、`collate_grouped_native_batch`、`move_cached_native_batch`、`model_ddp.training_step`、`grad_scaler.scale(weighted_loss).backward`、`model.on_after_backward()`，加权为 `len(batch.payloads)/plan.n_window`，候选 Sidecar 更新但不发布。
- 测量拟包括每 member 原生 loss/加权 loss、Generation/Action/Local（特别四个 `w0_fast_*`）grad、FSDP2 local shard hash、候选 Local fast state、RNG/optimizer/scheduler 指纹、时间/资源及参数未更新证明。
- DS 生成**骨架** `/tmp/ds_pro_v3_d1_r1/f3/no_optimizer_harness_skeleton.py`，执行 `py_compile` + AST 方法调用名称扫描（begin/run_member/abort 存在、finish 缺席）+ 关键生产函数 import/signature 检查，报告 `STATIC CHECK: PASS`；**未提供已可安全运行的完整启动程序及其完整 closure 接线验证**。
- DS 给定 `P0` bit-exact；`P1` 单独写 bf16 loss/grad `atol=rtol=1e-3`；未见 fp32 累加梯度及接近零值的独立阈值与异常判据。优化端建议添加单独 optimizer step，但尚不属于当前无 Step parity 合同。

## 5. 源文档位置与停止状态

- `/tmp/ds_pro_v3_d1_r1/f1/f1_same_job_shadow_restore.md`
- `/tmp/ds_pro_v3_d1_r1/f2/f2_gpu_memory_budget.md`
- `/tmp/ds_pro_v3_d1_r1/f3/f3_no_optimizer_step_harness.md`
- `/tmp/ds_pro_v3_d1_r1/f3/no_optimizer_harness_skeleton.py`、`f3_static_check.py`

DS 最终自评 F1/F2/F3 PASS，请求单个 matched D1 GPU 检查。**GPT 正式增量 Review** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_F1_F2_F3_remediation_evidence_review_444c232b_e9b8a41.md` 及下一轮精准 CPU prelaunch authority `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_final_CPU_harness_comparator_guard_authorization_444c232b_e9b8a41.md`。目前无人声明完整真实 F/B GPU parity 已运行；正式 Formal30k 原 Job 保持 STOPPED。
