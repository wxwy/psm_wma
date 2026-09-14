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

- immediate prior live blob SHA: `d516029505de9386c37673b1e9c257a8a2566c85`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter CPU/static publication-race remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `831be4b99f8564bb3695e445dcdfeb1770d7e7f0`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:289)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_immutable_source_collection_real_adapter_cpu_static_831be4b_93a89ba.md`

Canonical review commit:
`57557a9c60368e54bc47dc387eaae54c2cae31ea`

Current blockers: `2 HIGH Production/Authority+Evidence`; `0 child/runtime`.

Blocking summary:
1. `AtomicFileEvidenceSink.emit()` closes the emission-owned staging write FD before deriving `staged_identity`; it then reopens the mutable `.pending` name and trusts that inode. A replacement in the close→reopen gap can therefore become the accepted staging authority. A same-canonical-bytes foreign inode (especially with a retained hardlink) can pass current published-inode/byte checks and survive as accepted evidence. The submitted staged-replacement witness injects only later, inside `os.link`, after `staged_identity` has already been captured.
2. The final request-parent continuity check occurs before `os.unlink(temporary_name, dir_fd=parent_fd)`, not immediately before successful return. Relocating/replacing the parent during that final unlink lets the relative cleanup succeed on the retained old directory and then lets `emit()` return success while the frozen destination pathname is absent and the final evidence exists only under the relocated parent. The current parent-relocation witness injects earlier, inside `os.link`, so it does not cover this remaining window.

Prior blocker disposition:
- snapshot `allow_absent=True` continuity / descriptor cleanup: CLOSED, with direct native snapshot ancestor-disappearance witness;
- link-time parent relocation + known published-foreign cleanup: materially CLOSED for the submitted timing;
- same-FD snapshot hashing, native composition/rollback/mode/type matrix: remain CLOSED;
- first visible preflight snapshot leak: now detected and rolled back; non-blocking strengthening.

Exact acceptance is detailed in the canonical review. Remediation remains limited to the approved two-file CPU/static allowlist and temporary fixtures.

Scope reminder: no real source/checkpoint/manifest/data/cache I/O, live collection/receipt/publication execution, execution request activation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
