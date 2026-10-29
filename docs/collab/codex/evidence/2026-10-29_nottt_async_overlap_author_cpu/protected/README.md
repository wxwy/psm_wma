# Final release protected-source and fixture audit

This is **INTERNAL_AUTHOR_READONLY_STATIC_AUDIT_NOT_GPT_CODE_GATE**. The probe
uses only standard-library AST/hash operations and `git` reads of frozen objects.
It imports no project code and executes no tests, model, GPU or DCP operations.

Exact frozen comparison:

- Baseline Root `3d5806a2b702b42d3f24e7645aa7cec9cd70b0c7`, Child/Gitlink
  `746c5cf2f2324104a62fb71510343aa40d3976c5`.
- Final Root `e0fe911dfb9fd34957234828195cf051713f6c3d`, Child/Gitlink
  `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`.
- Last production Child before the fixture-only release:
  `d64e5c1d8541341b26f6ef0557822fe76d8dd52d`.

Reproduce using any checkout containing those Git objects:

```bash
python probe.py --root-worktree /workspace/psm-wma-nottt-async --output audit.json
```

`audit.json` binds the probe script's SHA256 and both Root Gitlinks. It records
51 passing equality checks. These include 14 protected Child files and 5 Root
files compared byte-for-byte with SHA256/Git Blob identities, unchanged source
subtrees, and exact or explicitly normalized protected-function ASTs.

The two fixture-corrected test files are intentionally **excluded from the
byte-identical table**. They have separate full before/after Blob and SHA256
witnesses, every old test function and every old `assert` AST is recorded, and
whole-module AST equivalence is required after only these exact normalizations:

1. In `examples/psm_wma_robocasa_matched_no_ttt_test.py`, remove the exact
   `make_dataclass` import and exact new `_structured_identity_fixture` helper;
   remove only the config conversion assignment and the two temporary receipt
   creation statements from the affected identity test. Assertions are retained.
2. In `tools/v3/no_ttt_workers_entry_test.py`, reverse exactly one `_args` input
   Job-name literal in the identity-negative test: the ordinary strict namespace
   replaces the existing Owner-exempt formal Job. No assertion or exception
   expectation changes. Other formatting/comments do not affect ASTs.

Those two modules retain all 25 old test functions and all 88 old `assert`
statements. The pre-existing Resume module separately retains all 3 old test
functions/decorators and its 14 `assert` statements; its complete module AST
matches after removing only the exact explicit legacy-RAW fixture injection.
Thus the three changed historical test modules preserve all 102 old assertion
ASTs. All untouched functions remain identical, and normalized changed test
functions are identical as well. Other protected regression files remain
byte-identical; their assertions are not included in the 102 subtotal.

For `d64e5c1...` to final `f6a92d4...`, the sole changed Child path is the Example
test fixture above. All other **1244 Git path/object entries** match, and the five new/modified
production files also have direct byte/SHA256 equality witnesses. The final
release therefore does not alter production code relative to `d64e5c1...`.

The CPU runner explicitly deselects the unchanged pre-existing optional
`test_optional_real_data_debug_smoke` node because this task forbids scientific
assets. The audit records the single exact selector and unchanged test-file
bytes. That node is neither deleted nor counted as executed PASS. This static
audit does not certify the runner's test results, native DCP Resume, CUDA RNG
restoration, actual GPU overlap or performance.

The earlier protected audit remains separately retained for its original
Root `66986d5f...` / Child `5124a2b7...`; it must not be presented as this release's
final audit.
