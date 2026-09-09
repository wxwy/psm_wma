# ChatGPT 独立 Runtime Owner CPU/static remediation v2 review

Formal reviewed pair:
- root implementation SHA: `a684202cbe389c08b4c60fc6fbd8ddd3729584ab`
- child/Gitlink SHA: `2ce1ac233dcb054b44995c724f74023f66e73b90`
- Gate: `G0-R09-B-TTT-V035-RUNTIME-OWNER-CPU-STATIC-IMPLEMENTATION`
- previous implementation pair: `6a33f7c1ed411f8d71d74ea4d29b4cc063754962` / `bdaba2729dfb343705e08fe91881eba580ad310a`
- approved design authority: `c31eecbf40f38ab0b6b4d277cd425c5b45e66744` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`, v0.8-v0.8.7

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh remediation review from `6a33f7c / bdaba27` to `a684202 / 2ce1ac2`. Child changes remain inside the approved CPU/static whitelist and touch only `canonical_segment_runtime.py` plus its test. The submitted request reports directed runtime-owner + adapter pytest=`14 passed`, target `py_compile` PASS, and child/root `git diff --check` PASS; those execution results are treated as request Evidence, not independently rerun here.

## Prior blocker status

- **CLOSED — `admit_next()` mutation ordering.** The owner now filters candidates to the frozen next plan-member projection before calling `scheduler.admit()`, and the public negative fixture proves wrong candidates leave scheduler state unchanged.
- **CLOSED — retry retains exact failed full identity.** `abort_retry()` now stores `_retry_identity = self.identity`; `begin_retry()` validates that exact retained object against plan projection, `stable_slots`, `admission_order`, and `committed_identities` before creating the attempt-1 transaction.
- **CLOSED — snapshot committed-frontier guard.** The owner now rejects open/retry/skip/admitted-uncommitted residue and checks sidecar identities against scheduler last-committed/stable authority plus terminal-slot sidecar absence.
- **CLOSED IN LARGE PART — public-path Evidence.** The runtime-owner tests now traverse public prepare/commit/finish, multi-member continuation, scaler-skip resume, retry, terminal and snapshot paths; the directed suite reportedly executes successfully.

## Current blockers

1. **HIGH — normal `begin(plan)` still accepts a reconstructed `GAWindowPlan(attempt=1)`, bypassing the frozen unique retry authority.**
   - implementation: `cosmos_framework/model/generator/mot/canonical_segment_runtime.py` (`begin`)
   - inherited contract: v0.8.2/v0.8.3 retry authority and v0.8.7 attempt-1 restrictions.

   `begin()` currently checks only owner phase, admitted identity, and `plan.members[0]` projection. It does **not** require `plan.attempt == 0`. Therefore a caller can take a freshly admitted identity and call the normal `IDLE -> ADMITTED -> begin(plan)` path with a caller-constructed `attempt=1` plan, creating `LocalMemoryTransaction(plan, scheduler)` without ever passing through `abort_retry() -> RETRY_READY -> begin_retry(exact retained suffix plan)`.

   The frozen design makes attempt-1 authority unique: the suffix plan must be the exact immutable object created by the one allowed transient recovery, and its first member must bind the retained exact failed full `SegmentIdentity`. Allowing attempt-1 through normal `begin()` defeats both requirements and permits fabricated retry state/weighting.

   **Acceptance:** normal `begin()` must fail closed unless `plan.attempt == 0` (and preserve owner/scheduler state on rejection). Attempt-1 plans must be enterable only through `begin_retry()` with the exact retained `_retry_plan` and `_retry_identity`. Add a CPU/static negative fixture that admits a fresh identity, supplies a reconstructed `attempt=1` plan with matching first-member projection, and proves zero mutation plus rejection.

2. **MEDIUM — required attempt-1/later-member scaler-skip fail-closed Evidence is still absent.**
   - implementation tests: `cosmos_framework/model/generator/mot/canonical_segment_runtime_test.py`
   - contract: v0.8.6 first-member-only skip and v0.8.7 explicit attempt-1 prepared-skip zero-mutation fixture.

   The current public-path tests cover first-member scaler-skip resume, retry, terminal, snapshot and multi-member continuation, but there is no fixture that prepares an attempt-1 retry transaction and proves `abort_scaler_skip()` rejects it with owner/transaction/scheduler/pending/sidecar zero mutation. There is likewise no later-member scaler-skip zero-mutation fixture even though v0.8.6 explicitly narrows the supported skip surface to first unresolved member only and v0.8.7 requires this regression coverage.

   Production code appears to enforce these guards (`transaction.plan.attempt != 0` or non-empty `completed_members`), so this blocker is Evidence-only.

   **Acceptance:** add public-path CPU/static negative fixtures for (a) attempt-1 prepared scaler skip and (b) later-member prepared scaler skip, comparing owner phase/handles, transaction snapshot, scheduler snapshot, adapter pending tuple and committed sidecar before/after to prove zero mutation. Rerun the same directed pytest suite successfully.

## Scope boundary

No closure authority is granted for this pair. This `REQUEST_CHANGES` is limited to the CPU/static runtime-owner implementation Gate. No production model/trainer/scheduler-source change, persistent checkpoint/sidecar I/O, config/default/registry change, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 operation is authorized.
