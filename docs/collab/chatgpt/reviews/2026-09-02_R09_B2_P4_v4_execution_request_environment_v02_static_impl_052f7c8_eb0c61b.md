# R09-B2 P4-v4 Execution Request `environment` v0.2 static implementation review

## Verdict

`REQUEST_CHANGES`

Target:
- implementation: `052f7c8f0149d6a6f703fcbec86b8085357f7e15`
- request: `eb0c61bfdcf5f3ef6b4f45eec477135c4a831a94`
- approved design: `61949b13b16310193466de0a2d60d031bd5fa9a8`
- design review: `c6a12cd7bf2b112dc3f1c87c250dcbfbf22338f9`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Accepted implementation

No new code-level blocker was found in the narrow environment authority logic:
- `validate_environment_pair()` hard-requires the existing D005 `verify_pair()` to return PASS;
- the D005 input key universe is bound to `REQUIRED_ENV ∪ P5_P3_BACKEND_ENVIRONMENT`;
- only `IMAGINAIRE_OUTPUT_ROOT` and `PYTHONPATH` are excluded from the environment projection;
- `effective_environment` / `native_loader_environment` reuse the exact P5 forbidden tuple, empty inheritance, and native empty-set grammar;
- the projected environment is bound by D005 digest, input-set digest, projected-set digest, backend, exclusion list, and projection self digest;
- the pair admits only the P3-owned `PSM_R09_B1_TTT_ENABLED` difference (`0` vs `1`).

The implementation remains static-only; `main()` is still hard-stopped and this review does not authorize execution.

## HIGH — approved v0.2 permanent fixture matrix is not closed

The approved v0.2 design made a substantially larger permanent CPU negative matrix part of closure. At `052f7c8`, the new environment tests contain only three test functions and cover primarily:
- positive path with mocked D005 PASS;
- mocked D005 FAIL;
- one unreviewed effective-set key;
- projection extra key / malformed D005 digest.

That does not close the frozen matrix. Missing targeted permanent regressions include at least:

1. Inner and outer identity/digest drift separately:
   - `effective_environment.sha256`;
   - `native_loader_environment.sha256`;
   - `d005_projection.sha256`;
   - section `identity_sha256`.
2. Exact P5 grammar:
   - forbidden tuple omitted / extra / reordered;
   - non-empty `inherit_allowlist`;
   - non-empty native `set`;
   - forbidden key inserted into effective `set`.
3. Ambient-parent irrelevance:
   - mutate `os.environ` (including forbidden/PYTHONPATH/loader variables) and prove the accepted projected result is unchanged.
4. D005 projection source mutations with the outer identities recomputed so the intended branch is exercised:
   - added D005 set key;
   - removed required D005 set key;
   - changed required fixed-value key;
   - wrong D005 backend;
   - wrong but well-formed `d005_sha256`;
   - wrong `input_set_sha256`;
   - wrong `projected_set_sha256`;
   - changed/reordered `excluded_keys`.
5. Excluded-key ownership:
   - `PYTHONPATH` leaking back into effective set;
   - `IMAGINAIRE_OUTPUT_ROOT` leaking back into effective set.
6. Pair invariants:
   - missing `PSM_R09_B1_TTT_ENABLED`;
   - recurrent/TTT values reversed;
   - a third effective-set backend difference;
   - malformed/third backend pair key.
7. Locale boundary:
   - `LC_CTYPE` present in request effective set must fail;
   - `LC_CTYPE` must remain a P5 projection-time injection only, not request authority.

The request reports `24/24 PASS`, but passing count is not a substitute for the fixture matrix explicitly frozen by the approved design.

### Required remediation

Static/CPU only:
- add the missing permanent fixtures above;
- for every request mutation, recompute the relevant inner SHA(s) and outer `identity_sha256` unless that digest itself is the mutation target;
- make each test fail on the intended environment/D005/pair branch, not an earlier outer identity guard;
- retain all existing entry/source/interpreter regressions.

No real P4 preflight, staging/materialization, candidate generation, record/refreeze, evidence publication, P5 authority/export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized.