# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer Implementation Design v0.5

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`  
**Formal root:** `17901f65d9f09772a98921cd28ffbb05d82d3725`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.5.md`  
**Previous same-Gate formal pair:** `7a678c28d4c9b47ffe6e9e9df0659b843fc49f81 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Verdict:** `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC`

## 1. Repository-truth lock

- Latest `origin/V2` at review start is request/ledger HEAD `59ec45bded2b41593f5369191814b650a85e67b1`; it declares the exact formal pair above and is not itself the formal target.
- The formal root tree stores `cosmos-framework` exactly at Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The child commit is reachable/readable and unchanged from the previous same-Gate review.
- Incremental compare `7a678c2... -> 17901f6...` is root-docs only for this technical remediation. The only new technical artifact is implementation design v0.5; intervening review/Inbox/request persistence does not replace formal authority.
- No project code, tests, real I/O, CUDA/GPU, training, evaluation or inference was executed in this Design review.

## 2. Previous blocker lifecycle

### CLOSED — carrier raw-row storage ABI is now singular

The previous v0.4 review left one HIGH because the design simultaneously retained the v0.1 typed-carrier contract (`raw_rows[B][T]`) while concretely describing a flat row-major `logical_raw_rows[B*T]` field. That left two incompatible storage ABIs for the same carrier.

v0.5 closes that blocker exactly by making one explicit choice:

- retain the v0.1 nested `raw_rows[B][T]` representation as the sole raw-row storage authority;
- define `row_model_samples[B][T]` with the same exact outer `B` / inner `T` shape;
- keep PAD as `None` in both nested fields;
- permit `flat=b*T+t` only as a transient immutable traversal/index derivation (`expected.logical_indexes`), never as a carrier field or second source of truth;
- derive `model_data_batch` only through deterministic gather from the exact nested source using the expected traversal;
- require CPU/static fixtures to reject flat-carrier input and verify outer/inner width, PAD, derived flat order and foreign nested source rejection pre-scan.

This is exactly the nested-ABI closure option requested by the prior review. The storage representation is now unique and implementation-visible.

## 3. Inherited contracts remain coherent

No new conflict is introduced by the v0.5 remediation. The following previously reviewed contracts remain in force and are mutually consistent with the nested carrier choice:

1. **Pre-scan expected authority:** derive expected stream-major valid identities/count only from the exact frozen request/member/`SegmentBatch`, chronology/provenance and nested logical raw source. Do not use an actual scan result or Local prefix pre-scan.
2. **Post-scan actual equality:** only after `adapter.scan(request)` compare actual `result.gathered.identities` / `item_count` to the already-validated expected traversal.
3. **Failure disposition:** actual mismatch, post-scan helper/materialization exceptions and the intentional pre-packer hard-stop all dispose the exact pending scan via identity-bound exact-once `abort_scan(request,result)` without commit/frontier/scheduler/transaction mutation.
4. **Local neutrality:** canonical `model_data_batch` rejects ordinary `local_memory` / foreign Local/history/legacy marker input before scan; `get_data_and_condition()` is followed by Local-neutral assertions; exactly one later adaptation maps only actual `result.gathered.local_prefixes` into `SequencePlan.has_local_memory` plus dense Local tokens.
5. **S0/PAD/order/count:** nested logical carrier preserves explicit PAD positions; expected traversal performs stream-major valid gather; S0 may have `None` Local prefix; PAD never becomes a native consumer; actual count remains bound to the frozen member.
6. **No-Local / CP / legacy boundaries:** No-Local stays on the ordinary path, CP remains pre-scan fail-closed for this Gate, and the canonical path must not enter `_prepare_training_data()`, `_get_training_inputs()`, `_inject_local_history()` or `_ttt_local_memory_tokens()`.

## 4. Implementation authorization boundary

Current blockers: **none**.

This approval authorizes only the requested **four-file CPU/static child implementation** under the exact accumulated v0.1-v0.5 design contract:

- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py`
- `cosmos_framework/model/generator/omni_mot_model.py`
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`
- `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`

Authorized work includes only the typed nested carrier / validation bridge, expected-vs-actual authority checks, Local-neutral safe preparation/static witnesses, single canonical prefix adaptation, CP fail-closed behavior, exact scan abort disposition, and the targeted CPU/static tests frozen by the design.

This approval does **not** authorize dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

After implementation, return the new formal root/child pair for a fresh implementation review. This Design approval does not imply implementation closure.

## 5. Exact verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC`
