# Independent Re-review — R09-B TTT v0.3.2 C5 fast-state transition CPU remediation

- Gate: `G0-R09-B-TTT-V032-C5-FAST-STATE-TRANSITION-IMPLEMENTATION`
- Requested token: `APPROVE_TO_CLOSE_R09_B_TTT_V032_C5_FAST_STATE_TRANSITION_CPU`
- Root implementation/remediation SHA: `0c5b3d253a7a06bff804f41fc8915e1063ae5ab3`
- Child/Gitlink: `6de8f2056c62cb10c89791d70335a44a6ab232fc`
- Request/ledger SHA observed at review start: `1e12ac58b66c2c4cc954dcb7c1d4131aa715c8a5`
- Approved design SHA: `d0f29f31cc223284769d726239e0ec71a59a484c`
- Prior ChatGPT implementation review: `627cf2bfadf19f720f13ac86a41cf1834319c7fb` (`REQUEST_CHANGES`, one HIGH)

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. Remote `V2` was resolved through the connected GitHub API. At review start and immediately before writing this review, remote `V2` HEAD was request/ledger SHA `1e12ac58b66c2c4cc954dcb7c1d4131aa715c8a5`, whose parent is exactly the remediation root `0c5b3d253a7a06bff804f41fc8915e1063ae5ab3`.

The root target points the `cosmos-framework` Gitlink exactly to `6de8f2056c62cb10c89791d70335a44a6ab232fc`. Compared with the previously reviewed child `4e34690af2e194104b4c10142d28edf88e8c5faf`, the remediation is exactly one commit ahead and modifies only `cosmos_framework/model/generator/mot/local_evidence_test.py` (+132/-10). Production `local_evidence.py` is unchanged. Root status changes are limited to `SESSION.md`, `TODO.md`, and the Gitlink update.

GitHub exposes no combined-status/check evidence for either the root remediation SHA or child remediation SHA. The submitted `36 passed`, two-file `py_compile`, and root/child `git diff --check` results are repository-recorded evidence and were not independently rerun in this environment.

## Technical verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V032_C5_FAST_STATE_TRANSITION_CPU`

The prior HIGH is closed. No new production-code blocker or scope drift was found.

## Closure of prior HIGH-1

Prior HIGH-1 required transition-level behavioral evidence for the wrapper-owned TBPTT/reset/counter contract rather than value-only assertions. The new child remediation supplies the missing evidence:

1. **Row-selective graph boundary** — `test_continual_ttt_transition_row_selective_detach_preserves_current_token_gradients` uses a mixed batch where one row reaches the N-th valid transition and the other does not. It compares returned carry numerically against the direct core update, then interrogates autograd reachability: detached-row returned carry has no gradient path to pre-boundary state while the non-boundary row retains a finite/nonzero live path.
2. **Read-before-detach / slow-gradient path** — the boundary-step token is differentiated against all registered core slow parameters and requires finite/nonzero gradients. Thus the current token is computed from the updated state before carry-state detachment.
3. **N=1 semantics** — a dedicated fixture compares the wrapper token and numerical state against direct `core.step_many()`, requires `counter_out==0`, and proves each returned carry tensor is graph-detached from learned W0.
4. **N matrix** — exact counter progression/reset is exercised for non-default `N=3` and default `N=16`, with the returned state continuously carried into subsequent calls.
5. **Counter/init fail-before-core** — negative, `>=N`, wrong dtype, wrong shape, wrong device, and `state_in=None + nonzero counter` all raise before a monkeypatched `core.step_many()` can execute; observed core-call count must remain zero.
6. **Done/invalid isolation** — a reset+invalid row returns exact learned W0/counter0/zero-token/present=false, while an untouched invalid row preserves its incoming state and counter exactly.
7. **Wrapper ownership** — `runtime.named_parameters()` is required to equal only the prefixed slow parameters of `core`; fast state remains explicit input/output data rather than registered parameters.

These directly address the prior review acceptance matrix. The earlier vacuous `torch.equal(x, x.detach())` assertion is removed.

## Accepted production contract retained

The production wrapper remains byte-identical to the prior reviewed implementation and still matches the approved C5 v0.2 design:

- one already-admitted causal transition only; no chronology/provenance authority claim;
- exact `counter_in:[B] int64` grammar with `0 <= c < N` and init-zero requirement;
- whole-row learned-W0 reset before transition;
- invalid row performs no write/read and preserves post-reset carry semantics;
- exactly one `core.step_many()` update/read call for valid rows;
- N-th valid transition computes the current token before row-selective carry detach, then resets that row's counter to zero;
- runtime fast state is external data, not an optimizer/checkpoint parameter surface.

## Scope boundary

This approval closes **only C5 single-transition synthetic CPU contract**. It does **not** authorize or close `C5A-CHRONOLOGY-OWNER-SEGMENT-DESIGN` and does not provide episode/rollout owner identity, transition/segment chronology, retry/replay semantics, state-owner binding, trainer segment materialization, or backward atomicity.

Still prohibited without separate frozen design + same-SHA approval:

- C5A production/runtime implementation;
- C6/C7/C8/C9;
- model/packer/attention/config/optimizer/checkpoint/trainer/inference/parallelization changes;
- native `MemoryState` mixing;
- GPU/CUDA/torchrun;
- real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- P4/P5 real operations;
- B2-T or LIBERO4IN1 training.

## Persistence status

Detailed review is persisted by this file. The canonical live `docs/collab/chatgpt/CODEX_INBOX.md` is append-only and the available GitHub connector exposes whole-file replacement rather than a server-side append primitive. I did not rewrite/regenerate the live Inbox because byte-for-byte safe append was not established in this environment.

Therefore the **technical verdict is approval**, but under the project persistence rule this review must be reported as **“未形成正式 verdict”** until the matching live Inbox handoff is safely appended.
