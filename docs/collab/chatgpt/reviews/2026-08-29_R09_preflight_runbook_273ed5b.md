# ChatGPT Review — R09 preflight Runbook v0.1 @ root 273ed5b / plan faa6b64

- Date: 2026-08-29
- Reviewer: ChatGPT
- Review request root: `273ed5b18f058c79ce8e4ee49da1198c9f6ba9fd`
- Runbook commit: `faa6b64d3110f820c39d7cb1fe9f73250912a454`
- File: `docs/build/PSM-WMA_R09_preflight_runbook_v0.1_2026-08-29.md`
- Requested scope: authorize **R09-A0 CPU contract only**
- Verdict: **REQUEST_CHANGES**
- GPU / A1 / R09-B / multi-GPU / matched SR / backend freeze: **NOT APPROVED**

## Executive summary

The overall sequencing is correct and should be preserved:

```text
R08 Gate B closed
-> R09-A0 CPU contract
-> independent review
-> R09-A1 single-GPU smoke
-> independent review
-> R09-B TTT proposal/review
```

The runbook also correctly keeps R09 out of shared Cosmos MoT, preserves the R08 evidence boundary, and forbids premature matched-SR/backend-freeze work.

However, the current 27-line plan leaves several state semantics ambiguous enough that two compliant implementations could implement materially different algorithms. The largest issue is that Backend A is currently window-local while Backend B is specified with cross-segment state carry, which breaks the promised single-variable backend comparison.

This is a runbook problem only. No code/GPU work is needed to close it.

## HIGH-1 — Backend A/B do not currently share the same persistence contract

Runbook `:8-9` defines A as:

```text
sample-internal window replay
M_start=zeros
no cross batch/worker/episode state carry
```

while `:23` gives B an additional contract:

```text
fast state actually updates through the episode
segment boundary value continuity
autograd detach at segment boundary
```

At the same time `:23` says B should **only replace A's temporal compressor**.

Those statements are inconsistent: B would change both:

1. compressor mechanism (`recurrent_latent` -> `ttt_fast_weight`), and
2. persistence/state-carry semantics (window-local -> segment-carried).

The frozen detailed design already treats recurrent and fast-weight state under a common hard state-management contract (`docs/build/PSM-WMA_02_detailed_design_v2.1_frozen.md:381-405`): episode reset, parallel-env isolation, segment detach, runtime/checkpoint separation, and persistent inference update apply to both backend families.

### Required runbook fix

Add a **common LocalMemoryBackend state contract** in A0 that both A and B must implement, even if the first A0/A1 execution uses only zero-initialized sample-local replay.

Conceptually:

```text
(evidence[B,H,D_e], mask[B,H], state_in, reset_mask)
    -> state_out
    -> Local readout
    -> local_present / optional Local token
```

Required semantics:

- chronological update only on valid mask positions;
- masked/padded positions leave state unchanged;
- reset applies only to selected sample/episode state;
- `state_in=zeros` is the A0 default, not the permanent architecture;
- state value may carry across a segment boundary;
- detach changes the autograd graph, not the numerical state value;
- no state sharing across batch elements/envs.

Add a CPU two-segment equivalence diagnostic:

```text
full replay over [0:H]
vs
segment-1 -> state_out.detach() -> segment-2
```

with dropout disabled and identical slow weights. The final forward state/value must match within a declared tolerance; detach is allowed to change gradients only.

Then keep A/B fair:

- either both A and B are evaluated with the same segment-carry protocol;
- or both first backend-selection smokes are explicitly window-local and persistent carry is introduced only after the A/B choice.

Do not let B alone receive a stronger persistence mechanism.

## HIGH-2 — `tokens[B,1,D_local]` conflicts with true all-mask absence

Runbook `:15` simultaneously specifies:

```text
output tokens[B,1,D_local]
all-mask absent
```

These are not equivalent under the existing R07/R08 Local path.

A zero Local tensor is **not** true absence because `local_memory2llm` bias / modality embedding can make a zero input produce a nonzero packed Local condition.

### Required runbook fix

Make per-sample presence explicit in the A0 contract, e.g. conceptually:

```text
state_out
local_tokens
local_present[B]
```

or an equivalent optional-token representation.

For a mixed batch:

```text
sample 0: valid history -> exactly one Local token
sample 1: all-mask      -> Local truly absent / not packed
```

Required assertions:

- all-mask sample does not enter Local packing;
- all-mask does not become a zero token;
- if state_in exists and no reset is requested, an all-mask update leaves state unchanged;
- if reset is requested, state follows the explicitly defined reset semantics;
- padding masked timesteps never alter state.

This should reuse the R08 meaning of true absence rather than inventing a new convention.

## HIGH-3 — new recurrent module needs production initialization lifecycle in A0

R08 already exposed a real failure mode where a module constructed under:

```text
meta device
-> to_empty(device)
```

could have uninitialized storage unless it received explicit R08 initialization after materialization.

R09-A introduces another trainable module under the Local runtime path, but the runbook does not require this lifecycle to be tested.

### Required runbook fix

A0 must state how the recurrent compressor is materialized and initialized.

If it is created inside the normal `net` meta-device lifecycle, require a CPU regression equivalent to:

```text
construct on meta
-> to_empty(cpu)
-> explicit init/reset_parameters
-> all params finite
-> fixed seed gives elementwise-identical params
```

If it is deliberately attached only after materialization, require an equivalent test proving correct device/dtype/init and save/load registration.

Do not approve A1 until this is proven.

## MEDIUM-1 — A1 freeze/optimizer criterion is too weak

Runbook `:19` says:

`冻结 Cosmos gradients=0`.

`grad == 0` is not sufficient to prove freezing. A parameter can remain in the optimizer and still change through weight decay / optimizer state even with a zero gradient.

### Required wording for the future A1 gate

Pin an exact trainable allowlist and verify **real optimizer object membership**.

For example, the intended Local-only scope should explicitly name:

- `LocalEvidenceEncoder` if intentionally trainable;
- recurrent compressor;
- Local readout;
- R07 `local_memory2llm`;
- R07 `local_memory_modality_embed`.

`adapter` must not ambiguously include native Action/state/other adapters.

For frozen Cosmos/shared-MoT/native heads require:

```text
not in optimizer param groups
AND no trainable grad path expected
AND parameter values unchanged after optimizer.step()
```

Prefer `grad is None` for `requires_grad=False` parameters rather than demanding a zero tensor.

## MEDIUM-2 — `detach/reset every step` is ambiguous

Runbook `:19` says `每 step 对 state detach/reset 记录`.

This can be misread as detaching the recurrent state after every historical evidence timestep, which would destroy temporal BPTT inside the H-step replay.

Clarify the boundary:

- **evidence timestep inside one replay window:** no detach unless a deliberately defined TBPTT boundary is reached;
- **segment boundary:** carry numerical state, detach graph;
- **episode/reset mask:** reset state;
- **independent sample-local A0/A1 smoke:** initialize/reset once at sample start, not after every evidence item;
- **optimizer step:** logging may record state lifecycle, but optimizer-step count is not itself the recurrent reset semantic.

## MEDIUM-3 — Stale / Truncated interventions are named but undefined

Runbook `:15` requires `Normal/Zero/Shuffle/Stale/Truncated`, but at the R09 handoff the main model input is already encoded `evidence[B,H,D_e]`.

`Stale` in particular can mean several different things:

- use older historical evidence;
- change age/dt metadata;
- shift the whole history window;
- replace the newest valid item with an older one.

These are not equivalent because age/dt have already contributed to R08 evidence encoding.

### Required fix

Either define exact transformations at the `LocalEvidenceBatch` boundary, or remove Stale/Truncated from A0 hard PASS and defer them to the later intervention gate.

For A0 minimal contract, Normal/Zero/Shuffle + H=0/all-mask + mixed-batch + segment split is sufficient if Stale/Truncated semantics are not yet frozen.

## MEDIUM-4 — A0 artifact contract needs minimum provenance fields

`artifacts/g0/r09/a0_contract.json` is named but its minimum content is not defined.

Require at least:

- schema version;
- root/submodule/Gitlink revisions;
- tracked-clean status;
- backend name;
- state shape/dtype/bytes;
- input/output shapes;
- parameter count and initialization seed/path;
- each named A0 assertion as a machine boolean;
- mixed-batch Local presence result;
- meta/materialization initialization result;
- test command/tool hash or equivalent provenance.

This avoids repeating the provenance-hardening cycle from R08.

## LOW — preserve the known multi-GPU block explicitly

The runbook correctly bans multi-GPU for now.

Add one sentence that A0/A1 approval does **not** waive:

- `DCP-MULTIRANK-RELOAD`, and
- the previously identified dedicated multi-rank/FSDP smoke for Local runtime/backend state and direct-child invocation.

This is not an A0 blocker, but it should remain visible before any later `world_size > 1` R09 training.

## What is already approved in principle

Do not change these good decisions:

- R08 `LocalEvidenceBatch` is the only temporal-data handoff;
- no re-read/re-alignment of raw RGB/parquet;
- no Global / Agent / RL;
- no shared-MoT TTT insertion;
- R08 encoder and Local token budget stay fixed during backend comparison;
- A before B;
- A0 CPU before A1 GPU;
- B requires a separate review;
- matched SR only after backend freeze;
- backend choice based on sensitivity/stability/state cost/VRAM/latency, not a tiny SR run.

## Required next action

Update only the runbook (and TODO/SESSION status text if needed).

No implementation, tests, GPU, training, or submodule code changes are authorized yet.

After the runbook explicitly closes the common state contract, true-absence contract, initialization lifecycle, and the narrower wording issues above, resubmit for:

**APPROVE_TO_ADVANCE_A0**.

## Verdict

**REQUEST_CHANGES**