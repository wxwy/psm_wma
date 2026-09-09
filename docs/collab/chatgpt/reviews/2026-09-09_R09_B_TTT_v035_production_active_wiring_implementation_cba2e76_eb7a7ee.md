# ChatGPT 独立 Production Active Wiring CPU/static implementation review

Formal reviewed pair:
- root implementation SHA: `cba2e763f4f8f4557abe4d45d47f5c73fb97812a`
- child/Gitlink SHA: `eb7a7ee0a391ea56f2967c4641b37d8baea2c0dc`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- approved design pair: `721b4100624a37edbdd75bb555515b7d7e67c8e1` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- design authority: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md` plus retained v0.5/v0.4 contracts
- request/ledger commit: `ccb4b2a54b4adc3aaf91c5fe5a75fd0bf39474ef`
- latest bookkeeping HEAD observed: `ca9e4133ba28ea3a6dc110cd52dc8fe439dc6593`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh implementation review relative to the approved v0.6 design pair. Root formal changes are Gitlink + collaboration bookkeeping/review persistence. Child is exactly one commit ahead of the approved design child. The seven changed child files are all inside the approved whitelist: `production_active_wiring.py` + adjacent test, `canonical_segment_runtime.py` + adjacent test, `omni_mot_model.py`, `trainer/__init__.py`, and `trainer/active_wiring_callback_test.py`. No packer/dataset/manifest/config/optimizer-selector/checkpoint file changed.

The request reports `36 passed`, target `py_compile`, scoped F-lint, and root/child `git diff --check` PASS. These execution results are request Evidence and were not independently rerun by this reviewer. The implementation and fixtures were independently inspected against the frozen contract.

## Correctly implemented direction

- Registry-bound prepared/forward capabilities carry exact registry identity and are one-shot at the model/forward publication surface.
- The model active marker branch occurs before `_get_training_inputs()`, so it bypasses legacy `_inject_local_history/_ttt_local_memory_tokens()` creation.
- Active callback dispatch uses the approved exact-class `TTTLifecycleCallback` exclusion while preserving callback list identity/order.
- Active backward uses the transaction-owned weighted objective and one `grad_scaler.scale(objective).backward()` with no second GA division.
- Owner slow-window preflight/seal APIs were added in the now-whitelisted `canonical_segment_runtime.py`.
- Child diff stays within the approved implementation surface.

These are necessary but not sufficient for closure.

## Current blockers

1. **HIGH — active prepare failures after `owner.prepare()` are not owner-terminalized and can leave the owner in `PREPARED` with a live graph-bearing pending scan.**
   - implementation: `cosmos_framework/model/generator/mot/production_active_wiring.py::ProductionActiveWiringRegistry._prepare`
   - related owner: `canonical_segment_runtime.py::CanonicalSegmentRuntimeOwner.prepare/abort_terminal`
   - violated contract: retained v0.4/v0.5 fail-closed active capability/count contract and the closure request's explicit no-pending/no-grad-leak requirement.

   `_prepare()` first executes `forward = self.owner.prepare(segment)`. At that point the owner is `PREPARED`, `owner.forward` is live, and the adapter owns the exact pending `(identity, transaction, result)` capability. It then constructs `ActiveNativeBatchInputs(...)` and checks `len(inputs.payloads)` against the frozen planned count. Both `ActiveNativeBatchInputs.__post_init__` (for a non-Mapping/callable/misaligned payload) and the gathered-count check can raise directly. Neither path calls `owner.abort_terminal(...)`, discards the exact pending scan, clears Local slow grads, terminalizes the transaction, or clears registry authority.

   This reintroduces the same post-prepare leak class previously closed in the production-segment bridge Gate.

   `prepare_initial()` has a related pre-admission problem: it calls `owner.admit()` before `owner.begin(plan)` has verified the plan's exact first member. A malformed initial plan can therefore fail after scheduler/owner admission and leave the owner `ADMITTED` instead of rejecting with zero mutation.

   **Acceptance:** preflight every checkable plan/member/GA/identity invariant before `owner.admit`; after `owner.prepare`, route every payload-shape/type/count validation failure through exactly one owner-owned terminal disposition (compatible code: `LOCAL_MEM_IDENTITY_CONTRACT_FAILURE`) and exact pending discard. Registry authority must be cleared consistently. Add CPU/static fixtures for at least: wrong first plan member, non-Mapping active payload, and gathered-count mismatch; prove zero native forward/backward, pending `None`, terminal/suffix suppression, real Local grad clear, and no new scheduler/sidecar commit.

2. **HIGH — the approved exact active/native GA-window binding is not implemented before mutation, and the trainer can take a normal optimizer step in the middle of an open active transaction.**
   - implementation: `production_active_wiring.py::prepare_initial`; `trainer/__init__.py::arm_active_local_memory_initial/training_step`
   - violated contract: v0.5 §2 retained by v0.6.

   The approved contract requires, before any model forward or owner mutation:

   `initial_plan.ga_effective == self.config.trainer.grad_accum_iter` and actual trainer `grad_accum_iter == 0`.

   The implementation checks only `trainer_grad_accum_iter != 0 or plan.ga_effective <= 0`. `arm_active_local_memory_initial()` does not receive the actual trainer counter and hardcodes `trainer_grad_accum_iter=0`; it also never compares the plan to `self.config.trainer.grad_accum_iter`.

   Consequences are not merely cosmetic:
   - a plan shorter than the configured GA can complete the owner early and leave `SLOW_RESOLUTION_PENDING` until a later batch;
   - a plan longer than configured GA reaches the native trainer optimizer boundary with no `_psm_active_completed_window`; the current code then executes the normal `_optimizer_step(..., active_seal=None)`, allowing optimizer/scheduler mutation while the active owner remains mid-window;
   - an active initial arm can mutate owner/adapter state before a later `training_step` discovers a nonzero trainer counter mismatch.

   **Acceptance:** make the trainer's actual counter and configured GA part of the initial active preflight before `owner.admit`; reject any `plan.ga_effective != config.trainer.grad_accum_iter` or nonzero start with zero owner/adapter/scheduler mutation. At every native optimizer boundary, if an active registry/window is open, require the exact completed capability; absence/mismatch must fail before callbacks/`grad_scaler.step` rather than falling through to a normal optimizer step. Add shorter-plan, longer-plan, mid-normal-window start, active/no-marker interleave, and full exact-window fixtures.

3. **HIGH — the retained first-member-only transient retry contract is absent from the active implementation.**
   - implementation: `production_active_wiring.py::ProductionActiveWiringRegistry`; `trainer/__init__.py` active forward exception route
   - violated contract: v0.4 §3 retained through v0.5/v0.6 and v0.6 Evidence requirement preserving first-only retry/later terminal behavior.

   The active registry implements only `prepare_initial()` and `prepare_continuation()`. There is no active retry capability/path and no active source-transient tagged outcome. Any model-forward exception in the trainer is unconditionally mapped to `LOCAL_MEM_OUTER_FAILURE` via `owner.abort_terminal(...)`. Therefore the approved policy — transient retry permitted only before any successful active member at counter zero, with later-member transient becoming `LOCAL_MEM_RETRY_AFTER_MEMBER` terminal/process-fatal — cannot occur on this active path.

   Existing production-segment bridge retry tests do not close this new active surface because the active model/trainer path bypasses `run_member()`.

   **Acceptance:** add an explicit active source-failure/retry seam that reuses the owner-owned `abort_retry/begin_retry` authority without guessing arbitrary exceptions as transient. Permit it only when `completed_members==()` and trainer counter is zero; any later-member transient must terminalize as the frozen later-retry failure and must not create a suffix optimizer window. Add both allowed first-member retry and later-member terminal active-path fixtures.

4. **HIGH — post-optimizer sealed resolution remains structurally fallible despite the frozen deterministic post-step contract.**
   - implementation: `canonical_segment_runtime.py::resolve_preflighted_slow_window`; `trainer/__init__.py::_optimizer_step`
   - violated contract: v0.4 §4 retained by v0.5/v0.6.

   The design moved all fallible authority checks before `grad_scaler.step()` specifically so no stale/substitute/identity/boundary failure could occur after irreversible optimizer mutation. The implementation still performs `if sealed is not self._sealed_slow_window: raise RuntimeError(...)` inside `resolve_preflighted_slow_window()` after `grad_scaler.step()`. It also calls transaction resolution methods that can still raise if transaction state is no longer open. The new test explicitly demonstrates that `resolve_preflighted_slow_window()` is a fallible exact-seal API.

   The trainer also reads GradScaler private state with defaults that silently treat missing `found_inf` state as `found_inf=False`, which is not a fail-closed exact scaler verdict.

   **Acceptance:** make all external capability/identity/boundary rejection happen before optimizer callbacks/step. Post-step resolution must consume only owner-retained preflighted state with no new caller-supplied identity decision that can legitimately fail. The scaler-result seam must not silently interpret missing enabled-scaler state as success. Add active trainer-level success and scaler-skip fixtures plus stale/substitute/counter negatives proving zero optimizer/scheduler/owner mutation before step.

5. **MEDIUM — active closure Evidence does not cover the frozen v0.6 matrix on this new surface.**
   - current request: aggregate `36 passed`.
   - active-specific tests added in this child are substantially narrower than the frozen acceptance matrix.

   Missing or insufficient active-path Evidence includes:
   - two valid entries in one batched internal seam with S0/PAD ordering;
   - `ga_effective != config.trainer.grad_accum_iter`, mid-normal-window start, other-token and active/no-marker interleaving with zero mutation;
   - allowed first-member active retry and later-member terminal;
   - post-prepare payload/count failure cleanup;
   - active forward exception and active backward exception proving exact pending/grad cleanup;
   - trainer-level preflight stale/substitute/reconstructed/counter negatives before optimizer callbacks/step;
   - sealed success **and** scaler-skip through the active trainer optimizer path;
   - a pre-existing legacy lifecycle spy through a full active step proving zero observe/commit/abort/resolve, plus adjacent no-marker original-dispatch parity.

   The callback helper test proves exact-class filtering/order at the helper itself, but it does not establish the full active-vs-no-marker trainer lifecycle contract. The active registry/model test uses a single valid S0 consumer and does not cover the required multi-entry/PAD/GA/retry/optimizer negatives.

   **Acceptance:** after closing the production blockers, add the missing active-path CPU/static fixtures and rerun/report the exact new formal pair's targeted suites, target `py_compile`, and root/child `git diff --check`. Evidence must witness contract invariants, not only aggregate pass counts.

## Scope boundary

No closure authority is granted for this formal pair. This `REQUEST_CHANGES` is limited to the CPU/static active-wiring implementation Gate. No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested closure literal remains reserved for a corrected formal pair:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
