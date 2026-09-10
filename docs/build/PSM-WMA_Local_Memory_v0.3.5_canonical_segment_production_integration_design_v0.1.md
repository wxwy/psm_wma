# PSM-WMA Local Memory v0.3.5 Canonical Segment Production Integration 设计 v0.1

**日期**：2026-09-10  
**状态**：docs-only design；须三方对本文件 formal pair 同 SHA 批准后才可开始下一阶段 source-ABI audit  
**任务/Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-INTEGRATION-DESIGN`

## 1. Authority、目的与禁止范围

本文件以 `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §1--§20，特别是 §18、§20.1--§20.2 为唯一算法/训练语义 authority；其目标是冻结从已经关闭的 synthetic scheduler contract 到真实 Cosmos 生产接入之前的**实现路线**。

已关闭的前置 Gate 为 formal root `ae14754de9ca6c5d74b3ec8a72222fe0280e0bcc` / child `3a078f28f3d107bb633c932271f86498f7c427f7` 的 `CANONICAL-SEGMENT-ADAPTER-SCHEDULER-CPU-STATIC-IMPLEMENTATION`。该 Gate 只证明 metadata-only `CanonicalBatchScheduler`/`CanonicalBatchWindowTransaction` contract，不是 producer、packer、model-forward 或 trainer implementation authority。

本文件只授权后续创建一个 docs-only source-ABI audit。它不授权修改 child、真实 cache/data/checkpoint I/O、CUDA/GPU、torchrun、runtime sidecar、LIBERO4IN1、训练、评测或推理；也不冻结 optimizer/checkpoint/config schema。

## 2. 必须 supersede 的旧路线

下列旧 row-wise active-wiring 生产路径不得作为 v0.3.5 的参数化变体复用：

```text
1 micro-batch = 1 native window = 1 evidence row
跨 row 累计一个 TTT segment
closing-window replay/materialize witness graph
```

其 `CanonicalSegmentRuntimeOwner`、`CanonicalLocalMemorySegmentAdapter`、`production_segment_bridge.py`、`production_active_wiring.py` 中的 capability、fail-closed、terminal/retry、callback 或 provenance 代码可以作为 source audit 对象和历史证据，但不能被静默绑定到 v0.3.5 production path。

v0.3.5 的唯一目标形态是：

```text
one native microbatch
    = one logical [B_stream, T] segment batch
    -> shifted evidence scan/update/read entirely inside this microbatch
    -> stream-major flatten + gather valid consumers
    -> exactly one native Cosmos forward and outer backward
    -> only after successful backward detach/commit numeric W_fast
```

因此旧 `GAWindowPlan`、`RankLocalSegmentScheduler`、`LocalMemoryTransaction` 与旧 owner 不能被当作新的 production scheduler/state authority；它们仅在 source audit 中逐项判定为“保留作 provenance/fail-closed helper”或“旁路/删除”。

## 3. 已冻结的 production ABI 语义

后续 source-ABI audit 与 implementation 必须同时满足以下语义；任何现有 seam 无法满足时必须 fail closed 并另起设计，不得塞入兼容 fallback。

| 项目 | 冻结语义 |
| --- | --- |
| logical segment | per-rank `[B_stream, T]`，首轮固定 `B_stream=8`、`T=16`，不要求所有 slot full-length |
| chronology | fresh `W_fast[-1]=clone(W_bar_0)`；`e_t -> Update(W_fast[t-1], e_t)=W_fast[t] -> M_{t+1}=Read(W_fast[t], Q_t)` |
| evidence | `visual_summary_t(96)` + 已执行 action `(10)`；state/dt/age 是真正关闭的分支，不得喂常数 |
| first consumer | S0 是 valid Cosmos consumer，但无 Local prefix/evidence，绝不构造 `e_-1` |
| tail | logical PAD 不 update/read、不计 valid、不在 block 中 rebind；优先 flatten 后 gather，PAD 不进入 Cosmos forward |
| flatten | stream-major `flat(b,t)=b*T+t`，gather 后顺序不可变 |
| Local output | 首轮 `K_local=1`；raw `[N_valid,1,32]` 经 `local_memory2llm` 成 `[N_valid,1,2048]` 后进入 Memory Prefix；S0 的 prefix 为 absent，不是零 token |
| backward/commit | 一个 microbatch 的完整 TTT graph 只由其一次 outer backward 关闭；成功后才 detach/commit state；异常/skip fail closed |
| GA | slow grad 可跨 GA；每 member 的 outer contribution 按 `N_valid_micro / N_valid_window` 加权；full valid 时精确退化为原 `1/GA` |

## 4. 分阶段实现路线

### P0：source-ABI audit（下一个 Gate）

只读审计必须在真实 child source 中给出下列精确 `file:line` 结论与最小接入点：

1. 原生 data batch 从 dataset/packer 到 `OmniMoTModel` 的 payload、batch dimension、consumer loss mask 与 flatten order；裁决 §20.2-A 的 variable valid gather 是否已有等价能力。
2. 原生 consumer loss 的 reduction 与 `ImaginaireTrainer.training_step` 的 backward/GA seam；裁决 §20.2-B/C，证明 planned valid counts 的 metadata 来源不要求预加载 tensor。
3. Memory Prefix 接收的位置、`local_memory2llm`/modality embed 的确切 shape 和 S0 absent 表达；不得由旧 `data_batch["local_memory"]` row-list 合同推断。
4. `LocalEvidenceEncoder` 的 state/dt/age branches、参数注册和 call path；裁决 §20.2-E 的真实关闭方法。
5. `CanonicalBatchScheduler` contract 与未来 producer 的边界；定义由 producer 提供的 immutable `MicrobatchPlanMember` metadata、slot/episode/provenance/count fields，而不是让 trainer 重新推导 chronology。
6. 旧 owner/bridge/active-wiring 的逐项表：`retain-as-provenance`、`reuse-as-fail-closed-helper`、`superseded/bypassed`；特别覆盖 pending slow resolution、retry、terminal、legacy callback filter、row-wise witness materialization。

P0 产物必须是 docs-only audit；不得顺便改 adapter/trainer/packer。它的 PASS 是一个完整 source map 加上每个 §20.2-A--F 的明确“可复用 / 必须新实现 / 需要另起 Gate”结论。

### P1：production ABI implementation design

仅在 P0 三方批准后创建。该设计必须冻结：

```text
SegmentBatchProducer -> CanonicalBatchScheduler.freeze_plan(GA window metadata)
    -> one [B_stream,T] evidence/TTT scan module
    -> stream-major valid gather + Memory Prefix payload
    -> exact native Cosmos forward/loss reduction
    -> member-bound backward -> atomic detach/commit scheduler frontier
```

它必须给出精确白名单、输入输出 dataclass/schema、native model/trainer hook、real reduction formula、PAD/gather 实现、GA planned-count planning、exception/GradScaler disposition、以及 CPU/static tests。P1 不自动授权 implementation。

### P2：CPU/static production integration implementation

只在 P1 三方批准后实施，并单独 closure review。它必须实际替代而非并存地绕开 row-wise witness materialization；No-Local path 字节语义等价；所有 P0/P1 assertions 均有 CPU tests。该 Gate仍不授权真实 I/O/GPU。

### P3：single-GPU canonical smoke design

只在 P2 closure 后进行，单独裁决 v0.3.5 §20.2-G：真实 model/latent-cache 输入、显存、higher-order gradient、fp32 `W_fast`、loss scaling、输入/输出/stop 条件。审批前不得执行 GPU。

### P4：runtime sidecar/distributed/long-train designs

独立于 P3。mid-episode exact resume、world-size change、runtime sidecar 和正式 LIBERO4IN1 training 均属于 §20.2-H，不能被 P0--P3 推定为已授权。

## 5. P0 审核验收与失败分流

P0 design 复审必须检查：

1. 是否明确将 row-wise active-wiring 与 segment-level v0.3.5 分离，且无隐式“复用旧 owner 即等价”的假设；
2. 是否逐项覆盖 §20.2-A--F，并将 G/H 留给后续独立 Gate；
3. 是否把 S0、PAD、stream-major gather、actual-valid weighted GA、post-backward detach/commit 作为 native ABI，而非测试 double 的推断；
4. 是否不给任何真实 producer/packer/model/trainer/GPU/训练权限；
5. 是否要求下一 audit 给出可复核 source `file:line`、实际 schema 与 fail-closed 分流。

若 source audit 发现 Cosmos 无 variable-valid gather、loss reduction 不可安全重加权，或 Memory Prefix 无 S0-absent 表达，P0 必须返回 `REQUEST_CHANGES` 或将该项目拆为新的 design Gate；禁止借 PAD zero sample、常数 evidence、loss 后处理或旧 row-wise replay 偷换语义。

请求唯一设计 verdict：

```text
APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_INTEGRATION_SOURCE_ABI
```

