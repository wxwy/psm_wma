# PSM-WMA Local Memory v0.3.5 Canonical Native Forward/Loss Implementation 设计 v0.1

**日期**：2026-09-10
**状态**：docs-only implementation design；须本文件新 formal pair 三方同 SHA 批准后才可进入 CPU/static implementation
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`

## 1. Authority、目标与范围

本设计继承 v0.3.5 addendum、已批准 canonical production ABI implementation design v0.3（`36df68d/3a078f2`）和 native forward/loss source audit v0.2（`d75a337/5d0e037`）。它只授权下一 Gate 的 CPU/static implementation design scope：以 typed canonical capability 保留原生多 vision-item、dense action/sound、sample-level scaling、LBL auxiliary、memory hooks，并产生 canonical weighted per-consumer loss 和一次 window-normalized backward。

不把路线降级为单 item/单 modality；尚未由 source/static contract证明的 gathered field 必在可逆 prepare 前 fail closed。此设计不授权真实输入、CUDA/GPU、torchrun、native forward/loss/backward、optimizer step、训练、评测、推理、checkpoint/runtime sidecar 或 LIBERO4IN1；不重启旧 row-wise `canonical_segment_forward` 或 active route。

## 2. 下一 CPU/static implementation 白名单

仅允许修改以下 child 文件和定向测试：

1. `cosmos_framework/model/generator/algorithm/loss/flow_matching.py`
2. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py`
3. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`
4. `cosmos_framework/model/generator/omni_mot_model.py`
5. `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`
6. `cosmos_framework/trainer/__init__.py`
7. `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py`

不得改 `packers.py`、配置、optimizer、dataset/dataloader/collate 或 runtime sidecar。原 packer Local ABI 不变：gathered plan 顺序消费 dense prefix，S0 prefix=`None`，PAD 无 plan/text/clean/prefix。ordinary No-Local 和旧 canonical dispatcher 语义不变。

## 3. Loss primitive 与 typed ownership

### 3.1 Weighted native item term

`flow_matching.py` 增加 immutable `FlowMatchingLossTerms`：

```text
weighted_mean: scalar
weighted_per_instance: Tensor[N]
unweighted_per_instance: Tensor[N]
```

唯一新 primitive 计算三者，且 `weighted_mean == weighted_per_instance.mean()`；原 `compute_flow_matching_loss()` 接口保持旧二元返回，只委托该 primitive。无有效 token 时三个值必须仍连接 prediction graph，不能伪造 canonical consumer。现有 unweighted `[B]` 仅为 diagnostics，不得作为 canonical weighted term。

### 3.2 Prepared inputs

`canonical_segment_production_adapter.py` 定义 immutable `CanonicalNativePreparedInputs`，object-bind exact request、scan result、expected traversal、attempt/retry lineage、working batch、text、plans、clean payload、resolution、VAE shapes、memory info、gathered identities和 logical-row→native item/dense-subset maps。它只由 exact immutable carrier 与 exact adapter scan result 构造。

carrier source 永不 mutation；任何 flatten/normalization 只作用于独立 `working_data_batch`。prepare 必先验证 identity/count/order/attempt lineage；错误必须 `abort_scan()`，且 frontier/scheduler/transaction零 commit。

### 3.3 Parity-or-fail-closed

| ordinary semantics | canonical rule |
|---|---|
| per-camera marker | gathered working batch 保留 marker，调用 `retain_raw_state_vision=not per_camera`。 |
| `image_size` | 同序生成 `data_resolutions`；dict shift 不得以 `None` 降级。 |
| VAE/raw state | 先取 `vae_pixel_shapes`，per-camera 后清 raw state。 |
| multi vision item | 保留 `num_vision_items_per_sample` 与 logical→flattened-item range。 |
| action/sound | 每个 dense entry 保留唯一 logical gathered source identity。 |
| hooks | exact order 为 `pack -> pre_noise_memory_hook -> noise/replace -> device move -> build_memory_state -> denoise`。 |

未知/foreign key、不可同序 gather、缺 source map、未知 hook override 或任何 mismatch，均在 pack/noise 前 fail closed、abort exact scan；不得调用 `_get_training_inputs()`、`_prepare_training_data()` 或 `_inject_local_history()` 来 ordinary fallback。

## 4. Per-consumer split 与 forward capability

定义 immutable `CanonicalNativeLossSplit`：

```text
consumer_loss: scalar
auxiliary_loss: scalar
actual_n_valid: int
consumer_identities: tuple[CanonicalIdentity, ...]
weighted_consumer_terms: Tensor[actual_n_valid]
```

模型将每个 modality 的 `weighted_per_instance` 通过 prepared source maps 先归入唯一 canonical identity：

```text
flat(b,t) consumer -> logical sample -> vision item(s)/dense action/sound
-> weighted native item terms -> weighted consumer term -> consumer mean
```

再以原生 modality weights 组合；sample-level scale 位于与 ordinary `_compute_losses()` 相同的位置；LBL auxiliary 保持原位置，独立为 `auxiliary_loss`，绝不乘 valid-consumer ratio。`consumer_loss = weighted_consumer_terms.mean()`，且 `actual_n_valid == len(identities) == gathered.item_count == planned_n_valid`；禁止用 total scalar、modality mean、unweighted vector或 caller count替代。

`CanonicalNativeForwardCapability` object-bind prepared inputs、loss split、prepared reconcile和 exact transaction。future native path只能在此 capability 上顺序调用现有 pack/hook/noise/denoise，并返回新 marker `psm_canonical_native_forward`。CPU/static test 必只用 fake/mocks 检查构造、顺序、拒绝，不得触及 VAE、CUDA、denoise、forward/loss。

## 5. Trainer、GA 与 terminal boundary

`ImaginaireTrainer` 新增独立 canonical-native dispatcher，不复用 `_run_canonical_segment_backward()` 或 active helpers。它只接受 exact capability；foreign/incomplete/old schema在 backward 前 abort。

```text
L_member = plan.objective(member_index, consumer_loss, auxiliary_loss, actual_n_valid)
grad_scaler.scale(L_member).backward()  # 精确一次，绝不 / grad_accum_iter
transaction.successful_backward(...)
adapter.prepare_commit/commit(...)      # success-only
```

attempt-1 仅消费既有 `CanonicalProductionRetryCapability` 的 exact request/transaction；不得 re-freeze、re-admit、重建 retry plan或创建第二 transition。成功仍仅 reconcile 原 frozen transition 一次。

canonical member 触达 enabled GradScaler 或真实 slow optimizer/scheduler boundary 时，必须在 `on_before_optimizer_step` 前 terminalize：abort scan、清本 capability 受控慢梯度、阻断 canonical `unscale_`/`step`/scheduler/`update`/zero-grad disposition，fast-state/scheduler/transaction零 commit。No-Local ordinary callback/optimizer/zero-grad行为不变；existing active seam只作 source evidence。

## 6. CPU/static acceptance

仅 CPU synthetic tensor/mocks；下一 Gate 必冻结定向 pytest、Ruff、目标 `py_compile`、child/root `git diff --check`。必须覆盖：

1. attempt-0/attempt-1 exact lineage，无 second freeze/admission/reconcile；
2. carrier working copy无 mutation；foreign/missing field或count/order mismatch pre-pack abort、零 commit；
3. per-camera、resolution、multi-item range、dense action/sound source maps；
4. S0=`None`、PAD exclusion、hook exact order和不支持 hook/mode拒绝；
5. weighted mean/per-instance等式及 unweighted vector不可替代性；
6. multi-item/dense subsets正确汇入 identity，`actual_n_valid` 为 consumer mean分母，LBL不按 valid ratio缩放；
7. full-valid GA 无 `1/GA²`、一次 backward、旧 schema/No-Local matrix；
8. enabled scaler/optimizer boundary在 callbacks 前 terminal，零 slow optimizer/scheduler/fast-state/transaction commit。

PASS 只证明 CPU/static contracts。任何真实 I/O/CUDA/GPU/torchrun/native forward/loss/backward/optimizer step 均为 Gate failure，保留证据不得自动重跑。

## 7. Verdict

三方批准后才可新建 `CANONICAL-NATIVE-FORWARD-LOSS-CPU-STATIC-IMPLEMENTATION` Gate；不得直接训练。

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS_CPU_STATIC
```
