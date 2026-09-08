# ChatGPT independent review — Local Memory v0.3.5 Production Wiring / Runtime Sidecar design v0.1

**Date:** 2026-09-08  
**Verdict:** `REQUEST_CHANGES`

Formal reviewed pair:
- root design SHA: `f3d74c01de0626bf667ee0943e4158374e92d26b`
- child/Gitlink SHA: `d05f14e7195ee5efc37f9d9955923d51fd4e4b25`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- requested implementation literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC`

Fresh design review against repository truth. Latest V2 request/bookkeeping commit is not the formal target. The prerequisite v0.5 CPU/static production-integration Gate for `90e34f420c5138fd1337fe3a3af646f73c7f672c / d05f14e7195ee5efc37f9d9955923d51fd4e4b25` is formally CLOSED: its ChatGPT closure outcome is present in canonical Inbox, so there is no prerequisite-process blocker.

The source audit direction is correct: current child `omni_mot_model.py` still routes `local_ttt_enabled` through the legacy per-sample `_ttt_local_memory_tokens()` / `TTTLifecycle.process_sample()` path, while `ImaginaireTrainer.training_step()` still performs the native scalar `loss / grad_accum_iter` backward. The isolated v0.5 adapter/transaction seam is therefore not yet production-wired.

## Current blockers

### 1. HIGH — this document requests implementation authority while explicitly deferring implementation-critical ABI and exact whitelist to a future design

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:11`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:20-30`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:50-59`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:71-77`

**Root cause:** §3 says “下一份实施设计必须精确冻结” the production bridge layers, and the table names only generic targets such as “新的相邻 production bridge”, “一个显式新 segment-only branch”, “显式 plan-aware backward branch”, and “新的 in-memory production coordinator”. §5 then explicitly leaves unresolved the native consumer payload/batch ABI and local-token injection point, provenance/plan construction, trainer callback/DDP/GradScaler/loss ABI and auxiliary-loss ownership, and model selector versus legacy `TTTLifecycle`. These are implementation-defining interfaces and authority boundaries, not coding details. Yet §7 requests the literal `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_WIRING_CPU_STATIC`, which would authorize code before those interfaces and exact symbols are frozen.

This conflicts with the project's implementation-Gate discipline: implementation authority must bind an exact repository surface and a complete executable contract. The current v0.1 is a useful source-audit / design-framework document, but it is not yet an implementation-ready design.

**Acceptance:** produce a new docs-only formal root that either:
1. completes the source audit and becomes the actual implementation design, freezing every allowed path and exact new/existing symbol plus signatures/types/shapes and ownership for segment source/packer, model bridge, trainer bridge and in-memory coordinator; or
2. explicitly downgrades this Gate to a design-only/source-audit approval whose literal grants no child-code implementation authority, followed by a separately reviewed implementation design.

For an implementation-ready version, at minimum freeze: exact production bridge file/class/function names; exact `omni_mot_model.py` hook/function and payload/local-token injection ABI; exact trainer entry/seam and primary/aux loss ABI; exact provenance-to-`SegmentIdentity`/`GAWindowPlan` construction owner; exact coordinator lifetime/reset/terminal API; exact adjacent test files; and state that all unlisted production symbols are unchanged/uninvoked.

### 2. HIGH — the new segment production path has no frozen selector/supersession rule relative to the existing `local_ttt_enabled -> _ttt_local_memory_tokens() -> TTLifecycle` authority

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:15`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:27`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:57-59`
- `cosmos_framework/model/generator/omni_mot_model.py:1031-1115`

**Root cause:** repository truth already assigns `local_ttt_enabled=True` to the legacy `_ttt_local_memory_tokens()` path, which lazily constructs `TTTLifecycle` and advances per sample. The design correctly says that old helper cannot be reused for the new segment path, but it does not freeze how the new branch becomes reachable, which authority wins, or when the old lifecycle must be unconstructed/uninvoked. §5.4 explicitly leaves that selector unresolved while §3 prohibits config/default expansion. Without an exact rule, an implementation can either create a second concurrent chronology authority, silently replace existing `local_ttt_enabled` semantics, or invent an unapproved selector/config.

**Violated contract:** canonical Local Memory requires a single chronology/commit authority and forbids duplicate production routes. Disabled parity also requires the disable owner and routing semantics to be uniquely frozen before implementation.

**Acceptance:** freeze the exact branch predicate and precedence in the next formal design. It must state, with exact function/symbol ownership, whether the canonical segment path supersedes or coexists with the legacy path; under the canonical segment path the legacy `_ttt_local_memory_tokens` / `_ttt_lifecycle` / `TTTLifecycle.process_sample()` route must be explicitly uncalled/unconstructed unless a separately named compatibility mode is approved; `local_ttt_enabled=False` must preserve the exact legacy-disabled route. If a new config/default field is required to select the path, follow this document's own fail-closed rule and open a new design that explicitly authorizes that config surface.

### 3. MEDIUM — plan-aware primary-loss reduction is not uniquely frozen

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:28`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:41-43`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:54-56`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.1.md:66`
- `cosmos_framework/trainer/__init__.py:480-508`

**Root cause:** §3 correctly states the canonical primary scale as `N_valid_micro / N_valid_window`, which assumes a microbatch primary **mean**. But §6.2 states the synthetic GA result as `sum_i loss_i / N_valid_window` without defining whether each `loss_i` is a per-consumer sum, a microbatch mean, or the native scalar returned by Cosmos. §5.1/§5.3 simultaneously leaves the native output loss reduction and auxiliary-loss ownership unresolved. Current trainer repository truth receives one scalar `loss` from `model_ddp.training_step()` and divides it by fixed `grad_accum_iter`, so the exact conversion from native reduction to canonical weighted objective is the core numerical contract of this Gate.

**Acceptance:** freeze one exact loss ABI before implementation. Define `primary_consumer_mean_i` (or a per-consumer sum, but not both ambiguously), `N_valid_i`, `N_valid_window`, `GA_effective`, auxiliary-loss presence/absence and owner, raw-native finite predicate, and the exact aggregate objective. If retaining the already-closed canonical contract, state explicitly:
`L_i = (N_valid_i / N_valid_window) * primary_consumer_mean_i + auxiliary_loss_i / GA_effective`, with no second `/grad_accum_iter`, and make the full-batch/native-equivalence fixture test that exact formula.

## Non-blocking confirmations

- The prerequisite v0.5 CPU/static adapter/trainer contract is formally closed for `90e34f4 / d05f14e`.
- The source-gap diagnosis is correct: current production model uses per-sample legacy `TTTLifecycle`, and current native trainer owns fixed-GA loss scaling.
- The proposed high-level order `plan/admit -> SegmentBatch -> adapter.scan -> gather -> native forward -> plan-aware backward -> successful_backward -> adapter.commit` is directionally consistent with the closed canonical contract.
- Durable runtime-sidecar persistence/resume, real data/cache/checkpoint I/O, config/default changes, multi-rank, GPU/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain correctly outside this Gate.

No production-wiring implementation authority is granted by this verdict. A remediated docs-only design forms a new formal root and requires fresh independent review against the same child unless the child itself changes.