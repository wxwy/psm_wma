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

- immediate prior live blob SHA: `0fe012f0e7aeb99825a37fcb32ac7becbe589b2d`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root ABI remediation APPROVED

Formal pair:
- root design SHA: `31819169c9430087f5e293cd1dce169ec055b371`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-BINDING-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_MATERIALIZATION_BINDING_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_authority_root_materialization_binding_design_3181916_93a89ba.md`

Canonical review commit:
`676f674a93dc6ea51700834c34aedb8cea674bb0`

Current blockers: `0`.

Closed from prior review:
1. The direct executor-facing authority tuple now uses the exact first key `root_revision`, matching the already-approved fail-closed executor ABI.
2. The exact seven-key serialization is frozen end-to-end; aliases, dual-key payloads, caller-side rename/translation, and unfrozen adapter bridges are explicitly forbidden.

No new blocker was found in the retained canonical-bytes, formal-parent, exact two-path full-entry delta, Gitlink preservation, independent verifier, fixed expected-zero CAS, rollback/`ROLLBACK_INCOMPLETE`, or docs-only scope contracts.

Still not authorized: real authority-root materialization or authority-ref creation, real source selection/read/hash, collection/receipt/source-evidence/publication mutation, root audit, child/runtime modification, checkpoint/data/cache I/O, network access, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.
