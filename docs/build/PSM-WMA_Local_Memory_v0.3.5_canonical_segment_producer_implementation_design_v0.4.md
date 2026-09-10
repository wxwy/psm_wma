# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer Implementation 设计 v0.4

**日期**：2026-09-10
**状态**：docs-only remediation；须三方同 SHA 批准后才可 CPU/static child implementation
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`
**Supersedes**：v0.3；v0.1 的 typed carrier、CP fail-closed、范围及四文件白名单保持有效。

## 1. v0.3 HIGH closure

v0.3 的 Local-neutrality、closed model-data keyset与 post-scan exact-once `abort_scan()`
均保持有效。其错误是 pre-scan validation 引用了仅由 `adapter.scan()` 产出的
`result.gathered`。本版本把 expected authority 与 actual scan result 分为两个不可混用的
阶段；不改数据侧，不预先制造 Local prefix。

## 2. Logical carrier 与 pre-scan expected traversal

`CanonicalRawRowCarrier` 的唯一 raw source 保持 v0.1 logical `[B,T]` shape：

```text
logical_raw_rows: tuple[CanonicalRawNativeRow | None, ...]  # row-major b*T+t; PAD=None
row_model_samples: tuple[Mapping[str, Any] | None, ...]     # 同一 logical index；PAD=None
model_data_batch: Mapping[str, Any]                          # expected-valid stream-major view
```

在 scan 前，model-owned helper 只从 exact `request.member`、exact
`request.segment_batch`、其 frozen chronology/provenance及这两个 logical tuple 推导
immutable `expected`：遍历 `flat(b,t)=b*T+t`，只保留 member-valid non-PAD entries，输出
stream-major `expected.identities`、`expected.logical_indexes` 与 `expected.item_count`。
这是 expected traversal，不是 `NativeConsumerBatch`、不是 `CanonicalProductionScanResult`，
不读取 `local_prefixes`，也不调用 adapter。

pre-scan validation 必须逐项验证：logical shape=`B*T`、PAD 位置的两个 carrier entry 都为
`None`、valid entries均非 `None`、row/source identity与 expected member/segment/chronology
相同；随后以 `expected.logical_indexes` deterministic gather `row_model_samples` 形成
`model_data_batch` 的 batch-major entries。任何 source/order/count/foreign mismatch 均在
`adapter.scan()` 前拒绝，零 scan mutation。此处不能引用 `result.gathered`。

`model_data_batch` 仅允许 v0.3 §2 的 closed keyset；其每个 expected-valid batch item必须是
对应 `row_model_samples[expected.logical_indexes[i]]` 的 identical object或 deterministic
shallow immutable wrapping。stacked tensor须记录 source key/row identity并验证 shape、dtype、
device、leading dimension与 expected order。`sequence_plan` 若存在仅是 raw collate metadata，
native model `SequencePlan` 仍由 helper build/validate，不得由 producer新建。

## 3. Post-scan actual equality、Local-neutral preparation 与 abort

只有 pre-scan expected validation成功后才调用 `result = adapter.scan(request)`。随即在任何
safe preparation 前验证：

```text
result.gathered.item_count == expected.item_count
result.gathered.identities == expected.identities
```

这两个 actual-result equality 失败时必须立即 `abort_scan(request, result)` 后 re-raise；
不得把 `result.gathered` 的 prefixes、payload或其他字段反向写入/重建 logical carrier或
expected traversal。

其余 v0.3 Local-neutral 合同不变：`model_data_batch` 有 `local_memory` key、foreign Local
token/history/legacy marker或任何 pre-call `has_local_memory=True` 都 pre-scan reject；
`get_data_and_condition()` 返回后再断言无 key、全 plan false、clean Local tokens为 `None`；
只在此后一次性从 exact `result.gathered.local_prefixes` 映射 plan flags及 dense Local tokens。
post-scan helper exception、actual mismatch、intentional packer-before hard-stop 都先执行
identity-bound exact-once `abort_scan()`。它只删除 exact pending request/result bookkeeping，
不得改变 fast frontier、scheduler、transaction、candidate state或 commit capability。

## 4. CPU/static acceptance 与 verdict

除 v0.3 acceptance 外，四文件 tests 必须证明：

1. foreign logical row/source/count/order、PAD non-`None`与 Local key均在 scan 前拒绝，且
   adapter scan spy为 zero-call；
2. expected traversal是 `[B,T]` logical source的 deterministic stream-major valid gather，
   不包含 PAD、不产生 prefix，model batch item能追溯到 exact logical source；
3. injected post-scan gathered identity/count mismatch 会 abort exact pending pair，且
   frontier/scheduler/transaction/commit capability不变；
4. intentional hard-stop与所有已定义 post-scan exceptions同样 abort；CP仍 pre-scan
   hard-stop；不运行 packer/noise/forward/loss/backward、真实 I/O、GPU、torchrun或训练。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC
```
