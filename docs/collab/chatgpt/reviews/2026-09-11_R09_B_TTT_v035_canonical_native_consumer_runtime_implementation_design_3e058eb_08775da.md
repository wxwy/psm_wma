# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Consumer Runtime Implementation Design v0.1

**Date:** 2026-09-11  
**Formal root:** `3e058eb418c63188856fa3d36667227561ca3a91`  
**Formal child/Gitlink:** `08775da2e73e352ebb1497548de5909baab8c2dc`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-IMPLEMENTATION-DESIGN`  
**Requested verdicts:** `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 1. Lock / pair / scope

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`. Current `V2` request/bookkeeping HEAD is not the technical target; the effective formal pair is the exact pair above.
- Independently verified root `3e058eb418c63188856fa3d36667227561ca3a91` resolves `cosmos-framework` exactly to reachable child `08775da2e73e352ebb1497548de5909baab8c2dc`.
- Relative to the closed source-audit formal root `d554ee6498c4d4facd60cf688beec77c86ea8705`, the child is unchanged. The new technical object is the root-only implementation design `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_consumer_runtime_implementation_design_v0.1.md`; intervening changes are prior review / inbox / bookkeeping material.
- No project code was executed for this design review.

## 2. Positive findings

The design correctly preserves the closed source-audit facts and several important fail-closed constraints:

- exact stream-major carrier identity and PAD exclusion remain authoritative;
- sparse `list[Tensor|None]` Memory Prefix remains the only Local Prefix ABI; trainable zero-PAD is forbidden;
- the new continuation must reuse native pack/noise/denoise/loss rather than recursively call ordinary `training_step()` or re-enter row-wise Local history injection;
- native modality loss must be split into per-consumer primary and independent auxiliary terms before plan scaling; the final scalar may not be reverse-engineered;
- `CanonicalGAWindowPlan.objective()` remains the sole owner of `planned/N_window` primary scaling plus `1/GA_effective` auxiliary scaling, including suffix-only recovery;
- one canonical-native backward is separated from ordinary unconditional `/grad_accum_iter`;
- legacy row-wise/active marker paths are required to be isolated;
- GPU, real I/O, producer/data integration, checkpoint refreeze, sidecar/resume and matched/formal training remain out of scope.

The six-file implementation whitelist is not itself a blocker. The current child already contains `compute_flow_matching_loss_terms()` / `FlowMatchingLossTerms.canonical_weighted_per_instance` in `algorithm/loss/flow_matching.py`, so the design can consume that existing API from `omni_mot_model.py` without modifying the loss module. If implementation discovers a required loss-file change, the design already requires a new Gate.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_consumer_runtime_implementation_design_v0.1.md:68)`

Current blockers: **2 HIGH, Design-only**. Production blockers: **0**. Evidence blockers: **0**.

---

## HIGH-1 — CPU/static design weakens the existing scaler/optimizer admission boundary while explicitly deferring its lifecycle semantics

**Location:** `...canonical_native_consumer_runtime_implementation_design_v0.1.md:68`.

### Source fact

Current production `ImaginaireTrainer.training_step()` rejects canonical-production **before scan/callback/model-forward** when either:

```text
grad_scaler.is_enabled()
OR
isinstance(optimizer, torch.optim.Optimizer)
```

and `_run_canonical_native_backward()` independently rejects enabled scaler before marking backward started. Only after that reject does the helper call `grad_scaler.scale(objective).backward()`; with a disabled scaler that call is a legal no-op wrapper and does not imply enabled-AMP support.

### Design regression

v0.1 says the current "enabled scaler reject 后 scale" must be removed and replaced by a "verified GradScaler route", while §4 simultaneously says optimizer/LR `GradScaler`-skip semantics are not implemented and stay in a later Gate. The design does not freeze whether the existing real-optimizer pre-scan rejection must remain, nor does it define the lifecycle semantics needed if an enabled scaler is admitted.

That is unsafe for an implementation authorization: an implementer could legally satisfy the text by removing the combined guard and thereby allow a real optimizer / enabled scaler into a route whose unscale/step/skip/zero-grad/LR consequences this Gate explicitly does not own.

### Exact acceptance

For this CPU/static Gate, choose and freeze one safe boundary. The minimal acceptable option is:

1. preserve pre-scan fail-closed rejection for any real `torch.optim.Optimizer`;
2. preferably preserve enabled-GradScaler rejection too, and prove the one-scale/one-backward structure with a disabled scaler / CPU-static test double;
3. if the design insists on admitting an enabled scaler for CPU-only scale/backward evidence, explicitly preserve the real-optimizer rejection and state that this Gate proves only scale/backward, not optimizer/unscale/skip disposition;
4. removal of the real-optimizer rejection and any claim of scaler skip / optimizer / LR semantics must require the later separately approved runtime/GPU Gate;
5. add direct production-entry witnesses that the forbidden real optimizer (and any still-forbidden scaler state) rejects before callback/model-forward/scan with zero scheduler/transaction/frontier mutation.

---

## HIGH-2 — DDP/FSDP/world-size is declared deferred but the proposed production continuation has no corresponding fail-closed admission rule

**Locations:** `...canonical_native_consumer_runtime_implementation_design_v0.1.md:81` and acceptance item 6 around line 92.

### Source fact

The existing trainer enters `distributed.ddp_sync_grad(...)` around forward/backward. The ordinary model loss path also computes sample-level scaling from the distributed averaging group and may `all_reduce` global sample counts. The current canonical model-side pre-scan guard rejects context parallelism, but the closed source audit explicitly found that this is **not** a complete distributed/world-size contract.

### Design regression

v0.1 correctly says `DDP/world-size` is not implemented and must remain a separate Gate, but its CPU/static acceptance only requires fail-closed behavior for CP and selected attention modes. It never requires the new canonical native continuation to reject DDP/FSDP/world-size>1 before scan/native work.

Once the hard-stop is replaced, that omission would leave a path capable of entering distributed sync / distributed sample-level loss semantics even though this Gate expressly declares them NOT IMPLEMENTED / not authorized.

### Exact acceptance

Amend the design so that until the dedicated distributed Gate is approved:

1. canonical-production admission fails closed before scan/native work for every unapproved distributed configuration (DDP/FSDP/data-parallel/world-size>1; CP remains rejected as today);
2. single-process/world-size-1 CPU/static is the only admitted execution class for this Gate;
3. add direct rejection witnesses proving callback/model-forward/core scan is not entered and scheduler/transaction/frontier/scan bookkeeping remains unchanged;
4. later distributed support must separately freeze global `N_window`, DDP/FSDP gradient averaging, `_sample_level_loss_scale`/all-reduce ownership, rank-local fast state and world-size-change semantics before removing that guard.

---

## 4. No other blocker found

Subject to the two admission-boundary corrections above, the rest of the design is sufficiently constrained for a six-file synthetic CPU/static implementation. In particular, current source already provides the typed per-instance flow-matching terms needed by the design, so there is no present evidence that the whitelist must expand.

The requested implementation must continue to preserve the existing pre/post-mutation commit failure semantics in `trainer._run_canonical_native_backward()` and the adapter; this review does not authorize weakening those already-reviewed contracts.

## 5. Scope

This verdict is bound only to formal pair `3e058eb418c63188856fa3d36667227561ca3a91 / 08775da2e73e352ebb1497548de5909baab8c2dc` and the exact implementation-design Gate above.

No child implementation, removal of production hard-stops/admission guards, project execution, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native real forward/loss/backward, optimizer/scheduler step, distributed execution, sidecar/resume, matched smoke, training, evaluation, inference or LIBERO4IN1 is authorized by this review.
