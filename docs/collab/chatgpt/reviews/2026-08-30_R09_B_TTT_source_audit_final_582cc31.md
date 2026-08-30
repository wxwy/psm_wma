# ChatGPT Review — R09-B TTT B0 tail/schema final re-review

- Date: 2026-08-30
- Reviewer: ChatGPT
- Rectification root: `582cc31fcb42f81bf505dc239449f79b6beb29df`
- Re-review request: `9975f00fa13c03464b446b1f45ca539f7b2cd8eb`
- Submodule/Gitlink: `c0287e215f265134cb8b8d947de7eb398f0246cf`
- Reviewed file: `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.1_2026-08-30.md`
- Verdict: **APPROVE_TO_IMPLEMENT_B0**

## Scope/provenance check

`65ff180 -> 582cc31` changes only the source-audit / TODO / SESSION governance documents. The Cosmos submodule Gitlink remains exactly `c0287e215f265134cb8b8d947de7eb398f0246cf`. No TTT backend, CPU contract, production runtime, optimizer, dataflow or GPU code has been executed or introduced by the reviewed rectification.

## Closure of the last two blockers

### 1. Terminal remainder semantics — CLOSED

The source audit now chooses the previously allowed **Option A** and removes the ambiguous short-tail wording:

- `segment_steps=4` means only a complete group of four valid evidence timesteps is an update segment;
- a terminal `N_valid mod 4` remainder of 1–3 valid timesteps is a **pending terminal remainder**, not an update segment;
- it never updates `W` and there is no B0 finalize API;
- ordinary `replay()` call boundaries never finalize;
- the exact inner-update count is `floor(N_valid / 4)`;
- pending remainder still updates `last_evidence`, `initialized/present`, returned state and the final token;
- the CPU contract must cover `N_valid=1,2,3,5,6,7` and check the exact update count.

This preserves call-boundary-independent replay compositionality: arbitrarily splitting the same causal evidence stream does not create extra update boundaries.

Known candidate behavior that must be recorded, not hidden: because `W` starts at zero, `N_valid < 4` produces no inner update, so the content term `W @ last_evidence` is exactly zero while `present=true`. This is accepted as a B0 algorithm choice, not a contract failure. The CPU contract should assert it explicitly for `N_valid=1,2,3`.

### 2. Composite mixed-dtype state artifact — CLOSED

The source audit now freezes per-member state metadata:

- `W`: `[32,256]`, bf16, 16,384 bytes/sample;
- `pending_evidence`: `[4,256]`, bf16, 2,048 bytes/sample;
- `last_evidence`: `[256]`, bf16, 512 bytes/sample;
- `initialized`: scalar bool, 1 byte/sample;
- `segment_progress`: scalar int64, 8 bytes/sample.

Logical tensor payload total is correctly frozen at:

`16,384 + 2,048 + 512 + 1 + 8 = 18,953 bytes/sample`.

The verifier must independently derive each member's bytes as `numel * element_size`, sum them, hard-check `logical_bytes_per_sample == bytes_limit == 18,953`, and require `bytes_limit_pass=true` for PASS. The value is logical tensor payload, not CUDA/allocator footprint.

The new `state.members` structure is sufficient to represent the mixed-dtype composite state. If legacy single `state.shape/dtype/bytes` fields are retained for compatibility, they must not override or substitute for the member-wise verifier checks.

## Previously closed implementation contract retained

The prior five implementation blockers remain closed and are part of this approval:

1. B0 is independent backend + dedicated CPU contract only; no `omni_mot_model.py` production wiring.
2. Inner objective is backend-local and parameter-free: `MSE(W @ e, stopgrad(e[:32]))`.
3. Every complete 4-valid segment uses one pre-update `W`, mean-over-position / mean-over-32 loss and one SGD step at lr=0.1.
4. Inner loop is first-order detached: `create_graph=False`; cached evidence, updated W and returned token/state are detached; native loss does not backpropagate through adaptation into earlier history evidence.
5. Fast runtime state is the five-member composite state above; arbitrary unaligned two-segment replay must be exact-equivalent to one full replay under the same evidence/mask.

## Authorized implementation scope

**APPROVE_TO_IMPLEMENT_B0** is limited to:

- adding an independent `TTTLocalMemoryBackend` at the audited `local_evidence.py` backend location;
- adding the dedicated B0 CPU contract test after the existing recurrent backend tests;
- producing `artifacts/g0/r09/b0_ttt_contract.json` and the minimal verifier/tool needed for that artifact;
- CPU/static execution required to produce and verify the B0 contract.

Hard CPU-contract requirements include:

- fixed-seed deterministic + finite;
- exact `floor(N_valid/4)` update count, including `N_valid=1,2,3,5,6,7`;
- for `N_valid=1,2,3`: W unchanged from zero, `present=true`, terminal remainder preserved, content token `W @ last_evidence` exactly zero;
- `fast_state_updated` for cases with at least four valid positions;
- masked/padding timestep inertness and all-mask absence;
- batch permutation and cross-sample isolation;
- partial/full reset over all five state members;
- boundary zero/reinitialization;
- arbitrary **unaligned** two-segment state/token/present exact equivalence (`tolerance=0.0`);
- detached graph contract;
- no fast state in `named_parameters()`, slow optimizer or checkpoint state;
- member-wise logical state bytes and total 18,953 hard verification;
- root/submodule/Gitlink cleanliness/provenance and command/tool hashes per the frozen B0 schema.

Implementation must stop at REVIEW after the CPU contract. Passing B0 does not authorize production integration.

## Still blocked

- `omni_mot_model.py` / production `LocalHistoryRuntime` TTT wiring (B1);
- GPU / A1-style smoke;
- multi-GPU;
- long training;
- matched SR;
- backend freeze;
- RoboTTT/shared-MoT code import;
- Global / Agent / RL.

Any implementation change to the frozen objective, update rule, segment semantics, state members/bytes, detach semantics or production wiring invalidates this approval and requires re-review.
