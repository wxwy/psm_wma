# ChatGPT 独立审核 — canonical CPU/static implementation design v0.2

日期：2026-09-08

## Verdict / formal target

**REQUEST_CHANGES**

- Gate：`G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`
- Formal root design SHA：`3e63a0d74f10326b6c5d514f5cfca32a689303be`
- child/Gitlink：`80aec090688e3c710c41e1dfd86b6500773db2c7`
- 审核时 V2 HEAD：`002b1d63575088135b634e6135ad3d532f299509`，仅 request/bookkeeping；不替代 formal target。
- 前一 formal target：`4874bfd223606e4d3b9335c4bc2490a088011c78` / same Gitlink。

本轮为新 formal pair 的 fresh incremental review。v0.1 的三个 ChatGPT blockers 均已关闭：

- B1 invalid-before-project：**CLOSED**。v0.2 明确禁止旧 `scan_segment_many()` 作为新 route 入口，并冻结 invalid-first compact-row scan。
- B2 `consumer_payload` ABI：**CLOSED**。v0.2 恢复 opaque payload，并冻结 payload/Local/identity 同 index gather。
- B3 current Gate literal：**CLOSED**。v0.2 唯一 implementation literal 已统一为 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC`。

## 当前 blocker

### NEW B4 — HIGH — feature-disable authority 与冻结 v0.3.6 明确冲突

- **file:line**：`docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.2.md:81-84`；关联 child `cosmos_framework/model/generator/mot/local_evidence.py:42-45`。
- **root cause**：冻结 v0.3.6 §7 明确规定 `EvidenceFeatureConfig(state=False, dt=False, age=False)` 必须在 **`LocalEvidenceEncoder` construction** 时真实移除 disabled branches，并要求不注册 `state_proj` / `dt_proj` / `age_embedding`、forward 不接受或读取对应 tensor。v0.2 却显式规定“既有 `LocalEvidenceEncoder` 完全不改”，另建 `SegmentEvidenceEncoder` 作为新 route encoder。当前 child 的 `LocalEvidenceEncoder` 仍无条件注册 `age_embedding` 与 `dt_proj`，因此该设计不是对冻结 authority 的实现，而是引入第二套 encoder authority；文档又未声明对 v0.3.6 §7 的经审核 supersession。
- **违反 frozen contract**：`PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md:125` 的 feature-disable construction contract，以及同节要求 implementation design 重新冻结 exact parameter inventory / optimizer membership / checkpoint config identity 的前置语义。当前 Gate 虽把 optimizer/checkpoint 接缝后置，但不能在未 supersede 合同的情况下把冻结 encoder owner 从 `LocalEvidenceEncoder` 静默改为 `SegmentEvidenceEncoder`。
- **可验收修复条件**：新 formal design 必须二选一并唯一化 authority：
  1. 按 v0.3.6 §7 让 `EvidenceFeatureConfig` 作用于 `LocalEvidenceEncoder` construction，同时冻结 legacy/default 调用如何保持既有行为，并把所需精确改动纳入白名单；或
  2. 若确需新 `SegmentEvidenceEncoder`，必须先在同一设计中明确、可追溯地 supersede v0.3.6 §7 的 encoder-owner literal，说明为何不形成 duplicate authority，并冻结新 route 的 exact parameter inventory 与后续 optimizer/checkpoint identity 绑定点。

  无论采用哪条，CPU acceptance 必须直接证明 canonical route 下 state/dt/age 参数不存在、forward 不接受/读取这些输入，且 legacy route 没有被静默改义。

## 其他核对

- formal root 的实际 Gitlink 已核对为 `80aec090688e3c710c41e1dfd86b6500773db2c7`。
- 实际 child `ContinualTTTLocalMemoryCore.scan_segment_many()` 确实会在 valid 分支前对 dense row 调 `project_evidence()`；v0.2 的 invalid-first masked seam 对上一 HIGH 的根因是有效整改。
- v0.2 的 `consumer_payload`、stream-major common gather、S0 `None` / PAD exclusion、rank-local metadata scheduler、GA planned==actual、episode-vs-slow-LR skip 语义未发现新的独立 blocker。
- v0.3.8/v0.3.9 的 recovery taxonomy 与 plan-chain retry budget继续作为继承合同；本轮未把其简写重新解释为新 supersession。
- 本 Gate 为 docs-only design review；未运行项目代码/测试、GPU、真实数据、模型或 checkpoint。

当前合计：**1 HIGH design blocker**。

当前 Gate 不关闭，不授权四文件 CPU/static implementation，也不授权 production adapter/forward/trainer/dataset/projector/config/optimizer/checkpoint 修改、真实 preflight/staging/record/refreeze/export/compose、真实 I/O、CUDA/GPU/torchrun、训练、评测、推理、P4/P5、B2-T、LIBERO4IN1 或任何后续 Gate。

Detailed review 与 canonical Inbox 同时持久化后，本 `REQUEST_CHANGES` 才构成正式 verdict；review/bookkeeping SHA 不改变 formal pair。
