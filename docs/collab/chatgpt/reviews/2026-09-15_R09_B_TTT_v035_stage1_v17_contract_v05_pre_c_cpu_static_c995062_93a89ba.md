# ChatGPT Formal Review — Stage-1 v1.7 ContractV05 pre-C CPU/static

- Formal root: `c99506295fed887a87670fc80fbdaf639baf5444`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`
- Verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC`
- Blockers: `0`

## Independent verification

The formal root resolves and its tree binds `cosmos-framework` mode `160000` exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit independently resolves.

The previous C08/C15 blocker is closed. `AUTHORITY_REF` is frozen as `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`. `AuthorityAbsenceV1.identity_ok()` now requires exact target equality to that literal, exact `authority_absent` predicate, and raw length/SHA consistency. The positive fixture uses the same frozen target for both local and remote fixed authority-ref absence observations.

The direct foreign-but-self-consistent witness is adequate: both `local_authority_absence` and `remote_authority_absence` are replaced with a foreign target and independently self-consistent foreign raw/length/SHA, and `rehearse_v05()` must fail with `closure_query` before any consumer invocation. This closes the prior case where any non-empty target plus a self-hashed raw record could pass.

The consolidated C01–C15 matrix now records the controlling exact/frozen authority literals or rehearsal-sealed observation identities and points to positive and foreign-drift witnesses. The already-closed P0/P1/ReplayBinding exact pins, exact v0.5 paths, six-key environment, typed query/absence records, in-memory frozen replay-helper fixture, capability/plan sealing, canonical JSON/Markdown/patch witnesses, freshness-before-apply, exactly-once retirement, byte-exact post-write readback, and terminal no-retry behavior remain intact.

## Scope

This approval closes only the root CPU/static pre-C rehearsal/consumer Gate. It does **not** authorize v0.5 request construction or C execution, materialization, source-evidence collection/receipt closure, real consumer/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1. Any downstream authority must be obtained through its own already-defined boundary.
