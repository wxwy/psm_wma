# PSM-WMA Local Memory v0.3.5 Production Wiring 与 Runtime Sidecar 实现设计 v0.3

**日期**：2026-09-08  
**状态**：docs-only remediation；待三方审核；未授权真实 I/O、GPU 或训练  
**Supersedes**：v0.2；本版是唯一 implementation-ready authority。  

## 1. 精确实现白名单

仅在本版获 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` 后，允许：

| 路径 | 状态 | 精确允许符号 |
|---|---|---|
| `cosmos_framework/model/generator/mot/production_segment_wiring.py` | new | `CanonicalSegmentForward`、`CanonicalSegmentWiring`、`build_segment_batch_for_test` |
| `cosmos_framework/model/generator/mot/production_segment_wiring_test.py` | new | 相邻 CPU fixtures |
| `cosmos_framework/model/generator/omni_mot_model.py` | existing/modified | `_canonical_local_memory_segment_forward`、`training_step` 的唯一 marker branch |
| `cosmos_framework/model/generator/omni_mot_model_test.py` | existing/modified | marker reachability/legacy-uninvoked/disabled parity fixtures |
| `cosmos_framework/trainer/__init__.py` | existing/modified | `_run_canonical_segment_backward`、`training_step` 的唯一 output marker branch |
| `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py` | new | loss/commit/failure CPU fixtures |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py` | existing/modified | read-only pending inspection only |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py` | existing/modified | bridge fixture only |

所有其他路径、符号均不变且不得由 canonical branch 调用；尤其禁止 config/default/recipe/registry/optimizer/dataset/manifest/checkpoint/C6/`ttt_lifecycle.py`/真实 I/O/GPU/训练。

## 2. 可达 model seam（v0.2 HIGH closure）

`OmniMoTModel.training_step(data_batch, iteration)` 是唯一受控入口。它在其第一条 `_get_training_inputs(...)` 调用**之前**执行以下 test-only branch：

```text
if data_batch.get("canonical_local_memory_segment") is True:
    return self._canonical_local_memory_segment_forward(data_batch, iteration)
```

该 private helper 只读取四个 test fixture 键：`canonical_segment: SegmentBatch`、`canonical_identity: SegmentIdentity`、`canonical_transaction: LocalMemoryTransaction`、`canonical_wiring: CanonicalSegmentWiring`。它调用 `wiring.prepare(...)` 一次，随后调用新 wiring 模块的 `run_native_forward_for_test(payloads, locals)`（纯 tensor spy，不是不存在的 native helper），并返回标准 `(output_batch, loss)`；`output_batch["canonical_segment_forward"]` 精确等于该 `CanonicalSegmentForward`，另含 `primary_consumer_mean`、`auxiliary_loss`、`actual_n_valid`、`plan/member_index/identity/transaction/clear_slow_grads`。

因此该 marker route 在 CPU tests 可达，且不进入 `_get_training_inputs`、`_inject_local_history`、`_ttt_local_memory_tokens`，不会构造 `_ttt_lifecycle` 或调用 `TTTLifecycle.process_sample`。marker 缺失时 `training_step` 的原始首行和全程保持不变；`local_ttt_enabled=False` 测试严格走原 disabled route。该 marker 只允许 `build_segment_batch_for_test` 产生，真实 dataloader 不可写入。

## 3. Trainer seam 与唯一 loss

`ImaginaireTrainer.training_step` 在 model 返回后、调用现有 `loss / grad_accum_iter` 前检查 `output_batch.get("canonical_segment_forward")`。存在时唯一调用 `_run_canonical_segment_backward(...)`，该 helper 按 v0.2 ABI 执行：

```text
L_i=(N_valid_i/N_valid_window)*primary_consumer_mean_i
    + auxiliary_loss_i/GA_effective
```

raw `primary_consumer_mean_i` 先 finite check；不得再除 `grad_accum_iter`、不得额外 backward。helper 成功后才调用 `adapter.commit(identity, result, transaction)`；失败/skip/count/identity/nonfinite 均零写。没有 output marker 时 trainer 的原生路径逐字语义不变。

## 4. 验收与边界

CPU fixture必须证明 marker 能从 `OmniMoTModel.training_step` 到 output marker、legacy lifecycle 未构造；一次 spy forward、stream-major/S0/PAD；unequal-valid 公式及 full-batch退化；post-backward commit/failure zero-write；marker缺失/disabled native parity。只准指定 pytest、py_compile、双仓 diff-check；不运行模型、数据、cache、checkpoint、GPU 或训练。

请求三方对本 formal pair 返回 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC` 或带 file:line 的 `REQUEST_CHANGES`。即使批准也不授权 persistent sidecar、真实 I/O、GPU smoke 或 LIBERO4IN1 training。
