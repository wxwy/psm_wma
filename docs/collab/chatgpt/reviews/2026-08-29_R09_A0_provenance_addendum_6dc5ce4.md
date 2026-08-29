# ChatGPT Addendum — R09-A0 provenance refresh @ 6dc5ce4

- Date: 2026-08-29
- Reviewer: ChatGPT
- Previous review: `docs/collab/chatgpt/reviews/2026-08-29_R09_A0_ce1ce00_c763475.md`
- Provenance refresh commit: `6dc5ce43d0e222b142c6b6657b2cea59248c4a82`
- Source root recorded by artifact: `8a5c488724fc555e64bbdbb2217b8a31f7bbf3f4`
- Source root Gitlink: `c763475c733740be6ef5914e3234375c01771a80`
- Submodule: `c763475c733740be6ef5914e3234375c01771a80`
- Verdict: **REQUEST_CHANGES**
- A1 / GPU / R09-B: **NOT APPROVED**

## What 6dc5ce4 closes

The stale-revision portion of the previous provenance finding is closed.

GitHub independently confirms:

```text
root 8a5c488
  -> Gitlink c763475

artifact submodule_revision
  = c763475
```

Therefore the artifact is no longer pointing to the old pre-A0 `9263dda / 860f532` runtime.

## What remains open

`6dc5ce4` changes only two artifact revision fields. It does not change the verifier, tests, or recurrent backend.

Therefore the following previous blockers remain unchanged.

### HIGH — hard PASS is still under-specified

Verifier still sets:

```python
status = "PASS" if state_segment_diff <= 1e-6 else "FAIL"
```

It does not require the other frozen A0 assertions.

`masked_timestep_inert` is still hard-coded to `True`.

`token_max_abs_diff` is still copied from the state diff rather than measured from actual tokens.

### HIGH — meta -> to_empty initialization lifecycle still not tested

Artifact still records:

```text
init.path = CPU contract constructor
```

No meta construction, `to_empty(cpu)`, explicit reset/init, all-parameter finite check, or fixed-seed elementwise-determinism check is present.

### HIGH — partial reset remains vacuous

The reset target is the all-mask sample whose pre-reset state is already zero.

This does not prove selected reset of a nonzero state.

A correct test must reset a sample with demonstrably nonzero pre-reset state while proving untouched samples remain exactly unchanged.

### HIGH — segment token equivalence / detach-value exact remain unproven

Only final state equivalence is measured.

The verifier still does not independently measure:

- full replay token vs segment-2 token;
- `state.detach()` numerical identity.

### MEDIUM — recurrent masked-step inertness and batch permutation isolation remain untested

The existing R08 encoder masked-input test is not a substitute for the R09 recurrent state-update contract.

## Provenance schema is still only partially closed

Although source root/submodule identity is now correct, the frozen A0 artifact schema also required the verifier to emit and validate:

- `gitlink_revision`;
- root tracked-clean;
- submodule tracked-clean;
- provenance-valid boolean;
- verifier/tool SHA;
- command or command hash.

These are still absent from `a0_contract.json`.

So provenance has improved from **wrong revision** to **correct but not self-validating**.

## Required next action

CPU-only:

1. strengthen tests and verifier as specified in the previous review;
2. make PASS depend on every hard A0 assertion;
3. add real meta->to_empty initialization regression;
4. use nonzero state for selected reset;
5. measure actual token segment diff and detach-value identity;
6. add recurrent masked-step and batch-permutation tests;
7. complete self-validating provenance fields;
8. regenerate artifact from committed clean root/submodule;
9. stop at REVIEW.

No A1/GPU/R09-B/multi-GPU/long training.

## Verdict

**REQUEST_CHANGES**
