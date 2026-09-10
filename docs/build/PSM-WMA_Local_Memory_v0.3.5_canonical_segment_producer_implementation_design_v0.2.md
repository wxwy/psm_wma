# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer Implementation 设计 v0.2

**日期**：2026-09-10
**状态**：docs-only remediation；须三方同 SHA 批准后才可 CPU/static child implementation
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`
**Supersedes**：v0.1 的 safe-preparation/prefix-adaptation 表述；v0.1 的 typed carrier、CP fail-closed、范围与白名单保持有效。

## 1. v0.1 HIGH closure

v0.1 错误地把已授权的 canonical-safe preparation factoring 和唯一 Local-prefix adaptation 延后。v0.2 在本 Gate 冻结它们；实现不得再把该选择留给下一 Gate。范围仍是 CPU/static，不授权真实 producer、真实 data I/O、GPU 或训练。

## 2. 精确 model-owned safe preparation

白名单保持 v0.1 §2 四文件。`omni_mot_model.py` 新增 model-private helper（名称可为 `_prepare_canonical_production_inputs`），输入为：exact `CanonicalProductionSegmentRequest`、exact `CanonicalRawRowCarrier`、exact `CanonicalProductionScanResult.gathered`、`iteration`；输出为 native tuple：

```text
input_text_indexes, sequence_plans, gen_data_clean,
memory_info, data_resolutions, vae_pixel_shapes
```

helper 的 canonical model batch 唯一来自 carrier 的 immutable, gathered-order `model_data_batch` capability。carrier 必新增该 field；其 top-level mapping 是 producer-supplied、已按 `result.gathered` stream-major valid rows组装的 native collated representation，且有 `len(sequence_plan)==actual_n_valid` 的验证。它不是对 current `data_batch` 的 silent reinterpretation，也不是 dataset/collate change；CPU fixtures只提供 in-memory mapping，不读真实数据。

执行顺序固定：

1. pre-scan 先验证 request/carrier/member/segment/raw rows/`model_data_batch` identity、`[B,T]` validity、stream-major gathered identities/count；任何失败零 scan mutation；
2. CP enabled 直接拒绝，随后才可 scan；若后续 boundary validation失败，也必须在 scan 前完成，避免遗留 adapter scan capability；
3. helper 对 carrier `model_data_batch` 只执行现有非 Local 语义的 `_load_and_tokenize_text_data()`、`build_sequence_plans_from_data_batch()`、`get_data_and_condition()`；明确**不**调用 `_prepare_training_data()`、`_get_training_inputs()`、`_inject_local_history()` 或 `_ttt_local_memory_tokens()`；
4. exact one Local adaptation（§3）后，才调用 `memory_init_training()`；随后本 P2仍在 packer/noise/forward/loss/backward 前 hard-stop。

`model_data_batch` mapping/plan batch cardinality与 `result.gathered.item_count` 不一致、任何 foreign/reconstructed capability或 CP enabled 都必须在 `_inject_local_history()` 前拒绝。No-Local 不构造 carrier/helper，原 ordinary path不变。

## 3. 唯一 Local-prefix adaptation

在 `get_data_and_condition()` 返回 `GenerationDataClean` 后、`memory_init_training()` 前，同一 helper 的唯一 adaptation：

```text
for i in stream-major gathered rows:
  plan[i].has_local_memory = (gathered.local_prefixes[i] is not None)
gen_data_clean.x0_tokens_local_memory =
  [prefix for prefix in gathered.local_prefixes if prefix is not None]
```

只能由 exact `result.gathered.local_prefixes` 提供 prefix；不得由 `raw_rows` / `consumer_payload` 重建，亦不得写 `data_batch["local_memory"]`。S0 prefix 是 `None`，故对应 plan 为 false 且不占 dense Local index；PAD 已不在 gathered rows中。assert plan length、gathered identity、actual count、dense prefix count与上述 relation一致。native `packers.py:244-255` 将依此唯一消费 `SequencePlan.has_local_memory` 与 dense tokens；本 Gate不调用 packer。

## 4. CPU/static acceptance与 verdict

除 v0.1 acceptance外，四文件测试必须证明：safe helper 的 call order、legacy two functions zero-call、`get_data_and_condition()`/`memory_init_training()` 的受控 fake witness、single prefix adaptation（mixed S0/non-S0/PAD）、foreign model batch/count rejection pre-scan、CP hard-stop pre-scan，及 hard-stop 在 native packer前。不得运行真实 I/O/GPU/torchrun/optimizer/training。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC
```
