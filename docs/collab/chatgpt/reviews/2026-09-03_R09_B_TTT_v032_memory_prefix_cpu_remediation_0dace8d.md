# ChatGPT Independent Re-Review — R09-B TTT v0.3.2 Memory Prefix CPU Remediation @ 0dace8d

**Date:** 2026-09-03  
**Task/Gate:** `G0-R09-B-TTT-V032-MEMORY-PREFIX-CPU-IMPLEMENTATION`

## Review identity

- exact root remediation SHA under verdict: `0dace8dc033eef445e89eecfdd58b5df5f82a37f`
- request/ledger SHA: `7dec625b6cbdb28cfb53a97e37199f8c2881f414`
- latest status/ledger SHA observed: `75c6499fce1f9177bb648deef05538031afe49d6`
- exact child/Gitlink under verdict: `f98b7193d9c33a373f277a66d90c2e26221944e9`
- prior rejected pair: `8cd506f2d61883ad112d31b5f5b7c1ee18bec577 + e0dbf839c513b162f4e4ad2d717fd3d4132421cf`
- approved C4 design authority: `73d592a90c93897ca6f9be681801b87617e0a7a9`

The required literal `git fetch origin V2` was attempted and failed with `Could not resolve host: github.com`. Freshness, target ancestry/Gitlink, governance/status, request ledger and exact child source were re-read through the connected GitHub interface. Current `V2` was `75c6499...`; the formal implementation target remains `0dace8d...`, and it resolves the child Gitlink exactly to `f98b719...`.

The child remediation is exactly one commit ahead of `e0dbf83...` and changes only five already-authorized C4 files: `memory_prefix.py`, `cosmos3_vfm_network.py`, `unified_mot.py`, `attention.py`, `memory_prefix_test.py`.

## Verdict

**REQUEST_CHANGES**

The code-level fixes for the prior MemoryState/MemoryValue fail-closed defect and the `K_local` prevalidation defect are correct. However, the prior production-route acceptance-test blocker is still not closed. The reported `14 passed` selector still does not exercise the successful Prefix-present production attention route, and owner-level fail-closed/native-generation parity evidence remains incomplete. C4 therefore cannot be formally closed on this pair.

## Findings

### HIGH-1 — Prior production-route C4 acceptance blocker remains open

**Frozen contract:** `docs/build/PSM-WMA_R09_B_TTT_v032_memory_prefix_runtime_contract_design_v0.2_2026-09-03.md:133-182` requires C4-K01/K02 and C4-A01 to verify the actual normalized/no-RoPE Memory K path and actual one-softmax `[MEM, AR, DM]` attention behavior; the retained C4-03/C4-04 require AR invariance and DM joint-softmax correctness. The design explicitly says these acceptance contracts cannot be replaced by mock metadata/helper-only checks.

**Current production code is structurally correct:**
- `cosmos_framework/model/generator/mot/unified_mot.py:700-765` performs native RoPE first, then computes `K_MEM = k_proj_moe_gen -> k_norm_moe_gen` with no Memory RoPE and forwards it through the Prefix-aware dispatch seam.
- `cosmos_framework/model/generator/mot/attention.py:250-310` keeps the causal AR attention call separate and, when Prefix is present, concatenates per-sample Prefix/native K/V and performs one dense varlen attention call for full/DM queries.

**But the tests still do not execute that production route:** `cosmos_framework/model/generator/mot/memory_prefix_test.py:140-300` still contains:
- `test_memory_prefix_cpu_joint_softmax_changes_dm_but_not_ar_reference()`, which computes AR/DM outputs only with a local `reference()` helper plus `concat_prefix_with_native_kv`; it never invokes the successful Prefix-present `two_way_attention()` / `dispatch_attention()` route.
- `test_memory_prefix_k_uses_real_generator_norm_without_rope_or_query_projection()`, which manually calls `k_proj_moe_gen` and `k_norm_moe_gen`; it never drives `PackedAttentionMoT.forward()` nor captures the K/V actually handed to dispatch.
- the newly added tests exercise Flex rejection, `MemoryValue` rejection and alternate-dispatch compatibility, but still do not provide a successful production-route Prefix-present fixture.

A wiring regression in `PackedAttentionMoT.forward()` or `two_way_attention()` could therefore still leave all 14 tests green.

**Acceptance criteria:**
1. Add a synthetic CPU fixture that monkeypatches the actual attention primitive with a deterministic reference and drives the real Prefix-present `two_way_attention()` / `dispatch_attention()` path. It must prove the AR call never receives Prefix K/V and its output is invariant to Memory perturbation, while the DM/full call occurs exactly once and equals the per-sample joint `[MEM, AR, DM]` reference.
2. Add a `PackedAttentionMoT.forward()` production-seam fixture (or equivalent spy at its real dispatch boundary) that proves the Memory key reaching dispatch is the result of `k_proj_moe_gen -> k_norm_moe_gen`, receives no Memory RoPE, and no Memory Q/output path is invoked.
3. Re-run the selector and report the new exact count.

### HIGH-2 — Owner-level fail-closed evidence is still incomplete even though the code guard is now correct

**Code fix accepted:**
- `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py:1060-1066` now rejects Prefix + native `MemoryState` with a feature-specific `ValueError` immediately after Prefix creation, before packed-attention construction/native memory use.
- `cosmos_framework/model/generator/mot/attention.py:687-700` now explicitly rejects Prefix + `MemoryValue` before the generic legacy assert.

This closes the code defect from the prior HIGH-1.

**Evidence gap:** `memory_prefix_test.py` only adds a direct `dispatch_attention()` `MemoryValue` negative test. It still has no owner-level CPU fixture proving Prefix + `MemoryState` fails before `build_packed_sequence()` / memory init-read-write work, and no owner-level fixtures for the already-frozen CUDA-graph and replicated-attention-I/O guards. The previous review explicitly required fail-before-cache/kernel evidence, not merely the presence of a branch in source.

**Acceptance criteria:**
1. Add a synthetic owner-route fixture or a small pure owner guard helper invoked by `Cosmos3VFMNetwork.forward`, with spies proving Prefix + `MemoryState` fails before packed-attention construction/native memory activity.
2. Cover the Prefix-present CUDA-graph and replicated-attention-I/O owner guards in the same CPU-only contract style.
3. No real model/checkpoint/data access is required or allowed.

### MEDIUM-1 — C4-P01 native packing parity is still only text-only/subset coverage

`cosmos_framework/model/generator/mot/memory_prefix_test.py:45-70` still compares a text-only pack and only `sample_lens`, `split_lens`, `attn_modes`, `sequence_length`, `text_indexes`, `position_ids`, and `ce_loss_indexes`.

The frozen C4-P01/C4-06 contract requires Prefix-present vs No-Memory parity for the relevant native generation geometry/index/loss/prepared metadata, not only a no-generation text sample. The remediation request itself stated this prior acceptance blocker was closed, but no native vision/action/sound generation parity fixture was added.

**Acceptance criteria:** add at least one synthetic native-generation packing case supported by the existing packer fixtures and compare the frozen relevant native modality indexes/counts/loss/prepared metadata between Prefix-present and No-Memory. Local payload must be the only intended difference.

## Closed prior findings / accepted remediation

The following prior findings are **closed** and need not be changed unless subsequent remediation alters them:

- Prior HIGH-1 code defect: Prefix + `MemoryState` and Prefix + `MemoryValue` now have named fail-closed `ValueError` paths.
- Prior MEDIUM-1: all present slot tensors are now prevalidated for positive/common `K_local` before any projector call; direct `MemoryPrefixContext.validate()` also enforces equal positive present lengths; the zero-projector-call negative fixture exists.
- Prefix-present alternate dispatch now fails closed while Prefix-absent preserves the legacy dispatch keyword signature.
- Flex rejection is now explicitly covered.
- Remediation stays within the approved C4 file boundary; no C5/config/optimizer/checkpoint/GPU/training scope drift was found.

## Required next step

Submit another same-scope C4 remediation pair focused on tests/evidence. Prefer test-only changes plus, only if needed, a minimal pure owner guard helper inside an already-approved C4 file. Keep the child scope within the approved seven C4 files and root status/ledger docs.

Allowed validation remains synthetic CPU C4 tests, `py_compile`, and `git diff --check` only.

Still prohibited: C5 fast-state/chronology, `local_evidence.py`, `utils/memory.py`, config/optimizer/checkpoint/trainer/inference/parallelization expansion, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 training.

A new root/child pair requires fresh same-SHA three-party review. This verdict applies only to `0dace8dc... + f98b7193...`.