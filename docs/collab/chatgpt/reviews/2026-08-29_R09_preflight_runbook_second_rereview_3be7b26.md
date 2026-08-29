# ChatGPT Review — R09 preflight Runbook second re-review @ root 3be7b26

- Date: 2026-08-29
- Reviewer: ChatGPT
- Runbook root: `3be7b264355d18b47d246e66202af82229f56b88`
- File: `docs/build/PSM-WMA_R09_preflight_runbook_v0.1_2026-08-29.md`
- Requested scope: authorize **R09-A0 CPU contract implementation only**
- Verdict: **APPROVE_TO_ADVANCE_A0**
- GPU / A1 / R09-B / multi-GPU / matched SR / backend freeze: **NOT APPROVED**

## Executive summary

All blockers from the previous two preflight reviews are now sufficiently frozen for A0 implementation.

The runbook now defines a common A/B state-management contract, true Local absence, selective batched reset, segment carry/detach semantics, production initialization lifecycle, a fixed segment-equivalence tolerance, and a sufficiently explicit machine-readable A0 artifact contract.

No further document-only blocker remains for **A0 CPU contract**.

## Closed blocker 1 — common A/B persistence contract

A and B now share:

```text
LocalMemoryBackend.step(evidence_t, state_in)
    -> state_out, token, local_present

reset_mask(state, done[B])
full reset
```

and B is explicitly constrained to replace only the temporal compressor.

The runbook also freezes:

- no implicit state carry across batch/worker/episode in the first smoke;
- zero initial state for sample/window A0;
- two-segment numerical state carry;
- graph detach only at segment boundary;
- no per-evidence-step detach;
- reset only at explicit sample/episode reset.

This is sufficient to keep A/B comparison single-variable at the backend level.

## Closed blocker 2 — batched partial reset / parallel-env isolation

The previous remaining HIGH is closed.

The runbook now explicitly requires:

```text
reset_mask(state, done[B])
```

with:

- only `done=true` samples reset to zero;
- all other samples remain elementwise unchanged;
- all-mask/no-valid-evidence never implicitly triggers reset.

A0 additionally requires mixed-batch partial-reset evidence.

This satisfies the frozen detailed-design requirement for episode reset + parallel-env isolation.

## Closed blocker 3 — true Local absence

A0 explicitly requires:

- valid history sample -> exactly one packable `[1,D_local]` Local token;
- all-mask sample -> truly absent / not packed;
- masked/padded timestep -> no state change;
- mixed-batch presence semantics.

This preserves the R07/R08 meaning of absence and avoids the invalid zero-token substitute.

## Closed blocker 4 — segment carry + detach equivalence acceptance

The runbook now freezes the acceptance criterion before implementation:

```text
max_abs_diff <= 1e-6
```

for both:

- final state;
- Local token.

The carried state value across `.detach()` must be exact before continuing the second segment.

This is an acceptable A0 numerical contract. A0 should record the actual deltas, threshold, and PASS boolean in the artifact.

## Closed blocker 5 — production initialization lifecycle

A0 now explicitly covers:

```text
meta
-> to_empty
-> explicit fixed-seed initialization
```

or an independently audited post-materialization attachment path.

Required evidence includes:

- all intended Local parameters finite;
- same fixed seed -> elementwise-identical parameters;
- initialization path/seed recorded.

This closes the R08-class uninitialized-storage risk before any GPU work.

## Closed blocker 6 — A0 machine-readable evidence contract

`artifacts/g0/r09/a0_contract.json` is now required to include:

- schema version;
- root/submodule/Gitlink;
- both tracked-clean statuses;
- backend name;
- state shape/dtype/bytes;
- input/output shapes;
- trainable parameter count/prefixes;
- init seed/path/meta-init result;
- named assertion booleans;
- mixed presence;
- partial-reset result;
- segment state/token max_abs_diff;
- tolerance and PASS;
- tool/command hash.

This is sufficient for A0. Do not relax these fields during implementation.

## Closed blocker 7 — Stale/Truncated scope

Stale/Truncated are correctly deferred from A0 hard PASS.

A0 only needs the frozen minimal intervention/contract set, including:

- Normal/Zero/Shuffle definitions where needed for module-level behavior;
- H=0/all-mask;
- mixed-batch presence;
- partial reset;
- segment equivalence.

Do not invent Stale/Truncated semantics during A0.

## A1 note — non-blocking for A0

The future A1 trainable scope is materially improved:

- real optimizer object allowlist;
- frozen parameters excluded from optimizer;
- frozen parameters unchanged after optimizer step.

Before authorizing A1, replace the descriptive term `Local adapter` with exact production parameter prefixes/objects.

At minimum the known R07 adapter boundary is:

```text
local_memory2llm
local_memory_modality_embed
```

and A1 should explicitly enumerate the R09 encoder/compressor/readout prefixes that are intended to train.

This is **not an A0 blocker**.

## Approved A0 scope

A0 may now implement and CPU-test only the minimal recurrent backend contract.

Allowed:

- minimal `LocalMemoryBackend` interface;
- recurrent-latent compressor baseline;
- state initialization/reset logic;
- per-sample `reset_mask`;
- mixed-batch Local presence/absence;
- masked-timestep inertness;
- batch permutation isolation;
- full-window vs two-segment carry+detach equivalence;
- meta -> to_empty -> explicit-init regression;
- deterministic fixed-seed init regression;
- machine-readable `artifacts/g0/r09/a0_contract.json`;
- CPU/static tests and verifier.

Not allowed:

- GPU;
- A1 optimizer training smoke;
- 100-step training;
- R09-B TTT implementation;
- shared-MoT modification;
- multi-GPU;
- matched SR;
- backend freeze;
- long training;
- Global/Agent/RL.

## A0 review expectations

After A0 implementation, stop at REVIEW and submit:

1. exact root/submodule SHAs;
2. code diff limited to A0 scope;
3. targeted CPU test results;
4. `a0_contract.json`;
5. provenance/tool hashes;
6. explicit evidence for:
   - true absent;
   - partial reset;
   - masked state inertness;
   - batch isolation;
   - segment carry+detach equivalence;
   - meta-init determinism.

Only after independent A0 approval may A1 be considered.

## Verdict

**APPROVE_TO_ADVANCE_A0**
