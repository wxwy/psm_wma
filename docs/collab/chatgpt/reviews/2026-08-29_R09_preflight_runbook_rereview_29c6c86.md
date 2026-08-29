# ChatGPT Review — R09 preflight Runbook re-review @ root 29c6c86

- Date: 2026-08-29
- Reviewer: ChatGPT
- Review request: `9a7ae79c3ee18c4744e154ad402da9ebb7615aec`
- Runbook root: `29c6c867c0168c3c21d8f1d7e2ace4366c7ef3e3`
- File: `docs/build/PSM-WMA_R09_preflight_runbook_v0.1_2026-08-29.md`
- Requested scope: authorize **R09-A0 CPU contract only**
- Verdict: **REQUEST_CHANGES**
- A0 implementation / GPU / A1 / R09-B / multi-GPU: **NOT APPROVED**

## Executive summary

The previous major design blockers are largely closed:

- A/B now share one backend protocol and only the temporal compressor is intended to differ;
- per-evidence-step detach is explicitly forbidden;
- two-segment carry + detach is part of A0;
- true Local absence is explicit for all-mask samples;
- mixed-batch presence is required;
- meta -> to_empty -> explicit initialization is now part of A0;
- Stale/Truncated are correctly removed from A0 hard PASS;
- A1 now requires object-level optimizer membership and frozen-parameter no-change evidence;
- the multi-GPU/FSDP block remains visible.

However, one state-management ambiguity remains directly in the A0 contract, and two evidence/acceptance details remain underspecified. These should be fixed in the runbook before implementation so A0 does not repeat the R08 evidence-hardening cycle.

## HIGH — batched reset semantics are still not frozen

Runbook line 8 defines:

`LocalMemoryBackend.step(evidence_t, state_in) -> (state_out, token, local_present)`

and:

`reset(state)`

Line 15 requires `episode reset` and `batch permutation isolation`.

This still does not define **partial reset in a batched/parallel-env state**.

The frozen detailed design requires both:

- episode reset;
- parallel-env isolation.

Those are not fully proven by a global `reset(state)` API. Two implementations can both satisfy the current text while behaving differently:

1. reset the whole batch whenever one env/episode ends;
2. reset only selected batch elements.

Only (2) is compatible with persistent Local state in parallel environments.

### Required fix

Make the common A/B contract explicitly support selected-sample reset, e.g. conceptually:

```text
step(evidence_t, state_in, valid_mask)
    -> state_out, token, local_present

reset(state, reset_mask[B])
    -> reset_state
```

Equivalent APIs are fine, but the semantics must be frozen:

- reset only elements where `reset_mask=true`;
- non-reset batch elements remain numerically unchanged;
- no state sharing across batch elements;
- all-mask/no-valid-evidence is **not** implicitly an episode reset;
- masked/padded evidence leaves state unchanged;
- A0 must include a mixed-batch partial-reset test.

This is the remaining A0 blocker.

## MEDIUM-1 — full-window vs two-segment equivalence has no acceptance tolerance

Line 15 correctly adds:

`full-window 与 two-segment carry+detach 数值等价`

but does not define what “equivalent” means.

Detach should change graph connectivity, not numerical state, so the acceptance rule should be fixed now rather than chosen after results are seen.

### Required fix

Declare one of:

- exact/bitwise equality if the implementation executes the same sequential operations; or
- a fixed numeric tolerance, e.g. `rtol/atol`, chosen before implementation.

The A0 JSON should record:

- final-state max_abs_diff;
- token max_abs_diff;
- chosen rtol/atol;
- PASS boolean.

Also explicitly require that the carried segment-1 state is numerically preserved across `.detach()`.

## MEDIUM-2 — A0 artifact minimum provenance schema is still incomplete

Line 17 currently requires:

- root/Gitlink provenance;
- state shape/bytes;
- init seed/path;
- meta-init result;
- assertion booleans;
- mixed-batch presence;
- full-window/segment equivalence.

This is an improvement, but it does not fully close the previous provenance requirement.

Before implementation, explicitly require at least:

- `schema_version`;
- root revision;
- submodule revision;
- Gitlink revision;
- root tracked-clean status;
- submodule tracked-clean status;
- backend name;
- state shape, **dtype**, bytes;
- input/output shapes;
- trainable parameter count / parameter-prefix list for A0 module;
- init seed and initialization path;
- each named assertion as a machine boolean;
- mixed-batch local_present result;
- partial-reset result;
- segment-equivalence deltas/tolerance;
- verifier/test tool SHA or command/hash equivalent.

This is CPU-only evidence schema work, not an algorithm change.

## LOW — freeze the exact A1 trainable prefixes before A1 approval

Line 21 is much better because it requires an object-level allowlist and frozen parameters to be absent from the optimizer and unchanged after step.

But `Local adapter` is still descriptive rather than exact.

Before A1—not necessarily before A0 implementation—freeze the actual production parameter prefixes/objects. The known R07 adapter boundary is:

- `local_memory2llm`;
- `local_memory_modality_embed`.

The A1 allowlist should similarly enumerate:

- LocalEvidenceEncoder if intentionally trainable;
- R09 recurrent compressor;
- Local readout if intentionally trainable;
- `local_memory2llm`;
- `local_memory_modality_embed`.

Do not let “Local adapter” accidentally widen to native Action/state/other adapters.

This item may be closed during A0 review before authorizing A1.

## Accepted closures from the previous review

### Common A/B persistence contract — mostly closed

The runbook now explicitly says A/B share the same `step/state/reset` protocol and B only replaces the temporal compressor.

It also says:

- sample/window starts from zero in the first smoke;
- two segments carry numerical state;
- graph detach occurs only at segment boundaries;
- no per-evidence-step detach;
- reset occurs at sample/episode boundary.

Once selected-sample reset is made explicit, this HIGH is fully closed.

### True all-mask Local absence — closed

Line 15 now requires:

- valid sample -> exactly one packable Local token;
- all-mask sample -> genuinely absent/not packed;
- mixed batch evidence.

This correctly preserves the R07/R08 absence semantics.

### Production initialization lifecycle — closed

Line 17 explicitly covers:

`meta -> to_empty -> fixed-seed explicit init`

or an audited post-materialization attach path, plus finite/deterministic parameter assertions.

### A1 freeze semantics — materially improved

Line 21 now requires:

- object-level optimizer allowlist;
- frozen params excluded from optimizer;
- per-parameter before/after no-change proof.

This closes the previous “grad==0 is enough” problem.

### Detach semantics — closed

The runbook explicitly forbids detach on every evidence step and allows it only at segment boundaries.

### Stale/Truncated — closed for A0

They are correctly deferred until the intervention boundary is precisely defined.

### Multi-GPU block — closed

The runbook retains the DCP-MULTIRANK + dedicated FSDP/local-state smoke block before any multi-GPU R09 execution.

## Required next action

Edit **only the runbook/status docs**.

Do not implement A0 yet.

Minimum change:

1. freeze per-sample `reset_mask` semantics and add mixed-batch partial-reset assertion;
2. freeze segment-equivalence tolerance and artifact delta fields;
3. complete the explicit A0 artifact/provenance schema above.

Then resubmit for:

**APPROVE_TO_ADVANCE_A0**

No GPU, A1, B, multi-GPU, long training, matched SR, or backend freeze.

## Verdict

**REQUEST_CHANGES**
