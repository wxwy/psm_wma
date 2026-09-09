# PSM-WMA Local Memory v0.3.5 Production Runtime Owner / Sidecar 实现设计 v0.8

**状态**：docs-only remediation；v0.7 superseded；请求新的 CPU/static implementation authority。  
**Gate**：`G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`。  
**formal context**：v0.7 root `ef13ad7` / child `5d16b84` 收到 ChatGPT HIGH-1/2、MEDIUM-3 与 DS L1/L2；本版关闭这些设计缺口，不改 child。

本版继承 v0.3.5 与已关闭 wiring pair `593fa24 / 5d16b84` 的 exact-once
capability、transaction、adapter commit 语义。它只授权下一阶段的 pure Python/CPU
runtime owner；不授权真实 data/cache/checkpoint I/O、config、GPU 或训练。

## 1. 精确白名单

| 路径 | 状态 | 允许变更 |
|---|---|---|
| `cosmos_framework/model/generator/mot/canonical_segment_runtime.py` | new | `CanonicalSegmentRuntimeOwner`、`RuntimePhase`、不可变 `CanonicalRuntimeSnapshot`。 |
| `cosmos_framework/model/generator/mot/canonical_segment_runtime_test.py` | new | synthetic CPU owner fixtures。 |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py` | existing/modified | 仅新增 exact `discard_pending()` 与只读 snapshot helper。 |
| `cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py` | existing/modified | 对上述 helper 的 CPU tests。 |

`production_segment_wiring.py`、`omni_mot_model.py`、trainer、scheduler source、dataset/
collator、config、optimizer、checkpoint、callback 均不改。不得新建第二 wiring、adapter、
transaction 或 result。

## 2. 唯一 exact wiring authority

owner 构造器固定为：

```python
CanonicalSegmentRuntimeOwner(
    scheduler: RankLocalSegmentScheduler,
    wiring: CanonicalSegmentWiring,
)
```

`wiring` 是唯一 capability authority；owner 不接受独立 adapter 或 slow-parameter tuple。
构造时冻结 `owner.adapter is owner.wiring.adapter`，并拒绝已被另一 owner 绑定的
`wiring` 或 scheduler。`wiring.local_slow_parameters` 继续是唯一 Local slow-grad owner，
不在 owner 重建或复制。

`prepare(segment, identity, transaction)` 仅可调用
`owner.wiring.prepare(segment, identity, transaction)` 一次，并要求：

```text
forward.wiring is owner.wiring
owner.wiring.adapter.pending_scan == (identity, transaction, forward.result)
```

per-call construction `CanonicalSegmentWiring(...)` 永久禁止。`commit()` 只接受该 exact
`forward`，且只在 trainer 已成功登记该 identity 后调用同一
`owner.wiring.adapter.commit(...)`。

## 3. owner phase machine 与 transaction API

`RuntimePhase` 只允许：

```text
IDLE -> ADMITTED -> OPEN -> PREPARED -> COMMITTED -> IDLE
                                  \-> ABORTED
```

- `admit(identity)` 委托 scheduler，记录 exact admitted identity，转 `ADMITTED`；snapshot
  禁止。
- `begin(plan)` 要求 phase=`ADMITTED`、无 open transaction，且 plan 的当前 member 精确
  等于 admitted identity；保存同一 `LocalMemoryTransaction` 对象，转 `OPEN`。
- `prepare(...)` 要求 exact open transaction/identity，保存 exact forward，转 `PREPARED`。
- `commit(...)` 要求 exact forward/result/pending tuple、`transaction.completed_members[-1]`
  已是 identity；仅 adapter commit 成功后转 `COMMITTED`。terminal identity 由现有 adapter
  丢弃 slot state，仍只在 commit 后可达该 phase。
- `finish_window(transaction)` 仅当 plan 全部 members 已 successful-backward、无 pending
  scan 且无未完成 admitted identity 时清除 owner transaction/forward，转 `IDLE`。它不代表
  slow optimizer/checkpoint 已完成；未来 persistent Gate 另行绑定该安全边界。

snapshot 不再接受 caller 提供的 `RuntimeBoundary`。它仅在 owner phase=`IDLE`、无 open
transaction、无 pending scan、无 admitted-but-uncommitted identity 时可调用；其他 phase
一律 fail closed。

## 4. 精确 abort/discard contract

`abort(transaction, forward, disposition)` 接收 exact currently-open objects；
`disposition` 仅为 `TERMINAL(code)`、`RETRY(member_index)` 或 `SCALER_SKIP`。它先以现有
`LocalMemoryTransaction` API 执行对应 terminal/recover/skip disposition，再调用：

```python
adapter.discard_pending(identity, transaction, forward.result)
```

新 helper 必须只在当前 pending tuple 逐对象相同（`is`）时清除 `_pending_scan`；mismatch、
已清除或替代 result 全部失败。它绝不调用 sidecar.commit/reset、不修改 scheduler、不会
回滚此前已 committed detached state。abort 成功后 owner 转 `ABORTED`，snapshot 仍禁止；
recovery suffix 只能经新的 exact `begin()`，且旧 forward 永远不能 commit。

## 5. snapshot 的 committed-frontier 一致性

snapshot 必须深拷贝 detached fp32 sidecar states、owner generation 和
`scheduler.snapshot()`；它还必须验证：

1. 每个 sidecar slot record 的 identity 是 scheduler `committed_identities` 中该 slot 的
   最后一个 identity，且是 `stable_slots[slot]` 的同一 identity。
2. `terminal_slots` 中 identity 无 sidecar record；terminal state 只能由 successful
   terminal commit 删除。
3. owner 的 admitted identity、open transaction、open forward 均为 `None`；因此
   `admit -> snapshot`、`begin -> snapshot`、`prepare -> snapshot` 和 `abort -> snapshot`
   都拒绝，不能由调用者伪造“after commit”。
4. snapshot 修改 tensor 或 mapping 不影响 live sidecar。

这只是内存 snapshot，不是 `state_dict` 或 persistent resume。将来保存/恢复仍需另立 Gate，
并绑定 world-size、rank、slow checkpoint/config/manifest identity 和 queue provenance。

## 6. CPU/static 验收

定向 tests 必须证明：

1. owner 保存并复用同一 wiring；forward wiring/result/transaction identity 全程一致，
   substitute/reconstructed wiring、result、transaction 均在 sidecar write 前失败。
2. fresh→continued 只读同 slot 前一 committed state；cross-episode/source/cursor gap 与
   unadmitted identity 在 scan 前失败。
3. terminal failure、suffix retry、GradScaler skip 都调用 exact discard：pending 变 None，
   既有 committed state 不变，stale forward 不可 commit，recovery 不携带旧 pending。
4. `admit -> snapshot` 负例、prepare/open/abort 负例，以及 post-finish committed 与
   terminal-discard 正例；每个正例验证第 5 节 committed frontier。
5. disabled/legacy/marker/model/trainer 路径完全未调用。仅 pytest、target py_compile、
   child/root `git diff --check`；无 CUDA、文件、网络、dataset 或 checkpoint I/O。

请求：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC` 或
`REQUEST_CHANGES(file:line)`。任何批准仅覆盖 §1 CPU/static 白名单，不授权生产 model
forward、persistent sidecar、真实 I/O、GPU、torchrun 或 LIBERO4IN1 训练。
