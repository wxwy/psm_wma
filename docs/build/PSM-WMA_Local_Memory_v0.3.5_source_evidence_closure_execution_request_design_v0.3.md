# Source-evidence closure execution request design v0.3

**Gate**：`G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN-REFREEZE`
**状态**：docs-only；待三方审核。

## 1. 目的与 v0.2 的显式 override

本文件仅处理 ChatGPT 对 v0.9 exact-pair review 提出的 HIGH-1：v0.2 的单次 activation 要求
materializer → collection → source-evidence producer → root audit 的完整 transaction，但当前正式仓库只有
authority materializer 与 collection executor；不存在 source-evidence producer 的 production entrypoint。
因此，不能把仅有 stage-1 的可执行 materialization 伪称为 v0.2 的全 transaction instance。

本 v0.3 只 supersede v0.2 §3 的 activation granularity，明确将其改为两个受独立 review 互锁的阶段：

1. **Stage 1 authority-root materialization**：仅以已关闭 materializer formal parent 创建固定 authority ref，
   生成 authority tuple 后硬停；
2. **Stage 2 source-evidence closure**：仅在 Stage-1 authority tuple 经独立三方 binding、且 source-evidence
   producer/record/receipt/root-audit production entrypoints 已另行实现并关闭后，才构造其 exact request。

除上述切分外，v0.2 的 input identity、freshness、fail-stop、rollback、禁止范围和 receipt-root 独立审核
合同继续生效。这个 refreeze 不授权 Stage 1/2 execution，也不实现任何 production code。

## 2. Stage 1 冻结合同

Stage 1 exact request 必须以 formal parent
`b3595395427114f73ff53a19a0c2b9180e39905f`、child
`93a89ba61306d840a008813f62f26a34d54850f4` 与唯一 ref
`refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` 为 bound authority。启动前必须同轮绑定：

- selection/config raw bytes、FD identity 与 SHA；
- complete outer launcher argv、sanitized environment、bootstrap contract/owner FD；
- formal-tree tool closure、Git/Python identity、cwd/index/evidence identity；
- fixed ref local/remote dual-end absent observation；
- canonical whole-request SHA-256。

任何字段缺失、过期、漂移或 ref 非 absent 均为 `BLOCKED_AUTHORITY_NOT_CLOSED`，零 mutation。Stage 1
PASS 仅产生 authority tuple；其 review/ledger commit 不得成为 candidate parent，也不得被当成 Stage 2 receipt。

## 3. Stage 2 前置与禁止

Stage 2 必须重新取得并审核以下独立资产，不能由 Stage 1 推断：production source-evidence producer、record
writer、receipt constructor、publication verifier 与 root audit entrypoint；它们的 formal root/child、argv、
identity、source-root binding、output path/ref/rollback ABI。Stage 2 一次 activation 仍须按 v0.2 的 collection →
producer → receipt root → root audit 顺序运行，PASS 后停于 receipt-root review。

本 refreeze 及任何 Stage-1 approval 均不授权 collection/receipt/source-evidence/publication、child/runtime
变更、真实 source/checkpoint/manifest/data/cache I/O、GPU/CUDA/torchrun、训练、评测、推理或 LIBERO4IN1。

## 4. 审核请求

请求最终 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT_MATERIALIZATION_REQUEST
```

或 `REQUEST_CHANGES(file:line)`。批准只允许据 §2 构造并审核一份 fully fresh-bound Stage-1 request；
不授权其执行。
