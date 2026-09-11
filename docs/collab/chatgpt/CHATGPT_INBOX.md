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

- immediate prior live blob SHA: `4691e476c0c7286c0d6447650907d99d7e72e9e1`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Execution Evidence branch-typing remediation REQUEST_CHANGES

Formal pair:
- root design SHA: `c8e05cff42b1a6d4a3a599d2c02f8cdbf648c43c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:27)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_design_c8e05cf_93a89ba.md`

Canonical review commit:
`8c8648aefc7a237156c92084f7b6bba1d85e610f`

Current blockers: `1 HIGH`; Design/Authority `0`; Production `0`; Evidence-only `1`.

Closed / positive:
- PASS and FAIL execution records now have separate exact key sets; the prior branch-key contradiction is closed;
- PASS source entries remain nonempty, while FAIL before source-read may use an empty array;
- unreached FAIL SHA/revision/blob/tree/boolean/ref/path fields now have explicit nullability, and placeholder digest fabrication remains forbidden;
- exact collection/receipt null-record schemas remain correct;
- executor implementation/source-identity progression and authority-root materialization/binding remain closed;
- formal root resolves exactly to the requested reachable child/Gitlink.

Remaining blocker:
1. Stage-aware nullability is not yet deterministically machine-verifiable because `phase` / `failure_code` are only arbitrary nonempty stable-identifier strings. Freeze an exact finite phase vocabulary tied to the fixed check order, with deterministic per-phase reached/failed/skipped semantics and exact rules for partial failures inside a stage. In particular, define legal evidence for source-read failure after a prefix of entries and candidate-derivation failure after only a subset of digests exists, without fabricated values. An equivalent fixed checks array with exact PASS/FAIL/SKIPPED records is acceptable if nullability derives deterministically from it.

Still not authorized: executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
