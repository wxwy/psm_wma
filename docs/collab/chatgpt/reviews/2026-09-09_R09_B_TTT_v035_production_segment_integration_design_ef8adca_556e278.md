# ChatGPT 独立 Production Segment Integration Design v0.4 review

Formal reviewed pair:
- root design SHA: `ef8adca6082e41c98dd75cd0c341c9bc91dca454`
- child/Gitlink SHA: `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-SEGMENT-INTEGRATION-DESIGN`
- previous formal pair: `b67006c3cbd8b3be37549f1746c3cc57a0dcc26b` / `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- request/bookkeeping HEAD observed: `bd3578259e4879c51aa9d6e2b48eef1abdb566eb`

Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`

## Incremental scope

Fresh docs-only remediation review relative to v0.3. Child is unchanged. Root formal changes add the v0.4 design plus bookkeeping/review persistence. Review basis is the Codex request, v0.4, the previous ChatGPT v0.3 blocker set, and the current runtime-owner / transaction source.

## Prior blocker closure

1. **CLOSED — transaction-owned plan is now the sole callback/objective/backward authority.**

   `run_member` accepts an external `initial_plan` only for the initial `IDLE` entry, where `owner.begin(initial_plan)` establishes the exact transaction. Continuation and retained-retry entries have no plan parameter. All later execution derives `plan = transaction.plan`.

   `_run_local_memory_bridge_backward` also removes the separate plan argument and uses only `transaction.plan` after `transaction.validate_success(...)`. This eliminates the former split authority in which transaction identity/count validation could use one plan while loss scaling used another plan with different later counts, `n_window`, `ga_effective`, ordering, or chain metadata.

2. **CLOSED — normal finish now has one explicit owner-retained slow-resolution phase instead of the old immediate-IDLE boundary.**

   v0.4 explicitly supersedes the closed runtime-owner `finish_window -> IDLE` behavior for this bridge and freezes:

   `MEMBER_COMMITTED(all complete) -> finish_window(exact transaction) -> SLOW_RESOLUTION_PENDING -> exact one-shot resolve -> IDLE`.

   The owner retains the exact completed transaction plus the unique original `CompletedWindowCapability`; pending state forbids snapshot/admit/begin/admit_next/prepare/retry/skip resume. `resolve_local_memory_slow_window` accepts only the exact owner-created capability, rejects stale/substitute/reconstructed/double consumption before mutation, and only after success/skip bookkeeping clears pending authority and returns to `IDLE`.

   This is implementable against the current `LocalMemoryTransaction`: after all successful members the transaction remains open, so `slow_optimizer_step_succeeded()` is valid for a real successful slow step, while `grad_scaler_skip()` can close the transaction on a real post-window scaler skip. The design preserves the already-committed fast frontier on scaler skip and keeps actual Local `.grad` clearing explicit.

## Contract consistency

- Retained retry remains a no-re-admission `MEMBER_READY` entry inherited from v0.3.
- Pre-backward order remains exact identity/order/count validation -> current raw finite/scaling owner -> one backward -> owner-only success disposition/commit.
- Real GradScaler resolution remains outside the member backward seam at the slow-window boundary.
- Terminal/retry paths retain exactly one real Local grad clear, one transaction disposition, one exact pending discard, and zero sidecar commit.
- The new pending phase is inside the explicitly whitelisted `canonical_segment_runtime.py` surface; no child code is authorized until this design Gate approval is consumed by a separate implementation commit/review.

## Current blockers

None.

## Approval scope

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`

This approval authorizes only the v0.3/v0.4 CPU/static implementation whitelist: the production-segment bridge and tests, the explicitly scoped runtime-owner pending/capability changes and tests, and the explicitly scoped pure-backward/post-window trainer seams and adjacent tests. It does not authorize production model/packer/dataset/config/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1. Any later formal root or child SHA change requires fresh independent review.
