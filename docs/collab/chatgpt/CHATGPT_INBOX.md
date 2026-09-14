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

- immediate prior live blob SHA: `5ca58b5d45ee991dbbf585057a53c4d01db21dd6`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static authority-race remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `a0e9d294320ad37cb127d45118b3f67107bfef7f`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:153)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_immutable_source_collection_real_adapter_cpu_static_a0e9d29_93a89ba.md`

Canonical review commit:
`41dc6be6a0f22e5f65d15ed5f6a831b60ec314bd`

Current blockers: `2 HIGH Production/Authority+Evidence`; `0 child/runtime`.

Blocking summary:
1. `NativeRootFd._open_regular()` now revalidates opened intermediate-directory identities for `open_regular()`, but its broad `FileNotFoundError` handler still treats a continuity failure as ordinary absence when `allow_absent=True`. `NativeCollectionGit.snapshot()` uses that optional path, so an ancestor renamed away after open can be encoded as authoritative `absent` instead of fail-closing; the required native snapshot ancestor-race witness is still missing.
2. `AtomicFileEvidenceSink.emit()` now verifies staged and published inode/bytes, but request-parent continuity is checked only before `os.link`; the existing parent-relocation witness still expects successful return while the frozen destination pathname disappears. Also, if `.pending` is replaced before link, post-link identity verification detects the foreign inode but exception cleanup removes only `.pending`, leaving the foreign final destination visible.

Prior blocker disposition:
- direct source `NativeRootFd.open_regular()` replacement-to-new-directory race: materially CLOSED by guard revalidation + direct native witness;
- native snapshot same-FD leaf hashing and direct native composition/rollback/mode matrix: remain CLOSED;
- staged inode/final byte verification: materially improved but publication authority/cleanup still OPEN.

Exact acceptance is detailed in the canonical review. Remediation remains limited to the approved two-file CPU/static allowlist and temporary fixtures.

Scope reminder: no real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
