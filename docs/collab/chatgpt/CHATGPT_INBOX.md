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

- immediate prior live blob SHA: `5960d77e29973ba5e4514afa7535fcc577e35476`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root materialization/binding design REQUEST_CHANGES

Formal pair:
- root design SHA: `36b4e6bc3144a67d16d6c9684649e8939d181230`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-BINDING-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_binding_design_v0.1.md:42)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_authority_root_materialization_binding_design_36b4e6b_93a89ba.md`

Canonical review commit:
`4f2e362e3d28857ad3d8e23b9e8a00ee68c154f7`

Current blockers: `1 HIGH` (Design/ABI).

Blocker summary:
- The design freezes the direct executor-facing seven-field tuple with first key `authority_root_revision`, while the already-approved fail-closed executor accepts the exact key set whose first key is `root_revision` and dereferences that key. No reviewed serialization bridge/refreeze exists. Reconcile the ABI explicitly; do not delegate the rename to caller/request/ledger or an unfrozen future adapter.

Still not authorized: real authority-root materialization, real source selection/read/hash, collection/receipt/source-evidence mutation, publication/root audit, child/runtime modification, checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.
