# ChatGPT 独立 Canonical Segment Production ABI Implementation Design v0.2 Review

Formal reviewed pair:
- root design SHA: `82574180f08fdee2682dd8699269e3198e7f3240`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-IMPLEMENTATION-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.2.md`
- previous formal review: `0b5cee1938adde3e1970edfbfba74e91274eaf43 / 3a078f28f3d107bb633c932271f86498f7c427f7`, verdict `REQUEST_CHANGES`, canonical review `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_abi_implementation_design_0b5cee1_3a078f2.md`.
- direct engineering authority: closed P0 source-ABI audit `395dadff0b17ed6206887e372718bb166aa63b40 / 3a078f28f3d107bb633c932271f86498f7c427f7`.
- request/ledger/poll/session commits after the formal root are bookkeeping only and do not replace the formal pair.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.2.md:35)`

## Incremental result

v0.2 materially improves v0.1. The pre-scan/post-scan/gather ABI is no longer circular; the adapter is the named scan owner; `NativeConsumerBatch.from_segment(...)` is the sole gather/count source; a per-slot detached fast-state frontier is introduced; the commit path is typed and scheduler-preflighted; and an explicit CPU/static GradScaler/real-optimizer hard stop is now present. These changes close most of the prior findings. Four issues remain before P2 can be authorized.

### CLOSED — prior HIGH-1 core circular ABI / missing typed scan result

The v0.1 caller-supplied gathered payload/prefix/count fields are removed from the pre-scan request. v0.2 explicitly names `CanonicalProductionAdapter` as scan owner, keeps the scan in the same autograd graph, returns typed `local_tokens/local_present/candidate_state_out`, and derives the native gathered batch only through `NativeConsumerBatch.from_segment(...)`. A dedicated per-slot fast-state frontier is also defined.

### CLOSED — prior HIGH-2 basic transaction/scheduler commit ownership

v0.2 replaces the arbitrary commit callable with an object-bound one-shot capability, binds scheduler/plan/transaction/member identities, requires `transaction.mark_backward_started(member_index)` immediately before backward, and adds a scheduler-side non-mutating reconcile preflight. This is sufficient for the normal attempt-0 path provided the implementation keeps the described exclusive-owner/no-late-validation discipline.

### NOT CLOSED — prior HIGH-3 activation still permits implicit legacy fallback

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.2.md:115-125`
- Root cause: `canonical_expected` is defined as `config.local_ttt_enabled and data_batch contains canonical-production mode declaration`. Therefore `local_ttt_enabled=True` plus *no* mode declaration makes `canonical_expected=False`; the truth-table row `false / absent / absent -> ordinary path` then allows `_get_training_inputs()`.
- Source conflict: current child requires `local_ttt_enabled=True -> local_history_enabled=True && local_history_backend='ttt_fast_weight'`; the ordinary `_prepare_training_data()` calls `_inject_local_history()`, and `_inject_local_history()` calls the superseded `_ttt_local_memory_tokens()` when `local_ttt_enabled=True` and history fields are present. Thus the old row-wise lifecycle can still be reached exactly through the supposed No-Local row.
- Exact acceptance:
  1. Define the true ordinary/No-canonical case so that `local_ttt_enabled=False` is required for the untouched ordinary path, unless a separately reviewed explicit legacy mode exists.
  2. For this Gate, `local_ttt_enabled=True` must require one exact canonical-production mode declaration plus one exact `CanonicalProductionSegmentRequest`; missing/malformed/foreign mode or request must fail before `_get_training_inputs()` regardless of whether a declaration key is absent.
  3. Simultaneous legacy/canonical/active markers must fail before forward.
  4. CPU/static evidence must include `local_ttt_enabled=True + no mode declaration` and prove `_inject_local_history()` / `_ttt_local_memory_tokens()` zero-call.

### HIGH-1 — exact registered canonical encoder/core slow-parameter binding is not frozen

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.2.md:35-46`
- Root cause: the design says the adapter calls an existing `LocalEvidenceEncoder(CANONICAL_EVIDENCE_FEATURE_CONFIG)` plus `ContinualTTTLocalMemoryCore`, but it never identifies the exact registered module objects or how they are created before model parallelization/optimizer ownership.
- Source conflict: current `OmniMoTModel.build_net()` registers the TTT core as `net.local_history_runtime.recurrent_backend` when `local_ttt_enabled=True`, but constructs `net.local_history_runtime.encoder` as `LocalEvidenceEncoder(...)` with the default `LEGACY_EVIDENCE_FEATURE_CONFIG`. `encode_segment()` rejects any encoder whose feature config is not canonical. Creating a second adapter-local encoder after `build_net()` would also leave trainable encoder parameters outside the already-registered/parallelized network unless explicitly bound.
- Exact acceptance:
  1. Freeze the exact production objects: for canonical TTT configuration, the encoder used by the adapter must be a model-registered `LocalEvidenceEncoder(..., feature_config=CANONICAL_EVIDENCE_FEATURE_CONFIG)` created in the existing `OmniMoTModel.build_net()` path before parallelization; the core must be the exact registered `ContinualTTTLocalMemoryCore` already owned by the network.
  2. Freeze the exact object lookup/binding path (for example, exact `net.local_history_runtime.encoder` and `.recurrent_backend`) and require the adapter to reject foreign/reconstructed module instances.
  3. The adapter itself must not introduce independent trainable copies of encoder/core parameters outside the registered network.
  4. CPU/static evidence must prove object identity and that the canonical scan produces gradients on the exact registered encoder/core slow parameters, while state/dt/age modules are not registered for the canonical encoder.

### HIGH-2 — first-member retry lineage contradicts the exact `freeze_plan()` object rule

- Severity: HIGH
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.2.md:91-98,142`
- Root cause: v0.2 requires `plan is scheduler.freeze_plan(...) result`, but later retains the existing attempt-1 policy. Current `CanonicalBatchWindowTransaction.retry_first_member_pre_backward()` creates a *new* attempt-1 plan via `replace(self.plan, attempt=1, ...)`; that retry plan is not object-identical to the scheduler's original `freeze_plan()` result.
- Contract impact: the retry path cannot satisfy both the one-shot retry requirement and the exact plan identity rule. Re-freezing would duplicate scheduler transitions/admission; accepting the retry plan without a frozen lineage would weaken the object-authority contract.
- Exact acceptance:
  1. Split attempt-0 and attempt-1 admission rules explicitly. Attempt-0 must bind the exact scheduler-frozen plan. Attempt-1 must be accepted only through a typed retry capability minted from the exact attempt-0 scheduler/plan/transaction before backward.
  2. The retry capability must bind the exact retry plan returned by `retry_first_member_pre_backward()`, preserve the same member objects, denominator, GA, plan-chain and frozen scheduler transitions, and create the exact replacement transaction without a second `freeze_plan()` or new admission.
  3. Scheduler reconcile must still consume the originally frozen exact member transition only once after successful retry.
  4. Evidence must cover attempt-1 success, no duplicate scheduler transition/admission, no second retry, and stale/foreign retry capability rejection before scan/backward.

### MEDIUM-1 — CPU/static fast-state frontier does not freeze the required fp32 dtype

- Severity: MEDIUM
- Location: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.2.md:76-83`
- Root cause: the frontier specifies detached `ContinualTTTFastState` and cloning current learned `W_bar_0`, but does not freeze runtime state/storage dtype to fp32.
- Source/contract conflict: v0.3.5 requires runtime `W_fast` and inner fast-MLP compute in fp32. Current `ContinualTTTLocalMemoryCore.initial_state()` defaults `dtype` to the slow `w0` parameter dtype; `OmniMoTModel.build_net()` later casts the network to the configured model dtype. Therefore a default clone is not sufficient to guarantee fp32 state.
- Exact acceptance:
  1. Freeze fresh state creation as a differentiable fp32 clone/cast of the exact registered `W_bar_0` parameters.
  2. Freeze continuation storage and every committed candidate state as detached fp32; mixed fresh/continuation batched state must preserve per-row provenance without cross-slot aliasing.
  3. CPU/static evidence must assert all four `ContinualTTTFastState` tensors are fp32 across fresh scan, continuation, commit and terminal retirement, while gradients from fresh rows still reach the registered `W_bar_0` slow parameters.

### CLOSED — prior MEDIUM-1 unsupported GradScaler path

v0.2 now explicitly forbids enabled GradScaler/real canonical optimizer execution in P2 and requires terminal+clear+suppress with zero canonical state mutation before that boundary. Real Option-B remains correctly deferred to P3.

## Verified non-blocking parts

- formal child/Gitlink resolves exactly to `3a078f28f3d107bb633c932271f86498f7c427f7`; this pair is docs-only;
- consumer vs auxiliary loss split and exactly-once canonical GA scaling remain correct;
- S0 is counted with prefix absent; PAD produces no native item; stream-major gather remains exact;
- `NativeConsumerBatch.from_segment(...)` is correctly retained as the only gathered-count authority;
- the new scheduler preflight/typed one-shot commit direction is acceptable for the normal attempt-0 path;
- `local_evidence.py`, `local_memory_segment.py`, `packers.py`, dataset/dataloader/manifest/cache/config/optimizer/checkpoint, real I/O, GPU, runtime sidecar and training remain outside P2.

Current blockers: **3 HIGH, 1 MEDIUM**.

No P2 implementation authority is granted. Authorized next action is docs-only remediation of this P1 design on a new formal root SHA, keeping the exact child SHA explicit if unchanged. No child implementation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training, evaluation or inference is authorized.