# ChatGPT Independent Review — R09-B TTT v0.3.2 Multi-Slot CPU-Core Design @ 411e967

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V032-MULTI-SLOT-CPU-DESIGN`

## 1. Review identity

- **root design SHA under verdict:** `411e96760bdd1187303c0c2bfe2185223cc5c58e`
- **request/ledger SHA observed on `V2`:** `86022073e631c60531d45ed90af90924f33bd643`
- **actual Cosmos child/Gitlink:** `cf52f43dc328d4c8eec51923d66835125664dee5`
- **design:** `docs/build/PSM-WMA_R09_B_TTT_v032_multi_slot_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`
- **approved v0.3.2 architecture authority:** `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3`
- **closed K_local=1 CPU-core implementation:** root `fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312`, child `cf52f43dc328d4c8eec51923d66835125664dee5`

The current remote `V2` head at the final pre-write check was `86022073...`, whose direct parent is the exact design SHA `411e967...`. The verdict is bound to the design SHA, not to the request/ledger commit.

The required literal `git fetch origin V2` was attempted in a temporary local repository, but this reviewer environment still cannot resolve `github.com` (`Could not resolve host`). Remote freshness, ancestry and the exact Gitlink were therefore independently rechecked through the connected GitHub repository interface. No claim is made that shell fetch succeeded.

## 2. Verdict

**APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE**

No HIGH or MEDIUM blocker was found.

This approval is valid only for root design `411e96760bdd1187303c0c2bfe2185223cc5c58e` with baseline child/Gitlink `cf52f43dc328d4c8eec51923d66835125664dee5`.

## 3. Scope / provenance review

The exact design commit changes only:

- `docs/build/PSM-WMA_R09_B_TTT_v032_multi_slot_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`;
- `SESSION.md`;
- `TODO.md`.

The root still pins `cosmos-framework@cf52f43...`; no child source is changed by C1. The effective LIBERO two-way anchor remains `cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py:44` with `joint_attn_implementation="two_way"`.

The design correctly constrains C2 implementation to exactly:

1. `cosmos_framework/model/generator/mot/local_evidence.py`
2. `cosmos_framework/model/generator/mot/local_evidence_test.py`

and explicitly excludes runtime/attention, `local_memory2llm`, Memory Prefix norm/KV projection, RoPE/position/mask, chronology/native loss, production config, optimizer, checkpoint migration/refreeze, GPU, training, evaluation and inference.

## 4. Accepted algorithm / API contract

The C1 design is consistent with the approved v0.3.2 architecture and the closed K=1 CPU core:

1. `k_local` is a non-bool positive **construction-time** integer and part of model/checkpoint identity; the same core instance cannot change slot cardinality at runtime.
2. A new registered slow parameter `slot_queries: [K_local,D_ttt]` is the only multi-slot state/parameter extension. The four-leaf fast-state payload remains unchanged at 12,448 elements/sample.
3. `query_proj` remains one evidence-conditioned base query. Multi-slot queries are `q_base[:,None,:] + slot_queries[None,:,:]`; K and V are not replicated by slot.
4. `K_local=1` uses zero-initialized `slot_queries`, preserving the existing single-query read numerically for equal old parameter values. `K_local>1` uses an explicit random initialization to break query-slot symmetry.
5. Each valid sample/timestep executes exactly one K/V-only inner loss, one `autograd.grad` over the complete four-member fast state, and one `W_(t-1) -> W_t` update. Query-base and slot-query parameters do not enter `L_inner`.
6. Every slot read uses the same **post-update** `W_t`; multi-slot read is pure and must not mutate fast state or introduce hidden counters/state.
7. `project_evidence()` retains its existing 3-tuple ABI; `project_queries()` is a separate pure slot-expansion function.
8. The new multi APIs (`read_many`, `step_projected_many`, `step_many`, `scan_segment_many`) have explicit ranks/shapes and preserve the prior per-sample functional KVB semantics.
9. Legacy `step_projected`, `step`, and `scan_segment` remain K=1 rank-compatible wrappers. With `k_local>1`, legacy methods must fail closed rather than silently discard slots.
10. Invalid rows remain exactly inert: four-leaf state value preserved, all multi-slot tokens zero, `present=false`.
11. `create_graph=True` remains the training/meta-gradient contract; the design does not regress to detached B0/B1 behavior.
12. The C2 test matrix MS01–MS13 is adequate to detect the main failure modes: wrong parameter count, repeated writes, pre-update read, state mutation, invalid-row drift, K=1 regression, slot-order coupling, missing gradients, segment mismatch and silent checkpoint cardinality conversion.

I found no mathematical contradiction with the v0.2/v0.2.1 persistent fast-state/KVB/TBPTT contract or the v0.3.2 one-write/many-read authority.

## 5. Checkpoint / parameter boundary

The design correctly treats `slot_queries` as a deliberate module `state_dict` schema addition and explicitly does **not** claim old `cf52f43` checkpoint strict-load compatibility. K-mismatched `slot_queries` shapes must fail standard strict loading; migration is a separate later Gate.

### Non-blocking wording clarification

Section 1.3 says C2 must not change “checkpoint/config schema”, while Section 3.2 correctly states that adding registered `slot_queries` is a deliberate checkpoint-schema change. For this approval, the authoritative interpretation is:

- **allowed in C2:** the module-level `state_dict` gains exactly the designed `slot_queries` key/shape;
- **not allowed in C2:** changes to checkpoint loader/migration logic, production checkpoint authority/refreeze, optimizer selection, model/recipe config schema, or compatibility adapters.

No remediation SHA is required solely for this wording because the detailed construction/checkpoint contract and the review request already make the intended boundary unambiguous.

## 6. Dtype / compute boundary

The new design inherits the prior CPU-core contract that reference CPU compute is fp32 and that future production bf16 fast-state storage is not validated by this Gate. C2 may prove the new multi-slot math on synthetic CPU fp32 tensors only.

If C2 implements `read_many` in a way that narrows or contradicts the previously approved dtype-preserving fast-state API, that is implementation drift and must be caught in the C2 closure review. This C1 approval does not claim that bf16 production read/storage has been validated.

## 7. C2 evidence required for closure

The later implementation review must verify, on the exact new child SHA/root Gitlink:

- child diff is limited to the two authorized files;
- `slot_queries` registry/counts and `k_local` validation are exact;
- exactly one KVB update per valid sample independent of `K_local`;
- `read_many` is state-pure and post-update;
- invalid rows are exactly inert;
- K=1 wrapper/direct-many equivalence and K>1 legacy fail-closed behavior;
- slot permutation/isolation;
- outer gradient reaches query projection, every slot parameter, K/V projections and all W0 leaves;
- scan-vs-step chronology equivalence;
- strict K-mismatched state-dict load fails without migration logic;
- existing + new targeted `continual_ttt` CPU tests PASS;
- child/root `git diff --check` PASS;
- no GPU/data/model/checkpoint/runtime execution outside the frozen CPU selector.

The environment previously accepted for the isolated CPU core may be reused only as test execution evidence; it does not establish production interpreter/runtime authority.

## 8. Authorized next step only

This verdict authorizes **C2 only**:

- implement the v0.3.2 multi-slot CPU algorithm core in `local_evidence.py`;
- add/adjust adjacent `local_evidence_test.py` contract tests;
- use synthetic CPU tensors and the frozen isolated pytest selector/diff checks;
- push a new child implementation SHA, bump the root Gitlink/status evidence, and submit that exact pair for fresh three-party closure review.

## 9. Still prohibited

This approval does **not** authorize:

- Memory Prefix source/ABI implementation;
- production runtime/attention wiring;
- `local_memory2llm`, Memory norm or K/V projection implementation;
- position/RoPE/mask or packer changes;
- chronology/native outer-loss integration;
- production model config, optimizer or checkpoint migration/refreeze;
- GPU/CUDA/torchrun;
- training, evaluation, inference or inference smoke;
- real cache/data/model/checkpoint access;
- P4/P5 real operations;
- B2-T.

Any new design remediation or implementation SHA requires a fresh same-SHA review; this C1 design approval must not be reused as C2 closure approval.
