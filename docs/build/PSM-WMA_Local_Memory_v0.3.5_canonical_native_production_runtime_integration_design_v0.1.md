# PSM-WMA v0.3.5 Canonical Native Production Runtime Integration 设计 v0.1

**日期**：2026-09-11  
**状态**：docs-only；须获得本文件 formal root/child 三方同 SHA 批准后才可改 child。  
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-INTEGRATION-DESIGN`

## 1. 目的与前置闭包

本 Gate 把已关闭的 canonical producer、scheduler/adapter、native consumer runtime、native forward/loss、runtime-owner 及 config/checkpoint 的 **CPU/static** 合同组织成下一阶段的真实运行设计入口；它不把任何 CPU/static witness 解释为真实训练授权。

权威输入为 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`、`canonical_native_forward_loss_source_audit_v0.2.md`、`canonical_segment_production_integration_source_abi_audit_v0.3.md`。当前 root=`42fcfce1acffab05e9bce58bbf92667a92c00244`、child=`f49f568923555fe15efe546925cbe6cc9140170e` 仅是本设计阅读锚点。

## 2. 唯一集成链与不可跳过的 Gate

后续真实路径只能按下列顺序建立：

```text
immutable episode-stream producer
  -> frozen CanonicalGAWindowPlan / stream-major valid gather
  -> canonical native preparation parity
  -> native pack/noise/hooks/denoise
  -> source-identified weighted per-consumer loss + independent auxiliary
  -> exact one-backward capability / canonical runtime owner
  -> optimizer-boundary disposition
  -> durable sidecar + checkpoint resume
  -> bounded single-GPU smoke
  -> matched LIBERO4IN1 training gate
```

每一箭头均须有独立 design、implementation、CPU/static closure，且真实 I/O/GPU gate 必须以相应实现 formal SHA 重新审核。不得将旧 row-wise marker、active-wiring、ordinary scalar `/grad_accum_iter` 或 synthetic seam 作为替代入口。

## 3. 真实 native integration 的冻结要求

下一份 implementation design 必须显式冻结：

1. producer 仅从 frozen member 产生 stream-major valid rows；PAD 不产生 native sample，S0 产生 `prefix=None`；
2. gathered preparation 对每个 admitted feature 完整复现 ordinary 的 image-size resolution、per-camera raw-state 生命周期、VAE shape 与 memory hooks，未证明的组合在可逆 prepare 前拒绝；
3. logical consumer 到 vision item、dense action/sound、weighted item term 的 source mapping；不得用 unweighted per-instance 值替代 weighted consumer 项；
4. `consumer_loss` 与 LBL `auxiliary_loss` 分离，并仅经 `CanonicalGAWindowPlan.objective()` 完成一次 window scaling；canonical backward 不得再除 GA；
5. trainer callback、scaler、optimizer、scheduler、zero-grad 的 exact disposition。任何未支持的 disposition 必须在不可逆优化器边界前 abort exact capability、清受控 Local slow grads，并零 fast-state/scheduler/transaction commit；
6. sidecar 必须绑定 formal config/selector/owner/scheduler frontier/stream slots；mid-episode resume、world-size change、缺失或不一致 sidecar 均 fail closed。

## 4. 分阶段授权边界

本 Gate 仅请求创建下一份 **CPU/static implementation design**，且其首批实现仍不得执行真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、真实 native forward/loss/backward、optimizer/scheduler step、sidecar write、训练、评测、推理或 LIBERO4IN1。

只有 CPU/static 实现三方 closure 后，才可新建 runtime-sidecar/real-I/O design；只有该设计及其实现 closure 后，才可申请 bounded single-GPU smoke；正式训练必须使用另一个 matched-training Gate。

## 5. 审核请求

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_INTEGRATION
```

或 `REQUEST_CHANGES(file:line)`。本文件不授权任何 child 修改或真实执行。
