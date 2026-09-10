# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer Implementation 设计 v0.3

**日期**：2026-09-10
**状态**：docs-only remediation；须三方同 SHA 批准后才可 CPU/static child implementation
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`
**Supersedes**：v0.2；v0.1 的 typed carrier、CP fail-closed、范围及四文件白名单保持有效。

## 1. v0.2 HIGH closure

v0.2 已关闭 safe preparation 与唯一 prefix adaptation 被延期的问题，但没有把
`model_data_batch` 逐字段绑定到 frozen raw-row authority，也没有定义 scan 后
intentional hard-stop 的 capability disposition。本版本在同一 CPU/static Gate 冻结
两项，不扩大到 dataset、dataloader、collate、packer、trainer 或真实运行。

## 2. Carrier 到 canonical model batch 的封闭派生

`CanonicalRawRowCarrier` 保持 immutable，并封装 ABI v0.2 的
`CanonicalGatheredRawBatch`，同时持有：

```text
raw_rows: tuple[CanonicalRawNativeRow, ...]           # stream-major valid gathered rows
model_data_batch: Mapping[str, Any]                   # native collated view
row_model_samples: tuple[Mapping[str, Any], ...]      # 与 raw_rows 同长度的 source view
```

`raw_rows`、`row_model_samples` 与 `model_data_batch["sequence_plan"]` 的长度必须都
等于 `result.gathered.item_count`，顺序必须逐项等于 `result.gathered` 的 stream-major
valid-row identity。`row_model_samples[i]` 只可来自该 exact `raw_rows[i]` 的 producer
native sample；不得由 `consumer_payload`、current `data_batch` 或另一个 member/segment
重建。

producer 构造 `model_data_batch` 时只允许下列 canonical-safe preparation keyset：

```text
self.input_image_key XOR self.input_video_key, text_token_ids,
video_latent, verify_cached_latent, image_size,
enable_per_camera_vae_encoding, sample_n_views, num_video_frames_per_view,
action, domain_id, raw_action_dim, sound,
conditioning_fps, conditioning_fps_action, control_weights,
num_vision_items_per_sample, is_preprocessed, sequence_plan
```

其中 `sequence_plan` 仅可为 raw collate metadata，不能是 producer 新建、model-built plan；
helper 必须通过既有 builder 建造或验证 native `SequencePlan`。每个 batch-major list/tuple
的第 `i` 项必须与 `row_model_samples[i]` 是同一对象，或是该对象的 deterministic shallow
immutable wrapping。为 native collate 必需的 stacked tensor 允许 deterministic copy/stack，
但必须在 carrier 创建时记录 source key 与逐行 source object identity；实现验证 source-key、
shape、dtype、device、batch leading dimension 及 row order。不得接受任何其他顶层键、nested
list 重排、foreign tensor 或仅同 cardinality 的 mapping。

任何 identity、source-key、nested arity、leading batch dimension、row order、member、
segment、chronology、`[B,T]` validity 或 count 检查失败，均在 `adapter.scan()` 前
fail-closed。若当前 producer 无法生成上述 carrier，而必须修改数据侧，停止本 Gate并另开
data-side Design Gate；不得降低为 length-only check。

## 3. Local-neutral safe preparation 与唯一 canonical 写点

在 scan 前，helper 对 `carrier.model_data_batch` 断言：`"local_memory"` key **不存在**；
任何 raw/foreign Local token、history field 或 legacy Local marker 均拒绝。它还断言每个
exact `sequence_plan.has_local_memory is False`。该 mapping 仅可调用既有 non-Local
`_load_and_tokenize_text_data()`、`build_sequence_plans_from_data_batch()`、
`get_data_and_condition()`；不得调用 `_prepare_training_data()`、`_get_training_inputs()`、
`_inject_local_history()`、`_ttt_local_memory_tokens()`。

`get_data_and_condition()` 返回后、`memory_init_training()` 前，再次断言：source mapping
仍没有 `local_memory`，所有 plan 仍为 `has_local_memory=False`，且
`gen_data_clean.x0_tokens_local_memory is None`。随后且仅随后执行一次：

```text
plan[i].has_local_memory = (result.gathered.local_prefixes[i] is not None)
gen_data_clean.x0_tokens_local_memory =
    [prefix for prefix in result.gathered.local_prefixes if prefix is not None]
```

prefix 只能来自 exact `result.gathered.local_prefixes`，不得读取或写入
`data_batch["local_memory"]`。S0 的 `None` 不占 dense index，PAD 不属于 gathered rows；
断言 gathered identity、plan length、actual count与 dense-prefix count。native packer
仍不在本 Gate调用。

## 4. Scan capability 的成功前 abort 生命周期

四文件白名单内的 adapter 必新增 `abort_scan(request, result)`。它只允许释放 exact
pending scan pair：`_scan_results[id(result)] is request` 且 `id(request)` 在
`_scan_requests`，否则 fail-closed；成功后仅移除这两个 bookkeeping entries。它不得调用
`prepare_commit()`/`commit_success()`，不得创建或消费 commit capability，不得改变 fast
frontier、scheduler、transaction或 candidate state。已 abort 或 foreign/identity-mismatch
pair 的二次调用均拒绝，故它是 identity-bound、exact-once disposition。

helper 在成功 `scan()` 后进入受控 `try`：任何 safe preparation、Local-neutral assertion、
canonical adaptation 或 `memory_init_training()` exception，都先 `abort_scan(request,result)`
再原样 re-raise。当前 CPU/static 正常路径到达 packer 前 intentional hard-stop 前也必须先
abort 后 raise。pre-scan validation/CP reject 保持零 scan mutation。此机制不把 abort
伪装为 commit，亦不授权 forward/loss/backward。

## 5. CPU/static acceptance 与 verdict

除 v0.2 acceptance 外，四文件测试必须证明：

1. foreign 同-cardinality `model_data_batch`、foreign row identity/source-key/nested order
   及 `local_memory` key 均在 scan 前拒绝，零 adapter mutation；
2. `get_data_and_condition()` 前后 Local-neutral witness 成立，唯一 canonical adaptation
   后 mixed S0/non-S0/PAD 的 plan/dense relation 精确成立；
3. intentional hard-stop 及 injected post-scan helper/materialization exception 都使 exact
   `_scan_requests`/`_scan_results` pair 消失，且 frontier/scheduler/transaction/commit
   capability 不变；foreign 或 double abort fail-closed；
4. CP hard-stop 仍在 scan 前；native packer/noise/forward/loss/backward、真实 I/O、GPU、
   torchrun、optimizer/training均未执行。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC
```
