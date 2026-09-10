# PSM-WMA Local Memory v0.3.5 Canonical Native Forward/Loss Source Audit v0.2

**日期**：2026-09-10
**状态**：docs-only remediation；替代 v0.1，须三方同 SHA 批准后才可创建 implementation design
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FORWARD-LOSS-SOURCE-AUDIT`

## 1. Authority、范围与结论

本版本以 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §18、§20、已批准的 canonical production ABI implementation design v0.3，以及对 v0.1 formal pair 的三方 review 为 authority。它只读取 child `5d0e037ced559c07081fd4880c633dc03f325efe`；不改 child、配置、packer、trainer、真实 I/O、GPU、训练或推理。

v0.1 对 producer hard-stop、Local Prefix ABI、ordinary `/GA` backward 与旧 `canonical_segment_forward` schema 的结论仍有效；但它没有闭合 native preparation parity、native reduction axis 与 optimizer 不可逆边界，故不得作为下一 implementation design 的 authority。本版本补正这些缺口。

结论：下一实现前必须以一个新的 typed canonical capability 冻结四项 ABI：

1. immutable gathered producer rows 到 native `SequencePlan`、text、`GenerationDataClean` 的同序 view；
2. gathered native preparation 与 ordinary `_prepare_training_data()` 的 exact parity，或在 pack/noise 前 fail closed 的明确不支持集；
3. native modality/item/dense-subset loss 到 canonical valid-consumer 的显式聚合；
4. canonical dispatcher 在 trainer DDP/GA、callback、GradScaler、optimizer、scheduler 与 zero-grad 边界的 fail-closed terminal disposition。

旧 row-wise `canonical_segment_forward` capability 与 active route 均不可复用为新 canonical authority。

## 2. Source map 与不可省略的差异

|对象|实际 source|事实|canonical disposition|
|---|---|---|---|
|producer bridge|`omni_mot_model.py:1399-1419`|preflight、registered adapter scan、expected/actual gather 对比后调用 safe prepare，再 hard-stop 并 `abort_scan()`|保留 pre-scan、scan、abort authority；不得删除 hard-stop 或落 ordinary path。|
|canonical-safe helper|`omni_mot_model.py:1421-1448`|从 `carrier.model_data_batch` copy 创建 text/plan/clean，clone plan 后唯一写 gathered Local prefix；调用 `get_data_and_condition()`，固定 `data_resolutions=None`|它只是 safe preparation prefix，**不是** native-equivalent creator；不得直接复用为 parity 声明。|
|ordinary preparation|`omni_mot_model.py:1013-1060`|`per_camera_vae_encoding` 由 marker 得出；`get_data_and_condition(... retain_raw_state_vision=not per_camera_vae_encoding)`；从 `image_size` 导出 per-sample `data_resolutions`；先取 `vae_pixel_shapes`，per-camera 再清 `raw_state_vision`|下一设计必须在 gathered axis 精确复现这五项语义，或在 pack/noise 前拒绝对应 marker/key/mode。`data_resolutions=None` 仅当 admitted batch 的 native shift 语义被证明等价时允许。|
|native schedule consumer|`omni_mot_model.py:1489-1588`、`_get_train_noise_level_vision():2024-`|noise schedule 使用 `batch_size`、vision latent frame count、`data_resolutions`、token count；随后 pack|canonical 不得忽略 `image_size -> data_resolutions`；它是 schedule input 而非 bookkeeping。|
|memory hooks|`omni_mot_model.py:950-1011,1661-1668`|packer 后、noise 前调用 overrideable `pre_noise_memory_hook()`；denoise 前调用 overrideable `build_memory_state()`|post-pack canonical route 必须调用同一 hooks，或在 capability construction 前证明 target class 没有 override；不得静默绕过。|
|packer Local ABI|`packers.py:244-255`|packer 按 caller `sequence_plans` 顺序消费 dense Local list；无 Local 写 `None` prefix，不改变 native geometry|S0 是 valid plan 但 prefix=`None`；PAD 无 plan/text/clean item/prefix。|
|vision item expansion|`omni_mot_model.py:4243-4271,4484-4507`|logical sample 可通过 `num_vision_items_per_sample` 展开为多个 vision item；`GenerationDataClean.batch_size` 仍是 logical-sample count|canonical valid consumer 与 native vision item axis 不得默认相等。|
|dense action/sound|`omni_mot_model.py:1514-1578,1885-1939`|action/sound 仅对有该 modality 的样本形成 dense list，并独立 reindex schedule|任何 consumer aggregation 必须保留 source identity，不能用 dense-list position 替代 canonical row identity。|
|flow reduction|`flow_matching.py:55-90`|weighted scalar 是 `per_instance_weighted_loss.mean()`；返回的 `[B]` 是未加时间权重的 `per_instance_loss`|不得把返回 `[B]` 当作 weighted scalar surrogate；必须显式暴露或计算同权重 item loss。|
|loss aggregation|`omni_mot_model.py:1830-2019`|`_compute_losses()` 聚合 vision/action/sound 的各自 mean、可选 sample-level scale、再加不应按 consumer 比例缩放的 LBL auxiliary；当前只返回 total scalar+logs|下一设计必须显式输出 canonical consumer aggregate 与 auxiliary；不得在 total scalar 后补 `N_valid/N_window`。|
|trainer backward|`trainer/__init__.py:520-570`|ordinary branch 是 `grad_scaler.scale(loss / grad_accum_iter).backward()`，随后 callbacks 与 `grad_accum_iter += 1`|canonical 不得走 ordinary scalar division；No-Local 必须保持该路径。|
|optimizer boundary|`trainer/__init__.py:571-589,591-617,723-775`|GA 边界先 preflight、执行 optimizer callbacks，再 `_optimizer_step()`；其中可 `unscale_`、`step`、`scheduler.step`、`update`，最后 zero-grad|新 canonical route 不得借用 active/legacy authority；任何不支持的 enabled scaler/slow optimizer/scheduler disposition 必须在 callbacks 前 terminalize、abort typed scan、清受控慢梯度并零 fast-state/scheduler/transaction commit。|
|历史 canonical branch|`trainer/__init__.py:896-927`|旧 `CanonicalSegmentForward/CanonicalSegmentWiring` row-wise transaction seam|明确 superseded；新 capability 不得伪装成该 schema。|

## 3. 下一 implementation design 的强制冻结项

### 3.1 Gathered preparation parity

新的 gathered native-input dataclass 必须绑定 request、scan result、same-source gathered rows、text、plan、clean payload、`image_size`/resolution view、per-camera disposition、`vae_pixel_shapes`、raw-state lifetime 和 hook disposition。它不得接受 caller supplied count 或普通 row-wise payload。

对每一个 admitted gathered row，设计必须选择并写死下列二选一语义：

- **exact parity**：以 gathered field-wise view 重现 ordinary `per_camera_vae_encoding`、`retain_raw_state_vision`、`image_size -> data_resolutions`、VAE shape extraction、raw-state cleanup，且在 pack 后依序执行 `pre_noise_memory_hook()` 与 `build_memory_state()`；或
- **fail closed**：在 scan/prepare 的可逆阶段拒绝未被逐项证明的 per-camera marker、`image_size`/dict-shift 组合、多 item/modalities 或 hook override。禁止把这些条件隐式降级为 `None`、空 list 或 ordinary fallback。

### 3.2 Consumer aggregation 与 loss split

下一设计必须从 `flat(b,t)` canonical consumer identity 建立明确映射：

```text
gathered consumer row
  -> SequencePlan / GenerationDataClean logical sample
  -> num_vision_items_per_sample flattened vision item(s)
  -> optional dense action / dense sound entries
  -> out_net predictions / weighted item losses
  -> per-consumer aggregate
  -> consumer_loss(actual_n_valid denominator)
```

该设计不得假设一 logical sample、一个 vision item、一个 action entry、一个 sound entry天然同轴。它必须在以下两种完整方案中选择其一：

1. 定义 source-identified、time-weighted native item/subset loss 的显式 per-consumer 聚合，再以 `actual_n_valid` 形成 consumer mean；或
2. 只 admit 已由 source/static contract 证明为一对一的 modality footprint，并对任何 multi-item、dense-subset 或不等基数情况在可逆边界 fail closed。

无论选择哪一种，sample-level scaling 的位置必须与 ordinary semantics一致；LBL auxiliary 在原 native 位置独立保留，且不得乘 valid-consumer 比例。`compute_flow_matching_loss()` 当前返回的 unweighted `[B]` 不能替代加权 consumer term。

### 3.3 Canonical dispatcher 与不可逆边界

新的 typed capability 必须 object-bind request、scan result、gathered native inputs、loss split、`actual_n_valid`、prepared reconcile 与 transaction。仅新的 canonical dispatcher 可精确一次执行：

```text
L_member = plan.objective(member_index, consumer_loss, auxiliary_loss, actual_n_valid)
grad_scaler.scale(L_member).backward()
```

它不得再除 `grad_accum_iter`，不得调用旧 canonical dispatcher，且 No-Local 必须继续 ordinary path。设计须将 unsupported enabled-scaler/optimizer case 在 `on_before_optimizer_step` 前明确 terminalize：abort typed scan、清受控慢梯度、阻止 `_optimizer_step`/`unscale_`/`step`/`scheduler.step`/`update`/zero-grad 的 canonical disposition，零 fast-state/scheduler/transaction commit。现有 active preflight/optimizer seam仅为 source map，不提供新的 canonical authority。

## 4. Required next Gate 与 CPU/static 验收

下一 Gate 只能是 docs-only `CANONICAL-NATIVE-FORWARD-LOSS-IMPLEMENTATION-DESIGN`。其必须冻结白名单、typed dataclass、parity/fail-closed matrix、loss split、canonical dispatcher 与 optimizer boundary；随后才可独立申请 CPU/static implementation Gate。

必需 CPU/static witnesses：

1. stream-major gathered field/order、S0 prefix `None` 与 PAD exclusion；
2. `image_size` resolution propagation、per-camera retain/cleanup、以及不支持组合的 pre-pack fail-closed；
3. overrideable `pre_noise_memory_hook` / `build_memory_state` 被调用或被显式拒绝；
4. single/multi vision item、dense action/sound alignment 与实际 `actual_n_valid` consumer denominator；
5. weighted consumer term 不冒充 unweighted `per_instance_loss`，auxiliary 不按 consumer 比例缩放；
6. full-valid GA algebra 无 `1/GA²`、canonical 一次 backward 无 ordinary `/GA`；
7. enabled scaler/optimizer boundary在 callbacks 前 terminal、零 canonical commit；
8. No-Local 零 canonical construction，旧 canonical/active schema fail closed。

本审计不授权任何 child 代码、真实 I/O、CUDA/GPU、torchrun、native forward/loss/backward、训练、评测、推理、runtime sidecar 或 LIBERO4IN1。请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FORWARD_LOSS
```
