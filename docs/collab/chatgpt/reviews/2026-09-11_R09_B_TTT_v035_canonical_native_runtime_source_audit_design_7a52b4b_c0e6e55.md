# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Runtime Source-Audit Design v0.1

**Date:** 2026-09-11  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-SOURCE-AUDIT-DESIGN`  
**Formal root:** `7a52b4bd00a2b0f5e6abb283c5212fa3f85b7bac`  
**Formal child/Gitlink:** `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`  
**Previous closed technical pair:** `e24e944a1dc8cfe2cab97ab19157f69be770c4f3` / `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_source_audit_design_v0.1.md:49)`

## 1. Lock / pair / diff classification

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md` before review. The latest effective request remains the exact formal pair above. Later `V2` commits are reviewer/MM/Kimi/ledger bookkeeping and do not replace the formal technical target.
- Independently verified the formal root tree: `cosmos-framework` resolves exactly to `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`; that child commit is reachable.
- Relative to the previous closed technical root `e24e944...`, the formal root is six commits ahead. The cumulative root diff contains `SESSION.md`, `TODO.md`, the new 72-line runtime source-audit design, reviewer/Codex ledgers, and the prior canonical review. The child Gitlink is unchanged; there is no new child production implementation in this Gate.
- The formal commit itself is docs-only and introduces the requested audit design plus SESSION/TODO bookkeeping.

## 2. Authority checked

I checked the new design against the still-effective chain rather than treating the previous CPU/static approval as runtime authorization:

- `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`
- `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.6.md`
- `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.8.md`
- `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.9.md`
- the closed synthetic CPU/static native-forward/loss contract at child `c0e6e55...`
- directly relevant current child production seams in `cosmos_framework/trainer/__init__.py`, `canonical_segment_production_adapter.py`, and `local_memory_segment.py`.

v0.3.8 explicitly preserves the inherited v0.3.6 contracts except for the recovery-plan construction it replaces; v0.3.9 only replaces the transient retry-budget owner and preserves the rest of v0.3.8. Therefore v0.3.6 loss partition, parameter/optimizer/checkpoint refreeze, and runtime-sidecar ordering remain authority for this Gate.

## 3. Blockers

### HIGH-1 — `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_source_audit_design_v0.1.md:49`

**Root cause**

The `real GA/scaler` audit row says the runtime must determine how v0.3.8 suffix recovery's **`GA_effective/N_window`** replaces ordinary `/grad_accum_iter`. There is no frozen scalar or ratio `GA_effective/N_window` in v0.3.8. The contract has two independent normalization owners:

```text
L_backward_mu = (planned_N_valid[mu] / N_window) * L_consumer_mu
              + (1 / GA_effective) * L_aux_mu
```

For a normal plan `GA_effective=GA`; for a suffix recovery plan `GA_effective=len(recovery.members)` and `N_window=sum(recovery.planned_N_valid)`. Treating this as an undifferentiated `GA_effective/N_window` rule leaves the source audit free to approve a wrong primary-loss coefficient, a wrong auxiliary coefficient, or a second GA division. That is precisely the scaling ambiguity this source-audit Gate is supposed to eliminate.

**Frozen contract violated**

- v0.3.6 §6: consumer and auxiliary losses have different scaling owners and the canonical path must not receive another unconditional `/grad_accum_iter`.
- v0.3.8 §§2-3: exact normal/recovery objectives above; normal and recovery `N_window`/`GA_effective` are separately defined.
- v0.3.9 §1: v0.3.8 suffix-only recovery, `GA_effective`, `N_window`, slow-step boundary and inherited contracts remain unchanged.

**Exact testable acceptance**

Revise the source-audit design so the audit must identify, by exact `file:line`, the unique runtime owner of each of the following and reject any duplicate owner:

1. `planned_N_valid[mu]`, `actual_N_valid[mu]`, and the pre-backward `actual==planned` check;
2. `N_window=sum(planned_N_valid)` over the exact current normal or recovery plan;
3. the primary coefficient `planned_N_valid[mu] / N_window`;
4. the auxiliary coefficient `1 / GA_effective`;
5. GradScaler scale/unscale and optimizer/scheduler boundaries **after** that objective is formed, with no second `/grad_accum_iter` or second GA scaling.

The design must state the exact normal-plan and suffix-recovery formulas, not the shorthand `GA_effective/N_window`, and require the full-valid normal case to reduce to the ordinary native `1/GA` behavior.

### HIGH-2 — `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_source_audit_design_v0.1.md:51,64-67`

**Root cause**

The `persistence/distributed` source-map row asks only for checkpoint save/load and rank ownership, and the post-audit sequence jumps from single-GPU smoke directly to LIBERO4IN1 matched smoke and formal training. This drops two still-effective v0.3.6 obligations:

1. before the canonical single-GPU smoke design, the runtime design must refreeze feature flags/dims, the exact trainable/slow parameter inventory, exact optimizer membership, checkpoint config identity, and fail-closed handling of incompatible old checkpoints;
2. after the single-GPU smoke and before LIBERO4IN1 matched smoke/formal training, formal runtime-sidecar design + CPU/static verification + resume smoke are mandatory.

The design does mention that a first GPU smoke may declare mid-episode resume unsupported and that a supported resume/distributed path needs a sidecar. That is not enough: §4 currently presents a complete authorized progression to formal training that omits the required sidecar/resume stage, while §3 does not force the source audit to collect the parameter/optimizer/checkpoint identity facts needed for the required refreeze.

**Frozen contract violated**

- v0.3.6 §7: feature/config/parameter/optimizer/checkpoint identity must be explicitly refrozen; old checkpoint handling is fail-closed unless separately reviewed.
- v0.3.6 §8: single-GPU smoke is followed by `runtime-sidecar design -> CPU/static verification -> resume smoke` before matched smoke and formal training.
- v0.3.8 §1 and v0.3.9 §1 retain those inherited v0.3.6 contracts.

**Exact testable acceptance**

Revise the audit design so that:

1. §3 explicitly requires a `file:line -> contract` source map for feature flags/dims, exact canonical slow/trainable parameter inventory, optimizer membership, checkpoint config/manifest/source identity, and old-checkpoint fail-closed handling; any missing or caller-guessed owner is `REQUEST_CHANGES`.
2. §4 restores the inherited ordering: the required feature/config/optimizer/checkpoint refreeze must be completed before the single-GPU smoke design/authorization; after single-GPU smoke, `runtime-sidecar design -> CPU/static verification -> resume smoke` must complete before LIBERO4IN1 matched smoke and formal training.
3. If a different ordering is desired, it must first be authorized by a new explicit superseding design contract; this audit design may not silently weaken the inherited sequence.

## 4. Positive findings / non-blockers

- The Gate is correctly docs-only and does not attempt to use the prior CPU/static closure as authorization for runtime implementation, real I/O, GPU, torchrun, training, evaluation, inference, or LIBERO4IN1.
- The source-map categories for model seam, packer/flatten, native loss, producer/cache, and persistence/distributed are directionally appropriate and require current-child `file:line` evidence instead of historical prose.
- The design correctly retains S0 as consumer-valid with Local absent, PAD exclusion, stream-major gather, exact pending-scan/native capability ownership, and the no-silent-legacy-injection principle.
- It correctly keeps the production scaler/optimizer hard-stop in place during the audit and requires a later implementation design rather than deleting the guard in place.
- The current child source still exhibits the expected source seams: production `training_step()` rejects canonical runtime with enabled GradScaler or real optimizer before the existing DDP/forward path, and the synthetic canonical-native lifecycle remains a one-shot capability with the post-mutation evidence boundary retained.

These positives do not close the two blockers because the next audit's acceptance language itself must be exact before it can authorize an implementation design.

## 5. Evidence statement

This was a docs/source review. I did **not** execute project Python, native forward/loss/backward, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, optimizer/scheduler steps, training, evaluation, inference, runtime sidecar, or LIBERO4IN1. The current request states that no such execution occurred. No runtime-test claim is used to support this verdict.

## 6. Scope of verdict

`REQUEST_CHANGES` applies only to `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-SOURCE-AUDIT-DESIGN` at the exact formal pair `7a52b4bd... / c0e6e55...`.

It does not reopen the already closed synthetic CPU/static native forward/loss Gate. It also does not authorize the proposed read-only runtime source/ABI audit until the design is remediated and independently reviewed at a new formal root pair.

## 7. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_source_audit_design_v0.1.md:49)`
