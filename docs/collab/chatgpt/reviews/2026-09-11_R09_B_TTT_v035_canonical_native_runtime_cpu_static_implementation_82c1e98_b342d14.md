# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Runtime CPU/static Implementation closure remediation v2

- Date: 2026-09-11
- Formal root implementation SHA: `82c1e989a8ab8b1b2221772c2fbe9ba0b3638577`
- Child/Gitlink SHA: `b342d1446414d64daef04c3cb9478d6b0832d20d`
- Request/ledger commit: latest request is downstream bookkeeping and is not part of the formal pair.
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-CPU-STATIC-IMPLEMENTATION`
- Frozen design authority: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_cpu_static_implementation_design_v0.2.md` plus unchanged v0.1 requirements.
- Prior reviewed formal pair: `984b0635412c72af396c9522244f09e951ddd003 / db995ceb448541f6d7517ddbc150dbe27de513d5`
- Prior ChatGPT review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_runtime_cpu_static_implementation_984b063_db995ce.md`

## Verdict

`REQUEST_CHANGES(cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:228)`

## Current blockers

`1 HIGH` — Evidence-only. No current production/contract blocker is found on this pair.

## Prior HIGH closure

### HIGH-1 — CLOSED: retryable-source-transient authority is now typed, request-bound and one-shot

The prior pair still accepted a caller-supplied free-form `failure_kind="LOAD_DECODE_TRANSIENT"`. The current child replaces that with `CanonicalRetryableSourceTransientCapability` and a two-step adapter-owned authority:

1. `declare_retryable_source_transient(request)` mints a typed capability bound to the exact unscanned attempt-0 request;
2. `derive_suffix_recovery(..., source_transient=...)` requires the exact still-registered capability and object-identical request, consumes the capability before scheduler suffix derivation, and rejects foreign/stale authority;
3. the request remains bound to the exact plan/transaction/member, while the scheduler's committed-prefix invariant is still checked by `derive_suffix_recovery(member_index)`;
4. attempt-1 `scan()` still requires the exact request object previously minted through `consume_suffix_recovery()`, so a direct scheduler-derived/manual recovery request cannot enter scan.

Within this synthetic CPU/static Gate, this satisfies the previous acceptance that free-form taxonomy be replaced by a typed one-shot source-transient authority tied to the exact failed request/original transaction. It does not imply that any real data/cache load/decode failure path exists or is authorized.

### HIGH-2 — CLOSED: original-transition receipt is now bound to actual suffix commit evidence

The current adapter no longer allows caller-visible transaction counters alone to complete recovery. For an active suffix recovery it now tracks:

- exact adapter-minted recovery request identities;
- requests that actually crossed recovery `scan()`;
- request identities that actually completed `commit_success()`.

`complete_suffix_recovery()` requires all of the following before consuming the original success receipt:

- the exact active recovery object;
- the recovery transaction has all local members reconciled;
- committed request IDs exactly equal the full minted recovery request-ID set;
- no exact recovery request remains outstanding in pre-scan or scanned state.

`commit_success()` records a suffix request as committed only after frontier commit, scheduler prepared-reconcile consumption, and recovery-transaction reconciliation. The existing negative test also manually advances the recovery transaction and confirms completion remains rejected without adapter commit evidence. This closes the prior production/contract bypass.

### HIGH-3 — PARTIALLY CLOSED: recovery dispatcher evidence is direct, but the normal `(2,5)` witness still covers only member 0

The remediation materially closes the recovery half of the prior Evidence blocker. `test_canonical_native_dispatcher_recovery_scales_and_commits_exact_suffix_once()` now:

1. freezes one real `(2,5,3)` scheduler plan;
2. commits the prefix and derives the exact typed suffix recovery `(5,3)` with `N_window=8`, `GA_effective=2`;
3. for **both** suffix members, scans through the production adapter, attaches native preparation, binds a canonical native capability with non-zero auxiliary loss, and invokes `ImaginaireTrainer._run_canonical_native_backward()`;
4. checks exact objectives `10.625` and `8.875`, exactly two scaler `scale()` calls and exactly two `.backward()` calls total;
5. relies on the dispatcher to cross `prepare_commit -> commit_success`, then completes the one-shot original success receipt;
6. observes retained prefix frontier, slow-grad-discard disposition, exhausted scheduler transitions and no outstanding suffix request/scan authority.

That is direct contract→behavior→evidence for the non-degenerate recovery path.

However, the normal witness at `trainer_canonical_segment_wiring_test.py:228` still freezes the required non-degenerate normal plan `(2,5), N_window=7, GA_effective=2` but constructs and dispatches **only `plan.members[0]`**. It proves one exact objective / one scale / one backward for the 2-valid member and then ends with `completed_members == (0,)`. It never constructs the member-1 request, never runs its 5-valid/non-zero-auxiliary objective through `_run_canonical_native_backward()`, and never demonstrates post-backward commit / completion of the normal two-member window.

The prior formal review's exact acceptance explicitly required that **each valid normal/recovery member** in the frozen non-degenerate paths be bound to a canonical native capability and sent through the production dispatcher with exactly one scale/backward per member. The current recovery path satisfies this; the normal path does not.

## Current HIGH — Evidence-only: complete the normal `(2,5)` dispatcher witness

**Location:** `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:228` (`test_canonical_native_dispatcher_scales_and_backwards_exactly_once`).

This is not a production reopening. The inspected production path for plan-owned objective scaling and post-backward commit remains consistent with the frozen design. The missing proof is that the second normal member is actually exercised through the exact same typed dispatcher lifecycle.

**Exact acceptance condition:** extend/add a synthetic CPU/static direct witness using one exact `freeze_plan()` normal `(2,5)` window such that **both members** are processed in frozen order. For each member, build the exact canonical native capability with non-zero auxiliary loss, invoke `_run_canonical_native_backward()` with a counting scaler, assert the exact numeric `planned_n_valid/N_window * primary + auxiliary/GA_effective`, prove exactly one `scale()` and one backward for that member, and require successful post-backward commit. The witness must finish with the normal transaction/window fully reconciled and must not enter ordinary `/grad_accum_iter`, a second `/GA`, ratio shorthand, extra backward, second admission/refreeze/resample, or legacy fallback.

The existing recovery `(5,3)` dispatcher witness and the negative typed-authority / incomplete-receipt tests should remain.

## Pair / scope verification

- Formal root `82c1e989a8ab8b1b2221772c2fbe9ba0b3638577` resolves `cosmos-framework` exactly to `b342d1446414d64daef04c3cb9478d6b0832d20d`.
- Child branch `v2` points to the same `b342d1446414d64daef04c3cb9478d6b0832d20d` commit; child is reachable.
- Child delta from prior reviewed `db995ceb448541f6d7517ddbc150dbe27de513d5` changes only three files: production adapter, production adapter test, and trainer wiring test. All are inside the already approved eight-file synthetic CPU/static whitelist.
- Root delta relative to the prior formal pair is Gitlink plus collaboration/review bookkeeping; request/ledger/review-persistence SHAs are not treated as the technical target.
- Public real-runtime activation/hard-stop scope is not widened by the inspected remediation.

## Evidence / execution scope

The request reports four CPU/static suites `64 passed in 56.25s`, changed-file Ruff PASS and child/root diff-check PASS. These are **读取到的执行结果**. I did not independently rerun the project tests.

No real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, real native model/loss/backward, optimizer/scheduler stepping, runtime sidecar, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1 was executed or authorized by this review.

## Authorized next action

Evidence-only remediation within the already approved eight-file synthetic CPU/static scope to close the missing second normal-member dispatcher witness, then submit a new formal root/child pair for fresh incremental review.

Not authorized by this verdict: Gate closure, public/real runtime activation, hard-stop removal, real I/O, CUDA/GPU, real model forward/loss/backward, optimizer/scheduler stepping, checkpoint/sidecar work, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.

Any new formal root or child SHA requires a fresh incremental review.
