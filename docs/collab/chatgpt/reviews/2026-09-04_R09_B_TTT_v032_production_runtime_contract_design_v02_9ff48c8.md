# ChatGPT independent review — R09-B TTT v0.3.2 production runtime contract design v0.2

- Gate: `G0-R09-B-TTT-V032-PRODUCTION-RUNTIME-CONTRACT-DESIGN`
- Formal root/design SHA: `9ff48c8c1ac9db0cfa4c973b70bc7057d6907c1d`
- Child/Gitlink: `fce9918609329ad419232c707586b46d669c2d8c`
- Verdict: `REQUEST_CHANGES`

## Prior blocker closure

- v0.1 HIGH-1 (production authority has no legal implementation owner): **CLOSED**. v0.2 now freezes `runtime_authority.py::ProductionRuntimeAuthority` as the single production-safe owner and keeps C5A/C6 test-only facades, with equivalence fixtures required before production adapter implementation.

## HIGH-1 — per-segment mean changes the frozen native outer-loss weighting/scale

**Location**
- `docs/build/PSM-WMA_R09_B_TTT_v032_production_runtime_contract_design_v0.2_2026-09-04.md:25-31`
- inherited v0.1 training-loss clause requiring native vision/action target, mask, time weighting and loss scale to remain unchanged.

**Root cause**

v0.2 defines `L_segment(s) = sum_{t in I_s} L_task[t] / |I_s|` and requires one backward per segment. Summing gradients from independently normalized segment means is not, in general, equal to the native window loss `sum_t L_task[t] / N_valid_window`. Segments with different valid counts receive equal segment weight instead of equal per-valid-item weight; terminal remainders/padding make this mismatch concrete. It also scales the accumulated gradient by the number and sizes of segments.

**Frozen-contract violation**

The design simultaneously requires Cosmos native target/mask/time weighting/recipe loss scale to remain unchanged. The current per-segment denominator violates that requirement whenever valid counts differ across segments.

**Acceptance**

Freeze a normalization whose summed per-segment backward contributions are exactly equal to the native window loss. For example, use each segment numerator divided by the same native `N_valid_window`, or equivalently weight each segment mean by `|I_s| / N_valid_window`. Preserve the zero-denominator no-step rule. Add a direct CPU/static fixture with unequal segment valid counts including a terminal remainder, proving scalar-loss and gradient parity against the unsliced native window loss.

## Scope

No other blocker found in the reviewed v0.2 delta. This verdict does not authorize production runtime implementation, config/optimizer/checkpoint changes, GPU, training, evaluation, inference, P4/P5 or LIBERO4IN1.
