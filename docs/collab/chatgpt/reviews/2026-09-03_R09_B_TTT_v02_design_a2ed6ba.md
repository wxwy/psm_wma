# Independent Design Review — R09-B TTT v0.2 continual fast-weight Local Memory

- Gate: `G0-R09-B-TTT-V02-DESIGN-REVIEW`
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_STATIC_SOURCE_AUDIT`
- Design chain under review: `79dfde1 -> 4975dac -> ede63b0 -> 4f21189 -> a2ed6bac747a4f65868bb4aee5bb7070e083b625`
- Canonical design document: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md`
- Cosmos implementation baseline / Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Current remote V2 observed during review: `c7e65ef2205eee23434a7a292db4cf73bf72e7ca`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. Remote `V2` was resolved through the connected GitHub API.

`a2ed6ba` is an ancestor of the current V2 head. The commits after it only modify P4-v4 log-binding status/design plus ChatGPT Inbox rollover; the TTT v0.2 design file and Cosmos Gitlink did not drift. The Gitlink at `a2ed6ba` is exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

No GitHub status/check-run evidence exists for the design SHA; submitted `git diff --check` is repository-recorded evidence.

## Verdict

`REQUEST_CHANGES`

The architectural correction is substantially right and should be retained: window-local replay is replaced by per-step causal streaming evidence; fast state persists across control timesteps; 16 becomes TBPTT graph-truncation length rather than memory horizon; KVB replaces the artificial `e[:32]` target; learned `Q/K/V` and `W0` become slow parameters; outer Cosmos task loss meta-learns the Local memory update/read rules; inference updates fast state only; and old B2/P3/P4/P5 algorithm-bound authority is explicitly invalidated.

This direction matches the core RoboTTT recipe: KVB fast-weight updates, learned `Q/K/V` and `W0`, fast-state carry during both training and inference, and TBPTT that detaches gradients while preserving fast-state values.

However the current document is not yet mathematically closed enough to authorize a source audit, because one core KVB tensor contract is dimensionally inconsistent and the per-sample update reduction is still implementation-defined.

## HIGH-1 — KVB value dimension conflicts with the declared fast-model output dimension

**File:** `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md:264-315`

The document defines:

```text
K_t = theta_K(e_t)
V_t = theta_V(e_t)
Q_t = theta_Q(e_t)
L_inner,t = || f_W(K_t) - V_t ||^2
```

but later freezes the candidate topology as:

```text
K/Q/V projection: D_e=256 -> D_ttt
fast model f_W: D_ttt -> D_ff -> D_local
D_local = 32
```

Therefore, as written:

- `V_t` has width `D_ttt`;
- `f_W(K_t)` has width `D_local`;
- `D_ttt` is explicitly config-driven/TBD and is not frozen to 32.

The stated KVB loss is thus undefined unless `D_ttt == D_local`, which the design does not require.

### Required fix

Freeze one mathematically complete shape contract before source audit. Two acceptable examples:

**Option A — value lives in Local output space**

```text
theta_K: D_e -> D_ttt
theta_Q: D_e -> D_ttt
theta_V: D_e -> D_local
f_W: D_ttt -> D_ff -> D_local
L_inner,b,t = MSE(f_W(K_b,t), V_b,t)
m_b,t = f_W(Q_b,t) in R^D_local
```

**Option B — fast model stays in TTT space**

```text
theta_K/Q/V: D_e -> D_ttt
f_W: D_ttt -> D_ff -> D_ttt
KVB loss in D_ttt
separate slow readout: D_ttt -> D_local
```

If Option B is chosen, the new readout must be explicitly classified as a slow optimizer/checkpoint parameter and included in the later matched optimizer contract.

Do not leave this choice to implementation/source-audit code.

## HIGH-2 — per-sample KVB update/reduction semantics are not frozen

**File:** `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md:278-284, 868-889`

The v0.2 design correctly requires per-sample/episode state isolation, but the inner update is written only as a scalar `L_inner,t` / generic `mse(...)`. For a batched fast state, a naive `.mean()` over batch and feature axes makes the effective update scale depend on batch size and number of valid samples. That silently changes the inner algorithm when batch packing changes.

The formal contract must be per-sample:

```text
L_inner,b,t = reduction_over_feature_only(...)
g_b,t = d L_inner,b,t / d W_b,t-1
W_b,t = W_b,t-1 - eta_t * g_b,t
```

with:

- no cross-sample gradient coupling;
- invalid/masked sample: no fast-state mutation;
- update scale independent of number of other valid samples in the batch;
- partial reset operates on the complete fast-state pytree for selected samples only;
- any vectorized implementation must be numerically equivalent to the per-sample definition within a frozen tolerance.

The exact feature reduction (`sum` vs `mean`) and its relation to `eta` must be frozen before implementation; otherwise inner LR is not a stable algorithm parameter.

## MEDIUM-1 — sequence outer-loss/noise contract must be explicit before implementation

**File:** `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md:868-892`

RoboTTT sequence training uses per-timestep flow-matching supervision and specifically samples the flow/noise level independently for each action chunk (“sequence action forcing”). The v0.2 pseudocode currently says only:

```text
outer_loss += cosmos_original_loss(...)
```

That is insufficient once a former single-step Cosmos path is transformed into a chronological `[B,T]` training sequence.

The next revision/source-audit contract must explicitly determine and freeze:

1. whether current Cosmos code already samples independent flow/noise timestep and noise per temporal action chunk when the segment is flattened/scanned;
2. if not, the minimal sequence adapter required to make it so;
3. outer-loss normalization over valid supervised timesteps (`sum` vs mean, padding masking, gradient-accumulation interaction);
4. no history/context-only padded timestep contributes native action/future loss unless explicitly intended.

This does not authorize changing Cosmos loss definitions; it freezes how the existing loss is applied over a sequence.

## MEDIUM-2 — inference autograd boundary must distinguish `no_grad` from `inference_mode`

**File:** `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.2.md:890-924`

The design correctly states that inference updates only fast state and freezes all slow parameters. But the implementation contract should explicitly require that the KVB inner update run outside an enclosing `torch.inference_mode()` region (or otherwise use ordinary non-inference tensors). `torch.enable_grad()` is a valid local override for `torch.no_grad()`, but an implementation must not assume it can safely recover the required autograd semantics from an arbitrary enclosing inference-mode path.

Freeze the runtime ordering as:

```text
slow encoder/QKV under frozen/no-slow-grad policy
-> obtain detached normal tensors K/V/Q
-> local fast-state inner update in grad-enabled scope, only W requires grad
-> detach/read Local token
-> Cosmos forward under normal no-grad/inference scope
```

and require a CPU/runtime fixture that starts from the actual production inference call path.

## Accepted design corrections

The following are accepted and should not be rolled back:

1. `runtime_evidence_steps=1` as the logical write contract, with offline `[B,T,...]` only as a training wrapper.
2. One-step causal shift: decision `t` consumes only completed evidence through `t-1`.
3. Fast state persists across the episode and resets only on episode/env/done semantics.
4. `ttt_tbptt_steps=16` means graph truncation only; numerical fast state carries across the boundary.
5. Canonical training requires higher-order/differentiable inner update; `create_graph=False + token/state detach` is historical prototype behavior only.
6. Learned `W0` is a slow parameter; runtime `W_t` is fast state and not Adam/model-checkpoint state.
7. Inference freezes Cosmos/encoder/QKV/W0/Local projection slow weights and updates only `W_t`.
8. TTT stays in the independent clean Local modality branch; no shared-MoT/backbone TTT insertion is introduced by this project.
9. GRU matched baseline must use the same chronological stream, persistent state and TBPTT semantics rather than per-window reset.
10. The old B0/B1 prototype and old B2/P3/P4/P5 optimizer/config authorities are correctly marked superseded/BLOCKED for new training authority.

The current Cosmos baseline independently confirms why the redesign is necessary: `TTTLocalMemoryBackend` still uses `W[32,256]`, `segment_steps=4`, detached evidence/state/token, `create_graph=False`, and `LocalHistoryRuntime.forward()` calls replay without an externally carried state; therefore the old B1 smoke cannot be treated as v0.2 implementation evidence.

## Required next revision

A minimal v0.2.1/design-remediation is sufficient. It does not need implementation code. Before `APPROVE_TO_IMPLEMENT_R09_B_TTT_V02_STATIC_SOURCE_AUDIT`, add/freeze:

1. exact K/Q/V and fast-model/readout dimensions so KVB loss is well-defined;
2. exact per-sample inner loss reduction/update/mask semantics;
3. source-audit checklist for sequence action forcing / outer-loss normalization;
4. source-audit checklist for actual inference `no_grad`/`inference_mode` boundary;
5. source-audit outputs for the full fast-state pytree: member names, shapes, dtype/compute precision, fast-vs-slow classification, learned W0 mapping, state bytes/sample, reset/detach semantics;
6. source-audit outputs for chronological sampler/stream ownership, including grad accumulation, worker/rank ownership and episode-boundary behavior.

Once those are frozen, the design is suitable to advance to a **read-only/static source audit only**. It still must not authorize Cosmos implementation, GPU, training, evaluation, inference smoke, optimizer refreeze, P4/P5 real operation or B2-T.

## Scope

No implementation/GPU/training authority is granted by this review. Existing old B2-T remains BLOCKED. P4/P5 provenance/static machinery may continue independently only where it is algorithm-agnostic; no old TTT backend selector/optimizer/resolved-config authority may be reused for v0.2 training.
