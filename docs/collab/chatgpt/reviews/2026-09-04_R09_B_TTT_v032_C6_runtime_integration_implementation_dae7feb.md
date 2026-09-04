# R09-B TTT v0.3.2 C6 runtime integration implementation re-review

- Gate: `G0-R09-B-TTT-V032-C6-RUNTIME-INTEGRATION-IMPLEMENTATION`
- formal root: `dae7feb3fbfaccf3837b55d1248d046c54c6aaa1`
- child/Gitlink: `ea152b6eab9296c3fc4dd7cf98fbd5b5ffd52ae7`
- frozen design: C6 v0.4 `574d28750883d9e69bd03aa39cc3640646190dfa`
- verdict: `REQUEST_CHANGES`

## Closure status

- pending `done` exact-snapshot evidence: CLOSED. Snapshot now includes pending phase/rows/validity/witness shape and verifies no mutation.
- backward-failure/abort rollback evidence: CLOSED. Abort is checked against the committed baseline.

## Current blocker

### HIGH — Local-disabled parity remains synthetic self-equality, not behavioral seam evidence

**Location:** `cosmos_framework/model/generator/mot/c6_runtime_adapter_test.py:~263-273`, `test_local_disabled_parity_is_zero_write_no_memory_path`.

**Root cause:** the test constructs `disabled_packed = (sample.clone(), None)` and `baseline_packed = (sample.clone(), None)` locally, then computes the same square-mean loss on both. No disabled/no-memory public path produces either packing or loss; the C6 adapter is only touched for zero-write/reset assertions.

**Frozen contract violated:** C6 v0.2 §5/§6 requires the Local-disabled synthetic path to preserve no-memory **input/packing/loss parity** and requires direct behavioral Evidence. Hand-constructing two identical tuples proves only test-local equality, not path parity.

**Acceptance:** add one C6 synthetic public-seam fixture in which the same synthetic input is run through the actual disabled/bypass path and the corresponding no-memory baseline path, and compare the resulting packed inputs and scalar loss exactly while proving zero C5 writes/no pending state. Do not require production runtime changes; this is tests/Evidence-only remediation.

No production-code blocker found in the reviewed delta. Scope remains synthetic C6 only; active Cosmos runtime/GPU/training/eval/inference remain prohibited.
