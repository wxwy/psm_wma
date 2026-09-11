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

- immediate prior live blob SHA: `434795fe167929320a1489bb91f1551b1ab83bf0`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Production Runtime Integration Design APPROVED

Formal pair:
- root design SHA: `ee979172b8bef4709e94fe84ed4ff4e9c711e2e7`
- child/Gitlink SHA: `f49f568923555fe15efe546925cbe6cc9140170e`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-INTEGRATION-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_INTEGRATION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_production_runtime_integration_design_ee97917_f49f568.md`

Canonical review commit:
`fa94c9a4652555077ca23a1fe2fd60f01eb0d9a7`

Current blockers: `0`.

Closure:
- v0.2 restores the inherited mandatory progression exactly and does not claim a superseding contract;
- feature/config/optimizer/checkpoint refreeze remains before single-GPU smoke design/approval;
- runtime-sidecar design remains after single-GPU smoke, followed by CPU/static verification and resume smoke;
- matched-smoke and formal-training design/command approval remain separate mandatory Gates;
- stale current-root reading anchor was removed.

Authorized next action: create the next docs-only CPU/static runtime implementation design.

Still not authorized: child modification, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real forward/loss/backward, optimizer/scheduler step, sidecar write, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
