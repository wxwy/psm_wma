# PSM-WMA V3 — D1 R1 F1/F2/F3 定向 CPU 整改审核（增量）

**Date:** 2026-10-11
**Formal Verdict:** `D1_R1_REMEDIATION_PARTIAL_PASS / D1_GPU_HOLD`（剩余可执行 Harness+比较器静态 Gate）
**Implementation:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`（不变）。
**Previous:** `C1_RESTORE_PASS / C1_CLOSED`; previous D1 review `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_CPU_readiness_evidence_review_444c232b_e9b8a41.md`。
**Owner-relayed DS report:** `docs/collab/chatgpt/evidence/2026-10-11_V3_D1_R1/DS_PRO_2026-10-11_D1_F1_F2_F3_remediation_owner_relay.md`（原始 DS /tmp 脚本与原始 GPU JSON 未直接取得）。不得因 V3 Docs HEAD 变化重开 Formal implementation code review。

## 独立审计对象

固定 Child 定点源码已核对：
- `cosmos_framework/checkpoint/dcp.py:758-815`, `cosmos_framework/checkpoint/base.py:161-225`: Same-job 的 source 是现 Job `save_dirname/latest_checkpoint.txt`，而非单独指定 `load_path`。
- `cosmos_framework/trainer/local_memory_grouped_resume.py:231-253`: 完整五组件 Same-job 恢复 Guard。
- `cosmos_framework/trainer/local_memory_grouped.py:201-347`: 两 GA member 的真实 forward/backward+最后 optimizer step。
- `cosmos_framework/model/generator/mot/local_memory_grouped_window.py:79-191`: `begin/run_member` 建立/更新候选，`finish` 调 optimizer callback 后发布，`abort` 清理未发布候选。

## Dispositions

### F1 — PASS / CLOSED

DS 改为两条模式**顺序**使用已经 C1 证明隔离的单一 Shadow Root 和 `job.name=formal_verified_index_30k_shadow`，但使用不同 /tmp 日志，独立进程从相同 iter800 checkpoint 重新完整恢复。Shadow 的 own `save_dirname/latest_checkpoint.txt` 存在，因此 actual source 是 `warm_start=False`。训练原 Job 不得被初始化为任何试验 OutputRoot。无需复制两份额外24GB DCP，且不需要重做 C1。

### F2 — CONDITIONAL PASS (budget accounting corrected; actual F/B GPU memory unknown)

旧错误已承认并修复：~13.49GB model +11.40GB optim 是 **8 rank 磁盘 shard 合计**；C1 ~52–54GiB 是整卡 NVML 含另一个 `robotwin_server`。DS 6.47–6.56GiB matched per-device delta 可作为 C1 **Job 增量估计**，不是 `torch.cuda.max_memory_reserved()` 实测。D1 F/B 的 4–7GiB 额外和10.5–13.5GiB合计属于实验预算估计；历史 12.281GiB整卡 telemetry（其他上下文）仅作量级参照，不能转换为当前真实 F/B 峰值。

**Conditional GPU resource gate candidate:** 所有8卡实时 free>=25,000MiB，外部进程稳定且 owner 已允许该并行实验；一旦观察到外部压力/显存不足立即 fail-stop，不能终止 robotwin_server。主机每100ms NVML + rank CUDA max allocated/reserved，并区分 device total/proc owner。`24GiB reserved` 及 `78,000MiB device used` 可作为报警停止触发器，而不能保证预防 OOM（采样间隙内可能已经分配失败）。不得自动启用 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 或其他更改冻结运行语义的配置；这需要额外独立证据。禁止将 6.5GiB 估计冒充 torch allocator 数据。

### F3 — CONDITIONAL PASS (no-step seam valid, harness not yet executable-approved)

真实 `run_member` 的内/外损失计算、每个有效 index 的加权 native backward 和候选 Sidecar 更新与正式生产一致；`finish` 才调 slow optimizer 并发布 live。**这不是固定 Child 的 production bug**：正式 `training_step` 最后 member 调用 Optimizer Step 是预期训练行为；测试应采用外部 pre-step seam。不得把本 Harness 需求表述成要改生产训练链路。

但是 DS 提供的静态证据只有外部 **skeleton** 的编译、AST 函数名字和符号签名，而没有被完整验证的真正外部 **load-only + run_member closure** 程序。名称级 AST 不证明 `native_loss/backward`、正确 FSDP2 参数处理、callbacks/Autocast/torch.distributed、RNG、段顺序都已经接好。若直接启动8×H100可能重现 C1 的 Harness 非生产失败和重试。

**Numerical comparator blocker:** 被声明的 `P1:bf16 atol=rtol=1e-3` 不是“逐 dtype”完整冻结；fp32 gradients、near-zero、nonfinite、`grad=None` vs `grad=0`（包括四个 `w0_fast_*`）、FSDP2 shard身份与数值对齐必须固定规则，再运行 GPU。不能跑完看差异后改阈值。可将 `P0_BIT_EXACT` 与 `P1_NUMERIC_WITHIN_FIXED_TOL` 分开记录，不允许将失去 P0 视为完全相同的 bitwise 证明。

## Status and precise scope

- `F1_CLOSED`.
- `F2_BUDGET_CONDITIONAL_PASS` (GPU resource status must be measured at launch).
- `F3_PRESTEP_SEAM_ACCEPTED / F3_EXECUTABLE_AND_NUMERIC_CRITERIA_PENDING`.
- **Overall `D1_R1_REMEDIATION_PARTIAL_PASS / D1_GPU_HOLD`.** No evidenced new production code Bug, no C1 reversal or repeat.
- **Authorize one minimal parallel CPU-only prelaunch work cycle** at `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_final_CPU_harness_comparator_guard_authorization_444c232b_e9b8a41.md`: complete external runnable Harness statically, freeze/validate separate numeric comparator, freeze safe load/monitor/failstop launcher. No model/GPU until those are inspected.
- Do not preauthorize optional optimized-only optimizer step: a single unmatched step cannot establish optimizer-step parity. Actual D1 must first prove matched pre-step Loss/Gradient parity under actual 8-rank FSDP2; full step is separate, two-mode matched authorization if later needed.

`C1_CLOSED / D1_GPU_HOLD / E_F_HOLD / FORMAL30K_STOPPED`. Historical C1 four-attempt protocol deviation remains on record; never auto-retry after first GPU run exception.