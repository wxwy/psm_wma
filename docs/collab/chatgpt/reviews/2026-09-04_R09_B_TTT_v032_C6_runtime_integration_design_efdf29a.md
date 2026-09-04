# ChatGPT independent review — R09-B TTT v0.3.2 C6 runtime integration design

Date: 2026-09-04

## Formal target

- Gate: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-DESIGN`
- root design SHA: `efdf29ad64f23d0b22f0e69723c6035052861aed`
- child/Gitlink: `0e904111c189bba46105cfe79c61301f4759c796`
- request/ledger SHA observed at review start: `8fcf8cc997c292b799528d2c1a1ef94783bf4bd5`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_C6_runtime_integration_design_v0.1_2026-09-04.md`
- inherited C5A design authority: `bbe0444eaa8c08f05ca5a5eea0e331253d263592`
- inherited closed C5A implementation pair: root `38f4633e4642189838bc71d87af4e5af1e05c767` / child `0e904111c189bba46105cfe79c61301f4759c796`

## Verdict

`REQUEST_CHANGES`

This is an independent design verdict for the exact target above. Kimi/MM status is not used as approval evidence.

## Findings

### HIGH-1 — C6 does not freeze the C5A segment transaction/terminal semantics at the runtime seam

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_C6_runtime_integration_design_v0.1_2026-09-04.md:13-23,42`

**Root cause:** The C6 lifecycle is written as `admission -> Encoder -> materialize[_many] -> backward -> commit`, but it does not state that all raw rows for one segment are admitted while the phase is `COLLECT_RAW`, that `materialize[_many]` is called once for the atomic segment after collection, or that C5A's frozen `N>0` / terminal remainder rules remain authoritative. The acceptance list also drops the C5A `N=1/3/16` and terminal `r=0..N` matrix. This permits a conforming implementation to collapse the runtime to per-timestep `materialize/backward/commit` (effectively `N=1`) even though C5A froze segment-level TBPTT transactions.

**Contract violation:** C5A v0.6 freezes `COLLECT_RAW -> MATERIALIZE_PENDING -> ordinary backward -> commit`, default segment length semantics, terminal remainder handling, and no graph leakage across segments. The closed child implementation materializes the full pending time axis and commits only after a graph-bound backward.

**Acceptance:** Revise C6 to state the exact runtime phase machine and boundary conditions: collect all contiguous admitted timesteps for each owner in `COLLECT_RAW`; materialize exactly once at the full segment or terminal remainder; one ordinary outer backward must reach every materialized owner witness; then commit/detach atomically. Preserve `N=1/3/16`, terminal `r=0..N`, reset/abort/new-epoch retry, no next-segment admission while pending, and add direct runtime-adapter CPU fixtures for those cases.

### HIGH-2 — Production admission/chronology authority is unspecified, allowing C5A hostile-admission guarantees to be bypassed

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_C6_runtime_integration_design_v0.1_2026-09-04.md:13,23,38-42`

**Root cause:** C6 names stable `owner_key` / `source_identity` and says “completed-causal source admission”, but does not define the production-side capability/authority boundary after explicitly forbidding production import of `C5AOwnerSegmentCPU`. It does not freeze who issues/verifies the completed-causal capability, how `source_timestep/epoch/provenance/source bytes` are bound, where lookup-before-allocation lives, or which component owns the one authoritative pending/committed reverse index. “Reuse the same semantics in a minimal adapter” is not an executable contract and permits a second, weaker authority using caller strings/booleans.

**Contract violation:** C5A v0.6 made the registry the unique chronology authority and froze sealed admission, canonical source-byte/digest binding, hostile admission rejection, lookup-before-allocation, owner/epoch isolation, permutation equivalence, and row-mismatch rejection. Those are prerequisites, not optional implementation details.

**Acceptance:** Freeze one production adapter authority and its exact API/state ownership. Specify the trusted completed-causal source/capability producer, exact fields and byte/digest binding, lookup-before-allocation order, owner/epoch reset/abort behavior, replay semantics, and fail-before-C5 conditions. The adapter may not create a second chronology source of truth. Extend acceptance with hostile capability/source mismatch, changed-byte same identity/timestep, replay-before-allocation, cross-owner/epoch, permutation and row-mismatch fixtures through the real C6 adapter seam.

### HIGH-3 — Gate scope is internally contradictory about production wiring and checkpoint/config identity

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_C6_runtime_integration_design_v0.1_2026-09-04.md:7-9,27-30,34,38-42,46`; request entry in `docs/collab/chatgpt/CODEX_INBOX.md` for `efdf29a`

**Root cause:** The design says C6 “connects” C5A into the Cosmos Local Memory modality and explicitly allows changes to production entry files (`omni_mot_model.py`, `data_and_condition.py`, `unified_mot.py`, `cosmos3_vfm_network.py`), while the review request says approval still prohibits “Cosmos production wiring”. Separately, the design requires `K_local` to be a positive config value included in checkpoint identity while the same Gate forbids config/checkpoint schema/refreeze changes. The allowed implementation therefore cannot unambiguously satisfy all frozen statements.

**Contract violation:** Gate authorization must have one unambiguous allowed/prohibited boundary. A design approval cannot simultaneously authorize changes whose semantic purpose is runtime wiring and prohibit that wiring, nor require checkpoint/config identity changes that are outside the allowed file/scope set.

**Acceptance:** Choose and freeze one C6 boundary. If this Gate is only an isolated synthetic adapter seam, state that production files are exercised only through a disabled/test-only seam and that no active Cosmos runtime path/config/checkpoint identity is changed; defer `K_local` config/checkpoint identity to the explicitly named later config/checkpoint Gate. If this Gate is intended to activate real production wiring, remove the conflicting prohibition and separately freeze the required config/checkpoint contract before implementation. The Inbox request, design scope, allowed-file list, and acceptance matrix must say the same thing.

## Accepted / unchanged

- Formal target is docs-only; child/Gitlink remains `0e904111...`.
- K/V-only Memory Prefix direction remains aligned with C4: Local does not become a query and no Q_MEM/residual/MLP path is introduced.
- The proposed `[B,K_local,32] -> [B,K_local,2048]` boundary and non-hardcoded `K_local=1` first fixture are directionally consistent with the closed multi-slot route.
- The outer-loss/meta-gradient intent and no-grad/inference no-mutation requirement are appropriate, subject to the authority/transaction fixes above.
- No GPU/training/real-I/O authorization is granted by this review.

## Scope after this verdict

Allowed remediation is design/status/ledger only. Do not implement C6 runtime code yet. GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, config/optimizer/checkpoint refreeze, staging/P4/P5, training/evaluation/inference, B2-T and LIBERO4IN1 remain prohibited.

A remediated design is a new root design SHA and requires a fresh independent same-SHA review with child/Gitlink pinned explicitly.
