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

- immediate prior live blob SHA: `937e5524af4112f5c11504152273a46fc86b5a85`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Feature / Config / Optimizer / Checkpoint Refreeze Design v0.3 APPROVED

Formal pair:
- root design SHA: `5ede9ac264518ccdbca1cdbc24f4e0694b6cf85a`
- child/Gitlink SHA: `f49f568923555fe15efe546925cbe6cc9140170e`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_REFREEZE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_feature_config_optimizer_checkpoint_refreeze_design_5ede9ac_f49f568.md`

Canonical review commit:
`a83679cde8d27f09d71dcaef49518d66d7adbf5a`

Current blockers: `0`. Production blockers: `0`. Evidence blockers: `0`.

Closure:
- the prior sole HIGH is closed: v0.3 freezes the exact progress relation as pristine-before-first-step;
- `payload.iteration == 0`, canonical optimizer state is exactly empty, and scheduler state must exactly match the pristine state of the approved exact-validated scheduler identity;
- constructor-created scheduler progress fields are compared as full canonical state, not guessed zero values;
- nonzero iteration/state/step, scheduler progress drift, one-sided optimizer/scheduler presence, or identity drift reject before any live mutation;
- any real optimizer/scheduler progress or resume semantics require a future independently approved checkpoint/runtime Gate.

Authorized next stage: create/review the next docs-only CPU/static implementation design under the composite v0.1 + v0.2 + v0.3 refreeze contract.

Still not authorized: child implementation, real checkpoint/data I/O, DCP, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler stepping, sidecar/resume, single-GPU smoke, matched smoke, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
