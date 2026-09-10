# PSM-WMA v0.3.5 Canonical Segment Production Adapter 与 Scheduler/GA Metadata 设计 v0.2

**日期**：2026-09-10
**状态**：docs-only remediation；须三方对同一 formal root/child 批准后才可开始 CPU/static implementation
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`
**替代关系**：本文件替代 `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.1.md`。v0.1 保留为审核历史；本文件在 batch-level member、pre-load projected planning、retry 及 queue rollover 上为唯一 authority。

## 1. Authority、目的与范围

唯一上游是：

1. `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §0--§20.2；
2. `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_supersession_source_audit_v0.1.md` 的已批准 formal audit pair：root `032cb6c3e24f66ae8ab25012cfc654e84b89a6e7` / child `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`；
3. immutable canonical chain：semantics root `e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9` / child `80aec090688e3c710c41e1dfd86b6500773db2c7`，CPU/static design root `1f6c0bad0faa4aabae1c71b01738ad95a4ea902c` / child `80aec090688e3c710c41e1dfd86b6500773db2c7`，closure root `d1f155d9a0cf0cf49055c065defa8119b0ac178f` / child `333792e845fe3b15ba4d8af8f34f704de2a79fa2`。

本设计闭合 v0.3.5 §20.2 A--D、F 的实现路线：完整 `[B_stream,T]` `SegmentBatch` 的 canonical scan、batch-level stream-major valid gather、native consumer ABI、valid-count weighted outer objective，以及无 tensor/latent load 的 scheduler/GA metadata planning。它不授权实现、真实 cache/checkpoint/data I/O、CUDA/GPU/torchrun、训练、评测、推理或 LIBERO4IN1。

E（production feature-disable binding）、G（single-GPU budget）、H（runtime sidecar/resume）仍为独立 Gate。旧 `1 row/microbatch` active-wiring 只保留 failure/transaction vocabulary 的 provenance 价值，绝不是 graph materialization、identity、scheduler 或 trainer control-flow authority。

## 2. 不变硬合同

每个 future production native microbatch 都是完整 `SegmentBatch`：

```text
consumer shape = [B_stream,T]，stream-major flat(b,t)=b*T+t
T <= ttt_tbptt_steps（首版 16）
S0 valid、Local absent；non-S0 valid 必有 e_(t-1)
PAD 不 encode、不 update、不 gather、不进入 native Cosmos loss
```

`SegmentBatch.validate()` 与 `gather_consumers()` 是 ABI owner；`scan_segment_masked_many()` 是每 stream temporal TTT owner。一次 native microbatch 必须先完整 materialize 一张 `[B,T]` TTT graph，再只执行一个 native outer backward；backward 成功后才允许 commit/detach runtime fast state。fast graph 不跨 native member；slow `.grad` 可以跨一个冻结 GA window 累积。

## 3. Batch-level member 与 native adapter ABI

现有 singular `SegmentIdentity`、`GAWindowPlan` 和 `RankLocalSegmentScheduler` 仅是历史 synthetic contracts。future CPU/static implementation 不得静默把一个 `SegmentIdentity` 解释为整张 `[B,T]` batch；必须新增不可变的 batch-level planning double：

```text
MicrobatchPlanMember(
    member_index,
    row_identities: tuple[SegmentIdentity, ...],       # 长度恰为 B_stream，slot_id 升序
    row_provenances: tuple[SegmentProvenance, ...],     # 与 row_identities 一一对应
    row_chronology: tuple[ChronologyCountRecord, ...],
    row_planned_n_valid: tuple[int, ...],
    planned_n_valid: int,                               # sum(row_planned_n_valid)
    queue_snapshot: QueueEpochSnapshot,
    projected_exposure_before: Mapping[str, int],
)
CanonicalGAWindowPlan(members: tuple[MicrobatchPlanMember, ...],
                      original_n_valid_window: int,
                      original_ga_effective: int,
                      plan_chain_id: str,
                      attempt: int)
```

`len(CanonicalGAWindowPlan.members)` 永远是 native GA member 数，绝不能扩张为 `B_stream * GA`。一个 member 的 `row_identities[b]` 是该 stream row 唯一 stable-slot/episode/cursor authority；adapter 验证每行 identity、provenance、chronology、`consumer_valid` count，并在 member 成功后通过**一个原子 member transaction**提交所有行。每行 `training_stream_end` 分别 terminalize；只有 projected plan 已冻结的下一 member 可做对应 terminal rebind，不能在 load/forward failure 时临时换行、换 episode 或 resample。

显式 opt-in、fail-closed adapter 的输入是 `SegmentBatch + MicrobatchPlanMember + CanonicalGAWindowPlan`，而不是旧 row-wise API：

```text
validate batch member -> canonical masked scan（single [B,T] graph）
-> project only gathered valid non-S0 Local tokens
-> stream-major gather payload/Local/row identity
-> NativeConsumerBatch CPU/static double -> one native forward
-> consumer_loss, auxiliary_loss, actual_n_valid
```

`NativeConsumerBatch` 只接收上述 stream-major gathered `payloads`/`local_prefixes` 并返回 `item_count`。真实 Cosmos packer 的 variable-batch binding 尚未被证明，必须留给独立 production-binding/GPU Gate；不得重排、补 PAD、把 `N_valid` 静默改为 nominal 128，或扩展 `_ttt_local_memory_tokens()` / `_run_active_local_memory_native_forward()`。

## 4. Count source、pure projected planning 与 commit

每个 `ChronologyCountRecord` 在 tensor/latent load 前从 immutable manifest/chronology metadata 读取，至少绑定：`slot_id`、`episode_id`、`category`、`source_digest`、`consumer_step_start`、`consumer_step_stop_exclusive`、`training_stream_end`、`manifest_digest`。其唯一 count 公式是该半开区间内满足 `consumer_step > 0` 的 consumer timestep 数；它同时必须与 `SegmentBatch.consumer_valid[b].sum()` 完全相等。S0 的 valid payload 不贡献 Local consumer count；PAD 没有区间或 count。`planned_n_valid = sum(row_planned_n_valid)`，必须为正。

在 load 前，scheduler 从 live committed state 构建深拷贝、无副作用的 `ProjectedSchedulerState`：

```text
stable/terminal slot records + per-category queue positions + queue epoch/permutation
+ cumulative valid-consumer exposure + target distribution + immutable chronology catalog
```

它以 member 顺序模拟 all-row continuation、tail terminal、terminal rebind、queue admission、projected exposure 和 queue rollover，生成整份 `CanonicalGAWindowPlan`；此过程不得改变 live `stable_slots`、`terminal_slots`、queue cursor/permutation、exposure、admission order 或 committed identities。执行时每个已 backward 成功的 member 才以该 frozen member 为唯一输入原子 reconcile 到 live state；实际 row identity/count/provenance、queue snapshot 或 native `actual_n_valid` 任一不等即 terminal/fail-closed，不得改变计划或用新样本替代。

## 5. Deterministic queue epoch 与 weighted admission

queue catalog 在每 category 内按 immutable `(source_digest, episode_id)` 规范排序。`QueueEpochSnapshot` 固定 `queue_seed`、`epoch`、每 category 的 permutation、position 与 catalog digest。epoch `e` 的 permutation 由下列 versioned deterministic algorithm 唯一导出：对每个规范索引 `j` 计算 `sha256("PSM-WMA/queue/v1\\0{seed}\\0{e}\\0{category}\\0{j}")`，按 `(digest bytes, j)` 升序排列 `j`。不得用 ambient RNG、worker order 或 Python hash。

bound stable slot 的 `cursor+1` continuation 优先于一切 free-slot queue admission。只在一个 member 的成功 post-backward atomic commit 后处理 queue 状态：若当前 epoch 的所有 catalog entry 已被 admission，且没有仍绑定/未 terminal 的 slot，则该 commit 安全边界执行 `epoch := epoch + 1`、从上述算法生成全新 permutation，并把所有 terminal slot 依 slot_id 升序变为 free；随后下一 projected member 才按 weighted deficit 为 free slots 选 category 与该 category 当前 epoch 的最前 eligible entry。这样不会在旧 epoch 的 active episode 尚未结束时重复 admission。同一 epoch 内 weighted deficit 仅对 free slot 新 admission 选择 category；已绑定 slot 必须同 episode、同 digest、cursor+1 连续推进。

`cumulative_valid_consumer_exposure` 永不因 epoch rollover 归零；它在每个成功 member commit 后只增加其各行 `row_planned_n_valid`，projected state 使用相同加法模拟。load/decode/cache/identity/count/forward failure、GA window frozen 后的 balance 变化和 native mismatch 都不能推进 queue、epoch、permutation、exposure 或 member identity。

## 6. Native loss、GA objective 与 retry

native forward 必须显式返回：

```text
consumer_loss: scalar，已按本 member 实际 gathered valid consumers mean 归一化
auxiliary_loss: scalar，非 consumer-count 线性项
actual_n_valid: int，等于 NativeConsumerBatch.item_count
```

`OmniMoTModel._compute_losses()` 是现有 native reduction owner。若无法证明上述 member mean，即 fail closed；不得对未知 reduction 的 total loss 二次加权。对 original plan 的 member `i`，唯一 outer objective 是：

```text
L_i = planned_n_valid[i] / original_n_valid_window * consumer_loss
      + auxiliary_loss / original_ga_effective
```

`actual_n_valid == planned_n_valid[i]` 必须在 backward 前验证。full batch（所有 `N_valid=128`）严格退化为 consumer 项 `1/GA`；`L_inner` 不计入；native/DDP sample scale 只能在产生 `consumer_loss` 的 native seam 内应用一次。

本 Gate 选择 first-member-only retry：只允许 `member_index==0`、且 native outer backward 尚未开始的显式 transient failure 重试；attempt-1 保留原始 members、original denominator、original GA、member indices、queue snapshot 与 plan-chain，不得截断为 suffix。任何 later-member transient、任何 backward 已开始后的异常、或无法证明 prefix gradient rollback 的情况，均 terminalize 整个 window、清零该 window slow grads、禁止 suffix retry/rebind。该政策避免 inherited `suffix_after_failure()` 改变 denominator 或丢弃已有效 prefix grads；后者绝不得被生产路径复用。

## 7. Future CPU/static implementation 白名单与验收

后续获批准时，仅可在 child 现有 canonical synthetic Local-Memory modules及相邻测试新增最小 adapter/scheduler contract double；implementation-review 必须按届时源码冻结精确文件白名单。不得触碰真实 producer/packer/dataset、model production forward、config、optimizer selector、checkpoint 或 old active-wiring row route。

最少 CPU/static evidence：

1. `B=2,T=3` mixed S0/non-S0/PAD，验证 stream-major gather、S0 absent、PAD 零 pack/forward，及每 row exact identity/provenance。
2. `B>1`、不同 category/episode/tail 的一个 native member，验证 `MicrobatchPlanMember` aggregate count、一个 shared backward 和一个 all-row atomic commit boundary。
3. variable counts（例如 member totals 5、3）与 full-batch matrix，验证 original weighted consumer objective、auxiliary `1/GA`、actual/planned exact match。
4. GA plan 跨至少一个 tail/terminal boundary，验证 pure projected plan 不变更 live state，post-backward 才按 frozen member reconcile；foreign row、count mismatch、load/forward failure 均 fail closed、无 resample/rebind。
5. first-member pre-backward retry 保留 original denominator/index/GA；later failure 或 post-backward failure terminalizes/clears whole window，不能调用 suffix retry。
6. deterministic rollover fixture：相同 state 得相同下一 epoch sequence/provenance；验证 exhaustion condition、bound continuation precedence 和 exposure 不归零。
7. legacy no-marker/old row-wise active route 不被隐式调用；adapter 未 arm 时 fail closed 或不激活。

验证仅限相关 pytest、`py_compile`、child/root `git diff --check`。成功 implementation closure 也只关闭 CPU/static contract；feature production binding、single-GPU smoke、LIBERO4IN1 matched smoke、runtime sidecar 和正式训练另起 Gate。

## 8. 请求 verdict 与禁止范围

请求唯一 verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。

本文件只做 docs-only remediation，不授权任何 child 代码、真实 I/O、CUDA/GPU、torchrun、训练/评测/推理、P4/P5、B2-T 或 LIBERO4IN1。只有三方对同一新 root SHA 与精确 child/Gitlink 批准后，才可开始限定的 CPU/static implementation。
