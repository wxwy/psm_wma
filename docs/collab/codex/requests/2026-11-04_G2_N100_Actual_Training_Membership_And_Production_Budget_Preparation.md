# G2 N100 — actual training membership and production budget preparation

**SUPERSEDED (2026-11-04):** Owner clarification
`a8da67f9c69c5936a681b3061d781436911b5f1b` confirms full-source training for
Local-TTT and No-TTT, with no historical N100 cap. The historical-N100 membership
prerequisite below is RETIRED. Preserve this earlier proposal as history, not an
active request to locate such a receipt. Current planning is
[full target-atomic batched production](2026-11-04_G2_Full_TargetAtomic_Batched_Depth_Pose_Storage_And_Production_Plan.md).
N100, if used, is a new production batch label; its exact definition is proposed,
not a training cohort. No export or V3 promotion is implied.

Date: 2026-11-04, Asia/Shanghai. **Preparation only; batch export NOT STARTED
and not authorized.** Gate C final authority:
`b68f14b0d73456c0710bbbffa2b3aa0fcef25244`,
[three-episode final acceptance](../../chatgpt/reviews/2026-11-04_G2_GateC_ThreeEpisode_Owner_Visual_Signoff_FINAL_PASS.md).
Source stays Root `3eb8b334150018212ae1f51afb5e954b83fa1186` /
Child-Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`.
No new implementation Pair, repeated Code Gate or repeated Gate C is requested.

## Accepted scope and remaining inputs

Gate C is closed for CloseFridge global502/429 frames, NavigateKitchen
global2022/177 and PickPlaceCounterToCabinet global4038/246: 852 frames,
18 sampled spatial checks, external Owner alignment, one interrupted-episode
restart and 3/3 verified reuse. This is reported independent server evidence;
Codex has not independently run or copied its raw artifacts. The original
machine VISUAL_PENDING report remains immutable. The separate Owner sidecar
SHA256 is `faa553c8acc1eb922a90ed929dc7487826aa9d0833c2254359d98123c1a1fbd7`.

**Actual N100 training manifest path/hash, accepted IDs, per-task counts,
total frames and production capacity/deadline are NOT YET FROZEN.** N100 is
not proof of 100 episodes total, 100 per task, 1800 accepted episodes, or seed42.
Report the actual cohort rather than fill missing/short episodes to reach a label.
The completed three-episode cache remains frozen in its own namespace.

## One server-side read-only intake

The next preparation step can inspect existing metadata and run the existing
non-rendering dry-run. It must not build a renderer, load a model/DCP, launch
training, regenerate latent caches, alter a running job, or write source files.
Server access is currently unavailable in this Codex runtime; a connected
execution role can carry out the following bounded metadata intake.

1. Identify the actual intended training job and its recorded SOURCE_ROOT,
   CACHE_ROOT, DATASET_INDEX_ROOT, dataset manifest path, task filters and window
   selection. Read existing config/index headers and build manifests only; do not
   edit Config/Job Identity or traverse/checkpoint-load DCP files. Freeze paths,
   sizes/stat identity and SHA256, and distinguish the actual consumer input from
   similarly named old caches, candidate builds and performance A/B outputs.
2. Reuse `tools/g2/rgbd_pose/source.py` functions `selected_episodes`,
   `verify_selection_source`, `mapping_episodes` and `select`. A compatible g0
   `exact_window_v1` / `lerobot_v3` manifest can be consumed directly. Accepted
   members are **tasks[].episodes[].episode_index**, global IDs. Validate the
   original selected-ID digest when present, but do not reintroduce selected
   short episodes missing from accepted rows. Reconcile any real training
   task/index filters; cache availability alone does not prove consumer membership.
3. Confirm the actual member set against the verified index/effective consumer
   metadata. Publish separate counts for selected, accepted and effective members
   when they differ, with the cause. Unknown identity, incompatible schemas or
   unreconciled differences are BLOCKED, not a request to change frozen inputs.
   Use the existing external `psm_wma_rgbd_episode_selection_v1` schema only when
   an exact effective subset needs its own server-local list. Bind it to the
   source manifest SHA and exact Flat mapping SHA; no random sampling or ID shifts.
4. Verify the current Flat source/mapping. Gate C mapping SHA was
   `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed`.
   Require that same identity for this proposed production lineage; drift stops
   preparation for an explicit source decision. Do not edit metadata to conceal
   a mismatch. Inspect all effective members' task/local/global IDs, half-open
   row intervals, lengths, unique raw source, both camera shapes and source
   state/frame binding using the existing loader/dry-run.
5. Preserve a new server-only exact selection, per-task count/frame/shape table,
   input identities, dry-run report/exit/log, free disk/inodes, available memory
   and proposed output/evidence paths. Proposed output must be separate from
   raw/Flat/training and old Gate B/C caches. Preparation must not create that
   future cache root. Raw manifests, scripts, images, Parquet and NPZ stay on
   server; only bounded non-sensitive aggregates/hashes/paths go into Git.

Do not execute g0 cache builders or manifest mergers during this intake: they
write cache inputs. Their existing output is the lineage evidence. In particular,
do not substitute `--episode-limit 100 --episode-seed 42` or recompute the sampler.
If the current training cohort cannot be established, report precisely which
metadata is missing, keeping membership and production size UNKNOWN.

## Existing dry-run, after the actual inputs are bound

Use the approved exact clean checkout and the existing server CPU interpreter,
process-local library/caches and one numeric thread/library. No new packages,
global environment changes or GPU fallback. NEW_PREP_EVIDENCE is a new external
server-only directory; N100_CACHE is only a proposed absent output path. The
following **30-minute preparation ceiling** is independent of the completed
Gate C budget and is not a production runtime authorization. Use one outer
owned process group for metadata discovery plus dry-run. N100_PREP_RUNNER is a
server-local temporary metadata runner; record its contents/hash before launch.
No foreground/detached descendants or automatic deadline extension.

```bash
env CUDA_VISIBLE_DEVICES='' MUJOCO_GL=disable \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  timeout --signal=TERM --kill-after=15s 1785s bash "$N100_PREP_RUNNER"
```

Inside that runner, after binding the actual inputs and recording the metadata:

```bash
cd "$CODE_ROOT"
"$SIM_PYTHON" -m tools.g2.export_robocasa_rgbd_pose \
    --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" \
    --output-root "$N100_CACHE" --selection-manifest "$ACTUAL_TRAINING_SELECTION" \
    --cameras robot0_agentview_left,robot0_eye_in_hand \
    --state-index-policy frame_index --depth-format uint16_mm --chunk-frames 32 \
    --dry-run > "$NEW_PREP_EVIDENCE/n100_dry_run.json" \
    2> "$NEW_PREP_EVIDENCE/n100_dry_run.stderr.log"
```

No `--frames`, no implicit default selection, no renderer. The preparation runner
must stop on nonzero/timeout/drift, retain logs and not create output by removing
`--dry-run`. Exit0 plus `mode=dry_run` / planned episode rows is only a verified
nonvisual plan, never an export or physical acceptance claim. Input discovery
and this dry-run share the single outer preparation ceiling; do not start an
additional full timeout for the dry-run.

## Budget calculation from the actual selected full episodes

Let E be the accepted/effective episode count and F the sum of their **full
mapping.length**. Do not use window_count×17, corpus averages or the whole Flat
corpus as the selected frame count. For uint16-mm Depth, bool mask, float32 K/GL/CV
poses and int64 indices, raw array bytes are exactly:

`R = sum_episode,camera length * (3 * H * W + 41 * 4 + 8)`.

Here 3 bytes/pixel is 2-byte Depth + 1-byte mask; original RGB is referenced,
not copied. With exactly two 256×256 cameras this is `R = 393560 * F` bytes.
Handle actual native camera shapes explicitly. R excludes ZIP/container headers,
JSON/source witnesses, staging, logs and validation artifacts.

Reuse these **three-task observations only as planning references**:

| Gate C measurement | Reported value / use |
| --- | --- |
| Successful export wall | 106.32 + 54.80 + 59.38 = 220.50s for 852 frames; 3.864 frames/s |
| All S1–S3 machine work | 329.99s including interruption/retry, verification, previews and skips; not pure export time |
| Raw arrays / compressed NPZ | 335313120 / 46507310 B; 7.2099× observed compression |
| Entire cache / committed task dirs | 49389714 / 47675013 B; includes metadata, with staging separate in the former |
| Preserved interrupted staging | 1703729 B; recovery evidence, not disposable capacity |
| Largest reported process RSS | 5051668 KiB, about 4.82 GiB; rendering dominates, not just chunk buffers |

Provide actual per-task E/F, length distribution and source sizes. Show `R/7.2099`
and `F*(220.50/852)` only as empirical payload/time proxies, explicitly excluding
unknown task variation and production acceptance overhead. They are not guaranteed
compression, throughput or approved limits; startup cost changes with E/F.

Set proposed disk quota from raw-array size plus measured/planned metadata,
compression overhead, maximum single-episode staging/retry allowance and logs/
validation reserve. Do not admit a job solely from the optimistic compression
proxy. Record fresh filesystem free space, retain at least the existing 1GiB
reserve, and specify exhaustion/stop conditions without deleting old Evidence.
Propose one CPU/OSMesa replay process initially. Include environment/RSS headroom,
per-episode startup, metadata I/O, full cache verification and physical/visual
sampling costs in a separately reviewed total deadline. Do not multiply a
single-worker throughput by a proposed worker count or reuse Gate C's45min as
the N100 deadline. Parallelism, if proposed, requires its own concrete budget.

Return a concrete production proposal only after membership and capacity are
known: exact source/selection/code/runtime identities, E/F/cameras/format,
fresh paths, wall/RSS/disk limits, stop/restart policy and acceptance scope.
The render/export command is intentionally not issued by this preparation.

## Existing data interface for later nav_sg work

Reuse `tools/g2/rgbd_pose_schema.md`. An episode is committed only with its
manifest and COMPLETE hash; frames bind task/global/local ID, original RGB video
and frame, source state/rows, chunk/offset and optical-Z/K/per-frame GL+CV poses.
The `valid` mask and quantization units/conventions must travel with Depth.
Uncommitted `.staging`/`.failed` are not consumer input. This defines the existing
data boundary; it does not implement or authorize a nav_sg/scene-graph converter,
world-model/Local-TTT change, training run, V3 promotion or N100 production.

Stop after the read-only freeze and budget handoff for the separate bounded
production execution decision. Do not repeat the closed Code/Gate B/Gate C tests.
