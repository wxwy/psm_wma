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

- immediate prior live blob SHA: `67b70ef4af017e3c1c6bdb7788852e5240193af7`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority Root Real Adapter / Execution Request Design v0.4 REQUEST_CHANGES

Formal pair:
- root design SHA: `be833f807e50a9a1d433c8fdf7f341e7ad3544f6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.4.md:11)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_real_adapter_execution_request_design_be833f8_93a89ba.md`

Canonical review commit:
`c7816b563951073a87f2d557594c3cf004667ef1`

Current blockers: `2 HIGH`.

The v0.4 remediation substantially improves both prior c413 blockers: writer-side fallible work is moved before guard unlink, primary and rollback failure fields are separated, and origin-specific rollback rows replace the generic rollback terminal. Two design inconsistencies remain:

1. **HIGH — PASS becomes visible at guard unlink before the authority side has safely accepted the returned sealed capability.** v0.3's inherited capability contract requires rejection of ordinary values, different-witness capabilities and replays. After `unlink(guard)` v0.4 says PASS is committed and rollback is forbidden, but `publish_candidate()` must still receive/determine that the returned object is the correct same-witness `EvidenceCommit`. If that post-unlink check can fail into the existing `try/except`, accepted PASS can coexist with ref rollback; if it cannot reject, the capability contract is weakened. Freeze all capability/token/witness/replay validation before unlink, or explicitly make any post-commit anomaly preserve candidate refs and never enter rollback. Add direct wrong-value/different-witness/replay tests around the commit point.
2. **HIGH — rollback reachability still disagrees with the actual production state machine.** Current `publish_candidate()` catches failures from pre-publication observation and local CAS as well, and `_rollback()` always performs fresh final observations even with no ownership witness. Thus pre-publication foreign/unreadable state and local-CAS race/ambiguity can legitimately end in `ROLLBACK_INCOMPLETE` while preserving unowned foreign/unproved refs. v0.4 declares only remote_cas/post_publication/binding_reverify/evidence_write origins valid and therefore cannot encode those real outcomes. Conversely, its post_publication row incorrectly allows remote succeeded/owned to vary although that phase is reached only after remote CAS succeeded and `remote_created=True`. Align evidence reachability exactly to production control flow and define `rollback.required` semantics explicitly.

MM exact-pair capture currently reports `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC`; Kimi was still reviewing with no final at the latest captured snapshot. These are coordination evidence only and do not supersede this independent ChatGPT verdict.

Scope reminder: remediation remains in the same design Gate. This verdict does not authorize implementation yet and does not authorize real selection/config files, candidate/ref/origin mutation, source read, collection/receipt/source-evidence/publication, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

This notice is coordination only and does not replace the exact formal pair or canonical review.