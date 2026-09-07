# PSM-WMA Local Memory v0.3.5 Supersession / Migration Design v0.1

**日期**：2026-09-07  
**状态**：docs-only implementation design；未授权代码、GPU、checkpoint I/O、训练、评测或推理  
**适用分支**：根仓 `V2`  
**上游语义**：`PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`  
**当前 child 基线**：`80aec090688e3c710c41e1dfd86b6500773db2c7`

## 1. 目的与禁止事项

本文件把 v0.3.5 的 rolling training semantics 转成可审核的迁移边界，解决旧 active-wiring 与新 segment-level 训练路线不可静默混用的问题。它不是 v0.3.5 canonical v1.0，也不授权实现；实现前必须获得本设计的三方同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_MIGRATION_DESIGN`。

禁止：修改 `cosmos-framework`、接入生产 trainer、真实 checkpoint/data/cache I/O、GPU/CUDA/torchrun、训练/评测/推理，以及继续扩展旧 `TTTLifecycle.process_sample()` 路径。

## 2. 不可改变的 v0.3.5 语义

首版实现必须同时满足：

```text
T = 16
B_stream = 8
N_consumer_nominal_micro = 128
fresh episode 必须从 step0 admission
S0 无 Local；e0 -> update -> M1
每个 [B_stream,T] microbatch 内完成完整 TTT graph
stream-major flat(b,t)=b*T+t
PAD 不产生 evidence/update/Local/Cosmos loss
outer loss 按实际 valid-consumer exposure 归一化
TTT graph 不跨 microbatch；slow .grad 可跨 GA
backward 后才 detach/commit W_fast
optimizer.step 不修改已有 W_fast
首轮 K_local=1、state/dt/age=OFF、W_fast/f_inner=fp32
```

旧路线的以下行为必须被 supersede，而不是通过参数开关继续保留为生产分支：

```text
1 micro-batch = 1 evidence row
detached candidate + closing-row replay/materialize
pre-write witness 作为生产 Cosmos 输入
跨 microbatch 延续同一 autograd graph
```

旧 C5A/C6/runtime authority 的 provenance/identity/transaction 逻辑只有在下节明确映射后才可复用。

## 3. 新生产数据合同与内部接口

### 3.1 Segment 输入

新 production seam 接收一个 logical segment，而不是单行：

```python
SegmentBatch(
    visual_summary: Tensor[B_stream, T, 96],
    executed_action: Tensor[B_stream, T, 10],
    consumer_valid: BoolTensor[B_stream, T],
    evidence_valid: BoolTensor[B_stream, T],
    episode_id: tuple[str, ...],
    category: tuple[str, ...],
    start_step: LongTensor[B_stream],
    end_step: LongTensor[B_stream],
    terminal: BoolTensor[B_stream],
    provenance: SegmentProvenance,
)
```

`consumer_valid` 与 `evidence_valid` 必须共享 `flat(b,t)=b*T+t` 映射；`S0` 可 valid 但 evidence 必须 false；PAD 两者都 false。每个 slot 在 segment 内只能属于一个 episode。

### 3.2 TTT scan 输出

```python
scan_segment_many(segment, state_in, create_graph=True)
    -> local_tokens[B_stream,T,K_local,32]
    -> state_out[B_stream,...]
    -> scan_provenance
```

scan 沿 `t` 递归、沿 `B_stream` 并行；每个 valid evidence row 独立完成一次 K/V write，使用 update-then-read；无 evidence 的 S0/PAD 不更新 W。`L_inner` 只定义 fast transition，不并入 outer loss。

### 3.3 Cosmos 适配

优先路径：先 stream-major flatten，再 `consumer_valid` gather；Cosmos 只接收 `N_valid_micro <= 128` 个真实 consumers，并返回可映射回 flat index 的 native per-consumer loss 或等价 unreduced loss。

若当前 packer 不能 variable gather，必须新增等价 mask ABI，并证明：PAD 不产生可训练 zero sample、native loss reduction 可恢复 valid-consumer 加权、Local/consumer/provenance 对齐保持不变。未完成该证明不得进入实现。

## 4. scheduler、tail 与 loss 接缝

### 4.1 WeightedDeficitScheduler

scheduler 只输出 fresh episode admission；状态至少包含 target `p_c`、累计 valid-consumer exposure、seed、category queue permutation/epoch、slot ownership 和 provenance digest。episode 未结束前不得 rebind；load/decode/cache identity 错误 fail closed，禁止随机换 chronology row。

### 4.2 planned counts

每个 GA window 在第一次 backward 前必须拥有每个 microbatch 的 planned `N_valid_micro`；该 metadata 由 scheduler/packer 先规划，不得为获取 count 提前加载全部 tensor。多卡实现另起 Gate，首版只要求单卡 contract。

### 4.3 native loss weighting

若 `L_mu_native` 是 valid consumers 的 mean，则 backward 使用：

```text
N_valid_window = sum_mu N_valid_micro[mu]
scale_mu = N_valid_micro[mu] / N_valid_window
loss_for_backward = scale_mu * L_mu_native
```

`N_valid_window=0` 必须 fail closed；full batch 时精确退化为 `1/GA`。loss reduction 的实际 trainer seam、unreduced/native mean 证据和数值 fixture必须在 implementation design 中锁定。

## 5. 新旧组件迁移矩阵

| 现有组件 | v0.3.5 处理 | 约束 |
|---|---|---|
| `TTTLifecycle.process_sample` | 生产路径废止 | 不得作为 segment adapter 逐行循环复用 |
| `ProductionLocalMemoryRuntime` authority | 仅保留 identity、admission、transaction provenance | 不得保留 closing-row replay 作为 Cosmos graph 来源 |
| `ContinualTTTLocalMemoryCore` | 复用 projection/KVB/read_many/reset | 新增/冻结 batched scan API |
| `LocalEvidenceEncoder` | 复用视觉+action 主分支 | state/dt/age 必须真实关闭，不得喂可训练常数 |
| `local_memory2llm`/prefix path | 复用 `[K_local,32] -> [K_local,2048]` | gather 后必须保持 consumer 对齐 |
| manifest/wrapper provenance | 复用 source identity/terminal 证据 | 新增 segment slot/cursor/valid-count schema |
| trainer backward/GA seam | 重写为 segment graph 生命周期 | backward 后 commit；graph 不跨 microbatch |
| slow checkpoint contract | 复用 slow-only strict contract | runtime W/queue ownership 另起 sidecar Gate |

## 6. 实施分阶段与审核门

1. **Static contract design**：冻结 `SegmentBatch`、flatten/gather、valid loss、scheduler state 和 migration matrix；本文件通过三方审核后才可进入 CPU implementation。
2. **CPU segment core**：只实现 batched scan、padding、flatten/gather、per-stream inner loss、loss weighting、scheduler fixtures；禁止 Cosmos/GPU/真实数据。
3. **CPU active adapter**：在新 seam 上接 Cosmos synthetic consumer spy，证明调用顺序、row identity、backward 后 commit、异常回滚和 disabled parity；旧 lifecycle 不接入。
4. **Canonical GPU smoke design**：单独冻结资源、higher-order gradient、显存、`K_local=1`、`8x16` 和 no-state/no-dt/no-age；三方批准后才可运行一次 GPU smoke。
5. **LIBERO4IN1 matched smoke design**：单独绑定 exact-window latent cache、4-suite manifest、checkpoint/config identity 和停止条件；三方批准前不得读取正式训练输入或启动训练。
6. **正式训练 Gate**：只有 GPU smoke、matched smoke 和正式训练命令分别通过三方同 SHA Gate，才能启动 Local Mem 在 LIBERO4IN1 latent cache 上的正式训练。

## 7. 必须在 implementation design 中补齐的验收

```text
A  flat round-trip 与 Local/consumer/provenance exact identity
B  S0/PAD no-evidence、no-update、no-loss
C  fresh step0、continued cursor、terminal reset、无跨 episode 泄漏
D  per-stream inner scale 不随 B_stream 改变
E  valid-consumer weighted loss 与 full-batch 1/GA 精确等价
F  N_valid_window=0、load failure、forward/backward exception fail closed
G  backward 后才 commit；GradScaler skip 只阻止 slow step
H  TTT graph 不跨 microbatch，slow grad 可跨 GA
I  scheduler 长期 exposure 接近 p_c，seed/permutation 可复现
J  state/dt/age branch 真关闭且 disabled parity 逐位保持
K  train/inference 使用相同 past-only update-then-read 顺序
L  所有 provenance 绑定 segment slot、episode、cursor、valid counts
```

## 8. 当前状态与停止条件

本设计提交前后均不执行项目代码；只允许 `git diff --check`、文档审阅和三方审核。若 v0.3.5 上游继续产生 rolling 修订，必须新建版本并重新核对本迁移矩阵；不得在未收敛文档上实现或训练。
