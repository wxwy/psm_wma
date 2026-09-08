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

---

## 2026-09-08 — ChatGPT independent review: v0.3.6 canonical semantics @ bc25211

**Verdict: REQUEST_CHANGES**

Formal target:
- root design SHA: `bc252114b6799559a172a3061677562c8df565a2`
- child/Gitlink baseline: `80aec090688e3c710c41e1dfd86b6500773db2c7`

Closed relative to `6828b55`: shifted previous-evidence ABI, `training_stream_end`/tail/rebind, sparse Local absence, episode-vs-slow LR scheduler split under GradScaler skip, unscaled native-loss finiteness, primary/aux loss partition + unique Local scaling ownership, physical state/dt/age disable with inventory refreeze, and runtime-sidecar Gate.

Blocking finding:
1. **HIGH — GA-window partial failure semantics are not atomic.** `PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md:78-88,92-121` commits successful segment fast chronology after each backward while `N_window` is fixed before the first GA backward. If a later microbatch load/forward/backward fails, earlier slow grads are already scaled by the original denominator and earlier fast chronology is already committed, but the design does not freeze whether the partial slow-grad window is discarded, continued, rescaled or replayed. It also does not explicitly bind planned `N_valid_mu` to the actual gathered count before each backward.

Acceptance: freeze one GA-window transaction rule. At minimum require planned==actual valid count before backward, define exact disposition of accumulated slow grads/optimizer/LR scheduler/remaining microbatches after a later failure, and preserve chronology/no-replay consistency. A deterministic acceptable policy is: retain already successful fast chronology commits, zero/discard the entire partial slow-gradient GA window, perform no slow optimizer/LR-scheduler step for that window, and start the next GA window with a newly planned denominator; otherwise freeze equivalent mathematics/rollback explicitly. Add CPU acceptance fixtures for failure at microbatch 0 and after at least one successful backward.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v035_canonical_semantics_v036_bc25211.md`

Review commit:
`2dfd518332d62378f8f27bb2adfc251d71b57d6a`

This verdict is design-only. Child/runtime/packer/trainer changes, GPU/CUDA/torchrun, real checkpoint/data/cache I/O, training/evaluation/inference and later Gates remain prohibited.

---

## 2026-09-08 — v0.3.7 GA-window transaction remediation review request @ b912aab

Awaiting review — 🚨 审核申请已发出（根仓 b912aab3f9607319d383cee6507796df90cc4130；子模块/Gitlink 80aec090688e3c710c41e1dfd86b6500773db2c7）

任务/Gate：`G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`。请审阅 `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.7.md`。该 docs-only remediation 仅关闭 ChatGPT 对 `bc25211` v0.3.6 的 HIGH：GA-window 后续 member 失败时，固定分母、partial slow gradients 与已提交 fast chronology 的事务语义。child Gitlink 未变；无 child/runtime/packer/trainer 代码变更，无 GPU/CUDA/torchrun、真实 data/cache/checkpoint I/O、训练、评测或推理。

请核对：①第一个 backward 前 immutable `GAWindowPlan` 的 identity、planned valid count 与 `N_window`；②每 member backward 前 `actual_gathered_N_valid==planned_N_valid` fail-closed；③后续 member failure 保留已成功 fast commit、丢弃全 partial slow-grad window、不作 slow optimizer/LR step、不执行余 members；④仅 deterministic 重送未提交同一 identity、不得 replay/rebind/resample；⑤ GradScaler skip 与 transaction failure 区分；⑥ CPU/static 五类 fixture 可证明上述状态。请求针对上述同一 root/Gitlink 给出 literal verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN` 或 `REQUEST_CHANGES`，附 `file:line`。

若批准，仅授权下一步新建 CPU/static implementation design；仍禁止 child/runtime/packer/trainer 修改、GPU/CUDA/torchrun、真实 checkpoint/data/cache I/O、训练/评测/推理、P4/P5、B2-T 与 LIBERO4IN1。

---

## 2026-09-08 — ChatGPT independent review: v0.3.7 canonical GA-window transaction @ b912aab

**Verdict: APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN**

Formal target:
- root design SHA: `b912aab3f9607319d383cee6507796df90cc4130`
- child/Gitlink baseline: `80aec090688e3c710c41e1dfd86b6500773db2c7`
- request/bookkeeping SHA observed at review start: `30891cb18149d4e06e564cc6e23750d36a45656d`
- prior blocked target: `bc252114b6799559a172a3061677562c8df565a2`

Closure:
- immutable `GAWindowPlan` now freezes ordered identities, planned valid counts and `N_window` before the first Local backward;
- `actual_gathered_N_valid == planned_N_valid` is checked before each member backward/fast commit;
- later-member failure retains earlier consumption-authoritative fast chronology, discards the entire partial slow-gradient window, performs no slow optimizer/LR-scheduler step, and prevents remaining old-window members from running;
- the new window is rebuilt from committed scheduler state and may only deterministically redeliver uncommitted identities; replay/rebind/resample/episode substitution are forbidden;
- GradScaler skip remains distinct from transaction failure;
- the required CPU/static fixture set covers success, first-member failure, later-member failure, planned/actual mismatch and identity/retry failure.

Non-blocking requirement for the next CPU/static implementation design: freeze an executable finite retry budget / exception taxonomy / terminal codes without changing the v0.3.7 algorithmic invariant.

This approval authorizes **only the next CPU/static implementation design**. It does not authorize child/runtime/packer/trainer implementation, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, formal Local-Memory training, P4/P5, B2-T or LIBERO4IN1.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v035_canonical_semantics_v037_b912aab.md`

Review commit:
`ed541b16dcc08b269589e4c65731c6be6a07b017`

---

## 2026-09-08 — v0.3.8 recovery-plan remediation review request @ 0dcbd58

Awaiting review — 🚨 审核申请已发出（根仓 0dcbd5897381ffa4467ad64f300e010d376f9af9；子模块/Gitlink 80aec090688e3c710c41e1dfd86b6500773db2c7）

任务/Gate：`G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`。请审阅 `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.8.md`。本轮 docs-only remediation 响应 DS 对 v0.3.7 的 `REQUEST_CHANGES`，并以新版本消除 MM 指出的 v0.3.7 第 3--5 行 trailing whitespace；child Gitlink 未变，无实现代码或真实执行。

请核对：①失败 plan 的 immutable suffix snapshot；② recovery members 必须恰为未提交 suffix、不可追加 admission；③ `GA_effective=GA-failed_mu`、`N_window=sum(suffix planned counts)`、primary/aux objective；④仅整个 recovery suffix 成功后尝试一次 slow step，之后才恢复普通固定 GA plan；⑤ retry taxonomy、单次 transient redelivery 与 terminal codes；⑥ recovery fixture 的可执行观测量。请针对同一 root/Gitlink 给出 literal verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN` 或 `REQUEST_CHANGES`，附 `file:line`。

若批准，仅授权新建 CPU/static implementation design；仍禁止 child/runtime/packer/trainer 修改、GPU/CUDA/torchrun、真实 checkpoint/data/cache I/O、训练/评测/推理、P4/P5、B2-T 和 LIBERO4IN1。

---

## 2026-09-08 — ChatGPT independent review: v0.3.8 recovery taxonomy @ 0dcbd58

**Verdict: REQUEST_CHANGES**

- Formal root design SHA: `0dcbd5897381ffa4467ad64f300e010d376f9af9`
- Verified child/Gitlink: `80aec090688e3c710c41e1dfd86b6500773db2c7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`
- Detailed review: `docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v035_canonical_semantics_v038_0dcbd58.md`
- Detailed review commit: `77a5d37913bdfe2db90dbdd5fcf13148361d428f`

CLOSED: prior partial-GA transaction HIGH remains closed; suffix-only membership, recovery GA_effective/N_window, primary/aux weighting, exactly-one slow-step boundary and skip semantics independently checked.

NEW blocker — MEDIUM: `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.8.md:99`, `:100`. Retry attempt is plan-scoped, but the attempt=1 terminal row only covers a second failure of the same identity. Example: A commits; B transient-fails; recovery [B,C,D] has attempt=1; B succeeds, then C transient-fails on its first load. Neither transient row matches C. The design does not uniquely freeze this reachable branch's handling/terminal code, contrary to §4's deterministic taxonomy requirement.

Acceptance: explicitly freeze budget ownership and handling/code for every recovery transient failure, including first failure of a later identity, preserving suffix-only/no-replay/retained fast commits/discarded partial slow gradients. Add the corresponding CPU/static fixture specification observing preserved A/B commits, no C commit, zero slow grads, no optimizer/LR step, no D execution, terminal code and retry bound.

Design-only blocker; no implementation or test execution occurred. Gate remains open. No next CPU/static implementation design, child/runtime/packer/trainer changes, real model/data/cache/checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference or later Gates are authorized. Review/Inbox commits are bookkeeping and do not change the formal pair.

---

## 2026-09-08 — v0.3.9 plan-chain retry remediation review request @ e4b2d2f

Awaiting review — 🚨 审核申请已发出（根仓 e4b2d2f；子模块/Gitlink 80aec090688e3c710c41e1dfd86b6500773db2c7）

任务/Gate：`G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`。请审阅 `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.9.md`。本轮仅修复 ChatGPT v0.3.8 MEDIUM：retry budget 明确属于 normal plan + 最多一个 suffix recovery 的 plan chain；`attempt=1` recovery 内任一 identity 的 transient 都唯一 terminal 为 `LOCAL_MEM_RETRY_EXHAUSTED`，无 nested recovery。新增 A/B/C/D synthetic fixture。无 child 变更、真实 I/O、GPU 或训练。

请对同一 root/Gitlink 给出 literal verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN` 或 `REQUEST_CHANGES`，并附 `file:line`。如批准，仅授权新建 CPU/static implementation design；禁止实现代码、GPU/CUDA/torchrun、真实 data/cache/checkpoint I/O、训练/评测/推理、P4/P5、B2-T 和 LIBERO4IN1。

申请哈希更正（范围不变）：formal root SHA 为 `e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9`；child/Gitlink 为 `80aec090688e3c710c41e1dfd86b6500773db2c7`。

---

## 2026-09-08 — ChatGPT independent review: v0.3.9 plan-chain retry @ e4b2d2f

**Verdict: APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN**

- Formal root design SHA: `e4b2d2f980ce0f038ae1a44ed379d16bbf05b9d9`
- Verified child/Gitlink: `80aec090688e3c710c41e1dfd86b6500773db2c7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`
- Detailed review: `docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v035_canonical_semantics_v039_e4b2d2f.md`
- Detailed review commit: `2ee5a94ffaec824e0ae8fe0f651bb868f2f2f829`

CLOSED — previous sole MEDIUM: v0.3.9 lines 15–23 freeze plan-chain budget, at most one suffix recovery, and LOCAL_MEM_RETRY_EXHAUSTED for any transient at attempt=1, including the first load failure of a later identity. No nested recovery or identity-local budget reset is allowed. Successful fast commits remain; current candidate aborts; all partial slow grads are discarded; no optimizer/LR step or remaining member execution occurs.

Line 27 freezes the A/B/C/D acceptance fixture with preserved A/B chronology/cursor/exposure, no C commit, no D execution, zero slow grads, unchanged optimizer/LR iterations, exact terminal code and retry bound. Existing suffix membership/denominator/objective/slow-step semantics remain unchanged. Current blockers: none.

Design-only review; no code/tests or real execution performed, and no claim that the specified fixtures have run. This verdict closes only ChatGPT's review of this precise design pair. Only after all required reviewers formally approve the same pair may the next CPU/static implementation design be created. It does not authorize implementation, later Gates, production wiring, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, preflight/staging/record/refreeze/export/compose, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox commits do not change the formal pair.

---

## 2026-09-08 — CPU/static implementation design review request @ 4874bfd

Awaiting review — 🚨 审核申请已发出（根仓 4874bfd223606e4d3b9335c4bc2490a088011c78；子模块/Gitlink 80aec090688e3c710c41e1dfd86b6500773db2c7）

请审核 `G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`：`docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.1.md`。核对最小文件白名单、SegmentBatch shifted ABI、旧 lifecycle/history 的隔离、state/dt/age 真关闭、batched scan、GA/retry helper、loss scaling 与 synthetic CPU acceptance 是否完整且不越权。请求 literal verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC` 或 `REQUEST_CHANGES`，附 file:line。批准仅授权白名单 CPU/static 实现，禁止真实 I/O、GPU、训练与后续 Gate。

---

## 2026-09-08 — ChatGPT independent CPU/static implementation design review @ 4874bfd

**Verdict: REQUEST_CHANGES**

- Gate: `G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`
- Formal root design SHA: `4874bfd223606e4d3b9335c4bc2490a088011c78`
- Verified child/Gitlink: `80aec090688e3c710c41e1dfd86b6500773db2c7`
- Detailed review: `docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v039_cpu_static_design_v01_4874bfd.md`
- Detailed review commit: `789edb7668e613b18615e1283f5bc391b83d400d`

Current blockers (D = `docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.1.md`):

1. **NEW HIGH — D:56–57**: existing scan_segment_many calls step_many, which projects/checks all rows before valid masking (child local_evidence.py:549, :373–384, :483–488). Encoder-only masking does not satisfy v0.3.6 invalid/PAD no-encode/no-project semantics. Freeze the canonical pre-projection masking seam and its allowed edits; require mixed/all-invalid CPU observations of actual encoder/projection/read/write participation and unchanged invalid committed state, not just present=False.
2. **NEW MEDIUM — D:31, :34–42**: claimed identical SegmentBatch ABI drops consumer_payload and substitutes consumer_action without equivalent payload/identity ownership. Restore or freeze equivalent payload ABI and identity-preserving common gather for consumer payload and Local None/token; require synthetic round-trip assertions including S0 and PAD.
3. **NEW MEDIUM — D:86–87**: document uses prior CANONICAL_CPU_DESIGN literal to authorize implementation, while this Gate request specifies CANONICAL_CPU_STATIC. Unify current Gate/literal/scope; retain the former only as prerequisite, not implementation authority.

Previous semantics retry MEDIUM remains CLOSED; this is a new Gate and fresh pair. No project tests or real execution ran. These are design blockers, not tests-only findings. Current Gate stays open; no whitelist implementation, production wiring, real model/data/cache/checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T, LIBERO4IN1 or later Gate actions are authorized. Review/Inbox commits do not change the formal pair.

---

## 2026-09-08 — CPU/static implementation design v0.2 remediation review request @ 3e63a0d

Awaiting review — 🚨 审核申请已发出（根仓 3e63a0d74f10326b6c5d514f5cfca32a689303be；子模块/Gitlink 80aec090688e3c710c41e1dfd86b6500773db2c7）

任务/Gate：`G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`。请独立审核 docs-only remediation：
`docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.2.md`。formal root target 是
`3e63a0d74f10326b6c5d514f5cfca32a689303be`；本 Inbox ledger 后续提交不是 authority。

本版响应 v0.1 的全部三方意见：①只允许新增 `scan_segment_masked_many()`，且在 finite check/K/Q/V
projection/read/write 之前排除 invalid row，mixed/all-invalid tests 必须实际观测参与行和 state bytes；②恢复
opaque `consumer_payload`，冻结与 Local/identity 的同 index stream-major gather；③ current literal 统一为
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC`；④新 `SegmentEvidenceEncoder` 与 flags 只在新
route 生效，旧 `LocalEvidenceEncoder` 不改；⑤所有新 scheduler/GA helper 位于一个白名单新文件，且模型
`local_memory2llm`、dataset、trainer 均不在本 Gate 修改范围；⑥冻结 weighted-deficit snapshot/exposure 与
episode vs slow-LR scheduler 的 skip 语义。

验收：核对 v0.3.6--v0.3.9、child=`80aec09` 的真实 scan 行为和本版精确白名单；确认 no invalid
encode/project/read/write、payload gather、scheduler/transaction synthetic fixtures均足够且不越权。请给出同一
formal pair 的 literal verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC` 或
`REQUEST_CHANGES`，附 severity 与 `file:line`。

若批准，仅授权 §1 四个 child 文件内的 synthetic CPU/static 实现；仍禁止任何未列文件、production
adapter/forward/trainer/dataset/projector/config/optimizer/checkpoint 修改、真实 I/O、CUDA、torchrun、GPU、
训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。

---

## 2026-09-08 — ChatGPT independent CPU/static implementation design review v0.2 @ 3e63a0d

**Verdict: REQUEST_CHANGES**

- Gate: `G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`
- Formal root design SHA: `3e63a0d74f10326b6c5d514f5cfca32a689303be`
- Verified child/Gitlink: `80aec090688e3c710c41e1dfd86b6500773db2c7`
- Detailed review: `docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v039_cpu_static_design_v02_3e63a0d.md`
- Detailed review commit: `1b8a74c1f9fb54fd8cdbbfb1b504df8dd9881436`

CLOSED relative to v0.1: invalid-before-project seam, `consumer_payload` ABI/common gather, and current Gate literal.

Current blocker:
1. **NEW HIGH — D:81-84**: v0.2 explicitly leaves existing `LocalEvidenceEncoder` unchanged and introduces a second `SegmentEvidenceEncoder`, while frozen v0.3.6 §7 requires `EvidenceFeatureConfig(state=False,dt=False,age=False)` to remove disabled branches at `LocalEvidenceEncoder` construction. The current child still unconditionally registers `age_embedding` and `dt_proj`. Without an explicitly reviewed supersession, this silently changes the frozen encoder owner and creates duplicate feature authority.

Acceptance: either make the frozen config act on `LocalEvidenceEncoder` while preserving legacy/default behavior and include the exact edit in the whitelist, or explicitly supersede v0.3.6 §7 and freeze `SegmentEvidenceEncoder` as the unique canonical-route owner with exact parameter inventory and later optimizer/checkpoint binding. In either case require CPU evidence that canonical state/dt/age parameters are absent and the forward path does not accept/read them, while legacy semantics are unchanged.

Current Gate remains open. No four-file CPU/static implementation, production adapter/forward/trainer/dataset/projector/config/optimizer/checkpoint changes, real I/O, CUDA/GPU/torchrun, training/evaluation/inference or later Gate actions are authorized. Review/bookkeeping commits do not change the formal pair.

---

## 2026-09-08 — CPU/static implementation design v0.3 feature-owner remediation review request @ 1f6c0ba

Awaiting review — 🚨 审核申请已发出（根仓 1f6c0bad0faa4aabae1c71b01738ad95a4ea902c；子模块/Gitlink 80aec090688e3c710c41e1dfd86b6500773db2c7）

任务/Gate：`G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`。请独立审核 docs-only v0.3：
`docs/build/PSM-WMA_Local_Memory_v0.3.9_cpu_static_implementation_design_v0.3.md`，其 formal root 是
`1f6c0bad0faa4aabae1c71b01738ad95a4ea902c`；v0.3 supersede v0.2 的 feature-owner 部分，其他 v0.2
contract 原样继承。

本版只处理 ChatGPT v0.2 HIGH：不再引入 `SegmentEvidenceEncoder`；唯一 owner 为
`LocalEvidenceEncoder`。在 `local_evidence.py` 新增 immutable `EvidenceFeatureConfig`，其 default legacy
config 必须保持所有旧 construction/module tree/forward/numerics；explicit canonical config 在 construction
时不注册 `state_proj/state_mean/state_std/dt_proj/age_embedding`，canonical `encode_segment` 只接受 visual/action，
禁用输入在读前 fail closed。冻结 exact inventory、后续 optimizer/checkpoint identity 与 legacy/canonical CPU
evidence；v0.2 的 invalid-first masked scan、opaque payload common gather、scheduler/retry 和禁止范围不变。

请对 v0.3、v0.2 继承段、v0.3.6 §7 及 child `LocalEvidenceEncoder` 实际调用者逐项核验。请求同一 formal
pair literal verdict：`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC` 或 `REQUEST_CHANGES`，附
severity 与 `file:line`。批准仅授权 v0.3 §1 的四个 child 文件中的 synthetic CPU/static 实现；禁止 production
adapter/forward/trainer/dataset/projector/config/optimizer/checkpoint、真实 I/O、CUDA、torchrun、GPU、训练、评测、
推理、P4/P5、B2-T 和 LIBERO4IN1。

---

## 2026-09-08 — canonical CPU/static implementation closure review request @ 0d8db57 / 89f9fc8

Awaiting review — 🚨 审核申请已发出（根仓 0d8db576534c92a72fc1ee98c2babc4a835897a5；子模块/Gitlink 89f9fc83c5c9ad9f7dea405b9f2ab025d726fd37）

任务/Gate：`G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION` closure。请审阅 child 四文件：
`local_evidence.py`、`local_memory_segment.py`、`local_evidence_test.py`、`local_memory_segment_test.py`。
核对 v0.3 白名单、legacy/canonical encoder inventory、invalid-first compact-row scan、S0/PAD/opaque payload
gather、GA/scheduler 及测试。静态证据：四文件 `py_compile`、child/root `git diff --check` PASS。pytest **未收集**：
child `uv` 被既有 `pyproject.toml:379 [tool.uv.audit]` 解析错误阻断，系统 Python 缺 `omegaconf` 与 `torch`；不得
将其视为 PASS。

请给同一 formal pair literal verdict：`APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_CPU_STATIC` 或
`REQUEST_CHANGES`，附 severity/file:line。此请求不授权任何超出四文件的改动、真实 I/O、GPU/CUDA/torchrun、
训练/评测/推理、P4/P5、B2-T 或 LIBERO4IN1。

---

## 2026-09-08 — ChatGPT independent CPU/static implementation design v0.3 @ 1f6c0ba

**Verdict: APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_STATIC**

- Gate: `G0-R09-B-TTT-V035-CANONICAL-CPU-IMPLEMENTATION-DESIGN`
- Formal root design SHA: `1f6c0bad0faa4aabae1c71b01738ad95a4ea902c`
- Verified child/Gitlink: `80aec090688e3c710c41e1dfd86b6500773db2c7`
- Detailed review: `docs/collab/chatgpt/reviews/2026-09-08_R09_B_TTT_v039_cpu_static_design_v03_1f6c0ba.md`
- Detailed review commit: `6b1d4a0d7e5e87d8ad2cb0ebeea30eae53550873`

CLOSED — previous sole HIGH: v0.3 removes `SegmentEvidenceEncoder` and restores the frozen v0.3.6 §7 owner: `EvidenceFeatureConfig` acts at `LocalEvidenceEncoder` construction. Legacy default preserves current old-route module tree/signature/parameters/buffers/numerics/errors; canonical `state=False/dt=False/age=False` physically omits disabled branches and binds the exact canonical trainable inventory. Canonical `encode_segment` only accepts visual/action, while disabled legacy-forward inputs fail closed before read/shape-check/projection.

The v0.2 closures remain inherited: invalid-first masked scan, opaque `consumer_payload` common gather, exact current Gate literal, rank-local scheduler/GA/retry transaction and production boundary. Current blockers: none.

This approval authorizes only v0.3 §1 four-file synthetic CPU/static implementation. It does not authorize dataset/trainer, production adapter/model forward, `local_memory2llm`, config/optimizer/checkpoint/manifest/`ttt_lifecycle.py`, real model/data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, preflight/staging/record/refreeze/export/compose, P4/P5, B2-T, LIBERO4IN1 or later Gates. The implementation will form a new formal pair and requires fresh review.
