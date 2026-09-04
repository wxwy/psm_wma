# ChatGPT independent review — R09-B TTT v0.3.2 C6 runtime integration design v0.2

Date: 2026-09-04

## Formal target

- Gate: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-DESIGN`
- root design SHA: `6ac74c5588a03304b590e803e6179537d5381317`
- child/Gitlink: `0e904111c189bba46105cfe79c61301f4759c796`
- request/ledger SHA observed at review start: `088fc9e95434d82fe793d2739d7b35d4ce36a140`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_C6_runtime_integration_design_v0.2_2026-09-04.md`
- previous C6 v0.1 review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_C6_runtime_integration_design_efdf29a.md`
- inherited closed C5A implementation pair: root `38f4633e4642189838bc71d87af4e5af1e05c767` / child `0e904111c189bba46105cfe79c61301f4759c796`

## Verdict

`REQUEST_CHANGES`

This is an independent design verdict for the exact target above. Kimi/MM status is not used as approval evidence.

## Previous blockers

- v0.1 HIGH-1 — segment transaction / terminal semantics: **CLOSED**. v0.2 now freezes full-segment `COLLECT_RAW -> MATERIALIZED_PENDING -> one scalar backward -> BACKWARD_OK -> atomic commit/detach`, preserves `N∈{1,3,16}` and terminal remainder cases, and forbids per-timestep N=1 degeneration.
- v0.1 HIGH-2 — chronology/admission authority unspecified: **CLOSED** for this synthetic-only Gate. v0.2 directly delegates `C5AOwnerSegmentCPU`/`AdmissionAuthority`, forbids a second chronology/reverse index, and freezes capability fields plus replay/changed-byte/cross-owner/epoch/hostile-admission coverage.
- v0.1 HIGH-3 — production wiring vs synthetic scope contradiction: **CLOSED**. v0.2 clearly limits C6 to a test-only synthetic adapter and adjacent CPU tests; production Cosmos wiring, config/checkpoint identity and GPU/training remain deferred.

## Current finding

### HIGH-1 — reset/done pending-state semantics are internally contradictory

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_C6_runtime_integration_design_v0.2_2026-09-04.md`, §2, sentence: `每次 reset/done 先 abort pending（若存在则拒绝 reset），再递增 epoch`.

**Root cause:** The sentence freezes two mutually exclusive transitions for the same pending state. “先 abort pending，再递增 epoch” authorizes automatic rollback/abort followed by reset/done, while “若存在则拒绝 reset” requires the reset transition itself to fail when pending exists. These produce different observable phase, epoch, retry and rollback behavior and therefore cannot both be the contract.

**Frozen-contract impact:** C5A chronology/owner/segment semantics are inherited rather than reimplemented, and C6 v0.2 explicitly claims direct delegation. A synthetic adapter design must therefore state one exact delegated transition rule; it cannot leave reset-vs-abort ordering to implementation choice. This is especially material because the same document also requires exact rollback and new-epoch re-admission behavior.

**Acceptance:** Replace the contradictory clause with one unambiguous state-machine rule matching the closed C5A authority. Freeze separately for `reset` and `done` if their behavior differs: (a) whether a pending segment causes rejection or is explicitly aborted first, (b) whether epoch increments on the rejected path, (c) what state remains after rejection/abort, and (d) when same owner/identity/timestep may be re-admitted with new source bytes. Add one direct synthetic adapter fixture for the chosen pending→reset/done transition and new-epoch retry.

## Accepted / unchanged

- The Gate is now coherently synthetic-only and does not authorize active Cosmos runtime changes.
- Direct delegation to the closed C5A authority is the correct architecture for this Gate; no duplicate chronology/state machine should be introduced.
- Segment-level outer loss, witness connectivity, unrelated/grad-free/partial-owner fail-closed coverage, Local-disabled parity, and `[B,K_local,32] -> [B,K_local,2048]` synthetic shape assertions are directionally consistent.
- No config/optimizer/checkpoint refreeze, real model/data/cache/checkpoint I/O, GPU/CUDA/torchrun, P4/P5, B2-T, training/evaluation/inference, or LIBERO4IN1 is authorized.

## Scope after this verdict

Allowed remediation is design/status/ledger only. Do not implement the C6 adapter yet. A corrected v0.3 design is a new formal root SHA and requires a fresh same-SHA independent review with child/Gitlink pinned explicitly.
