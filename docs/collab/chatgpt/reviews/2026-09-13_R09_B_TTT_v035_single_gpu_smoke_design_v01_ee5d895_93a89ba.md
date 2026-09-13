# ChatGPT Review — R09-B TTT v0.3.5 Single-GPU Smoke Design v0.1

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-SINGLE-GPU-SMOKE-DESIGN`

## Exact formal pair

- root design SHA: `ee5d895043222763849ab60aa17d782f3c1596fd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its tree records `cosmos-framework` as mode `160000` at exactly `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior ChatGPT-reviewed pair `aba42f3c077629074f3f8c03420bc8a01bc1ebd7 / 93a89ba61306d840a008813f62f26a34d54850f4`. The formal scope is docs-only: `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_design_v0.1.md` plus task records; child/runtime is unchanged.

Requested verdict:

`APPROVE_TO_DESIGN_R09_B_TTT_V035_SINGLE_GPU_SMOKE_EXECUTION`

or `REQUEST_CHANGES(file:line)`.

Approval at this Gate would authorize only the next docs-only single-GPU smoke execution runbook/command design. It would not authorize reading real source/checkpoint/manifest/data/cache, source-evidence publication, child/runtime/config changes, CUDA/GPU execution, torchrun, training, evaluation, inference, or LIBERO4IN1.

## Authority and review focus

The design explicitly preserves the previously frozen Local chronology / S0 / shifted evidence / T=16 / B_stream=8 / K_local=1 / fp32 fast-state semantics, delegates segment/tail/GA failure/GradScaler behavior to the approved canonical-semantics and native CPU/static contracts, and keeps immutable source-evidence post-commit receipt as the sole real-input prerequisite. This review therefore checks the new single-GPU execution admission, bounded smoke transaction, failure semantics, PASS conditions, and scope without reopening those prior closed contracts.

The new design is coherent on the following material points:

- source-evidence post-commit receipt remains prerequisite authority and no new horizontal provenance Gate is introduced;
- `world_size=1`, no `torchrun`, `num_workers=0`, no resume/sidecar resume, fresh smoke-only output root, and bounded positive step count `<=100` are intended as hard admission constraints;
- GA-window failure preserves already-committed fast chronology while clearing partial slow gradients and forbidding slow optimizer/LR step for the failed window, with no replay/resample/rewrite;
- smoke PASS is bounded to execution-path viability and does not claim convergence, SR, checkpoint reload, deployment, or formal training closure.

## Current blocker

### HIGH-1 — valid single-GPU admission contradicts the immediate FAIL predicate

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_design_v0.1.md:93` (§5, immediate FAIL conditions).

**Root cause:** §3.5 and §4 explicitly freeze the only admitted execution topology as `world_size=1`. However §5 declares `非零 world size` (non-zero world size) to be an immediate FAIL condition. Taken literally, the sole valid single-GPU value `world_size=1` is itself non-zero and therefore must fail immediately.

This leaves the future execution runbook with two mutually exclusive frozen instructions: admit `world_size=1`, then fail because `world_size` is non-zero. A runbook cannot resolve this by inference or implementation convention because this Gate is supposed to freeze the exact fail-closed admission predicate before any GPU execution authorization.

**Violated frozen contract:** the design's own §3.5/§4 exact single-GPU admission (`world_size=1`) and the Gate's requested unambiguous world-size-1/no-torchrun execution path.

**Why current Evidence/design text does not close it:** the request and surrounding sections repeatedly state `world_size=1`, but nothing explicitly supersedes or narrows the §5 literal `非零 world size` FAIL predicate. A later runbook must not silently guess that the intended wording was `world_size != 1`.

**Exact acceptance:**

1. replace the §5 immediate-failure condition with an exact predicate consistent with admission, e.g. `world_size != 1` / `非 1 world size`;
2. preserve §3.5 and §4 exact `world_size=1`, no-`torchrun` admission;
3. ensure the future runbook/static preflight uses the same exact predicate and fails before CUDA/training work on any value other than 1;
4. make no scope expansion while remediating this wording/contract conflict.

## Evidence / feasibility assessment

This is a design blocker, not an implementation- or Evidence-only blocker. The formal target is docs-only and correctly avoids real source/checkpoint/data I/O and GPU execution. No additional production/runtime change is required to close this review; the design contract itself must first be made internally consistent.

No additional current blocker was found in the new GA-window chronology/failure text: its preservation of already-committed fast chronology, clearing of the partial slow-gradient window, no slow optimizer/LR step on the failed window, fresh next-window planning, and prohibition on replay/resample/rewrite are internally coherent at this design layer.

## Blocker summary

- current blockers: `1 HIGH`
- design/admission blockers: `1 HIGH`
- implementation blockers: `0`
- Evidence-only blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_single_gpu_smoke_design_v0.1.md:93)`

This verdict binds only exact pair `ee5d895043222763849ab60aa17d782f3c1596fd / 93a89ba61306d840a008813f62f26a34d54850f4`.

No single-GPU smoke execution-runbook design approval is granted from this pair. No real input I/O, source-evidence publication, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.