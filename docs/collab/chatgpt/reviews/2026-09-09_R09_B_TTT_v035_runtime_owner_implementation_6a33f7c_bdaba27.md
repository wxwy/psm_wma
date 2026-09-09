# ChatGPT 独立 Runtime Owner CPU/static remediation review

Formal reviewed pair:
- root implementation SHA: `6a33f7c1ed411f8d71d74ea4d29b4cc063754962`
- child/Gitlink SHA: `bdaba2729dfb343705e08fe91881eba580ad310a`
- Gate: `G0-R09-B-TTT-V035-RUNTIME-OWNER-CPU-STATIC-IMPLEMENTATION`
- previous implementation pair: `acf1cfe35844fbfc2ecdabe1f41f048061dd720f` / `d12dda51d9f0eb89310e5e785d4f485dd3e68be2`
- approved design authority: `c31eecbf40f38ab0b6b4d277cd425c5b45e66744` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`, v0.8-v0.8.7

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh remediation review of the runtime-owner CPU/static implementation. Root changes only advance the Gitlink; child changes remain within the approved whitelist. The remediation adds the previously missing owner methods, single-owner guard and fp32 snapshot conversion. Request-reported `py_compile` and diff-check are PASS; directed pytest still did not run because the environment lacks `omegaconf`, so no pytest PASS is credited.

## Prior blocker status

- **CLOSED IN SURFACE — missing owner methods.** Normal commit/finish, multi-member continuation, terminal/retry paths, begin-retry, snapshot type and single-owner binding now exist.
- **CLOSED — committed snapshot fp32 ABI.** `committed_snapshot()` now converts detached cloned fast-state tensors to fp32 and adds an adjacent isolation test.
- **OPEN — Evidence remains insufficient.** The runtime-owner test file is still the prior two private-state skip fixtures; see blocker 4.

## Current blockers

1. **HIGH — `admit_next()` mutates scheduler authority before proving the chosen identity is the frozen next plan member.**
   - implementation: `cosmos_framework/model/generator/mot/canonical_segment_runtime.py` (`admit_next`)
   - inherited contract: v0.8.1 per-member/window phase machine and fail-closed skip/reorder rule.

   `admit_next()` calls `scheduler.admit(candidates)` first. That call immediately appends the chosen identity to `admission_order` and writes `stable_slots[slot]`. Only afterwards does the owner compare the chosen projection against `transaction.plan.members[index]`. If scheduler selection chooses an admissible but wrong candidate, the method raises but leaves scheduler chronology mutated. This violates the frozen requirement that skip/reorder fail closed and poisons later sidecar/scheduler continuation authority.

   **Acceptance:** prove the exact next member before scheduler mutation, or otherwise ensure the only candidate passed to `scheduler.admit()` is the exact frozen next full identity authorized by owner state. A mismatch must leave scheduler snapshot/admission order/stable slots and owner state unchanged. Add a negative CPU/static fixture with an admissible wrong candidate showing zero mutation.

2. **HIGH — retry entry drops the retained exact failed full `SegmentIdentity` required by v0.8.2/v0.8.3.**
   - implementation: `canonical_segment_runtime.py` (`abort_retry`, `begin_retry`)
   - contract: v0.8.2 §2 and v0.8.3 full-identity guard.

   `abort_retry()` retains only `_retry_plan` and clears `self.identity`. `begin_retry()` then searches `scheduler.admission_order` by `(slot_id, episode_id, cursor)` projection and uses the first uncommitted match. The frozen design explicitly requires retaining the exact failed full `SegmentIdentity` and separately validating `stable_slots[slot] is retained_identity`, because same projection with different category/source_digest/segment_id/training_stream_end must not regain authority.

   **Acceptance:** retain the exact failed full identity object at retry abort, bind it alongside the exact immutable retry plan, and require object/value authority against scheduler `stable_slots`, `admission_order` and `committed_identities` before creating attempt-1 transaction. Do not reconstruct or rediscover authority by projection alone. Add wrong-metadata/same-projection negative Evidence.

3. **HIGH — `snapshot()` does not implement the frozen committed-frontier consistency guard.**
   - implementation: `canonical_segment_runtime.py` (`snapshot`)
   - contract: v0.8 snapshot §5 and inherited later snapshot rules.

   The implementation only checks `phase is IDLE` and `adapter.pending() is None`, then returns `scheduler.snapshot()` plus `adapter.committed_snapshot()`. It does not verify that each sidecar slot identity is the last committed identity for that slot and the same authority as `stable_slots[slot]`, nor that terminal slots have no sidecar record, nor that there is no admitted-but-uncommitted residue/retained retry/skip handle. Returning an unchecked pair of snapshots is not the owner-derived safe boundary frozen by the design.

   **Acceptance:** perform the full frontier validation before constructing `CanonicalRuntimeSnapshot`: no open transaction/forward/identity/retry/skip handles; no admitted-but-uncommitted slot; each sidecar record equals the scheduler's last committed/stable identity for that slot; terminal slots have no sidecar record. Any mismatch must fail closed. Add positive post-finish/terminal-discard and negative frontier-mismatch fixtures plus clone isolation.

4. **MEDIUM — runtime-owner Evidence still does not cover the submitted implementation, and directed pytest did not execute.**
   - `cosmos_framework/model/generator/mot/canonical_segment_runtime_test.py`

   The file remains the two prior fixtures that manually set `owner.phase = SKIP_READY` and private `_skipped_identity/_skipped_plan`; it does not traverse public `prepare -> abort_scaler_skip`, nor test the newly added normal commit, two-member continuation, finish-window, terminal/retry/begin-retry, snapshot frontier, single-owner guard, attempt-1/later-member scaler-skip zero-mutation or stale/substitute capability paths. Therefore contract→behavior→evidence is still missing even aside from the environment-blocked pytest run.

   **Acceptance:** replace/extend these shortcuts with public-path end-to-end CPU/static fixtures covering every supported transition and every required negative case. Then run the directed pytest suite successfully in an environment with repository dependencies available; keep `py_compile` and both diff-checks. A blocked test environment may be documented but cannot close the implementation Gate.

## Scope boundary

No closure authority is granted for this pair. This `REQUEST_CHANGES` is limited to the current CPU/static runtime-owner implementation Gate. No production model/trainer/scheduler-source change, persistent checkpoint/sidecar I/O, config/default/registry change, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 operation is authorized.
