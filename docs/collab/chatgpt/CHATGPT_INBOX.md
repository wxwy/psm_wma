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

- immediate prior live blob SHA: `3f7ba022771cf0cbed107777c3f66801a0b186cf`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 launcher freeze design v0.1 REQUEST_CHANGES

Formal pair:
- root design SHA: `47801113f90348304a2843ff215d48240a490d7e`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- canonical review Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_launcher_freeze_design_v0.1.md:3)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_launcher_freeze_design_v01_4780111_93a89ba.md`

Canonical review commit:
`0960ee56b4a9aa9bf7d16b902b238fc6fa2a7fdc`

Current blockers: `1 HIGH Design/Authority`; Production implementation blockers: `0`; Evidence-only blockers: `0`; child/runtime blockers: `0`.

Positive disposition:
1. v1.6 one-shot execution authority is explicitly consumed after the pre-exec wrapper replay/SHA fail-close; this design does not authorize retry.
2. The design correctly proposes a root-only stdlib launcher-replay module plus direct temporary CPU/static tests, with formal Git-blob base replay rather than hand-copied wrapper bytes.
3. It requires zero pre-existing owner-FD flag, exactly one adjacent owner-FD insertion, declared outer-payload bytes/SHA verification before `os.execve`, and fail-close on drift.
4. The direct test matrix includes wrong adapter SHA, pre-existing owner flag, wrong insertion position and source-level drift, while prohibiting project clean-root/index/ref/evidence creation and source/checkpoint/data/cache access.
5. Formal root changes only docs/task records and retains Gitlink exactly at reachable child `93a89ba...`.
6. The design correctly requires later independent CPU/static implementation/close review and then a newly constructed/freshly observed exact v1.7 request; no execution authority is inherited from v1.6.

Remaining HIGH — Gate identity mismatch:
- Live `CODEX_INBOX`, SESSION/TODO and the requested positive verdict define this as dedicated Gate `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`.
- But the formal design file declares the older execution-request-instance Gate `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-INSTANCE-CONSTRUCTION-AND-REVIEW`.
- The same exact pair therefore carries two different Gate identities. Approval would be ambiguous between launcher-freeze implementation design and an execution-request-instance review.

Exact acceptance:
1. Change the formal design `**Gate**` to exactly `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`.
2. Explicitly bind the requested positive verdict to `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LAUNCHER_FREEZE_CPU_STATIC`.
3. Preserve the current root-only implementation-design scope: launcher-replay module + direct temporary CPU/static tests only; no v1.7 request construction, no Stage-1 retry/materialization, no real source/checkpoint/data/cache I/O, child/runtime/GPU/training.
4. Keep v1.6 consumed authority historical only; no revival by this design approval.

No replay-algorithm redesign is requested in this round.

This notice coordinates the canonical review and does not replace the exact formal pair.
