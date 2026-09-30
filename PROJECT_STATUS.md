# PSM-WMA Current Project Status

Updated: 2026-09-30

## Current V3 H100 route

| Item | Value |
|---|---|
| Formal root | `e272a589ce2204f5b4324e79c0f1227d855f3e97` |
| Cosmos child / Gitlink | `f89876a4bb013d9a48d622db776996ded295884b` |
| RoboCasa train catalog | `9036` target-atomic train episodes |
| B1 H5 cache | `9036/9036` valid; manifest `a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df` |
| H100 Stage-A | regenerated Edge/raw15 one-step authority; Stage 3D CLOSED |
| H3-E | **CLOSED**: 8×H100 fresh iter1 + same-job resume iter2 PASS |
| H3-E smoke budget | fresh iter1 + same-job resume iter2 only |
| H3-F formal launcher | **V2-semantic generation + Local-TTT READY / 30k AUTHORIZED**, max_iter=30000, SAVE_ITER default=500 |
| H3-F trainable profile | V2 semantic generation/action + V3 Local four blocks; reasoner frozen |
| H3-F data profile | official_v30 / 9036 / raw15 / current manifest; intentionally not V2 ego20D |
| H3-F mesh profile | dp_shard8 for generation + Local slow params; intentionally not V2 Local replicated mesh |
| H3-F checkpoints/eval | `1000, 2000, 4000, 8000, 12000, 16000, 20000, 24000, 30000` |
| H3-F current-profile readiness10 | **CLOSED** on `e272a589/f89876a4`; 8/8 PASS, generation/action/Local gradients non-zero |
| H3-F 30k Gate | **APPROVED**: `APPROVE_TO_START_H3F_FORMAL_30K_V2_SEMANTIC_GENERATION_LOCAL` |
| H3-F old-profile readiness10 | **CLOSED** on `42289907/00241445`; retained as runtime/timing baseline only |
| H3-F long-run started | **false; formal 30k authorized on `e272a589/f89876a4`** |

The 30k budget applies to the future RoboCasa H3-F formal Local-TTT training run. Historical
LIBERO 5000-step planning/evidence below remains a historical snapshot and is not the current
RoboCasa training budget.

## Historical 2026-09-19 training implementation

| Item | Value |
|---|---|
| Cosmos child | `8c07e9ecf3c0815c9f54839c4474813fc3bcb0d7` |
| Topology | `8 ranks / 8×H100 single node` |
| A2 layout | stable-slot synchronized `[B_stream,T]` |
| Per-rank geometry | `B_stream=8`, `T=16`, `GA=2` |
| Per-rank consumers / update | `256` |
| Global consumers / update | `2048` |
| Catalog policy | global per-suite catalog → deterministic disjoint rank shards → rank-local stable slots |

## Historical 2026-09-19 validation status

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
