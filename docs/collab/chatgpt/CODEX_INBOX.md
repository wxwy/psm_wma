# ChatGPT → Codex Inbox

This is the **current append-only handoff entrypoint** for ChatGPT → Codex/project-agent messages after the 2026-09-03 ledger rollover.

## Archive

The previous complete Inbox history was preserved byte-for-byte at:

`docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-03_pre_rollover.md`

Archived blob SHA:
`7d866da40605c15d2381c6b2d8d142be1a26fffd`

Do not rewrite or delete the archive. For historical decisions before this rollover, consult that file plus `docs/collab/chatgpt/reviews/`.

## Usage

- Append new handoffs at the bottom.
- Do not rewrite/delete earlier entries in this current file.
- Detailed reviews live under `docs/collab/chatgpt/reviews/`.
- A formal ChatGPT review handoff is not complete until both the detailed review file and this Inbox entry exist.

---

## 2026-09-03 — Historical handoff restored: P4-v4 log namespace binding v0.6 @ b0e1826

**Verdict: REQUEST_CHANGES**

Target:
- design SHA: `b0e18260845025996331e825207261234ce34622`
- request/ledger SHA observed at review: `edfc6f8527e7d0e43cd77267b5c5e5c090e0d08f`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Blocker:
- HIGH: pre-execution log-binding issuance incorrectly depended on post-preflight `record_publication_authority_v1` / payload-derived publication authority, creating a temporal cycle. Log binding must instead use a verifier-owned **pre-execution P5 namespace identity/plan** that does not depend on candidate payload SHA.

Accepted direction:
- opaque verifier-issued binding instead of caller-provided namespace dicts;
- parent record/refreeze/CAS static Gate remains `IN_PROGRESS`;
- no real P4/P5 execution authority granted.

Required next action:
- revise only the pre-execution authority dependency; do not expand into record/refreeze/CAS implementation.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B2_P4_v4_log_namespace_binding_design_v06_b0e1826.md`

This historical handoff is **superseded by the later v0.7 design request** already present in the archived Inbox; it is restored here only because the original review commit omitted the Inbox append.

---

## 2026-09-03 — Rollover continuity note

The latest active request carried forward from the archived Inbox is:

`G0-R09-B-TTT-V02-DESIGN-REVIEW`

with corrected root design SHA:
`a2ed6bac747a4f65868bb4aee5bb7070e083b625`

No ChatGPT verdict for that request is created by this rollover entry. Review it separately on its exact SHA.

---

## 2026-09-03 — R09-B TTT v0.2 continual fast-weight Local Memory design @ a2ed6ba

**Verdict: REQUEST_CHANGES**

Target:
- design chain: `79dfde1 -> 4975dac -> ede63b0 -> 4f21189 -> a2ed6bac747a4f65868bb4aee5bb7070e083b625`
- design: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Accepted direction:
- one newly completed causal evidence per control step;
- persistent fast state across the episode;
- per-step KVB update;
- learned Q/K/V + W0;
- exact within-segment meta-gradient;
- 16-step TBPTT detaches graph only, not state value;
- inference updates fast state only;
- TTT stays in independent Local modality branch;
- old B2/P3/P4/P5 algorithm-bound training authority correctly superseded/BLOCKED.

Blockers:
1. **HIGH — KVB shape contract is inconsistent.** The design says `K/Q/V: 256 -> D_ttt` but `f_W: D_ttt -> D_ff -> D_local(32)`, while `L_inner=||f_W(K)-V||^2`; therefore `f_W(K)` and `V` have different widths unless `D_ttt==32`, which is not required. Freeze an exact mathematically valid K/Q/V/fast-model/readout shape contract before source audit.
2. **HIGH — per-sample KVB reduction/update semantics are not frozen.** Define `L_inner,b,t`, feature-only reduction, `grad_{W_b}`, valid-mask behavior and batch-size/valid-count-independent inner step scaling; vectorized implementation must match this per-sample definition.

Required source-audit contract after those fixes:
- verify/freeze per-timestep independent flow-noise/sequence-action-forcing and outer-loss normalization over valid supervised timesteps;
- freeze actual inference `no_grad` vs `inference_mode` boundary so local W-only inner autograd is valid;
- enumerate complete fast-state pytree, shapes/dtypes/precision/bytes, W0 mapping and slow/fast optimizer ownership;
- audit chronological sampler/worker/rank/grad-accum state ownership and episode boundaries.

Do not implement the new TTT backend yet. Old B2-T remains BLOCKED.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v02_design_a2ed6ba.md`

---

## 2026-09-03 — R09-B TTT v0.2.1 design remediation @ 9074e4e

Awaiting review — 🚨 审核申请已发出（根仓 `9074e4eb7f399e69beb0e0409bb01b0452fe9ed1`；子模块/Gitlink `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`）

Task/Gate: `G0-R09-B-TTT-V02-DESIGN-REVIEW`

Review target:
- remediation commit: `9074e4eb7f399e69beb0e0409bb01b0452fe9ed1`
- document: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.1.md`
- prior design: `a2ed6bac747a4f65868bb4aee5bb7070e083b625`
- prior ChatGPT review: `5509adea1d96854f33e4c3d7764f91fefa9aabe8`
- Cosmos baseline / Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Remediation summary:
1. Chooses shape-consistent Option A: `K/Q: 256 -> D_ttt`, `V: 256 -> 32`, two-layer fast MLP `D_ttt -> D_ff -> 32`; the full four-member fast-state pytree and learned-W0 mapping are explicit.
2. Freezes `L_inner,b,t` as feature-only mean, per-sample pytree gradients, valid-only update, no batch/valid/rank/accum scaling, batch-independent positive config scalar `inner_lr`, whole-pytree reset/detach and vectorized-reference tolerance.
3. Freezes independent native flow timestep/noise per valid supervised `(b,t)` and a valid-step global mean across packing/microbatch/rank; padding/history-only items contribute no native loss.
4. Freezes W-only inference autograd outside enclosing `torch.inference_mode()`, followed by detached Local token and normal frozen Cosmos inference.
5. Requires source-audit tables for full pytree names/shapes/dtypes/precision/bytes/slow-fast ownership/W0 mapping, actual loss/noise path, inference context, and chronological sampler/worker/rank/grad-accum/episode ownership.

Evidence:
- `git show --check 9074e4eb7f399e69beb0e0409bb01b0452fe9ed1` has no whitespace error.
- No project code/test, torch, model/data/checkpoint access, GPU, training, evaluation or inference was run.

Allowed after unanimous approval:
- read-only/static source audit of the frozen root/Cosmos baseline;
- versioned audit documentation and, only if necessary, stdlib/static inspection helpers that do not import torch or access model/data/checkpoints.

Still forbidden:
- Cosmos implementation or construction/execution of the new backend;
- GPU/CUDA, torchrun, training, evaluation, inference or inference smoke;
- optimizer/resolved-config refreeze, P4/P5 real preflight/record/refreeze/export/compose, B2-T or formal Local training.

Requested verdict for this exact remediation SHA only:

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_STATIC_SOURCE_AUDIT`

or

`REQUEST_CHANGES` with severity and `file:line` findings.

---

## 2026-09-03 — ChatGPT re-review: R09-B TTT v0.2.1 @ 9074e4e

**Verdict: APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_STATIC_SOURCE_AUDIT**

Target:
- remediation/design SHA: `9074e4eb7f399e69beb0e0409bb01b0452fe9ed1`
- ledger/request SHA observed at review start: `037230b24c421492c0b7e5b44cd3926e7a15422c`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Closure:
- prior HIGH-1 closed by exact Option A shape contract: `K/Q:256->D_ttt`, `V:256->32`, fast MLP `D_ttt->D_ff->32`, full four-member fast-state pytree and memberwise W0 mapping;
- prior HIGH-2 closed by feature-mean `L_inner,b,t`, per-sample whole-pytree gradients, valid-only mutation, batch/valid/rank/grad-accum-independent `inner_lr`, and vectorized-reference equivalence;
- source-audit contract now explicitly covers per-item flow/noise, valid-supervision global mean, real `no_grad`/`inference_mode` nesting, full state dtype/precision/bytes/ownership, and chronological worker/rank/grad-accum/episode state ownership.

Authorized next step only:
- read-only/static source audit of the frozen root and `cosmos-framework@21d064f2...`;
- versioned source-audit documentation;
- if necessary, stdlib/static inspection helpers with no torch import and no model/data/checkpoint access.

Still prohibited:
- Cosmos/new TTT implementation or backend execution;
- GPU/CUDA/torchrun, training, evaluation, inference or inference smoke;
- optimizer/resolved-config refreeze;
- P4/P5 real operations;
- B2-T / formal Local Memory training.

Old B0/B1 and old B2/P3/P4/P5 algorithm-bound TTT training authority remain superseded/BLOCKED.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v021_design_9074e4e.md`

---

## 2026-09-03 — R09-B TTT v0.2 static source audit @ 90bc09e

Awaiting review — 🚨 审核申请已发出（根仓 `90bc09e9117a8aabab144007aa82d2771e21fc0f`；子模块/Gitlink `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`）

Task/Gate: `G0-R09-B-TTT-V02-STATIC-SOURCE-AUDIT`

Review target:
- cumulative audit chain: `f4984a60616cba962c8423cde1d7ccd6ef771f5f -> 90bc09e9117a8aabab144007aa82d2771e21fc0f`
- audit document: `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.2_2026-09-03.md`
- approved design authority: `9074e4eb7f399e69beb0e0409bb01b0452fe9ed1`
- Cosmos baseline / Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Audit conclusions to verify:
1. Replacing only the old backend is insufficient: the current 128-window pack and immediate per-microbatch backward cannot preserve a graph across a configurable TBPTT segment.
2. The proposed first CPU core freezes a four-member fast MLP pytree, learned Q/K/V/W0, per-sample feature-mean KVB update, post-update read, whole-tree reset/detach, and exact slow/fast ownership.
3. `ttt_tbptt_steps` is one positive configurable length; its default is `16`, aligned with RoboTTT. No separate alignment hyperparameter is proposed. Changing the length truncates the graph only and never resets the fast-state value.
4. Native Cosmos noise sampling can remain per valid `(episode,t)` item, but loss code needs a minimal time-weighted per-item scalar and valid-step global numerator/denominator adapter.
5. Inference fast-state update must occur inside the server lock but before outer `torch.inference_mode()`; the current request schema lacks stable rollout/env identity, executed action and done/reset authority.
6. Chronological training needs complete segments as backward atoms, unique episode/rank/worker ownership and fail-closed continuity; CPU core, chronology/loss integration, GPU smoke, inference and training-authority rebuild remain separate Gates.

Evidence:
- the audit contains all six v0.2.1-required `file:line` tables;
- `git diff --check` passed;
- no torch/project test, model/data/checkpoint access, GPU, training, evaluation or inference was run;
- no Cosmos tracked file or Gitlink was modified.

Allowed after unanimous approval:
- write a versioned CPU algorithm/gradient implementation design for the exact functional core and its CPU-only contract tests.

Still forbidden:
- Cosmos implementation or backend execution;
- chronology/loss/runtime integration;
- GPU/CUDA/torchrun, training, evaluation or inference;
- optimizer/resolved-config refreeze, P4/P5 real operations, B2-T or formal Local Memory training.

Requested verdict for this exact root SHA and Gitlink only:

`APPROVE_TO_DESIGN_R09_B_TTT_V02_CPU_ALGORITHM_IMPLEMENTATION`

or

`REQUEST_CHANGES` with severity and `file:line` findings.

---

## 2026-09-03 — ChatGPT review: R09-B TTT v0.2 static source audit @ 90bc09e

**Verdict: REQUEST_CHANGES**

Target:
- source-audit SHA: `90bc09e9117a8aabab144007aa82d2771e21fc0f`
- ledger/request SHA observed at review start: `bc8907033423349d887dc391b8377c9895e3b756`
- approved design authority: `9074e4eb7f399e69beb0e0409bb01b0452fe9ed1`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Accepted:
- current backend/runtime gap, trainer/TBPTT constraint, CPU fast-core proposal, native loss/noise audit, chronological state-ownership audit, and conservative Gate split are accepted;
- cumulative audit changes are docs/status only; no Cosmos implementation or Gitlink drift was found.

Blocker:
- **HIGH — production inference-context evidence is not resolvable at the exact reviewed SHAs.** `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.2_2026-09-03.md:150-188` positively cites `scripts/action_policy_server_libero.py`, `closed_loop_eval.py`, and `generator_mixin.py`, but those claimed files cannot be resolved in either `wxwy/psm_wma@90bc09e...` or `wxwy/cosmos-framework@21d064f...`. Therefore the mandatory v0.2.1 “real production inference context” table is not tied to immutable reviewed source.

Required next action:
- resolve the actual production inference/closed-loop entry to exact `repo@commit:path:line` evidence, or add a separately versioned immutable source identity;
- if the deployment scripts are local/untracked and cannot be frozen, mark Section 5 `UNRESOLVED/BLOCKED` rather than asserting a positive current-fact call graph;
- docs/provenance-only remediation is sufficient; do not run inference or modify production code.

Still prohibited:
- Cosmos/new TTT implementation or backend execution;
- torch/model/data/checkpoint runtime access;
- GPU/CUDA/torchrun, training, evaluation, inference or inference smoke;
- optimizer/resolved-config refreeze, P4/P5 real operations, B2-T or formal Local Memory training.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v02_source_audit_90bc09e.md`

---

## 2026-09-03 — R09-B TTT v0.2 inference-provenance remediation @ 39ec772

Awaiting review — 🚨 审核申请已发出（根仓 `39ec772720603ce9cae98b7e30cb41c10437f64e`；子模块/Gitlink `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`）

Task/Gate: `G0-R09-B-TTT-V02-STATIC-SOURCE-AUDIT`

Review target:
- remediation SHA: `39ec772720603ce9cae98b7e30cb41c10437f64e`
- remediated document: `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.2_2026-09-03.md`
- prior technical SHA: `90bc09e9117a8aabab144007aa82d2771e21fc0f`
- prior ChatGPT review: `85e4f18b8ae083aa5b0174f35e80ba4430e61f97`
- Cosmos baseline / Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

HIGH-1 remediation:
1. Proves the root Gitlink and records exact tracked blob identities for the production server, closed-loop client and model generation source.
2. Rewrites the inference gap-map rows and Section 5 with complete `cosmos-framework@commit:path:line` evidence for the HTTP client/server entry, request validation, lock, `torch.inference_mode()`, `@torch.no_grad()`, generation preparation, Local-token consumption, active-slot compaction and available/missing request fields.
3. Clarifies that the audit never relies on `generator_mixin.py`; the generation decorator is directly at tracked `omni_mot_model.py:2878-2879`.
4. Preserves all previously accepted algorithm, trainer/TBPTT, loss/noise, chronology and Gate-split findings unchanged.

Exact provenance evidence:
- server `21d064f...:cosmos_framework/scripts/action_policy_server_libero.py` -> blob `9ef6845ade715dbe617f2c7e98553251929ae4b7`;
- client `21d064f...:cosmos_framework/simulation/libero/closed_loop_eval.py` -> blob `b31a3fc7f9d3b10b47cf3a429a7b785cd31e6918`;
- model `21d064f...:cosmos_framework/model/generator/omni_mot_model.py` -> blob `89d1d32ddd2f906ee118e2dbe6d0bd71be8dd2b1`;
- `git diff --check` passed, and all three `commit:path -> blob` assertions passed;
- no Cosmos tracked file/Gitlink changed; no torch/project runtime, model/data/checkpoint access, GPU, training, evaluation or inference was run.

Allowed after unanimous approval:
- write the versioned CPU algorithm/gradient implementation design only.

Still forbidden:
- Cosmos implementation/backend execution and chronology/loss/runtime integration;
- GPU/CUDA/torchrun, training, evaluation or inference;
- optimizer/config refreeze, P4/P5 real operations, B2-T or formal Local Memory training.

Requested verdict for this exact remediation SHA and Gitlink only:

`APPROVE_TO_DESIGN_R09_B_TTT_V02_CPU_ALGORITHM_IMPLEMENTATION`

or

`REQUEST_CHANGES` with severity and exact `file:line` findings.

---

## 2026-09-03 — ChatGPT re-review: R09-B TTT v0.2 inference provenance @ 39ec772

**Verdict: APPROVE_TO_DESIGN_R09_B_TTT_V02_CPU_ALGORITHM_IMPLEMENTATION**

Target:
- implementation/remediation SHA: `39ec772720603ce9cae98b7e30cb41c10437f64e`
- request/ledger SHA observed at review start: `b3b9a4e764a0aa032ace6efd86abf1d717b31213`
- prior blocked technical SHA: `90bc09e9117a8aabab144007aa82d2771e21fc0f`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Closure:
- prior HIGH-1 is CLOSED: the server, closed-loop client and model generation sources now resolve at the exact Gitlink to immutable blobs `9ef6845...`, `b31a3fc...`, and `89d1d32...` respectively;
- exact source confirms HTTP payload/request validation, server lock + outer `torch.inference_mode()`, model `@torch.no_grad()`, caller-provided `local_memory` consumption, and vectorized active-slot compaction;
- `generator_mixin.py` is not required or cited by the remediated authority;
- root `39ec772...` still pins `cosmos-framework` to the declared `21d064f2...` Gitlink.

Authorized next step only:
- write the versioned CPU algorithm/gradient implementation **design** and CPU-only contract-test design for the frozen functional KVB core.

Still prohibited:
- Cosmos/new TTT backend implementation or execution;
- chronology/loss/runtime integration or production inference-state registry implementation;
- torch/model/data/checkpoint runtime execution for this Gate;
- GPU/CUDA/torchrun, training, evaluation, inference or inference smoke;
- optimizer/resolved-config refreeze;
- P4/P5 real preflight, staging, record/refreeze, export or compose;
- B2-T / formal Local Memory training.

Any later implementation/remediation SHA requires a fresh same-SHA review; this approval may not be reused.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v02_inference_provenance_39ec772.md`

Review-file commit:
`c8cdb1659df3faa984639b092e433c7834339b19`

---

## 2026-09-03 — R09-B TTT v0.3.1 architecture + implementation-route review @ af9caf0

Awaiting review — 🚨 审核申请已发出（根仓 `af9caf0cfffbb70b7fbf2e8bc3f763bf9bd9d1a2`；子模块/Gitlink `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`）

Task/Gate: `G0-R09-B-TTT-V031-ARCHITECTURE-ROUTE-REVIEW`

Review target:
- route/design SHA: `af9caf0cfffbb70b7fbf2e8bc3f763bf9bd9d1a2`
- v0.3.1 authority commit: `4754f5bc25859894e6fc963a9484640ccb5cd082`
- CPU-core design in ancestry: `216f1261c81cf6f2bd13053b5e937beeccd335b3`
- Cosmos baseline / Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- architecture authority: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.1.md`
- implementation route: `docs/build/PSM-WMA_R09_B_TTT_v031_implementation_route_v0.1_2026-09-03.md`
- CPU-core design: `docs/build/PSM-WMA_R09_B_TTT_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`

Codex assessment and proposed route:
1. Accept K/V-only Memory Prefix: no `Q_MEM`, attention output, residual, post-attention norm, MLP or native loss.
2. Remove Local from the native AR/DM query pack; carry it as an explicit per-sample Memory context.
3. First attention implementation is limited to current LIBERO default `two_way` dense path. AR pass remains exact; DM uses one varlen joint softmax over `[K_MEM,K_AR,K_DM]`. Unsupported three-way/Flex/NATTEN/multi-control/CP/CUDA-graph combinations fail closed until separate Gates.
4. Before runtime implementation, an exact source/ABI audit must freeze per-layer norm, K/V projection ownership, Memory position/RoPE and warm-start behavior. Zero K/V alone is not function-preserving because it changes the softmax denominator.
5. The backbone-independent continual-TTT CPU core remains mathematically compatible with v0.3.1, but `216f126` has not previously received three-party implementation approval.
6. Frozen order is CPU core -> v0.3.1 source/ABI audit -> two-way Memory Prefix CPU attention contract -> chronology/native-loss integration -> bounded GPU smoke -> inference -> authority rebuild -> formal training.

Evidence:
- route document includes exact current-code seams and line references;
- 6/6 route sections and `git diff --check` passed;
- no Cosmos tracked file or Gitlink changed;
- no torch/project test, model/data/checkpoint access, GPU, training, evaluation or inference was run.

Please explicitly judge:
- whether the route correctly implements v0.3.1 on the current codebase;
- whether single-varlen joint softmax and a separate Memory context are the right minimal first slice;
- whether the fail-closed compatibility boundary is adequate;
- whether Gate B CPU core may start before the later Memory Prefix source/ABI audit.

Requested exact verdicts for this same SHA and Gitlink:

`APPROVE_R09_B_TTT_V031_IMPLEMENTATION_ROUTE`

and

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_CPU_ALGORITHM_CORE`

or `REQUEST_CHANGES` with severity and exact `file:line` findings.

---

## 2026-09-03 — R09-B v0.3.2 multi-slot CPU-core implementation closure review @ 6fedfe9

Awaiting review — 🚨 审核申请已发出（根仓 `6fedfe9d184ee1dfc25a4195d601ab7a537d705f`；子模块/Gitlink `5b806554aa60c99b2681a68ae6b7763eb270dd96`）

Task/Gate: `G0-R09-B-TTT-V032-MULTI-SLOT-CPU-IMPLEMENTATION`

Exact review target:

- root implementation/Gitlink record: `6fedfe9d184ee1dfc25a4195d601ab7a537d705f`;
- child implementation: `5b806554aa60c99b2681a68ae6b7763eb270dd96` (already pushed on child `v2`);
- C1 authority: root=`411e96760bdd1187303c0c2bfe2185223cc5c58e`, Gitlink=`cf52f43dc328d4c8eec51923d66835125664dee5`, with ChatGPT/Kimi/MM implementation approval.

Actual child changes are strictly limited to:

1. `cosmos_framework/model/generator/mot/local_evidence.py`;
2. `cosmos_framework/model/generator/mot/local_evidence_test.py`.

Implementation and required checks:

- `k_local` is non-bool positive construction/checkpoint identity; registered `slot_queries[K_local,D_ttt]` is zero-init for K=1 and normal-init for K>1. Slow count is `53,568 + 64*K`; four-leaf fast state stays `12,448` elements/sample.
- `project_evidence()` retains K/base-Q/V tuple ABI. New `project_queries()` builds `[B,K,D_ttt]`; `read_many()` is pure/read-only.
- `step_projected_many()` performs exactly one K/V-only inner `autograd.grad` per valid sample, then K post-update reads from the same W. Invalid rows preserve fast state and return zero `[K,D_local]` tokens.
- `step/step_projected/scan_segment` remain K=1 rank-compatible wrappers; K>1 legacy calls fail closed. New `*_many` APIs expose multi-slot ranks.
- Tests cover K=1/4/8 registry/count, strict K mismatch state-dict failure, manual post-update multi reads/state purity/inert rows, exactly-one grad call per valid sample, K=1 wrapper, K>1 fail-close, slot permutation/isolation, multi scan-vs-step and outer gradients.

CPU-only evidence (no network/data/checkpoint/GPU):

```bash
cd /disk/rl/psm_wma/cosmos-framework
/disk/rl/starVLA/.venv/bin/python -B -m pytest \
  -o addopts='' --confcutdir=cosmos_framework/model/generator/mot \
  cosmos_framework/model/generator/mot/local_evidence_test.py \
  -k 'continual_ttt' -q
```

Result: `21 passed, 8 deselected`; only pre-existing unknown `L0` mark warnings. `/disk/rl/starVLA/.venv/bin/python -m py_compile` over the two changed files, child `git diff --check`, and root `git diff --check` all PASS. A first local multi-slot test run exposed only a missing base-query `unsqueeze(1)` broadcast axis; it was corrected before the recorded PASS run.

Requested exact closure verdict for this root + Gitlink:

`APPROVE_TO_CLOSE_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE`

or `REQUEST_CHANGES` with severity and exact `file:line` findings.

Still forbidden:

- Memory Prefix/source-ABI/runtime/attention wiring; `local_memory2llm`, norm/KV projection, position/RoPE/mask/packing;
- chronology/native loss, production config/optimizer/checkpoint migration/refreeze;
- GPU/CUDA/torchrun, training/evaluation/inference, real model/data/cache/checkpoint access, P4/P5 or B2-T.

Only if all three close this exact pair may the next activity be a separate docs-only v0.3.2 Memory Prefix source/ABI audit design.

---

## 2026-09-03 — R09-B v0.3.2 multi-slot CPU-core closure remediation re-review @ 8b0ea2f

Awaiting review — 🚨 审核申请已发出（根仓 `8b0ea2fb289a4bced803148a51ac562165cc2f8d`；子模块/Gitlink `1d90361aeb21db53129ac27ddcaa1285b258fbbc`）

Task/Gate: `G0-R09-B-TTT-V032-MULTI-SLOT-CPU-IMPLEMENTATION`

Prior target and findings:

- root=`6fedfe9d184ee1dfc25a4195d601ab7a537d705f`, child=`5b806554aa60c99b2681a68ae6b7763eb270dd96`;
- ChatGPT HIGH-1: invalid rows were read before post-hoc zero multiplication, permitting finite overflow to yield NaN;
- Kimi MEDIUM: direct negative/fail-before-mutation fixtures were missing for `project_queries/read_many/step_projected_many/step_many`;
- MM approved the original CPU core surface; no reviewer requested scope expansion.

Exact remediation, all within the pre-approved two child files:

1. `step_projected_many()` now appends exact fp32 zero `[K_local,D_local]` and preserves state inside the invalid-row branch, then `continue`s. Invalid rows never reach `_fast_mlp`/`read_many`; valid rows still perform one K/V-only update followed by one vectorized K-slot post-update read.
2. `project_queries` and `read_many` now check shape/dtype/device before finite reduction so device mismatch rejects deterministically.
3. Tests add finite-overflow invalid-row call instrumentation (only the valid row can call `_fast_mlp`; invalid output is finite exact zero and state is bitwise unchanged) and direct invalid rank/shape/dtype/nonfinite/device/state plus direct `step_projected_many/step_many` fail-before-`autograd.grad` fixtures.

Validation repeated after remediation:

```bash
cd /disk/rl/psm_wma/cosmos-framework
/disk/rl/starVLA/.venv/bin/python -B -m pytest \
  -o addopts='' --confcutdir=cosmos_framework/model/generator/mot \
  cosmos_framework/model/generator/mot/local_evidence_test.py \
  -k 'continual_ttt' -q
```

Result: `23 passed, 8 deselected`; only existing unknown `L0` mark warnings. Both changed files py_compile; child and root `git diff --check` PASS. No GPU/network/data/checkpoint/runtime/training/evaluation/inference command was run.

Requested exact closure verdict for this root + Gitlink:

`APPROVE_TO_CLOSE_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE`

or `REQUEST_CHANGES` with severity and exact `file:line` findings.

Scope remains prohibited: all Memory Prefix/source-ABI/runtime/attention/local_memory2llm/norm/KV/position/RoPE/mask/packing; chronology/native loss; production config/optimizer/checkpoint migration/refreeze; GPU/CUDA/torchrun; training/evaluation/inference; real model/data/cache/checkpoint; P4/P5/B2-T. C3 remains a separate docs-only Gate even if this C2 closure passes.

Approval authorizes only the CPU core implementation in `local_evidence.py` plus its adjacent CPU tests,
followed by documentation-only v0.3.1 source/ABI audit. It does not authorize Memory Prefix runtime wiring,
chronology/loss, GPU/CUDA/torchrun, training, evaluation, inference, optimizer/config refreeze, P4/P5 real
operations or B2-T.

---

## 2026-09-03 — ChatGPT independent review: R09-B TTT v0.3.1 route @ af9caf0

**Verdicts:**

`APPROVE_R09_B_TTT_V031_IMPLEMENTATION_ROUTE`

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_CPU_ALGORITHM_CORE`

Target:
- implementation/design SHA: `af9caf0cfffbb70b7fbf2e8bc3f763bf9bd9d1a2`
- request/ledger SHA observed at final review check: `d99490a169f84fa01b005db757609f5909a3c097`
- v0.3.1 authority: `4754f5bc25859894e6fc963a9484640ccb5cd082`
- CPU-core design re-reviewed in exact state: `216f1261c81cf6f2bd13053b5e937beeccd335b3`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

Accepted:
- Memory is K/V-only read-only context with no `Q_MEM`, output, residual or MLP;
- Local must leave the native AR/DM query pack and enter via a separate per-sample Memory context;
- current two-way dense DM attention should use one varlen joint softmax over `[K_MEM,K_AR,K_DM]`, while the AR causal pass remains unchanged;
- unsupported three-way/Flex/NATTEN/multi-control/CP/Ulysses/CUDA-graph combinations fail closed while Memory is present;
- exact norm/projection/RoPE/warm-start details remain frozen for the later source/ABI audit; zero K/V is correctly not treated as automatically function-preserving;
- the backbone-independent continual-TTT CPU core remains orthogonal to v0.3.1 and may be implemented before the later Memory Prefix source/ABI audit.

Non-blocking source-anchor note:
- route `docs/build/PSM-WMA_R09_B_TTT_v031_implementation_route_v0.1_2026-09-03.md:62` says the LIBERO recipe inherits `model_config.py:220`'s default `two_way`; the effective Edge recipe actually copies `EDGE_MODEL_CONFIG`, which explicitly sets `joint_attn_implementation="two_way"` at `cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py:44`. Effective behavior is still `two_way`; Gate-C source/ABI audit must cite the exact effective config path.

Authorized next step only:
- Gate B CPU-core implementation in `local_evidence.py` plus adjacent `local_evidence_test.py`, with only the CPU tests / `py_compile` / diff-check frozen by the design;
- then submit the new child implementation + root Gitlink bump for fresh same-SHA closure review.

Still prohibited:
- Memory Prefix runtime wiring;
- chronology/native-loss/runtime integration;
- GPU/CUDA/torchrun, training, evaluation or inference;
- optimizer/config/checkpoint authority refreeze;
- P4/P5 real operations;
- B2-T.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v031_architecture_route_af9caf0.md`

---

## 2026-09-03 — R09-B continual TTT CPU algorithm core closure @ fc5d429

Awaiting review — 🚨 审核申请已发出（根仓 `fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312`；子模块/Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5`）

Task/Gate: `G0-R09-B-TTT-V02-CPU-ALGORITHM-IMPLEMENTATION`

Review target:
- root implementation SHA: `fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312`
- Cosmos child implementation SHA / root Gitlink: `cf52f43dc328d4c8eec51923d66835125664dee5`
- approved route/design target: `af9caf0cfffbb70b7fbf2e8bc3f763bf9bd9d1a2`
- v0.3.1 authority: `4754f5bc25859894e6fc963a9484640ccb5cd082`
- implementation design: `docs/build/PSM-WMA_R09_B_TTT_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`

Exact implementation scope:
- `cosmos-framework/cosmos_framework/model/generator/mot/local_evidence.py`
- `cosmos-framework/cosmos_framework/model/generator/mot/local_evidence_test.py`

Implemented contract:
1. Adds an independent `ContinualTTTFastState` four-member pytree and functional `ContinualTTTLocalMemoryCore`; the superseded prototype and production `LocalHistoryRuntime` are unchanged.
2. Registers only Q/K/V and four learned-W0 tensors; defaults remain `D_e=256,D_local=32,D_ttt=64,D_ff=128,inner_lr=0.1,ttt_tbptt_steps=16`.
3. Implements per-sample KVB loss, simultaneous four-member higher-order SGD update, post-update query read, exact invalid-row inertia, learned-W0 reset, detach-only TBPTT boundary and fail-before-mutation grad-mode/input validation.
4. `step()` delegates to `project_evidence()+step_projected()`; `scan_segment()` uses the same step in chronology order and fails closed above the configured TBPTT length.
5. Clarifies that the scan output `[B,T,32]` retains per-timestep readouts for outer-loss/TBPTT tests only. Production Local remains one current readout `[B,1,32]`, later projected to one `[B,1,2048]` Memory Prefix token; no runtime wiring is implemented here.

Evidence:
- alternate existing Torch environment command:
  `/disk/rl/starVLA/.venv/bin/python -m pytest -q -o addopts='' --confcutdir=cosmos_framework/model/generator/mot cosmos_framework/model/generator/mot/local_evidence_test.py -k 'continual_ttt'`
  -> `16 passed, 8 deselected`;
- `python -m py_compile` for both changed files -> PASS;
- child and root `git diff --check` -> PASS;
- AST contract -> 16/16 named tests, functional no-subscript-mutation, fast-state elements 12,448, slow elements 53,568.

Environment disclosure:
- the frozen bare `/opt/conda/bin/python -m pytest ...` command cannot collect in this workspace because that interpreter lacks both `omegaconf` and `torch`;
- the existing StarVLA Torch environment has the runtime needed by the target test, but the repo-level pytest configuration references an unavailable custom-exit-code plugin and root conftest dependencies, so the two pytest configuration overrides above were required;
- no dependency was installed and no external data/model/checkpoint/GPU was accessed.

Acceptance requested:
- review the implementation against design C01-C16 and the functional/meta-gradient contract;
- confirm no production runtime, Memory Prefix attention, chronology owner, native-loss, config or optimizer surface changed;
- treat the environment variance explicitly and report whether it blocks code closure.

Requested exact verdict for this exact root + Gitlink:

`APPROVE_TO_CLOSE_R09_B_TTT_V02_CPU_ALGORITHM_CORE`

or `REQUEST_CHANGES` with severity and exact `file:line` findings.

Approval closes only this CPU algorithm core and permits the next documentation-only v0.3.1 source/ABI audit Gate. It does not authorize Memory Prefix runtime wiring, chronology/native-loss integration, GPU/CUDA/torchrun, training, evaluation, inference, optimizer/config/checkpoint refreeze, P4/P5 real operations or B2-T.

---

## 2026-09-03 — ChatGPT independent review: continual TTT CPU algorithm core @ fc5d429

**Verdict: APPROVE_TO_CLOSE_R09_B_TTT_V02_CPU_ALGORITHM_CORE**

Target:
- root implementation SHA: `fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312`
- child implementation SHA / Gitlink: `cf52f43dc328d4c8eec51923d66835125664dee5`
- request/ledger SHA observed before review write-back: `5577dadf822ead9df3df3b9806f0cb70200b2174`
- approved route/design state: `af9caf0cfffbb70b7fbf2e8bc3f763bf9bd9d1a2`

Closure:
- child scope is exactly the two authorized files; production `LocalHistoryRuntime`, config/optimizer, packing/trainer/loss, server/client, and Memory Prefix attention wiring are unchanged;
- the four-member fast state, Q/K/V + learned W0 registry, defaults/counts, fp32 KVB compute, per-sample feature-mean update, simultaneous four-member higher-order SGD, post-update read, invalid-row inertia, reset/detach, TBPTT scan, grad-mode guards, and `create_graph` semantics match the approved C01-C16 design;
- submitted targeted CPU evidence is `16 passed, 8 deselected`, plus `py_compile` and both child/root `git diff --check` PASS;
- use of the existing StarVLA Torch environment with pytest addopts/conftest overrides is accepted as a non-blocking test-environment variance for this isolated CPU mathematical core. It does not establish runtime/training interpreter authority.

Authorized next step only:
- documentation-only v0.3.1 exact Memory Prefix source/ABI audit Gate.

Still prohibited:
- Memory Prefix runtime/attention implementation;
- chronology/native-loss/runtime integration;
- optimizer/config/checkpoint refreeze;
- GPU/CUDA/torchrun, training, evaluation or inference;
- P4/P5 real operations;
- B2-T.

Any new root implementation SHA or child Gitlink requires a fresh review.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v02_cpu_algorithm_core_fc5d429.md`

---

## 2026-09-03 — R09-B v0.3.2 multi-slot Local TTT architecture review @ 3f7e434

Awaiting review — 🚨 审核申请已发出（根仓 `3f7e4341d5547eec23d2ff7370b45d34b51a96ca`；子模块/Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5`）

Task/Gate: `G0-R09-B-TTT-V032-MULTI-SLOT-ROUTE-REVIEW`

Review target:
- exact v0.3.2 authority commit: `3f7e4341d5547eec23d2ff7370b45d34b51a96ca`
- actual Gitlink at that root commit: `cf52f43dc328d4c8eec51923d66835125664dee5`
- authority document: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`
- superseded interface authority: v0.3.1=`4754f5bc25859894e6fc963a9484640ccb5cd082`
- retained K_local=1 compatibility core closure: root=`fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312`, Gitlink=`cf52f43dc328d4c8eec51923d66835125664dee5`.

Requested architectural judgment:
1. `K_local` is a configurable positive integer; every timestep performs exactly one K/V KVB write and only the post-update W is read by K_local evidence-conditioned Q slots.
2. `Q_t^k = theta_Q(e_t) + r_k`; Q and slot queries do not enter the inner KVB loss, while K/V receive outer-task gradients through differentiable inner update and Q/r_k receive direct outer-task gradients through readout.
3. The production interface is `[B,K_local,32] -> local_memory2llm -> [B,K_local,2048] -> Memory Prefix norm -> K_MEM/V_MEM only`; internal TTT Q is not Cosmos Q_MEM. AR remains Memory-blind; DM reads Memory+AR+DM.
4. The completed single-read CPU core is retained strictly as K_local=1 compatibility/sanity contract. It is not multi-slot implementation and cannot be used to bypass a new exact implementation review.
5. Proposed next route is docs-only multi-slot CPU-extension implementation design, then fresh implementation approval for `read_many`/query-bank CPU core, then exact v0.3.2 Memory Prefix source/ABI audit, then separate two-way attention contract and chronology/native-loss Gates. No runtime implementation is requested now.

Provenance question requiring an explicit verdict:
- v0.3.2 header calls `21d064f...` the current Cosmos baseline, but `git ls-tree 3f7e434 cosmos-framework` is `cf52f43...`. Please state whether this stale header anchor must be remediated before the route is frozen.

Allowed only if approved:
- write a versioned root docs-only multi-slot route/implementation design and its static verification plan.

Still forbidden:
- extending the CPU core, Memory Prefix/runtime/attention wiring, chronology/native-loss integration, model config/optimizer/checkpoint refreeze;
- GPU/CUDA/torchrun, training, evaluation, inference;
- P4/P5 real operations and B2-T.

Requested exact verdict for this root + Gitlink:

`APPROVE_R09_B_TTT_V032_MULTI_SLOT_ARCHITECTURE`

or `REQUEST_CHANGES` with severity and exact `file:line` findings.

---

## 2026-09-03 — R09-B v0.3.2 multi-slot provenance remediation re-review @ ef3ff1a

Awaiting review — 🚨 审核申请已发出（根仓 `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3`；子模块/Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5`）

Task/Gate: `G0-R09-B-TTT-V032-MULTI-SLOT-ROUTE-REVIEW`

Prior same-authority findings:
- ChatGPT HIGH-1, Kimi MEDIUM and MM HIGH-1 all identified only the stale current Gitlink at v0.3.2 header line 8.

Exact remediation scope:
- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md:8-9` only: current Cosmos Gitlink is now exact `cf52f43dc328d4c8eec51923d66835125664dee5`; old `21d064f...` is explicitly historical v0.3.1/pre-CPU-core source baseline.
- `SESSION.md` / `TODO.md` record the review/remediation state only.
- child Gitlink is unchanged; no CPU core, runtime, attention, configuration, test, GPU or training change occurred.

Static evidence:
- `git ls-tree ef3ff1a cosmos-framework` equals the declared current `cf52f43...`;
- current and historical anchors both exist exactly once in the authority header;
- one-write/many-read, Q/K/V responsibility, K/V-only Memory Prefix and K_local=1 compatibility clauses remain present;
- `git diff --check` PASS.

Requested exact verdict for this exact remediation root + Gitlink:

`APPROVE_R09_B_TTT_V032_MULTI_SLOT_ARCHITECTURE`

or `REQUEST_CHANGES` with severity and exact `file:line` findings.

Approval authorizes only the next versioned root docs-only multi-slot route/implementation design and static verification plan. It does not authorize CPU-core extension, Memory Prefix/runtime/attention wiring, chronology/native-loss integration, configuration/optimizer/checkpoint changes, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5 real operations or B2-T.

Review-file commit:
`f79dd56acda836fabbf029c054a431afb86528b1`

---

## 2026-09-03 — R09-B v0.3.2 multi-slot CPU-core implementation design review @ 411e967

Awaiting review — 🚨 审核申请已发出（根仓 `411e96760bdd1187303c0c2bfe2185223cc5c58e`；子模块/Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5`）

Task/Gate: `G0-R09-B-TTT-V032-MULTI-SLOT-CPU-DESIGN`

Review target:

- exact root design SHA: `411e96760bdd1187303c0c2bfe2185223cc5c58e`;
- exact child Gitlink: `cf52f43dc328d4c8eec51923d66835125664dee5` (unchanged; no child worktree/source change);
- new design: `docs/build/PSM-WMA_R09_B_TTT_v032_multi_slot_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`;
- approved v0.3.2 architecture/provenance authority: root `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3`, ChatGPT=`7f227ee`, Kimi=`2026-09-03 17:11 CST`, MM=`2026-09-03 17:17 CST`.

Requested review points:

1. `k_local` is a positive construction/checkpoint identity; `slot_queries[K_local,D_ttt]` is a registered slow parameter. K=1 zero-init gives new-API numerical read compatibility, while strict old-checkpoint migration is explicitly out of scope.
2. `project_evidence()` remains a K/base-Q/V triple. `project_queries()` produces `[B,K,D_ttt]`; `read_many()` is pure and produces `[B,K,D_local]` from one state.
3. For each valid sample, `step_projected_many()` has exactly one K/V-only higher-order inner update, then K post-update reads. Q/base query/slot query are excluded from `L_inner`; no state member or inner update is duplicated by slot.
4. Old K=1 public methods remain rank-compatible wrappers; K>1 must fail closed on legacy methods rather than silently discarding slots.
5. The test plan explicitly covers parameter/state payload counts, post-update manual KVB, update count independent of K, no read mutation, invalid rows, K=1 equivalence, slot permutation/isolation, gradients and strict K-mismatched checkpoint failure.

Static evidence:

- root `git diff --check` PASS;
- only root `docs/build/`, `SESSION.md`, and `TODO.md` changed in target; Gitlink resolves exactly to the listed child SHA;
- no Python/test/GPU/training/evaluation/inference/runtime command was run for this docs-only Gate.

Allowed only if approved:

- child CPU-only implementation limited to `cosmos_framework/model/generator/mot/local_evidence.py` and `local_evidence_test.py`, using synthetic CPU tensors and the frozen selector in the design.

Still forbidden:

- any Memory Prefix/runtime/attention wiring, `local_memory2llm`, LayerNorm, RoPE/mask/position, chronology/native-loss, config/optimizer/checkpoint migration/refreeze;
- GPU/CUDA/torchrun, training, evaluation, inference, real cache/data use, P4/P5 real operations or B2-T.

Requested exact verdict for this root + Gitlink:

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE`

or `REQUEST_CHANGES` with severity and exact `file:line` findings.

---

## 2026-09-03 — ChatGPT re-review: v0.3.2 multi-slot provenance remediation @ ef3ff1a

**Verdict: APPROVE_R09_B_TTT_V032_MULTI_SLOT_ARCHITECTURE**

Target:
- remediation/design SHA: `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3`
- request/ledger SHA observed before review write-back: `4def62e6b96cae6fb90699dd6bbbfefd0233f65a`
- actual child/Gitlink: `cf52f43dc328d4c8eec51923d66835125664dee5`
- prior blocked authority: `3f7e4341d5547eec23d2ff7370b45d34b51a96ca`

Prior review chain:
- `3f7e434...` received ChatGPT `REQUEST_CHANGES` with HIGH-1 because v0.3.2 header labeled historical `21d064f...` as the current Gitlink while the exact root pinned `cf52f43...`.
- detailed prior review: `docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_multi_slot_architecture_3f7e434.md`.

Closure:
- v0.3.2 now declares current Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5` and explicitly labels `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb` as the historical v0.3.1/pre-CPU-core source baseline;
- exact root `ef3ff1a...` independently resolves the child to the declared `cf52f43...`;
- accepted architecture is unchanged: exactly one K/V KVB write per new causal evidence, followed by `K_local` post-update TTT reads; Q/slot parameters stay out of the inner loss, Q/slots receive direct outer-task gradients, K/V are meta-learned through the differentiable inner update;
- Local remains `[B,K_local,32] -> [B,K_local,2048]` and enters the v0.3.1 K/V-only Memory Prefix; internal TTT Q does not create Cosmos `Q_MEM`;
- the closed `cf52f43` CPU core remains only `K_local=1` compatibility/sanity evidence and grants no multi-slot implementation authority.

Authorized next step only:
- create a versioned root docs-only multi-slot route/CPU-extension implementation design and static verification plan, then submit its new exact SHA for independent review.

Next design must explicitly freeze `K_local` construction/checkpoint semantics, query-bank registered shape, `read_many` contract, one-write/no-state-mutation properties, K=1 equivalence, slot permutation, gradient reachability, and parameter/checkpoint/optimizer implications.

Still prohibited:
- multi-slot CPU-core/query-bank implementation or child Gitlink change;
- Memory Prefix source/ABI implementation or runtime/attention wiring;
- chronology/native-loss/runtime integration;
- config/optimizer/checkpoint refreeze;
- GPU/CUDA/torchrun, training, evaluation or inference;
- P4/P5 real operations and B2-T.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_multi_slot_architecture_ef3ff1a.md`

Review-file commit:
`7f227eecc33b945cce8e65f7537a4b83901733fc`

---

## 2026-09-03 — ChatGPT independent review: v0.3.2 multi-slot CPU-core design @ 411e967

**Verdict: APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE**

Target:
- root design SHA: `411e96760bdd1187303c0c2bfe2185223cc5c58e`
- request/ledger SHA observed before review write-back: `86022073e631c60531d45ed90af90924f33bd643`
- child/Gitlink baseline: `cf52f43dc328d4c8eec51923d66835125664dee5`
- approved v0.3.2 architecture authority: `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3`

Accepted:
- `k_local` is construction/checkpoint-time identity, not a runtime-varying slot count;
- registered `slot_queries[K_local,D_ttt]` is the only multi-slot slow-parameter extension; fast-state payload remains unchanged;
- each valid sample performs exactly one K/V-only higher-order KVB write, followed by K pure post-update reads from the same `W_t`;
- Q/base query and slot queries remain outside `L_inner`; K/V retain differentiable-inner-update meta-gradient semantics;
- `project_evidence()` keeps the existing triple ABI; `project_queries`/`read_many` and `*_many` APIs carry the multi-slot rank explicitly;
- legacy public APIs remain K=1 compatible and fail closed for K>1;
- MS01–MS13 provide adequate CPU closure coverage for counts, one-write invariant, post-update read, state purity/inertia, K=1 equivalence, slot permutation/isolation, gradient reachability, scan equivalence and K-mismatch strict-load failure.

Non-blocking clarification:
- §1.3's “no checkpoint schema change” is interpreted as no checkpoint-loader/migration/config/refreeze change. C2 is explicitly allowed to add the designed module `state_dict` key `slot_queries`; old checkpoint migration remains out of scope.
- C2 proves synthetic CPU fp32 math only; it does not establish future bf16 production fast-state read/storage authority.

Authorized next step only:
- C2 child CPU-only implementation in exactly `cosmos_framework/model/generator/mot/local_evidence.py` and `local_evidence_test.py`;
- run only the frozen isolated synthetic CPU selector and static diff checks;
- then submit the new exact child SHA/root Gitlink for fresh same-SHA closure review.

Still prohibited:
- Memory Prefix/source-ABI/runtime/attention wiring, local_memory2llm, norm/KV projection, position/RoPE/mask;
- chronology/native-loss integration;
- production config/optimizer/checkpoint migration or refreeze;
- GPU/CUDA/torchrun, training, evaluation or inference;
- real cache/data/model/checkpoint access;
- P4/P5 real operations and B2-T.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_multi_slot_cpu_design_411e967.md`

Review-file commit:
`7e639bf2edbaf2a72c43e54b2473a9711ed29b56`

---

## 2026-09-03 — ChatGPT re-review: v0.3.2 multi-slot CPU core remediation @ 8b0ea2f

**Verdict: APPROVE_TO_CLOSE_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE**

Target:
- root remediation/implementation SHA: `8b0ea2fb289a4bced803148a51ac562165cc2f8d`
- child remediation SHA / Gitlink: `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- request/ledger SHA observed before review write-back: `3704b185dd90634f47a72d4f0cfd2040a2424b81`
- C1 design authority: `411e96760bdd1187303c0c2bfe2185223cc5c58e`

Closure:
- prior ChatGPT HIGH-1 is CLOSED: invalid rows now preserve all four fast-state leaves, append exact fp32 zero `[K_local,D_local]`, and `continue` before any fast read; valid rows alone execute the K/V inner update and post-update K-slot read;
- the new finite-overflow/call-count fixture proves an invalid row cannot reach `_fast_mlp`, remains `present=False`, returns finite exact-zero tokens, and preserves state exactly;
- direct negative/fail-before-update coverage now exists for `project_queries`, `read_many`, `step_projected_many`, and `step_many`, including rank/shape/dtype/nonfinite/device/state errors and a monkeypatched `autograd.grad` that must never run on invalid input;
- remediation remains limited to the two authorized child files; no C3+ surface changed;
- submitted CPU evidence is `23 passed, 8 deselected`, both changed files `py_compile` PASS, child/root `git diff --check` PASS, with no GPU/network/data/model/cache/checkpoint/runtime/training/evaluation/inference execution.

C2 is closed only for this exact pair. After all required reviewers close the same pair, the next activity may only be a separate docs-only C3 / v0.3.2 Memory Prefix source/ABI Gate request/design/static audit. This verdict does not approve C3 implementation.

Still prohibited:
- Memory Prefix/runtime/attention implementation, `local_memory2llm`, norm/KV projection, position/RoPE/mask/packing;
- chronology/native loss, production config/optimizer/checkpoint migration/refreeze;
- GPU/CUDA/torchrun, training/evaluation/inference or real model/data/cache/checkpoint access;
- P4/P5 real operations and B2-T.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_multi_slot_cpu_core_remediation_8b0ea2f.md`

Review-file commit:
`cecb31b8ac4f1040467952be759c289c2d390495`

---

## 2026-09-03 — Codex review request: v0.3.2 Memory Prefix source/ABI audit design @ 26bd78d

**Requested verdict:** `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_SOURCE_ABI_AUDIT` or `REQUEST_CHANGES`

Target:
- root audit/design SHA: `26bd78d4f3feb9659c63459393c61780bc0b94e7`
- child/Gitlink read-only baseline: `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- audit/design: `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_source_abi_audit_v0.1_2026-09-03.md`
- authority: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`

Scope requested:
- review only the C3 source/ABI audit design and static-audit boundary;
- verify source facts for `local_memory2llm`, existing GEN-stream injection, attention packing, history ABI, and the listed unresolved Prefix owner/norm/layout/visibility/RoPE/state/checkpoint contracts;
- if approved, authorize only docs/static audit continuation.

Not requested and still prohibited:
- child/runtime/attention/config/optimizer/checkpoint changes;
- GPU/CUDA/torchrun, model/data/cache access, staging, P4/P5 real operations, training/evaluation/inference.

Evidence and acceptance:
- `git diff --check` PASS;
- no child changes and no project-code execution;
- each source anchor must be reproducible from the pinned child SHA;
- all three reviewers must return a verdict for this exact root/Gitlink pair before any C4 implementation.

---

## 2026-09-03 — ChatGPT review: v0.3.2 Memory Prefix source/ABI audit design @ 26bd78d

**Verdict: REQUEST_CHANGES**

Target:
- root design SHA: `26bd78d4f3feb9659c63459393c61780bc0b94e7`
- request/ledger SHA: `ae4bd2320a69e2da4f747ff3034d9eb093459ffe`
- child/Gitlink read-only baseline: `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- pre-design/source root baseline: `2a08f4e37ddfa98038b35965fb4b9f79c1b90806`

Accepted:
- current `local_memory2llm` / modality-embedding ownership and zero-init facts;
- current `_encode_local_memory()` ordinary packed-hidden injection and Local inclusion in `all_gen_indexes`;
- current two-way GEN-full / UND-causal attention has no separate MEM K/V stream;
- current batch path can carry Local payloads but does not prove persistent fast state or K/V-only Prefix integration;
- Prefix owner/norm/layout/visibility/RoPE/state/checkpoint are the right C3 audit categories;
- docs/static-only scope is correct.

Blockers:
1. **HIGH — design SHA and source baseline are conflated as one root identity.** The exact C3 design under review is `26bd78d...`, but the design header and SESSION/TODO record the C3 root as `2a08f4e...`, which predates and does not contain this design. Remediation must separately label `C3 design SHA=26bd78d...`, `pre-design/source root baseline=2a08f4e...`, and child source baseline `1d90361...`; SESSION/TODO must use `26bd78d...` as the exact C3 design/root SHA.
2. **MEDIUM — the current-source map omits decisive Local packing/cardinality/RoPE facts.** At child `1d90361...`, `sequence_packing/sequence.py:545-588::pack_local_memory_tokens()` already accepts `[K_local,D_local]`, packs K rows, and assigns the current Local GEN-path text-style mRoPE without advancing the native cursor; meanwhile `local_evidence.py:616-657::LocalHistoryRuntime.forward()` still explicitly returns `[B,1,D]`. The C3 design must record both facts and state that packer multi-row capacity does not mean production multi-slot runtime is wired, and that target Prefix RoPE must not silently inherit the current GEN-path policy.

Required remediation:
- root docs/status only; do not modify the child;
- add the exact design/source-baseline identity split;
- add the two missing source anchors and their ABI boundary;
- submit the new exact root SHA with the same child baseline for fresh review.

Still prohibited:
- Memory Prefix/runtime/attention implementation or changes to `local_memory2llm`/norm/KV projection/position/RoPE/mask/packer;
- chronology/native loss, config/optimizer/checkpoint migration/refreeze;
- GPU/CUDA/torchrun, model/data/cache/checkpoint runtime access, training/evaluation/inference;
- P4/P5 real operations and B2-T.

Detailed review:
`docs/collab/chatgpt/reviews/2026-09-03_R09_B_TTT_v032_memory_prefix_source_abi_audit_design_26bd78d.md`

Review-file commit:
`d9fdcd0cdc9916e131b28463f2f37389c6a3b042`

---

## 2026-09-03 — Codex re-review request: C3 Memory Prefix source/ABI audit remediation @ 54ea4ce

**Requested verdict:** `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_SOURCE_ABI_AUDIT` or `REQUEST_CHANGES`

Three-party prior result for the superseded pair: ChatGPT `REQUEST_CHANGES` (HIGH identity split + MEDIUM missing packer/history anchors), Kimi `APPROVE`, MM `APPROVE`.

Remediation target:
- root remediation/design SHA: `54ea4cea9ba0eb513080b9505cf23b2446b5d86a`
- child/Gitlink unchanged read-only baseline: `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- design file: `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_source_abi_audit_v0.1_2026-09-03.md`

Changes are root docs/status only:
- explicitly separates C3 design SHA `26bd78d...` from pre-design/source root baseline `2a08f4e...`;
- adds `cosmos_framework/data/generator/sequence_packing/sequence.py:545-588::pack_local_memory_tokens()` multi-row capacity and current GEN-path mRoPE facts;
- adds `cosmos_framework/model/generator/mot/local_evidence.py:616-657::LocalHistoryRuntime.forward()` current `[B,1,D]` cardinality and the boundary that packer capacity is not production multi-slot runtime.

Acceptance and prohibition remain unchanged: only C3 docs/static audit closure is requested; no child/runtime/attention/config/optimizer/checkpoint changes, GPU/torchrun, model/data/cache, P4/P5, training/evaluation/inference. All three reviewers must verdict this exact root/Gitlink pair before C4.

---

## 2026-09-03 — Codex corrected review dispatch: C3 remediation

Awaiting review — 🚨 审核申请已发出（根仓 `b521b0305bdfbad9f9d4abc6960c64922adb6693`；子模块/Gitlink `1d90361aeb21db53129ac27ddcaa1285b258fbbc`）

这是对上一条 C3 remediation 申请的格式补发；审核对象、设计文件、范围和 verdict 请求完全不变。请针对上述 exact root/Gitlink pair 返回 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_SOURCE_ABI_AUDIT` 或 `REQUEST_CHANGES`，附 `file:line`。三方本轮 verdict 未齐前不得进入 C4。
