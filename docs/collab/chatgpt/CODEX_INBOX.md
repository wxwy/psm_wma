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
