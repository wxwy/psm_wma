# R09-B2 P3 PASS provenance hard-gate static implementation review

- Review request root: `ac1a2d81c40d8345d0d0e87e299b11822ab1ede9`
- Reviewed implementation root: `8dced7546b682f03cf50f5968b232b4a126abbc9`
- Submodule/Gitlink: `0af5d53900ec169f43104d4fdf1827ad6691600d`
- Scope: Codex request + implementation only; no GPU/model-construction authorization

## Verdict

**REQUEST_CHANGES**

The new provenance field inventory is directionally correct, but the submitted `pass_provenance` check is not a provenance hard gate. It only checks that each artifact-provided value is truthy.

## HIGH — provenance values are artifact-controlled and not independently bound

`tools/g0/verify_r09_b2_p3_gpu_inventory.py:25-41` defines the expected provenance field names, but `:120` reduces the entire validation to:

`all(provenance.get(key) for key in PASS_PROVENANCE_KEYS)`

Therefore a future artifact containing arbitrary non-empty strings for `root_revision`, `gitlink_revision`, source SHAs, `gpu_uuid`, `d005_record`, or `approved_run_token` satisfies this check. The verifier does not prove that any of those values correspond to the executed/reviewed source or D005 record.

This does not satisfy the previously frozen requirement that execution provenance be a **hard PASS gate**.

### Required CPU/static fix

For a future PASS, make the verifier independently establish at least:

1. `root_revision` resolves to the reviewed/runtime source root; derive its `cosmos-framework` Gitlink with `git ls-tree <root_revision> cosmos-framework` and require `derived_gitlink == gitlink_revision == submodule_revision`.
2. `approved_run_token` must equal the exact frozen token `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`, not merely be non-empty.
3. Freeze source paths for recipe / collector / verifier / model-construction / optimizer / DCP-serialization code and independently recompute their SHA256 values. A bare artifact-supplied SHA string is insufficient.
4. `d005_record` must be a structured path/reference plus SHA256 (or equivalent immutable identity); parse it and require its root/submodule/Gitlink, exact command/cwd/environment, world-size/GPU/resource cap, processor path and run authorization to match the artifact/runtime evidence.
5. Validate `command_argv`, `cwd`, `environment`, and `gpu_uuid` structurally and cross-bind them to the D005/runtime record rather than checking truthiness.
6. Emit separate machine-readable booleans such as `root_gitlink_valid`, `source_hashes_valid`, `d005_identity_valid`, `command_binding_valid`, `gpu_binding_valid`, `run_token_valid`, and include all in PASS.
7. Add negative tests where every provenance field is non-empty but one of root/Gitlink, source SHA, D005 identity, run token, command/environment or GPU UUID is deliberately wrong; each must FAIL.

BLOCKED artifacts should continue to be allowed to omit run-only provenance when execution never occurred; do not regress the existing BLOCKED semantics.

## Still open from the previous review

The following remain run-approval blockers and are not closed by this submission:
- verifier-owned canonical asset path + size binding;
- actual isolated-worker offline-environment ordering before HF/Transformers import;
- recipe-resolved production processor canonical-path binding;
- complete processor package read-only proof;
- actual production DCP persistent-membership inspection rather than symbolic source naming.

## Scope

No GPU, processor/model construction, checkpoint I/O, forward/backward/step, B2-T/P4/P5, training, eval or inference is authorized.
