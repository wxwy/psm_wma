# R09-B2 P3 second hardened closure review

- Review target root: `829c3318c1c7ad960919b7efa6a152564449d737`
- Implementation root: `a5cc7c6550cc92f40ede3838f70498966b0725fa`
- Evidence root: `8dbb0c7695056c0f6d5e79b9467981010952acf4`
- Submodule/Gitlink: `fe133043e4afe5f79e586af42b849c44fcf46757`
- Verdict: **APPROVE_TO_CLOSE_B2_P3_BLOCKED**

## Review conclusion

The second-round整改 is sufficient to close the **CPU/meta-only P3 attempt as an honest BLOCKED result**. It does not close the underlying optimizer-inventory blocker and does not authorize GPU.

The previous blockers are materially addressed for the current BLOCKED closure:

1. Missing assets now produce an auditable `BLOCKED` artifact instead of raising before artifact creation.
2. A backend cannot become PASS while `dcp_state.inspected` is false.
3. The verifier now separates record validity from final gate status; the committed evidence remains `status=BLOCKED`, `record_valid=true` rather than presenting a structural PASS as P3 closure.
4. Resolved-selector membership, actual optimizer membership, recurrent-vs-TTT diffs, optimizer-state eligibility, and TTT/DCP exclusion semantics are now represented in the verifier contract.
5. The actual no-CUDA run remains truthful: both real recipe paths reach fused optimizer construction and stop with `RuntimeError: No CUDA GPUs are available`; no weights/checkpoint/forward/backward/optimizer step/GPU execution is claimed.

Therefore the correct closure is: **P3 CPU/meta path is closed as BLOCKED because the actual full-recipe optimizer cannot be constructed within the approved no-CUDA execution surface.**

## Important: this is NOT GPU-only approval

`APPROVE_GPU_ONLY_P3_INVENTORY_GATE` is **not granted** by this review. A new GPU-only P3 Gate must be separately designed and reviewed before any GPU/model runtime action.

The future GPU-only Gate must also harden the following PASS-path issues before it can produce canonical inventory evidence:

### HIGH-GPU-1 — verifier policy must not come from the artifact

`tools/g0/verify_r09_b2_optimizer_inventory.py:53` currently derives `allowed` from `matched_diff.allowed_backend_specific_prefixes` stored inside the artifact. A modified artifact could broaden that list (for example to an empty-string prefix) and make unexpected recurrent/TTT differences appear allowed.

Required for a future PASS-capable gate: freeze the canonical allowed prefix in verifier code (currently `local_history_runtime.recurrent_backend.`) and separately verify that any artifact declaration exactly equals that canonical value.

### HIGH-GPU-2 — selector exclusions must be frozen/validated

`tools/g0/verify_r09_b2_optimizer_inventory.py:24` accepts artifact-provided `selector_optimizer_exclusions` and subtracts it before checking selector-to-optimizer equality. This can excuse arbitrary missing optimizer membership if the artifact is edited.

Required for a future PASS-capable gate: either require the exclusion set to be empty, or freeze an exact independently derived allowlist and verify the artifact against it.

### HIGH-GPU-3 — actual optimizer-state/DCP inspection is still required

The successful worker path in `tools/g0/collect_r09_b2_optimizer_inventory.py` currently records optimizer state as `not_materialized=true` with empty entries and deliberately records `dcp_state.inspected=false`, then returns BLOCKED. That is acceptable for this CPU/meta BLOCKED closure, but simply enabling CUDA would not by itself satisfy the approved P3 four-layer membership contract.

A future GPU-only gate must actually read the real optimizer `state` / state-dict schema and a read-only DCP-compatible persistent-key schema, map them back to stable parameter names, prove the TTT five runtime members are absent, and keep save/load/forward/backward/step disabled unless separately authorized.

## Scope ruling

This approval means only:

- `G0-R09-B2-P3-OPTIMIZER-INVENTORY` CPU/meta attempt may be marked **DONE/BLOCKED**;
- the P0 optimizer-membership blocker remains unresolved;
- B2-T remains BLOCKED;
- P4/P5 do not gain training/runtime authorization from this closure;
- no GPU, model/checkpoint/VAE load, forward/backward, optimizer/scheduler step, training, eval/inference/closed-loop, SR, multi-GPU, long training, backend freeze, Global/Agent/RL is authorized.

Next permitted action is a **new GPU-only P3 inventory Gate plan/review**, if the project chooses to resolve the blocker rather than leave B2 preflight blocked.
