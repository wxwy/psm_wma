# R09-B2 P3 selector contract closure review

- Request: `6f8e9d4be7b6aa360d5ce4a0a834963d42d556bc`
- Implementation: `b1283d63966f87cdb3700482f9353d9ff4143afc`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Finding

### HIGH — frozen selector metadata is not yet bound to row-level selector membership

The new verifier correctly freezes the recurrent/TTT `keys_to_select` lists and production recipe source hashes, but it still does not independently recompute which concrete model parameters those selectors must select.

In `tools/g0/verify_r09_b2_p3_gpu_inventory.py`:

- `selector_contract_exact` checks only that artifact `selector.backend` / `selector.keys_to_select` equal the frozen constants and that the two recipe provenance hashes equal the frozen hashes.
- `backend_checks()` then checks `selector_equals_optimizer` by comparing two sets derived from artifact row booleans (`selected_by_resolved_selector` vs `selected_by_optimizer`), and checks optimizer/DCP structures against those same artifact-derived sets.
- No check recomputes the expected row-level membership from `model_parameters[*].name` using the frozen selector list and the production optimizer rule `any(key in name for key in keys_to_select)`.
- `explainable_by_selector_allowlist()` permits a recurrent-only name if it contains any key in `EXPECTED_RECURRENT_SELECTOR_KEYS - EXPECTED_TTT_SELECTOR_KEYS`.

This leaves a false-PASS path. The recurrent contract contains broad key `local_history_runtime`, while the TTT contract contains the narrower shared key `local_history_runtime.encoder`. A malformed artifact can keep both frozen `keys_to_select` lists unchanged, but mark a TTT encoder parameter false for both selector/optimizer booleans and consistently remove it from optimizer groups/DCP membership. In that state:

1. `selector_contract_exact` remains true;
2. `selector_equals_optimizer` and `optimizer_equals_selected` can remain true;
3. DCP membership/schema checks can remain internally consistent;
4. the resulting recurrent-only `local_history_runtime.encoder.*` name is nevertheless accepted because it contains recurrent-only key `local_history_runtime`.

Therefore the verifier still proves internal artifact consistency, not exact production selector membership. This is the same trust boundary the previous review required to remove, now shifted from `keys_to_select` metadata to row-level selector booleans.

The added regression covers mutation of `keys_to_select`, but does not cover the case where frozen selector metadata remains exact while row-level membership is missing/forged.

## Required change

1. For each backend, independently recompute expected selector membership from the backend's model parameter names and the frozen production selector keys using the exact production substring semantics. Since selector exclusions are required empty, any non-empty ignore/exclusion state must remain fail-closed.
2. Require both `selected_by_resolved_selector` and `selected_by_optimizer` to equal that independently recomputed expected set exactly.
3. Prefer comparing optimizer/DCP recurrent-only differences against the exact independently computed expected recurrent-vs-TTT membership delta, rather than allowing them through a broad substring test over selector-key differences. This avoids the `local_history_runtime` / `local_history_runtime.encoder` overlap.
4. Add a negative regression that leaves both frozen `keys_to_select` metadata lists untouched but removes/mislabels a TTT `local_history_runtime.encoder.*` member consistently across selector/optimizer/group/DCP views; verifier must return `FAIL`.

No GPU rerun is required for this verifier-only correction. Existing attempt-6 evidence may be reverified after the static verifier contract is fixed.

## Gate decision

`APPROVE_TO_CLOSE_B2_P3` is **not granted**.

This review does not authorize P4/P5, B2-T, training, evaluation, inference, any GPU rerun, or any broader gate.