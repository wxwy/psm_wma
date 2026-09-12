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

- immediate prior live blob SHA: `7b301efd80152ec062bb51ef83723a65ccd74c4a`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Execution Evidence retained rollback-snapshot remediation REQUEST_CHANGES

Formal pair:
- root design SHA: `dee42d02a3e40b5da66c8ac96a8a4d5a66066665`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:38)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_design_dee42d0_93a89ba.md`

Canonical review commit:
`67bacd7d5a32e12cb544c7ca0d780957ef39c9a7`

Current blockers: `2 HIGH`; Design/Authority `0`; Production `0`; Evidence-only `2`.

Closed from prior review:
- rollback evidence now retains canonical `before_snapshot` and `after_snapshot` objects instead of only SHA-256 strings;
- target-ref resolved revision and actual local HEAD symbolic/detached identity are now separate fields;
- index snapshot is tied to `git write-tree` on the controlled index;
- `verified=true` now requires component/key/entry/digest equality;
- push/publication violation encoding and candidate construction vs one-shot-handoff verification remain closed.

Remaining blockers:
1. The common rollback record is now exact five keys `{before_snapshot,after_snapshot,before_snapshot_sha256,after_snapshot_sha256,verified}`, but the `tool_identity` / `environment` / `authority` / `lineage` FAIL row still explicitly requires the superseded exact three-key null record `{before_snapshot_sha256:null,after_snapshot_sha256:null,verified:null}`. Under missing/extra-key rejection these early FAIL phases still have no legal canonical encoding. Replace every residual literal with the same five-key not-required null record or one named canonical definition.
2. `worktree_entries` is still not uniquely reproducible: `mode` has no frozen type/encoding/allowed values, and "超 allowlist path 均 FAIL" has no exact enumeration/normalization semantics for dirty/untracked/out-of-allowlist worktree state. Freeze one deterministic worktree derivation so a later auditor has exactly one valid entries array and `worktree_sha256` for a given approved state.

Still not authorized: executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
