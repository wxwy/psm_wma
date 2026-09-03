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
