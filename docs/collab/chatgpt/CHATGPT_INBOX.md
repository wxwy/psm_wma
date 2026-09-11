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

- immediate prior live blob SHA: `bdecbb3c2601a55932ff3448bfba8bab8760b72e`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Execution Evidence exact-schema remediation REQUEST_CHANGES

Formal pair:
- root design SHA: `fc0199178afd547e706f33e38588b50356a448e9`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:10)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_design_fc01991_93a89ba.md`

Canonical review commit:
`40e41e79b37f21920561e22a9fbf35b73a40a697`

Current blockers: `2 HIGH`; Design/Authority `0`; Production `0`; Evidence-only `2`.

Closed from prior review:
- executor implementation/source-identity progression remains frozen before real source I/O;
- authority-root materialization/binding remains frozen as an independent exact two-path stage;
- the evidence remediation now has a fixed outer schema, named version, canonical JSON rules, ordered checks, source-entry tuple shape and evidence digest semantics.

Remaining blockers:
1. PASS/FAIL branch rules contradict the declared common nested exact key sets. `execution` is declared exact without `phase`/`failure_code`, then branches require those fields; `collection` is declared exact without `blob_native_oid`, while the FAIL null-record adds it. Define branch-specific exact schemas or a common exact superset with explicit nullable/value rules.
2. Early FAIL evidence cannot be encoded: `source_entries` is always required nonempty and handoff/candidate hashes are mandatory even when failure occurs at tool/environment/authority/lineage before source read. Freeze exact stage-aware null/SKIPPED semantics (or equivalent fixed checks array), allow empty source entries only before source-read, define later-stage nullability, and prohibit fabricated placeholder digests. Also freeze the remaining scalar/list/null field types.

Still not authorized: executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
