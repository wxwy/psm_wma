# Codex reading ACK — Evaluation V2 r2 (2026-10-28)

ACK: I have read the entire canonical Owner contract from exact V3
`9858e70b6d66e40429017ce9a752926fc7330af6`:
`docs/collab/chatgpt/requests/2026-10-28_V3_RoboCasa_EvalV2_r2_CANONICAL_LATEST_OWNER_CONTRACT.md`,
the latest canonical Inbox, and the exact r1 GPT review (dc750f8e / 746c5cf2).
This ACK is recorded BEFORE r2 prototype edits. Issue #7 API access returned
Forbidden (both GraphQL and REST); this handoff/Inbox is the permitted ACK channel,
not a claim that an Issue comment was posted.

D1: immutable scoped process fault history, explicit cleanup/retry resolution;
current/late faults block clean qualification without rewriting environment SR.
D2: recoverable Task/Episode initialization and exclusive immutable Core Commit.
D3: retry only missing Episode37, preserve all valid success AND behavioral_failure
results, including valid slots after a gap; resumed scenes need NOT match old ones.
No whole-Task replay, reset-only replay, forced per-Episode SHA seed or RNG snapshot.
D4: strict initial success admission before model/action/Local begin; bounded
already-success resampling; separate consecutive recoverable init errors, reset by
any legal precheck; fourth error skips slot, continues only safely, no auto-retry
without explicit Owner authorization. Unsafe faults require safe stop.

Superseded: r1 whole-Task restart, old fixed per-Episode seed requirement,
media/ffmpeg gating of SR, automatic retry of SKIPPED_INIT_ERROR. Environment
post-step success authority, media independence, flat Task/Episode storage,
process/results separation, new900-only namespace and immutable old431 stay frozen.

Scope: isolated candidate r2 design + CPU prototype/tests + exact new SHA/Evidence;
then STOP for GPT review. No production/Child/vendor/train edits, V3 merge,
GPU/server/DCP/Canary/real simulator or historical results access.
