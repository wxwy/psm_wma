# R09-B2 P4-v4 preflight v0.4 static tooling implementation review

## Request / implementation

- Request commit: `382ab2c1787d20538b64038ddbb661b297e9c5d3`
- Implementation commit: `010dfc7da60418586fb1270e2f05f104c9893179`
- Approved design: `5de996bf2c1e5b5b8ac11300b190d76eae8a21dd`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

`APPROVE_TO_CLOSE_P4_V4_PREFLIGHT_STATIC_TOOLS` is not authorized.

## Findings

### HIGH — PASS admission proves byte linkage, not that the payloads are valid final P4-v4/P5 evidence

`tools/g0/r09_b2_p4_v4_static_contract.py:32-51` checks the candidate directory file set, canonical JSON bytes, `candidate_link.json` SHA mapping, request backend, and `request.p4_run.run_token`. It does not validate the frozen final evidence contract for `request.json`, `result.json`, and `verification.json`: exact top-level key sets, PASS statuses, request/result SHA chain, verification checks/self-SHA, source/tool identities, run/staging binding, payload manifest/roster, runtime sys.path/environment, native closure, or other nested grammar already enforced by `load_p4_v4_preflight()`.

This is not theoretical: `tools/g0/test_r09_b2_p4_v4_static_contract.py:18-22` constructs a supposed PASS trio containing only minimal objects such as `{"backend": ..., "p4_run": ...}` / `{"backend": ..., "status": "PASS"}`. `stage_atomic_publication()` accepts them, while `tools/g0/export_r09_b2_p5_resolved_config.py:278-333` would reject those same bytes immediately because the final P4-v4 request/result/verification schemas are exact.

Required fix: candidate PASS validation must reuse or refactor the verifier-owned P4-v4 payload grammar so that the three bytes returned by `load_pass_candidate()` are already acceptable as final P5 evidence without any transformation. CPU fixtures must use a complete temporary source/run/staging/P4-v4 evidence object and add permanent negatives for malformed request/result/verification key sets, wrong status, broken SHA chain, verification checks/self-SHA, source/run/staging/roster/native-closure drift.

### HIGH — pair admission does not implement the frozen cross-backend invariants

`tools/g0/r09_b2_p4_v4_static_contract.py:63-66` only checks that the two directory names equal the backend set and then independently calls `load_pass_candidate()`. It never proves the design-required shared-source and existing cross-backend invariants.

Two individually link-valid candidates can therefore carry different production source identities, request defaults/interpreter identities, unrelated run/staging contracts, or an invalid recurrent/TTT environment relationship and still be returned as an atomic six-blob publication candidate. The frozen v0.4 design explicitly requires independent backend verification plus pair-level shared-source/cross-backend checks before publication admission.

Required fix: `stage_atomic_publication()` (or a verifier-owned helper it calls) must validate both complete P4-v4 payloads together using the existing pair grammar, including the shared production/source contract and the narrowly allowed backend-specific environment differences, before returning any six-blob publication object. Add shared-forgery/mismatched-source and backend-environment negatives.

### HIGH — FAIL candidate binding and permanent failure-poison are not implemented

`tools/g0/r09_b2_p4_v4_static_contract.py:54-60` validates only `failure.json`; it never canonicalizes or semantically validates the accompanying `request.json`, does not require the candidate directory itself to match the backend, does not bind `failure.run_token` to `request.p4_run.run_token` / run-root identity, does not require a 64-hex token, and does not validate the failure schema-version value. Candidate/root directory symlinks are also not rejected.

The current test is a direct under-validation example: `tools/g0/test_r09_b2_p4_v4_static_contract.py:42-45` uses an arbitrary `{"backend":"recurrent"}` request and even uses the candidate-link schema string in `failure.json`; `verify_fail_candidate()` still accepts it.

More importantly, there is no mechanism that can enforce the frozen poison rule across attempts: after a FAIL using a given attempt/token/run-root, a later PASS using the same token/run-root can be presented to `stage_atomic_publication()` and the helper has no history/poison input to reject it.

Required fix: define and validate the exact FAIL request/failure relationship, canonical non-symlink candidate paths, backend/path identity, 64-hex token, request token/run-root binding, and a verifier-owned poison mechanism/history scan that makes reuse of a failed attempt/token/run-root permanently inadmissible. Add negatives for wrong failure schema, non-hex token, request/failure token mismatch, directory symlink, and FAIL→PASS identity reuse.

### MEDIUM — the submitted CPU evidence does not cover several claimed/frozen negatives

The closure request says the two tests cover missing-backend fail-closed, but the committed tests do not exercise a missing backend. They also do not cover the v0.4 review hard constraints for link/path mismatch, candidate-directory symlink, non-hex token, malformed result/verification, cross-backend mismatch, or poisoned identity reuse.

The existing byte-drift and candidate-only top-key tests are useful, but 2/2 passing tests cannot support closure while the core final-evidence and pair semantics above remain untested.

## Positive observations

- The implementation is correctly static-only: no CLI, materialization, staging, preflight execution, refreeze, export, GPU, or training path was added.
- `candidate_link.json` is kept outside the publishable payload and hashes the original payload bytes, which is the correct basis for byte-preserving publication.
- The exact recurrent/TTT directory-set check is a useful first layer for all-or-none admission.

## Gate decision

Keep `G0-R09-B2-P4-V4-EXECUTION-PREFLIGHT` in review/remediation. Fix the static contract so PASS candidates are already fully valid P4-v4/P5-final evidence, pair invariants are verifier-owned, and FAIL poison is enforceable before requesting closure again.

Still unauthorized: real staging, candidate generation/execution, P4 preflight, record/refreeze/evidence publication, filling real P5 evidence authority, P5 export/compose, torchrun/CUDA/GPU, model/data/checkpoint I/O, training/evaluation/inference, B2-T, and Local Memory training.
