# R09-B2 P4 static D005 closure review

- Request: `c5a9e2b26c9b552b5021334e6e637997b4b2e042`
- Integration/root: `59d46fcfaf75821f103455b94bdcdfcf800b4d42`
- Implementation: `64aad3d57974cd26e4d3cc86627df4c2b6b3a1ea`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Findings

### HIGH — P4 cannot close without the two actual frozen D005 records

The approved design defines P4 itself as generating and accepting exactly two non-executable launch D005 records, `recurrent` and `ttt_fast_weight`, at `artifacts/g0/r09/b2/p4_launch_d005/{recurrent.json,ttt_fast_weight.json}` (`docs/build/PSM-WMA_R09_B2_P4_launch_d005_design_v0.1_2026-09-01.md:7-15, 48-76`).

The current request explicitly states that no real D005 has been generated. Therefore the builder/verifier implementation can be reviewed as ready for the next static artifact step, but `APPROVE_TO_CLOSE_P4_STATIC_D005` is premature. A Gate whose contract is the frozen pair cannot close from unit fixtures alone.

Required change:
1. after the verifier blockers below are fixed, create the two real `FROZEN_NOT_EXECUTED` records from the approved production assets;
2. run the pair verifier against those records in a clean source context;
3. commit the two D005 files plus verifier result and request closure on that evidence.

No `torchrun`, GPU, model, data-loader, training, evaluation or inference execution is required for this.

### HIGH — current production Gitlink is not frozen to the P1/P3 evidence Gitlink

`tools/g0/verify_r09_b2_p4_d005.py:78-90` only checks that D005 `source.submodule_revision` and `source.gitlink_revision` equal whatever submodule/Gitlink happens to be present in the current root. `_load_frozen_inputs()` (`:112-129`) freezes the P1/P3 files by SHA, but never requires the current submodule/Gitlink to equal the provenance they were validated against.

That permits this false-PASS sequence:

1. keep the frozen P1 header and P3 attempt-6 files unchanged;
2. advance `cosmos-framework` to a different Gitlink;
3. create D005 `source` fields that truthfully describe that new Gitlink;
4. `_source_ok()` and the frozen-input SHA checks can both pass, even though P1/P3 evidence belongs to `21d064f`.

P1 production evidence and P3 attempt-6 were both validated against Gitlink `21d064f`; the P4 design also explicitly binds P3 to that Gitlink. The verifier must therefore require the live submodule HEAD and root Gitlink used for D005 generation to remain exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb` (or derive and compare the same frozen identity independently from both P1 and P3 evidence).

Add a regression where the root/submodule move to another clean Gitlink while the frozen P1/P3 files remain unchanged; the P4 pair must FAIL.

### HIGH — semantic parent-environment sanitization is incomplete

`tools/g0/verify_r09_b2_p4_d005.py:28-35` hard-codes `SANITIZED_ENV`, but it does not cover all environment variables actually consumed by the production recipe. In particular, production `action_policy_libero_edge_all.py:65-89` reads `PSM_LOCAL_DUMMY_DIM`; because `PSM_R08_LOCAL_HISTORY_ENABLED=1`, this value directly controls `cfg["local_memory_dim"]`. A parent shell containing, for example, `PSM_LOCAL_DUMMY_DIM=64` can therefore change model shape while the current D005 environment contract still verifies.

The same production recipe also conditionally consumes probe/config variables not present in the current sanitization set, including `PSM_R07_RUNTIME_PROBE_OUTPUT`, `PSM_R08_GATE_A_PROBE_OUTPUT`, `PSM_R09_B1_PROBE_OUTPUT`, `PSM_R08_GATE_A_DEVICE_MONITOR_EVERY_N`, `PSM_R07_PARITY_OUTPUT`, `PSM_R07_PARITY_TENSOR_OUTPUT`, `PSM_R08_GATE_B_PROVENANCE_OUTPUT`, and `ONLINE_VAE_PROBE_MAX_SAMPLES` (`cosmos-framework/.../action_policy_libero_edge_all.py:258-304`).

The approved design is stronger than a hand-curated partial list: any unapproved parent variable matching `PSM_*`, `LIBERO_*`, checkpoint/cache/HF/Transformers/WAN-VAE/proxy semantics must be rejected or explicitly scrubbed (`docs/build/PSM-WMA_R09_B2_P4_launch_d005_design_v0.1_2026-09-01.md:98-112`).

Required change: either
- make the execution contract an exact clean environment (`env -i` / equivalent explicit env map), or
- implement pattern-based parent-environment rejection/sanitization plus the complete known production variable set.

Add at minimum a negative regression for `PSM_LOCAL_DUMMY_DIM` and one omitted probe variable.

### HIGH — verifier accepts a different record shape while claiming the approved v1 schema

The approved `r09_b2_p4_launch_d005_v1` schema contains, among other fields, `command.effective_overrides`, top-level `backend_contract`, top-level `prohibitions`, explicit resolved-config/cache inputs, and the fixed output field names defined in `docs/build/PSM-WMA_R09_B2_P4_launch_d005_design_v0.1_2026-09-01.md:48-76`.

The positive fixture in `tools/g0/test_verify_r09_b2_p4_d005.py:55-69` returns a record with the same schema version but omits `command.effective_overrides`, `backend_contract` and `prohibitions`, uses a different `inputs` structure, and renames output fields (`stdout_log`, `capture_dir`, `fresh`). `verify_r09_b2_p4_d005.py` checks the schema version string but does not enforce the approved top-level schema.

That means a structurally different record can PASS while being labeled `r09_b2_p4_launch_d005_v1`.

Required change: either implement the approved v1 schema exactly and fail on missing/extra fields, or publish a revised schema/design version and have that design reviewed before using the new shape. Do not silently redefine v1 inside the verifier/tests.

### MEDIUM — frozen P1 header is not enough to bind the currently consumed manifest directory

`_load_frozen_inputs()` freezes the P1 header SHA, while `inputs.external_assets.stream_manifest` only carries a caller-supplied tree SHA that `_asset_ok()` recomputes against the current directory. The verifier does not independently require the current `records.jsonl` SHA and per-suite JSONL SHAs to equal the frozen values in the P1 header, nor does it freeze/revalidate the committed P1 `verification.json`.

A later clean commit could therefore alter `records.jsonl`/suite files while leaving the frozen header unchanged; a D005 updated with the new self-consistent directory SHA could still satisfy the current P4 input checks.

Required change: before accepting D005, independently bind the current P1 directory to the frozen header by checking at least `records.jsonl` against `records_sha256` and each suite file against `suite_record_sha256` (or freeze/revalidate the canonical P1 verifier result plus the referenced file hashes).

## Gate decision

`APPROVE_TO_CLOSE_P4_STATIC_D005` is **not granted**.

The current implementation is materially closer to the approved contract and does not require any GPU rerun. Continue with root-only static verifier/writer/test changes, then generate and verify the two real non-executable D005 artifacts. This review does not authorize P5, B2-T, `torchrun`, GPU, training, evaluation, inference, or broader scope.
