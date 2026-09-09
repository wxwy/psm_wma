# ChatGPT 独立 Production Active Wiring CPU/static implementation remediation review

Formal reviewed pair:
- root implementation SHA: `f24599d92f7447064c7422a43575e38cec843d48`
- child/Gitlink SHA: `acb2bf2c8b4caf5a415b3eaaffa34edf9a514323`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `cba2e763f4f8f4557abe4d45d47f5c73fb97812a` / `eb7a7ee0a391ea56f2967c4641b37d8baea2c0dc`
- approved design pair: `721b4100624a37edbdd75bb555515b7d7e67c8e1` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- design authority: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md` plus retained v0.5/v0.4 contracts
- request/bookkeeping chain observed: canonical request/correction prefixes `8654b22` / `b109764`; latest poll HEAD observed `56053c942c4e03afb2e0ac6c41e4df0437dc5524`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh remediation review relative to the previous formal implementation pair. Root formal diff is collaboration records plus Gitlink update. Child is exactly one remediation commit ahead of the prior child and changes only approved whitelist files: `canonical_segment_runtime.py` + test, `production_active_wiring.py` + test, and `trainer/__init__.py`. No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint file changed.

The request reports targeted CPU/static pytest `31 passed in 34.20s`, target `py_compile`, and root/child `git diff --check` PASS. These are request Evidence and were not independently rerun by this reviewer. Code and fixtures were independently inspected against the frozen v0.6/v0.5/v0.4 contracts and the previous ChatGPT blockers.

## Previous blocker status

1. **CLOSED — pre-admission and post-prepare fail-closed cleanup.**
   - `prepare_initial()` now rejects a mismatched attempt/first member before `owner.admit()`.
   - `_prepare()` routes payload/type/cardinality and gathered-count failures after `owner.prepare()` through `owner.abort_terminal(...)`, discarding pending state and clearing Local slow grads.

2. **CLOSED — active/native GA boundary binding.**
   - trainer initial arm now receives the actual `grad_accum_iter`, requires counter zero, and requires `plan.ga_effective == config.trainer.grad_accum_iter` before owner mutation.
   - native optimizer boundary now rejects an open incomplete active window before optimizer callbacks/step.

3. **PARTIALLY CLOSED — explicit tagged retry policy exists, but the real trainer retry path is still not executable and retry identity is not fail-closed.** See HIGH blockers 1-2.

4. **CLOSED IN SUBSTANCE — post-step external seal substitution and unknown enabled-scaler outcome.**
   - post-step owner resolution no longer accepts a caller-supplied seal object; it consumes owner-retained preflighted state.
   - enabled GradScaler path calls `unscale_()` and requires an explicit `found_inf_per_device` result before `grad_scaler.step()`, so missing/invalid state fails before irreversible optimizer mutation.

5. **NOT CLOSED — active Evidence matrix remains incomplete.** See MEDIUM blocker 4.

## Current blockers

1. **HIGH — retry member identity is not validated before backward; a wrong retry identity can execute scaled backward and then fail, leaving `PREPARED`/pending and partial gradients.**
   - implementation: `cosmos_framework/model/generator/mot/production_active_wiring.py::prepare_retry/_prepare`
   - completion: `cosmos_framework/trainer/__init__.py::_run_active_local_memory_backward`
   - owner: `canonical_segment_runtime.py::begin_retry`
   - violated contract: exact identity validation must occur before native backward; owner-owned fail-closed cleanup on identity failure.

   `owner.begin_retry(plan)` restores the owner-retained exact retry identity. However `ProductionActiveWiringRegistry.prepare_retry(identity, ...)` accepts an independent caller-supplied `identity` and never verifies that it is the retained owner identity. `_prepare()` then calls `owner.prepare(segment)` using the retained owner identity but stores the caller identity in `PreparedActiveMemberCapability`.

   `_run_active_local_memory_backward()` does not call `transaction.validate_success(...)` before `grad_scaler.scale(objective).backward()`. It calls `transaction.successful_backward(...)` only after backward; that method performs the identity validation. Therefore a mismatched retry identity can create the graph, execute backward, and only then raise `ValueError`, with no enclosing owner terminal cleanup. The owner remains `PREPARED`, the adapter still owns the pending scan, and partial Local/model gradients may remain.

   **Acceptance:** make retry identity authority exact before `owner.prepare()`/backward. Preferred: remove the independent retry identity argument and use the owner-retained identity, or require object/tuple identity equivalence immediately after `begin_retry()` and before `_prepare()`. In all active completions call `transaction.validate_success(member_index, identity, actual_n_valid)` before constructing/executing backward; any failure must route through exact owner terminal cleanup with pending discard and Local grad clear. Add a wrong-retry-identity fixture proving zero native backward, pending `None`, terminal/fail-closed state, and zero new scheduler/sidecar commit.

2. **HIGH — the first-member tagged transient retry is not integrated into the real trainer orchestration: the exact retry plan is discarded and no trainer retry arm surface exists.**
   - implementation: `trainer/__init__.py::training_step`
   - registry: `production_active_wiring.py::abort_source_transient/prepare_retry`
   - violated contract: v0.4 first-member retry is an active-path retry, not merely a registry unit helper; retry must not advance the trainer accumulation counter.

   On `ActiveSourceTransientError`, trainer calls `armed_prepared.registry.abort_source_transient(armed_prepared)`, but ignores the returned exact retained `GAWindowPlan`, clears `_psm_active_armed_prepared`, and re-raises the original exception. The surrounding training loop has no retry handler. The registry exposes `prepare_retry(...)`, but the exact plan object returned by `abort_source_transient()` is no longer available to trainer/caller, and there is no `arm_active_local_memory_retry(...)` or equivalent main-process orchestration seam.

   Consequently the code can prove `RETRY_READY` in a direct registry unit test, but the real trainer path terminates rather than executing the permitted first-member retry. Later-member terminal behavior is implemented correctly.

   **Acceptance:** retain and consume the exact owner-produced retry authority in the trainer path. Either retry the same member inside the active training-step orchestration without advancing `grad_accum_iter`, or store the exact retry plan/capability on the trainer and expose one main-process retry-arm method that consumes it once. Do not reconstruct/equality-match the plan. Add an end-to-end CPU/static trainer fixture: tagged first-member transient -> `RETRY_READY` -> exact retry re-arm -> one successful model/backward/commit at counter 0; and a later-member transient -> terminal/process-fatal with no suffix optimizer window.

3. **MEDIUM — optimizer-window preflight still does not enforce the frozen exact registry identity chain.**
   - implementation: `trainer/__init__.py::training_step` optimizer-boundary branch
   - retained design: v0.4 owner/registry sealed preflight, retained by v0.5/v0.6.

   The trainer reads `active_registry = self._psm_active_registry` and `open_registry = self._psm_active_wiring_registry`, but before owner preflight it only checks that `active_registry` is non-`None` and the counter matches. It does not require `active_registry is open_registry`, nor does it seal the exact trainer registry/completed capability/counter relation in a registry-owned optimizer capability as frozen in v0.4.

   Normal internal assignment currently sets these fields together, so this is not a normal-path functional failure. It is nevertheless an unresolved fail-closed authority gap: a stale/foreign completed-owner state with any non-`None` registry can pass to owner preflight and then mutate the current trainer optimizer.

   **Acceptance:** before callbacks/optimizer mutation require the exact bound registry chain (`active_registry is open_registry`, completed owner is `open_registry.owner`, exact current completed capability/counter/token), or implement the frozen registry-owned `SealedActiveOptimizerCapability` equivalent. Add foreign/stale registry/completed-capability negatives proving zero callback/optimizer/scheduler/owner mutation.

4. **MEDIUM — remediation Evidence still does not witness the full active trainer contract.**
   - request Evidence: targeted aggregate `31 passed` plus static checks.
   - added fixtures close several prior gaps, but the frozen acceptance matrix remains only partially covered.

   Still missing or insufficient on the exact active model/trainer surface:
   - full first-member transient through trainer exception handling and successful retry/re-arm (current retry test calls registry directly);
   - wrong retry identity rejected before backward with no pending/grad leak;
   - multi-entry batched internal seam with at least two valid consumers, S0 Local `None`, and PAD absent;
   - full GA>1 trainer window proving same registry/token continuity, active/no-marker/other-token interleaving rejection, and exactly one optimizer boundary;
   - enabled-scaler success **and** skip through the active trainer optimizer path (current new scaler fixture covers only missing-state rejection);
   - foreign/stale registry optimizer preflight negatives;
   - a full active step with a pre-existing legacy lifecycle spy proving zero observe/commit/abort/resolve, plus adjacent no-marker original-dispatch parity.

   **Acceptance:** after production blockers are fixed, add the missing active-path CPU/static fixtures and report the exact new formal pair's targeted suites, target `py_compile`, and root/child `git diff --check`. Aggregate pass count alone is not sufficient.

## Scope boundary

No closure authority is granted for this formal pair. This `REQUEST_CHANGES` is limited to the CPU/static active-wiring implementation Gate. No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested closure literal remains reserved for a corrected formal pair:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
