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

- immediate prior live blob SHA: `1e04ac2a97fe782c6b23a4bb09fc4ac6be374396`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Immutable Source Collection Design authority remediation APPROVED

Formal pair:
- root design SHA: `885956cb6cddf57f04b3ed5097cf87a176779403`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_design_885956c_93a89ba.md`

Canonical review commit:
`03dc0fc60fb17eb66d54600c8281946943d039f0`

Current blockers: `0`. Design/Authority `0`; Production `0`; Evidence-only `0`.

Closure:
- the previously approved source-evidence/publication progression is preserved; collection execution design/closure, controlled write, record/post-commit receipt, publication materializer/verifier and read-only root audit remain binding before GPU smoke;
- immutable source identity now has fixed root-owned input-descriptor and manifest artifacts with canonical raw-byte derivation into `source_input_sha256`, `source_manifest_sha256` and `immutable_source_identifier`;
- the exact five-key `root_gitlink_checkpoint_source_descriptor_v1` is persisted at a fixed path and its canonical bytes/digest/blob ownership are bound by the receipt;
- the collection receipt binds all five collection artifacts by exact path/schema/raw SHA-256/blob OID and requires tree/blob lookup plus full descriptor→manifest→identifier→checkpoint-descriptor→collection recomputation;
- the non-circular collection-root -> receipt-root structure, isolated preflight, rollback/`ROLLBACK_INCOMPLETE`, and staged-set exclusions remain intact;
- formal root resolves exactly to the requested reachable child/Gitlink.

Authorized next action only: proceed to the separately reviewed docs-only `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`. That next Gate must freeze the concrete approved real-source selection/read contract before any real source bytes are read.

Still not authorized: real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
