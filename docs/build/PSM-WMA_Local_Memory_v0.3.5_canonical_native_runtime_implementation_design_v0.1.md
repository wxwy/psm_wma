# PSM-WMA Local Memory v0.3.5 Canonical Native Runtime Implementation 设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-IMPLEMENTATION-DESIGN`
**状态**：docs-only；须对本文件的新 root SHA / 当前 Gitlink 收齐三方 `APPROVE_TO_IMPLEMENT` 后才可改代码
**前置关闭**：source/ABI audit root `8d9bcee0df5f414f21c0e4b94c1ed617d58b3c6e` / Gitlink
`c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`；ChatGPT=`SOURCE_AUDIT_COMPLETE`（blockers=0），MM/Kimi=`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_IMPLEMENTATION`。

## 1. 目标与不授权范围

本 Gate 只冻结未来 CPU/static implementation 的 canonical native runtime transaction；不改变 child，
不解除任何现有 hard-stop，不执行 Python、真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、真实
native forward/loss/backward、optimizer/scheduler step、训练、评测、推理、sidecar 或 distributed。

目标不是把旧 row-wise active-wiring 参数化，而是在一个 canonical `[B_stream,T]` carrier 中建立唯一：

```text
scan -> per-stream fast-state candidate -> stream-major valid gather -> native prefix/forward/loss
-> one valid-weighted outer backward -> post-backward runtime commit -> native slow optimizer boundary
```

未获后续独立 Gate 授权前，runtime sidecar、exact resume、multi-GPU、真实数据与 LIBERO4IN1 均为禁止项。

## 2. 不可变来源与入口分工

| 职责 | 唯一已有 owner | 未来实现要求 |
| --- | --- | --- |
| canonical request/scan/prepared carrier | `canonical_segment_production_adapter.py:54-238,548-718` | 继续以 exact request/result/prepared identity 绑定；foreign、stale、cardinality 或 actual/planned mismatch 一律拒绝。 |
| clean materialization | `omni_mot_model.py:1014-1063,1440-1485` | 仅复用 `_prepare_training_data()` / `_prepare_canonical_production_inputs()` 的 clean/tokenization owner；不得注入 legacy `local_memory` payload。 |
| 现有 native candidate seam | `omni_mot_model.py:1399-1438` | `:1434` 必须在 implementation 开始时仍 fail-closed；未来仅用经审计的新、明确命名的 canonical path 替换其停止点，禁止删除 guard 后落入 ordinary route。 |
| prefix ABI | `sequence_packing/sequence.py:163-171,919-922`、`packers.py:246-254`、`cosmos3_vfm_network.py:942-966` | 每个 gathered consumer 仅接受 `[K_local,D_local]` 或 `None`；S0/PAD 恒为 `None`，投影后 hidden prefix 不改变 consumer identity。 |
| plan/loss scale | `local_memory_segment.py:109-136`、`canonical_segment_production_adapter.py:304-341,706-718` | immutable plan 在 first backward 前冻结；primary=`planned_n_valid/N_window`、auxiliary=`1/ga_effective`，不得合并或二次 `/GA`。 |
| native training lifecycle | `trainer/__init__.py:524-595,935-999` | DDP/no-sync、callback、scale/unscale、step/scheduler/zero-grad 仍由 trainer 唯一拥有；canonical objective 成立后才进入该边界。 |

审计中出现而当前 child 未实现的 fast-state slot、canonical gather bridge、attempt/replay lineage、sidecar
与 exact resume，均必须在实现中显式建 owner；不得从普通 batch、泛用 checkpoint 或 DCP 自动推断。

## 3. 最小未来实现面（尚未授权）

未来 implementation 只能在一份后续获批白名单中新增一个 canonical runtime coordinator，并对
`CanonicalProductionAdapter`、`OmniMotModel`、trainer 各作最小接线；禁止改 dataset/collate、普通
packer 语义、默认 config、checkpoint、distributed 或 legacy active-wiring。

协调器的不可变 capability 至少绑定：

```text
exact prepared request/result
immutable window plan (stream-major identities, planned count, N_window, GA member)
per-slot episode/cursor/terminal provenance
state_in numeric/graph identity
gathered Local prefixes and exact consumer mapping
one forward/backward disposition
```

它只能产生三类状态：`PREPARED`、`BACKWARD_COMPLETE`、`TERMINAL`。任何 duplicate prepare、foreign
capability、pending interleave、forward/backward exception 或 count/prefix mismatch 都 terminal fail-closed；
不得静默重排、resample、replay或提交 runtime state。

## 4. Chronology、fast state 与 gather

对每一个 stream slot，输入必须是 v0.3.5 的 `E_prev[B_stream,T,256]`、`evidence_valid` 与 exact
episode/cursor provenance。scan 是 stream-independent、`create_graph=True`、update-then-read：

```text
fresh S0: consumer valid, evidence invalid, prefix=None, state=W_bar_0 clone
valid e_t: W_t=Update(W_(t-1),e_t); M_(t+1)=Read(W_t,Q_t)
tail PAD: no update, no prefix, no loss
```

`M_local[B_stream,T,K_local,32]` 仅以 `flat=b*T+t` gather 到其 exact valid consumer；无 Local 的 S0/PAD
不得压缩、补零或移交给另一 consumer。continued slot 只接收其同 slot、前一个成功 backward 后 detached
numeric state；fresh slot 只在 admission 时 clone 当前 learned `W_bar_0`，episode boundary 后才 discard。

## 5. objective、backward 与 commit

每个 microbatch 的唯一顺序为：

```text
freeze plan -> scan/prefix -> native pack/forward/loss -> validate actual=planned
-> one primary+auxiliary objective -> one backward -> detach/commit runtime state
```

`L_inner` 仅生成 fast-state transition，绝不进入 outer objective。canonical path 不得使用 ordinary
`loss / grad_accum_iter`。full-valid case 必须精确退化为 native `(L_consumer+L_aux)/GA`；tail 以
`planned_n_valid/N_window` 加权。fast-state graph 不跨 microbatch，slow `.grad` 可跨 GA member。

backward 成功后才允许 runtime cursor/state commit；native optimizer step 绝不修改已存在 `W_fast`。GradScaler
skip 沿用 v0.3.5 Option-B：已成功的 runtime commit 保留，slow step/scheduler 不推进且 controlled slow grads
清理。forward、inner finite、backward 或 commit 前异常均零 runtime commit、零 cursor advance，并保留 exact
capability 证据后 terminalize。

## 6. 现有 hard-stop 与 sidecar 边界

`trainer/__init__.py:520-523` 的 scaler/optimizer pre-scan rejection 在本 Gate 不能删除；未来 implementation
必须先证明 objective 已形成、exact plan/GA boundary 与 disposition 均已验证，才可设计受控替代。任何实现若
让 ordinary branch、第二次 GA scale、或 optimizer 在 scan/forward 前可达，均为 `REQUEST_CHANGES`。

首轮 future smoke 仍明示 `mid-episode resume=UNSUPPORTED`。不新增 sidecar 或 checkpoint serialization；
没有 exact rank/world/config/manifest/source identity 与 detached `W_fast` restore contract 时，必须 fail closed，
不得以 generic DCP 推断兼容。

## 7. 未来 CPU/static 验收与分流

后续 implementation design 至少要指定静态/CPU tests，证明：

1. S0、continued、tail 的 prefix/cardinality/stream-major identity 精确；
2. 每 stream 单独 inner update，跨 stream 无 shared update；
3. planned/actual、N_window、primary/auxiliary、full-valid reduction、GA boundary 均精确；
4. backward 前无 detach/commit，成功后 detach numeric carry，异常和 stale capability 零 mutation；
5. canonical route 永不走 legacy Local payload、ordinary `/grad_accum_iter` 或 pre-objective optimizer；
6. 缺 fast-state owner、gather mapping、replay lineage、sidecar restore owner 时分别 fail closed，而不是伪造支持。

任何需要真实 native forward、optimizer、checkpoint I/O、GPU 或 distributed 才能证实的项必须留给独立 GPU/
sidecar Gate，不能用本 CPU/static Gate 代替。

## 8. 请求 verdict

请求三方仅对本文件的新 formal root/Gitlink 给出：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_CPU_STATIC_IMPLEMENTATION
```

或 `REQUEST_CHANGES(file:line)`。批准只允许创建下一份 CPU/static implementation design；不授权 child
实现、真实 I/O、GPU、torchrun、native forward/backward、optimizer、checkpoint/sidecar、训练、评测、推理或
LIBERO4IN1。
