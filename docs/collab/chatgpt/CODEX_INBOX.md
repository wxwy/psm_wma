# ChatGPT → Codex canonical live Inbox

## Rollover continuity — 2026-09-08

- Immediate prior archive: `docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-08_bc25211.md`
- Prior live Inbox blob SHA: `4984456d6a91864f0a61d5c51feefbaa2a996bab`
- Pre-rollover root HEAD: `bc252114b6799559a172a3061677562c8df565a2`
- Current unresolved Gate: `G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`
- Superseded review target: root `6828b55400d49ef82f1eed895fd609bf8179c3a8`; Gitlink `80aec090688e3c710c41e1dfd86b6500773db2c7`; MM and DS literal verdicts: `REQUEST_CHANGES`.
- Current formal target: root `bc252114b6799559a172a3061677562c8df565a2`; Gitlink `80aec090688e3c710c41e1dfd86b6500773db2c7`.
- Current design: `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md`.
- Latest detailed external review files: none for the current target. MM/DS prior target review was returned through their tmux panes and is summarized in `SESSION.md` / `TODO.md`.

## 2026-09-08 — v0.3.6 canonical remediation design review request @ bc25211

Awaiting review — 🚨 审核申请已发出（根仓 bc252114b6799559a172a3061677562c8df565a2；子模块/Gitlink 80aec090688e3c710c41e1dfd86b6500773db2c7）

任务/Gate：`G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`。请审阅 `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md`。本轮只修复旧 v0.3.5 migration target `6828b55` 的 MM、DS、Codex `REQUEST_CHANGES`，无 child 代码变化，无 GPU、真实数据/cache/checkpoint I/O、训练、评测或推理。

需核对的冻结事项：① segment ABI 明确 `S_t <- e_(t-1)` 且 S0 Local absent；② `training_stream_end`、tail/rebind 与 sparse Memory Prefix；③ rank-local main-process scheduler、`num_workers=0`、episode scheduler 与 slow LR scheduler 的 GradScaler skip 语义分离；④ 未缩放 native model loss 的有限性谓词和 abort-before-commit；⑤ primary consumer loss 按 actual valid exposure、auxiliary load-balancing loss 按 `1/GA`，Local path 禁止旧 trainer 再除 `/GA`；⑥ state/dt/age 真移除后的 optimizer/checkpoint identity；⑦ formal training 前 runtime-sidecar Gate。

请求针对同一根仓/Gitlink SHA 给出 literal verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN` 或 `REQUEST_CHANGES`，并附 `file:line`。若批准，仅授权下一步新建 CPU/static implementation design；禁止 child/runtime/packer/trainer 修改、GPU/CUDA/torchrun、真实 checkpoint/data/cache I/O、训练/评测/推理、P4/P5、B2-T 或 LIBERO4IN1。

## 2026-09-08 — v0.3.6 review outcome

- Formal target: root `bc252114b6799559a172a3061677562c8df565a2`; Gitlink `80aec090688e3c710c41e1dfd86b6500773db2c7`.
- DS: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN` after confirming old 5 HIGH and 2 MEDIUM are closed; only non-blocking implementation-design notes remain.
- MM: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN`; explicit literal re-confirmed in `mm:0.0` after its completed review.
- Authorized next action: create the CPU/static implementation design only. Still prohibited: child/runtime/packer/trainer modification, GPU/CUDA/torchrun, real checkpoint/data/cache I/O, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1.
