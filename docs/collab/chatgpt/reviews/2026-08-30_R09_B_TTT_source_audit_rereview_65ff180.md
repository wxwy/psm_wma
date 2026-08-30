# ChatGPT Review — R09-B TTT B0 source-audit five-fix re-review

- Date: 2026-08-30
- Reviewer: ChatGPT
- Rectification root: `65ff180eb371527d3ef4685cb03ce75af9f47e95`
- Re-review request: `9fd9b70fbcfc728075f376ce2c5140870a9c4fcd`
- Submodule/Gitlink: `c0287e215f265134cb8b8d947de7eb398f0246cf`
- Reviewed file: `docs/build/PSM-WMA_R09_B_TTT_source_audit_v0.1_2026-08-30.md`
- Verdict: **REQUEST_CHANGES**

## Prior five blockers

The five blockers from ChatGPT review `9c928ae / d210c3e` are substantively closed:

1. **B0 runtime scope — CLOSED.** `source_audit:54-61` now limits B0 to an independent `TTTLocalMemoryBackend` plus CPU contract test; `omni_mot_model.py` production wiring is explicitly deferred to B1.
2. **Unreachable teacher — CLOSED.** The inner objective is now backend-local and parameter-free: `MSE(W @ e, stopgrad(e[:32]))`.
3. **Segment SGD math — CLOSED.** `source_audit:31-41` freezes mean-over-valid-position / mean-over-32 loss, one shared pre-update W, one SGD step, zero-valid behavior and fp32/bf16 cast points.
4. **Autograd semantics — CLOSED.** `source_audit:43` freezes `create_graph=False`, detached cache/update/token and no native-loss gradient through adaptation/history.
5. **Composite fast state / unaligned split — MOSTLY CLOSED.** The design now carries `W`, pending evidence, last evidence, initialized and segment progress, and explicitly targets arbitrary unaligned two-segment equivalence.

The arithmetic for the declared logical tensor payload is correct:
`16,384 + 2,048 + 512 + 1 + 8 = 18,953 bytes/sample`.

## Remaining blockers before APPROVE_TO_IMPLEMENT_B0

### HIGH-1 — final short-tail semantics are still internally inconsistent

Relevant lines:
- `source_audit:22`: final tail segment may be shorter than 4 valid timesteps.
- `source_audit:31`: an inner update occurs **only when progress reaches 4**.
- `source_audit:41`: an incomplete tail is retained in pending state and is **not updated at call boundary**.
- preflight freezes `state_start=zeros` per sample/window and forbids carry across outer trainer/policy/control forwards.

These statements leave the logical end-of-window behavior undefined.

If a sample/window ends with 1–3 valid pending timesteps, there is no later outer call allowed to complete that segment. Under the current text those pending timesteps never trigger an inner update. That can be a valid algorithm choice, but then it is not a 'short tail segment with one inner step'; it is an intentionally **non-updating remainder** and must be stated that way.

Alternatively, if the intended tail is a real shorter segment that should receive one final SGD update, the backend needs an explicit logical-finalization signal/API. It cannot use ordinary `replay()` call boundaries, because arbitrary call splits must remain compositionally equivalent.

Required fix: freeze exactly one of the following:

**Option A — no tail update (minimal):**
- full 4-valid blocks update;
- final remainder of 1–3 valid timesteps never updates W;
- remainder still contributes to `last_evidence` / final token and remains observable in returned state;
- rename/describe it as a pending terminal remainder, not an updated tail segment;
- CPU contract includes valid-count cases 1,2,3,5,6,7 and proves expected update count `floor(N_valid/4)`.

**Option B — explicit finalize:**
- add a backend-local `finalize(state)` or `replay(..., final=True)` contract for logical sample/window end;
- finalization performs exactly one update on the 1–3 valid pending positions using the same mean reductions;
- ordinary replay call boundaries never finalize;
- full replay and arbitrarily split replay + one finalization are exact-equivalent;
- B0 state/test/schema must include this finalization contract.

Do not let the implementation infer terminal semantics.

### MEDIUM-2 — approved machine-readable schema cannot represent the new composite mixed-dtype state

The approved preflight schema still models state as:

`state: {shape: [], dtype: "", bytes: 0, fast_state_parameter_count: 0}`

But the rectified candidate now has five state members with mixed dtype/shape:
- `W`: bf16 `[B,32,256]`;
- `pending_evidence`: bf16 `[B,4,256]`;
- `last_evidence`: bf16 `[B,256]`;
- `initialized`: bool `[B]`;
- `segment_progress`: int64 `[B]`.

A single `shape` and `dtype` field cannot truthfully record this state, and B0 is supposed to emit a machine-readable artifact/verifier rather than an informal summary.

Required fix: freeze a backward-compatible composite-state artifact extension before coding, for example:

```text
state:
  members:
    W: {shape_per_sample:[32,256], dtype:"bfloat16", bytes_per_sample:16384}
    pending_evidence: {shape_per_sample:[4,256], dtype:"bfloat16", bytes_per_sample:2048}
    last_evidence: {shape_per_sample:[256], dtype:"bfloat16", bytes_per_sample:512}
    initialized: {shape_per_sample:[], dtype:"bool", bytes_per_sample:1}
    segment_progress: {shape_per_sample:[], dtype:"int64", bytes_per_sample:8}
  logical_bytes_per_sample: 18953
  fast_state_parameter_count: 0
  bytes_limit_pass: true
```

Exact key names may differ, but the verifier must independently compute `numel * element_size` for every tensor member and hard-check the total against the frozen candidate limit. Call this **logical tensor payload bytes**, not allocator/VRAM footprint.

If Option B finalization adds or changes state, the schema/byte formula must be updated accordingly.

## Non-blocking B1 note

The fully detached token means the future B runtime path will not send native vision/action gradients back through the TTT adaptation into `LocalEvidenceEncoder`. That does not block this isolated B0 CPU backend implementation, but B1 runtime/training review must explicitly audit active optimizer membership/gradients rather than assuming 'same optimizer prefixes' means the same effective trainable path.

## Verdict

**REQUEST_CHANGES**

No TTT implementation or CPU contract execution is authorized yet.

Only the two source-audit contract items above need revision. The previous five fixes are accepted and should not be reopened unless the tail decision changes them.

After tail semantics and composite artifact schema are frozen, the expected next verdict is `APPROVE_TO_IMPLEMENT_B0` limited to:
- independent `TTTLocalMemoryBackend`;
- dedicated CPU contract test;
- B0 machine-readable artifact/verifier;
- no production runtime wiring.

Still blocked: `omni_mot_model.py` TTT wiring, GPU/A1-style smoke, multi-GPU, long training, matched SR, backend freeze, RoboTTT/shared-MoT code import, Global/Agent/RL.
