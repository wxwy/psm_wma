# ChatGPT independent review — C6 runtime integration design v0.4 @ 574d287

**Gate**: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-DESIGN`  
**Formal target**: root/design `574d28750883d9e69bd03aa39cc3640646190dfa`; child/Gitlink `0e904111c189bba46105cfe79c61301f4759c796`  
**Observed V2 request/bookkeeping HEAD at review start**: `4d5398f8a258e3895d73703a45984d38426465b8` (parent is the formal design SHA; bookkeeping only)

## Verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C6_RUNTIME_INTEGRATION_CPU`

## Delta review

The sole v0.3 HIGH blocker is **CLOSED**.

v0.4 replaces the incompatible segment-relative `source_timestep` with the exact delegated C5A-compatible owner-epoch chronology coordinate: `source_timestep` starts at 0 for a new owner epoch and remains strictly contiguous across successive segments in that epoch. `segment_id` and segment-local row index remain separate grouping/logging coordinates and cannot reset or redefine C5A chronology; the adapter is explicitly forbidden from maintaining a second chronology authority.

This now matches the delegated `C5AOwnerSegmentCPU` contract at child `0e904111...`: admission computes the next timestep from the owner's committed `_last_timestep` plus pending-row count, commit stores the last valid admitted timestep, and reset opens a new epoch/chronology. The new acceptance fixture also directly covers two consecutive non-terminal segments in one epoch, reset/new-epoch restart at timestep 0, stale old-epoch rejection, and retained hostile-source/fail-closed cases.

The v0.3 reset/done correction remains inherited unchanged: pending reset/done rejects without mutation or epoch advance; abandoning pending work requires explicit abort before reset; no-pending reset/done opens the new epoch. No new contradiction was found in the inherited v0.2/v0.3 clauses reviewed for this delta.

## Scope / authorization

This approval authorizes only the next **C6 test-only synthetic adapter + adjacent CPU tests** implementation under the frozen design, after the required same-SHA reviewer policy is satisfied.

It does **not** authorize active Cosmos runtime wiring, `omni_mot_model.py` / `data_and_condition.py` / `unified_mot.py` / `cosmos3_vfm_network.py` production-path changes, config/optimizer/checkpoint schema or identity refreeze, attention/packing changes, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1.

A new root implementation SHA and/or child Gitlink SHA requires a fresh implementation review and independent closure verdict.
