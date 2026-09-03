# ChatGPT Independent Review — R09-B TTT v0.3.2 Memory Prefix CPU Implementation @ 8cd506f

**Date:** 2026-09-03  
**Task/Gate:** `G0-R09-B-TTT-V032-MEMORY-PREFIX-CPU-IMPLEMENTATION`

## Review identity

- exact root implementation SHA under verdict: `8cd506f2d61883ad112d31b5f5b7c1ee18bec577`
- request/ledger SHA observed at review start: `b2a31af5f69f90e73a6ba9c57f548fdc29d9dd87`
- exact child/Gitlink under verdict: `e0dbf839c513b162f4e4ad2d717fd3d4132421cf`
- child baseline: `1d90361aeb21db53129ac27ddcaa1285b258fbbc`
- approved C4 design authority: `73d592a90c93897ca6f9be681801b87617e0a7a9`

The required literal `git fetch origin V2` was attempted and failed because the reviewer shell cannot resolve `github.com` (`Could not resolve host: github.com`). Freshness, exact target ancestry/Gitlink, governance/status, request ledger and pinned child source were therefore re-read through the connected GitHub interface. At review time current `V2` was `b2a31af...`, whose parent is the formal target `8cd506f...`; the target resolves the child Gitlink exactly to `e0dbf83...`.

The child compare `1d90361... -> e0dbf83...` is exactly one commit and touches exactly the seven C4-authorized files:

1. `cosmos_framework/data/generator/sequence_packing/packers.py`
2. `cosmos_framework/data/generator/sequence_packing/sequence.py`
3. `cosmos_framework/model/generator/mot/memory_prefix.py`
4. `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`
5. `cosmos_framework/model/generator/mot/unified_mot.py`
6. `cosmos_framework/model/generator/mot/attention.py`
7. `cosmos_framework/model/generator/mot/memory_prefix_test.py`

## Verdict

**REQUEST_CHANGES**

The core architectural implementation is directionally correct, but C4 cannot close on this SHA. One production fail-closed contract is missing, and the reported `10 passed` CPU selector does not actually exercise several frozen C4 acceptance paths. A small seven-file-scope remediation is sufficient; C5/GPU/training remain out of scope.

## Findings

### HIGH-1 — Prefix + native `MemoryState` is not fail-closed at the owner boundary

**Frozen contract:** `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_runtime_contract_design_v0.1_2026-09-03.md:154-166,203-212` requires Prefix-present `memory_value/native KV-cache memory` to fail closed before entering an attention kernel, with a feature-specific `ValueError`.

**Implementation:**

- `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py:1015-1018` exposes `memory: MemoryState | None` on the same public forward that now builds Prefix.
- `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py:1060-1062` creates `memory_prefix_context` and only guards CUDA-graph padding; it does not reject `memory is not None`.
- `_impl_forward()` subsequently initializes/reads native `MemoryState` while also forwarding `memory_prefix_context` to every decoder layer.
- `cosmos_framework/model/generator/mot/attention.py:690` only has the pre-existing generic `assert memory_value is None`, before the new Prefix-specific guard logic. That is an `AssertionError`, not the frozen `ValueError`, is not Prefix-specific, and is not a reliable fail-closed contract (assertions can be disabled).

This leaves an explicitly forbidden combination admitted past the correct owner boundary. Depending on native memory frame/state semantics, it can also reach deeper execution before failing rather than being rejected deterministically at Prefix admission.

**Acceptance criteria:**

1. When `MemoryPrefixContext` is present, reject native `MemoryState` / `MemoryValue` with a feature-specific `ValueError` before any attention kernel and before native memory state read/write can affect the call.
2. Prefer an owner-level guard in `Cosmos3VFMNetwork.forward` (or equivalently before `memory.init/read_for_layer`) for `memory_prefix_context is not None and memory is not None`; also make the dispatch-level Prefix + `memory_value` behavior explicit rather than relying on the generic assert.
3. Add a synthetic CPU fixture proving Prefix + native memory fails with the expected `ValueError` before the attention function can be invoked.

### HIGH-2 — The 10-test selector does not satisfy the frozen production-route C4 acceptance suite

**Frozen contracts:** `...runtime_contract_design_v0.1...md:196-212` freezes C4-01..08; v0.2 additionally freezes C4-P01/P02/P03, C4-K01/K02, C4-A01 and C4-F01. These are acceptance tests, not merely helper-unit suggestions.

**Current tests:** `cosmos_framework/model/generator/mot/memory_prefix_test.py:120-203` do not exercise the actual Prefix attention route for the most important semantics:

- `test_memory_prefix_cpu_joint_softmax_changes_dm_but_not_ar_reference()` computes both AR and DM outputs entirely in a local `reference()` function plus `concat_prefix_with_native_kv`; it never calls `two_way_attention()`/`dispatch_attention()` for the successful Prefix-present path. A wiring bug in the real route would not fail this test.
- `test_memory_prefix_k_uses_real_generator_norm_without_rope_or_query_projection()` manually calls `k_proj_moe_gen` and `k_norm_moe_gen`; it does not drive `PackedAttentionMoT.forward()` or spy the K passed to dispatch. If the production Prefix branch bypassed `k_norm_moe_gen`, this test would still pass.
- `test_memory_prefix_dispatcher_rejects_unsupported_paths_before_attention_kernel()` covers only sharded, three-way and multi-control. The frozen C4-F/C4-07 set also requires Flex, native `MemoryValue`, CUDA graph and replicated-I/O fail-closed behavior.
- `memory_prefix_test.py:43-68` checks packer parity using a text-only pack and only a subset of metadata fields. It does not directly exercise the full native generation/index/loss/prepared-metadata parity contract that C4-P01/C4-06 froze.

Therefore `10 passed` is valid evidence for those ten test cases, but it is not evidence that the frozen C4 acceptance suite passed. Closure would overstate what was tested.

**Acceptance criteria:** keep the remediation synthetic CPU-only and within the approved test/source boundary, but make the fixtures hit the production route:

1. Monkeypatch the attention primitive with a deterministic CPU reference and call the real `two_way_attention()`/`dispatch_attention()` Prefix-present path; prove actual AR output is invariant to Memory perturbation and actual DM output equals one per-sample joint `[MEM, AR, DM]` softmax.
2. Exercise `PackedAttentionMoT.forward()` (or an equivalent production Prefix projection seam) with a spy/capture so the test fails if `K_MEM` bypasses `k_norm_moe_gen`; also prove no Memory Q/output path is invoked.
3. Add fail-before-kernel fixtures for **all** frozen unsupported combinations: Flex, native `MemoryValue`, CUDA graph, replicated I/O, plus the already-covered three-way/multi-control/sharded cases.
4. Strengthen packer parity to include a native generation case and the frozen relevant native modality/index/loss/prepared-metadata fields, not only text-only geometry.
5. Re-run the resulting selector and report the new exact count; do not retain `10 passed` as the closure count after adding required cases.

### MEDIUM-1 — Common `K_local` is detected only after earlier samples may already be projected

**Frozen contract:** `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_runtime_contract_design_v0.2_2026-09-03.md:48-62` requires all present rows in a batch to have the same positive `K_local`, with violation rejected **before the projector**.

**Implementation:** `cosmos_framework/model/generator/mot/memory_prefix.py:60-70` validates and immediately projects each present sample inside one loop. For `[K=1, K=2]`, the first sample is already sent through `projector(...)` before the second sample triggers the mismatch error. In addition, `MemoryPrefixContext.validate()` validates monotonic offsets/present consistency but does not enforce equal positive per-sample lengths for directly constructed contexts.

This does not currently produce an incorrect accepted Prefix through the normal builder, but it violates the frozen fail-before-projector invariant and leaves the public context validator weaker than the fixed-`K_local` ABI.

**Acceptance criteria:**

1. Pre-validate all present token ranks, positive slot counts and common `K_local` before invoking the projector on any sample.
2. Make `MemoryPrefixContext.validate()` reject unequal positive per-sample lengths (or otherwise make it impossible for a directly constructed context to bypass the fixed-`K_local` invariant).
3. Add a projector-spy fixture proving inconsistent `K_local` fails with zero projector calls, plus a direct-context unequal-length negative fixture.

## Accepted portions

The following portions are accepted and need not be redesigned unless the remediation changes their assumptions:

- child scope is exactly the approved seven files and exactly one commit ahead of `1d90361...`;
- Local is removed from native sequence geometry in the packer and carried as an out-of-band per-sample payload;
- Local is removed from native generation/EOV structural decisions and from `all_gen_indexes`;
- `MemoryPrefixContext` is separate from native `MemoryValue/MemoryState` storage;
- per-layer `memory_input_layernorm` exists;
- `K_MEM` production code uses generator K projection + `k_norm_moe_gen` and intentionally receives no RoPE;
- Memory has no Q row/output/residual/MLP path;
- AR causal attention is structurally kept outside the Prefix branch;
- DM Prefix path forms per-sample `[MEM,native]` K/V and invokes one dense varlen attention call;
- three-way, multi-control, sharded/CP and Flex guards exist in the Prefix-aware dispatch path; CUDA-graph and replicated-I/O owner guards also exist;
- no out-of-scope child files, config/optimizer/checkpoint/chronology/GPU/training changes were found in the reviewed commit pair.

## Required next step

Submit a new same-scope remediation root/child pair. The remediation may touch only the already approved seven C4 files and root status/ledger docs. Re-run only synthetic CPU C4 tests / py_compile / diff-check. No C5, config/optimizer/checkpoint, GPU/CUDA/torchrun, model/data/cache/checkpoint runtime access, training, evaluation, inference, P4/P5 or B2-T is authorized.

The new implementation SHA requires a fresh same-SHA three-party review. This verdict applies only to `8cd506f2... + e0dbf839...`.
