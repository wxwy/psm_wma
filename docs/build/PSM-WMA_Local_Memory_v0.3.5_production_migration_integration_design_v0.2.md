# PSM-WMA Local Memory v0.3.5 Production Migration Integration Design v0.2

**日期**：2026-09-08  
**状态**：docs-only；未授权代码、真实 I/O、GPU 或训练  
**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-MIGRATION-DESIGN`

## 1. 唯一 authority 与 supersession

`PSM-WMA_Local_Memory_v0.3.5_supersession_migration_design_v0.1.md`（root `6828b55`）是历史输入，现明确 superseded，零 implementation authority。不得重新定义其旧 `SegmentBatch`、`scan_segment_many()`、scheduler、GA 或开启第二条 CPU implementation 路线。

本设计绑定 current child Gitlink `0fddc27f9c3c463f784be9f528ffbbe123f244ff`；唯一语义源为 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`、canonical v0.3.6--v0.3.9 及已关闭的 v0.3.9 CPU/static core。冲突时以后者为准。

## 2. 已关闭与剩余边界

已关闭 synthetic CPU/static core；不得重做或替换。剩余 Gate 只设计 production adapter、trainer backward/GA seam 与 runtime-sidecar integration：以 canonical `SegmentBatch` 的 opaque `consumer_payload`、shifted previous-evidence source chronology、invalid-first `scan_segment_masked_many()` 为输入；保留 `RankLocalSegmentScheduler` stable slot/terminal/rebind/admission、`GAWindowPlan` planned==actual、suffix-only retry taxonomy、partial slow-grad disposition，以及 construction-time state/dt/age feature-disable owner/inventory。

## 3. 后续 implementation-design 白名单与验收

下一份 implementation design 必须冻结精确文件白名单、调用次序、synthetic consumer spy、backward 后 commit、异常/GradScaler-skip rollback、disabled parity 与 no cross-microbatch TTT graph。它不得重定义 CPU core。只有该 design 获三方批准后，才可作 CPU/static production-adapter 实现；其新 SHA 仍须复审。

## 4. 禁止范围

本文件及其审核不授权 child 代码、registry/defaults、真实 checkpoint/data/cache I/O、CUDA/GPU/torchrun、训练/评测/推理、P4/P5、B2-T 或 LIBERO4IN1。GPU smoke、matched smoke 与正式训练均须各自独立三方 Gate。
