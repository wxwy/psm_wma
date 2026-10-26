# V3 RoboCasa Owner manual evaluation

The manual entry now implements the Owner's flexible Episode Resume contract (`cc7820bee1a7`), following the approved r2 design. Its new production Implementation Gate requires GPT review and DS_PRO independent CPU acceptance. Author CPU results do **not** authorize a GPU run or close the physical-environment gate. Owner alone releases GPUs and runs the commands below. The running G1 training worktree and its Config, Job Identity and checkpoints remain untouched.

## Freeze a separate evaluation checkout

Use a clean, independent Root/Child checkout at the reviewed implementation pair. Keep an active evaluation checkout unchanged until its invocation exits. Future Resume may use a newer separately reviewed version: Root/Child/runtime/config provenance is recorded per source instead of imposing whole-run equality. Only Checkpoint, prediction steps, action horizon and guidance are hard reuse invariants. Do not synchronize the running G1 checkout to this branch.

The launcher Python needs PyYAML (author CPU: 6.0.3). The selected simulator Python must contain the locked Batch B runtime, Pillow, imageio and imageio-ffmpeg (author media tests: 11.3.0, 2.37.0, 0.6.0). Server and simulator can use the same compatible venv; their executable paths retain venv symlinks. Nothing installs or patches dependencies during evaluation. See `third_party/robosuite_patches/README.md` for the offline vendor builder and pins. Provisioning the real server environment remains a separately approved operation.

Copy `configs/eval/robocasa_g1_iter8900.example.yaml` outside the source checkout and edit paths, GPU IDs, task names, episode count, timeouts and output namespace. YAML relative paths resolve against the YAML directory; CLI paths resolve against the current directory. CLI values override YAML, then schema-v1 defaults. `--config` is evaluation YAML; `--config-file` is the frozen model configuration. YAML never rewrites the model configuration.

If installed dependencies contain downloaded, untracked assets, provide `asset_manifest` / `--asset-manifest` pointing to the separately approved Batch B per-package, repo-relative SHA256 inventory. An unknown file, backup, dirty tracked source or different dependency SHA rejects startup. Do not use an invented empty inventory to bypass that check.

## Read-only preparation

List task classes from `extras/dataset_meta.json` without starting any process or requiring checkpoint/runtime validation:

```bash
bash scripts/run_robocasa_eval.sh \
  --config /path/to/eval.yaml --list-tasks
```

Preview the fully resolved configuration, model/config and dependency identity, output destination, GPU/slot/port mapping and command templates:

```bash
bash scripts/run_robocasa_eval.sh \
  --config /path/to/eval.yaml --gpus 2,3 \
  --tasks CloseFridge,TurnOnSinkFaucet --episodes 5 \
  --run-name iter8900_demo --save-generated-video first --dry-run
```

Dry-run reads model identity and revalidates historical Episode evidence, then prints the current reuse plan and JSON command templates. If any Episode needs execution, CPU subprocesses in the **selected simulator interpreter** audit its imports, source, versions, native library and registry. Pure reuse does not probe the current simulator runtime, occupy ports or start model/simulation processes. Dry-run never creates the output namespace. It does not attest GPU availability or actual model loading. Missing required runtime dependencies for new execution produce a nonzero result; cloud doubles are not real-runtime evidence. Cache directories remain external; an explicit external `HF_HOME` is preserved.

Model identity hashes `.metadata` and every model shard without executing pickle or loading tensors. Preview reads once; real admission reads before and after acquiring the same `.run.lock`. Console and invocation evidence report actual bytes/files/time. This costs roughly two model-sized reads per real invocation; later batch guards check file inventory/inode/size/mtime/ctime without rehashing each Episode. No `optim/` or training state is read. A successful header/hash check is not proof that a real DCP can load.

`tasks: all` requires exactly 18 underlying task classes. A selected subset can contain any valid classes; paraphrases are not additional tasks, and multiple dataset directories for the same class reject the run. GPU IDs must be unique nonnegative CUDA IDs. Each GPU has one Worker, a fresh Action Server per task, and one serial Simulator/Local-TTT session at slot 0. `slots_per_gpu` must equal 1; training B8 does not imply eight inference sessions.

## Owner-authorized execution

Only after the combined gate and separate execution authorization, use the **same command without `--dry-run`**. Start with an explicitly authorized 1-task/1-episode canary, then 4×5 and 18×5. For the latter, use `--tasks all --episodes 5` and a new run name. GPU availability, memory, disk, ports and real Kitchen behavior are independently checked by DS_PRO/Owner; dry-run does not reserve or attest GPU resources.

```bash
bash scripts/run_robocasa_eval.sh \
  --config /path/to/eval.yaml --gpus 2,3 \
  --tasks CloseFridge,TurnOnSinkFaucet --episodes 5 \
  --run-name iter8900_demo --save-generated-video first
```

Optional `PYTHON=/absolute/path/to/python` selects the lightweight launcher interpreter; `server_python` and `sim_python` in YAML select the actual execution environments. The launcher does not change the caller's working directory or CUDA environment.

Frozen ABI: Local-TTT required, raw15/state15, left+wrist cameras, raw base encoding, chunk/H_pred16, 20 Hz, target objects and ten paired target layout/styles, first-success latch. `action_horizon` is the number of actions executed before replanning, from 1 to 16. The policy sampling seed is 0. New Task environment sampling retains the literal requested Seed, one environment and sequential resets. Partial-resume gaps use separately recorded derived seeds because historical environment RNG cannot be reconstructed. Official RoboCasa 1.0.1 registry horizons already incorporate its update; no second 1.5× multiplier is applied.

Environment videos follow `save_rollout_mp4` / `--[no-]save-rollout-mp4`; initial PNGs follow `save_init_png`. Generated video modes are `none`, `first` (first prediction **per episode**) and `all` (separate file per replan). Actions and prediction JSONL are mandatory even if videos are off. In `all` mode every generated file records replan, source step and frame count. Enabled media are checked for nonempty, actual decoding; matching filenames alone cannot complete a task.

## Terminal progress and browsing videos

Terminal progress is enabled by default. Every5s it shows each Worker's GPU, task, Episode/total, executed steps/official limit, returned prediction count, latest prediction latency in milliseconds and current stage. Episode boundaries, task completion and errors print immediately through a single output thread. Stages distinguish model loading, environment initialization, prediction/execution, video saving, process cleanup and result validation. Unknown fields display `?`; a quiet interval does not establish that a task is stuck. Server and simulator logs are still retained at their original paths.

Use `--progress-interval-s 10` or `--no-progress` to control terminal observation. These options do not affect Episode reuse. The independent `live_progress.jsonl` records stage metadata and the actual model instruction. It does not replace authoritative `episode_progress.jsonl`, Local cleanup or core validation. List output is JSON; preview additionally prints identity-read telemetry and the reuse plan.

After Workers finish or are cancelled, browsing copies for legacy root evidence remain under `videos_view/<Task>/<attempt>/`; new batch sources use `videos_view/sources/<source-id>/<Task>/<attempt>/` and their own indexes. Each exporter reads the corresponding original source Manifest. Raw filenames and evidence remain unchanged. Browsing names use the actual instruction, for example:

```text
rollout00_success_close_the_fridge.mp4
rollout00_success_close_the_fridge_generated_replan0000.mp4
```

The four labels are `success`, `fail` (normal behavioral failure), `error` (runtime error) and `incomplete` (no final outcome). A generated video's label describes its Episode's final outcome; it does not establish the accuracy of that prediction. Unsafe filename characters are filtered, spaces become underscores, and long names carry a short digest. The index retains the full instruction and original-file mapping. Missing historical instructions are explicitly marked `unknown_instruction`, never replaced with task class names. Repeated exports preserve prior copies and isolate different Attempts; changed source/status/instruction produces a distinct revision. Browsing copies require additional disk space; an export failure does not change the completed evaluation's exit code or SR.

To export an already saved run without loading a policy or starting a simulator, use a separate checkout at the reviewed source version:

```bash
python scripts/robocasa_eval_video_view.py \
  --run-dir /absolute/path/to/saved_run \
  --view-dir /absolute/path/to/separate_browsing_directory
```

The command reads the saved run and writes only the browsing destination. For a currently active run, keep its source worktree unchanged and use a separate destination; any unfinished Episode is labeled `incomplete`. Re-export after it finishes to add final labels. Do not rename the raw files while the evaluator is writing them.

## Evidence and bounded failure

A nonblocking lease on the same `.run.lock` protects admission and all scheduling. Four-parameter mismatches or a missing explicit `--resume` reject before control writes or launch. Existing legacy runs require their original regular lock. A failed fresh preflight may leave only its newly created directory/lock; it has not claimed an experiment. Source allocations are atomic, fsynced and durable before any Worker launch. Layout:

```text
<output_root>/<run_name>/
  evaluation_manifest.json          # original root manifest; never replaced
  .run.lock
  latest_invocation.json            # points to current view and immutable snapshot
  _resume_v2/model_identity.json
  _resume_v2/legacy_migration.json   # when importing a legacy manifest
  _resume_v2/catalog/*.json          # references, never trusted outcome shortcuts
  _invocations/<id>/
    invocation_manifest.json, resolved_config.json, resume_plan.json
    runtime_probe.json              # only when new execution requires a probe
    current_summary.json            # mutable UI view for this invocation only
    snapshots/000000.json, ...       # immutable progress/final snapshots
    reservations/<batch-id>.json     # physical/logical map and sampling provenance
    _workerNN_gpuN/action_server.log
    sources/<Task>/<batch-id>/
      evaluation_manifest.json      # actual batch seed/trials/media/runtime/model
      <Task>/attempt_0001/
        attempt.json                # RUNNING / FAILED / COMPLETE
        commands.json, server_info.json, server_process.json
        runtime_attestation.json, process_cleanup.json
        eval.log, episode_progress.jsonl, live_progress.jsonl
        results.json, rollout00_episode.json, rollout00_cleanup.json
        rollout00_actions.jsonl, rollout00_predictions.jsonl
        rollout00_init.png, rollout00.mp4
        rollout00_generated.mp4, rollout00_generated_manifest.json
        # all: rollout00_generated_replan0000.mp4, ...
  <Task>/attempt_NNNN/               # any legacy raw evidence remains unchanged
  screening_summary.json            # historical summary if present; not latest view
```

Open `latest_invocation.json` and follow `summary_path` for live/final results; `report_path` identifies an immutable snapshot. Episode/Task source references in the report locate their raw files. A current RUNNING view can have full result coverage while cleanup/other Worker initialization remains outstanding; only the final joined invocation can be COMPLETE. Failed-attempt raw video paths are separate `diagnostic_rollout_mp4s` / `diagnostic_generated_mp4s`; they do not count as completed-media coverage.

Model identity binds the full model SHA baseline and the other three hard parameters. Original source Manifests separately retain source/config/Task/runtime/Seed/media/timeout/resource evidence; they are never rewritten to the new plan's digest. Legacy metadata/stat bridging cannot invent a missing historical payload SHA. Every reused Episode is revalidated against its own source, ABI, progress, Local cleanup and original media policy. The actual simulator reruns the vendor probe before environment creation for each new batch.

Recorded data-generator versions/unknown Git commits and actual evaluation runtime are separate manifest fields. RoboCasa1.0.1 is the chosen evaluation runtime; equivalence with the recorded 0.5.1 generator is **not proven**. Historical diagnostic SRs remain diagnostic.

Server startup, request, Episode wall, batch wall and terminate-grace deadlines have distinct meanings. The Task/batch wall budget includes loading, rollout and validation; each gap batch is a separate one-Episode Task invocation. Cancellation reclaims only owned groups, with TERM then KILL/reap as necessary. Every batch gets a fresh server; failed sessions are never handed to the next batch. Default infrastructure policy is `stop`; `continue_with_new_server` collects more evidence but preserves PARTIAL/nonzero status and original/secondary cleanup errors.

A COMPLETE summary requires every selected task, every expected episode, successful infrastructure cleanup, typed outcomes and required valid evidence. Episode progress must contain exactly the ordered start/end pairs with the same Run and Task/Attempt identity. Each episode must also have a Local-TTT cleanup witness with a valid slot0 session ID, successful reset and no rollout/media/cleanup error; process termination alone does not substitute for that witness. Behavioral failure counts in the denominator. Runtime errors never silently disappear from SR: formal `sr` is null for incomplete runs, and `partial_sr` is labeled separately. Keep all partial actions, JSON, videos and logs for review.

## Resume by Episode and current plan

Keep the original output namespace and add `--resume`. Use a separately reviewed clean source version; never update a still-running checkout.

```bash
bash scripts/run_robocasa_eval.sh \
  --config /path/to/eval.yaml --gpus 2,3 \
  --tasks CloseFridge,TurnOnSinkFaucet --episodes 5 \
  --run-name iter8900_demo --save-generated-video first --resume
```

| Change | Behavior |
| --- | --- |
| Checkpoint / prediction steps / action horizon / guidance | Reject with old/new mismatch |
| More/fewer Tasks | Reuse eligible Episodes; execute missing selected Tasks; count only current selection |
| Completed3, requested5 | Reuse3 and execute2 |
| Completed8, requested5 | Reuse/count first5; retain/exclude3 |
| Seed change | Retain old actual Seeds; new executions use current Seed family; report mixed conditions |
| Media change | Reuse valid history without rerunning for missing newly requested recordings |
| GPU, timeouts, display, source/config/runtime provenance | Current invocation settings; new execution still passes safety/ABI/runtime checks |

RUNNING/FAILED sources can contribute independently verified closed Episodes. A contradictory COMPLETE source is wholly quarantined with diagnostics. No policy-success preference is used when deduplicating. Raw source digest, Attempt and physical Episode identities remain unchanged.

New Task batches retain literal Seed and one environment with N sequential resets. Partial-resume gaps cannot restore the historical RNG stream: each logical slot gets a stable derived seed and its own physical Episode0/source sandbox. Persistent reservations, real legacy progress and catalog gap evidence recover pending slots before appending IDs. `{0,1,3,4}` requests5 retry slot2; shrinking the view does not erase pending slots. Same-slot retries keep logical identity while using new Attempts. Mixed/unknown Seed, runtime, config, source and sampling protocols are explicit convenience aggregates, not a single-condition benchmark.

Resource limits reject more than100000 records/Episodes or logical IDs outside0..99999 before range allocation, and bound JSON control documents to64MiB. Inputs containing symlinks, ambiguous identities or unsafe mappings fail closed. These limits do not delete historical evidence.

## Review boundary

Author CPU cases use real Git/process/socket/media primitives with synthetic policy/simulation boundaries. They cannot prove policy loading, 8×H100 inference, real PandaOmron physics, vendor installation on DS_PRO's host, Local-TTT effectiveness or benchmark SR. DS_PRO independently verifies the exact new pair read-only; GPT issues the verdict. Owner manually starts the separately authorized real run. No command in this runbook is automatic execution authorization.


## Owner-acknowledged manual relocation of a legacy checkpoint (2026-10-26)

When the Owner manually **moved or copied** the G1 `iter_000012000` DCP, an old `evaluation_manifest.json` may store the original absolute checkpoint directory and shard `ctime_ns`. Merely changing filesystem location or copying a DCP can change these values without modifying tensor contents. The original legacy manifest did **not** record full shard SHA256 hashes, however: current full hashing does **not** prove historical shard bytes were identical.

- **Default behavior stays strict:** `--resume` alone continues to reject any change in old checkpoint path/ctime. **Explicit per-invocation opt-in only:** add `--allow-relocated-legacy-checkpoint` together with `--resume`, optionally `--dry-run` first. This option is **only applied to old manifests** without a strong `model_identity`; it does not relax modern full-hash checkpoint comparisons.
- The candidate checkpoint must retain exactly the same `iter_NNNNNNNNN` basename, `.metadata` SHA256 and complete sorted shard names, sizes and `mtime_ns`. `num_steps`, `action_horizon`, `guidance` still match. Raw `path` and shard `ctime_ns` are not required equal **only in this explicit old-schema legacy bridge**. The current model `.metadata` and every shard are still SHA256-hashed with unchanged-file stat-witness checks and nonexecuting ZIP/pickle header checks.
- On acceptance, the new `_resume_v2/legacy_migration.json` records the original identity and path, actual current path/full-hash digest, `OWNER_ACCEPTED_LEGACY_CHECKPOINT_RELOCATION` warning, which comparisons were waived, and the fact that **historical shard payload hashes remain unavailable**. The original legacy `evaluation_manifest.json`, prior Episode evidence and original Manifest digest are **never overwritten**. The new strong `_resume_v2/model_identity.json` binds the current physical checkpoint so future Resume uses strict full SHA hashes again.
- Do not use this flag to change model weights, iteration, dimensions, inference parameters or another job's strongly pinned checkpoint. If source shards of the old run are still available, an independent content-hash comparison is stronger evidence. A claimed matched-seed benchmark based on mixed historical/current provenance must still be marked as such.
- The requested `--episodes 50 --tasks all` means **18×50 = 900** total planned Episodes, not 18×5; at most20 of the original four-task/five-episode run can be reused if each passes evidence rescan. Confirm disk headroom and GPU4–7 ownership before dropping `--dry-run`.

Example (all original required asset/runtime/output arguments must also be supplied):

```bash
bash scripts/run_robocasa_eval.sh \
  --checkpoint /path/to/relocated/iter_000012000 \
  --dataset-root /path/to/robocasa365_official/v1.0/target/atomic \
  --output-root /path/to/robocasa_eval_runs \
  --run-name g1_iter12000_4task5ep_genall_20261023_085955 \
  --tasks all --episodes 5 --resume \
  --allow-relocated-legacy-checkpoint --dry-run \
  # plus server/simulator Python, vendor assets, GPU, protocol and media options
```

The example is illustrative and incomplete; do **not** paste as a whole launcher command with the trailing Bash comment line. Use the same full command as the prior invocation, adding `--allow-relocated-legacy-checkpoint` and `--dry-run`. The override does not grant permission to run GPU evaluation.
