# ChatGPT 独立 Runtime Owner CPU/static implementation review

Formal reviewed pair:
- root implementation SHA: `acf1cfe35844fbfc2ecdabe1f41f048061dd720f`
- child/Gitlink SHA: `d12dda51d9f0eb89310e5e785d4f485dd3e68be2`
- Gate: `G0-R09-B-TTT-V035-RUNTIME-OWNER-CPU-STATIC-IMPLEMENTATION`
- approved design authority: root `c31eecbf40f38ab0b6b4d277cd425c5b45e66744` / child `5d16b84fe17a42f128065bf36361f6b1bb93a436`, v0.8-v0.8.7
- request/bookkeeping HEAD observed: `c22838ade818fe8db2998f7edef677c713ce1ecc`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh implementation review from approved design pair `c31eecb / 5d16b84` to implementation pair `acf1cfe / d12dda5`. Root changes are Gitlink + SESSION/TODO/review bookkeeping. Child is one commit ahead and changes only three allowed files: new `canonical_segment_runtime.py`, new `canonical_segment_runtime_test.py`, and `local_memory_segment_adapter.py`. No model/trainer/scheduler-source or real-I/O/GPU surface is changed.

Request-reported execution status is treated exactly as reported: `py_compile` and diff-check PASS; directed pytest did **not** run because the environment lacks `omegaconf`, and `uv` was separately blocked by the existing `tool.uv.audit` configuration. This is not test PASS.

## Current blockers

1. **HIGH — the production owner implements only the scaler-skip subset of the approved runtime-owner state machine; the normal/terminal/retry/snapshot contract is absent.**
   - implementation: `cosmos_framework/model/generator/mot/canonical_segment_runtime.py:15-54`
   - inherited design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.md:11-104`, `...v0.8.1.md:24-55`, plus v0.8.7 refinements.

   `CanonicalSegmentRuntimeOwner` currently exposes only `admit`, `begin`, `prepare`, `abort_scaler_skip`, and `resume_skipped`. It has no normal `commit()` path at all, no `MEMBER_COMMITTED -> admit(next)` multi-member continuation, no `finish_window()`, no retry/terminal abort path, no `begin_retry()`, no snapshot/frontier API or `CanonicalRuntimeSnapshot`, and no constructor guard preventing the same scheduler/wiring authority from being bound by multiple owners. Consequently a normal prepared member cannot be committed through the owner and a GA window cannot reach its frozen normal `IDLE` boundary.

   This is not a later production-model/trainer concern: these methods and guards are the exact CPU/static owner surface authorized by the design Gate. Closing the implementation while they are absent would approve only a scaler-skip helper, not the approved runtime owner.

   **Acceptance:** implement the complete frozen owner surface within the existing whitelist: exact normal commit delegating once to the same adapter result/transaction; same-transaction multi-member continuation; all-members-only `finish_window`; exact retry/terminal abort and immutable attempt-1 retry entry; v0.8.7 scaler-skip restrictions; owner-derived snapshot with committed-frontier guards; `CanonicalRuntimeSnapshot`/owner generation as frozen; and single-owner binding protection for exact scheduler/wiring authority. All stale/substitute capability paths must fail before sidecar writes or unauthorized phase transitions.

2. **MEDIUM — the new runtime tests bypass the real skip transition and do not establish contract→behavior→evidence for the implementation Gate.**
   - `cosmos_framework/model/generator/mot/canonical_segment_runtime_test.py:18-41`

   `test_skip_resume_reuses_exact_admission_and_plan` manually writes `owner.phase = SKIP_READY` and private `_skipped_identity/_skipped_plan` fields instead of executing `prepare -> abort_scaler_skip -> exact discard -> SKIP_READY`. The second test similarly injects private state. There is no adjacent Evidence for normal commit, two-member continuation, finish-window, retry/terminal abort, snapshot frontier/clone isolation, wrong full identity, stale/substitute transaction/forward/result, later-member skip zero mutation, or attempt-1 scaler-skip zero mutation required by v0.8-v0.8.7. Directed pytest also did not execute in the submitted environment.

   **Acceptance:** replace private-state shortcut fixtures with end-to-end CPU/static owner fixtures that traverse the public frozen transitions and directly witness every supported positive/negative path, including the v0.8.7 attempt-1/later-member scaler-skip preflight. Rerun the directed pytest suite successfully in an environment with the repository dependencies available; retain `py_compile` and both child/root diff-checks. Environment blockage may be documented, but cannot count as closure Evidence.

3. **MEDIUM — `committed_snapshot()` does not enforce the frozen fp32 snapshot ABI.**
   - implementation: `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py:55-61`
   - contract: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.4.md:7-10` and v0.8 snapshot requirements.

   The helper returns `value.detach().clone()` and therefore preserves the live state's dtype. The frozen ABI requires committed snapshot state to be detached **fp32** deep-copy. There is also no new adapter test proving dtype conversion and clone isolation.

   **Acceptance:** convert every returned fast-state tensor to detached cloned fp32 without mutating live state, and add an adjacent CPU test using a non-fp32 committed state to prove snapshot dtype is fp32 and snapshot mutation cannot affect the live sidecar.

## Closed / correct portions

- Child change set remains inside the approved four-file whitelist; only three files actually changed.
- `pending()` exposes the exact pending tuple without clone/detach/reconstruction.
- `discard_pending()` requires object-identical identity/transaction/result and only clears pending.
- `abort_scaler_skip()` performs exact pending preflight before mutating the transaction and enforces attempt-0 / no-completed-members.
- `resume_skipped()` reuses the retained exact identity and exact original plan without duplicate scheduler admission or caller replacement plan.

These correct subsets do not compensate for the missing normal/retry/snapshot owner surface or missing executable Evidence.

## Scope boundary

No closure authority is granted for this implementation pair. `REQUEST_CHANGES` is limited to the current CPU/static runtime-owner Gate. No production model/trainer/packer wiring, scheduler-source change, persistent checkpoint/sidecar I/O, config/default/registry change, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1 operation is authorized.
