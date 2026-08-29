# ChatGPT Review — R08 Gate B strict verifier pre-capture @ root e88a569 / submodule 055e101

- Date: 2026-08-29
- Reviewer: ChatGPT
- Target root: `e88a56962f534f802c36bac7ab58ea166151c379`
- Target submodule: `055e101c8cd8a603ee206f92fd856a54f0e21442`
- Scope: pre-GPU Gate-B evidence pipeline only
- Verdict: **REQUEST_CHANGES**
- Normal/Zero/Shuffle GPU recapture: **DO NOT START YET**
- Gate C / R09 / multi-GPU / long training: **DO NOT START**

## Executive summary

Two previous blockers are substantially improved:

- provenance repo discovery is now cwd-independent in production code;
- a Gate-B-specific verifier and `r08_gate_b_history_sensitivity_v1` schema now exist before GPU capture.

However, the verifier is not yet strict enough to support canonical Gate-B PASS. Three concrete logic gaps can still produce a false-positive causal result:

1. missing invariant fields can pass as equal because `.get()` returns `None` in all three captures;
2. infinite output deltas pass the current `> 0` response test even though Gate B requires finite response;
3. same checkpoint is only established by same path string / load log, not by checkpoint content identity.

Fix these CPU/static issues before the three forward-only GPU captures.

## 1. cwd-independent provenance callback: PASS

At `cosmos_framework/callbacks/r08_gate_b_provenance.py:20-21`, repository paths are now derived from the callback source location:

```python
root = Path(__file__).resolve().parents[3]
submodule = root / "cosmos-framework"
```

This removes the previous `Path.cwd()` dependency.

The dedicated test changes cwd before invoking the callback, so the core cwd-independence intent is now covered.

Root/submodule tracked-clean flags and Gitlink/submodule revisions are also recorded at process startup.

### LOW test-quality note

The current cwd test mocks every Git command to return `abc`, so it does not assert the exact `git -C <root/submodule>` paths used by the callback.

This does not block the next step because the production path calculation is straightforward and correct for the repository layout, but improving the mock to inspect command arguments would make the regression stronger.

## 2. Gate-B-specific verifier/schema: direction PASS

`tools/g0/verify_r08_gate_b.py` now exists before capture and emits:

`r08_gate_b_history_sensitivity_v1`.

It also consumes per-mode:

- JSON capture;
- PT tensor capture;
- provenance sidecar;
- log;
- config.

It checks expected history modes, capture-only, same runtime tuple, Gitlink/submodule equality, tracked-clean status, checkpoint load log, non-history invariants, Local/Future/Action response, and hashes the raw files plus verifier itself.

This is the correct architecture.

## HIGH-1 — missing invariant fields can incorrectly PASS

At `tools/g0/verify_r08_gate_b.py:26`:

```python
invariant = {
    k: summaries["normal"].get(k)
       == summaries["zero"].get(k)
       == summaries["shuffle"].get(k)
    for k in INVARIANT_KEYS
}
```

If a required field is missing in **all three** capture JSONs, then:

```text
None == None == None
```

is `True`.

This is especially dangerous for the newly-added `history_mask`: a capture regression that omits it everywhere could still yield `invariant_exact.history_mask=true`.

### Required fix

Use the earlier strict pattern:

```python
invariant = {
    key: (
        all(key in summaries[m] for m in modes)
        and summaries["normal"][key]
            == summaries["zero"][key]
            == summaries["shuffle"][key]
    )
    for key in INVARIANT_KEYS
}
```

Also make schema validity a hard PASS condition:

- capture JSON schema is the expected parity/capture schema for all three;
- PT schema is the expected tensor schema for all three;
- provenance schema is exactly `r08_gate_b_capture_provenance_v1` for all three.

Add verifier CPU tests showing that deleting `history_mask` from all three inputs forces FAIL.

## HIGH-2 — response test requires nonzero but not finite

At `verify_r08_gate_b.py:28`:

```python
response = all(metrics[p][k]["l2_diff"] > 0 ...)
```

`float('inf') > 0` is true.

Therefore an overflow / non-finite Future or Action difference can currently satisfy Gate-B PASS, contradicting the frozen requirement of **finite and nonzero** response.

### Required fix

For Local, Future, and Action intervention metrics require, at minimum:

```text
math.isfinite(l2_diff)
AND l2_diff > 0
AND math.isfinite(max_abs_diff)
```

Prefer also finite `relative_l2_diff` when the reference norm is nonzero.

Add verifier tests where one Future or Action metric becomes Inf/NaN and ensure FAIL.

## HIGH-3 — same checkpoint path is not same checkpoint identity

At `verify_r08_gate_b.py:23`, `same_runtime` includes `checkpoint_path`, and line 25 checks that each log contains that path.

This is better than the previous artifact, but it only proves:

```text
all three processes declared the same path
+ logs say they loaded that path
```

It does **not** prove the checkpoint contents at that path are the same identity.

A path can be overwritten between captures while the current verifier still passes.

The previous review explicitly froze checkpoint identity as part of the causal contract.

### Required fix

Bind Gate B to the already-approved canonical Gate-A checkpoint manifest.

Preferred low-cost approach:

1. add a verifier argument such as `--gate-a-artifact` or `--checkpoint-manifest`;
2. load the canonical Gate-A checkpoint file manifest/hashes;
3. verify the Gate-B declared/loaded checkpoint path corresponds to that canonical checkpoint;
4. verify at least the model checkpoint metadata + DCP payload identity against the retained Gate-A hashes; preferably reuse the full available manifest rather than inventing a second one;
5. record the checkpoint identity/hash in the Gate-B output.

This does not require hashing the large checkpoint separately in each GPU process. The post-run CPU verifier can validate the retained checkpoint once against the canonical Gate-A manifest, while the three logs prove all captures loaded that exact path.

PASS must include `checkpoint_identity_valid=true`.

## HIGH-4 — actual load regex is too loose

At line 25:

```python
re.search(re.escape(checkpoint_path) + r" .* in iteration 0", log)
```

This can match any unrelated line containing the path followed later by `in iteration 0`; it is not tied to the framework's successful load marker.

### Required fix

Match the actual checkpointer completion message, e.g. the exact equivalent of:

```text
Loaded checkpoint from <checkpoint source> in iteration 0
```

and, if retained in the logs, also validate the preceding `Resuming ckpt ... with keys:` marker.

For the intended Gate-B model-only warm start, `iteration 0` is consistent with framework behavior because trainer state is not restored. Make that contract explicit in the verifier/config check rather than leaving `0` as an unexplained regex literal.

At minimum verify the capture config has the intended model-only/fixed-weight load semantics, or record an expected loaded iteration argument and validate it.

## MEDIUM — file hashes are recorded but config semantics are not validated

The verifier hashes all three config files, which is useful provenance, but currently does not validate the relevant settings inside them.

Before canonical PASS, ensure either the verifier or capture provenance proves:

- local history enabled;
- R07 dummy disabled;
- capture-only enabled;
- no backward/optimizer path by the reviewed `b5798c8+` code;
- intended checkpoint load mode.

History mode and capture-only are already in provenance; the remaining settings can be checked from config/log or treated as code/config provenance if the exact committed recipe plus environment contract is recorded.

Do not over-expand this into a new experiment.

## 3. Nested history-mask normalization: PASS

The previous nested-list issue remains correctly fixed in `f90f9d4/055e101`.

No further change is required there.

## Required next action

Remain CPU/static only:

1. require invariant key presence + schema validity;
2. require finite **and** nonzero Local/Future/Action response;
3. bind checkpoint path to canonical Gate-A checkpoint identity/manifest;
4. tighten actual successful-load log matching;
5. add small verifier tests for missing mask, non-finite response, wrong checkpoint identity/path, and wrong/missing load marker;
6. request re-review.

Once those verifier issues close, ChatGPT expects to approve exactly one minimal GPU round:

```text
Normal capture-only forward
Zero capture-only forward
Shuffle capture-only forward
```

with fixed weights, no backward, no optimizer step, then strict verification and REVIEW.

## Verdict

**REQUEST_CHANGES**

Gate B remains REVIEW.
No Gate C / R09 / multi-GPU / long training.