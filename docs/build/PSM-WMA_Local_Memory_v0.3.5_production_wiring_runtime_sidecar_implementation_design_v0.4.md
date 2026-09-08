# PSM-WMA Local Memory v0.3.5 Production Wiring 实现设计 v0.4

**状态**：docs-only remediation；待三方审核；v0.3 superseded。  
**范围**：仅 CPU/static test-only wiring；不授权真实 I/O、GPU 或训练。

## 1. 精确白名单

仅允许以下路径/符号：

| 路径 | 状态 | 精确符号 |
|---|---|---|
| `mot/production_segment_wiring.py` | new | `CanonicalSegmentForward`、`CanonicalSegmentWiring`、`build_segment_batch_for_test`、`run_native_forward_for_test(payloads: tuple[Any,...], locals: tuple[Tensor|None,...]) -> tuple[Tensor, Tensor]` |
| `mot/production_segment_wiring_test.py` | new | fixtures |
| `omni_mot_model.py` | existing/modified | `_canonical_local_memory_segment_forward`、`training_step` marker branch |
| `omni_mot_model_test.py` | existing/modified | marker/disabled/legacy tests |
| `trainer/__init__.py` | existing/modified | `_run_canonical_segment_backward` orchestration、`training_step` output branch |
| `trainer/trainer_canonical_segment_wiring_test.py` | new | fixtures |
| `mot/local_memory_segment_adapter.py` | existing/modified | read-only pending inspection only |
| `mot/local_memory_segment_adapter_test.py` | existing/modified | bridge fixture |

`run_native_forward_for_test` 是唯一 in-memory tensor spy：只被 `_canonical_local_memory_segment_forward` 调用，不引用 native training forward，不读写 filesystem，不构造模型/数据/cache/checkpoint。全部未列路径/符号不变且不得调用。

## 2. disable-first 可达 selector

`OmniMoTModel.training_step` 在 `_get_training_inputs` 之前唯一新增：

```text
if self.config.local_ttt_enabled and data_batch.get("canonical_local_memory_segment") is True:
    return self._canonical_local_memory_segment_forward(data_batch, iteration)
```

`local_ttt_enabled=False` 无条件赢：即使 marker 存在，也不构造/call wiring、adapter、`_ttt_lifecycle` 或 `TTTLifecycle`，而走原始 disabled route。enabled 且 marker缺失时保持原旧 path。marker只由 `build_segment_batch_for_test` 产生，真实 dataloader/config 不可写入。

## 3. 精确 model 与 trainer ABI

model helper 只读取 fixture keys `canonical_segment`、`canonical_identity`、`canonical_transaction`、`canonical_wiring`、`canonical_plan`、`canonical_member_index`；前四键用于 `wiring.prepare`，后两键原样写入 output。它调用 spy 一次，返回标准 `(output_batch, loss)`，其中 output 精确包含 `canonical_segment_forward`、`primary_consumer_mean`、`auxiliary_loss`、`actual_n_valid`、`canonical_plan`、`canonical_member_index`、`canonical_identity`、`canonical_transaction`。`clear_slow_grads` 不来自 model：trainer branch 定义为 `lambda: optimizer.zero_grad(set_to_none=True)`。

`ImaginaireTrainer._run_canonical_segment_backward` **不得**构造 objective、finite predicate、taxonomy、backward 或 `successful_backward`。它仅：从上述 output 读取 `plan/member_index/identity/transaction`，调用既有 `_run_local_memory_segment_backward(plan, member_index, primary_consumer_mean, auxiliary_loss, actual_n_valid, transaction=..., identity=..., clear_slow_grads=...)` 恰好一次；仅该调用成功后执行 `adapter.commit(identity, result, transaction=transaction)`。既有 seam 仍是唯一 formula/backward/transaction owner。

其唯一公式仍由既有 seam/plan 给出：`L_i=(N_valid_i/N_valid_window)*primary_consumer_mean_i + auxiliary_loss_i/GA_effective`，raw finite predicate先行、无额外 `/grad_accum_iter`、无第二 backward。

## 4. 验收与禁止

CPU fixtures证明 disable-first、legacy-uninvoked、一次 spy、stream-major/S0/PAD、delegation仅一次、unequal-valid formula/full退化、post-success commit/failure zero-write。仅 pytest/py_compile/diff-check。禁止 config/default/registry/optimizer/dataset/manifest/checkpoint/C6/ttt lifecycle 改动，及真实 I/O/GPU/训练。

请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；任何批准仍不授权 persistent sidecar、真实 I/O、GPU smoke、LIBERO4IN1 training。
