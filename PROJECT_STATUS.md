# PSM-WMA Current Project Status

Updated: 2026-09-19

## Current training implementation

| Item | Value |
|---|---|
| Cosmos child | `8c07e9ecf3c0815c9f54839c4474813fc3bcb0d7` |
| Topology | `8 ranks / 8×H100 single node` |
| A2 layout | stable-slot synchronized `[B_stream,T]` |
| Per-rank geometry | `B_stream=8`, `T=16`, `GA=2` |
| Per-rank consumers / update | `256` |
| Global consumers / update | `2048` |
| Catalog policy | global per-suite catalog → deterministic disjoint rank shards → rank-local stable slots |

## Validation status

| Gate | Status |
|---|---|
| Historical single-rank engineering delivery | **PASS** |
| Historical single-rank exact resume | **PASS** |
| Historical single-rank 20-step budget | **PASS** |
| Historical single-rank 5000-window planning | **PASS** |
| 8-rank code adaptation | **IMPLEMENTED** |
| 8×H100 runtime smoke | **PENDING** |
| 8-rank 20-step timing/resume | **PENDING** |
| 5000-step training started | **false** |

The 8-rank adaptation does not use a frozen Git SHA as a training gate. Current root/child SHAs are logged at launch for reproducibility.

## Historical reference evidence

- Reference implementation root: `2a9df880713da179aee141dd97c6b20a2b1d8c2e`
- Reference child: `22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e`
- Delivery verifier: `artifacts/g0/sync_a2_final_verification_2a9df880_v3.json`
- Long-run verifier: `artifacts/g0/a2_long_run_readiness_2a9df880/a2_long_run_readiness_v1.json`
- Full-catalog 20-step single-rank measurement: `176.059 s/step`, peak allocated `45.045 GiB`

Those measurements are not presented as 8×H100 throughput measurements.
