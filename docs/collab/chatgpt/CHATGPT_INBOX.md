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

- immediate prior live blob SHA: `39b5d82909fdd3805b14b45a3db2eac63a28f777`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static retained-staging remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `77564a85c07a6c936c52fd0b63810994a879b5fc`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:316)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_immutable_source_collection_real_adapter_cpu_static_77564a8_93a89ba.md`

Canonical review commit:
`402086ff920c3b53c935b0b1eaa41cc13b4fc685`

Current blockers: `1 HIGH Production/Authority+Evidence`; `0 child/runtime`.

Blocking summary:
1. The original staging-authority blocker is closed: `staged_identity` now comes from the retained emission-owned `O_CREAT|O_EXCL` FD and the same-byte foreign-hardlink witness covers the former close→reopen seam. However, after `.pending` cleanup the sink checks the global frozen parent pathname and then performs another final leaf `os.open(..., dir_fd=parent_fd)` / byte read. Parent relocation after that check but during the final retained-parent leaf verification can still allow normal return while the frozen request-bound destination pathname is absent. The final request-path continuity check is therefore still not the last authority validation before success.

Prior blocker disposition:
- retained staging inode/capability through publication verification: CLOSED;
- parent relocation during `.pending` cleanup: CLOSED for the submitted timing;
- snapshot/source continuity, same-FD snapshot hashing, native composition/rollback/mode/type matrix, link-time relocation handling, known foreign-final cleanup, and visible-preflight rollback: remain CLOSED.

Exact acceptance is detailed in the canonical review. Remediation remains limited to the approved two-file CPU/static implementation/test surface and temporary fixtures.

Scope reminder: no real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
