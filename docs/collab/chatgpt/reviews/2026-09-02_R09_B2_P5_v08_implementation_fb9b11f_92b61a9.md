# R09-B2 P5 v0.8 static tooling implementation review

## Request / implementation

- Request commit: `fb9b11ff155ca2f61435d9998df61600385e80ef`
- Implementation commit: `92b61a9144255e59bdc078e50f116ca30e85fcf4`
- Approved design: `bae668a287673bc1b533746d3c209cadee3c65e4`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

`APPROVE_TO_CLOSE_P5_V08_STATIC_TOOLS` is not authorized.

## Findings

### HIGH — the real parent/child path still executes the historical P4-v2 contract

`tools/g0/export_r09_b2_p5_resolved_config.py:320-337` still implements `build_pair_requests()` by importing `_evidence_records()` from the existing P5 verifier, validating `production_root` through historical D005, and constructing child requests from P4-v2 record SHA/verification SHA. `tools/g0/export_r09_b2_p5_resolved_config.py:365-408` then has `run_parent_export()` call this old `build_pair_requests()` directly.

The new `load_p4_v4_preflight()` and `p5_effective_environment()` helpers are never on the production parent path. `validate_child_request()` also still admits only the old hard-coded `FROZEN_CHILD_REQUEST_SHA256` identities. Therefore a future P5 run would still consume historical P4-v2 evidence, despite v0.8 explicitly requiring P4-v4 execution-preflight PASS as the sole handoff and requiring BLOCKED otherwise.

Required fix: remove the historical P4-v2 admission path from P5 execution; derive each P5 request only from independently verified P4-v4 request/result/verification evidence, and bind the verified loader request/child/env/cwd/sys.path to that handoff.

### HIGH — the pair verifier was not migrated at all and still proves the old world

`tools/g0/verify_r09_b2_p5_full_config_diff.py:13-23` still freezes `P4_DIR=artifacts/g0/r09/b2/p4_launch_d005`, the historical recurrent/TTT v2 record SHA values, and `r09_b2_p4_d005_verifier_v2`. `_evidence_records()` and `_expected()` continue to read those files, and `_bound()` continues to bind envelopes against D005-v2 fields.

This directly violates the v0.8 requirement that the **pair verifier independently** fixed-discover and recompute the P4-v4 request/result/verification chain, current source/staging/run-root bytes, staging manifest/readonly state, runtime sys.path, environment, native closure, and run-root roster. The verifier can still PASS an old-v2 envelope even when no P4-v4 execution-preflight exists.

Required fix: make P4-v4 preflight evidence the verifier's only P4 authority; historical v2 artifacts may remain inspectable history but cannot satisfy P5 verification.

### HIGH — `load_p4_v4_preflight()` is a top-level-shape check, not the v0.8 evidence verifier

`tools/g0/export_r09_b2_p5_resolved_config.py:62-114` checks regular-file/canonical-JSON, top-level key sets, backend/status, and request/result SHA links only. It does **not** verify the design's required nested schemas and verifier-owned truth, including:

- exact schema-version values;
- `path_identity` kind/root/resolved-root/identity SHA and non-overlap rules;
- production Git revision/Gitlink/submodule/TOML Git-blob/current-byte binding;
- request/result field equality except the explicitly result-owned fields;
- `request_defaults`, interpreter, loader argv and producer/verifier tool identity;
- `effective_environment.sha256` or `native_loader_environment`;
- payload/staging manifest and readonly tree;
- runtime sys.path exact mapping;
- native closure recomputation;
- pre-P5 run-root exact roster and mode/content checks;
- verification `checks` exact ordered PASS list;
- `verification_sha256` self-digest.

The permanent fixture at `tools/g0/test_r09_b2_p5_full_config_diff.py:22-45` is itself a concrete false-PASS proof: it supplies `{}` for `production_source`, `p4_run`, `p4_staging`, `request_defaults`, `interpreter`, `loader_argv`, `native_loader_environment`, `payload_manifest`, `producer`, `verifier`, uses `checks=[]`, fake digest strings, and a non-Git temporary evidence root; `load_p4_v4_preflight()` is expected to accept it. That is incompatible with the approved design.

Required fix: the positive fixture must contain the exact real schema shape and independently recomputable identities; every omitted/extra/forged nested field, shared replacement, Git/current drift, path/staging/roster/native-closure mutation must fail.

### HIGH — P5 environment projection is both under-bound and inconsistent with the approved grammar

`tools/g0/export_r09_b2_p5_resolved_config.py:75-89` validates neither `effective_environment.sha256` nor `native_loader_environment`; it only compares `set/unset/inherit_allowlist`. It also requires the complete recurrent/TTT `set` mappings to be identical, whereas v0.8 explicitly permits only verifier-owned P3/backend-specific entries to differ before constructing the P5 environment. Conversely, a pre-existing `LC_CTYPE` entry is silently overwritten by `{**left, **PYTHON_CHILD_LOCALE}` instead of treating locale drift/conflict as fail-closed.

More importantly, this computed environment is not used by `run_parent_export()`, which still spawns with the historical child request's `request["environment"]["effective"]`.

Required fix: derive the environment from independently verified P4-v4 evidence from an empty mapping, validate both environment digests/ordered unset arrays, admit only the exact verifier-owned backend-specific differences, reject locale conflicts, and use the exact derived mapping for native-closure resolution, child spawn, first-import equality, and envelope verification.

## Positive observations

- The implementation correctly introduces fixed backend directory literals and rejects symlinked/non-canonical JSON evidence files at the helper layer.
- The ordered native-loader/rank/PYTHONPATH forbidden-variable tuple matches the design's intended direction.
- No submodule change is present; Gitlink remains the frozen `21d064f...`.
- The request stays within root tooling/CPU-test scope and does not claim P4 preflight/P5 export/GPU/training execution.

## Gate decision

Remain fail-closed. This review does not authorize:

- P4-v4 record/refreeze or execution-preflight;
- P4 staging/run-root creation;
- P5 export or compose;
- `load_experiment_from_toml` execution;
- torchrun/distributed/CUDA/GPU;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- P5 closure;
- B2-T or Local Memory training.

A remediation submission should migrate both the real parent/child path and the independent pair verifier to the exact P4-v4 contract, then replace the permissive fixture with exact positive/negative schema/path/env/sys.path/roster/native-closure tests.
