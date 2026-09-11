# PSM-WMA v0.3.5 Canonical Native Production Runtime CPU/static Implementation 设计 v0.1

**日期**：2026-09-11  
**状态**：docs-only；须本文件 formal root/child 三方同 SHA 批准后才可修改列出的 child 文件。  
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-CPU-STATIC-IMPLEMENTATION-DESIGN`

## 1. 前置 authority、范围与禁止项

本设计的唯一前置为已关闭的 `G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-INTEGRATION-DESIGN`：formal root `ee979172b8bef4709e94fe84ed4ff4e9c711e2e7` / Gitlink `f49f568923555fe15efe546925cbe6cc9140170e` 已获 ChatGPT、MM、Kimi 同 SHA `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_INTEGRATION`。它从属于该 Gate 恢复的完整 progression，不重排 feature/config/optimizer/checkpoint refreeze、single-GPU smoke、runtime-sidecar/resume、LIBERO4IN1 matched smoke 或 formal-training 节点。

本 Gate 仅授权下一阶段的 **single-process / world-size-1 synthetic CPU/static implementation**。允许的 child 白名单为：

```text
cosmos_framework/model/generator/omni_mot_model.py
cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py
cosmos_framework/trainer/__init__.py
cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py
cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py
cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py
```

禁止修改配置、checkpoint/sidecar、数据/packer、flow-matching 算法、注册表或生产启动命令；禁止真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、真实 native forward/loss/backward、real `torch.optim.Optimizer` step、scheduler step、sidecar write、训练、评测、推理和 LIBERO4IN1。若实现需要白名单外 source 变化或任一真实执行，必须 fail closed 并另起 design Gate。

## 2. 当前 source truth 与最小替换边界

`omni_mot_model.py:1422-1464` 已完成 exact carrier preflight、adapter scan、native-safe preparation、gather identity 校验和 `CanonicalNativeForwardCapability` 绑定；但 `:1459` 只能消费 injected `_psm_canonical_native_cpu_static_loss_split` test seam。`trainer/__init__.py:986-1045` 只允许 disabled scaler / non-Optimizer CPU static double，并由 `CanonicalGAWindowPlan.objective()` 完成一次 backward 与 exact capability/commit 处置。

实现不得“解除 hard-stop 后调用真实模型”。它只能把当前已经存在的 preparation/loss/capability contracts整理为以下可观察、可拒绝的 CPU/static native-runtime boundary：

```text
exact frozen request + raw carrier
  -> scan / stream-major gathered traversal
  -> model-safe canonical preparation (no pack/noise/denoise)
  -> source-identified typed native loss inputs
  -> CanonicalNativeLossSplit
  -> one exact CanonicalNativeForwardCapability
  -> plan.objective() -> one disabled-scaler backward
  -> prepare_commit / commit_success, or exact abort
```

任何缺失 injected CPU/static typed terms、foreign/stale capability、actual/planned count 不等、重复消费、ordinary scalar `/grad_accum_iter`、enabled scaler、真实 optimizer、distributed topology 或 post-mutation failure，均必须在不可逆 commit 前 fail closed；不得降级到 legacy row-wise Local 或 ordinary No-Local path。

## 3. 实现合同

1. **Preparation parity owner**：模型仅可复用 `_prepare_canonical_production_inputs()` 已完成的 gathered image-size、per-camera raw-state、sequence plan、memory prefix 与 VAE-shape preparation；adapter 的 `attach_native_preparation()` 必须继续对 exact pending scan、cardinality、S0 `prefix=None` / non-S0 prefix present 和 working-copy ownership 验证。PAD 无 plan、prefix、loss 或 state mutation。
2. **Typed loss owner**：只由 `build_prepared_canonical_native_loss_split()` 及其 `CanonicalNativeModalityTerms` 将 vision/action/sound 的 already-weighted per-instance populations 映射到 gathered consumer ownership；`consumer_loss` 保留原 modality weight 与一次 sample-level scale，`auxiliary_loss` 只能是独立 LBL 项。禁止以 native total loss 或 unweighted instance mean 替代。
3. **Window algebra**：在 trainer 唯一使用 `request.plan.objective(member_index, consumer_loss, auxiliary_loss, actual_n_valid)`；每个 normal 或 suffix-recovery member 在 backward 前要求 `actual_n_valid == planned_n_valid[member_index]`。normal 与 recovery 均须使用非等 planned valid count、非零 auxiliary 的数值 witness，精确断言 `planned_n_valid / N_window * consumer_loss + auxiliary_loss / GA_effective`，并断言无 ordinary `/GA` 或第二次 scaling。full-valid normal 的 `(L_consumer + L_aux)/GA` 是附加不变量，不替代该 witness。
4. **Exact capability / failure owner**：adapter 只能 bind/consume/abort 同一 pending scan 的 `CanonicalNativeForwardCapability`；成功路径一回 `prepare_commit`、一回 `commit_success`。forward、pre-backward、loss-build、prepare-commit 与 pre-mutation commit failure 必须清 controlled Local slow grads、abort exact capability/scan、terminalize 且零 frontier/scheduler/transaction reconcile；跨 mutation boundary 的故障保留证据并拒绝自动重试。
5. **Topology / optimizer boundary**：本 Gate 继续在 callback、model-forward、scan 前拒绝 enabled scaler、real optimizer、DDP/FSDP/DataParallel、initialized process group、world-size!=1 与 CP。CPU/static double 的 `.scale(objective).backward()` 只能证明一次调用，不得声称 AMP/unscale/skip/optimizer/LR 生命周期支持。
6. **Recovery lineage**：实现只能消费现有 public suffix-recovery capability；不得新增 admission/refreeze/resample、私有状态重建或 attempt-2。已提交 prefix fast state保留；recovery suffix 的 identities/order/count、`N_window` 与 `GA_effective` 必须由 exact recovery plan 取得，original transition 只在全部 suffix commit 后 reconcile 一次。

## 4. CPU/static 验收矩阵

| 编号 | 定向 witness | PASS 条件 |
| --- | --- | --- |
| A | normal multi-member | 一次 frozen admission，stream-major identity；S0 `None`、PAD 无 native object；actual=planned 后才 bind。 |
| B | normal loss algebra | 非等 valid count、非零 auxiliary、weighted multi-modality owners；精确 objective，且无 second `/GA`。 |
| C | suffix recovery | 已提交 prefix 后的公开 typed suffix capability；无 second admission；recovery 非等 valid count、非零 auxiliary、精确 recovery `N_window/GA_effective`，original transition 恰 reconcile 一次。 |
| D | source / ownership rejects | foreign/raw-reordered carrier、missing term、unweighted substitute、S0/prefix mismatch、count mismatch、stale/double capability 均在 commit 前拒绝、零 frontier mutation。 |
| E | backward / commit disposal | loss-build、forward、pre-backward、prepare-commit、pre-mutation commit failure 均清 controlled grads/abort/terminalize；post-mutation failure不自动 disposal。 |
| F | admission rejects | enabled scaler、real optimizer、DDP/FSDP/DataParallel/group/world-size/CP 在 callback/model-forward/scan 前拒绝，零 scheduler/transaction/frontier mutation。 |

验收命令仅在独立 implementation Gate 获批后冻结为定向 pytest、目标 `py_compile` 与双仓 `git diff --check`；本设计 Gate 不执行这些命令。

## 5. 后续顺序与 verdict

本 Gate 的实现 closure 后，唯一下一步仍为独立 feature/config/optimizer/checkpoint refreeze design；不得直接申请 GPU、sidecar、matched smoke 或训练。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。批准仅授权第 1 节白名单的 synthetic CPU/static implementation，不授权任何真实运行。
