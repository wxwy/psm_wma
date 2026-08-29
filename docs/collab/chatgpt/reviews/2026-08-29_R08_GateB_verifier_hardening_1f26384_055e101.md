# ChatGPT Review — R08 Gate B verifier hardening @ root 1f26384 / submodule 055e101

- Date: 2026-08-29
- Reviewer: ChatGPT
- Target root: `1f263846f8368c22d71dc0ecf5d13d31fa49ee0c`
- Target submodule/Gitlink: `055e101c8cd8a603ee206f92fd856a54f0e21442`
- Scope: verifier-only pre-GPU review
- Verdict: **REQUEST_CHANGES**
- Gate-B Normal/Zero/Shuffle capture: **DO NOT START YET**

## Executive summary

This round closes two parts of the previous review:

1. required invariant key presence is now enforced before exact equality;
2. `l2_diff` must now be finite and nonzero.

However, three core strict-verifier requirements remain unclosed:

- capture/PT/provenance schemas are still not validated in PASS;
- checkpoint `manifest` is not interpreted or validated against the actual checkpoint at all;
- successful checkpoint-load matching is still the same loose regex rather than the framework's exact completion marker.

There is also no dedicated verifier test suite in the submitted root tree, despite the prior request for false-PASS regression tests.

Therefore the evidence pipeline is still capable of canonical false PASS and should be fixed before GPU capture.

## Closed — invariant key presence

`verify_r08_gate_b.py` now uses:

```python
invariant = {
    k: all(k in summaries[m] for m in modes)
       and summaries["normal"][k]
           == summaries["zero"][k]
           == summaries["shuffle"][k]
    for k in INVARIANT_KEYS
}
```

This closes the previous `None == None == None` failure mode, including for `history_mask`.

## Partially closed — finite response

The verifier now checks:

```python
math.isfinite(metrics[p][k]["l2_diff"])
and metrics[p][k]["l2_diff"] > 0
```

That is an improvement and prevents `Inf` L2 from passing.

But the prior contract also required finite `max_abs_diff`, because a metric object containing a finite aggregate with a non-finite element should not be accepted as canonical evidence.

### Required small fix

For all six intervention/output combinations require:

```text
isfinite(l2_diff)
AND l2_diff > 0
AND isfinite(max_abs_diff)
```

If `relative_l2_diff` is present and the reference norm is nonzero, require it finite too.

## HIGH-1 — schema validity is still not part of PASS

The current verifier loads:

- three capture JSONs;
- three PT tensor payloads;
- three provenance JSONs;

but does not check their schema versions at all.

Therefore an old/incompatible payload with coincidentally matching fields can still pass.

### Required fix

Hard-require all three modes to have:

```text
capture JSON schema == expected capture schema
PT schema           == r07_sensitivity_tensors_v1 (or the finalized R08 tensor schema)
provenance schema   == r08_gate_b_capture_provenance_v1
```

Expose machine fields such as:

```text
capture_schema_valid
tensor_schema_valid
provenance_schema_valid
```

and include all in the PASS expression.

## HIGH-2 — `--checkpoint-manifest` currently proves nothing about checkpoint identity

The new code does:

```python
checkpoint_identity = {
    "path": str(a.checkpoint_manifest),
    "sha256": sha(a.checkpoint_manifest),
}
...
and a.checkpoint_manifest.is_file()
```

This only proves that **some supplied file exists** and records that file's hash.

The verifier never:

- parses the manifest;
- verifies its schema;
- reads the canonical Gate-A checkpoint path from it;
- verifies the three declared checkpoint paths equal that canonical path;
- hashes any actual checkpoint DCP file;
- compares current checkpoint contents to manifest hashes.

Consequently, an arbitrary text file supplied as `--checkpoint-manifest` can satisfy this condition.

### Required fix

Create/use a real canonical checkpoint identity manifest, for example:

```json
{
  "schema_version": "r08_gate_a_checkpoint_manifest_v1",
  "checkpoint_path": "/.../iter_000000002",
  "files": {
    "model/.metadata": {"size_bytes": ..., "sha256": "..."},
    "model/__0_0.distcp": {"size_bytes": ..., "sha256": "..."}
  }
}
```

At minimum bind model `.metadata` + model DCP payload; using the full model/optim/scheduler/trainer manifest is even stronger.

The Gate-B verifier must:

1. parse and schema-check the manifest;
2. require all three provenance `checkpoint_path` values equal `manifest.checkpoint_path`;
3. verify the retained actual files at that checkpoint path exist;
4. recompute size/hash and match the manifest;
5. emit `checkpoint_identity_valid=true`;
6. include it in PASS.

Important: the current committed Gate-A artifact records checkpoint file names/sizes but **not DCP hashes**, so simply pointing `--checkpoint-manifest` at `gate_a_single_gpu.json` is not enough. Generate one canonical CPU-only checkpoint manifest now from the retained approved Gate-A checkpoint; no GPU rerun is needed.

## HIGH-3 — actual-load regex remains loose and unchanged

The current verifier still uses:

```python
re.search(
    re.escape(prov[m]["checkpoint_path"])
    + r" .* in iteration 0",
    log_text,
)
```

This is the same broad pattern identified in the previous review.

It is not anchored to the framework's successful checkpoint-load message.

### Required fix

Match the actual framework completion marker explicitly, e.g. robustly against the source object's rendered form:

```text
Loaded checkpoint from <...canonical checkpoint...> in iteration 0
```

and preferably also require a `Resuming ckpt ...` marker for that same source.

Do not merely search for the checkpoint path anywhere before the words `in iteration 0`.

Make the expected iteration explicit as a verifier argument/config (`0` for the intended model-only Gate-B warm start), and check the capture config/log establishes `load_training_state=false` / model-only semantics.

## HIGH-4 — no strict-verifier regression tests are committed

I searched the submitted root tree and found no dedicated:

`verify_r08_gate_b*_test`

or equivalent verifier test file.

The previous review explicitly requested tests for false-PASS cases.

Before GPU, add CPU tests that exercise the actual PASS logic for at least:

- missing `history_mask` -> FAIL;
- wrong capture/PT/provenance schema -> FAIL;
- non-finite Future/Action metric -> FAIL;
- arbitrary/wrong checkpoint manifest -> FAIL;
- changed checkpoint file hash -> FAIL;
- declared checkpoint path != manifest path -> FAIL;
- missing/wrong `Loaded checkpoint from ...` marker -> FAIL;
- canonical valid synthetic fixture -> PASS.

Refactor the verifier into testable helper functions if needed rather than invoking a subprocess for every case.

## What does not need further work

- cwd-independent provenance callback;
- nested history-mask normalization;
- R08 real-history Zero/Shuffle implementation;
- capture-only no-backward/no-optimizer path;
- required invariant key presence;
- `l2_diff` finite/nonzero check direction.

Do not modify the algorithm/model.

## Required next action

One final CPU/static verifier-hardening round:

1. add schema hard checks;
2. require finite `max_abs_diff` (and finite relative L2 when applicable);
3. create a real canonical Gate-A checkpoint hash manifest;
4. parse/validate it and compare actual checkpoint contents;
5. tighten successful-load matching to the real framework marker;
6. add the negative/positive verifier tests above;
7. request review.

After those pass, ChatGPT expects to issue:

**APPROVE_TO_RUN_GATE_B_CAPTURE_ONLY**

for exactly three forward-only runs:

```text
Normal
Zero
Shuffle
```

and no backward/optimizer/long training.

## Verdict

**REQUEST_CHANGES**

Gate B remains REVIEW; no Gate C / R09 / multi-GPU.