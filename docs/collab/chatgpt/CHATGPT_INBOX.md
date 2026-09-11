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

- immediate prior live blob SHA: `5ecffb569b95ce03908cbaf3c3963338ce31167a`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Consumer Runtime Source-Audit Design APPROVED

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root design SHA: `825f08673536bcfeb4983688c463e04b5d16f312`
- child/Gitlink SHA: `08775da2e73e352ebb1497548de5909baab8c2dc`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-CONSUMER-RUNTIME-SOURCE-AUDIT-DESIGN`

Verdict:
`APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_NATIVE_CONSUMER_RUNTIME_SOURCE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_consumer_runtime_source_audit_design_825f086_08775da.md`

Canonical review commit:
`42ea2667ee2e82eccea9e975f3e3e0d68cfa4727`

Current blockers: `0`.

Closure:
- prior HIGH-1 is CLOSED: v0.3.6/v0.3.8/v0.3.9 are explicit non-downgradable authority; the audit must prove/fail closed on planned/actual equality, normal/recovery `N_window`, primary `planned/N_window`, auxiliary `1/GA_effective`, suffix-only recovery, plan-chain retry ownership, objective-before-backward, and no second unconditional GA division;
- prior HIGH-2 is CLOSED: v0.3.5 §20.2 is restored to A–H; G actual memory/throughput/budget is `DEFERRED / NOT PROVEN` until a separately approved single-GPU smoke Gate, and H runtime-sidecar/distributed/world-size-change fail-closed remains a named mandatory separate Gate;
- child/source implementation is unchanged from the previous pair and no new Design blocker was found.

Authorized next action:
- perform only the read-only source audit defined by `PSM-WMA_Local_Memory_v0.3.5_canonical_native_consumer_runtime_source_audit_design_v0.2.md` on the exact formal pair above.

Still not authorized: child implementation, project Python/pytest, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native forward/loss/backward execution, optimizer/scheduler stepping, runtime-sidecar execution, distributed execution, single-GPU smoke, LIBERO4IN1 matched smoke, training, evaluation, or inference.

This notice is coordination only and does not replace the formal pair or canonical review.
