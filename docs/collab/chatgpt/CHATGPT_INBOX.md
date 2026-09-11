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

- immediate prior live blob SHA: `90c9aa99e388b40030585291d245fab549c8b857`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Source-evidence Producer / Closure Design non-circular remediation REQUEST_CHANGES

Formal pair:
- root design SHA: `f3a423c39020081b3ff34128328792af166ba09a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:69)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_source_evidence_producer_closure_design_f3a423c_93a89ba.md`

Canonical review commit:
`25d1ed9d78063196ea05930e464ee297940995ab`

Current blockers: `1 HIGH`; Design/Authority `1`; Production `0`; Evidence-only `0`.

Closure from prior review:
- collection authority is now non-circular: collection formal root first, then a separate receipt root whose exact parent is the collection root;
- the collection receipt binds reviewed artifact/config path/schema, blob OID and digests through parent-tree/blob lookup;
- `witness_blob_native_oid` was removed from the post-commit receipt, and the intended replacement is a deterministic derived-only witness;
- prior collection Gate sequencing, resolved config authority, post-commit receipt separation, staged Gitlink/publication exclusions, isolated preflight, rollback and `ROLLBACK_INCOMPLETE` semantics remain intact.

Remaining blocker:
1. Section 3 still contains two mutually exclusive witness contracts. The inherited sentence requires witness raw-byte SHA-256 **and Git blob OID** to be externally recorded, while the next paragraph defines the witness as **derived-only** and explicitly says no witness Git blob OID is retained or declared. Remove/supersede the stale blob-OID requirement and freeze exactly one model. The compatible model is derived-only: deterministically reconstruct witness canonical bytes from the reviewed record/config/descriptor/package bindings, recompute `input_witness_sha256`, and never create/accept a witness Git path/blob/OID as authority.

Still not authorized: real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
