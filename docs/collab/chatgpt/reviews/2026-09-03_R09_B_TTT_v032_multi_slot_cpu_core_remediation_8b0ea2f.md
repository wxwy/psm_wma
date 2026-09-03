# ChatGPT Independent Re-Review — R09-B TTT v0.3.2 Multi-Slot CPU Core Remediation @ 8b0ea2f

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V032-MULTI-SLOT-CPU-IMPLEMENTATION`

## 1. Review identity

- **root remediation/implementation SHA under verdict:** `8b0ea2fb289a4bced803148a51ac562165cc2f8d`
- **Cosmos child remediation SHA / root Gitlink:** `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- **request/ledger SHA observed on `V2`:** `3704b185dd90634f47a72d4f0cfd2040a2424b81`
- **prior implementation pair:** root `6fedfe9d184ee1dfc25a4195d601ab7a537d705f`, child `5b806554aa60c99b2681a68ae6b7763eb270dd96`
- **C1 implementation-design authority:** root `411e96760bdd1187303c0c2bfe2185223cc5c58e`, baseline child `cf52f43dc328d4c8eec51923d66835125664dee5`
- **approved v0.3.2 architecture authority:** `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3`

The current remote `V2` head at review start was `3704b185...`, whose direct parent is the exact remediation root `8b0ea2f...`. The verdict is bound to `8b0ea2f... + 1d90361...`; the request/ledger commit is not an implementation SHA.

The required literal `git fetch origin V2` was attempted in a temporary local repository, but this reviewer environment still cannot resolve `github.com` (`Could not resolve host`). Remote freshness, ancestry, root Gitlink and child branch head were therefore independently rechecked through the connected GitHub repository interface. No claim is made that shell fetch succeeded.

## 2. Verdict

**APPROVE_TO_CLOSE_R09_B_TTT_V032_MULTI_SLOT_CPU_CORE**

The prior ChatGPT invalid-row correctness blocker is closed. The additional public-API validation / fail-before-update coverage requested in the parallel review is also present. No remaining HIGH or MEDIUM blocker was found for C2.

This closure applies only to root `8b0ea2fb289a4bced803148a51ac562165cc2f8d` with `cosmos-framework@1d90361aeb21db53129ac27ddcaa1285b258fbbc`.

## 3. Scope / provenance

The exact root resolves `cosmos-framework` to `1d90361a...`. The child `v2` branch also resolves to that exact child SHA.

The remediation delta from `5b80655...` to `1d90361...` remains strictly within the two C1-authorized child files:

1. `cosmos_framework/model/generator/mot/local_evidence.py`
2. `cosmos_framework/model/generator/mot/local_evidence_test.py`

The production-code remediation is only 20 changed lines (`12` additions / `8` deletions); tests add 77 lines. No Memory Prefix, runtime, attention, config, optimizer, chronology, native-loss, training, inference or other C3+ surface is touched.

The root remediation updates only Gitlink/status bookkeeping in addition to carrying the prior review/request history. No design authority is rewritten.

## 4. Prior ChatGPT HIGH-1 closure — invalid-row structural read-inertia

### Prior blocker

At child `5b80655...`, `step_projected_many()` preserved invalid-row fast state in the update loop but then called `read_many(queries, state_out)` for **all** rows and only afterward multiplied by `valid`. That violated the frozen C1 pseudocode and allowed finite fp32 inputs to overflow the invalid-row read to `inf`, followed by `inf * 0 -> NaN` rather than exact zero.

### Remediation accepted

At child `1d90361...`, `cosmos_framework/model/generator/mot/local_evidence.py:467-493` now constructs `token_rows` inside the per-sample loop:

- invalid row: copy each of the four fast-state leaves unchanged, append exact fp32 `zeros([K_local,D_local])`, then `continue`;
- valid row: execute exactly one K/V-only inner prediction/update and then one vectorized K-slot post-update `_fast_mlp(queries[row], updated)` read.

The old whole-batch `read_many()` followed by `* valid` has been removed from `step_projected_many()`.

This now exactly matches the C1 structural contract: invalid rows do not execute a fast read at all, while valid rows preserve the one-write/many-read semantics.

### Regression evidence accepted

`local_evidence_test.py` adds `test_continual_ttt_multi_slot_invalid_rows_skip_fast_read_even_when_finite_values_overflow`:

- fills the invalid row's four fast-state leaves with finite `1e20` values;
- gives the invalid query base finite `1e20` values;
- instruments `_fast_mlp` call shapes;
- proves only the valid row executes the scalar-key prediction `(4,)` and K-slot read `(4,4)`;
- proves invalid token is finite and exact zero;
- proves invalid `present=False`;
- proves all four invalid-row state leaves are bitwise/exactly preserved.

This is the missing structural evidence; it no longer relies on ordinary random-scale values or post-hoc masking.

## 5. Public API negative / fail-before-update closure

The remediation also hardens and directly tests the new public multi-slot APIs.

### `project_queries()`

`local_evidence.py:377-386` now checks:

1. rank/shape/dtype;
2. device compatibility with `slot_queries`;
3. finiteness;

before the broadcast add. This ordering makes meta-device mismatch reject deterministically instead of attempting an unsupported reduction first.

### `read_many()`

`local_evidence.py:410-432` now checks:

1. rank/shape/dtype;
2. device compatibility with `slot_queries`;
3. finiteness;
4. fast-state structure/dtype/device/finiteness;
5. query/state device match;

before any fast read.

### Direct negative fixture

`test_continual_ttt_multi_slot_public_validation_fails_before_any_update` directly exercises:

- `project_queries`: wrong rank, wrong width, wrong dtype, nonfinite, meta-device mismatch;
- `read_many`: wrong K shape, wrong dtype, nonfinite, meta-device mismatch, inconsistent fast-state dtype;
- `step_projected_many`: invalid projected input while `torch.autograd.grad` is replaced with a function that must never be called;
- `step_many`: nonfinite evidence under the same fail-before-update guard;
- input fast state is verified unchanged after all failures.

This closes the missing negative/fail-before-mutation evidence without adding counters or production instrumentation.

## 6. Previously accepted C2 contract remains intact

The remediation does not alter the previously accepted multi-slot design:

- `k_local` remains a non-bool positive construction/checkpoint-time identity;
- `slot_queries[K_local,D_ttt]` remains the only new registered slow parameter;
- `K=1` slot query remains zero initialized; `K>1` remains normal initialized;
- the four-leaf fast-state payload remains 12,448 elements/sample;
- `project_evidence()` retains the K/base-Q/V triple ABI;
- Q/base query and slot queries remain outside `L_inner`;
- each valid sample performs one `autograd.grad` over the four fast-state leaves, independent of `K_local`;
- all K slots read the same post-update `W_t`;
- legacy `step_projected`, `step`, `scan_segment` remain K=1 wrappers and fail closed for `K>1`;
- strict K-mismatched `slot_queries` state-dict loading remains rejected without migration logic;
- scan/reset/detach and meta-gradient semantics are unchanged.

## 7. Submitted CPU evidence

The remediation request records the frozen isolated CPU selector result:

```text
23 passed, 8 deselected
```

with only the existing unknown-`L0` marker warnings, plus:

- both changed child files `py_compile`: PASS;
- child `git diff --check`: PASS;
- root `git diff --check`: PASS;
- no GPU, network, real data, model, cache, checkpoint, runtime, training, evaluation or inference execution.

The test environment remains acceptable only as isolated CPU mathematical-contract evidence. It does not establish production interpreter/runtime authority or bf16 production storage/read validation.

## 8. Closure and next Gate boundary

C2 is closed for this exact pair.

After all required reviewers close the same pair, the project may proceed only to a **separate docs-only C3 / v0.3.2 Memory Prefix source/ABI Gate request/design/static audit activity**. This C2 closure does not itself approve any C3 implementation.

The future C3 authority still needs to freeze, from exact current Cosmos source:

- `local_memory2llm` owner and `[B,K_local,32] -> [B,K_local,2048]` ABI;
- Memory pre-attention norm exact class/epsilon/ownership;
- Memory K/V projection ownership;
- K/V-only Memory context insertion and offsets;
- DM joint `[MEM,AR,DM]` two-way varlen attention contract while AR stays Memory-blind;
- Memory position/RoPE semantics;
- warm-start / structural perturbation semantics;
- checkpoint/optimizer ownership implications;
- fail-closed unsupported attention/runtime combinations.

## 9. Still prohibited

This closure does **not** authorize:

- Memory Prefix implementation or runtime/attention wiring;
- `local_memory2llm`, Memory norm or K/V projection implementation;
- position/RoPE/mask/packer modifications;
- chronology/native outer-loss integration;
- production model config, optimizer or checkpoint migration/refreeze;
- GPU/CUDA/torchrun;
- training, evaluation, inference or inference smoke;
- real model/data/cache/checkpoint access;
- P4/P5 real operations;
- B2-T.

Any later C3 design/remediation or runtime implementation SHA requires a fresh same-SHA review; this C2 closure must not be reused as runtime authority.