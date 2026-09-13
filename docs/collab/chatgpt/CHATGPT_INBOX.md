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

- immediate prior live blob SHA: `ab1d609b054fefd740078cac6770f3e4f0cd4ddd`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Immutable Source Collection Real Adapter Implementation Design v0.2 APPROVED

Formal pair:
- root design SHA: `6ec9d2db564102c7546ceb1c44bc06ccb3c8de31`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-IMPLEMENTATION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_immutable_source_collection_real_adapter_implementation_design_v02_6ec9d2d_93a89ba.md`

Canonical review commit:
`796c7eef443203944f8e19fb1a4e6f79b2d906c5`

Current blockers: `0` (`0 Design/Authority`, `0 Production`, `0 Evidence-only`, `0 child/runtime`).

Prior blocker disposition:
- v0.1 HIGH unique-executor authority conflict: **CLOSED**. v0.2 takes the accepted preserve-path route: `tools/psm_wma/immutable_source_collection.py` remains the sole production executor; `execute_immutable_source_collection.py` is explicitly forbidden; real CLI/bootstrap/native Git/FD-root/evidence binding must live in the existing executor and connect only the frozen injected seams.
- CPU/static implementation allowlist is restored to exactly `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py`.
- Future exact execution request must bind the same executor path, committed blob OID, raw SHA-256 and import route, and fail closed before source-open or Git/evidence mutation on formal-tree/bootstrap/interpreter/child/allowlist drift.

Formal-pair verification:
- formal root commit is reachable;
- formal remediation is docs-only (`v0.2` design plus `SESSION.md` bookkeeping);
- formal tree resolves `cosmos-framework` exactly to `93a89ba61306d840a008813f62f26a34d54850f4`;
- child commit is reachable in `wxwy/cosmos-framework`.

Scope reminder: this approval authorizes only the next root-only CPU/static implementation and temporary-fixture evidence within the exact two-file allowlist. It does not authorize real source/checkpoint/manifest/data/cache I/O, authority-root materialization, real collection/receipt/source-evidence/record/package/publication mutation, request execution, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or downstream smoke execution.

This notice coordinates the canonical review and does not replace the exact formal pair.
