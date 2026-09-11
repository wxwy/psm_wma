# PSM-WMA v0.3.5 Canonical Native Production Runtime Integration 设计 v0.2

**日期**：2026-09-11  
**状态**：docs-only remediation；须获得本文件 formal root/child 三方同 SHA 批准后才可改 child。  
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-INTEGRATION-DESIGN`  
**替代关系**：本文件替代同 Gate 的 v0.1；v0.1 保留为已审核的历史草案。v0.2 不创建 superseding contract，而是从属于已冻结的 canonical native runtime source-audit design v0.2 进展顺序。

## 1. 目的与前置闭包

本 Gate 把已关闭的 canonical producer、scheduler/adapter、native consumer runtime、native forward/loss、runtime-owner 及 config/checkpoint 的 **CPU/static** 合同组织成后续真实运行设计入口；它不把任何 CPU/static witness 解释为真实训练授权。

权威输入为 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`、`PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_source_audit_design_v0.2.md`、`PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_source_audit_v0.1.md`、`PSM-WMA_Local_Memory_v0.3.5_canonical_native_forward_loss_source_audit_v0.2.md` 与 `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_integration_source_abi_audit_v0.3.md`。本设计的 formal review root 由审核申请明确声明；`bd6ea801367efc88e569c2cd4f9f62ebce2cdaeb`/`f49f568923555fe15efe546925cbe6cc9140170e` 仅为 v0.1 历史审核对，不再作为本版“当前 root”阅读锚点。

## 2. 不可跳过的冻结进展顺序

后续真实路径只能按既冻结的下列顺序建立；本文件不重排、不省略其中任何 Gate：

```text
runtime implementation design
  -> CPU/static implementation
  -> feature/config/optimizer/checkpoint refreeze
  -> single-GPU smoke design/approval
  -> single-GPU smoke
  -> runtime-sidecar design
  -> CPU/static verification
  -> resume smoke
  -> LIBERO4IN1 matched-smoke design/approval
  -> matched smoke
  -> formal-training design/command approval
  -> formal Local Memory training
```

每一箭头均须有独立 design、implementation 或 verification（依其语义）、三方同 SHA closure 与相应 formal root/child 审核。若需要不同顺序，必须先有独立 superseding contract，逐项重新冻结被重排或省略阶段的等强或更强验收边界；本文件未作该类替代。

不得将旧 row-wise marker、active-wiring、ordinary scalar `/grad_accum_iter` 或 synthetic seam 作为真实路径替代入口。

## 3. 真实 native integration 的冻结要求

本阶段的下一份 implementation design 必须显式冻结：

1. producer 仅从 frozen member 产生 stream-major valid rows；PAD 不产生 native sample，S0 产生 `prefix=None`；
2. gathered preparation 对每个 admitted feature 完整复现 ordinary 的 image-size resolution、per-camera raw-state 生命周期、VAE shape 与 memory hooks，未证明的组合在可逆 prepare 前拒绝；
3. logical consumer 到 vision item、dense action/sound、weighted item term 的 source mapping；不得用 unweighted per-instance 值替代 weighted consumer 项；
4. `consumer_loss` 与 LBL `auxiliary_loss` 分离，并仅经 `CanonicalGAWindowPlan.objective()` 完成一次 window scaling；canonical backward 不得再除 GA；
5. trainer callback、scaler、optimizer、scheduler、zero-grad 的 exact disposition。任何未支持的 disposition 必须在不可逆优化器边界前 abort exact capability、清受控 Local slow grads，并零 fast-state/scheduler/transaction commit；
6. feature/config/optimizer/checkpoint refreeze 必须在 single-GPU smoke design 前完成；sidecar 的 formal config/selector/owner/scheduler frontier/stream-slot 绑定、safe-boundary 写入、mid-episode resume、world-size change 与缺失或不一致 sidecar fail-closed，均仅在其后独立 runtime-sidecar Gate 定义、CPU/static 验证并经 resume smoke 证明。

## 4. 本 Gate 的分阶段授权边界

本 Gate 仅请求创建第 2 节首项的下一份 **CPU/static runtime implementation design**。其首批实现仍不得执行真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、真实 native forward/loss/backward、optimizer/scheduler step、sidecar write、训练、评测、推理或 LIBERO4IN1。

该 CPU/static implementation 的三方 closure 不自动授权后续项：必须先完成独立 feature/config/optimizer/checkpoint refreeze，再申请并获得 single-GPU smoke design/approval；single-GPU smoke 后再依次完成 runtime-sidecar design、CPU/static verification、resume smoke、LIBERO4IN1 matched-smoke design/approval、matched smoke，最后另行完成 formal-training design/command approval。只有最后一项批准后，才可申请正式 Local Memory training。

## 5. 审核请求

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_INTEGRATION
```

或 `REQUEST_CHANGES(file:line)`。本文件不授权任何 child 修改或真实执行。
