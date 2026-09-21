# PSM-WMA R09-B TTT v0.3.2 — Memory Prefix + Text-KV Reuse Phase B Implementation Record

- Date: 2026-09-21
- Status: IMPLEMENTED / STATIC-REVIEWED / RUNTIME-PROFILE-PASS / UNIT-CLOSURE-RETEST-PENDING
- Scope: Phase B, single-sample inference only (B=1), matching the locked single-episode profile gate
- Parent baseline: `5bd0d7544cb8ad18867b9e0b99e7ea3572a29960`
- Child Phase A baseline: `8f6d439df6088383e722ef5d2373306e03106653`
- Child Phase B implementation commit: `60be568e809786f94ae81ed8de668131b1083f6a`

## 1. Entry condition

Phase A runtime verification passed on child `8f6d439`:

- diffusion_sampling p50: 15241 ms -> 2791 ms
- off baseline: 1445 ms
- post-PhaseA required/off residual ratio: ~1.9x

This residual gap satisfies the Phase B entry condition. Phase B is intentionally isolated from Phase A.

## 2. Objective

Restore request-local inference text-KV reuse for Local Memory requests while preserving the canonical Memory Prefix semantics.

First denoise step:

```
GEN Q -> [MEM | text | current GEN]
          |
          +-- cache text K/V only
```

Subsequent denoise steps:

```
GEN Q -> [MEM | cached text | current GEN]
```

Memory Prefix is never stored inside the text cache.

## 3. Implementation

### 3.1 MemoryState capability gate

File:
`cosmos-framework/cosmos_framework/model/generator/utils/memory.py`

Added fail-closed capability:

```python
MemoryState.supports_memory_prefix() -> False
```

Only the request-local `InferenceTextKVMemoryState` overrides it to `True`.

This prevents Phase B from silently enabling Memory Prefix with training KV-cache states or unrelated AR memory paths.

### 3.2 Network blocker narrowed

File:
`cosmos-framework/cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`

The previous unconditional rejection of:

```
Memory Prefix + any MemoryState
```

is replaced by:

```
Memory Prefix + MemoryState without supports_memory_prefix() -> reject
```

Therefore only the explicitly compatible inference text-KV state may coexist with the prefix.

### 3.3 Alternate dispatcher blocker narrowed

File:
`cosmos-framework/cosmos_framework/model/generator/mot/unified_mot.py`

Memory Prefix now permits exactly:

- base `dispatch_attention`
- `dispatch_attention_with_text_kv_memory`

Other alternate attention dispatchers remain fail-closed.

### 3.4 Cached GEN attention includes Memory Prefix

File:
`cosmos-framework/cosmos_framework/model/generator/mot/inference_text_kv_memory.py`

The gen-only cached path now builds K/V in the canonical order:

```
[MEM | cached UND/text | current GEN]
```

For the first cache-fill denoise step, Memory Prefix arguments are forwarded to the normal two-way attention path. The resulting `kv_to_store` still contains only native GEN/UND K/V, so only text K/V enters `UndKVCache`.

### 3.5 Local Memory no longer disables B=1 text-KV reuse

File:
`cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py`

Removed the Local-Memory-specific rejection from `_can_reuse_inference_text_kv()`.

All existing eligibility guards remain:

- no velocity postprocess
- reusable pack templates required
- no CP / CFGP / DP-shard
- two-way attention only
- no video temporal causal
- no incompatible sound path
- exactly one sample / one sequence plan
- no multi-vision-items-per-sample path

## 4. Scope boundary

This Phase B commit intentionally keeps the existing `batch_size == 1` text-KV reuse contract.

It does **not** implement batched text-KV caching for `predict_batch` / `num_envs=4`.

Reason: batched reuse requires separate packed/varlen cache geometry and would be a distinct optimization. Keeping Phase B at B=1 preserves clean attribution against the existing single-episode profile.

## 5. Added tests

New file:
`cosmos-framework/cosmos_framework/model/generator/mot/inference_text_kv_memory_test.py`

Coverage includes:

- inference text-KV state explicitly advertises Memory Prefix compatibility
- cached GEN attention K/V order is exactly `[MEM | cached text | current GEN]`
- first cache-fill step forwards Memory Prefix to standard attention
- optional-prefix dispatch allows the text-KV alternate while arbitrary alternates remain rejected by existing tests
- Local Memory single-sample requests are eligible for text-KV reuse

## 6. Runtime gate

Runtime verification is pending. The authorized remote device available to ChatGPT was offline at implementation time and no GitHub CI status was attached to the child commit.

Required next verification:

1. targeted unit tests:
   - `mot/inference_text_kv_memory_test.py`
   - `mot/memory_prefix_test.py`
   - `mot/unified_mot_test.py`
   - `mot/attention_test.py`
2. same single-episode profile:
   - iter_000003000
   - libero_10 task 0
   - UniPC 30
   - guidance=1.0
   - B=1
   - required vs off
3. compare:
   - `model.diffusion_sampling`
   - `model.generate_total`
   - `server.total`
4. functional smoke:
   - SR remains successful on the profile episode

Primary performance question:

> Does required diffusion p50 move materially from the Phase A value 2791 ms toward the off baseline 1445 ms?

Do not infer batched `num_envs=4` throughput from this B=1 Phase B gate.


## 7. Runtime verification result

Runtime verification was executed on production child `60be568e809786f94ae81ed8de668131b1083f6a`.

Locked profile setup:

- iter_000003000
- libero_10 task 0
- UniPC 30, shift=5.0
- guidance=1.0
- B=1
- `--profile_inference`
- action_horizon=8
- max_steps=520
- required / TTT mode

Steady-state p50:

| Metric | Phase A `8f6d439` | Phase B `60be568` | off baseline |
| --- | ---: | ---: | ---: |
| model.diffusion_sampling | 2791 ms | **1996 ms** | 1445 ms |
| model.generate_total | 2845 ms | **2050 ms** | 2202 ms |
| server.total | 3789 ms | **3032 ms** | 2235 ms |
| model.prepare_inference | 24 ms | 25 ms | 526 ms |
| model.pack_template | 19 ms | 19 ms | 18 ms |
| history_overhead_total | 888 ms | 921 ms | — |
| SR | 1/1 | **1/1** | 0/1 |

Phase B reduced diffusion p50 by approximately **28%** relative to Phase A and moved the required/off residual ratio from about **1.9x to 1.38x**.

Performance/functional runtime gate: **PASS**.

### 7.1 Unit-test regression and closure

Runtime executor found one Phase-B-only regression in:

`memory_prefix_test.py::test_memory_prefix_owner_guards_fail_before_packed_attention_work[False-memory0-sequence_sharded-None-native MemoryState]`

Cause: the test used bare `object()` as a fake MemoryState. Phase B production code correctly expects the MemoryState capability API and production MemoryState defaults fail-closed.

A test-only closure commit was added:

- child test-closure commit: `879c8e07f353836e8613d50a0cb9530805d7e97d`
- change: replace bare `object()` fixture with a real `MemoryState` subclass inheriting `supports_memory_prefix() == False`
- production Phase B code is unchanged from `60be568`

The new child commit requires only targeted unit-test re-run for final suite closure. The Phase B runtime profile remains valid because production code did not change.
