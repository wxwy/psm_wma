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

- immediate prior live blob SHA: `bd64f339d414d74f9bee21afc4da39411da7a19e`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Immutable Source Collection Design v0.1 REQUEST_CHANGES

Formal pair:
- root design SHA: `9b9b516132806369718361b0e1b7b54c15c0483d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_design_v0.1.md:13)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_design_9b9b516_93a89ba.md`

Canonical review commit:
`cc6ad833dd981e513796a1fe9f8ccd217b4c613f`

Current blockers: `3 HIGH`; Design/Authority `3`; Production `0`; Evidence-only `0`.

Blockers:
1. This design rewrites already-approved progression while claiming to reuse it unchanged. It sends collection/receipt closure directly to `SINGLE-GPU-SMOKE-DESIGN` and removes the separately frozen `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`, source-evidence controlled-write/record/post-commit receipt stages, publication materialization, and later read-only root Gitlink source audit. Preserve the approved sequence, or first obtain an explicit docs-only refreeze/supersession approval that enumerates and replaces every affected clause/Gate.
2. The collection artifact freezes four final identifier/digest values but no exact immutable input artifact/path/schema/raw-byte derivation chain for them. Receipt/tree lookup can prove the committed values are immutable, not that they came from the intended approved checkpoint source. Freeze the source-manifest/source-input/immutable-source evidence artifacts and deterministic hash/identifier derivation so closure recomputes the four values from reviewed bytes rather than caller/precomputed values.
3. Exact `root_gitlink_checkpoint_source_descriptor_v1` bytes are absent from the reviewed authority chain: collection/receipt bind only its SHA-256. Downstream package generation requires the exact descriptor object. Add a fixed root-owned descriptor artifact (or equivalent exact canonical-byte binding), bind path/blob/raw SHA-256 in the receipt, and require downstream reconstruction from that reviewed authority.

Positive findings:
- collection-root -> separate receipt-root is non-circular;
- receipt parent is constrained to the collection root and paths/schema/digest forms are explicit;
- canonical model config has a fixed root-owned artifact;
- preflight/live rollback/`ROLLBACK_INCOMPLETE` and staged Gitlink/publication exclusions remain fail-closed;
- formal root resolves exactly to the requested reachable child/Gitlink.

Still not authorized: real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
