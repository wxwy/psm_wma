# ChatGPT 独立 production wiring CPU/static remediation review

Formal reviewed pair:
- root implementation SHA: `aebfa551fbaa22fcbd831cc3302fee9689d9a31c`
- child/Gitlink SHA: `0b165b148d40475461e31dea1e76be3001ccfe25`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-CPU-STATIC-IMPLEMENTATION`
- frozen design authority: root `e68fd83023c6c9877f18f7c34cff13f97b9b93b7`, v0.6 inheriting v0.5/v0.4 contracts.

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh review relative to prior formal pair `6522870454f30ed38cbd76c028042188f62aee96` / `3a61114939e7724e93f1b0860ffe662c19ce3c88`. Child delta is one commit and modifies only three already-authorized paths: `production_segment_wiring.py`, `production_segment_wiring_test.py`, and `trainer_canonical_segment_wiring_test.py`. Root implementation updates only `SESSION.md`, `TODO.md`, and the Gitlink. Request/bookkeeping HEAD observed at review start: `9ffd773d70bb07e6e55003fac8129b31748424e1`; it is not the formal implementation target.

## Prior HIGH status

**CLOSED — non-S0 primary double-count implementation defect.** `cosmos_framework/model/generator/mot/production_segment_wiring.py:64-69` now computes the visible consumer scalar exactly once from non-None `forward.locals`; `all_local_tokens.sum() * 0` and Local slow-owner zero terms are graph anchors only. This restores the inherited v0.4/v0.5 spy semantics while preserving S0 graph-bearing behavior. No model/trainer production code changed, so the previously closed exact-wiring capability, disable-first selector, transaction.plan ownership, fail-closed identity/result guards, single delegated seam, and post-success commit remain unchanged.

## Current blocker

1. **MEDIUM — tests/Evidence-only: the required non-zero witness is not actually frozen by the tests.** `cosmos_framework/model/generator/mot/production_segment_wiring_test.py:90-98`; `cosmos_framework/trainer/trainer_canonical_segment_wiring_test.py:115-122`.

   The previous review acceptance explicitly required at least one **non-zero** non-S0 visible Local contribution so that the old buggy `2 * expected` behavior could not pass. The new fixtures compute `expected = sum(token.sum() for token in forward.locals if token is not None)` and assert `primary == expected`, but they never assert or deterministically guarantee `expected != 0`. The fixture obtains the visible Local from randomly initialized `LocalEvidenceEncoder` / `ContinualTTTLocalMemoryCore`; therefore a zero-sum visible Local is not structurally excluded. If `expected == 0`, both the corrected implementation and the prior double-count implementation would satisfy the asserted equality. The real marker→trainer witness has the same vacuity.

   **Acceptance:** make the two-step witness deterministic and explicitly non-zero at the scalar compared against the old duplicate term (for example, pin/seed the fixture and assert `abs(expected) > tolerance`, or otherwise construct a deterministic non-zero visible Local without bypassing the real marker path). Then assert exact-once primary and execute the actual marker→trainer backward/commit. Re-run wiring/model/canonical-trainer target suites, the declared adapter/trainer regression with a readable terminal PASS/zero-exit result, target `py_compile`, and child/root `git diff --check`.

## Evidence observed

Request reports wiring=`4 passed`, canonical trainer=`7 passed`, model marker=`3 passed`; adapter/trainer regression displayed all 18 pass points but its final summary was truncated; target `py_compile` and child/root `git diff --check` PASS. These execution claims were read from the request and were not independently executed by this reviewer.

## Scope boundary

No production-wiring closure is granted for this pair. This review remains limited to the frozen CPU/static synthetic wiring Gate and does not authorize persistent runtime-sidecar/resume, real data/cache/checkpoint I/O, config/default/registry/optimizer/dataset/manifest changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1.
