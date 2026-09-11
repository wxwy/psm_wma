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

- immediate prior live blob SHA: `938d6f68fe0804dc3702bfa36dbc9cbfb2d5bf82`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Canonical Native Production Runtime CPU/static Implementation Design APPROVED

Formal pair:
- root design SHA: `106c2ad19d93d289cb33e7d1f38d9309e6614b23`
- child/Gitlink SHA: `f49f568923555fe15efe546925cbe6cc9140170e`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-PRODUCTION-RUNTIME-CPU-STATIC-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_production_runtime_cpu_static_implementation_design_106c2ad_f49f568.md`

Canonical review commit:
`36c4a443e7cb8b361525c5b46dfa3517d5b5b436`

Current blockers: `0`.

Closure:
- v0.2 cleanly separates pre-mutation disposal from post-mutation evidence retention;
- post-mutation paths explicitly forbid abort/reconstruction/automatic retry;
- six-file synthetic CPU/static scope, hard-stops, loss/window algebra, recovery lineage and progression remain binding.

Authorized next action: implement only the approved six-file synthetic CPU/static scope, then return for implementation closure review.

Still not authorized: real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native real workload, real optimizer/scheduler stepping, sidecar writes, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
