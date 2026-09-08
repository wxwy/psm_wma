# PSM-WMA Local Memory v0.3.5 Production Wiring 实现设计 v0.5

**状态**：docs-only remediation；v0.4 superseded；待三方审核。

## 1. 精确 child 白名单

| 路径 | 状态 | 精确符号 |
|---|---|---|
| `cosmos_framework/model/generator/mot/production_segment_wiring.py` | new | `CanonicalSegmentForward`、`CanonicalSegmentWiring`、`build_segment_batch_for_test`、`run_native_forward_for_test` |
| `cosmos_framework/model/generator/mot/production_segment_wiring_test.py` | new | fixtures |
| `cosmos_framework/model/generator/omni_mot_model.py` | existing/modified | `_canonical_local_memory_segment_forward`、`training_step` marker branch |
| `cosmos_framework/model/generator/omni_mot_model_test.py` | existing/modified | fixtures |
| `cosmos_framework/trainer/__init__.py` | existing/modified | `_run_canonical_segment_backward`、`training_step` branch |
| `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py` | new | fixtures |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py` | existing/modified | read-only pending inspection only |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py` | existing/modified | bridge fixture |

未列 child 路径/符号不可变且不得调用。

## 2. selector、单一 plan 与 Local-only grad owner

marker 条件严格为 `self.config.local_ttt_enabled and data_batch.get("canonical_local_memory_segment") is True`；disabled 无条件走原 route。

model output **不含** `canonical_plan`。它仅携带 `canonical_transaction: LocalMemoryTransaction`、`canonical_member_index: int`、`canonical_identity`、`canonical_segment_forward`；trainer 唯一 plan 定义为 `plan = transaction.plan`，并把这个同一对象传给既有 seam。任何外部 plan fixture 键都必须 fail closed，且在 objective/backward/commit 前拒绝。

`CanonicalSegmentWiring.__init__(adapter, local_slow_parameters: tuple[torch.nn.Parameter,...])` 冻结 Local-only owner；构造时拒绝重复或 non-leaf parameter。其 `clear_local_slow_grads()` 只对该 tuple 每个 `.grad` 置 `None`，不得调用 `optimizer.zero_grad` 或写入任何未列参数。test fixture 以一个 unrelated parameter gradient sentinel 验证其完全保留；Local failure/skip 清除仅这组 Local grads。

## 3. orchestration

`_run_canonical_segment_backward` 从 output 取 transaction，绑定 `plan=transaction.plan`、member_index、identity、forward.result，并调用现有 `_run_local_memory_segment_backward` 恰好一次，参数 `clear_slow_grads=wiring.clear_local_slow_grads`。仅成功后 `adapter.commit(identity, forward.result, transaction=transaction)`。它不得重写 formula/finite/taxonomy/backward。v0.4 的 `run_native_forward_for_test` 仍仅 in-memory spy，唯一由 model helper 调用。

## 4. 验收和禁止

CPU tests 证明 full paths 实施；disable-first、legacy-uninvoked、single spy、transaction.plan唯一性（外部 mismatched plan在 backward前拒绝）、Local-only grad clearing/unrelated sentinel、single delegated seam、commit/failure、S0/PAD、weighted loss。仅 pytest/pycompile/diffcheck；禁止真实 I/O/config/default/registry/optimizer/dataset/manifest/checkpoint/C6/GPU/训练。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；批准仍不授权 persistent sidecar、真实 I/O、GPU smoke 或 LIBERO4IN1 training。
