# R09-B2 P4 static D005 review

- Implementation: `805ade943a016c3c2d28ad3ac882ec418c7595fc`
- Reviewed Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — P3 remains caller-owned rather than verifier-owned

`tools/g0/verify_r09_b2_p4_d005.py` still derives `selector_keys` directly from the supplied P3 object's `inventory.selector.keys_to_select` and derives membership from supplied `selected_by_optimizer` rows. `805ade9` correctly stops requiring the backend-specific P3 contract itself to be identical across recurrent and TTT, but it still permits an arbitrary self-consistent synthetic P3 object to define both contracts.

Required change:
- Bind P4 to the canonical attempt-6 P3 artifact identity/SHA and its PASS verifier evidence.
- Reuse/freeze the P3 verifier-owned recurrent/TTT selector constants and independently recompute row-level expected membership; do not accept caller-provided selector metadata as authority.
- Add a negative regression where a forged P3 object changes both selector metadata and selected rows consistently; P4 must still FAIL.

### HIGH — P1 is not bound to a canonical full-budget stream manifest

`_inputs_ok()` accepts any P1 object whose `schema_version` is a string, whose `status` starts with `PASS`, and whose `tiny_cpu_build.record_count` is an integer. The unit-test positive fixture still uses a synthetic `{"schema_version":"p1","status":"PASS","tiny_cpu_build":{"record_count":1}}` object.

The committed P1 tiny contract is only a one-update CPU proof: `optimizer_updates=1`, `grad_accum=4`, `max_samples_per_batch=1`, `record_count=4`. It cannot serve as the actual 100-update matched-run manifest. P4 must bind the actual production manifest/header/records (or explicitly remain BLOCKED until that manifest exists), including the canonical P1 verifier result and source hashes.

For the frozen production budget, the manifest record count must match the actual consumption budget. With `100` optimizer updates, `grad_accum_iter=16`, and `max_samples_per_batch=128`, the required total is `204800` records.

### HIGH — launch budget is still only internally self-consistent

`_budget_ok()` accepts arbitrary numbers provided they satisfy a multiplication identity. The current permanent positive test still uses `micro_batch_size=1`, `grad_accum_steps=1`, `global_batch_size=1`, `samples_per_update=1` and expects PASS.

The frozen production recipe instead has `trainer.grad_accum_iter=16`, while the production joint dataloader has `max_samples_per_batch=128`; on `world_size=1` this gives `2048` samples per optimizer update. P4 must derive or freeze those exact values from the production TOML/resolved-config/P0-P1 contract, not from D005 self-report.

Required change:
- Freeze `world_size=1`, `grad_accum=16`, `max_samples_per_batch=128`, `samples_per_update=2048`, `optimizer_updates=100` (or equivalent unambiguous schema).
- Tie the P1 manifest count to `100 * 16 * 128`.
- Reject the current 1/1/1 synthetic budget positive fixture.

### HIGH — output path is still derived from D005 self-reported job identity, not production job identity

`_output_ok()` derives `run_root` from `IMAGINAIRE_OUTPUT_ROOT + outputs.job_identity`, but `outputs.job_identity` is supplied by the D005 itself. The positive fixture uses `project=p`, `group=g`, `name=<backend>` without any matching argv override.

The frozen production TOML actually defines:
- `project = cosmos3_action_libero`
- `group = action_sft`
- `name = edge_libero_4in1`

Therefore the verifier can PASS a D005 whose declared `run_root` differs from the trainer's real `JobConfig.path_local`.

Required change:
- Independently derive the effective `job.project/group/name` from the frozen TOML/resolved config and any exact argv overrides.
- Derive `run_root`, checkpoints, log and capture paths from that effective identity plus `IMAGINAIRE_OUTPUT_ROOT`; do not trust `outputs.job_identity` as input authority.
- If backend isolation is achieved only through different `IMAGINAIRE_OUTPUT_ROOT` values, keep the production job identity equal on both sides unless exact job.* overrides are actually present.

### MEDIUM — external output and environment-sanitization contracts remain incomplete

`_output_ok()` now requires the effective output path to be under the repository root. The approved design allows a canonical external `IMAGINAIRE_OUTPUT_ROOT` under a verifier-owned output allowlist. This implementation will false-FAIL a valid external run root.

Also `environment.unset` still contains only rank variables. The approved D005 contract requires sanitizing all known semantic parent variables that can alter backend/data/probe/checkpoint/cache/network behavior (for example `PSM_LOCAL_DUMMY_ENABLED`, `PSM_R09_A1_ENABLED`, `PSM_R09_A1_PROBE_OUTPUT`, `PSM_LOCAL_DUMMY_MODE`, `PSM_R08_LOCAL_HISTORY_HORIZON`, `LIBERO_MAX_EPISODES`, `LIBERO_PREFETCH_FACTOR`, `ONLINE_VAE_PROBE_OUTPUT`, `PSM_R08_GATE_B_CAPTURE_ONLY`, proxy variables, etc.), or an equivalent exact-environment / `env -i` contract.

## Gate decision

`APPROVE_TO_CLOSE_P4_STATIC_D005` is **not granted**.

No GPU rerun is required. Continue with root-only static verifier/writer/test corrections. This review does not authorize P5, B2-T, `torchrun`, GPU, training, evaluation, inference, or broader scope.
