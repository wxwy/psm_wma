# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `2a0e31829b7ba97eafc823bc646e9fcbd2d771b3`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Feature / Config / Optimizer / Checkpoint CPU/static evidence closure v3 APPROVED

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `87bdb26ebe860cf48c1ec61a54ea6a1d474f74cf`
- child/Gitlink SHA: `410dd00258443c175f72f4ffd87e7cf4f9f25653`
- Gate: `G0-R09-B-TTT-V035-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-CPU-STATIC-IMPLEMENTATION`

Verdict:
`APPROVE_TO_CLOSE_R09_B_TTT_V035_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_feature_config_optimizer_checkpoint_cpu_static_implementation_87bdb26_410dd00.md`

Canonical review commit:
`85d0ee90989809518aa44b3ff45b94752f0cc807`

Current blockers: `0`.

Closure:
- the prior pair's only remaining HIGH was Evidence-only;
- the pending-commit witness now attempts restore after `scan -> mark_backward_started -> prepare_commit` and before commit/abort, proves slow-state zero mutation, then successfully uses the same typed capability in `commit_success()`, proving it remained live across the restore boundary;
- the recovery-lineage witness uses a fresh adapter/scheduler and passes the real `CanonicalSuffixRecovery` from `derive_suffix_recovery()` through restore admission, so no suffix pending collection masks the explicit recovery-authority rejection;
- all previously accepted optimizer reorder/duplicate/missing, native-forward, retry, suffix capability/request, build-net registration, round-trip/late-defect, scan/frozen/frontier/open-transaction, config/inventory/runtime-key and public-hard-stop evidence remains unchanged;
- no production code changed in this remediation and no new production/contract blocker was found.

Authorized next action:
- close only this exact six-file synthetic CPU/static Feature / Config / Optimizer / Checkpoint implementation Gate and proceed only to a separately frozen/approved next Gate.

Still not authorized: real checkpoint/filesystem/DCP/remote I/O, checkpoint backend wiring, public runtime/hard-stop removal, real native forward/loss/backward, real optimizer/scheduler stepping, CUDA/GPU, `torchrun`, runtime sidecar/mid-episode resume, training, evaluation, inference, distributed execution, matched smoke or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.

---

## CODEX NOTICE — Canonical Segment Production ABI CPU/static Implementation REQUEST_CHANGES

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `b0df0572dfb28b8ec3fb82fe2ca09ca533251d50`
- child/Gitlink SHA: `f6a660f73043c0fe0c6ba4230c1b6a68f4120cfd`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:665)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_segment_production_abi_cpu_static_implementation_b0df057_f6a660f.md`

Canonical review commit:
`63f1ac2c02f849d97e1e713ee2eba2f539ca21be`

Current blockers: `3 HIGH` (`2 production + 1 Evidence-only`).

Required remediation summary:
- bind every canonical pre-scan request to the scheduler's exact `freeze_plan()` result, exact next frozen member transition and current live `before` frontier; reconstructed/manual/stale/reordered requests must fail before frontier/core scan;
- make first-member attempt-1 scan consume the exact typed retry capability authority; direct pre-consume retry-request scan, copied/foreign request, stale scheduler after mint, duplicate scan and second/post-backward retry must fail before scan without a second freeze/admission;
- add direct CPU/static Evidence for production-registered encoder/core -> production adapter -> actual scan -> backward gradients on the same registered slow Parameters, plus terminal-success frontier retirement/all-four fp32 fast-state postconditions.

The `f6a660f` fixture owner-path migration itself is correct under the later approved `local_memory_runtime.evidence_encoder/ttt_core` refreeze. The later Native Forward/Loss v0.4 post-backward commit ordering is also explicitly honored and is not a blocker here.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, runtime sidecar, real optimizer/scheduler execution, training, evaluation, inference, distributed execution or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.

---

## CODEX NOTICE — Canonical Segment Production ABI CPU/static remediation still REQUEST_CHANGES

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root implementation SHA: `74baed85688c84aa42e9eb3fb00077665267b588`
- child/Gitlink SHA: `b1a138b79bdc2d4dc40b978ea34094512a07d378`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-CPU-STATIC-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:330)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_segment_production_abi_cpu_static_implementation_74baed8_b1a138b.md`

Canonical review commit:
`68ce1651430ae749c113730ee98bae4f5225a947`

Current blockers: `2 HIGH`, both Evidence-only. Production blockers: `0`.

Closure / remaining work:
- prior scheduler exact-admission production blocker is CLOSED in source;
- prior first-member attempt-1 capability/staleness production blocker is CLOSED in source;
- terminal-success frontier retirement Evidence is CLOSED;
- registered-owner scan/backward witness is still assembled with `SimpleNamespace`, so it does not prove production registration -> exact adapter -> scan/backward -> same registered Parameter gradients;
- scheduler/retry remediation tests cover reconstructed-plan and pre-consume retry, but do not yet provide the complete direct causal negative matrix frozen by the prior review, including stale/foreign/reordered authority cases and a core-scan-not-entered witness.

Required remediation:
- compose the real production static registration/build-net authority with adapter lookup, admitted scan, backward and exact registered Parameter gradient assertions;
- add the missing scheduler-admission/retry negative witnesses using real typed/public authority and an instrumented core-scan seam/counter, without private-state authority fabrication.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real forward/backward, optimizer/scheduler step, training, evaluation, inference, runtime sidecar, mid-episode resume, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
