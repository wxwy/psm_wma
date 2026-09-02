# R09-B2 P4-v4 Execution Request `environment` v0.2 static closure review

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_ENVIRONMENT_STATIC_TOOLS`

Target:
- remediation implementation: `50d08df03d632ea4457cbefeccc97b9c3309fd4c`
- closure request / Inbox ledger: `2ff2b07d3c1c7452caa9592b0dc526fbc5ffc017`
- approved design: `61949b13b16310193466de0a2d60d031bd5fa9a8`
- design approval: `c6a12cd7bf2b112dc3f1c87c250dcbfbf22338f9`
- previous ChatGPT remediation review: `566aa754d4735772cfc6ab650a24965a27ff83fb`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Review scope

This review is intentionally narrow. The environment validator main logic was already accepted in the prior review; this pass rechecks only the three remaining frozen v0.2 permanent-fixture gaps and verifies no unrelated authority drift was introduced.

## Closure findings

All three remaining fixture gaps are now closed on the submitted SHA:

1. **Changed projected D005 value**
   - the permanent negative now mutates `HF_HUB_OFFLINE`, a non-excluded key that remains in the projected effective environment;
   - this exercises actual projected-set/source binding rather than only changing excluded `PYTHONPATH`.

2. **Top-level third backend roster**
   - the fixture adds an `unexpected` third key to the environment pair itself;
   - `validate_environment_pair()` rejects it through the exact pair schema `{recurrent,ttt_fast_weight}`.

3. **Locale ordering / ownership**
   - the request environment pair is asserted to contain no `LC_CTYPE`;
   - the validated pair is passed through the existing P5 `p5_effective_environment()` projection;
   - only that P5 projection injects `PYTHON_CHILD_LOCALE={"LC_CTYPE":"C.UTF-8"}`;
   - an ambient parent `LC_CTYPE` / `PYTHONPATH` shadow does not affect the result.

The earlier remediation matrix also remains present for inner/outer identities, P5 forbidden tuple ordering, empty allowlist, native-loader empty set, forbidden effective keys, unverified D005, D005 added/removed/backend/digest/projection/exclusion drift, excluded-key leakage, P3-owned backend difference, and ambient-parent independence.

No new production/runtime authority was added. The decision not to wire `load_execution_request()` to a concrete `authorities.d005_pair` here is consistent with approved v0.2: path/bytes/source identity for that named authority is explicitly deferred to the independent `authorities` section and must not be silently invented inside the environment Gate.

The frozen Gitlink remains exact at `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Authorization boundary

This verdict closes **only** the root environment static parser/validator and stdlib CPU regression scope.

It does **not** authorize:
- a real P4-v4 execution preflight;
- staging/materialization/candidate generation;
- record/refreeze/evidence publication;
- P5 authority population/update/export/compose;
- torchrun/GPU/CUDA;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- B2-T or Local Memory training.

The next execution-request sections (`run`, `candidates`, `backends`, `authorities`) remain independent Gates. A real CPU-only preflight must not be re-authorized until those sections, the complete request, and its authorities are separately closed and reviewed.
