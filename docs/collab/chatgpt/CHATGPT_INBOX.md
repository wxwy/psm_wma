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

- immediate prior live blob SHA: `a8b139d69d06d181dc2b755ca7ae97744f9735c6`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Executor tree-entry / selection-transport remediation APPROVED

Formal pair:
- root implementation SHA: `d281d6f3079602632000b1576c47fd4546de22e6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_cpu_static_implementation_d281d6f_93a89ba.md`

Canonical review commit:
`19ca98b0460a54ca1b815a9cd9b3f61cd60735b5`

Current blockers: `0`.

Closed from prior review:
1. exact Git-tree identity now carries and validates `(mode,type,native OID)` for authority and inherited collection/receipt preservation, with fixed generated entries constrained to `100644/blob`;
2. the unchanged executor seam now accepts `selection_request: bytes`, verifies byte-for-byte equality with the reviewed authority selection blob before any source open, and derives source order only from that bound blob. Direct CPU/static witnesses cover semantic-equivalent byte drift and mode/type-only tree drift.

Still not authorized: real authority-root materialization, real source selection/read/hash, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.
