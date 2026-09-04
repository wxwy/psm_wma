# ChatGPT independent re-review — C6 runtime integration implementation remediation @ 32bf92a

**Gate**: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-IMPLEMENTATION`  
**Formal target**: root implementation `32bf92a600e13c3414cf4c1cbd9a8cd1af73ee82`; child/Gitlink `0a2a438a9440db9243634f1358a73fa00c4711c1`  
**Observed V2 request/bookkeeping HEAD at review start**: `1eaa9a4547d1c6463d0db0a1a19199e0c5fedec2`  
**Frozen C6 design authority**: `574d28750883d9e69bd03aa39cc3640646190dfa`

## Verdict

`REQUEST_CHANGES`

## Closed from prior review

- Prior HIGH-1 **CLOSED**: public raw `commit()` is removed; C6 now delegates segment closure to C5A `finish(owner, terminal=...)`, so the C5A segment/terminal grammar cannot be bypassed through the public adapter.
- Prior HIGH-2 **CLOSED**: `admit()` now binds `capability.source_identity == f"{segment_id}:{capability.source_timestep}"` and has mismatch/invalid-coordinate fixtures.
- Public batch loss now uses the returned `materialize_many()` output instead of private `_pending_by_owner` witnesses; permutation-value and row-mismatch fixtures were added.
- Child remediation changes only `c6_runtime_adapter.py` and `c6_runtime_adapter_test.py`; no active Cosmos/runtime/config/GPU/training scope drift found.

## Remaining blocker

1. **HIGH — C6 adapter-level acceptance Evidence is still incomplete.**
   - File: `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py:29-138`.
   - Current C6 tests now cover basic shape, two N=1 segments, pending reset, no-pending done/reset, public permutation, one N=3 short-nonterminal rejection + terminal r=1/r=0, identity mismatch, skip/replay/changed-byte and row mismatch.
   - Still missing from the frozen C6 seam matrix: successful fresh-epoch same owner/identity/timestep=0 re-admission after reset; pending `done` rejection with snapshot/epoch invariance; unrelated/grad-free/partial-owner segment-loss rejection; abort and backward-failure exact rollback through the public adapter; Local-disabled parity; and public-seam N=1/3/16 plus terminal `r=0`, `0<r<N`, `r=N` matrix / N>1 shape-gradient evidence.
   - Root cause: the submission relies on the delegated C5A 36-test regression for several behaviors that the frozen C6 v0.2 §4/§6 explicitly requires to be reproduced/proven at the adapter seam.
   - Acceptance: add tests-only public-API C6 fixtures for the missing cases above; no production-code change is required unless stronger fixtures expose one. Re-run C5A + expanded C6 selector, `py_compile`, and child/root `git diff --check`, reporting exact counts.

## Scope

Allowed remediation is tests-only in the C6 synthetic adapter boundary plus root review/status bookkeeping. Active Cosmos runtime, config/optimizer/checkpoint, attention/packing, GPU/CUDA/torchrun, real I/O, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1 remain prohibited.
