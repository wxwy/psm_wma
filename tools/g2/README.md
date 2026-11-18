# RoboCasa365 G2 Stage-1 RGB-D/Pose cache

This is offline data preparation, with no Cosmos model/recipe changes and no
nav_sg integration. Original RGB videos are referenced, never re-encoded.

From the Root checkout:

```bash
python -m tools.g2.export_robocasa_rgbd_pose --help
python -m tools.g2.verify_robocasa_rgbd_pose --help
```

Use `--dry-run` to verify the episode mapping and nonvisual raw/Flat rows without
creating a renderer or writing the output directory. Real export requires the
RoboCasa/robosuite/MuJoCo environment, assets and original recordings on the server.
`--state-index-policy frame_index` is an explicit mapping declaration, not proof
of physical alignment. Gate B/C must establish that proof.

- [Input/output schema](rgbd_pose_schema.md)
- [Depth v2 zero sentinel and seven-episode transition plan](../../docs/build/PSM-WMA_G2_Depth_ZeroSentinel_v2_and_SevenEpisode_Transition_2026-11-05.md)
- [Current spatial-v2 acceptance and bounded Gate C plan](../../docs/build/PSM-WMA_G2_Spatial_Acceptance_v2_and_GateC_Plan_2026-11-04.md)
- [Original implementation/recovery runbook (historical RGB hard gate)](../../docs/build/PSM-WMA_G2_Stage1_RGBD_Pose_Cache_r1_2026-11-04.md)

The spatial-v2 verifier preserves re-rendered RGB metrics as nonblocking
diagnostics. Automatic spatial PASS is separate from external human RGB/Depth
review; an `--owner-visual-review-ref` citation never automatically attests PASS.
Historical reports remain unchanged.

No default N/seed selection exists. Supply one explicit episode or an exact
external batch/membership manifest. A completed cache is reusable only after
its identity, file checksums, arrays and frame references validate.

Issue #19 uses schema `psm_wma_robocasa_rgbd_pose_v2`: uint16 out-of-range and
renderer-invalid pixels are 0; NPZ has depth/K/GL-CV poses/frame indices only.
Validity is derived in memory. v1 directories fail before new export writes;
the seven existing production episodes require a separately reviewed transition.
This change does not perform migration or authorize production resume. Synthetic
73/74 far-floor regressions do not replace native CloseFridge 736 acceptance.

## Issue #52: independent spatial-View VAE cache

These entry points consume completed G2 spatial packages, not raw simulator
recordings. Run from the **PSM-WMA Root**, with its fixed Cosmos child present:

```bash
python -m tools.g2.build_spatial_view_vae_cache --help
python -m tools.g2.verify_spatial_view_vae_cache --help
```

The builder requires an explicit action. `--dry-run` (alias `--plan`) reports
all valid views, unique physical PNG owners, logical references and expected
cache paths without creating `vae_cache/` or loading a VAE. Supply a local
weight file to bind the candidate recipe; planning does not encode it.
`--execute` is the actual encoding action, for a separately authorized real
sample after this code/CPU candidate is reviewed. It is not a production switch.

```bash
# Read-only plan; placeholders must identify existing local assets.
python -m tools.g2.build_spatial_view_vae_cache \
  --dataset-root /path/to/robocasa365-target-atomic-6views \
  --task CloseBlenderLid --episode 0 --weights /path/to/local/wan_vae.pth \
  --height 256 --width 256 --storage-dtype float32 --batch-size 1 --dry-run

# Read-only complete-cache/source audit; no encoder or online services.
python -m tools.g2.verify_spatial_view_vae_cache \
  --dataset-root /path/to/robocasa365-target-atomic-6views \
  --task CloseBlenderLid --episode 0
```

All valid logical views are encoded, including views not currently selected by
a task. Each Episode gains one `vae_cache/<logical-view>.pt` per existing view;
each file holds every physical image version for that view and the reference
index. No file is created for an absent view. Multiple Room/Island directory
levels remain distinct. Original PNGs, arrows, SG and completion files stay
unchanged. Reader calls load only requested view payloads, with bounded lazy
file caching, rather than the whole Episode.

256×256 white-padded, aspect-preserving preprocessing and FP32 storage are
initial **candidate** settings. B=1 is supported; larger batches are rejected
until independently implemented and validated. Low-precision storage, actual
Wan numerical/decode quality, mixed-batch parity, real GPU throughput and
full-corpus encoding remain separate gates. Ordinary verification is read-only;
`--reencode` explicitly requests the separate real-VAE comparison and requires
the same local weights/device identity. See the [Issue52 runbook](../../docs/build/PSM-WMA_G2_spatial_view_vae_cache_2026-11-16.md)
for the library ABI, atomic resume contract and precise validation scope.

## Issue54 Stage A candidate producer profile

The original `python -m g2.offline.atomic_6views_run` accepts an explicit
`--output-profile` JSON and `--flat-root` caption authority. Candidate examples
are in `tools/g2/profiles/`; use a new staging output/plan/work root. Omitting
the profile retains strict legacy publishing. `floor_top` is clean only in the
new schema; its independently stamped sibling is `floor_top_w_rbs`.

```bash
python -m tools.g2.verify_spatial_profile --episode-root /path/to/new/episode
# Inspect a sealed source awaiting VAE verification; exit 75 pending:
python -m tools.g2.verify_spatial_profile --episode-root /path/to/new/episode \
  --allow-source-ready
```

A1 metadata/GT roles/selection/candidate text remain in place. A2 adds the
independent `python -m tools.g2.consume_spatial_view_vae_events` consumer and
the explicit sealed-source adapter in the existing cache build/verify CLIs.
Initialize a bounded recipe-bound spool, start one separately authorized
consumer, then pass `--vae-spool` to the original producer. Every valid View
and both top variants are encoded; selection does not trim cache coverage.

VAE-enabled new profiles accept spatial readiness without episode COMPLETE;
final profile publication waits for all owners and numerical verification.
VAE-disabled new profiles are not silently upgraded. Legacy completed-package
semantics remain strict. CPU FakeEncoder checks do not certify native output,
real VAE parity, performance or production settings. See the
[A2 implementation/runbook](../../docs/build/PSM-WMA_G2_Stage_A_A2_implementation_2026-11-17.md)
for commands, ACK/recovery/cleanup contracts and pending independent gates.

## Issue58: one-shot Stage A production candidate

The repository launcher is `scripts/g2/run_stage_a_full.sh`; thin CLI is
`python -m tools.g2.run_stage_a_production`. Copy/fill
`tools/g2/production/stage_a_9126.template.json` into an absolute frozen config.
Its reviewed Root and mapping SHA placeholders deliberately reject execution.
Use `preflight`, `progress`, `stop`, or explicitly `run/resume --manual-start`.
One original plan/queue covers9,126 episodes and92 packages; this is not a
48-episode loop. Full completion waits for VAE plus verified work cleanup.

New spoolv3 archives acknowledged events behind durable episode receipts;
only active events use the100k budget. A fresh owned work/spool/output namespace
is required. F27-only EGL dependencies never enter the original-environment
B1 VAE consumer. No automatic production start, old-data deletion, build,
installation or merge. P1 microbatch is deferred; approved B1 recipe is intact.
See [the Issue58 runbook](../../docs/build/PSM-WMA_G2_one_shot_production_issue58_2026-11-17.md)
for exact manual commands, output/cleanup contracts, CPU evidence and pending
GPT real-sample/resource gates. Author CPU checks do not authorize full start.

## Issue63: explicit final source capsule

The new production template declares `final_source_format=capsule_v2`, fresh
Issue63 paths and `keep_full_audit=false`. Production retains full working v1
source until all products/cache/ACK are verified. Then spoolv4 publishes a
small authenticated source index and safely retires only the working source/
READY; PT/PNG/SG/spatial/task/language bytes remain intact. Legacy v1 stays
strict; no automatic migration of accepted data or old spools.

```bash
python -m tools.g2.verify_spatial_source_index --help
python -m tools.g2.resume_spatial_source_retirement --help
python -m tools.g2.audit_spatial_capacity --help
```

The v2 reader loads small JSON indices and requested PT files, without the
deleted full source or a renderer. Existing build/verify entrypoints remain.
Resume fixes source transactions before the original planner checks outputs.
Optional lossless full-audit archive requires a distinct filesystem and an
explicit protected-root/retention policy. Default production keeps no full
audit copy in the training dataset.

See [the Issue63 contract/runbook](../../docs/build/PSM-WMA_G2_source_capsule_issue63_2026-11-17.md)
for actual field dependencies, hash graph, locking/recovery, private server
commands and capacity/real169+419 Gates. Two sample sizes never certify all
18 tasks or9,126 production; missing strata yield HOLD_CAPACITY. No automatic
full run, old-view deletion, environment installation or training is added.

## View-first: independent VAE and compressed-source retirement

The existing build CLI accepts `--view-first --spool-root <external-spool>`
to consume published View-only episodes, using the same B1/T1 encoder,
preprocessing, bounded ledger/ACK and per-View cache. Legacy invocation stays
strict. It does not rerender or rewrite original spatial products/completion.

After the cache verifies, `python -m tools.g2.retire_view_first_sources --help`
describes the explicit CPU-only plan/execute/resume adapter to existing v2
retirement. Its posthoc policy binds the original View-only root claim and
uses an external spool. Final publication verifies every retained product/PT
before retiring gzip/receipt/READY. Resume uses the same spool/policy/recipe;
it never recreates the full JSON or loads a model. Exit75 means pending,
exit2 rejects a conflict; never delete source files manually.

See [the View-first retirement runbook](../../docs/build/PSM-WMA_G2_view_first_posthoc_retirement_2026-11-18.md)
for typed source states, exact isolated-sample commands, recovery, physical
byte accounting and corpus command drafts. Small sample acceptance does not
authorize retirement of the running9,126-episode View production.
