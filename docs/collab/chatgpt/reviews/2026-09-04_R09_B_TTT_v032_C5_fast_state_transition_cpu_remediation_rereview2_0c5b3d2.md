# Independent Re-review #2 — R09-B TTT v0.3.2 C5 fast-state transition CPU remediation

- Gate: `G0-R09-B-TTT-V032-C5-FAST-STATE-TRANSITION-IMPLEMENTATION`
- Requested token: `APPROVE_TO_CLOSE_R09_B_TTT_V032_C5_FAST_STATE_TRANSITION_CPU`
- Formal root implementation/remediation SHA: `0c5b3d253a7a06bff804f41fc8915e1063ae5ab3`
- Formal child/Gitlink: `6de8f2056c62cb10c89791d70335a44a6ab232fc`
- Remote `V2` HEAD independently resolved at re-review start: `f9acc8c74ac5e5c99e8c1d257d3d3f10b8f023d1`
- Approved design authority: `d0f29f31cc223284769d726239e0ec71a59a484c`
- Prior implementation finding authority: `627cf2bfadf19f720f13ac86a41cf1834319c7fb` (`REQUEST_CHANGES`, one HIGH)
- Prior review file at the same formal target was treated as historical context only and its verdict was not reused.

## Repository / identity verification

The connected GitHub repository reports the formal root target `0c5b3d2...` pointing the `cosmos-framework` submodule exactly to `6de8f205...`. The child compare `4e34690... -> 6de8f205...` is exactly one commit ahead and changes only `cosmos_framework/model/generator/mot/local_evidence_test.py` (+132/-10); production `local_evidence.py` is unchanged. Root `0c5b3d2...` updates the Gitlink plus status bookkeeping (`SESSION.md`, `TODO.md`). Current remote `V2` is two bookkeeping/review commits ahead of the formal implementation target; those commits do not replace the target under verdict.

The submitted runtime evidence remains: synthetic CPU selector `36 passed`, two-file `py_compile`, child/root `git diff --check` PASS. This environment could not independently execute the repository test environment, so those command results are accepted as repository-recorded evidence and are not represented as independently rerun evidence.

## Independent technical re-review

### 1. Prior HIGH — CLOSED

The previous HIGH required wrapper-level evidence for the TBPTT/reset/counter contract instead of the vacuous numeric assertion `torch.equal(x, x.detach())`. The remediation now provides direct behavioral/autograd coverage:

- a mixed batch reaches the TBPTT boundary on one row while another row remains live; returned carry is numerically compared with the direct core update, and autograd proves the boundary row has no path to the pre-boundary state while the non-boundary row retains a finite/nonzero path;
- the current boundary-step token is differentiated against all registered core slow parameters and retains finite/nonzero gradients, proving readout happens before carry detachment;
- `N=1` is compared against direct `core.step_many()`, returns the updated readout, resets the counter to zero, and carries a graph-detached numerical state;
- non-default `N=3` and default `N=16` counter progression/reset are exercised through repeated carried-state calls;
- negative counter, `counter>=N`, wrong dtype, wrong shape, wrong device, and `state_in=None` with nonzero counter all fail before a monkeypatched `core.step_many()` can execute;
- reset+invalid isolation proves a done row returns learned W0/counter0/zero-token/absent while an untouched invalid row preserves incoming state and counter;
- `runtime.named_parameters()` is exactly the prefixed slow parameters owned by `core`; fast state stays explicit input/output data rather than a registered optimizer/checkpoint parameter.

### 2. Production contract — still consistent with frozen v0.2 design

Fresh source inspection of `ContinualTTTFastStateTransition.step()` confirms the production ordering remains:

1. validate transition mask/counter grammar;
2. initialize only when `state_in is None`, with zero-counter requirement;
3. row-selective learned-W0 reset using `done_before_t`;
4. exactly one `core.step_many()` call for the admitted transition;
5. valid rows increment the per-row counter;
6. rows reaching the N-th valid transition return the already-computed token, detach only their carry state, then reset only those counters to zero.

This remains a single already-admitted transition transform. It does not claim duplicate/future/provenance/episode ownership authority; those remain explicitly deferred to C5A.

### 3. Scope / drift

No new production-code change or scope drift is present in the remediation. The child delta is test-only. No C5A owner/chronology code, Cosmos forward/packer/attention, config/optimizer/checkpoint/trainer/inference/parallelization, native `MemoryState` mixing, GPU path, or training path is introduced by this formal target.

## Verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V032_C5_FAST_STATE_TRANSITION_CPU`

No blocking finding remains for the frozen C5 single-transition synthetic CPU contract.

## Authority boundary

This approval closes **only** `G0-R09-B-TTT-V032-C5-FAST-STATE-TRANSITION-IMPLEMENTATION` for root `0c5b3d253a7a06bff804f41fc8915e1063ae5ab3` + child `6de8f2056c62cb10c89791d70335a44a6ab232fc`.

It does **not** authorize C5A chronology/owner implementation, C6/C7/C8/C9, model/packer/attention/config/optimizer/checkpoint/trainer/inference/parallelization changes, native `MemoryState` mixing, GPU/CUDA/torchrun, real model/data/cache/checkpoint I/O, training/evaluation/inference, P4/P5 real operations, B2-T, or LIBERO4IN1 training. C5A remains mandatory before those later runtime/training gates.

A matching append-only entry in `docs/collab/chatgpt/CODEX_INBOX.md` is required for this re-review to constitute the project's formal persisted verdict handoff.
