# ChatGPT independent review — R09-B TTT Observability O2 CPU/static design

- Gate: `G0-R09-B-TTT-OBSERVABILITY-O2-DESIGN`
- Formal root design SHA: `8f84f3fb58b4929c2c65280bb5ea1c566b20509d`
- Formal child/Gitlink SHA: `611174b8d8a30976b11442efb833f69890e85a06`
- Requested literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_OBSERVABILITY_O2_CPU_STATIC` or `REQUEST_CHANGES`
- Verdict: `REQUEST_CHANGES`

## Scope checked

Fresh docs-only review. The `token_vs_consumer_hidden` metric is correctly deferred: no approved side-effect-free consumer-hidden tap is frozen, so O2 v0.1 must not fabricate that ratio and production wiring remains prohibited.

## Blocking findings

1. **MEDIUM — inherited telemetry contract is silently reduced/renamed.** `docs/build/PSM-WMA_Local_Memory_observability_extension_design_v0.3.md:3-5` says v0.2 telemetry reuse and the O1–O5 split remain inherited. The inherited O2 metric set in `docs/build/PSM-WMA_Local_Memory_observability_extension_design_v0.2.md:223-299` includes `local/fast/initialized_fraction`, `local/fast/segment_progress_mean`, `local/exposure/terminal_remainders`, `local/exposure/by_category/*`, `local/exposure/by_slot/*`, scheduler target/actual/deficit metrics, and the `local/txn/*` transaction namespace. O2 v0.1 `docs/build/PSM-WMA_Local_Memory_observability_O2_implementation_design_v0.1.md:69-88` omits several of these and renames others (`pad_rows`→`pad_count`, `segments_committed`→`committed_segments`, `local/txn/*`→`local/transaction/*`) without an explicit supersession/defer rule. That creates two valid-but-incompatible telemetry schemas.

   **Acceptance:** either preserve the inherited v0.2 key set/names for the O2 CPU/static producer, or explicitly supersede/defer every omitted/renamed metric in O2 v0.1, with its authoritative source and the later Gate that owns it. Consumer-hidden ratio may remain deferred as already specified. Add CPU/static acceptance that freezes the exact emitted-key schema and confirms forbidden/deferred keys are absent.

2. **MEDIUM — fast-state/update metric semantics are not uniquely frozen.** O2 v0.1 `:58-63,74-78,90` allows existing `fast_state`/`fast_update` observations and emits `state_l2_mean/max` and `update_l2_mean/max`, but it does not define accepted tensor ranks/shapes/dtypes or the reduction axes for those four L2 metrics. The only precise L2 formula in §4 is explicitly “per token” for `local_tokens`. Yet §6 requires invalid shape/dtype to fail closed and fast norm values to be exact. Two implementations can therefore satisfy the prose while producing different fast L2 values.

   **Acceptance:** freeze the admissible `fast_state` and `fast_update` tensor shapes/ranks and dtypes (or a normalization-to-canonical-shape rule), and define exactly how each fast L2 mean/max is computed, including empty/absent behavior. Add CPU fixtures for each accepted shape plus fail-closed fixtures for unsupported rank/dtype.

## Boundary status

No blocker was found in the docs-only/CPU-static boundary itself: the two-file whitelist, no registry/default/recipe/trainer/model/packer/runtime changes, no hooks/collectives/sink, no real I/O, no CUDA/GPU/torchrun/training/eval/inference, and the separate hidden-tap Gate are coherent.

This verdict authorizes no O2 implementation or production action until a new formal pair closes both design blockers. No code/tests or real execution were performed by this reviewer.
