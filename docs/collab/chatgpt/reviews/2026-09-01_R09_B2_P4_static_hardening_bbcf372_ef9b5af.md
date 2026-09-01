# R09-B2 P4 static D005 hardening review

- Request: `bbcf372136641cbb4195b22af101c887e5cadbb8`
- Implementation: `ef9b5afbcb8a76633ce94539c0dd37f026af07ff`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — P3 binding is still caller-owned, and the matched rule rejects the real recurrent/TTT P3 contracts

`tools/g0/verify_r09_b2_p4_d005.py:70-72` builds the backend contract directly from the supplied P3 artifact's `inventory.selector.keys_to_select` and `selected_by_optimizer` rows. It does not bind the input to the canonical attempt-6 artifact/provenance nor rederive the selector from the verifier-owned P3 constants.

More importantly, `_inputs_ok()` embeds this backend-specific contract under `inputs.p3_inventory`, while `verify_pair()` at `tools/g0/verify_r09_b2_p4_d005.py:156-158` requires the entire `inputs` object to be equal between recurrent and TTT. The canonical P3 contracts are intentionally different: recurrent uses the base + Local History selector, while TTT uses only encoder + Local projections. Therefore a truthful pair cannot satisfy `matched.inputs`. The current unit-test positive fixture hides this by giving both backends the same synthetic selector `["net"]` and the same synthetic membership.

Required change:
1. Bind P3 to the exact canonical attempt-6 artifact path/SHA and recorded collection provenance/Gitlink, or an equivalently frozen verifier-owned identity.
2. Use the P3 verifier-owned recurrent/TTT selector constants and recompute expected membership from model parameter names; do not accept arbitrary supplied selector metadata as authority.
3. Compare only common P3 identity fields across backends. Allow the backend-specific selector/membership contract to differ exactly as frozen; preferably restore it to the approved top-level `backend_contract` field.
4. Add a positive regression using the real recurrent-vs-TTT selector shape, plus a negative test for forged-but-self-consistent P3 input.

### HIGH — P1 binding still accepts an arbitrary synthetic PASS object rather than the frozen stream-manifest contract

At `tools/g0/verify_r09_b2_p4_d005.py:100-109`, P1 is accepted when `schema_version` is merely any string, `status` merely starts with `PASS`, and `tiny_cpu_build.record_count` is an integer. The unit-test positive fixture explicitly uses `{"schema_version":"p1","status":"PASS","tiny_cpu_build":{"record_count":1}}`, which proves that a noncanonical caller-created P1 object can authorize a D005.

The closed P1 verifier contract is much stronger: exact `r09_b2_stream_manifest_v1` header/records, exact ordinal arithmetic, suite partition, source hashes, world_size=1, num_workers=0, cache-window coverage and dataset-index bijection. The currently committed `p1_tiny_manifest_contract.json` is only a tiny CPU contract and points to a historical `/tmp` manifest; the request itself states that no real D005 was generated for this reason.

Required change:
1. Bind to a canonical production P1 manifest/header/records identity, not just the tiny summary object.
2. Freeze exact path/SHA/count/schema and the required tuple/ordinal contract; validate or reuse the canonical P1 verifier result/source hashes.
3. If a production 100-update P1 manifest has not yet been materialized, keep P4 in REVIEW/BLOCKED rather than closing `P4_STATIC_D005`. A gate whose purpose is to freeze two actual D005 records cannot close with no canonical D005 inputs/artifacts.

### HIGH — launch budget is self-consistent only; it is not bound to the production recipe

`tools/g0/verify_r09_b2_p4_d005.py:139-143` accepts any positive-looking batch numbers as long as `global_batch_size = micro_batch_size * grad_accum_steps * world_size` and `optimizer_updates == 100`. The test positive fixture uses `micro_batch_size=1`, `grad_accum_steps=1`, `global_batch_size=1` and passes.

That is not the frozen production contract. The reviewed `21d064f` recipe has `trainer.grad_accum_iter = 16`, and the production dataloader has `max_samples_per_batch = 128`, giving 2048 samples per optimizer update on world_size=1. P0 already records these exact values.

Required change:
1. Derive/freeze the P4 budget from the actual production TOML/resolved-config/P0-P1 contract, not from D005 self-report.
2. Reject any budget whose grad accumulation / effective samples-per-update differs from the frozen matched-run values.
3. Define the `microbatch` field unambiguously relative to Cosmos' `max_samples_per_batch` vs inner DataLoader `batch_size=1`; do not let an arbitrary local naming convention satisfy the gate.

### MEDIUM — approved external-output and environment-sanitization contracts are not implemented

`tools/g0/verify_r09_b2_p4_d005.py:120-135` calls `expected.relative_to(root)` and returns false on `ValueError`, so a backend-specific `IMAGINAIRE_OUTPUT_ROOT` outside the repository can never pass. The approved P4 design explicitly allows a canonical external output root and requires verifier-owned allowlisting plus freshness checks there.

Also `_env_ok()` at approximately `tools/g0/verify_r09_b2_p4_d005.py:84-98` only requires rank variables in `environment.unset`; it does not implement the approved rule that all known semantic `PSM_*`, `LIBERO_*`, checkpoint/cache/HF/Transformers/proxy variables outside the frozen set/inherit allowlist are explicitly removed or rejected. A future launch inherited from a dirty parent shell can therefore still diverge from the D005 metadata.

Required change:
- Validate external output roots directly against a verifier-owned output allowlist; only perform Git-tracked checks when the path is under the repo.
- Implement the approved parent-environment sanitization contract (or an equivalent `env -i`/exact-environment execution contract) and permanent negative regressions.

## Gate decision

`APPROVE_TO_CLOSE_P4_STATIC_D005` is **not granted**.

No GPU rerun is required. Continue with root-only static verifier/writer/test corrections. This review does not authorize P5, B2-T, `torchrun`, GPU, training, evaluation, inference, or broader scope.