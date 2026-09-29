# PSM-WMA V3 — H3-E Route-B Stage 3C multi-file video fix promotion

- Date: 2026-09-29
- Formal recovery root: `16f296cd959820c93ae36e9d8abf16546cd637ea`
- Formal recovery child/Gitlink: `ba1996c85cc4de41df2e8bd22c0289ea4deef736`
- Prior frozen child: `55582980b992dac10481b0ba9e86cd8075cef33c`
- Verdict: **APPROVE_TO_RESUME_H3E_ROUTE_B_STAGE3C_FULL_B1_H5_BUILD**
- Bookkeeping/review commits after this pair do **not** replace the formal pair.

## Why the prior Stage 3C was blocked

The prior builder used global `dataset_from_index` as the start frame inside a single camera
mp4. This failed when one camera stream was split across multiple files, because the mp4 requires
a file-local frame offset.

The affected production-train scope was 43 episodes in
`SlideDishwasherRack/20250820`, wrist camera file index 1.

Production `RoboCasaLeRobotDataset` remained valid and was not modified.

## Promoted fix

Child `ba1996c85cc4de41df2e8bd22c0289ea4deef736`:

1. requires per-camera `videos/{cam}/from_timestamp` in episode metadata;
2. converts it to a file-local start frame using `round(from_timestamp * fps)`;
3. decodes each camera mp4 using that local start;
4. remains fail-closed on missing/non-finite/negative local timestamp metadata;
5. leaves H5 schema, train enumeration, manifest semantics, production loader, Local/model/trainer
   untouched.

## Promotion evidence

CPU/static:

- 19/19 pytest PASS;
- both new regression tests executed, not skipped;
- ruff check PASS;
- ruff format --check PASS;
- git diff --check PASS;
- clean child worktree.

Exact multi-file regression:

- identity: `SlideDishwasherRack/20250820/ep_000461`;
- global source row: 76996;
- wrist file index: 1;
- wrist `from_timestamp`: 23.7 s;
- frozen fps: 20;
- computed file-local start: 474.

Frame equivalence:

- candidate-builder decode vs production loader: same shape;
- mean absolute difference: 0.0;
- max absolute difference: 0.0.

Targeted real-Wan2.2 GPU smoke on a fresh temp output:

- exact identities:
  - `SlideDishwasherRack/20250820/ep_000461`;
  - `CloseFridge/20250816/ep_000067`;
- `records_total = 9036`;
- `built = 2`;
- `failed = 0`;
- exact selected-full-id set;
- H5 attrs/schema/dtypes/endpoints/valid/finite PASS;
- `RoboCasaLatentReader` PASS;
- no-future-endpoint causality PASS.

Resume smoke:

- `built = 0`;
- `skipped = 2`;
- `failed = 0`;
- SHA256 unchanged;
- mtime unchanged.

This is sufficient to promote the candidate fix to formal Stage 3C recovery authority.

## Full Stage 3C resume authorization

Resume the original Stage 3C output:

`/mnt/data1/data_v2_0617/robocasa365_official_v30_wan2.2vae_latent_b1`

with the promoted child `ba1996c85cc4de41df2e8bd22c0289ea4deef736`.

Critical concurrency rule:

- do **not** run old child `55582980...` and new child `ba1996c85cc4de41df2e8bd22c0289ea4deef736` concurrently against
  the same output/worker partition;
- let old workers finish or stop them first;
- then rerun all 8 worker partitions under the promoted child.

Do not delete valid existing H5 files. The promoted builder validates and skips complete files.
The rerun is intended to fill failed/missing affected episodes while preserving valid assets.

The worker geometry remains frozen:

- `--workers 8`;
- worker indices 0..7;
- no `--limit`;
- no `--tasks`;
- no `--episode-filter`;
- no `--full-id-filter`.

## Stage 3C closure criteria remain unchanged

After all eight promoted-child workers finish:

1. exactly 9036 unique production-train H5 files;
2. no temp/partial files;
3. every worker final report has zero failures;
4. full 9036-file reader/schema/dtype/finite/endpoints validation PASS;
5. exact source/full-id coverage, no extra/missing/duplicate identity;
6. production `RoboCasaEpisodeCatalog` rebuild has 9036 episodes;
7. recomputed manifest digest must equal:

`a8cad3f053232b348ea155f15bf79c2c9cf807dedcf39b89e246b17e43f283df`

If the digest differs, stop and report
`H3E_ROUTE_B_STAGE3C_MANIFEST_MISMATCH`. Do not re-freeze the digest.

If all criteria pass, report `H3E_ROUTE_B_STAGE3C_CLOSED`.

## Still forbidden

Until Stage 3C closes:

- no production loader change;
- no Local/model/trainer change;
- no manifest re-freeze;
- no Stage-A H100 one-step warmstart;
- no H3-E 8×H100 integration smoke;
- no formal RoboCasa Local-TTT training.
