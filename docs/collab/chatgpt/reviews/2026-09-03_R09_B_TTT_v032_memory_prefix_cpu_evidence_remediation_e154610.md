# ChatGPT Independent Re-Review — R09-B TTT v0.3.2 Memory Prefix CPU Evidence Remediation @ e154610

**Date:** 2026-09-03  
**Task/Gate:** `G0-R09-B-TTT-V032-MEMORY-PREFIX-CPU-IMPLEMENTATION`

## Review identity

- exact root implementation/remediation SHA under verdict: `e15461014ca5c9ee0c37e8290e927cd8f4e9ff04`
- request/ledger SHA observed on current `V2`: `6b6c407f8d017219f4c66894227ccb4f5ca8afef`
- exact child/Gitlink under verdict: `dd6b7dc4ac0713736dca61c5a01de6932b7e5576`
- prior remediation pair: `0dace8dc033eef445e89eecfdd58b5df5f82a37f + f98b7193d9c33a373f277a66d90c2e26221944e9`
- approved C4 design authority: `73d592a90c93897ca6f9be681801b87617e0a7a9`

The required literal `git fetch origin V2` was attempted and failed because the reviewer shell cannot resolve `github.com` (`Could not resolve host: github.com`). Freshness, target ancestry/Gitlink, canonical Inbox, governance/status and exact child source were therefore re-read through the connected GitHub interface. Current `V2` is the request/ledger commit `6b6c407...`, whose parent is the formal target `e154610...`.

The child compare `f98b719... -> dd6b7dc...` is exactly one commit and changes only the already-approved `cosmos_framework/model/generator/mot/memory_prefix_test.py`; no production code or C5/config/optimizer/checkpoint/GPU/training surface changed.

## Verdict

**REQUEST_CHANGES**

The substantive production-route evidence gaps from the prior review are now largely closed. One remaining evidence assertion is vacuous, so the frozen C4 prepared-metadata parity contract is still not actually tested on this SHA.

## Closed from prior review

- **Production Prefix attention route — CLOSED.** The new fixture drives real `dispatch_attention -> two_way_attention` with a deterministic CPU attention primitive. It verifies the AR call receives only native K/V, the DM call receives one joint `[MEM, AR, DM]` K/V sequence, AR output is invariant to Memory-value perturbation, and DM output changes with Memory.
- **Actual Prefix K projection/norm/no-RoPE seam — CLOSED.** The new `PackedAttentionMoT.forward` fixture captures the K delivered to dispatch and checks it equals `k_proj_moe_gen -> k_norm_moe_gen`; only the two native AR/DM key paths pass through the rotary seam, and no extra Memory query projection call occurs.
- **Owner fail-before-work guards — CLOSED.** New owner-route fixtures cover Prefix+`MemoryState`, CUDA-graph padding and replicated attention-I/O and install a failing `build_packed_sequence` sentinel, demonstrating rejection before packed-attention construction. Direct Prefix+`MemoryValue`, Flex, three-way, multi-control and sharded guards remain covered.
- **Native generation packing parity — mostly CLOSED.** The new action-generation fixture compares native sequence geometry, text/action indexes, action loss/condition/timestep metadata and out-of-band Local ownership while keeping Local out of native rows.

## Finding

### MEDIUM-1 — prepared-metadata parity assertion compares `None == None`

**Files:**
- `cosmos_framework/model/generator/mot/memory_prefix_test.py:102-157`
- `cosmos_framework/data/generator/sequence_packing/sequence.py:1110-1127`

The new native action-generation parity fixture ends with:

`assert prefix.get_sequence_pack_metadata() == native.get_sequence_pack_metadata()`

But freshly returned CPU `PackedSequence` objects have `_sequence_pack_metadata = None`. `get_sequence_pack_metadata()` only returns that field; it does not lazily build metadata. Metadata is populated only by `prepare_sequence_pack_metadata()` (or by `to_cuda()`, which calls it). Therefore the current assertion is only `None == None` and does **not** validate the request's claimed prepared-metadata parity.

This is an evidence blocker, not a production-architecture blocker. The already-compared source inputs strongly suggest parity, but C4 explicitly froze native prepared metadata as an acceptance surface and closure cannot claim it was exercised when the test is vacuous.

**Acceptance criteria:**
1. In the synthetic CPU action-generation parity fixture, explicitly call `prepare_sequence_pack_metadata()` on both `native` and `prefix` before comparing metadata, or compare the fully prepared metadata fields through an equivalent real preparation path.
2. Assert the prepared metadata is non-`None` on both sides before equality/field comparison, so the fixture cannot regress to a vacuous `None == None` pass.
3. Re-run only the C4 synthetic CPU selector and report the exact count; `py_compile` and `git diff --check` remain sufficient companion evidence.
4. Keep remediation test-only inside the already-approved C4 seven-file boundary. No production-code change is required for this finding.

## Accepted and unchanged

No redesign is requested. The following remain accepted:
- out-of-band Local Prefix packing;
- `[B,K_local,32] -> [B,K_local,2048]` Prefix context;
- per-layer Memory pre-attention norm;
- `K_MEM = k_proj_moe_gen -> k_norm_moe_gen`, no RoPE;
- no `Q_MEM`, Memory output row, residual or MLP;
- AR Memory-blind path;
- DM one-call joint Prefix/native attention layout;
- Prefix+MemoryState/MemoryValue, Flex, three-way, multi-control, CP/Ulysses, CUDA-graph and replicated-I/O fail-closed boundaries;
- fixed positive common `K_local` prevalidation before projection;
- no scope drift outside C4.

## Required next step

Submit a new test-only child SHA and corresponding root Gitlink/status SHA. Fresh same-SHA review is required. Until closure, C5 fast-state/chronology, `local_evidence.py`, `utils/memory.py`, config/optimizer/checkpoint/trainer/inference/parallelization, GPU/CUDA/torchrun, real model/data/cache/checkpoint access, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 training remain prohibited.
