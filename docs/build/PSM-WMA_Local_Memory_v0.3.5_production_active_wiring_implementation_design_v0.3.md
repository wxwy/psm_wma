# PSM-WMA Local Memory v0.3.5 Production Active Wiring 实现设计 v0.3

**日期**：2026-09-09

**状态**：docs-only remediation；须三方对本文件 formal pair 同 SHA 批准后才可实现

**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`

## 1. Authority、supersession 与范围

本文件以 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §0--§20 和已关闭的 production-segment-integration pair `1c6c9ec` / `78b8c9c` 为语义 authority。它 supersede v0.1、v0.2 的 Local-enabled production active-wiring 路径；旧版本仅保留审计历史。

本 Gate 仅授权未来四文件白名单的 CPU/static implementation design，绝不授权 packer、dataset、manifest、config、optimizer selector、checkpoint、真实 cache/data I/O、CUDA/GPU、torchrun、训练/评测/推理或 LIBERO4IN1。synthetic control-flow evidence 不能作为真实 native model/loss 数值、真实 GradScaler/GPU smoke 或正式训练证据；这些是后续独立 Gate。

Local-enabled active marker 路径必须 supersede 旧 `TTTLifecycle.process_sample()` / `ProductionLocalMemoryRuntime.materialize()` row witness 路径。active path 不得创建、observe、commit、abort 或 resolve `TTTLifecycle`；disabled/无 marker/历史测试保留旧行为。

## 2. 单次批量 native seam 与固定 native-input boundary

future producer 为每个 Local-enabled member 提供已验证 `SegmentBatch`，包含 stream-major `[B_stream,T]` chronology、provenance、valid 标记与 consumer payload。`owner.prepare(segment)` 只可执行一次，并产生按 stream-major gather 的：

```text
ActiveNativeBatchInputs(
    payloads: tuple[Mapping[str, object], ...],
    locals: tuple[Tensor | None, ...],
    identities: tuple[(slot_id, episode_id, cursor), ...],
)
```

`payloads` 是 native consumer 的最小输入边界：每项为 producer 已构造的非 callable 映射；它不是 caller callback，也不是 zero-PAD 占位。未来 producer ABI Gate 才能规定具体 MoT tensor field/packing；本 Gate 的 CPU/static synthetic fixture 仅可使用符合该 Mapping shape 的 opaque spy payload，不能把 spy function 填进 `data_batch` 或 capability。

`actual_n_valid=len(payloads)` 必须只由 tuple 长度导出，并严格等于 frozen plan 的当前 `planned_n_valid[member_index]`。每个 Local-enabled member 恰好一次由模型内部调用：

```text
OmniMoTModel._run_active_local_memory_native_forward(
    inputs: ActiveNativeBatchInputs, iteration: int,
) -> NativeBatchResult(primary_consumer_mean, auxiliary_loss)
```

该方法属于模型，不接受 caller-supplied function/callback。它把完整 ordered `locals` 注入现有 Memory Prefix ABI，并把完整 `payloads` 一次性送入普通 MoT forward/loss surface。所有 valid consumers 各出现一次，S0 一次且 Local 为 `None`，PAD 零次；不得 per-consumer loop 调用模型。

## 3. 精确 production marker 与模型/训练器 handoff

新增 `production_active_wiring.py` 是唯一 capability registry。下列 data/output 键是 production ABI，任何缺失、多余 active key、错误 type 或 object identity 不匹配均 fail closed：

```text
data_batch["psm_local_memory_active"] is True
data_batch["psm_local_memory_prepared"] is PreparedActiveMemberCapability

output_batch["psm_local_memory_active_forward"] is ActiveForwardCapability
```

`PreparedActiveMemberCapability` 固定含 exact `owner`、`transaction`、`identity`、`member_index`、`forward`、`ActiveNativeBatchInputs`、`actual_n_valid`、`ga_window_token` 与 one-shot state。`ActiveForwardCapability` 固定持有该 exact prepared object 和模型产生的 exact `NativeBatchResult`。两者均是 registry 创建的不可序列化、不可复制、不可跨进程传递的 object-identity authority；禁止在 marker 内传入 `native_batch`、`callback`、`forward_fn`、`loss_fn` 或任何 callable。

`OmniMoTModel.training_step(data_batch, iteration)` 的唯一 active branch 为：

```text
if data_batch.get("psm_local_memory_active") is True:
    prepared = data_batch["psm_local_memory_prepared"]
    active = registry.consume_prepared_for_model(prepared)
    result = self._run_active_local_memory_native_forward(active.inputs, iteration)
    return {"psm_local_memory_active_forward": registry.publish_active_forward(active, result)},
           result.primary_consumer_mean + result.auxiliary_loss
```

此 branch 必须位于 `_get_training_inputs()` 之前，因此不可能进入 `_inject_local_history()` / `_ttt_local_memory_tokens()`。没有该两个 exact marker fields 的 batch 必须原样进入既有普通路径；disabled path 不得创建 registry、owner、plan、Local token 或 active output key。

`prepare_active_member(...)` 是唯一 admission/prepare API：它接受正好一个 initial/open/retry authority，检查 owner phase、plan/member index、identity 与 count，调用恰好一次 `owner.admit`/`admit_next`/retained retry 与 `owner.prepare`，然后注册一个 prepared capability。它不调用模型、backward、commit 或 `finish_window`。stale/substitute/double prepare/consume、source/forward/count/identity failure 都 owner-owned fail closed。

## 4. retry policy：不混合 suffix 与原 optimizer window

当前 owner 的 `abort_retry/begin_retry` 形成 attempt-1 suffix `GAWindowPlan`，其 `n_window` 与 `ga_effective` 是 suffix 值；因此它不能在已有 slow gradients 的原 native optimizer window 中继续。

本 Gate 只允许最小安全 retry：

```text
transient retry is permitted iff
    transaction.completed_members == ()
    and trainer.grad_accum_iter == 0
    and no active-path backward has succeeded.
```

此唯一允许情形中 retry 发生在第一个 member 的 model/native source failure 之前，原 plan 尚未产生 slow gradients 或 fast commit；`abort_retry/begin_retry` 的 suffix 等于整个未执行 plan，新的 attempt-1 transaction 绑定仍为 counter 0 的同一未开始 optimizer window。retry 本身不推进 trainer counter、optimizer、scheduler 或 fast frontier。

任一 later-member transient（包括已有一个 successful completion 后）一律由 active adapter 以 `LOCAL_MEM_RETRY_AFTER_MEMBER` terminal/process-fatal disposition 结束当前训练 loop：禁止创建 suffix retry transaction、禁止执行 optimizer/scheduler step、禁止 in-process 继续下一 window 或复用残留 `.grad`。它保留已 commit fast chronology仅作故障证据，进程终止使其不可能与新 window 混合。CPU/static fixture 必须覆盖“第一 member transient 可 retry”和“至少一个 successful member 后 transient 必 terminal/process-fatal、零后续 optimizer/scheduler mutation”。

## 5. completion、GA clock 与不可变 optimizer preflight

`ImaginaireTrainer.training_step` 在模型返回 active output key 后只可调用一次：

```text
registry.complete_active_member(
    active=output_batch["psm_local_memory_active_forward"],
    grad_scaler=grad_scaler,
    trainer_grad_accum_iter=grad_accum_iter,
) -> OpenMemberCapability | CompletedWindowCapability | TerminalMemberResult
```

completion 先校验 exact registry/owner/transaction/identity/member/forward chain，再按固定顺序：validate count → build v0.3.5 weighted objective → raw finite predicate → **exactly one** `grad_scaler.scale(objective).backward()` → `transaction.successful_backward` → `owner.commit`。成功的 member 恰好将 trainer counter 加一；Local path 不再除 `/grad_accum_iter` 或 `/GA`，也不调用 raw `loss.backward()`。objective 严格为：

```text
(actual_n_valid / N_valid_window) * primary_consumer_mean
+ auxiliary_loss / ga_effective
```

window 开始时 metadata authority 冻结 `planned_n_valid`、`N_valid_window`、`ga_effective`，并绑定 `grad_accum_iter=0`。一个 final completion 只能在 `grad_accum_iter + 1 == ga_effective` 时产生一个 `CompletedWindowCapability(SLOW_RESOLUTION_PENDING)`；任何 completed/counter 不匹配在 optimizer boundary 前 terminal fail closed。

在**任何** optimizer callback、`model.on_before_optimizer_step`、`grad_scaler.step(optimizer)` 或 scheduler mutation 前，trainer 必须调用不产生 mutation 的：

```text
SealedActiveOptimizerCapability = registry.preflight_completed_active_window(
    completed, trainer_grad_accum_iter,
)
```

preflight 一次性验证并 seal：owner-created且未消费的 exact completed object、owner phase 为 `SLOW_RESOLUTION_PENDING`、exact registry/transaction/member chain、transaction 未闭合、`trainer_grad_accum_iter == ga_effective`、无 stale/substitute/reconstructed/double capability。任何失败均保证零 optimizer、scheduler、owner 变更；不得进入 callbacks。

preflight 成功后的顺序固定为：

```text
sealed = preflight_completed_active_window(...)      # all fallible identity/boundary checks
-> callbacks/model on_before_optimizer_step
-> grad_scaler.step(optimizer)
-> read actual scaler found-inf/skip result
-> registry.resolve_preflighted(sealed, SUCCESS | SCALER_SKIP)
     success: exactly one owner slow resolution, then scheduler.step()
     skip: clear Local slow .grad, one owner skip resolution, no scheduler.step()
-> grad_scaler.update()
-> callbacks/model on_before_zero_grad -> zero_grad
```

`resolve_preflighted` consumes only the sealed object produced in the immediately preceding preflight;它不得再执行任何可失败的 capability/identity/GA validation。success/skip 之外不得有 post-`step` 的 fail-closed branch。skip 保留既有 committed numeric W_fast frontier，零 slow optimizer/scheduler step；新路径绝不调用 `TTTLifecycle.resolve_transaction`。

## 6. 实现白名单与 CPU/static 验收

| 路径 | 仅允许变更 |
|---|---|
| `cosmos_framework/model/generator/mot/production_active_wiring.py` / 相邻 test | 上述 marker/capability/registry、retry、preflight/seal/resolve 与 synthetic spies；无 I/O。 |
| `cosmos_framework/model/generator/omni_mot_model.py` / 相邻 test | 精确 early active branch、模型内部一次 batched native seam、legacy bypass/disabled parity。 |
| `cosmos_framework/trainer/__init__.py` / 相邻 test | active completion、counter guard、pre-step preflight 与 sealed success/skip resolve。 |
| `cosmos_framework/model/generator/mot/production_segment_bridge.py` / 相邻 test | 仅共享无副作用 validation/result schema；不得改已关闭 `run_member()` CPU contract。 |

禁止改 dataset/packer/manifest/config/optimizer selector/checkpoint、`ttt_lifecycle.py`、`production_runtime_adapter.py`、`runtime_authority.py`、权重定义或其他入口。

CPU/static fixtures 必须使用 non-callable `Mapping` payload 与 model-internal spy，不加载真实模型、数据、cache 或 GPU，并证明：

1. 至少两个 valid entries 恰好一次 batched seam；S0=None、PAD 零 entry；
2. marker schema/output handoff exact，caller callback field rejected，active branch 早于 legacy lifecycle，no-marker/disabled loss、slow-grad、输出不变；
3. initial/continuation、allowed first-member retry 与 later-member terminal/process-fatal、count/forward/finite/backward failure 的 owner disposition；
4. single scaled weighted backward、post-backward commit、counter/final capability对齐；
5. stale/substitute/reconstructed/double capability 与 counter mismatch 在 preflight 处导致零 callback、optimizer、scheduler、owner mutation；
6. synthetic scaler success/skip 的 sealed deterministic resolve。不得将这些测试表述为真实 native numerical/GPU 验收。

implementation closure 必须以新的 child/root formal pair 重获 ChatGPT、MM、DS 三方 `APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`。之后仍须独立 Gate 才可处理 producer/packer ABI、真实 GPU native numerical smoke、checkpoint/sidecar 和 LIBERO4IN1 训练。
