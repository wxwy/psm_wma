# PSM-WMA Local Memory Observability Extension Design v0.3

> 状态：docs-only remediation；待 MM、DS 独立审核
>
> 取代范围：本版 supersede v0.2 的 scheduler authority、trace schema、R3/R4/R11 与 bounded trace 描述；其余 telemetry reuse、O1--O5 切分及禁止范围原样继承。

## 1. 范围与权威基线

本设计只冻结 observability contract，不授权代码、生产 wiring、真实 I/O、GPU、训练、评测、推理或 O1--O5 的任一实现。

当前 canonical CPU/static scheduler context：

```text
root formal remediation: d1f155d9a0cf0cf49055c065defa8119b0ac178f
child/Gitlink:           333792e845fe3b15ba4d8af8f34f704de2a79fa2
```

唯一 scheduler authority 是 `RankLocalSegmentScheduler`。其 terminal contract 为：

```text
terminal_slots[slot_id] -> terminal SegmentIdentity
```

`training_stream_end=true` 只关闭该 `slot_id`；同一 rank 的其它 stable slot 可继续 admission、backward 与 commit。`terminal_rebind(identity)` 只释放精确 terminal slot，不选择、绑定或 admission replacement。释放后的 fresh episode 必须由同一 scheduler 对 `cursor=0` candidates 执行 weighted-deficit `admit()`，该 admission 才是进入 GA/commit 的唯一入口。

Observer/trace/validator 只能只读映射该 state；不得定义 global `stream_closed`、不得自行推断 rebind、不得成为第二 scheduler authority。

## 2. 事件相关性与 payload-free witness

所有 `psm_local_trace_v3` event 均有如下 required envelope：

```text
schema, event, event_index, rank, global_step, microbatch,
plan_chain_id_or_null, attempt_or_null, member_index_or_null,
slot_id_or_null, segment_id_or_null
```

`event_index` 对单个 rank trace 严格递增；同一 `(plan_chain_id, attempt, member_index)` 是 GA member linkage key。任何 event 使用 identity 时，必须包含完整、直接来自 `SegmentIdentity` 的：

```text
slot_id, episode_id_hash, category, cursor, segment_id,
source_digest, training_stream_end
```

`segment_layout` 另有 `layout_id`；所有 row event 必须携带该 `layout_id` 和：

```text
batch_row, t_index, flat_index, consumer_step, evidence_source_step,
consumer_valid, evidence_valid, local_present
```

这组字段是唯一 permitted common-gather witness。它证明 stream-major order 与 Local present/absent，而**不得**记录、哈希、读取或让 validator 接触 `consumer_payload`、consumer/evidence visual tensor 或 executed-action tensor 的任何字节。`flat_index == batch_row * segment_length + t_index` 必须逐 row 校验。

## 3. 每种 event 的最小字段与因果关系

| Event | 必需附加字段 | Validator 关系 |
|---|---|---|
| `segment_layout` | `layout_id, segment_length, consumer_valid_bitmap, evidence_valid_bitmap, consumer_step[], evidence_source_step[], pad_count` | 同 identity/layout 一次；bitmap 与 row witness 一致。 |
| `segment_admit` | full identity, `admission_index` | 非 terminal/free slot；fresh identity 必须 cursor0；产生后才可有其 GA member。 |
| `consumer_read` | row witness, `state_before` | 仅 valid row；S0 `local_present=false`，valid non-S0 为 true。 |
| `backward_success` | full identity, GA key, `planned_n_valid, actual_n_valid` | 该 member 已 admitted，且 planned=actual。 |
| `scheduler_commit` | full identity, GA key, `valid_consumers, target_exposure_after, actual_exposure_after` | 紧随相同 key 的 `backward_success`；identity 仅一次。 |
| `transient_failure` | GA key, `failure_kind` | 未 commit member 才可失败。 |
| `suffix_retry_begin` | `plan_chain_id, attempt=1, suffix_member_keys` | 只对应当前未提交 suffix。 |
| `scaler_skip` | `plan_chain_id, attempt, slow_grads_cleared=true, slow_optimizer_step=false, slow_lr_step=false` | 不回滚既有 scheduler commit。 |
| `slow_optimizer_step` | `plan_chain_id, attempt, slow_optimizer_step=true, slow_lr_step=true` | 不得与同 transaction scaler skip 混淆。 |
| `training_stream_end` | full terminal identity | 只把该 slot 置 terminal。 |
| `terminal_rebind` | released terminal identity | 只表明 slot free；不含 replacement identity。 |
| `failure` | GA key, `failure_kind, terminal_state` | 与 retry exhaustion/transaction terminal state 一致。 |

未列 event、缺 required field、错误类型或跨 rank 复用同一 `(rank,event_index)` 均 fail closed。`attempt` 只允许 `0` 或 `1`；attempt=1 transient failure 必须以 `LOCAL_MEM_RETRY_EXHAUSTED` 结束，禁止嵌套 retry。

## 4. Invalid/PAD 与 terminal validator 规则

`segment_layout` 是唯一允许感知 PAD layout 的 metadata event。对于 PAD 或 `evidence_valid=false` row：

```text
不得有 consumer_read / Local encode / project / fast update / write / read event；
不得读取任何 payload、visual 或 action bytes；
可选 noop_state_fingerprint 只能读取既有 fast-state pre/post detached scalar/fingerprint。
```

R3 不验证 opaque payload 内容；它验证 §2 的 payload-free witness 在 common gather 后保持 stream-major 一致。R4 验证 valid S0 的 `evidence_valid=false/evidence_source_step=-1/local_present=false`，以及 valid non-S0 的 previous-evidence/Local presence 合同。

Terminal rule：

```text
training_stream_end(identity) -> terminal_slots[identity.slot_id]
terminal slot 未释放前不得再 admit 同一 slot
terminal_rebind 只释放同一 exact terminal identity
其它 slot admission 不受影响
释放后 fresh cursor0 identity 仍必须出现 segment_admit 才可 backward/commit
```

因此 validator 不使用任何 global stream-closure predicate。

## 5. Bounded capture 与 non-mutation

trace 默认关闭。开启 Gate/debug capture 时，每个 `(rank, slot_id, plan_chain_id, attempt)` 最多保留 `trace_max_events_per_chain` 条，默认 `256`；超限 FIFO 丢弃，并在该 chain 的 `trace_overflow` summary event 记录 `dropped_event_count`。正常 training telemetry 仅写 detached scalar aggregation。

任何 trace 读取必须：

1. 不改变模型参数、buffer、optimizer、scheduler、RNG、fast state 或 batch metadata；
2. 不触发第二次 encode/project/read/write/update 或 superseded replay/materialize；
3. 不自建 distributed collective；复用已有 sink/aggregation；
4. `wandb.run is None` 时正常 flush/reset；
5. 不能将 validator/trace 结果反向用于 admission、commit、retry 或 reset。

## 6. 后续 Gate

本版若获同 SHA docs-only 批准，仍只允许建立 O1 的独立实现设计。O2 的 consumer-hidden 取点、O3 trace sink、O4 validator 与 O5 recipe enablement 必须各自有明确白名单、验收与独立 Gate；任何 production 或训练动作仍未授权。
