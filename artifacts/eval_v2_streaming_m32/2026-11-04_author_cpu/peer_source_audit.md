# Read-only implementation-side peer audit

Reviewer: existing `/root/review_requirements` agent, requested under AGENTS.md's independent-agent rule. No file edits, project/test execution or further delegation. This is a source audit, not GPT's formal Code Gate, DS evidence or Owner promotion authorization.

Five original actionable findings were fixed and re-read closed: (1) same-Task multi-Episode fault recovery must match the missing Episode and allow safe concurrent identical resolution; (2) meter a Server from durable spawn even before READY publication; (3) terminal Server INFO/proof failure must forbid an automatic second spawn; (4) capture matching cleanup Task/attempt at the error point; (5) NVML unavailable-meter handling must not be masked by unconditional shutdown. No new reachable HIGH remained in the re-read audit.

The later Store cleanup split was separately re-read: external ownership probe outside metadata lock; immutable stream rechecked and receipt/only-that-stream release serialized under the lock. Runtime must still freeze spawn and wait all jobs before cleanup; the Store method is not itself a generic drain barrier. Strict M/B/manifest comparisons remain and identity.py has no diff.

Formal01 CPU environment/fixture follow-up reviewed as test corrections: record OSMesa environment; merge shared DEFAULTS plus explicit CPU/no-media into the legacy CpuSlotRuntime fixture, then preserve caller overrides. Production already read save_generated_video at baseline. Old assertions and production render proof remain.

Formal02 legacy Registry compatibility fix re-read: only streaming consumes owned_processes, so condition its new record-ID entry on streaming. Streaming still records immediately after durable start and before returning; no unpublished-meter blind spot is reintroduced. Legacy BridgeRegistry without id is compatible; starting/closing gates unchanged.

Remaining AST extraction fixture must inject the exact production transaction_capacity function. Permanent-ACK-loss fixture has no Owner-frozen 2s requirement; old sink already has10s, configurable bounded drain time is required. Raising only this test's server/client total window to10s is reasonable if actual ACK-loss is asserted after durable publication, while original INCOMPLETE/path/decode/hash/cleanup assertions remain. Controlled2.1s RED proves independent fixture phase coupling; it cannot establish the internal cause of the original broad-run failure, which stays INCONCLUSIVE. Transparent diagnostic passes cannot replace an exact-pair Gate.

Author later executed the targeted8PASS and controlled delayed GREEN; these counts are author evidence and were not independently executed by this reviewer. Final pair00e119cc20cabe082974bd3495474b589c4b46b6 /82fa270e8cdb76b3e1a4e94adf0c7ce2b497884e still requires the complete exact-pair CPU Gate, fresh GPT Code Gate, then DS independent acceptance.
