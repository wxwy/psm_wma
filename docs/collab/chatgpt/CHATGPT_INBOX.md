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

- immediate prior live blob SHA: `f5ff367e44799d5f9b368b09d9c2028220961355`
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
