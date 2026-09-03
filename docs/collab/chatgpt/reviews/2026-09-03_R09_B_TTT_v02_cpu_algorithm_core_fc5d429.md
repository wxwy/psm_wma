# ChatGPT Independent Review — R09-B Continual TTT CPU Algorithm Core @ fc5d429

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V02-CPU-ALGORITHM-IMPLEMENTATION`

## 1. Review identity

- **root implementation SHA under verdict:** `fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312`
- **Cosmos child implementation SHA / root Gitlink:** `cf52f43dc328d4c8eec51923d66835125664dee5`
- **request/ledger SHA observed on `V2`:** `5577dadf822ead9df3df3b9806f0cb70200b2174`
- **approved route/design state:** `af9caf0cfffbb70b7fbf2e8bc3f763bf9bd9d1a2`
- **CPU-core design:** `docs/build/PSM-WMA_R09_B_TTT_CPU_algorithm_implementation_design_v0.1_2026-09-03.md`
- **v0.3.1 architecture authority:** `4754f5bc25859894e6fc963a9484640ccb5cd082`

The current remote `V2` head at the final pre-write check was `5577dad...`; it is exactly one ledger/request commit ahead of `fc5d429...` and changes only `docs/collab/chatgpt/CODEX_INBOX.md`. The verdict is therefore bound to the implementation SHA `fc5d429...`, not to the ledger SHA.

The required literal `git fetch origin V2` was attempted in a temporary local repository, but this execution environment still cannot resolve `github.com` (`Could not resolve host`). Remote freshness, ancestry, exact Gitlink, and child branch state were independently rechecked through the connected GitHub repository interface. No claim is made that shell fetch succeeded.

## 2. Verdict

**APPROVE_TO_CLOSE_R09_B_TTT_V02_CPU_ALGORITHM_CORE**

No HIGH or MEDIUM blocker was found.

This approval is valid only for root `fc5d4296b2d0e48dad37d7e9f7fd02e9b6cc1312` with `cosmos-framework@cf52f43dc328d4c8eec51923d66835125664dee5`.

## 3. Scope / provenance closure

The root implementation is one commit ahead of the prior ChatGPT route/design review ledger `3832906...` and changes only:

- `SESSION.md`;
- `TODO.md`;
- the `cosmos-framework` Gitlink.

The child commit `cf52f43...` is one commit ahead of the prior Gitlink `21d064f2...` and changes only the two files authorized by the design:

- `cosmos_framework/model/generator/mot/local_evidence.py`;
- `cosmos_framework/model/generator/mot/local_evidence_test.py`.

The production `LocalHistoryRuntime`, model construction, config/recipe, optimizer selectors, packer, trainer/loss, action server, closed-loop client, and Memory Prefix attention path are not modified by this implementation.

## 4. Functional / mathematical review

The implementation matches the approved CPU-core contract:

1. `ContinualTTTFastState` contains exactly four members: fast-in weight/bias and fast-out weight/bias.
2. `ContinualTTTLocalMemoryCore` registers only Q/K/V projections plus the four learned W0 tensors. The frozen defaults remain `D_e=256`, `D_local=32`, `D_ttt=64`, `D_ff=128`, `inner_lr=0.1`, and `ttt_tbptt_steps=16`.
3. W0 initialization follows the frozen two-layer `nn.Linear`-equivalent Kaiming/bias bounds and does not use the degenerate all-zero initialization.
4. `initial_state()` expands/clones learned W0 per sample without detach, preserving the slow-W0 autograd path and independent storage.
5. `project_evidence()` performs K/Q/V projection in fp32 while retaining gradient flow through casts.
6. `step_projected()` computes an independent per-sample feature-mean KVB loss, calls `autograd.grad` over all four fast-state members, performs one simultaneous SGD update, and reads the Local token with the updated state.
7. No batch or valid-count reduction enters the inner update, so neighboring samples do not scale or couple the fast update.
8. Invalid rows perform no inner gradient or readout, return an exact-zero token / `present=false`, and numerically preserve all four state members.
9. State updates are functional rather than in-place; valid state is cast back to the input storage dtype without detach.
10. `step()` delegates to the single `project_evidence() + step_projected()` implementation; no second update rule exists.
11. `scan_segment()` advances in exact chronology order and fails closed when `T > ttt_tbptt_steps`; it does not reset, detach, backward, or optimizer-step internally.
12. `reset_mask()` restores the complete learned W0 only for done rows; `detach_state()` cuts the graph while preserving state values.
13. `create_graph=True` retains the higher-order path required for K/V meta-gradient; `create_graph=False` is numerically equivalent for the forward/update result and is not misrepresented as a slow-parameter-free inference policy.
14. The implementation fails under outer `no_grad` / `inference_mode` before update work, preserving the later W-only inference boundary contract.
15. The default fast-state payload remains 12,448 elements/sample and the registered slow count remains 53,568 elements, matching the design.

I found no mathematical drift from the approved v0.2.1 CPU-core design and no contradiction with the later v0.3.1 K/V-only Memory Prefix architecture. The CPU core remains backbone-independent; `scan_segment [B,T,32]` is correctly only a chronological training/reference return, not a claim that the Cosmos attention path receives T simultaneous Memory tokens.

## 5. C01–C16 test-contract review

The adjacent implementation tests cover the frozen contract set C01–C16, including:

- constructor validation and configurable TBPTT length;
- exact parameter registry/state-dict and 53,568 slow-element count;
- independent initial storage plus W0 gradient path;
- manual one-step KVB/update/read equivalence;
- batch independence;
- exact invalid-row inertia;
- complete per-sample reset;
- detach value preservation / graph cut;
- `scan_segment` versus repeated `step()` equivalence;
- detached carry rebuilding a new graph without numerical reset and TBPTT-length invariance;
- invalid/nonfinite/dtype/device/shape fail-closed checks;
- outer gradient reaching K/Q/V and W0 with nonzero deterministic coverage;
- `create_graph` numerical equivalence;
- outer `no_grad` / `inference_mode` rejection;
- `step()` versus projected-step single-math equivalence;
- fast-state element/byte formulas.

Submitted execution evidence reports `16 passed, 8 deselected`, plus `py_compile` and child/root `git diff --check` PASS.

### Environment variance

The originally expected bare interpreter could not collect the test in the implementation workspace because it lacked Torch/OmegaConf and the repository pytest configuration referenced unavailable test infrastructure. The implementation therefore used an already-existing Torch environment and disabled unrelated root pytest addopts/conftest discovery while keeping the exact target test file and `-k continual_ttt` selector.

I do **not** treat this as a closure blocker for this CPU mathematical core because:

- no dependency was installed;
- the tested code and selected contract tests are the exact tracked child files at `cf52f43...`;
- the overrides remove unavailable repository-wide pytest infrastructure rather than alter the algorithm or assertions;
- no model/data/checkpoint/GPU/runtime surface was exercised.

This acceptance does **not** create interpreter/environment authority for later runtime, GPU, training, or inference Gates. Those must use their separately frozen environments and evidence.

## 6. Authorized next step

This verdict closes only `G0-R09-B-TTT-V02-CPU-ALGORITHM-IMPLEMENTATION` and permits the next **documentation-only v0.3.1 exact Memory Prefix source/ABI audit Gate**.

That audit must, among other required items, freeze the exact effective LIBERO two-way config anchor, Memory pre-attention norm ownership/family/eps, K/V projection ownership, Memory position/RoPE semantics, and Memory-present warm-start behavior before any Memory Prefix runtime implementation.

## 7. Still prohibited

This closure does **not** authorize:

- Memory Prefix runtime wiring / attention implementation;
- chronology owner or native outer-loss integration;
- production Local runtime replacement;
- optimizer/config/checkpoint authority refreeze;
- GPU/CUDA/torchrun;
- training, evaluation, inference, or inference smoke;
- P4/P5 real operations;
- B2-T / formal Local Memory training.

Any new implementation/remediation SHA or new child Gitlink requires a fresh same-SHA independent review; this approval must not be reused across later code changes.
