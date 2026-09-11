# ChatGPT Independent Review — R09-B TTT v0.3.5 Canonical Native Runtime CPU/static Implementation closure

- Date: 2026-09-11
- Formal root implementation SHA: `fb9bd00978c7ef3db2b16d60e8129df29f3eeac8`
- Child/Gitlink SHA: `03e2442d12e26492c44180257c61737b7ce4f611`
- Request/ledger commit: `e7cba4a87c7d44745b5804b8d62866593bec758b` (not part of the formal pair)
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-CPU-STATIC-IMPLEMENTATION`
- Frozen design authority: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_runtime_cpu_static_implementation_design_v0.2.md` plus unchanged requirements inherited from v0.1.
- Prior design approval pair: `c13eaabee8b72b277bfa2ff110e2d1a62efbac7c / c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`
- Prior ChatGPT design review: `docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_runtime_cpu_static_implementation_design_c13eaab_c0e6e55.md`

## Verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:263)`

## Current blockers

`3 HIGH` — two production/contract blockers and one Evidence-only blocker.

## HIGH-1 — suffix recovery authority is bypassable before scan

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:263-274`, with the bypass completed by `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:556-617` and the generic `scan()` request checks immediately after.

The frozen v0.2 design makes suffix recovery a single public typed authority with all of these conditions bound before scan: exact attempt-0 lineage, committed prefix, no active backward, `member_index > 0`, **declared retryable source transient**, one-shot recovery capability consumption, and fail-closed rejection of nontransient/foreign/stale/double-consume authority.

The exact child does not make that authority unique:

1. `CanonicalBatchWindowTransaction.derive_suffix_recovery(member_index)` is public and accepts no failure-kind authority. After a committed prefix it can mint `CanonicalSuffixRecovery` for any caller, regardless of whether the failure is `LOAD_DECODE_TRANSIENT` or a forbidden nontransient failure.
2. `CanonicalProductionAdapter.derive_suffix_recovery(..., failure_kind=...)` does enforce `LOAD_DECODE_TRANSIENT`, but it is only a wrapper around the public scheduler derivation.
3. The returned scheduler recovery already exposes `recovery_plan` and `recovery_transaction`. A caller can construct `CanonicalProductionSegmentRequest` objects directly from those public objects and call `adapter.scan()`; `scan()` checks plan/transaction/member consistency but does **not** require the request to originate from an exact one-shot `CanonicalProductionSuffixRecoveryCapability` consumed through `consume_suffix_recovery()`.
4. Therefore the adapter capability is not the sole object-bound gate. The `LOAD_DECODE_TRANSIENT` taxonomy and one-shot consumption can be bypassed before scan through the public scheduler recovery object.

This violates v0.2 §2's `declared failure kind == retryable source transient`, `nontransient ... failures均拒绝派生`, `recovery capability仅可消费一次`, and `foreign/stale/... mismatch 在 scan前 fail closed` contract.

**Exact acceptance condition:** the recovery path must have one unbypassable typed authority before scan. A recovery derivation/request must be object-bound to the exact retryable-source-transient authority and exact original transaction, and `scan()` (or an earlier mandatory public seam) must reject recovery requests that did not come from the exact still-valid one-shot recovery capability. Direct use of the scheduler recovery API must not be able to enter attempt-1 scan without the frozen failure taxonomy and one-shot ownership. Add a negative witness that attempts the current direct scheduler-derive/direct-request route for a nontransient failure and proves zero scan/mutation.

## HIGH-2 — the frozen one-shot original-transition reconciliation receipt is not implemented

**Location:** `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:199-229,263-291` and `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py` suffix capability/consume path.

The approved v0.2 design distinguishes two things:

- derivation closes/suppresses the original attempt-0 execution path and derives an attempt-1 suffix; and
- **after recovery success**, recovery members reconcile locally and a **one-shot original transition reconciliation receipt** closes/reconciles the original transition exactly once.

The exact child implements only the first part. `derive_suffix_recovery()` sets `slow_grads_cleared=True`, `remaining_members_suppressed=True`, and `_closed=True` immediately. `CanonicalSuffixRecovery` stores a numeric `transition_identity`, but there is no typed original-transition reconciliation receipt, no one-shot consume/resolve seam for it, and no success-path operation that records/reconciles the original transition exactly once after the recovery transaction completes. `transition_identity` is not used to enforce such a lifecycle.

Per-member recovery commit can consume the existing scheduler's remaining member transitions, but that is not the separately frozen one-shot original-transition reconciliation authority. The implementation therefore cannot prove the required distinction between (a) original-path suppression at derivation, (b) attempt-1 failure disposition, and (c) successful recovery reconciliation of the original transition exactly once.

**Exact acceptance condition:** preserve the original-path suppression at derivation, but add the frozen object-bound success reconciliation semantics: a typed receipt/capability tied to the exact original transition and exact recovery lineage, consumable exactly once only after all recovery members have successfully reconciled/committed. Attempt-1 failure must not be able to produce the success reconciliation; duplicate/foreign/stale receipt consumption must fail closed. The original transition's success disposition must be directly observable in the synthetic contract rather than inferred only from scheduler queue depletion.

## HIGH-3 — Evidence-only: mandatory recovery lifecycle and no-second-scaling witnesses are missing

**Locations:**
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler_test.py` — new suffix/objective tests;
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py` — new one-shot suffix consume test;
- inherited frozen acceptance in CPU/static design v0.1 §5 items 4/6 and v0.2 §4.

The newly added tests do prove useful pieces:

- committed prefix -> suffix derivation preserves exact original member objects;
- recovery owns `N_window=8`, `GA_effective=2` for `(5,3)`;
- normal `(2,5)` and recovery `(5,3)` use non-zero auxiliary and assert the exact numeric objective;
- adapter suffix capability is consumed once on the happy path.

But they do **not** establish the full required contract→behavior→evidence chain:

1. `test_committed_prefix_derives_one_exact_suffix_recovery()` stops after derivation; it does not execute recovery members through the production scan/backward/commit seams or prove successful original reconciliation exactly once.
2. `test_adapter_consumes_exact_committed_prefix_suffix_recovery_once()` stops after returning recovery requests; it does not scan/commit those requests and does not prove committed-prefix fast-state retention, exact partial-slow-grad discard once, or original-transition reconciliation once.
3. The unchanged integration test file contains no suffix-recovery witness, so the reported integration/trainer pass count does not itself prove the new suffix lifecycle.
4. v0.2 §4 explicitly requires a **spy** proving no ordinary trainer `/grad_accum_iter`, no second `/GA`, no ratio shorthand, and no second backward for the non-degenerate normal/recovery cases. The new tests assert the pure `CanonicalGAWindowPlan.objective()` numerically, but they do not provide that frozen spy witness through the relevant canonical native backward/dispatch seam.

This is Evidence-only: it does not by itself assert an additional production bug beyond HIGH-1/HIGH-2, but the Gate cannot close while the required direct behavioral witness is absent.

**Exact acceptance condition:** add direct synthetic CPU/static witnesses using the exact production typed seams for: committed member-0 -> retryable source transient -> exact typed suffix derivation/consumption -> each suffix request scan -> one synthetic backward per suffix member -> post-backward commit -> successful original reconciliation exactly once. The witness must prove committed-prefix fast state is retained, controlled partial slow grads are discarded exactly once, no second admission/refreeze/resample occurs, and attempt-1 failure is terminal. For both non-degenerate normal `(2,5)` and recovery `(5,3)` objectives, use spies/counters that prove there is no ordinary trainer `/grad_accum_iter`, second `/GA`, ratio shorthand, or second backward. Include negative coverage for the HIGH-1 direct-bypass/nontransient route.

## Checks that pass on this exact pair

- Root `fb9bd00978c7ef3db2b16d60e8129df29f3eeac8` resolves `cosmos-framework` exactly to `03e2442d12e26492c44180257c61737b7ce4f611`.
- Child branch `v2` points to the same `03e2442d12e26492c44180257c61737b7ce4f611` commit and the child commit is reachable.
- Child delta from the approved design baseline `c0e6e55...` changes only five files, all inside the frozen eight-file whitelist: scheduler contract/test, production adapter/test, and trainer wiring test. No dataset/collate/packer/config/checkpoint/sidecar or other out-of-scope file changed.
- The recovery plan preserves the original suffix `MicrobatchPlanMember` objects and adds `member_index_offset`, allowing local recovery request positions while retaining original member indices.
- The pure objective implementation uses recovery-local `N_window`/`GA_effective`, and the new numeric tests use the required non-equal counts and non-zero auxiliary terms.
- The test-only wiring change calls the declared test seam directly. `omni_mot_model.py` production activation logic remains unchanged and still rejects legacy Local markers on the public canonical-production route.
- Existing canonical native backward source continues to branch away from the ordinary `loss / grad_accum_iter` path and invokes one `grad_scaler.scale(objective).backward()` per invoked member lifecycle; the current problem is missing required recovery authority/evidence, not a newly observed ordinary-GA fallthrough in this exact diff.

## Evidence / execution scope

The closure request reports the following execution results: scheduler/adapter targeted pytest `26 passed in 16.19s`; canonical integration/trainer pytest `35 passed in 34.81s`; changed-file Ruff PASS; eight-file `py_compile`; child/root `git diff --check` PASS; and four pre-existing import-order findings in unchanged `omni_mot_model.py` / `trainer/__init__.py`.

These are **读取到的执行结果**. I did not independently rerun project Python/tests, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, native model/loss/backward execution, optimizer/scheduler step, sidecar, training, evaluation, inference, or LIBERO4IN1. Static source/Evidence inspection is sufficient to identify the blockers above and does not authorize any deferred runtime activity.

## Authorized next action

Remediate this same CPU/static implementation Gate only within the already approved eight-file synthetic CPU/static scope, unless a separate Design Gate is required to change authority beyond that whitelist. Submit a new formal root/child pair for fresh review.

Not authorized by this verdict: closure of the implementation Gate, public/real native runtime activation, hard-stop removal, real data/cache/checkpoint I/O, CUDA/GPU, `torchrun`, real model forward/loss/backward, real optimizer/scheduler stepping, checkpoint/sidecar work, training, evaluation, inference, distributed execution, matched smoke, or LIBERO4IN1.

Any new formal root or child SHA requires a fresh incremental review.