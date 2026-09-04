# ChatGPT independent review — C6 runtime integration design v0.3 @ 1cca6bb

**Gate**: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-DESIGN`  
**Formal target**: root/design `1cca6bbec2297086d7adc519a57588fa0e435b6e`; child/Gitlink `0e904111c189bba46105cfe79c61301f4759c796`  
**Observed V2 request/bookkeeping HEAD at review start**: `a4eaaab60774f17debedff29f6a938fe56bddb4d` (parent is the formal design SHA; bookkeeping only)

## Verdict

`REQUEST_CHANGES`

## Delta review

The v0.2 reset/done ambiguity is **CLOSED** by v0.3: pending reset/done is now rejected without mutation or epoch advance; abandon requires explicit `abort(owner)` followed by reset/done; no-pending done/reset are equivalent; terminal `r=0` cannot silently consume pending rows.

## New blocker

1. **HIGH — C6 freezes `source_timestep` as segment-relative, contradicting the delegated C5A owner chronology contract.**
   - Design: `docs/build/PSM-WMA_R09_B_TTT_v032_C6_runtime_integration_design_v0.2_2026-09-04.md:18` (inherited unchanged by v0.3) states `source_timestep = segment-relative integer`.
   - Delegated implementation authority: `cosmos_framework/model/generator/mot/c5a_owner_segment.py:132-135` computes the next admissible timestep from owner committed chronology (`_last_timestep + pending rows + 1`) and rejects any non-contiguous `cap.source_timestep`; commit stores the last admitted timestep, so the next non-reset segment continues at the owner-global next timestep rather than restarting from zero.
   - Root cause: C6 says it directly delegates chronology authority to closed C5A, but simultaneously freezes an incompatible timestep coordinate system. The second segment in one owner epoch would restart its segment-relative timestep and fail admission or force a duplicate chronology authority in the adapter, both violating the Gate contract.

### Acceptance criteria

- Replace `segment-relative integer` with the exact C5A-compatible owner-epoch chronology coordinate: monotonically contiguous `source_timestep` across segments within one owner epoch; reset/done starts a new epoch and permits the chronology to restart according to C5A semantics.
- Keep `segment_id` / segment-local row index separate from `source_timestep`; they must not redefine C5A chronology.
- Add synthetic adapter acceptance covering at least two consecutive non-terminal segments in the same epoch and proving the second segment continues the next owner timestep, plus reset/new-epoch restart and stale old-epoch capability rejection.

## Scope

No other v0.3 blocker found in the reviewed delta. Remediation remains design/status/ledger only. C6 implementation, production Cosmos wiring, config/optimizer/checkpoint refreeze, GPU/CUDA/torchrun, real I/O, P4/P5, B2-T, training/evaluation/inference and LIBERO4IN1 remain prohibited pending fresh same-SHA approval.
