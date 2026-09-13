# PSM-WMA Local Memory v0.3.5 单卡 Smoke 设计 v0.1

**日期**：2026-09-13
**状态**：docs-only design；待三方审核
**Gate**：`G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`
**适用分支**：根仓 `V2`
**当前 Gitlink 基线**：`93a89ba61306d840a008813f62f26a34d54850f4`

## 1. 目的与边界

本设计冻结首次 canonical single-GPU smoke 的唯一执行边界。它验证 Local
Memory 的真实 native forward/backward、slow optimizer/scaler 和 segment chronology
能在一个受控、小步数运行中闭合；它不是 matched experiment、收敛实验或正式训练。

本设计只授权后续编写和审核 single-GPU smoke runbook/命令的准备工作。它本身不读取
checkpoint、manifest、latent cache 或数据，不创建 source-evidence、candidate、record、
receipt 或 publication，不改 child 代码/配置，不申请 GPU，不启动 CUDA、torchrun、训练、
评测或推理。

## 2. 固定语义来源

下列事实不在本 Gate 重新设计：

- Local chronology、`S0` Local absent、`S_t <- e_(t-1)`、update-then-read、`T=16`、
  `B_stream=8`、`K_local=1`、fp32 fast state，来自
  `PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §0--§17；
- segment、tail、valid-consumer loss partition、GA failure transaction、GradScaler skip
  与 disabled feature branches，以已通过 canonical-semantics remediation 的 v0.3.9
  系列及其后继 native CPU/static contracts为准；不得回退至 v0.3.6 的旧 GA-window 语义；
- source、checkpoint、manifest、config 的唯一 authority 仍由已审 immutable
  source-evidence collection/closure 路线提供。source-evidence closure 完成后直接进入
  本 Gate 的 execution approval，不新增横向 provenance Gate。

## 3. 执行准入（全部为硬前置）

真正 smoke 命令只能在同一份 execution request 中逐项绑定并复核：

1. 已审 source-evidence post-commit receipt，能唯一给出 formal root、record blob、
   canonical model config、checkpoint descriptor、manifest/source-input digest；
2. 当前 root/child tree 与 receipt 所绑定的 source identity 一致；任一 Gitlink、blob、
   config、descriptor 或 manifest digest 不同即 FAIL，禁止“就地更新”；
3. 已审 Local Memory native runtime/feature/config/optimizer CPU/static contracts在当前
   child Gitlink 上可复核，且其 exact parameter inventory 与 strict checkpoint policy
   已冻结；
4. 单卡环境、CUDA device、driver、PyTorch、CUDA runtime、可用显存和 conda/venv
   interpreter 由 runbook 在启动前只读记录；无可用单卡即 BLOCKED，不降级 CPU；
5. `world_size=1`、无 `torchrun`、`num_workers=0`、无 resume、无 sidecar resume；
   任一不符即 admission FAIL；
6. 输出根为新建、显式命名的 smoke-only path；任何既有 output、正式训练 output 或
   checkpoint 目录均不得复用。

## 4. 唯一 smoke 配置

execution runbook 必须从 receipt-authoritative config 派生一个不可覆盖的 smoke config，
并写入 resolved copy。它至少固定：

```text
world_size = 1
B_stream = 8
ttt_tbptt_steps = 16
K_local = 1
state/dt/age feature = OFF
W_fast storage and inner compute = fp32
num_workers = 0
resume = disabled
exact mid-episode resume = unsupported
```

步数只能在 execution request 中指定为有界正整数，且上限不得超过 `100`。它必须覆盖：

- 至少一个 fresh `S0`、一次 shifted-evidence update/read 和一次 continued segment；
- 至少一个 tail/PAD 或经 authority manifest 证明不存在 tail 的等价说明；
- 至少一次真实 slow optimizer boundary；
- 一次受控的 GradScaler/finite 状态记录（若 native precision path 无 scaler，明确记录
  `not-applicable`，不伪造 skip）。

## 5. 运行事务与停止条件

每个 segment 的 native forward/backward 后，只有所有 finite/identity/actual-valid-count
检查成功才能提交 fast chronology。GA window 的 planned valid counts 必须在第一次
backward 前取得，且每个 microbatch 在 backward 前断言：

```text
planned_N_valid_mu == actual gathered consumer count
```

若任一 microbatch在该 GA window 内失败，保留之前已成功的 fast chronology/cursor/exposure，
清空整个 partial slow-gradient window，不做该 window 的 slow optimizer/LR step，并以新的
planned denominator开始下一个 window；不得重放、resample 或重写已消费 chronology。

以下任一事件是立即停止并保留最小日志/JSON证据的 FAIL：NaN/Inf、OOM、CUDA error、
source/config/manifest identity drift、planned/actual count mismatch、跨 episode W leak、
非法 PAD/Local token、`world_size != 1`、任何 resume 尝试、超出批准步数，或任意未声明的
文件写入。FAIL 后不得自动重跑或扩大步数。

## 6. 最小产物与 PASS

runbook 必须将产物限制在该次 smoke output 根内，并至少生成：

```text
resolved_smoke_config.toml
authority_binding.json
environment.json
segment_chronology.jsonl
optimizer_scaler.jsonl
smoke_summary.json
```

`smoke_summary.json` 的 PASS 必须同时断言：

1. authority/config/manifest/checkpoint bindings 全部一致；
2. 所有已执行 forward、inner update、native loss、backward、slow optimizer state 均 finite；
3. S0 absent、shifted evidence、stream-major gather、tail/PAD 与 state commit 满足 canonical
   chronology；
4. 实际 valid count 与每一 planned count 一致，full batch时 loss scaling 退化为 native
   `1/GA`；
5. 只发生已批准次数的 slow steps，且没有 DDP、torchrun、sidecar/resume、评测或推理；
6. 输出只位于本次 smoke root，且不存在训练完成、收敛、SR、checkpoint reload 或部署结论。

PASS 只说明该有界单卡路径可运行。它不授权 runtime-sidecar、LIBERO4IN1 matched smoke、
多卡、20--100 step 以外的训练，或正式 Local Memory training。

## 7. 后续顺序与审核请求

```text
source-evidence controlled closure + post-commit receipt
  -> 本 single-GPU smoke design 三方批准
  -> single-GPU smoke execution runbook/command 的三方批准
  -> 一次有界 single-GPU smoke
  -> runtime-sidecar design/CPU-static/resume smoke
  -> LIBERO4IN1 matched-smoke design and approval
  -> matched smoke
  -> formal-training design/command approval
  -> formal Local Memory training
```

本文件请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION
```

或 `REQUEST_CHANGES(file:line)`。三方同一 formal root/Gitlink 批准前，不得运行 GPU、
读取真实输入、改 child 或启动训练。
