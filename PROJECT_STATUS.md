# PSM-WMA Current Project Status

Updated: 2026-09-19

## Canonical implementation

| Item | Value |
|---|---|
| Implementation root | `2a9df880713da179aee141dd97c6b20a2b1d8c2e` |
| Cosmos child | `22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e` |
| A2 layout | stable-slot synchronized `[B_stream,T]` |
| Default geometry | `B_stream=8`, `T=16`, `GA=16` |
| Consumers / update | `2048` |

## Readiness

| Gate | Status |
|---|---|
| Engineering delivery | **PASS** |
| Exact resume | **PASS** |
| Full-catalog 20-step budget | **PASS** |
| 5000-window capacity + epoch reuse | **PASS** |
| Long-run readiness | **READY_FOR_LONG_RUN** |
| Long-run authorization | **true** |
| 5000-step training started | **false** |
## Current measured values

- Full-catalog A2 20-step wall time: `176.05919465 s/step`
- Full-catalog A2 peak CUDA allocated: `45.045145 GiB`
- Base 5000-step projection: `10.1886 days`
- The projection excludes evaluation and checkpoint overhead.
- The observed B1→A2 `1.369×` speedup belongs only to the matched 10-episode/suite control and is not a full-catalog speedup claim.

## 5000-window planning witness

- Windows completed: `5000 / 5000`
- Native groups: `80,000`
- Logical segments: `640,000`
- Consumers: `10,240,000`
- Per stable slot: `80,000` segments
- Per suite exposure: `2,560,000` consumers
- Chronology errors: `0`
- Group-shape errors: `0`
- Queue replay mismatches: `0`
- Final slot epochs: `{0:27, 1:63, 2:45, 3:60, 4:28, 5:60, 6:46, 7:60}`
## Canonical evidence

- Delivery verifier: `artifacts/g0/sync_a2_final_verification_2a9df880_v3.json`
- Long-run verifier: `artifacts/g0/a2_long_run_readiness_2a9df880/a2_long_run_readiness_v1.json`
- GPU control: `artifacts/g0/sync_a2_gpu_control_2a9df880/`
- GPU resume: `artifacts/g0/sync_a2_gpu_resume_2a9df880/`
- Full-catalog 20-step budget: `artifacts/g0/sync_a2_budget20_2a9df880/`
- 5000-window planning: `artifacts/g0/a2_long_run_readiness_2a9df880/`

See `artifacts/CANONICAL.json` for machine-readable pointers.

## Current research boundary

The Local Memory A2 stage is engineering-complete and ready for the long run. The actual 5000-step result and LIBERO success-rate conclusion are not yet available. Persistent Spatial State and Action-conditioned World Model are later project stages and are not claimed complete by this status.