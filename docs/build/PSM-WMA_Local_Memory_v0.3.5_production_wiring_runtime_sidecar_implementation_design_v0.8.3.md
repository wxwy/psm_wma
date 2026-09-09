# Runtime Owner / Sidecar 实现设计 v0.8.3

**状态**：docs-only remediation；v0.8.2 superseded；child=`5d16b84`。仅关闭 v0.8.2 retry projection HIGH，继承 v0.8--v0.8.2 的所有白名单、exact wiring/pending、phase/snapshot 与禁止范围。

`GAWindowPlan.members[0]` 的 canonical type 是 member projection `(slot_id, episode_id, cursor)`；`retry_first_identity` 是 retained full `SegmentIdentity`。因此 `begin_retry(retry_plan)` 必须同时满足：

```python
retry_plan.members[0] == (
    retry_first_identity.slot_id,
    retry_first_identity.episode_id,
    retry_first_identity.cursor,
)
```

并独立要求 scheduler `stable_slots[slot_id] is retry_first_identity`、`retry_first_identity` 已在 `admission_order`、尚不在 `committed_identities`。不得再次 `scheduler.admit()`，不得以同 projection 但 category/source_digest/segment_id/training_stream_end 不同的 reconstructed identity 替代 retained exact identity。通过后才创建 exact attempt-1 transaction 并直接进入 `MEMBER_READY`。

CPU/static Evidence：真实 failed full identity 通过 projection check 且 admission count/order 不变；retry read 使用 prior committed sidecar frontier；same projection/wrong metadata identity 被 exact guard 拒绝；old attempt-0 transaction/forward/result 永不可提交。请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；无真实 I/O/GPU/training。
