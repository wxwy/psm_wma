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

- immediate prior live blob SHA: `07d558546d2e57df8777f661fab74bc404735ed7`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Stage-1 v1.7 request-instance design v0.9 REQUEST_CHANGES

Formal pair:
- root design SHA: `de92df512e1a239e7c2fd2d8d6ea60c5fc9ca02c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-DESIGN`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_design_v0.9.md:22)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_request_instance_design_v09_de92df5_93a89ba.md`

Canonical review commit:
`1773f888410c562b8e3a34d3b66b3b10ca8307e3`

Current blockers: `1 HIGH`; Design/Authority: `1 HIGH`; Production: `0`; Evidence: `0`; child/runtime: `0`.

Blocker summary:
- v0.9 closes the prior outer-as-Git-source error and the generic future-root allowlist contradiction, but the complete canonical `ReplayBinding` authority is still not frozen/sourced by the closed P0 allowlist. The replay helper validates a supplied binding but does not provide the canonical binding constructor/value; the complete canonical tuple currently appears in the replay test object, which v0.9 does not allow P0 to read. Freeze the full binding literals or an exact immutable binding factory/object and reject all drift before replay.

Still NOT authorized:
- request construction under v0.9;
- Stage-1 materialization/execution/retry;
- launcher/materializer execution;
- source/checkpoint/manifest/data/cache/runtime I/O outside a future specifically approved construction allowlist;
- child/runtime mutation;
- GPU/CUDA/torchrun, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.
