# DS_PRO — V3 D1 R1 定向整改：三个 CPU-only 工作流并行

**日期:** 2026-10-11
**Authority:** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_CPU_readiness_evidence_review_444c232b_e9b8a41.md`.
**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`; **Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Verdict before execution:** `D1_R1_REQUEST_CHANGES / D1_GPU_HOLD / C1_CLOSED / FORMAL30K_STOPPED`.

本轮只补三个定点设计问题；**可以并行**，一次性汇总，不等待 GPT 中途验收。它不是新一轮全量 Dataset/C1 审计，也不是授权 8×H100 试验。

## Task F1 — CPU/static 修复严格 same-job Shadow 路径

- 使用固定 Child 的生产源码核查 `DistributedCheckpointer.keys_to_resume_during_load` 与 `require_dcp_grouped_resume_component`；说明为什么新的 `d1_shadow_singlestep_ref/opt` job 仅凭 `load_path` 不能直接 same-job 严格恢复。
- 优先制定**同一已验收的独立 C1 Shadow Job**、**ref 和 opt 两次顺序启动**的方案：保持 `IMAGINAIRE_OUTPUT_ROOT=<C1_SHADOW_ROOT>`，`job.name=formal_verified_index_30k_shadow`，其 `save_dirname/latest_checkpoint.txt` → iter800，`source.warm_start=False`、keys 全五组件，`strict_resume/load_training_state=True`；两个模式的 `/tmp` 外部日志及诊断产物完全独立。每次都从原样 iter800 **重新实例化模型和加载相同 RNG/fast state**；不能从第一次梯度/内存/候选状态直接接第二次。
- 明确本 Shadow Job 的 `config.yaml/config.pkl` 在 Trainer constructor 可改写（仅 Shadow 可写），且每次执行前后保护并记录 `checkpoints/latest_checkpoint.txt` 和 iter800 元数据、Sidecar 字节不变；原 Formal30k 是第三方不可写原始源。不得通过 symlink/hardlink 指向原 Job，也不得改写原 DCP。
- 本轮 **只做 CPU-only 路径推导、dry-run read-only source resolution**，不执行 Trainer ctor、DCP load、torchrun 或复制 24GB；将路径/args/env/source type/五组件及 realpath witness 形成执行准备方案。

## Task F2 — CPU-only 重算显存预算，不混 GPU global/device/process 或 rank totals

- 抽取现有 G0/C1 P4 per-rank JSON/既有正式旧训练 Telemetry 若可用，分别列出 **整卡 global used/free incl robotwin_server**、**自身进程 CUDA max allocated/reserved**（仅真实报告有则列；没有标 unknown）、以及 checkpoint **per-rank disk shard** (model ≈1.685GB, optim≈1.424GB) 与 8-rank aggregate (≈13.48GB / ≈11.39GB)，不得把 aggregate 当 per-card。
- C1 的 global 52,051–53,819MiB 与外部 baseline 45,581–47,263MiB 只能导出非同步观测的粗 own-process increment 范围，不能冒充 FSDP2 实际 allocator peak，不能据此认证 Forward/Backward 安全性。
- 重新给出模型/selected grads/activation/Local scan/workspace 的内存未知项、依据、保守安全余量，明确是否有足够**实测来源**支持 D1 下一 GPU 启动；若无则标 `D1_RESOURCE_BLOCKED`，提出不扰动 robotwin_server 的可行负载窗口/owner 调度条件。不得随意发明 33.5GB 启动阈值或进程 76GB cutoff、修改环境优化开关来减少显存压力。
- 仅做 CPU `nvidia-smi` 与已有日志读取，不启动 CUDA、模型加载、GPU 测试或影响他人进程。GPU free 的一次性读数不代表锁定资源。

## Task F3 — CPU/static 将 no-Optimizer-step 梯度 Harness 设计落到真实生产调用点

- 依据 `cosmos_framework/trainer/local_memory_grouped.py:201-347` 与 `cosmos_framework/model/generator/mot/local_memory_grouped_window.py:79-191`，给出精确的外部 Harness 调用序列：严格 iter800 5组件 restore → real `GroupedLocalMemoryWindow` with restored live → `window.begin` → two `run_member` using **同生产** SegmentProducer、`collate_grouped_native_batch`、`move_cached_native_batch`、`model_ddp.training_step`、`grad_scaler.scale(loss).backward` 等闭包，累积全部 16 index 有效 consumer 的 weighted loss 和 FSDP gradients → pre-step finite checks/gradient+Local candidate capture → `window.abort` / process exit；禁止 `window.finish`、`trainer.training_step` 最终 GA 成员、`optimizer.step`、`scheduler.step`。
- 明确真实权重 `len(batch.payloads)/plan.n_window`、local candidate 更新事务、`model.on_after_backward` / loss callback / registered FSDP2 scan 等接线，及是否任何改变会令 Harness 不再等价于 production pre-step objective。不能只声称数学上可截停。
- 给出 CPU 静态预检清单：syntax/AST（特别验证没有 `train()` / `finish()` / optimizer/save 调用）、真实生产符号/路径/shape/ABI、2 GA request 及已恢复 source/frontier 预期字段、每 rank exact logs/exception 的创建发生在 torchrun 前。**本轮禁止运行 4B/H100**。允许在 /tmp 创建/编译外部 Harness **静态源文件**，不修改 production/test/launcher。
- 每种 dtype（bf16/fp32）分别冻结 tolerance 和 max_abs/max_rel/nonfinite 比较方法、Loss 权重/归一化尺度及 w0 四梯度 present/zero/None 的正确判据。未来若要验证 Optimizer Step，需**两模式各自 matched step** 且单独授权，不接受只 Optimized 做 Step 却声称整体 step parity。

## Common safety, concurrency and handoff

- F1/F2/F3 独立 CPU-only 并行，各自外部新 `/tmp` Evidence 目录，复用已有 P2/P4/C1 和 D1 R1 evidence。严禁重复整个 B1/B2/C1 Gate、VAE、Index、全量 dataset scan。
- 不允许 GPU 模型、CUDA 初始化、torchrun、真实 Checkpointer.load、forward/backward 或 Trainer/Otimizer/Scheduler step；不允许复制/改写任一原 DCP / latest、任何生产源码、git reset/clean、覆盖 MM Notes 或他人任务。
- 如果某项失败/证据缺失，保持该项 `BLOCKED`，独立的其他 CPU 项可完成；保存第一处异常，不自动 retry、不能事后放宽容差。
- 输出一份 `DS_PRO_V3_D1_R1_TARGETED_CPU_REMEDIATION_2026-10-11.md`，单独列 `F1/F2/F3 PASS/FAIL/BLOCKED`，给准确 source/sha、改后的 same-job 方案、显存指标与资源结论、可运行但未启动的 no-step Harness static call graph，以及未来单个 paired D1 GPU 试验的可行条件。
- **STOP after combined report**。D1 GPU、E/F 和 Formal30k Resume 继续 HOLD；由 GPT 审核后给下一步。