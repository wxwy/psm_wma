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

- immediate prior live blob SHA: `949d55575cd83c5e31cf65b698c2b675df6d187c`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Executor CPU/static three-fix remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `08afbed4e1843c23a1cc3542f0184a1898c1772c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:599)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_cpu_static_implementation_08afbed_93a89ba.md`

Canonical review commit:
`291b0c873db0c8fa9923b9194835a5e12276a44b`

Current blockers: `2 HIGH`; Design/Authority `2`; Implementation `0` beyond those authority-seam defects; Evidence-only `0`.

Closed from prior review:
- authority full-tree handling now validates an exact two-fixed-path delta over the reviewed parent while preserving inherited paths, and the late post-check reuses that rule;
- the EvidenceSink interface now requires atomic no-visible/no-persistent-new-record semantics on exception, with partial-write and after-write CPU/static witnesses;
- unavailable or invalid post-rollback snapshots now surface a dedicated non-authoritative `ROLLBACK_INCOMPLETE` diagnostic carrying the primary phase rather than being reclassified as ordinary phase failure.

Remaining blockers:
1. `GitTransaction.tree_entries()` exposes only `path -> OID`; exact tree-delta verification therefore cannot detect Git mode/type drift with unchanged object IDs. Bind and compare exact tree-entry identity (at minimum path + mode/type + OID, or canonical raw tree entry) for authority and the inherited collection/receipt delta checks.
2. The frozen execution contract requires the caller selection-request transport bytes to be byte-for-byte equal to the reviewed authority selection blob before source open. The current seam accepts only a parsed `paths` mapping and checks path-set equality, so transport-byte/canonical drift cannot be witnessed. Move exact transport-byte verification into the same unchanged executor seam, or remove caller selection-request transport under a separately reviewed invocation contract; do not delegate this authority check to an unbound future adapter.

Still not authorized: authority-root materialization, real source selection/read/hash, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
