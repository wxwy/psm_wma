# PSM-WMA Local Memory v0.3.5 Production Active Wiring 实现设计 v0.2

**日期**：2026-09-09

**状态**：docs-only remediation；须三方对本文件的 formal pair 同 SHA 批准后才可实现
**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`

## 1. Authority、范围与 v0.1 supersession

本文件以 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §0--§20 和已关闭的 production-segment-integration pair `1c6c9ec` / `78b8c9c` 为语义 authority。它 supersede v0.1 中 Local-enabled production 接线路径的调用序、callback cardinality、split-phase capability 和 GA/GradScaler 描述；v0.1 保留为审计历史。

本 Gate 只冻结 CPU/static implementation 设计。它不授权 packer、dataset、manifest、config、optimizer selector、checkpoint、真实 cache/data I/O、CUDA/GPU、torchrun、训练/评测/推理或 LIBERO4IN1。真实 native-model/native-loss 数值正确性、真实 GradScaler/GPU smoke、runtime-sidecar persistence 与正式训练分别是后续独立 Gate，不能由本 Gate 的 synthetic 证据替代。

旧 `TTTLifecycle.process_sample()` / `ProductionLocalMemoryRuntime.materialize()` 的逐 row witness 路径在 Local-enabled production marker 下被 supersede。旧路仅可保留给历史测试、disabled 或旧配置兼容；新路径不得创建、observe、commit、abort 或 resolve `TTTLifecycle`。

## 2. 固定数据 ABI 与单次批量 native seam

未来已验证的数据 producer 必须给每个 Local-enabled trainer microbatch 提供一个 `SegmentBatch`：stream-major `[B_stream,T]` 的 evidence、valid/provenance 与 opaque consumer payload。`flat(b,t)=b*T+t`；PAD 在 forward 前 gather 掉；S0 是合法 consumer entry，但对应 Local token 为 `None`。本 Gate 不实现该 producer；缺失或不匹配一律 fail closed，不能以 PAD zero sample 代替。

对一个已 admitted 的 Local-enabled member，`owner.prepare(segment)` 只执行一次，生成 ordered `payloads`、`locals`、identities 和 `actual_n_valid=len(payloads)`。`actual_n_valid` 必须等于该 member 的 frozen `GAWindowPlan.planned_n_valid[member_index]`，而且只能由该 gathered payload tuple 长度导出。

该 member 的普通模型 native seam 必须**恰好调用一次**：

```text
native_model_forward(payloads: tuple[opaque, ...], locals: tuple[Tensor|None, ...])
    -> NativeBatchResult(primary_consumer_mean, auxiliary_loss)
```

这一次调用携带整个 gathered ordered batch。每个 valid consumer 恰好出现为一个 tuple entry，S0 entry 恰好一次且 Local 为 `None`，PAD 零 entry；严禁按 consumer 循环调用模型或 callback。此定义替代 v0.1 的“one native callback per gathered consumer”措辞。

## 3. 精确 split-phase public capability

现有 `production_segment_bridge.run_member()` 是 CPU/static 的闭合单体 helper，不能被 production model/trainer 直接调用。待批准 implementation 在新增 `production_active_wiring.py` 中提供下列唯一 production 适配层；它复用、而不重建 `CanonicalSegmentRuntimeOwner`、其 transaction、`SegmentForward` 与 `CompletedWindowCapability`。

```text
PreparedActiveMemberCapability(
    owner, transaction, identity, member_index, forward, actual_n_valid,
    ga_window_token, consumed=False,
)

ActiveForwardCapability(
    prepared, native_result, consumed=False,
)
```

两种 capability 都是不可伪造的 in-memory object identity authority：不得序列化、持久化、跨进程传递、复制为等值对象，且只能由同一个 active-wiring registry 创建。每个 registry 在一个 optimizer window 内只保留一个 current capability chain；replace、stale、double consume、owner/transaction/identity/member-index/forward object 任一不一致，均须 owner-owned terminal abort，不能调用 native backward 或 commit。

### 3.1 admission / prepare phase（model forward 之前）

`prepare_active_member(...) -> PreparedActiveMemberCapability | RetryMemberCapability | TerminalMemberResult` 的唯一职责是：

1. 只接受一个 exact initial-plan、open-continuation 或 retry authority；检查 owner phase、member index、identity 和 frozen plan；
2. 只调用一次 `owner.admit` / `admit_next`（或 retained retry）和一次 `owner.prepare(segment)`；
3. 检查 `actual_n_valid`；失败走 owner terminal abort；
4. 注册 exact `PreparedActiveMemberCapability`，但不调用模型、backward、commit 或 `finish_window`。

source transient 在 prepare 前或 native-forward 前显式由该层转换为原有 owner retry capability；attempt-1 transient、identity/count failure 与其他 source failure 都 terminal。retry 不前进 trainer accumulation counter。

### 3.2 model native-forward phase

普通 `OmniMoTModel.training_step` 在 `_get_training_inputs()` 之前检查完整 production marker 和 exact `PreparedActiveMemberCapability`。marker 路径只消费该 capability 一次，直接把其 gathered `locals` 注入现有 Memory Prefix ABI，并以完整 `payloads` 执行一次普通模型 batch forward，返回原生 `primary_consumer_mean` 和 `auxiliary_loss` 及 `ActiveForwardCapability`。

该 branch 必须在 `_inject_local_history()` / `_ttt_local_memory_tokens()` 之前返回，因而新路径不可能惰性创建旧 lifecycle。没有完整 active marker/capability 的 normal batch 必须沿用原有 `_get_training_inputs -> _inject_local_history` 及 loss/output 行为；disabled 路径不创建 registry、owner、plan 或 Local token。

模型 forward 异常、不是 `NativeBatchResult` 的结果、或任一 capability identity failure 由 active-wiring 层调用 owner abort；不得产生 `ActiveForwardCapability`。

### 3.3 trainer completion phase（唯一 backward/commit authority）

`complete_active_member(active, grad_scaler) -> OpenMemberCapability | CompletedWindowCapability | RetryMemberCapability | TerminalMemberResult` 只能在 trainer 的 model forward 返回后调用一次。它必须核对 `active.prepared` 与 registry 的 exact current chain，并按如下顺序执行：

```text
validate frozen member identity/count
-> construct transaction-plan-weighted objective
-> raw finite predicate
-> exactly one grad_scaler.scale(objective).backward()
-> transaction.successful_backward(...)
-> owner.commit(transaction, forward)          # detach-copy W_fast / advance cursor
-> if final: owner.finish_window(transaction)
```

`objective` 必须等价于 v0.3.5 §7.1：

```text
(actual_n_valid / N_valid_window) * primary_consumer_mean
+ auxiliary_loss / ga_effective
```

故 Local-enabled path **绝不**再除以 `grad_accum_iter` 或 `GA`，且绝不调用 raw `loss.backward()`。普通 no-marker path 继续使用原有 `grad_scaler.scale(loss / grad_accum_iter).backward()`。raw finite failure、backward exception、或 completion identity failure 都走 owner abort/retry，且零 fast-state commit；只有 backward 成功后才允许 `owner.commit`。

## 4. trainer GA / GradScaler 时钟与 optimizer boundary

生产 adapter 的 `GAWindowPlan.ga_effective` 必须等于该 native optimizer window 的 effective member count。window 开始时由 metadata authority 在 tensor forward 前冻结 `planned_n_valid`、`N_valid_window` 和 `ga_effective`，并与 trainer 当前 `grad_accum_iter=0` 绑定。一个 successful `complete_active_member` 恰好令 trainer accumulation counter 加一；transient retry 不加一；terminal failure 不得静默开始或继续另一个 window，必须将本 transaction 的 remaining suffix suppress/abort 并向 trainer 传播明确失败。

最终 successful member 只可产生一个 owner-retained `CompletedWindowCapability`，并且只在 `grad_accum_iter + 1 == ga_effective` 的 native optimizer boundary 被消费。出现 completed capability 而 trainer counter 未到边界，或 counter 到边界却无 exact completed capability，都是 identity contract failure，必须 fail closed。

在最终 member 的正确顺序固定为：

```text
complete_active_member successful backward + owner.commit
-> owner.finish_window -> CompletedWindowCapability(SLOW_RESOLUTION_PENDING)
-> callbacks/model on_before_optimizer_step
-> grad_scaler.step(optimizer)
-> read actual found-inf/step-skipped verdict
-> consume exact CompletedWindowCapability once:
     success: owner.resolve(SUCCESS), then scheduler.step()
     skip:    clear Local slow .grad, owner.resolve(SCALER_SKIP), no scheduler.step()
-> grad_scaler.update()
-> callbacks/model on_before_zero_grad -> zero_grad
```

每条完成 capability 的 owner/transaction/member-index identity 必须精确匹配当前 registry chain，重复、早消费、替代或 stale consumption 均 fail closed。skip 保留此前已 commit 的 numeric W_fast frontier，零 slow optimizer/scheduler step；success 恰好一次 slow resolution 和 scheduler step。新路径禁止调用 `TTTLifecycle.resolve_transaction`。

## 5. 允许 implementation 白名单（待批准）

| 路径 | 仅允许变更 |
|---|---|
| `cosmos_framework/model/generator/mot/production_active_wiring.py` / 相邻 test | 新 split-phase capability、registry、owner/bridge adaptation、synthetic spy 与 fail-closed identity checks；无 I/O。 |
| `cosmos_framework/model/generator/omni_mot_model.py` / 相邻 test | production marker 的 early branch、一次 batched Memory Prefix native seam、legacy bypass 与 disabled parity。 |
| `cosmos_framework/trainer/__init__.py` / 相邻 test | active completion 的 scaled backward、GA counter guards、exact optimizer-boundary resolution。 |
| `cosmos_framework/model/generator/mot/production_segment_bridge.py` / 相邻 test | 只抽取/复用无副作用 validation 或 result schema；不得改变已关闭 CPU contract。 |

不得改 dataset/packer/manifest/config/optimizer selector/checkpoint、`ttt_lifecycle.py`、`production_runtime_adapter.py`、`runtime_authority.py`、模型权重定义或其他生产入口。

## 6. CPU/static 验收与后续 Gate 分界

本 Gate 的 CPU/static fixture 只使用 synthetic opaque payload 和 spy native seam，不加载真实模型、数据、cache 或 GPU。它必须证明：

1. 至少两个 valid consumers 的一个 member 只触发一次 batched native seam，spy 收到两个 ordered entries；S0 为 `None` Local、PAD 完全不出现；
2. initial、continuation、retry、stale/substitute/double-consumption、count mismatch、forward/raw-finite/backward failure 均为 owner-owned 正确 disposition；
3. normal marker branch 在 legacy lifecycle 前切断，no-marker/disabled 的 loss、slow grads、输出与旧路径完全一致；
4. 每个 successful member 一次 scaled transaction objective backward，post-backward 才 commit；retry 不推进 GA counter；final completed capability 与 optimizer boundary 一一对应；
5. synthetic scaler-success/skip seam 精确证明 success/skip resolve、scheduler 与 Local slow-grad 行为；不得把该 seam 宣称为真实 CUDA GradScaler 或 native-loss 数值验证。

此外必须运行仅限 CPU 的定向 pytest、目标 `py_compile` 和 child/root `git diff --check`。implementation closure 仍须对新的 child/root formal pair 重新取得 ChatGPT、MM、DS 三方同 SHA verdict：`APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`。之后才可另立真实 producer/packer ABI、GPU native numerical smoke、checkpoint/sidecar 与 LIBERO4IN1 training Gate。
