# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer Implementation 设计 v0.5

**日期**：2026-09-10
**状态**：docs-only remediation；三方同 SHA 批准前不得 child implementation
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`
**Supersedes**：v0.4；v0.1 的 typed carrier、CP fail-closed、四文件白名单保持有效。

## 唯一整改：carrier raw-row storage ABI

v0.4 已关闭 pre-scan expected 与 post-scan actual result 的时序问题；本版本仅消除
raw-row storage 的双重权威。**保留 v0.1 nested ABI**，不采用 flat `logical_raw_rows`
作为 carrier field：

```text
raw_rows: tuple[tuple[CanonicalRawNativeRow | None, ...], ...]   # exact outer B, inner T
row_model_samples: tuple[tuple[Mapping[str, Any] | None, ...], ...] # same exact [B,T]
model_data_batch: Mapping[str, Any]                              # derived expected-valid view
```

`raw_rows[b][t]` 与 `row_model_samples[b][t]` 是唯一 raw/model source authority；PAD
位置两者必须均为 `None`，valid 位置均非 `None`，且与 exact request member、segment、
chronology/provenance绑定。`flat=b*T+t` 仅为 helper 在扫描 `[B,T]` 时创建的 immutable
`expected.logical_indexes` 派生视图，绝不存回 carrier、绝不成为第二 raw source。所有
foreign/PAD/source/order/count 检查均使用 nested field；`model_data_batch` 仅按 expected
logical indexes deterministic gather而成。

v0.4 其余合同原样有效：pre-scan expected 不读取 adapter/result/local prefix；scan 后才
校验 actual gathered identity/count；mismatch、post-scan exception与 intentional hard-stop
都 exact-once `abort_scan()`；Local-neutral 与唯一 prefix adaptation 不变。

CPU/static acceptance新增：fixture 使用 nested `B=2,T=3`，验证 outer/inner width、PAD
`None`、derived flat index order及 foreign nested source pre-scan zero-call reject；不得接受
flat carrier字段。其余 v0.4 tests/禁止范围保持。

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC
```
