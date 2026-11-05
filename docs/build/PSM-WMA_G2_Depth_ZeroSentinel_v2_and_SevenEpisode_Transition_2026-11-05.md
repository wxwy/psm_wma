# G2 Issue #19 — Depth v2 and seven-episode transition plan

Status: implementation candidate; author CPU evidence and fresh review required.
Scope: isolated `v3-g2-codex-depth-zero-sentinel-20261105`, Draft PR #20 against
`v3-g2-spatial-policy-20261104`. No V3 merge, nav_sg, training, source-data edit,
GPU execution, legacy conversion or production resume is authorized here.

## Authority and frozen inputs

- Issue #19: https://github.com/wxwy/psm_wma/issues/19
- Owner decision: `docs/collab/chatgpt/reviews/2026-11-05_G2_Uint16_Depth_ZeroSentinel_No_Stored_Valid_Owner_Decision.md`
- Stopped batch evidence: `docs/collab/chatgpt/reviews/2026-11-05_G2_Batch000_GPU456_Export_Stopped_Uint16DepthRange.md`
- G2 base Root: `9568723fd19d008be180c7b3e4126e1176c07d26`.
- Historical spatial-v2 implementation: `3eb8b334150018212ae1f51afb5e954b83fa1186`.
- Child/Gitlink unchanged: `1069fe78841228cadbbfbe6afbd767eaed6225da`.
- Owner output root remains
  `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-depth`.
- Batch000 selection: 100 episodes / 24,059 frames; SHA256
  `8561c81b0382bf79d360f5028d6fa67ab2848589bf77199f9d3f97861e760080`.
- Reported retained v1 output: seven completed episodes / 2,353 frames, plus
  `.failed` and `.staging`. These are server facts supplied by the review, not
  an inventory independently read or migrated by the cloud author.
- The active production reserve is 100 GiB per the stopped-batch contract.
  Older exploratory 1 GiB reserves or four-hour/25 GiB limits are not reinstated.

## Codec and verification contract

`psm_wma_robocasa_rgbd_pose_v2` is a new, incompatible cache schema. Each NPZ has
exactly `depth`, `K`, `T_world_camera_gl`, `T_world_camera_cv`, `frame_indices`.
K and both poses stay float32; frame indices stay int64. No persistent boolean
mask or alternative per-pixel JSON mask is added.

For uint16, finite renderer-valid optical Z in [0.001, 65.535] m is rounded to
nearest millimeter. Renderer-invalid and out-of-range values become 0. There is
no clipping, modulo conversion, rescaling, camera-plane change or format fallback.
The in-memory mask is `depth > 0`, and quantization error remains <=0.0005001 m.
A nonfinite value marked renderer-valid remains a malformed-input error. The
native buffer conversion already marks nonfinite/background pixels invalid.

Float32 retains finite positive representable Z, including >65.535 m and <1 mm;
its validity is also derived from positive depth. Float32 overflow or underflow
to zero is rejected. Compression is lossless for encoded arrays, not for the
original floating depth quantized to millimeters.

Frames record disjoint source counts (renderer-invalid, below 1 mm, above
65.535 m, encoded-valid), raw finite min/max and the exclusion fraction. A >1%
range-exclusion diagnostic is explicit; lower fractions and counts remain visible.
Episode manifests aggregate counts per camera. Offline verification checks the
counts, totals, five-array set, dtypes, file hashes and identity. Only native
replay can validate the claimed source classifications against the renderer.

Spatial verification compares saved validity with representability-filtered
renderer validity. Independent rays, K/Pose, source binding, frame ordering and
projection remain mandatory with unchanged thresholds (1 cm, minimum 16 rays).
Filtering every point cannot yield PASS. RGB MAE/PSNR/SSIM remain nonblocking
photometric diagnostics; external human review is never synthesized by the tool.

Two 256x256 cameras require 262,488 raw array bytes/frame for uint16, or 524,632
for float32, including calibration and indices. Compressed disk cost must be
measured anew; removing a compressible boolean array does not establish a fixed
compressed-size saving.

## Auditable transition proposal — NOT an executed migration

The current implementation **rejects v1**, including direct per-episode export
into a root with a v1 manifest, before creating locks or new data. An unidentified
nonempty CLI output root is also rejected. No seven-episode rewrite, deletion,
new production namespace or automatic cache adoption is implemented.

A conversion/promotion tool is a follow-up only after separate approval. Its
minimum auditable procedure is:

1. Freeze a server-local, read-only inventory: seven exact IDs, 2,353 frames,
   all file hashes, root/episode manifests, original producer code identities,
   `.failed` and `.staging`. Stop only an owned exporter if separately authorized.
   Verify the retained v1 format using its frozen reader; preserve the inventory.
2. For every frame and camera, prove `legacy_valid == (legacy_depth > 0)` and
   expected uint16 dtype/shape, calibration, frame indices and complete source
   bindings. Reject any mismatch. Do not guess whether an old positive depth is
   valid, saturated or wrapped; the original strict producer must be identified.
3. Build a separate server-local staging generation, never edit the current
   root. Remove only the redundant mask and preserve depth/K/poses/indices
   bit-for-bit. Derive counts from verified legacy arrays and original frame
   statistics **only if** the frozen producer proves all valid pixels were in
   range (the v1 encoder rejected such overflow). Otherwise replay that episode
   under a separately authorized native check; do not invent exclusion counts.
4. Record original root/episode hashes, actual legacy producer, conversion code,
   new codec and conversion time as lineage. Regenerate all v2 identities,
   checksums and COMPLETE markers coherently. A separately reviewed tool must
   demonstrate that its target root contract/recipe and episode digests match
   subsequent v2 CLI expectations without pretending that migration was native
   re-rendering. This proposal alone does not establish that compatibility.
5. Verify the new generation with the strict v2 reader, compare all retained
   numeric arrays and indices bitwise, and compare seven IDs/frame totals. A
   synthetic fixture or offline checksum does not replace the native 736 check.
6. A later approved promoter may switch complete directory generations on the
   same filesystem using supported atomic `renameat2(RENAME_EXCHANGE)`, with a
   durable journal and parent-directory fsync. The old generation remains intact
   under its exchanged staging/archive path, including failures and staging.
   Recover by journal and hashes after a crash. **Two ordinary renames are not
   claimed atomic**. If atomic exchange is unavailable, stop for an explicitly
   approved alternative namespace/promotion design; do not silently improvise.
7. Retain the old generation and audit receipt for rollback. Do not delete it or
   resume Batch000 as part of conversion. Production resume needs its own
   authorization after new code/native acceptance and capacity checks.

This plan supplies the safe transition deliverable requested by Issue #19;
there is deliberately no automatic or in-place converter in this PR.

## Author CPU checks and native acceptance boundary

The author suite executes the real exporter, cache reader and spatial verifier
with synthetic parquet/state/RGB fixtures. It covers representability boundaries,
raw source counts, both formats, chunk32/terminal chunks, all-zero rejection,
identity/schema corruption, unchanged K/Pose/indices, immutable skip and v1
root/episode refusal. Existing failure/recovery, disk, source and spatial-policy
regressions remain in the suite.

The synthetic global-ID-736 fixture places 25 values of 591.547 m at wrist frame
73 and 230 values of 614.359 m at 74, reflecting the reported failure. It is not
the real episode (local ID 234, 230 frames). Native acceptance must later use
that exact recorded episode on the server, verify excluded pixels are zero,
inspect fresh renderer/source counts, retain unchanged calibration and mapping,
and pass independent geometry on representable pixels. No sensor data leaves
the server. Historical Gate B/C reports remain immutable and do not certify v2.

Deliver exact implementation Root + unchanged Child/Gitlink, diff, raw CPU JUnit
and lint logs, this proposal and a fresh review request. Stop at review; no
server export, migration, production resume or V3 merge follows automatically.
