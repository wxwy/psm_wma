# ChatGPT Independent Review — R09-B TTT v0.3.2 Multi-Slot CPU Core @ 6fedfe9

**Date:** 2026-09-03  
**Reviewer:** ChatGPT (independent code / design / evidence reviewer)  
**Task/Gate:** `G0-R09-B-TTT-V032-MULTI-SLOT-CPU-IMPLEMENTATION`

## 1. Review identity

- **root implementation SHA under verdict:** `6fedfe9d184ee1dfc25a4195d601ab7a537d705f`
- **Cosmos child implementation SHA / root Gitlink:** `5b806554aa60c99b2681a68ae6b7763eb270dd96`
- **request/ledger SHA observed on `V2`:** `9efa3e655cf9fa36e8f60223f90c30d7b3cb912b`
- **C1 implementation-design authority:** root `411e96760bdd1187303c0c2bfe2185223cc5c58e`, baseline child `cf52f43dc328d4c8eec51923d66835125664dee5`
- **approved v0.3.2 architecture authority:** `ef3ff1a9dfe73c62df5991d3ece88b1677a2b6d3`

The remote `V2` head at review start was `9efa3e65...`, whose direct parent is the exact root implementation SHA `6fedfe9...`. The verdict is bound to `6fedfe9... + 5b80655...`; the request/ledger commit is not an implementation SHA.

The required literal `git fetch origin V2` was attempted in a temporary local repository, but this reviewer environment still cannot resolve `github.com` (`Could not resolve host`). Remote freshness, ancestry, exact Gitlink, root scope, and child diff were independently rechecked through the connected GitHub repository interface. No claim is made that shell fetch succeeded.

## 2. Verdict

**REQUEST_CHANGES**

One HIGH correctness blocker remains. No authorization is granted to enter C3 / Memory Prefix source-ABI work.

## 3. Scope / accepted implementation surface

The root implementation record changes only `SESSION.md`, `TODO.md`, and the `cosmos-framework` Gitlink. The child delta from `cf52f43...` to `5b80655...` is exactly the two C1-authorized files:

1. `cosmos_framework/model/generator/mot/local_evidence.py`
2. `cosmos_framework/model/generator/mot/local_evidence_test.py`

No runtime/attention/config/chronology/training surface is modified.

The following implementation direction is accepted and should be preserved in the remediation:

- `k_local` is a positive construction/checkpoint-time identity;
- `slot_queries[K_local,D_ttt]` is a registered slow parameter, zero-initialized for `K=1` and randomized for `K>1`;
- `project_evidence()` keeps the existing K/base-Q/V triple ABI;
- `project_queries()` expands only the read queries; K/V are not replicated by slot;
- each **valid** sample executes one K/V-only higher-order inner update and one `W_(t-1) -> W_t` transition independent of `K_local`;
- `read_many()` reads all slots from one fast state;
- legacy `step_projected/step/scan_segment` remain K=1 wrappers and fail closed for K>1;
- strict K-mismatched `slot_queries` state-dict loading is rejected without migration logic;
- fast-state payload remains unchanged.

Submitted evidence reports `21 passed, 8 deselected`, plus `py_compile` and child/root `git diff --check` PASS. Those results do not cover the blocker below.

## 4. Finding

### HIGH-1 — invalid rows are still evaluated by the fast read before masking, so finite inputs can return NaN instead of exact-zero inert tokens

**Location:** `cosmos_framework/model/generator/mot/local_evidence.py:491-492`

**Observed implementation:**

```python
state_out = ContinualTTTFastState(*(torch.stack(rows) for rows in state_rows))
tokens = self.read_many(queries, state_out)
return tokens * valid[:, None, None], state_out, valid
```

The per-row update loop correctly skips `autograd.grad` for `valid=False`, but after the loop `read_many()` is called for **every** row, including invalid rows. The zeroing happens only afterward by multiplication.

This violates the frozen C1 algorithm contract, whose exact pseudocode requires an invalid row to set `state_out[b] = state_in[b]`, set `tokens[b] = zeros(K_local,D_local)`, and `continue` without executing a read for that row.

It is also a real numerical correctness issue rather than only an efficiency/style difference. Input validation requires finite fp32 state/query values, but finite values can still overflow a linear/MLP read to `inf`. IEEE arithmetic then gives `inf * 0 -> NaN`; therefore an invalid row can return NaN rather than the required exact-zero token even though all API inputs passed the finite checks. The current random-scale inert-row test does not exercise this case.

**Root cause:** token masking is applied *after* evaluating the fast MLP on invalid rows, rather than making invalid rows structurally read-inert.

**Acceptance criteria:**

1. Invalid rows must bypass the fast read entirely, not merely mask its result afterward. A minimal implementation may build `token_rows` inside the same per-sample loop: append an exact fp32 zero `[K_local,D_local]` and preserve the four state leaves for invalid rows; only valid rows call the post-update fast read.
2. Preserve the one-write/K-read rule for valid rows; do not add extra KVB updates, counters, or state fields.
3. Add a regression test proving invalid-row read-inertia under finite values that would overflow if evaluated. The returned invalid token must be finite and bitwise/exact zero, `present=False`, and all four state leaves must remain exactly equal to input. Prefer also instrumenting the read path so the invalid row is proven not to call `_fast_mlp`/`read_many`, rather than relying only on normal random values.
4. Re-run the full frozen `-k continual_ttt` CPU selector, `py_compile` for both changed child files, child/root `git diff --check`, and submit the new child SHA plus bumped root Gitlink for fresh same-SHA review.

This remediation is fully within the already-approved C2 two-file scope; it does not require a new design Gate.

## 5. Test-plan note

The existing `test_continual_ttt_multi_slot_post_update_read_is_pure_and_invalid_rows_are_inert` checks the returned invalid token on ordinary random values, but because the production implementation reads the invalid row and only then multiplies by zero, that fixture cannot distinguish structural read-inertia from post-hoc masking. The remediation must add a sentinel/overflow or call-instrumentation case that closes this gap.

## 6. Still prohibited

While this C2 implementation remains open, the following remain prohibited:

- Memory Prefix/source-ABI design or implementation as the next Gate;
- `local_memory2llm`, Memory norm/KV projection, position/RoPE/mask/packing;
- production runtime/attention wiring;
- chronology/native outer-loss integration;
- production config/optimizer/checkpoint migration or refreeze;
- GPU/CUDA/torchrun;
- training, evaluation, inference or inference smoke;
- real model/data/cache/checkpoint access;
- P4/P5 real operations;
- B2-T.

Any remediation must produce a new child implementation SHA and root Gitlink SHA and receive a fresh same-SHA closure review. This `REQUEST_CHANGES` cannot be closed by reusing the current `5b80655...` evidence.