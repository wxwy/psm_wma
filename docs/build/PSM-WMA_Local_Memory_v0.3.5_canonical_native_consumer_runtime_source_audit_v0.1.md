# PSM-WMA Local Memory v0.3.5 Canonical Native Consumer Runtime Source Audit v0.1

**日期**：2026-09-11  
**状态**：P0 只读源码事实审计；不构成 runtime/训练授权  
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-SOURCE-AUDIT`  
**审计授权**：formal root `825f08673536bcfeb4983688c463e04b5d16f312` / child `08775da2e73e352ebb1497548de5909baab8c2dc` 的 ChatGPT、MM、Kimi 同 SHA `APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_SOURCE`

## 1. 方法与不可越界结论

所有 child 证据都针对 Git object `08775da2e73e352ebb1497548de5909baab8c2dc`；审计时 child 工作树仅有无关 `uv.lock` 与未跟踪训练遗留，不读取其作为证据，也未修改它。只执行文本/源码读取；未执行 Python/pytest、真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。

结论：现有 child 拥有若干可复用的 canonical metadata、typed scheduler、Local Prefix 与 native-loss split **静态构件**，但 canonical-production 路径在 native pack/forward 前硬停止。因此它不能证明 variable-valid canonical consumer 已进入真实 Cosmos pack/noise/denoise/loss/backward；任何实现设计必须从该 fail-closed 事实开始，不得把 synthetic CPU/static 证据当成生产接通。

## 2. A--F 当前事实

| 项 | source `file:line` | identity/事实 | 结论与唯一 owner / 分流 |
| --- | --- | --- | --- |
| A variable-valid gather/PAD | `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:97-126` | carrier 逐 `[B_stream,T]` 检查 `consumer_valid`；PAD 必须 `(raw,sample)=(None,None)`，valid 必须存在，并以 frozen `planned_n_valid` 校验 expected traversal。`omni_mot_model.py:1429-1433` 又比较 scan gathered identity/count 与 carrier。 | **PARTIAL / fail-closed**：metadata/gather authority 是 carrier+adapter，但 `omni_mot_model.py:1443` 在真实 native pack 前无条件抛错；未证明 native packer 能消费 `N_valid_micro < B_stream*T`。后续 Gate 必须在“真实 gather adapter”与“native-loss mask 等价 ABI”二选一，禁止 trainable zero-PAD。 |
| B native reduction / GA | `omni_mot_model.py:1880-1953`；`canonical_segment_production_adapter.py:312-339`；`trainer/__init__.py:551-561` | ordinary `_compute_losses()` 聚合 modality loss；static split 按 owner index 聚合 weighted per-instance term，并产出 `(consumer_loss, auxiliary_loss, actual_n_valid)`。普通 trainer 分支仍固定 `grad_scaler.scale(loss / grad_accum_iter).backward()`。 | **FAIL-CLOSED**：canonical forward 在 `omni_mot_model.py:1443` 未生成 native capability，故不能把 static split 认定为实际 native reduction owner。下一 implementation design 必须把 `actual==planned`、`N_window` 和 consumer/auxiliary scalar seam 接入真实 native output，并让 Local path排除普通无条件 `/grad_accum_iter`。 |
| C planned count / provenance / recovery | `canonical_segment_adapter_scheduler.py:1-5, 39-54, 150-165, 169-202, 279-308` | scheduler 明确自称 metadata-only，冻结 row identity/provenance、planned count；`objective()` 在 backward 前以 actual==planned 拒绝；typed suffix recovery 保留 original uncommitted suffix、重新计算 suffix `N_window/GA_effective`。 | **PARTIAL / fail-closed**：owner 是 `CanonicalBatchScheduler`/`CanonicalBatchWindowTransaction`，但它不是 producer/packer/trainer integration；未证明 dataset/collate 能在不 materialize tensor 前冻结 queue/seed/epoch/category exposure。必须新建 scheduler/data-side integration Gate。 |
| D state/dt/age disable | `local_evidence.py:21-31, 58-83, 101-140, 142-145` | canonical config 为 `state=False,dt=False,age=False`；construction 不注册这三支；forward 拒绝 disabled 输入，`encode_segment()` 只接受 canonical config。 | **PASS（模块内）**：`LocalEvidenceEncoder` 是唯一 construction/forward owner，非“常数零”伪关闭。**未证明 production inventory**：canonical production runtime 尚未跨过 `omni_mot_model.py:1443`，因此 optimizer/checkpoint identity 仍须独立 refreeze Gate。 |
| E legacy supersession / mutation authority | `omni_mot_model.py:1524-1540, 1067-1140`；`trainer/__init__.py:551-561, 935-995` | `training_step()` 先分派 canonical-production marker、active registry、旧 canonical marker，随后才 ordinary path；ordinary history injection 仍产生 row-wise `local_memory` list。trainer 对 canonical native capability 有独立 backward 分支，但该 capability 当前不可达。 | **FAIL-CLOSED**：须保留 metadata scheduler/transaction/retry 构件；row-wise injection、active registry 与旧 marker 不能与未来 canonical `[B_stream,T]` route 共享 mutation authority，直到 real-route integration 逐 object identity/abort/terminal 证明隔离。 |
| F Prefix / gathered consumer identity | `omni_mot_model.py:1476-1482, 4564-4586`；`mot/memory_prefix.py:50-86`；`mot/unified_mot.py:1272-1313` | canonical preparation 将 gathered local prefixes 按 sample 设置 `has_local_memory` 和 dense list；prefix context 接受 `list[Tensor|None]`，为每 sample 建 offsets/present，要求共同 `K_local`；unified MoT 在 prefix layernorm 后注入 attention。 | **PARTIAL / fail-closed**：可复用 ABI 是 `tokens_by_sample: list[[K_local,32]|None] -> hidden/offsets/present`；ordinary clean materialization 保留 mixed-batch 对齐。但 canonical path在调用 packer前终止，故未证明 stream-major `[B_stream,T] -> [N_valid,K_local,2048]` 的真实 native pack/gather identity。 |

## 3. Canonical objective 与 backward seam

现有 typed static plan 的 objective 位于 `canonical_segment_adapter_scheduler.py:193-202`：

```text
planned_n_valid / original_n_valid_window * consumer_loss
+ auxiliary_loss / original_ga_effective
```

它与 contract v0.3.6/v0.3.8/v0.3.9 的 normal/recovery formula 在静态对象层一致；`derive_suffix_recovery()` 的 suffix-only members、`N_window` 与 `GA_effective` 见同文件 `279-308`。trainer 的 canonical-native 分支也意图在 `trainer/__init__.py:935-995` 从 `request.plan.objective()` 形成 objective 后仅 scale/backward 一次，普通分支在 `551-561` 才做 `/grad_accum_iter`。

但是 `omni_mot_model.py:1408-1447` 明确在 prepare 之后抛出 `canonical-production native forward seam is unavailable`，未交付 `psm_canonical_native_forward`。故下列 production acceptance 全部为 **NOT PROVEN / 必须 fail closed**：

1. 每个 member 的 `actual_N_valid == planned_N_valid` 在真实 native loss/backward 前成立；
2. normal `N_window=sum(planned)`、`GA_effective=GA`；suffix recovery 仅保留 uncommitted suffix、`GA_effective=len(suffix)`；
3. `L_backward = planned/N_window * L_consumer + 1/GA_effective * L_aux` 在 native output 到 GradScaler 之间无第二次无条件 GA 缩放；
4. full-valid normal 严格退化为 `(L_consumer+L_aux)/GA`；
5. native noising、network output、modality reduction 与 gathered consumer identity 的一一对应。

## 4. G--H 与 smoke 前置

| 项 | 可证明 source evidence | 结论 |
| --- | --- | --- |
| G fp32 W_fast / graph / single device | `omni_mot_model.py:1411-1414` 在 scan 前拒绝 CP；`local_evidence.py:142-145` 仅提供 canonical evidence encoder；typed scheduler `:1-5` 明确不是 runtime integration。 | **DEFERRED / NOT PROVEN**：当前 source 不可证明真实 `W_fast` storage、higher-order graph lifetime、单卡 memory/throughput/budget。不得估报或分配 GPU；须由独立批准的 single-GPU smoke Gate 测量。 |
| H sidecar / distributed / world size | `canonical_segment_adapter_scheduler.py:1-5` 排除 runtime-sidecar；`omni_mot_model.py:1412-1414` 只拒绝 CP，非完整 distributed/resume contract。 | **MANDATORY SEPARATE GATE**：正式训练前必须设计并验证 safe-boundary sidecar schema/restore、rank ownership、config/manifest/source/world-size mismatch fail-closed；当前不存在生产证据。 |

## 5. 后续实现输入与 Gate 分流

| 保留 | canonical real route 旁路/删除候选 | 必起后续 Gate |
| --- | --- | --- |
| `CanonicalRawRowCarrier` 的 PAD/identity preflight；typed plan/recovery/transaction；`MemoryPrefixContext` 的 sparse per-sample offsets；construction-time `LocalEvidenceEncoder` feature disable。 | ordinary `_inject_local_history()` row-wise history/replay；`psm_local_memory_active` registry route；旧 `canonical_local_memory_segment` marker。它们不可成为 canonical real route 的 producer 或 shared mutator，除非新审计逐一证明 identity/abort isolation。 | canonical native consumer runtime implementation design：真实 pack/noise/denoise/loss adapter、`[B,T]` stream-major gather、normal/recovery objective and one-backward integration、actual/planned pre-backward guard；随后独立 feature/config/optimizer/checkpoint refreeze、single-GPU smoke、runtime-sidecar/distributed、LIBERO4IN1 matched smoke 与 formal-training Gates。 |

## 6. Verdict

本 P0 只读审计完成，且所有未接通的 production runtime 事实均已 fail-closed。它**不批准** child 修改、任何项目代码执行、真实 I/O、GPU、torchrun、forward/loss/backward、optimizer/scheduler step、训练、评测、推理或 LIBERO4IN1。下一步只能基于本事实新建 docs-only canonical native consumer runtime implementation design，并再次取得三方同 SHA 批准。
