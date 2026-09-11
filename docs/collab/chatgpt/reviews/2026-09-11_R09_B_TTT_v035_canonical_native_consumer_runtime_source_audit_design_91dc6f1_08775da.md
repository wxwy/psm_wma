# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Consumer Runtime Source-Audit Design v0.1

**Date:** 2026-09-11  
**Formal root:** `91dc6f16d80c410aaa103637cd0e65efc7888525`  
**Formal child/Gitlink:** `08775da2e73e352ebb1497548de5909baab8c2dc`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-SOURCE-AUDIT-DESIGN`  
**Requested verdicts:** `APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_SOURCE` or `REQUEST_CHANGES(file:line)`.

## 1. Lock / pair / scope

I re-locked remote `V2`, re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`, and independently verified the formal root submodule entry. At root `91dc6f16d80c410aaa103637cd0e65efc7888525`, `cosmos-framework` resolves exactly to reachable child `08775da2e73e352ebb1497548de5909baab8c2dc`.

The formal root is docs-only for this Gate: the technical object is the newly added `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_consumer_runtime_source_audit_design_v0.1.md`; the child is unchanged from the already-closed Canonical Segment Production ABI CPU/static pair. This review therefore evaluates only whether the proposed read-only source audit preserves the full current contract and is sufficiently constrained to produce safe facts for a later implementation design.

## 2. Positive findings

The proposal has several correct constraints:

- it explicitly refuses to infer production runtime connectivity from the closed synthetic CPU/static Gate;
- it keeps the audit read-only: no child modification, Python/pytest, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, real native forward/loss/backward, optimizer/scheduler step, runtime sidecar, training, evaluation, inference or LIBERO4IN1;
- it asks for `file:line` source evidence, object/input/output identity and explicit PASS/FAIL rather than prose guesses;
- it directly covers the important v0.3.5 §20.2 themes around variable-valid packing, native reduction, planned valid counts, weighted scheduling/provenance, true feature disable and old active-wiring supersession;
- it correctly forbids trainable zero-PAD as a substitute for a variable-valid consumer ABI;
- it treats single-GPU work as static feasibility/accounting only and does not authorize a smoke run.

Those are good properties, but two contract regressions prevent approval of the design as written.

## 3. Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_consumer_runtime_source_audit_design_v0.1.md:9)`

Current blockers: **2 HIGH, Design-only**. Production blockers: **0**. Evidence blockers: **0**.

---

## HIGH-1 — Current training/runtime supersessions are omitted from the audit authority and loss/recovery acceptance

**Locations:**

- `...canonical_native_consumer_runtime_source_audit_design_v0.1.md:11-15` — upstream authority list;
- `...canonical_native_consumer_runtime_source_audit_design_v0.1.md:33-34` — loss/reduction and planned-count questions.

### Root cause

The proposed authority list names the v0.3.5 detailed addendum, the later Segment Production ABI implementation design and the closed CPU/static pair, but omits the still-binding Canonical Training & Runtime contracts v0.3.6/v0.3.8/v0.3.9.

That omission is material because this audit explicitly asks about normal/recovery `planned_n_valid`, `N_valid` weighting and GA semantics. The latest binding recovery contract does not permit those semantics to be summarized merely as “`N_valid` weighting with full batch reducing to `1/GA`”. It freezes, for normal and suffix-recovery plans, the exact owners and formula:

```text
actual_N_valid[mu] == planned_N_valid[mu]     # pre-backward
N_window = sum(planned_N_valid)
L_backward_mu
  = planned_N_valid[mu] / N_window * L_consumer_mu
  + 1 / GA_effective * L_aux_mu
```

with normal `GA_effective=GA`, suffix recovery `GA_effective=len(recovery.members)`, recovery membership fixed to the uncommitted suffix, and no second unconditional `/grad_accum_iter`/GA scaling downstream. v0.3.9 changes only retry-budget ownership and explicitly preserves the v0.3.8 recovery/loss semantics.

A source audit run under the current v0.1 wording could therefore report a path as suitable for valid-exposure weighting while failing to prove the auxiliary coefficient, recovery denominator, pre-backward actual/planned equality or the absence of a second GA division. That would regress a contract already frozen and previously required by ChatGPT’s approved Native Runtime Source-Audit Design v0.2.

### Exact acceptance

Amend the P0 design so that the current v0.3.6/v0.3.8/v0.3.9 contract chain is explicit binding authority for this audit. The audit output must map `file:line -> unique owner -> fail-closed` for at least:

1. `planned_N_valid[mu]`, `actual_N_valid[mu]` and pre-backward `actual==planned`;
2. `N_window=sum(planned_N_valid)` for normal and suffix-recovery plans;
3. primary coefficient `planned_N_valid[mu]/N_window`;
4. auxiliary coefficient `1/GA_effective`;
5. normal `GA_effective=GA` and recovery `GA_effective=len(recovery.members)` with suffix-only recovery membership;
6. objective formation before GradScaler/backward/optimizer seams and explicit proof that no second `/grad_accum_iter`/GA scaling is applied;
7. full-valid normal case reducing exactly to native `(L_consumer + L_aux)/GA`.

This is still entirely docs-only/read-only and does not authorize execution.

---

## HIGH-2 — v0.3.5 §20.2 is mis-stated as six questions; G/H are not completely frozen

**Locations:**

- `...canonical_native_consumer_runtime_source_audit_design_v0.1.md:9` — states that §20.2 contains six source questions;
- `...canonical_native_consumer_runtime_source_audit_design_v0.1.md:37` — static single-GPU feasibility item;
- `...canonical_native_consumer_runtime_source_audit_design_v0.1.md:41-49` — required audit outputs / later-Gate handling.

### Root cause

The authoritative v0.3.5 §20.2 contains **A through H**, not six items:

- A–F: packer, loss seam, planned count, weighted scheduler, feature disable, active-wiring supersession;
- G: actual single-GPU memory/throughput/higher-order-gradient/fp32-`W_fast` budget feasibility;
- H: formal-training runtime sidecar, distributed ownership and world-size-change fail-closed must be a separate Gate.

The proposed design does add a useful static item covering part of G, but it deliberately forbids throughput measurement and does not explicitly state that the unresolved throughput/budget portion of G cannot receive PASS from this source audit and must remain deferred to an approved single-GPU smoke Gate. H is not explicitly carried forward at all; a generic “must separately Gate what cannot be answered” is weaker than the authority’s mandatory sidecar/distributed/world-size-change separation.

This matters because the document says its output becomes input to the next native implementation design. The P0 design must not allow G/H to disappear from that handoff merely because they cannot be answered read-only.

### Exact acceptance

Correct the authority description to §20.2 A–H and explicitly classify the later-only items:

1. A–F: source-audit questions to resolve with current `file:line` evidence;
2. G: audit only static prerequisites (`W_fast` storage, higher-order graph lifetime, single-device admission and CP/DDP restrictions); mark actual memory/throughput/budget satisfaction **DEFERRED / NOT PROVEN** until a separately approved single-GPU smoke Gate, with no estimation or execution in P0;
3. H: explicitly preserve runtime-sidecar schema/restore, distributed ownership and world-size-change fail-closed as a mandatory separate Gate before any claim of resume/distributed/formal-training support.

The audit artifact should carry those deferred obligations forward by name, not merely through a generic future-Gate bucket.

---

## 4. No other blocker found

Subject to the two corrections above, the remaining proposed audit structure is sound for a read-only P0 Gate: its current-source `file:line` discipline, variable-valid/PAD handling, prefix ownership table, scheduler/provenance questions, real feature-disable requirement and retain/bypass/delete supersession table are appropriate.

The older `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-SOURCE-AUDIT-DESIGN` was based on an older child and is not treated as current-source evidence here. Its already-approved contract refinements, however, cannot be silently weakened by this later narrower Gate.

## 5. Scope

This verdict is bound only to formal pair `91dc6f16d80c410aaa103637cd0e65efc7888525 / 08775da2e73e352ebb1497548de5909baab8c2dc` and the exact docs-only design Gate above.

No child implementation, project-code execution, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward, optimizer/scheduler step, runtime sidecar, training, evaluation, inference, distributed execution, smoke or LIBERO4IN1 is authorized.
