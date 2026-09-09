# PSM-WMA Local Memory v0.3.5 Production Active Wiring 实现设计 v0.4

**日期**：2026-09-09

**状态**：docs-only remediation；须三方对本文件 formal pair 同 SHA 批准后才可实现

**任务/Gate**：`G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`

## 1. Authority、范围与 v0.3 supersession

本文件以 v0.3.5 addendum 和 closed production-segment pair `1c6c9ec` / `78b8c9c` 为 authority，并 supersede v0.1--v0.3 的 active-wiring 设计。仅冻结未来 CPU/static implementation；不授权 packer/dataset/manifest/config/optimizer selector/checkpoint、真实 I/O、CUDA/GPU、torchrun、训练/评测/推理或 LIBERO4IN1。

Local-enabled active 路径 supersede 旧 row-wise `TTTLifecycle` 路径；active step 不得创建、observe、commit、abort 或 resolve legacy lifecycle。真实 native numerical/GPU evidence 仍是后续 Gate。

## 2. 固定 active input、registry binding 与 pre-forward orchestration

每个 active member 的 `ActiveNativeBatchInputs` 固定为：

```text
payloads: tuple[Mapping[str, object], ...]
locals: tuple[Tensor | None, ...]
identities: tuple[(slot_id, episode_id, cursor), ...]
```

payload mapping 必须 non-callable、非 PAD-zero；每个 member 仅一次模型内部 `_run_active_local_memory_native_forward(inputs, iteration)`，包含整个 gathered batch；valid entry 各一次、S0 Local=None、PAD 零次，禁止 caller callback 或 per-consumer model loop。

一个 `ProductionActiveWiringRegistry` 在 trainer main process 初始化时创建，并 object-identically 绑定为：

```text
trainer._psm_active_wiring_registry is model._psm_active_wiring_registry
```

禁止 module-global lookup、按 equality 重建、loader/worker/producer 传输该 registry 或任何 runtime capability。registry 创建的 `PreparedActiveMemberCapability`、`ActiveForwardCapability`、`SealedActiveOptimizerCapability` 均显式持有 `registry` 的 exact object；不同 registry、reconstructed/equal object、stale 或 double consumption 在模型 forward 前失败且零 owner mutation。

`ImaginaireTrainer.training_step` 是唯一 pre-forward creator/injector，严格在 `model_ddp.training_step(data, iteration)` 前、main process 内调用：

```text
prepared = trainer._psm_active_wiring_registry.prepare_active_member(
    authority, segment, trainer_grad_accum_iter=grad_accum_iter,
)
active_data = dict(data)                    # shallow envelope only
active_data["psm_local_memory_active"] = True
active_data["psm_local_memory_prepared"] = prepared
```

producer 只提供 `SegmentBatch`/metadata authority，绝不得制造或携带 prepared capability。没有 active admission authority 时 trainer 原样传递 `data`。marker 只允许上述两项 active key，禁止 `native_batch`、`callback`、`forward_fn`、`loss_fn` 或任何 callable。

模型唯一 active branch 位于 `_get_training_inputs()` 前：从 `self._psm_active_wiring_registry` 取 exact registry，consume prepared，调用内部 native seam，并只返回：

```text
output_batch["psm_local_memory_active_forward"] = ActiveForwardCapability
```

没有 complete marker 的 batch 原样走 legacy/no-marker 路径。这样 active step 无法触发 `_inject_local_history` 或 `_ttt_local_memory_tokens`。

## 3. retry、completion 与 exact clock

transient retry 仅当 `completed_members==()`、`grad_accum_iter==0` 且尚无 active backward 时允许；later transient 为 `LOCAL_MEM_RETRY_AFTER_MEMBER` terminal/process-fatal，禁止 suffix in-process window、optimizer/scheduler step 或 `.grad` 复用。

completion 仅由相同 trainer-bound registry 从 output active key 消费一次：identity/count validation → v0.3.5 weighted objective → finite predicate → one `grad_scaler.scale(objective).backward()` → transaction success → owner.commit。Local path 不作第二次 GA 除法；final completed capability 只在 `grad_accum_iter + 1 == ga_effective` 产生。

## 4. owner-sealed preflight/resolve 与 optimizer boundary

为使 post-step resolution 真正无新的可失败 authority check，本 Gate 将下列文件及相邻 CPU tests 纳入白名单：

```text
cosmos_framework/model/generator/mot/canonical_segment_runtime.py
```

该 owner 新增唯一两阶段 surface，owner 仍是所有状态 mutation 唯一 authority：

```text
owner.preflight_slow_window(completed) -> OwnerSealedSlowWindowCapability
owner.resolve_preflighted_slow_window(sealed, *, scaler_skipped: bool) -> None
```

`preflight_slow_window` 在任何 callback/optimizer/scheduler mutation 前验证 owner phase `SLOW_RESOLUTION_PENDING`、exact unconsumed completed object、owner/transaction/pending identity、transaction open，并返回 owner-created sealed object。registry 将该 object 与 exact trainer registry、GA counter 和 completed object 一起封装为 `SealedActiveOptimizerCapability`。所有 stale/substitute/reconstructed/double/counter mismatch 必须在此时零 owner/optimizer/scheduler/callback mutation 失败。

`resolve_preflighted_slow_window` 仅接受同一 owner 刚签发且未消费的 sealed object；其实现不得重做任何可失败的 identity/phase/GA assertion，也不得接受外部 completed capability。preflight 后到 resolve 前，registry 和 owner 禁止任何改变 sealed relation 的操作。固定顺序：

```text
trainer/registry preflight + owner.preflight_slow_window
-> callbacks/model on_before_optimizer_step
-> grad_scaler.step(optimizer)
-> read actual scaler result
-> owner.resolve_preflighted_slow_window(sealed.owner_seal, scaler_skipped=...)
-> success only: scheduler.step()
-> grad_scaler.update()
-> zero_grad
```

skip 只清 Local slow grad、保留 committed fast frontier、零 scheduler step。此路径不调用 `TTTLifecycle.resolve_transaction`。

## 5. active/legacy isolation across trainer callbacks

trainer 以 exact output active key 确定 `is_active_step`。当它为 true：

1. 所有 generic callbacks 仍保持原有调用顺序，但 `TTTLifecycleCallback.on_before_backward/on_after_backward` 必须被 dispatcher 明确跳过；
2. trainer 的 normal backward exception branch 不得读取或调用 `model._ttt_lifecycle.abort_open_segments()`；
3. `_optimizer_step` active branch 必须完全绕过现有 `model._ttt_lifecycle` found-inf/resolve route，只走 §4 sealed owner route；
4. no-marker batch 保持现有 callback、abort 和 optimizer lifecycle 路径逐行为不变。

CPU/static 必须放置 pre-existing `_ttt_lifecycle` spy 与真实 `TTTLifecycleCallback`，证明一个 active marker 的 forward/backward/optimizer 全程 zero observe/commit/abort/resolve calls；紧邻 no-marker control 必须仍调用旧路径。

## 6. 完整白名单与验收

允许：`production_active_wiring.py`、`canonical_segment_runtime.py`、`omni_mot_model.py`、`trainer/__init__.py`、`production_segment_bridge.py` 及相邻 tests；其中 bridge 只可共享无副作用 schema/validation，不得改 closed `run_member()` contract。其他路径禁止。

CPU/static fixture 必须证明：两个 valid entries 的一次 batched internal seam、marker key/type/callback rejection、wrong-registry/reconstructed capability zero mutation、trainer pre-forward shallow injection、first-only retry/later terminal、single weighted scaled backward、preflight failures zero callback/owner/optimizer/scheduler mutation、sealed success/skip deterministic resolution、以及 pre-existing legacy lifecycle zero-call active isolation/no-marker parity。只运行 CPU pytest、py_compile、child/root diff-check；implementation closure 必须重新三方同 SHA 审核。
