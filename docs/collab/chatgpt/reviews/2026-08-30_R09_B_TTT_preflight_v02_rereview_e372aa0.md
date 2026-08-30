# ChatGPT Review — R09-B TTT B0 preflight v0.2 re-review

- Date: 2026-08-30
- Reviewer: ChatGPT
- Rectification root: `e372aa009652209c94ec7c4552a8ff9aaf00e96e`
- Review-request commit: `3b26bca9bdba8438eedd81fdcc010754764d15c8`
- Current remote review-state commit: `75e4e89358c78c85635709a26d03ffd5b90c8e9a`
- Submodule/Gitlink: `c0287e215f265134cb8b8d947de7eb398f0246cf`
- Reviewed file: `docs/build/PSM-WMA_R09_B_TTT_preflight_runbook_v0.2_2026-08-30.md`
- Verdict: **APPROVE_TO_ADVANCE_B0_SOURCE_AUDIT**

## Closure of prior ChatGPT blockers

The three blockers from
`docs/collab/chatgpt/reviews/2026-08-30_R09_B_TTT_preflight_v02_2c424c67.md`
are closed.

### 1. segment / inner semantics — CLOSED

The runbook now defines `segment_steps` over the causal evidence axis `H` inside one sample/window.

It explicitly freezes:

- `state_start=zeros` for every sample/window;
- state carry only across explicit replay segments inside that sample/window;
- a final short tail segment is allowed;
- no `segment_steps >= inner_steps` requirement;
- no hidden carry across outer trainer/policy/control forwards;
- any future outer-forward persistence requires a separate later Gate.

This is the correct B0 boundary.

### 2. backend optimizer namespace — CLOSED

The runbook now preserves the backend-agnostic A1 optimizer namespace:

```text
local_history_runtime.encoder.*
local_history_runtime.recurrent_backend.*
local_memory2llm.*
local_memory_modality_embed
```

The current GRU-specific `.cell.*` leaf layout is no longer promoted into the design contract.

Default remains zero newly introduced slow learned parameters. Any later exception must enumerate exact names/counts and prove every slow parameter remains inside the existing four A1 selection prefixes; no fifth optimizer key is permitted.

### 3. machine-readable contract / provenance — CLOSED

The schema now explicitly records the frozen assertions required for B0:

- deterministic;
- finite;
- fast-state update;
- masked-timestep inertness;
- padding inertness;
- all-mask absence;
- batch-permutation isolation;
- cross-sample isolation;
- partial reset;
- full reset;
- boundary isolation;
- boundary zero/reinitialization;
- segment present equality;
- detach value exact;
- graph detached;
- exclusion from named parameters;
- exclusion from optimizer;
- exclusion from checkpoint.

Segment equivalence now includes state/token max-abs diffs, tolerance and a pass field.

Provenance now includes:

- root/submodule/Gitlink;
- root/submodule clean;
- Gitlink==submodule;
- argv/cwd/python/output;
- canonical command hash;
- tool SHA256.

Concrete tolerance/value choices remain correctly deferred to source audit rather than being silently frozen in preflight.

## Scope audit

The rectification range from the previously reviewed content to `e372aa0` contains only runbook/schema and review/governance documentation changes. It does not modify Cosmos runtime, model, optimizer configuration, dataset, training code, or submodule source.

RoboTTT remains algorithm-reference-only:

- no RoboTTT implementation import;
- no dependency/package import;
- no shared-MoT structural adoption;
- no runtime wiring.

MM and Kimi have also recorded `APPROVE_TO_ADVANCE_B0_SOURCE_AUDIT` for the same rectified object. Their noted tolerance/slow-parameter/boundary-init points are appropriate source-audit details and are non-blocking at this preflight gate.

## Authorized next step

**APPROVE_TO_ADVANCE_B0_SOURCE_AUDIT**

The authorized next step is read-only/source-design work only.

The B0 source-audit request must freeze, before implementation:

1. exact fast-weight parametrization;
2. exact update rule;
3. exact inner objective;
4. exact inner_steps;
5. exact segment_steps;
6. exact fast-state dtype;
7. exact fast-state byte limit;
8. exact slow learned parameter policy;
9. exact implementation symbols and file:line locations;
10. exact CPU test symbols/locations;
11. concrete numerical tolerance(s);
12. exact state shape/bytes formula;
13. A/B matched implications for parameter count, Local token budget, history schema, losses and optimizer scope.

Source audit may inspect and propose; it may not implement the TTT backend yet.

A separate three-way request for:

```text
APPROVE_TO_IMPLEMENT_B0
```

is still required before any B0 code or CPU contract execution.

## Still blocked

- TTT backend implementation;
- CPU contract execution;
- runtime wiring;
- GPU / A1-style smoke;
- multi-GPU;
- long training;
- matched SR;
- backend freeze;
- RoboTTT/shared-MoT code import;
- Global / Agent / RL.
