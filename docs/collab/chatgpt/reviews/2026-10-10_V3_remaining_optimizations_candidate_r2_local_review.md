# V3 remaining optimizations r2 — local source review draft

**UNPUBLISHED DRAFT — NOT A FORMAL PAIR REVIEW / NOT DS OR RESUME AUTHORIZATION**.

Inspected baseline: Root `2d45bcbe075f27b860aaf0749370f01aabaa4c8a`, Child/Gitlink `95c82d12d6780fedf8becda18cbd36d550adaadf`.

The candidate replaces dense per-window placeholder allocation/resize/H2D with a validated one-byte shape view. It adds bounded rank-shared single-flight payload reads, actual consumer identity/task accounting, sampled fast-state/storage telemetry, explicit evaluation run identity, runtime-failure episode/action/MP4 evidence, and a callable native Local-prefix intervention probe.

Readiness verdict: **COMPONENT_TESTS_PASS / FULL_SOURCE_INTEGRATION_OPEN / FULL_GATE_OPEN**.

The 83 local tests do not import the full training repository. Shared-reader tests stub the original corpus validator and do not certify actual LeRobot/HF concurrency. The paired action-generation test uses a toy model, not Cosmos Policy. Root/Child source replacement anchors have been read at the fixed baseline, but complete replacement/rendering against the actual Git objects, whole-file AST and Ruff checks remain required.

The storage reporter explicitly handles the official `OptimizersContainer.optimizers` and never calls distributed state_dict for observation. Unknown optimizer state is unavailable, not zero. The remaining CUDA allocation is not assigned an activation/communication label. The evaluation checkpoint witness is metadata hash plus shard stats, not a full payload digest.

No new GitHub SHA exists for this draft. Publishing must be performed by the code owner after materialization, static fixes and full-project self-tests. Freeze the Child implementation commit first, then Root Gitlink, then a fresh exact-pair review. Preserve MM notes, all prior evidence, V2 and original training branches. DS must not apply this package to its working tree.
