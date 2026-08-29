# ChatGPT Review — R08 Gate B provenance capture patch @ root c036cf9 / submodule f90f9d4

- Date: 2026-08-29
- Reviewer: ChatGPT
- Requested scope: pre-recapture provenance + history-mask normalization
- Target root: `c036cf954c5d81f0d2a80a6f49a348f08ed33e36`
- Target submodule: `f90f9d430fdcb7e11075a4c7e8af7718f2f074c3`
- Verdict: **REQUEST_CHANGES**
- GPU Normal/Zero/Shuffle recapture: **DO NOT START YET**
- Gate C / R09 / multi-GPU / long training: **DO NOT START**

## Executive summary

The previous nested history-mask bug is fixed correctly.

The new provenance callback is directionally useful, but it is not yet strong enough to support a canonical Gate-B causal claim, and the strict Gate-B verifier/pass contract has not been committed before the planned recapture.

Because the next GPU work is only three forward-only captures, it is worth fixing the evidence path first so that one recapture closes Gate B once.

## 1. Nested history-mask normalization: PASS

`R07ParityCaptureCallback._tensor_or_list_summary()` now supports the same three practical input forms needed by the production history path:

- `Tensor`;
- `list[Tensor]`;
- `list[list[Tensor]]` with singleton inner lists.

It also fails fast on invalid entries.

The new test exercises:

```text
Tensor
list[Tensor]
list[list[Tensor]]
invalid list entry
```

This closes the previous mask-capture compatibility blocker.

Adding `history_mask` to the comparator exact invariants remains correct.

## HIGH-1 — provenance callback is cwd-dependent

`R08GateBProvenanceCallback.on_train_start()` currently does:

```python
root = Path.cwd().parent
submodule = Path.cwd()
```

This assumes the training process is always launched with cwd exactly equal to the `cosmos-framework` submodule root.

That is not a safe provenance contract. A launcher invoked from the root repo, a wrapper script, Hydra cwd behavior, or any future command change can make these paths wrong while the capture itself still runs.

### Required fix

Derive repository paths from the callback file location, not current working directory.

For example, conceptually:

```text
submodule = Path(__file__).resolve().parents[2]   # cosmos-framework
root = submodule.parent                          # psm_wma
```

Use the exact parent depth appropriate to the actual file path and assert:

- `<submodule>/.git` or valid Git worktree;
- `<root>/cosmos-framework` resolves to the same submodule.

Add a CPU test that changes cwd to an unrelated temporary directory before calling the callback and still gets the correct repo SHAs.

## HIGH-2 — checkpoint_path is declarative, not proof of actual checkpoint load

The callback records:

```python
"checkpoint_path": os.environ.get("PSM_R08_GATE_B_CHECKPOINT_PATH")
```

This only proves what the launch environment *claims* the checkpoint should be.

It does not prove the framework actually loaded that path.

For Gate B, same-checkpoint identity is the core causal prerequisite.

### Required design

It is acceptable to keep the startup-declared checkpoint path, but the final strict verifier must cross-check it against the **actual checkpointer load evidence** from each capture process.

For each mode, require a log marker equivalent to:

```text
Resuming ckpt <actual source> with keys: [...]
Loaded checkpoint from <actual source> in iteration 2
```

or the exact framework markers produced by the capture configuration.

The verifier must reject:

- missing actual load marker;
- actual load path != declared checkpoint path;
- different actual checkpoint paths across Normal/Zero/Shuffle;
- wrong loaded iteration.

Also hash a stable identity of the Gate-A checkpoint (at minimum model DCP metadata/payload; preferably reuse the canonical Gate-A manifest) and require the same identity for all three.

## HIGH-3 — strict Gate-B verifier/PASS contract is not committed yet

The prior review explicitly requested that the next GPU recapture produce a canonical:

`r08_gate_b_history_sensitivity_v1`

artifact whose PASS requires all causal conditions.

At root `c036cf9`, there is still no Gate-B-specific strict verifier committed in the root repository. The existing comparator remains `tools/g0/compare_r07_sensitivity.py`.

Do not defer the strict verifier design until after GPU capture. Otherwise the capture may omit a field the verifier later needs and force another GPU rerun.

### Required pre-GPU verifier

Commit a Gate-B-specific verifier now. It can consume the future capture files even before those files exist.

The PASS logic should require at least:

```text
three modes exactly = normal / zero / shuffle
AND each capture provenance schema valid
AND each runtime root/submodule/Gitlink valid
AND same root/submodule across captures
AND capture_only == true for all
AND actual checkpoint load proven for all
AND same checkpoint identity/path/iteration for all
AND history_mask exact across modes
AND all other non-history invariants exact
AND history payload changed for zero/shuffle
AND Future output finite and nonzero response
AND Action output finite and nonzero response
AND raw capture/config/log/provenance files hashed
```

The verifier should itself record its SHA256 and produce the new R08 schema.

## MEDIUM — startup provenance should record cleanliness / Gitlink validity directly

The callback currently records root HEAD, submodule HEAD, and Gitlink SHA, which is useful.

While fixing it, also record:

- `gitlink_matches_submodule`;
- root tracked-clean status;
- submodule tracked-clean status.

These can also be recomputed by the strict verifier, but recording them at process startup makes the evidence stronger and easier to audit.

Do not necessarily fail the capture process on untracked evidence outputs; use tracked-only cleanliness as in Gate A.

## MEDIUM — no dedicated provenance callback regression is visible

The submitted CPU count says 5 callback tests pass, but the new provenance callback itself has no dedicated test file in the submitted tree.

Add focused CPU tests for:

1. cwd independence;
2. correct root/submodule/Gitlink extraction;
3. history mode and capture-only flag recording;
4. missing/invalid required environment fields fail fast, if those fields are required for canonical Gate B;
5. atomic output write if practical.

## What is already acceptable and should not be reworked

- Real R08 Zero/Shuffle intervention implementation;
- capture-only forward return before backward/optimizer;
- Future and Action sensitivity observed in the previous development capture;
- exact non-history invariant comparator;
- newly fixed history-mask invariant capture.

No algorithm change is needed.

## Required next action

Remain CPU/static only.

1. Make provenance repo discovery cwd-independent.
2. Add dedicated provenance callback tests.
3. Commit the Gate-B-specific strict verifier/schema/pass logic **before** recapture.
4. Make verifier cross-check declared checkpoint against actual load logs and checkpoint identity.
5. Request re-review.

Only after this evidence pipeline is approved should Codex automatically run the one minimal GPU round:

```text
Normal capture-only forward
Zero capture-only forward
Shuffle capture-only forward
```

with no backward, no optimizer step, no long training.

## Verdict

**REQUEST_CHANGES**

Gate B remains REVIEW.
No Gate C, no R09, no multi-GPU, no long training.