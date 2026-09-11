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

- immediate prior live blob SHA: `b62f3fd1b06acf702039050534f8c6924dcd1f42`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Immutable Source Collection Execution Design authority-root remediation APPROVED

Formal pair:
- root design SHA: `1b658bfbf7068a05dc6b409414ba2c98b7b03cc8`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_EXECUTION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_execution_design_1b658bf_93a89ba.md`

Canonical review commit:
`df64286ab413dd0f2505e78fb0262117a66aff77`

Current blockers: `0`. Design/Authority `0`; Production `0`; Evidence-only `0`.

Closure:
- the prior prose-only execution-authority record is replaced by a non-circular execution-authority root containing only the fixed selection-request and resolved-config canonical blobs;
- independent three-party review must bind the exact authority tuple `(authority_root_revision, selection_path, selection_blob_native_oid, selection_raw_sha256, config_path, config_blob_native_oid, config_raw_sha256)`;
- transported selection/config bytes must match the reviewed authority byte-for-byte before any source entry is resolved or opened;
- caller/environment/default/working-tree authority remains forbidden;
- root-directory-FD, descriptor-safe no-symlink open, same-FD double-hash and pre/post fstat stability semantics remain intact;
- downstream collection closure, source-evidence controlled write/receipt, publication materializer/verifier and read-only root audit remain separate required stages;
- formal root resolves exactly to the requested reachable child/Gitlink and child is unchanged.

Authorized next action only: proceed to the independently reviewed docs-only collection closure design / execution-authority binding step required by the frozen progression. The actual authority-root tuple must be independently bound before any real source bytes are opened.

Still not authorized: any real source selection/read/hash, collection/receipt creation, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
