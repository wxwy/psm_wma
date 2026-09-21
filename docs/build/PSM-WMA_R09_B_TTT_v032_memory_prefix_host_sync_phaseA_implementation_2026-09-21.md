# PSM-WMA R09-B TTT v0.3.2 — Memory Prefix Hot-Path Host-Sync Elimination Phase A Implementation Record

- Date: 2026-09-21
- Status: IMPLEMENTED / STATIC-REVIEWED / RUNTIME-PENDING
- Scope: Phase A only. Text-KV reuse (Phase B) was intentionally not changed.
- Source proposal: `Memory Prefix Hot-Path Host-Sync Elimination — 修复建议 v0.2`
- Root baseline before implementation: `1a67d6570b7915a2bcbe9f92060ada23248e77b7`
- Child baseline before implementation: `e1f3fc7953f29eed08e9afb04f04527f8a99e7eb`
- Root implementation commit before this record: `b62cc44972bdad9434320af81f3b9f1d15d644e4`
- Child implementation commit: `8f6d439df6088383e722ef5d2373306e03106653`

## 1. Objective

Remove Memory Prefix CUDA device-to-host synchronization from the diffusion hot path while preserving the canonical per-sample attention order:

```
sample_i: [MEM_i | native_i]
```

This implementation deliberately does not restore inference text-KV reuse. The next profile must therefore isolate the latency contribution of Memory Prefix host synchronization.

## 2. Implemented changes

### 2.1 Build-time prefix validation moved to Python metadata

File:
`cosmos-framework/cosmos_framework/model/generator/mot/memory_prefix.py`

`build_memory_prefix_context()` no longer materializes CUDA offset/present tensors and then calls `MemoryPrefixContext.validate()`.

The immutable invariants are checked from Python metadata before device tensors are constructed:

- offsets start at zero
- offset count is sample count + 1
- final offset equals flattened prefix length
- lengths are non-negative
- present mask matches positive per-sample lengths
- all present samples use the same positive `K_local`

`MemoryPrefixContext.validate()` remains available as an explicit diagnostic API and may synchronize CUDA. It is no longer used by the production Memory Prefix hot path.

### 2.2 Layer hot-path validation removed

Files:
- `cosmos-framework/cosmos_framework/model/generator/mot/memory_prefix.py`
- `cosmos-framework/cosmos_framework/model/generator/mot/unified_mot.py`

Added `MemoryPrefixContext.replace_hidden()`.

It replaces only the layer-normalized hidden payload and performs metadata-only checks on shape/device/dtype. It preserves:

- `sample_offsets`
- `present`
- `k_local`

The previous per-layer:

```
memory_prefix_context.validate()
with_hidden(...)->validate()
```

path is removed from production attention execution.

### 2.3 `concat_prefix_with_native_kv()` host reads removed

File:
`cosmos-framework/cosmos_framework/model/generator/mot/memory_prefix.py`

Removed the per-sample CUDA offset reads:

```
prefix_offsets[index].item()
native_offsets[index].item()
```

New execution:

- B=1 inference fast path: direct `torch.cat([MEM, native])`
- B>1: GPU-side `repeat_interleave + index_copy` reordering
- no `.item()`, `.tolist()`, `.cpu()`, or `.numpy()` inside the concat helper
- `repeat_interleave(..., output_size=...)` is used to avoid determining output size through a host synchronization
- varlen `max_seqlen_KV` is supplied from Python metadata as `max_native_len + K_local`; no `.max().item()` is introduced

### 2.4 Python K_local metadata threaded through attention

Files:
- `cosmos-framework/cosmos_framework/model/generator/mot/unified_mot.py`
- `cosmos-framework/cosmos_framework/model/generator/mot/attention.py`

`MemoryPrefixContext.k_local` is passed through PackedAttentionMoT / dispatch into two-way attention so the prefix-augmented KV upper bound does not require inspecting CUDA tensor values.

No Text-KV reuse guard or alternate attention dispatcher was changed.

## 3. Added/extended tests

File:
`cosmos-framework/cosmos_framework/model/generator/mot/memory_prefix_test.py`

Coverage added for:

- B=1, K=1
- B=4, K=1
- mixed present/None samples
- K=4
- variable native sequence lengths
- exact per-sample `[MEM | native]` ordering
- combined offsets
- gradient propagation through prefix/native K/V after GPU-side reorder
- `replace_hidden()` preserving immutable prefix metadata
- static source guard against `.item()`, `.tolist()`, `.cpu()`, `.numpy()` in hot-path helpers

## 4. Static implementation conclusion

Phase A source implementation is complete.

Verified statically:

- production Memory Prefix path no longer calls `memory_prefix_context.validate()`
- `concat_prefix_with_native_kv()` contains no CUDA tensor value reads to host
- B=1 and B>1 paths preserve canonical `[MEM_i | native_i]` ordering by construction
- Text-KV reuse remains disabled for Local Memory requests, preserving clean performance attribution

## 5. Runtime verification status

Runtime verification is still pending.

At implementation time:

- authorized remote device was offline
- no GitHub CI workflow/status was attached to child commit `8f6d439df6088383e722ef5d2373306e03106653`

Therefore do NOT mark this Phase A as runtime PASS yet.

Required next checks:

1. run targeted `memory_prefix_test.py` and related MoT tests
2. run `ruff` on touched files / repository policy equivalent
3. re-run the original single-episode profile with the exact same setup:
   - iter_000003000
   - libero_10 task 0
   - UniPC 30
   - guidance=1.0
   - required vs off
4. compare at minimum:
   - `server.total`
   - `model.diffusion_sampling`
5. only after the new profile decide whether Phase B (Memory Prefix + Text-KV reuse) is necessary

## 6. Performance attribution gate

Do not assume Phase A will reduce required latency to the off baseline.

Interpret the re-profile as follows:

- large collapse of required/off ratio -> host-sync was the dominant cause
- substantial residual gap -> evaluate Text-KV recomputation / Phase B
- no meaningful change -> reopen performance root-cause analysis before additional optimization

Phase B must remain a separate change so host-sync and text-KV-reuse contributions stay identifiable.
