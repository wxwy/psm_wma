# PSM-WMA Local Memory v0.3.5 Canonical Native Runtime Source-Audit 设计 v0.1

**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-SOURCE-AUDIT-DESIGN`
**状态**：docs-only；待独立审核；不授权实现或执行
**根仓基线**：`e24e944a1dc8cfe2cab97ab19157f69be770c4f3`
**child/Gitlink 基线**：`c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`

## 1. 目的与边界

此前 Gate 仅关闭 canonical native forward/loss 的 synthetic CPU/static capability、loss
algebra 与 failure-disposal contract；它刻意在真实 `training_step()` 的 scaler/optimizer
前 hard-stop（`cosmos_framework/trainer/__init__.py:520-523`）。本设计只定义下一步
**只读源码审计**：找出在不改变 v0.3.5 chronology、v0.3.8/0.3.9 GA transaction 与原生
Cosmos loss/scaling 语义的前提下，真实 runtime 所必须新建的 implementation design 边界。

本 Gate 不修改 child、配置、checkpoint、数据或 cache；不运行 Python、native forward/loss/
backward、optimizer/scheduler step、CUDA/GPU、torchrun、训练、评测、推理或 LIBERO4IN1。
它不能解除现有 hard-stop，也不能成为 GPU smoke 或训练授权。

## 2. 审计输入与不可变约束

审计以 detailed addendum v0.3.5（`S0` Local absent、`[B_stream,T]` stream-major、past-only
evidence、`T=16` 默认 TBPTT）和 canonical training/runtime contract v0.3.8/0.3.9 的
immutable plan、suffix-only retry、partial slow-gradient discard 为语义 authority。

必须保持以下既有 source facts，任一不能在审计中证明即为 `REQUEST_CHANGES`：

1. 普通训练的 DDP sync、callback、forward、backward、GA boundary 与 optimizer seam 在
   `trainer/__init__.py:524-590`；canonical route 不得绕过其 native distributed ownership。
2. canonical-native CPU/static lifecycle 是 one-shot capability：validate → mark backward →
   one un-divided-by-GA backward → prepare/commit，见 `trainer/__init__.py:935-999`；真实路线
   必须重新冻结 GradScaler、optimizer 与 scheduler 的等价顺序，不能删除 guard 即执行。
3. `CanonicalProductionAdapter` 只把 exact pending scan 交给 native capability，且 commit
   mutation 边界在 `canonical_segment_production_adapter.py:706-768`；真实路线须证明
   post-mutation failure 的证据/slow-gradient disposition 仍可恢复审计。
4. Segment S0/PAD、opaque payload、stream-major gather 语义来自
   `local_memory_segment.py:27-106`；不得把 S0 从 native consumer count 删除、给 PAD 造
   payload 或重排以迎合 packer。

## 3. 必答 source/ABI 地图

只读审计必须对当前 child 精确记录 `file:line -> contract`，而非以历史文档替代源码：

| 审计项 | 必答问题 |
| --- | --- |
| real model seam | `omni_mot_model.py` 中 canonical diversion 后，哪个 exact seam 可同时持有 scan-bound working batch、native sequence preparation、Memory Prefix 与 native loss terms？该 seam 前后是否存在 legacy Local 注入。 |
| packer/flatten | `data/generator/sequence_packing/sequence.py` 与 `packers.py` 中 payload order、multi-vision/action/sound cardinality、Memory Prefix `[B,K_local,2048]`、S0 absent 和 PAD exclusion 分别由谁验证。 |
| native losses | `model/generator/algorithm/loss/flow_matching.py` 与 model loss owner 中 weighted item populations、sample-level scale、LBL auxiliary 和 final scalar 的唯一 owner；须证明 canonical `N/K_m` reduction 不重复缩放。 |
| real GA/scaler | trainer 的 `GradScaler.scale`、unscale、optimizer step、LR scheduler step、zero-grad 与 DDP no-sync 的实际顺序；须明确如何以 v0.3.8 suffix recovery 的 `GA_effective/N_window` 替代 ordinary `/grad_accum_iter`，且不提前修改。 |
| producer/cache | dataloader/collate 到 canonical carrier 的 exact object/identity path；是否能读出 LIBERO4IN1 latent-cache 的 manifest/config/source digest、episode/cursor/terminal 与 raw visual/action evidence，而不在 model 侧猜测。 |
| persistence/distributed | checkpoint save/load 和 rank ownership seam；首轮 GPU smoke 可否明示 mid-episode resume unsupported。任何要声称 resume/distributed supported 的路径必须具有 sidecar schema、rank-local state 与 restore audit。 |

## 4. 审计结论与后续分流

审计仅可输出以下之一：

- `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_IMPLEMENTATION`：所有 §3
  seam 有唯一 source owner，且可形成一个仍不运行真实工作负载的 implementation design；
  该批准不授权 child 实现、GPU smoke 或训练。
- `REQUEST_CHANGES`：任一 seam 需要静默重排 payload、改变 native loss/GA scaling、缺失
  cache identity、无法隔离 legacy Local、或无法定义 failure/checkpoint/distributed owner。
  必须给出 `file:line` 与所需的独立 design Gate。

审计完成后，才可依次新建并审核：runtime implementation design → CPU/static implementation
→ single-GPU smoke design → approved GPU smoke → LIBERO4IN1 matched-smoke design → approved
matched smoke → formal training Gate。任何步骤均不可由本审计或此前 CPU/static closure 推导为
已授权。

## 5. 验收

本 Gate 的验收仅为：审计设计能逐项约束 §3 的 source map、输出明确 verdict 和
`file:line` 级 fail-closed 结论；root `git diff --check` 通过。不得执行项目代码。
