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


## D5 reading ACK — latest Owner contract (before D5 prototype edits)

I have now fully read the updated canonical D1–D5 contract and D5 dedicated
review at exact remote V3 `b59d1faf486765271295a00ee5e20e4d239e0163`.
This supersedes the previous ACK scope, not its historical reading record.
D5 freezes actual Task order, Episode-index outer loop, concurrent same-round
Workers with a strict round barrier, authoritative success/failure skip on every
Resume and explicit Owner-pending skip. No per-Task50 batch is an implementation
of D5. Runtime design must reuse checked model servers, isolate Local sessions
and bound environment/EGL lifetimes while honestly recording scene stream changes.
Only isolated r2 design + CPU prototype changes are authorized; no production,
GPU, server, DCP, real simulator, V3 merge or historical431 access. Issue API was
Forbidden; this published handoff and Inbox are the canonical permitted ACK route.
