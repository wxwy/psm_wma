# PSM-WMA Temporal Local Memory Canonical Training & Runtime Contract v0.3.6

**日期**：2026-09-08
**状态**：docs-only remediation design；待 MM、DS 对同一 SHA 审核；未授权代码、GPU、真实 checkpoint I/O、训练、评测或推理
**适用分支**：根仓 `V2`
**取代范围**：解决 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` 与 `PSM-WMA_Local_Memory_v0.3.5_supersession_migration_design_v0.1.md` 的实现接缝歧义；未列出的 v0.3.5 chronology/mathematics 保持有效
**当前 child 基线**：`80aec090688e3c710c41e1dfd86b6500773db2c7`

## 1. 目的、范围与不可越过的边界

本版把 v0.3.5 的 segment-level Local Memory 训练路线收敛为可实现的唯一接口合同。它响应 MM、DS 与 Codex 对旧 migration design 的 `REQUEST_CHANGES`，并 supersede 旧 row-wise `TTTLifecycle.process_sample()`、detached candidate、closing-row replay/materialize 和 pre-write witness 作为生产 Cosmos graph 来源的路线。

本版只定义后续 CPU/static implementation design 的前置合同。禁止修改 child/runtime/packer/trainer，禁止真实数据、cache、checkpoint I/O，禁止 CUDA、torchrun、训练、评测或推理。获得本文件的审核批准也不等于批准上述动作。

## 2. 固定训练单位与时间语义

首轮 canonical smoke 固定：

```text
B_stream = 8                 # 每 rank 的 stable stream slots
T = ttt_tbptt_steps = 16     # 每 slot 每 segment 最大 consumer 数
N_nominal_micro = 128
K_local = 1
W_fast / fast inner compute = fp32
state / dt / age neural feature = OFF
```

对一个 slot 的 segment，令 `c` 为 `start_step`，第 `t` 个 logical position 的 consumer 是 `S_(c+t)`。TTT evidence 不可按同一行解释，唯一 ABI 为：

```text
consumer_step[b,t]        = c_b + t                    if consumer_valid[b,t]
evidence_source_step[b,t] = consumer_step[b,t] - 1     if evidence_valid[b,t]
evidence_valid[b,t]       = consumer_valid[b,t] and consumer_step[b,t] > 0
```

所以 fresh episode 的第一段严格是 `S0..S15` 对应 `NONE,e0..e14`；continued segment 的每个 valid consumer 都使用前一个 completed evidence。`S_t` 的 Local 永远是 `Read(Update(..., e_(t-1)), Q_(t-1))`，当前 consumer 的 observation、target action 或预测但未执行 action 不得进入其 evidence。

`SegmentBatch` 的生产语义字段必须至少为：

```python
SegmentBatch(
    consumer_visual_summary: Tensor[B_stream, T, 96],
    consumer_payload: ...,
    consumer_valid: BoolTensor[B_stream, T],
    consumer_step: LongTensor[B_stream, T],
    evidence_visual_summary_prev: Tensor[B_stream, T, 96],
    evidence_executed_action_prev: Tensor[B_stream, T, 10],
    evidence_valid: BoolTensor[B_stream, T],
    evidence_source_step: LongTensor[B_stream, T],  # -1 iff evidence_valid=False
    slot_id: LongTensor[B_stream],
    episode_id: tuple[str, ...],
    category: tuple[str, ...],
    segment_provenance: SegmentProvenance,
)
```

无 evidence 的 dense tensor 位置只是不可读取的填充存储；scan 必须先按 `evidence_valid` 分支，禁止编码、投影或把其值作为常数 evidence 使用。

## 3. `training_stream_end`、tail 与 Local Prefix

`training_stream_end` 定义为一个 episode 在当前冻结 manifest/config 下**最后一个 eligible Cosmos consumer anchor**：该 anchor 同时具有可验证的 causal current condition、native target、completed previous evidence（除 step0）与 source identity。它不是物理 episode 的最后控制步，也不是未经验证的原始 dataset 末帧。

最后一个 eligible consumer 被成功 commit 后，slot 才 terminal；其后真实 action/evidence 即使存在，也不会因为没有下一 eligible consumer 而额外更新 W。一个 slot 在 `[T]` 内只属于一个 episode；tail 的剩余位置为 PAD，`consumer_valid=False`、`evidence_valid=False`、Local absent、不更新 W、不进入 Cosmos 或 loss。下一 segment 才能 rebind 新 episode，并且必须从 step0 与当时的 learned `W_bar_0` 开始。

scan 产生 `local_tokens[B_stream,T,K_local,32]` 后，按 stream-major `flat=b*T+t` flatten，只 gather `consumer_valid=True` 的 sample；S0 的 gathered Local payload 是 `None`，其余 valid consumer 是 `[K_local,32]`。现有 sparse Memory Prefix 的 `list[Tensor | None]` 是该 ABI 的唯一适配形式；不得伪造 zero token。

## 4. Scheduler ownership 与事务

首版 canonical CPU/GPU smoke 的 `WeightedDeficitScheduler` 是**rank-local main-process owner**，要求 `num_workers=0`；worker/prefetch 拥有 slot、queue 或 W_fast 的方案不在本版范围。它的持久运行态至少包括：

```text
rank, slot_id, category, episode_id, cursor,
target_distribution, cumulative_valid_consumer_exposure,
queue_seed, queue_epoch, queue_permutation, admission_order,
segment_id, manifest/config/source-identity digest
```

slot admission、cursor、episode queue 与 exposure 只可在一个 segment 的 outer backward 成功后提交。load/decode/cache identity failure、inner non-finite、forward exception 或 backward exception必须 abort candidate；不得推进 cursor、exposure 或 queue，不得 rebind/resample。

本版明确区分两个 scheduler：

```text
episode_stream_scheduler : 已成功 backward 的 valid consumer/cursor/W commit 后推进；
                           即使随后 GradScaler skip，也必须保持与已消费 chronology 一致。
slow_lr_scheduler        : 仅在实际 slow optimizer.step() 成功时推进；GradScaler skip 时不推进。
```

GradScaler skip 不回滚已完成的 fast-state/cursor/exposure commit，也不允许随机重放或换 episode；它只清除 slow grads、禁止 slow optimizer 与 `slow_lr_scheduler` step。下一 admission 使用当时尚未更新的 `W_bar_0`，已有 episode 继续使用已提交 W_fast。

## 5. 有限性谓词与 fast-state commit

每个 microbatch 在 commit 前必须同时取得以下证据：

```text
1. 所有 valid inner transition 与 candidate W_fast 有限；
2. 未缩放 native model loss（模型原始返回、任何 valid-count/GA 缩放前）有限；
3. outer backward 正常返回；
4. candidate slot/cursor/provenance 与输入 segment identity 一致。
```

第 2 项是唯一 native-loss 有限性权威；不得用 AMP-scaled loss、日志 loss 或 detached substitute 代替。任一失败必须调用 abort，且状态在异常前后逐字段不变。只有四项均成立才 detach/commit `state_out`；terminal slot 在同一 commit 时 discard W_fast。

## 6. Loss partition 与唯一缩放权

native Cosmos loss 必须在 model seam 显式拆为：

```text
L_consumer_mu : 当前真实 consumer 的 mean primary task loss
L_aux_mu      : load-balancing 等不具有逐 consumer mean 语义的 auxiliary loss
```

对一个 `GA` window，令 `N_window=sum_mu N_valid_mu`。唯一 canonical backward objective 是：

```text
L_backward_mu = (N_valid_mu / N_window) * L_consumer_mu
              + (1 / GA) * L_aux_mu
```

全满时它严格退化为现有 `(L_consumer_mu + L_aux_mu) / GA`。因此 Local-Memory enabled path 必须由 trainer 的显式 segment-loss seam 承担唯一缩放：它接收已解析的 `L_backward_mu`，并禁止再无条件除以 `grad_accum_iter`。非 Local-Memory path 保持现有 `loss / grad_accum_iter` 不变。

不得把当前 `total_loss` 整体乘 `N_valid_mu/N_window`，因为现有 load-balancing loss 不属于 consumer mean。`N_window=0` fail closed。首版单 GPU 的 planned `N_valid_mu` 必须在 window 第一次 backward 前由 scheduler 的 metadata plan 给出，不得为计数预加载 tensor。多 GPU 的 global denominator、DDP mean 和 all-reduce 是独立 Gate。

## 7. Evidence feature construction、optimizer 与 checkpoint identity

首版使用 `EvidenceFeatureConfig(state=False, dt=False, age=False)`。该 config 必须在 `LocalEvidenceEncoder` construction 时真实移除 disabled branches：不注册 `state_proj`、`dt_proj`、`age_embedding`，forward 也不接受或读取其 tensor。visual/action projection 与 LayerNorm 保持注册和可训练。

因此 v0.3.2 的 slow optimizer/checkpoint inventory 不能宣称兼容。后续 implementation design 必须重新冻结：

```text
feature flags + dims
exact parameter inventory
exact optimizer membership
checkpoint config identity
old checkpoint handling = fail closed unless an explicitly reviewed migration exists
```

禁用分支不得以可训练参数接收常数零、假 age 或虚拟 dt 来实现。

## 8. Runtime sidecar 与 Gate 顺序

canonical single-GPU smoke 明确不支持 mid-episode exact resume。任何正式长训之前，必须先完成单独的 runtime-sidecar Gate，sidecar 只能在所有 open segment 已 backward/commit 的安全边界写入，并至少绑定：

```text
rank, slot/episode/category/cursor, detached W_fast,
episode queue seed/epoch/permutation/admission order/exposure,
optimizer iteration, slow checkpoint SHA, config SHA, manifest/source identity
```

identity、world size 或 config 不一致时 exact resume fail closed。正式路线的唯一顺序为：

```text
v0.3.6 design approval
-> CPU segment core
-> CPU Cosmos synthetic adapter + loss fixtures
-> feature/config/optimizer/checkpoint refreeze
-> canonical single-GPU smoke design and approval
-> canonical single-GPU smoke
-> runtime-sidecar design, CPU/static verification, resume smoke
-> LIBERO4IN1 matched-smoke design and approval
-> matched smoke
-> formal-training design/command approval
-> formal Local Memory training
```

## 9. Required CPU/static acceptance matrix

后续实现至少必须证明：

```text
A. fresh S0 is consumer-valid and Local/evidence absent; S1 reads only e0.
B. continued segment source steps are exactly previous consumer steps.
C. PAD is never encoded, updated, emitted, gathered or counted in loss.
D. flatten/gather round-trip preserves consumer/evidence/slot/episode/source identity.
E. each stream has independent inner update scale; no cross-stream fast-state mixing.
F. finite native-loss failure, inner failure, forward failure and backward failure abort with byte-identical committed state.
G. GradScaler skip commits fast chronology/exposure but skips only slow optimizer/LR scheduler.
H. full-valid loss and gradient exactly match legacy 1/GA; tail fixture weights primary loss by valid counts and auxiliary loss by 1/GA.
I. disabled state/dt/age parameters are absent from module, optimizer and strict checkpoint inventory.
J. `training_stream_end`, tail terminal and next-segment step0 re-admission preserve no cross-episode W leak.
K. sidecar save/load identity mismatch fails closed before formal-training Gate.
```

## 10. Decision

本文件是 v0.3.5 的唯一 remediation implementation-design 前置。任何实现必须先获得同一根仓 SHA 与 Gitlink 的 MM、DS 审核批准；在此之前，任务保持 `REVIEW`。
