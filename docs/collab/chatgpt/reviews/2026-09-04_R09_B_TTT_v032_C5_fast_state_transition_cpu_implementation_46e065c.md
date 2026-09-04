# Independent Implementation Review — R09-B TTT v0.3.2 C5 fast-state transition CPU

- Gate: `G0-R09-B-TTT-V032-C5-FAST-STATE-TRANSITION-IMPLEMENTATION`
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V032_C5_FAST_STATE_TRANSITION_CPU`
- Root implementation SHA: `46e065c3484823228ed29900fdb3ea032a8e1c27`
- Child/Gitlink: `4e34690af2e194104b4c10142d28edf88e8c5faf`
- Request/ledger SHA observed at review start: `060f88b62155befd0ca044eb424bbb0c0ee714ac`
- Approved design SHA: `d0f29f31cc223284769d726239e0ec71a59a484c`
- Design detailed review commit: `d0599206817b978d385ec271e216bf5b6d004150`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. Remote `V2` was resolved through the connected GitHub API.

At implementation-review start, remote `V2` HEAD was request/ledger SHA `060f88b62155befd0ca044eb424bbb0c0ee714ac`; its parent is exactly root implementation SHA `46e065c3484823228ed29900fdb3ea032a8e1c27`. The root implementation changes the Gitlink from `447f4a61...` to exact child `4e34690a...` and updates root status docs. The child commit changes exactly `cosmos_framework/model/generator/mot/local_evidence.py` and adjacent `local_evidence_test.py`, matching the approved C5 scope. No trainer/config/optimizer/checkpoint/attention/packer/inference/GPU/training scope drift was found.

GitHub exposes no status/check-run evidence for the implementation SHA. The submitted `32 passed`, `py_compile`, and diff-check results are repository-recorded evidence; they were not independently rerun in this environment.

## Verdict

`REQUEST_CHANGES`

The production transition wrapper is structurally consistent with the approved v0.2 state-machine design: it enforces `0 <= counter < N`, init-zero, per-row done reset, one `step_many()` update/read call, row-selective N-th-step detach, and counter reset. I did not find a production-code algorithm blocker in the reviewed delta.

However, the implementation Gate cannot close because the newly added transition-level evidence does not prove the central C5 graph/state-machine acceptance contract. The single new transition fixture contains a vacuous detach assertion and does not cover several explicitly frozen wrapper-level cases. This is best repaired test-only; no production algorithm change is required unless a stronger fixture exposes one.

## HIGH-1 — transition-level acceptance evidence does not prove row-selective TBPTT graph semantics or the frozen counter matrix

**Production:** `cosmos_framework/model/generator/mot/local_evidence.py:616-657`

**Test:** `cosmos_framework/model/generator/mot/local_evidence_test.py:769-787`

### Root cause

The C5 v0.2 design made the wrapper itself responsible for a new state-machine property that the pre-existing `ContinualTTTLocalMemoryCore` tests cannot prove: after the N-th valid transition for one row, the current step's token must still expose the pre-detach outer-gradient path, while the **returned carry state for that row** must no longer connect to the previous segment; non-boundary rows must remain connected.

The only new transition fixture currently checks:

```python
assert all(torch.equal(member[0], member[0].detach()) for member in state2)
```

This assertion is vacuous for graph semantics. `Tensor.detach()` preserves numerical values by definition, so `torch.equal(x, x.detach())` passes whether `x` is connected, detached, or incorrectly left connected. It does not test row-selective autograd truncation at all.

The same fixture uses only `N=2`, checks only one `counter_in == N` negative case, and does not exercise the wrapper-level matrix frozen by the design/request:

- `N=1` read-before-detach + detached carry + zero counter;
- default `N=16`;
- another non-default positive N / consecutive carry;
- selected-row graph detach while another row remains graph-connected;
- current boundary token retains finite/nonzero outer-gradient reachability to the expected slow Q/K/V/slot/W0 path;
- `state_in=None` with nonzero counter rejection;
- negative counter rejection;
- wrong counter shape/dtype/device;
- reset + invalid-row post-reset state/counter isolation;
- fail-before-projection/update for invalid counter/init grammar;
- runtime fast state remains external to `named_parameters()` at the wrapper level.

Existing core tests legitimately cover KVB math, multi-slot post-update reads, K_local=1 compatibility and slow-gradient reachability **inside the core**. They do not establish that the new transition wrapper applies reset/counter/detach in the frozen order and preserves/cuts the graph on the correct rows.

### Required acceptance criteria

A test-only remediation inside `local_evidence_test.py` is sufficient unless a fixture exposes a production bug. Add permanent synthetic CPU transition fixtures that prove at least:

1. **Row-selective graph boundary:** use a mixed batch where one row hits N and another does not. Prove numerically identical state carry, zero/no gradient path from the detached row's returned `state_out` to its pre-boundary state/slow history, and a live finite/nonzero path for the non-boundary row.
2. **Read before detach:** on the boundary step, backpropagate from that step's returned token and prove the expected slow Q/K/V/slot/W0 gradients remain reachable/nonzero; detachment may affect only the returned carry state, not the current token.
3. **N=1:** every valid call returns the updated-read token, numerically updated but graph-detached carry state, and counter zero.
4. **N matrix:** cover default N=16 and at least one non-default positive N with exact counter progression/reset and consecutive state carry.
5. **Counter/init fail-closed:** negative, `>=N`, wrong shape/dtype/device, and `state_in=None + nonzero counter` must fail before projector/`step_many` use. Use a spy/monkeypatch so this is behavioral, not only exception-text coverage.
6. **Done/invalid isolation:** partial `done_before_t` copies the complete row to learned W0/counter0 before transition; an invalid reset row remains W0/counter0 with exact-zero token/present=false; untouched rows remain unchanged.
7. **Wrapper ownership:** demonstrate that runtime fast state is passed/returned data and is not added to `runtime.named_parameters()`; only the core slow parameters are registered.
8. Re-run the exact `local_evidence_test.py` synthetic CPU selector and report the new exact count plus two-file `py_compile` and child/root `git diff --check`.

Do not weaken these checks into value-only comparisons. Graph assertions must directly interrogate autograd reachability/gradients.

## Accepted implementation pieces

The following production behavior is accepted and should be retained unless the stronger tests reveal a concrete defect:

- exact two-file child implementation scope;
- wrapper explicitly documents an already-admitted causal transition rather than claiming chronology provenance;
- `counter_in` exact int64 `[B]` grammar and `0 <= c < N` check;
- `state_in=None -> counter=0`;
- whole-row learned-W0 reset before the transition;
- one call to the already-closed `core.step_many()` for K/V write plus updated-state multi-slot read;
- valid-only counter increment;
- N-th valid row uses `torch.where(..., value.detach(), value)` to create row-selective carry-state truncation while tokens are computed before that detach;
- N-th counter reset to zero;
- no C5A/config/optimizer/checkpoint/trainer/inference/GPU/training scope drift.

## Authority / scope boundary

C5A chronology-owner/segment/backward design remains a hard predecessor of C6/config/checkpoint and of any GPU/training Gate. Closing this implementation later will still **not** authorize stable episode/transition ownership, retry/replay handling, trainer segment materialization/backward atomicity, runtime wiring, GPU, training, evaluation or inference.

Allowed remediation now:
- child `local_evidence_test.py` only unless a new fixture proves `local_evidence.py` requires a minimal correction;
- root status/ledger docs;
- synthetic CPU selector, `py_compile`, `git diff --check`.

Still prohibited:
- C5A production/runtime implementation;
- Cosmos forward/packer/attention/config/optimizer/checkpoint/trainer/inference/parallelization changes;
- native `MemoryState` mixing;
- GPU/CUDA/torchrun;
- real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5 real operations;
- B2-T or LIBERO4IN1 training.