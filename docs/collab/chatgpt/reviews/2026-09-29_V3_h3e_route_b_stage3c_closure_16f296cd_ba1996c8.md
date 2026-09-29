# PSM-WMA V3 — H3-E Route-B Stage 3C full B1 H5 cache closure

- Date: 2026-09-29
- Formal implementation root: `16f296cd959820c93ae36e9d8abf16546cd637ea`
- Formal child/Gitlink: `ba1996c85cc4de41df2e8bd22c0289ea4deef736`
- Bookkeeping closure commit after this pair does **not** replace the formal pair.
- Verdict: **H3E_ROUTE_B_STAGE3C_CLOSED**
- Next gate: **APPROVE_TO_RUN_H3E_ROUTE_B_STAGE3D_H100_STAGE_A_WARMSTART**

## Final Stage 3C asset state

Frozen source:

`/mnt/data1/data_v2_0617/robocasa365_official_v30`

Frozen B1 cache:

`/mnt/data1/data_v2_0617/robocasa365_official_v30_wan2.2vae_latent_b1`

The original 55582980 workers naturally completed with 8993 valid files and exactly 43 failures.
All 43 failures were the previously isolated multi-file wrist-video cases under
`SlideDishwasherRack/20250820`.

The promoted child `ba1996c85cc4de41df2e8bd22c0289ea4deef736` then resumed all eight frozen worker partitions. It rebuilt
exactly the 43 missing/failed episodes and validated+skipped the existing 8993 files.

Final physical state:

- H5 files: 9036;
- temp/partial files: 0;
- task/date cache directories: 18;
- duplicate relative identities: 0.

## Full 9036 contract validation

Every one of the 9036 files passed:

- exact `episode_id`;
- exact `frame_count`;
- `temporal_compression_factor = 4`;
- `source_frame_to_latent_policy = "causal_endpoint"`;
- left + wrist fp16 latent `[N,48,16,16]`;
- int64 exact endpoint vector `0,4,8,...` plus terminal `F-1` when required;
- bool valid mask all true;
- finite latent values;
- `RoboCasaLatentReader` load;
- finite visual96 summaries.

Coverage result:

- total = 9036;
- valid = 9036;
- invalid = 0;
- missing = 0;
- extra = 0;
- duplicate = 0.

## Manifest gate

Production `RoboCasaLeRobotDataset` + `RoboCasaEpisodeCatalog.from_stage_a_dataset` under the
frozen Stage-A contract produced:

- catalog episodes = 9036;
- tasks = 18;
- manifest digest =
  `a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`.

This exactly matches the pre-existing frozen manifest authority. No digest re-freeze occurred.

Therefore Stage 3C is closed.

## Stage 3D authorization

Authorize one H100 Stage-A Edge/raw15 one-step warmstart regeneration.

This Gate exists because the original Stage-A config/DCP paths lived on the old /disk/rl machine
and are unavailable on the H100 host. The goal is to recreate an H100-local Stage-A asset under
the already closed Stage-A raw15 contract, not to change or re-evaluate Stage-A semantics.

Use the existing repository entrypoint:

`examples/psm_wma_robocasa_native.py`

with:

- task = `CloseFridge`;
- steps = 1;
- dataset root = the current canonical H100 v3 source;
- local Cosmos3-Edge-Policy-DROID asset;
- local Edge-Policy-DROID base DCP that passes `check_droid_dcp`;
- local Wan2.2 VAE;
- exactly one authorized H100;
- a fresh output root outside the root/child worktrees.

CPU/dryrun preflight must pass before CUDA is used.

Stage 3D closure requires:

1. generated `config.yaml` records the exact frozen raw15 Stage-A contract;
2. `iter_000000001` exists and has complete DCP model/trainer metadata;
3. one-step loss is finite;
4. trainable gradients are finite/non-empty;
5. DCP model metadata includes the required host/action keys and no Local-memory keys;
6. no Local-TTT/grouped trainer path is involved;
7. the exact output config + iter1 DCP are preserved as H100 Stage-A authority;
8. report exact local asset paths and SHA/digests needed by later H3-E preflight.

Do not claim bitwise equivalence to the old /disk/rl Stage-A checkpoint. This is a regenerated
H100-local warmstart under the same frozen contract.

## Still forbidden during Stage 3D

- no Local-TTT training;
- no H3-E 8×H100 fresh/resume smoke;
- no production loader change;
- no B1 cache change;
- no manifest change;
- no longer Stage-A training run;
- no RoboCasa SR/capability claim.
