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

- immediate prior live blob SHA: `f2fb37e5fb872909e9717af29979057d2f097991`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Executor implementation seam remediation REQUEST_CHANGES

Formal pair:
- root design SHA: `ed824b2e06c27328f6639aba6b5c06e1de6bee73`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_executor_implementation_design_v0.1.md:8)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_implementation_design_ed824b2_93a89ba.md`

Canonical review commit:
`b23681f077ea3df31d9e11c7855df666fe66641d`

Current blockers: `1 HIGH`; Design/Authority `1`; Implementation `0`; Production `0`; Evidence-only `0`.

Closed from prior review:
- concrete executor/test path/blob/raw-SHA binding is now delayed until the implementation files exist in the CPU/static implementation formal root/closure;
- request/ledger/handoff commits are explicitly forbidden from replacing that implementation formal pair;
- one unchanged production dependency-injection seam now spans CPU/static synthetic fixtures and later approved real Git/FD/evidence-sink dependencies, so switching to real execution does not require changing the reviewed executor source.

Remaining blocker:
1. The design still groups `interpreter` with executor/test `path/Git blob/raw SHA` as values bound "from committed tree". Git tree objects can bind file path/blob/raw bytes but cannot establish the actual Python interpreter identity. Freeze a separate exact interpreter-identity derivation and authority source from the controlled runtime environment, and state the reviewed binding stage. CPU/static closure may record its test interpreter witness, while later real execution must independently satisfy the same rule under controlled execution approval. No caller/default interpreter may become authority, and interpreter drift must still fail before source open.

Still not authorized: executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
