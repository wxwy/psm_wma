# ChatGPT Review — R09-B TTT B0 source-audit implementation request

- Date: 2026-08-30
- Reviewer: ChatGPT
- Source-audit root: `02788a1d3cea175fb36cd9076a8eebf7054f87f4`
- Review-request commit: `36df13f25d78fa9861b3b9e9eca4170202b7cd54`
- Current peer-review state: `8613af93ac13e98a96b59dd4abd97cf175818e6a`
- Submodule/Gitlink: `c0287e215f265134cb8b8d947de7eb398f0246cf`
- Reviewed file: `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.1_2026-08-30.md`
- Verdict: **REQUEST_CHANGES**

MM/Kimi peer approvals are noted, but the implementation request is not yet internally consistent with the three-way-approved B0 contract.

## Accepted

The following candidate choices may be retained unless another fix requires changing them:
- per-sample/window fast weight `W[B,32,256]`;
- zero initialization;
- bf16 persistent fast weight;
- per-sample SGD, lr=0.1, no momentum/Adam state;
- `inner_steps=1`;
- `segment_steps=4` over causal evidence axis `H`, shorter tail allowed;
- zero newly introduced slow learned parameters;
- one `[B,1,32]` Local token and unchanged history schema/native losses/A1 optimizer selection keys;
- no RoboTTT/shared-MoT code import.

`32 * 256 * 2 = 16,384` bytes for the **W tensor alone** is correct.

## Blocking findings

### HIGH-1 — proposed B0 implementation includes runtime wiring that the approved preflight forbids

Approved preflight:
- `PSM-WMA_R09_B_TTT_preflight_runbook_v0.2_2026-08-30.md:25` limits B0 implementation to an **independent backend + targeted CPU tests**.
- The same document at `:63` explicitly keeps **runtime wiring** blocked.

But source audit:
- `PSM-WMA_R09_B_TTT_source_audit_v0.1_2026-08-30.md:39` proposes replacing `omni_mot_model.py:309-312` with the TTT backend in the implementation being requested.
- `:45` simultaneously says runtime wiring remains prohibited.

Changing `OmniMoTModel` construction from `RecurrentLocalMemoryBackend` to `TTTLocalMemoryBackend` is production runtime wiring.

Required fix:
- do **not** modify `omni_mot_model.py` in B0;
- instantiate `TTTLocalMemoryBackend` directly in the dedicated CPU contract test;
- keep production `LocalHistoryRuntime` wired to the A1 recurrent backend until a separate B1/runtime-integration review.

### HIGH-2 — frozen inner objective is not implementable through the frozen backend interface

Source audit `:20` freezes `MSE(W @ evidence_t, stopgrad(readout(prefix)_token))`, where the teacher is the existing `StatelessLocalReplayReadout`.

At submodule `c0287e2`, `LocalHistoryRuntime.forward` calls `recurrent_backend.replay(evidence, history_mask)` at `local_evidence.py:244-249`; the backend receives no readout/teacher reference.

Therefore the objective cannot be implemented while simultaneously preserving unchanged `LocalHistoryRuntime.forward`, zero new slow parameters, unchanged replay interface, and no runtime wiring.

Required fix: freeze one implementable option before coding:
1. redefine the inner objective so it is backend-local and parameter-free given only `evidence/mask/state`; or
2. explicitly revise the backend interface/teacher dependency in a new audited contract and account for module registration, optimizer/checkpoint naming, and later B1 runtime integration.

Do not leave teacher access as an implementation detail.

### HIGH-3 — one SGD update per segment is under-specified

Source audit `:20-22` says every valid causal prefix contributes an MSE target, `inner_steps=1`, and there is one update per 4-valid-timestep segment, but it does not define the per-sample segment loss.

Freeze at least:
- sum vs mean over prefix losses;
- MSE reduction over 32 Local dimensions;
- whether all prefix predictions use the same pre-update `W_b`;
- whether the one SGD update occurs only after all valid prefix losses are accumulated;
- zero-valid-position behavior;
- exact fp32/bf16 cast points.

Required fix: write explicit per-sample math/pseudocode for `L_b(segment)`, `g_b`, and `W_b'` including reduction and dtype semantics.

### HIGH-4 — inner-loop autograd / outer-loss semantics are not frozen

The phrase “inner loss is isolated from native vision/action loss” does not say whether the eventual Local token is differentiable through the fast update into earlier history evidence.

Freeze:
- `torch.autograd.grad(..., create_graph=False|True)`;
- whether `W` is detached after each update/segment;
- whether native vision/action loss may backprop through adaptation into earlier evidence;
- whether only teacher targets are stop-grad or the whole inner update is first-order/detached.

This materially changes encoder gradients, graph size, memory, and A/B training semantics. The CPU contract should assert the chosen graph behavior.

### HIGH-5 — the declared state/byte budget cannot satisfy present/reset/two-segment compositionality

Source audit `:24` freezes 16,384 bytes/sample by counting only `W`. But the common backend contract must preserve whether a sample has ever seen valid evidence so `present` survives all-mask continuation and reset. Current A backend stores this explicitly as `initialized` in `local_evidence.py:186-199`.

So `W` alone is not a complete state.

Also, preflight `:27` requires full replay vs two-segment replay state/token/present equivalence. Source audit `:34` narrows this to paths using the same aligned 4-step segmentation. That silently weakens the already-approved contract.

If a replay call splits a logical 4-step update segment at an arbitrary position, one-update-per-4-step semantics require enough state to continue the unfinished segment. `W` alone cannot do this; at minimum segment progress is needed, and depending on the loss implementation an accumulator/buffer may also be required.

Required fix: either
- **Preferred:** preserve call-boundary-independent replay compositionality; expand state schema/byte formula to include `initialized/valid_seen`, segment progress, and required pending accumulator/buffer, then test an unaligned split; or
- issue a new three-way preflight amendment intentionally limiting replay calls to segment-aligned boundaries.

Also distinguish `W_bytes = 16,384 bytes/sample` from total fast runtime state bytes.

## Non-blocking note — A/B parameter matching

A uses a trainable GRUCell while B proposes zero slow backend parameters. This is disclosed, so it does not block B0 once the issues above are closed. Later matched A/B reporting must record this backend slow-parameter difference rather than call parameter count matched.

## Verdict

**REQUEST_CHANGES**

No TTT code or CPU contract execution is authorized yet.

After the five blockers are closed, the next expected verdict can be `APPROVE_TO_IMPLEMENT_B0` for independent `TTTLocalMemoryBackend` code, dedicated CPU contract tests, and the machine-readable B0 artifact/verifier only.

Production `omni_mot_model.py` wiring remains a later B1 gate.

Still blocked: production runtime wiring; GPU/A1-style smoke; multi-GPU; long training; matched SR; backend freeze; RoboTTT/shared-MoT code import; Global/Agent/RL.
