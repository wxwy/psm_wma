# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Runtime Implementation Design

- Date: 2026-09-11
- Formal root design SHA: `bb71e4fe49e3ae146b48ccab01cc8c397753d43c`
- Child/Gitlink SHA: `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`
- Request/ledger commit: `67546a0b73efe84f7a87af26ed6f6915ec612c2f` (not part of the formal pair)
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-IMPLEMENTATION-DESIGN`
- Review object: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_implementation_design_v0.1.md`
- Inherited source-audit authority: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_source_audit_design_v0.1.md` + superseding v0.2 §§1-4
- Prior source/ABI audit pair: `8d9bcee0df5f414f21c0e4b94c1ed617d58b3c6e / c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`

## Verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_implementation_design_v0.1.md:4-6)`

## Current blockers

3 HIGH.

### HIGH-1 — predecessor Gate provenance is stale and uses a non-frozen verdict literal

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_implementation_design_v0.1.md:4-6`

The exact formal root records the predecessor ChatGPT verdict as `SOURCE_AUDIT_COMPLETE`. The predecessor source/ABI audit request froze only `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`. `SOURCE_AUDIT_COMPLETE` was therefore not a valid formal verdict literal.

ChatGPT has now repaired that predecessor record as a persistence-only correction (canonical review correction commit `2d35448c7eb587eabef817db141c32b74fa87014`; coordination correction commit `bcf71f4d5ef3f4bcbc340b8a1c5c74c4b1b1afe2`) without repeating the technical audit. However, this exact `bb71e4f...` design root still freezes the stale literal and therefore does not accurately identify its predecessor authority.

**Violated frozen contract:** exact Gate/verdict authority and traceable predecessor closure.

**Acceptance:** submit a new formal root whose design records the predecessor ChatGPT verdict exactly as `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_IMPLEMENTATION`, with the same predecessor formal pair and corrected canonical review provenance. Do not retain or alias `SOURCE_AUDIT_COMPLETE` as a formal verdict.

### HIGH-2 — the design header can be read as direct code authorization, contradicting this Gate's frozen scope

**Locations:** `...runtime_implementation_design_v0.1.md:4` and `:115-125`

Line 4 says that after three parties provide `APPROVE_TO_IMPLEMENT`, code may be changed. But §8 freezes a different verdict — `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_CPU_STATIC_IMPLEMENTATION` — and explicitly says approval only allows creation of the next **docs-only CPU/static implementation design**, not child implementation.

This is not a wording-only issue: the header creates a second, broader authorization path that can bypass the next Design Gate.

**Violated frozen contract:** Design Gate and Implementation Gate must remain separate; approval scope is only the exact next docs-only design step.

**Acceptance:** the header must use the same authorization semantics as §8: approval of this Gate may create/review only the next CPU/static implementation design. It must explicitly state that child/code changes remain forbidden until that later design is separately approved and an implementation Gate is opened. Remove `APPROVE_TO_IMPLEMENT` from this Gate unless a separate frozen authority explicitly introduces that literal.

### HIGH-3 — immutable-window suffix recovery is weakened into per-microbatch refreeze + terminal no-replay

**Locations:** `...runtime_implementation_design_v0.1.md:54-56` and `:75-89`

Inherited authority is explicit that v0.3.8/v0.3.9 semantics include an **immutable plan**, **suffix-only retry/recovery**, fast-commit retain, and partial slow-gradient discard. Source-audit v0.2 further freezes normal/recovery ownership of `planned_N_valid`, `N_window`, and `GA_effective` (`GA` for normal, `len(recovery.members)` for recovery).

The current design instead says:
- any forward/backward exception terminalizes the capability and forbids replay;
- each microbatch sequence starts with `freeze plan`;
- objective text uses `/GA` and does not define recovery `GA_effective` or suffix-plan ownership.

That leaves no frozen owner for attempt-1/suffix lineage and permits an implementation to refreeze/admit per microbatch rather than consume one immutable window transaction.

**Violated frozen contract:** immutable plan / suffix-only recovery / exact retry lineage / recovery GA transaction semantics.

**Acceptance:** the remediation must freeze all of the following before implementation design can be approved:
1. the normal GA window plan is frozen once; each microbatch consumes an exact member of that immutable plan rather than calling a fresh admission/freeze;
2. recovery is suffix-only and derived from the original frozen transaction; attempt-1 reuses the exact attempt-0 owner/transaction and cannot perform second admission, resample, or unrelated refreeze;
3. `N_window=sum(planned_N_valid)` remains owned by the relevant normal/recovery plan, primary scale is `planned_N_valid[mu]/N_window`, and auxiliary scale is `1/GA_effective`, with recovery `GA_effective=len(recovery.members)`; no second `/GA` is permitted;
4. already committed fast state remains committed, controlled partial slow gradients are discarded exactly per the inherited recovery contract, and the original transition is reconciled once;
5. tests in the next CPU/static design must witness normal and suffix-recovery ownership separately, including a failure after an earlier member has committed.

## Findings that are acceptable in this root

The following design choices are aligned with the frozen contract and are not blockers:

- S0 remains a native consumer while Local prefix is `None`; tail PAD has no update/prefix/loss.
- stream-major gather uses `flat=b*T+t` and preserves exact consumer identity.
- continued state is same-slot detached carry after successful backward; fresh admission clones learned `W_bar_0`.
- legacy `local_memory` payload is not promoted into the canonical route.
- primary and auxiliary scaling are kept conceptually separate and a second ordinary `/grad_accum_iter` is rejected.
- runtime cursor/state commit occurs only after backward success; Option-B scaler-skip retains already committed fast state and does not advance slow step/scheduler.
- current scaler/optimizer hard-stop and missing runtime sidecar/resume support remain fail-closed.

These positives do not close the three HIGH blockers above.

## Pair / source verification

- Root `bb71e4fe49e3ae146b48ccab01cc8c397753d43c` resolves `cosmos-framework` exactly to `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`.
- The child commit is reachable in `wxwy/cosmos-framework`.
- Child is unchanged from the immediately preceding reviewed pair; this review therefore focuses on the new root design and inherited frozen contracts rather than re-reviewing unchanged child production code.

## Evidence and execution scope

This is a docs-only Design Gate. No project Python, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native forward/loss/backward, optimizer/scheduler step, training, evaluation, inference, runtime sidecar, distributed execution, or LIBERO4IN1 was executed or authorized.

## Closure scope

No code implementation is authorized by this verdict. Required next action is only a docs-only remediation on a new formal root, preserving the same child unless an independently authorized child change is introduced. Any new root or child SHA requires a fresh incremental review.