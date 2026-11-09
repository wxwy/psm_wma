# G2 F3 author A/B results — pending independent review

This records Codex author measurements, not a GPT independent verdict.
Native implementation: `abcc87ca636c81455f397e8b0813522c70874c00`.
PSM implementation/build helper: `72b223499ae6fd080a337dafe0bb60f9f879c953`.
Draft PRs: [nav_sg #9](https://github.com/wxwy/nav_sg/pull/9) and
[PSM-WMA #34](https://github.com/wxwy/psm_wma/pull/34), both unmerged.
The production Gitlink remains `1ca308055fc41fb69efaeb9efaa23808f164a18e`.

## Implementation and source identity

The single existing native ColorCloudMap is tested at 0.05/0.02/0.01m.
Navigation geometry, Room/SG/Island algorithms and their parameters are
unchanged. Default color leaf remains 0.05m; 0.005m is untested. Fusion is
measured separately from the existing 2Hz publication, conversion and export.
Telemetry is opt-in, bounded, and includes actual queue overwrite/clear/stop/
reject outcomes rather than interpreting publication as fusion.

Source-bound color snapshots contain native RGB-D observations only. A separate
explicitly labelled MuJoCo source-GT geometry path receives those already fused
colors without another map/cache, re-fusion or voxel-size change. Source-GT
structures and object identities are not YOLOE/SigLIP observations. The bridge
checks raw RGB/depth/pose/K, encoding/layout, source time, frame identities,
terminal counts, original compressed model/state and strict rebinding proofs.
No model/GPU/asset-texture color/extra view interpolation was used.

The code was published before execution, then delivered inward as scoped
immutable archives because server Git fetch could not use its expired VSCode
credential socket. No credentials were inspected. All308 native runtime Git
blobs and60 PSM runtime Git blobs matched their fixed trees; the isolated
build overlay matched native bytes. This is an archive run, git_checkout=false.
The153-file active C++ source fingerprint is
`49335ae314ae1f6a51e6a586cb05fa0f490332bc35bd7d50747fec80c560ecfa`.
The reused external Patchwork source SHA256 is
`7dc34ef8a4f40e3c1b83c174ddd1d56cd3852df9ad03c477b4c67de65b683d3d`,
matching F2.

After all runs,153 active native source files,153 build-overlay files and all60
PSM runtime files were rehashed against the fixed source pair and still match.
The final_source_readback.json receipt SHA256 is
e0cec5096930f011687ab3073096bf4b5ef0d1b7a4512dc8ddb176e22c8c463e.

Formal source edits occurred only in the development repositories. Server
work used new isolated directories and immutable source packets; no server
source checkout, original data or production cache was edited. All original
MJCF/assets/states/images/clouds and raw outputs remain on data. This repository
contains own-fixture evidence plus derived aggregate/count/hash facts.

## Tests and actual native runs

- Native173 distinct C++ tests pass locally and on the server, retaining all168
  original IDs. Catkin's346 summary double-counts wrappers; it is not346 distinct.
- Native121 Python data/GT tests pass, retaining all106 collected baseline IDs.
- PSM553 Python tests pass, retaining all517 original IDs. No failures/errors/skips.
- Three own-fixture leaves each integrate4frames, export2color+2normal snapshots,
  and reject16 malformed bindings. Separate worker smoke checks overwrite,
  clear/stop, reject and independent publication accounting. Two actual own
  RGB-D→native GT→sealed bundle→view roundtrips pass.
- Author peer code/evidence review closed all scoped P0/P1/P2; it did not
  independently rerun the private server scenes.

Noetic uses Python3.12.16/NumPy2.5.4 with a separate MuJoCo3.3.7 overlay. Producer
and verifier use the same serializer runtime: a different Python/NumPy pairing
caused23 quaternion last-bit SHA mismatches and was rejected, without tolerance.
All201 recorded RGB-D frames and49/106 source-GT entities/states verify in the
matched runtime. The published CMake helper repairs a legacy GTest imported
location containing a target name into the same installed library's physical
path. No native/test source changes were made to obtain the server build.
Earlier failed dependency/GTest configuration attempts remain in server logs.

The same first201frames (0..200) of each F2 RGB-D source are used:
Layout1 PickPlaceDrawerToCounter global005077 and Layout10 CloseBlenderLid
global000001, agentview_left. Exact cached input hashes match F2. Each leaf uses
a fresh process, CPU affinity0/1, one BLAS/OMP thread, no GPU.

All6runs receive/dequeue/integrate201/201. Each has zero skip, rejected input,
overwritten pending frames and residual pending work, and11 successful color
snapshots at source frames0,20,...,200:66 total. This is ACK-paced replay, not an
unthrottled live-camera loss guarantee. Color publication stays2Hz; actual
publication counts19/20 reflect the wall-time throttle rather than dropped
fusion frames.

At all11 checkpoints per layout, recorded navigation grids and emitted SG
summaries are byte-identical across leaves. This comparison does not certify
navigation tasks, genuine model observations or full semantic stability.
Layout1 normal exports pass33/33. Layout10 normal exports pass0/33 (33 refusals) with the
same F2 reason, `native object identity/geometry/mode conflict`; source-GT
preview success does not close this normal-path Gate.

|Layout|leaf cm|final color voxels|native node peak MiB|fusion CPU p50 ms|normal RPC p50 ms|replay wall s|
|---|---:|---:|---:|---:|---:|---:|
|1|5|4010|199.28|6.99|44.25|10.54|
|1|2|25301|204.00|7.59|93.75|10.60|
|1|1|101252|228.77|7.30|227.64|11.69|
|10|5|2041|209.61|5.35|41.47 refused|10.61|
|10|2|12732|209.66|6.87|38.11 refused|10.59|
|10|1|57644|221.02|8.29|38.48 refused|10.71|

Fusion n=201/run, RPC n=11/run. Layout10 RPC is refusal latency.
Layout1 normal export at1cm costs about5.1×5cm, and replay wall time rises11%.
The1cm Layout1 source-tick capture interval median is1.119s, p95 1.187s.
Do not infer zero performance impact or a live1Hz guarantee from zero overwrites.

## Four-frame view comparison and measured failure of1Hz

The existing N6 four-frame quality scope (each layout frame0/200) is rendered
at all3leaves:12 cases. All66 native source-time color snapshots are retained;
optional intermediate-time six-view rendering was stopped after the12 required
cases. No66-rendered-snapshot claim is made.

There are72 direction records:36 generated PNGs,36
SKIPPED_NO_PROJECTABLE_OBJECT directions with metadata/missing masks and noPNG,
and zero UNKNOWN_NOT_OBSERVED directions in these particular twelve cases.
All36 PNGs were read back with color/geometry masks and exact RGB membership
checked against the corresponding native observed cloud. Existing tests also
cover objects present without observation, which must stay UNKNOWN with noPNG.
Each required snapshot has3images and3skips. There are zero native Islands in
these twelve snapshots: no real Island visual-quality acceptance is supplied.

|Layout|leaf cm|core render p50 s|full render CLI p50 s|lifetime render peak MiB|observed object pixels in both frames|
|---|---:|---:|---:|---:|---:|
|1|5|11.71|33.82|3772.10|660|
|1|2|11.91|34.61|3772.37|2155|
|1|1|12.24|37.94|3772.37|8596|
|10|5|22.96|57.07|4869.59|396|
|10|2|23.02|57.22|4869.77|1496|
|10|1|23.30|60.11|4869.73|6885|

Each render row has only2samples. Core CPU/wall timers include parsing,
projection and image IO but exclude load_bundle's strict source revalidation.
Full CLI includes that audit; lifetime peak RSS also includes it and is not
isolated render-only memory. Maximum process-tree RSS across offline stages is
about3775MiB for Layout1 and5115MiB for Layout10, under the8GiB actual RSS guard.
These offline figures are separate from the199–229MiB native fusion node.
The first offline attempt failed under an8GiB virtual-address-space cap because
MuJoCo reserves large arenas; its log remains. The successful retry guarded
actual process-tree RSS instead, with the source code unchanged.

**Live1Hz six-view output fails, including at5cm.** Denser color voxels increase
observed pixel support, which does not itself prove visual clarity or whole-house
coverage. The quality gate needs GPT/Owner image comparison against server-local
MuJoCo views. Native point ownership, source/face/state evidence and conservative
depth/thin-object masks are retained. There is no per-voxel directional ray
certificate; local thin features/general directional visibility remain open.

## Evidence and next reviewer

Server evidence ID: `.g2_f3_color_ab_author_20261109_01`.
Server machine summary `codex_f3_machine_summary.json` SHA256:
`9524fed1994e0cb9fbd157152f28560752cc4b00dec2fc9c50b7ee3376e1a01c`.
Server-local indices include real_keyframe_scope_result.json, the two complete
native A/B comparisons,12 view-stage receipts, source package receipts and
unchanged raw failed-attempt logs. Own benchmark processes and the local test
container are stopped; private evidence remains in place.

Public own-fixture raw tests and derived real facts:
`docs/evidence/g2_f3_2026-11-09/`, particularly
real_ab_final_derived_facts.json, real_native_ab_aggregate_facts.json,
test_retention.json, author_peer_closure.txt and protected_refs_readback.json.
All17 protected refs (V3 and historical implementation/review branches) were
re-fetched and equal their captured starting SHAs.

GPT next independently verifies the exact source pair/build/input identities,
repeats the real native A/B, checks normal-path failures and source-GT labels,
and inspects all12 masked view comparisons on data. Owner visual review follows
GPT validation. Keep5cm default and prioritize existing-renderer throughput and
the normal Layout10 identity/geometry/mode Gate before a higher default or new
map/cache proposal. Intermediate-time view cadence, genuine ordinary semantic
observations, Island quality, directional visibility, historical/full-source/
full-appearance certification and training remain unapproved.

Status: AUTHOR_AB_COMPLETE_RENDER_1HZ_NOT_MET_PENDING_GPT_AND_HUMAN;
training_ready=false. No source-pair approval, production promotion, merge,
V3/Gitlink/old PR modification, model inference, GPU or training follows this report.
