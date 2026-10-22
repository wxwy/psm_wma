# V3 RoboCasa Owner manual evaluation

Batch C implements the manual entry; author CPU results do **not** authorize a GPU run or close the combined A/B/C physical-environment gate. GPT reviews the new formal pair, DS_PRO independently validates it, and Owner alone releases GPUs and runs the commands below. The running G1 training worktree and its Config, Job Identity and checkpoints must remain untouched.

## Freeze a separate evaluation checkout

Use a clean, independent Root/Child checkout at the exact reviewed implementation pair. Preserve it unchanged through task resume; updating even the Root SHA changes evaluation identity. The source includes G1 Resume, Batch A process isolation and Batch B locked dependencies. Do not synchronize the running G1 checkout to this branch.

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

Dry-run uses CPU subprocesses in the **selected simulator interpreter** to audit its real imports, source, versions, native library and registry. It does not load a policy, construct a Kitchen, bind server ports or create the output namespace. Missing full runtime dependencies correctly produce a nonzero result; cloud unit-test doubles do not constitute a real-runtime pass. Probe and execution Numba/Matplotlib/XDG caches use external temporary directories, removed when the launcher exits. An explicit external `HF_HOME` is preserved for reusable weights; otherwise HF caching is also external and temporary. Stdout/stderr of a failed preflight should be captured externally by the operator.

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

Frozen ABI: Local-TTT required, raw15/state15, left+wrist cameras, raw base encoding, chunk/H_pred16, 20 Hz, target objects and ten paired target layout/styles, first-success latch. `action_horizon` is the number of predicted actions executed before replanning, from 1 to 16. The policy sampling seed is 0; the environment seed is configurable and fixed by identity. Official RoboCasa 1.0.1 registry horizons already incorporate its horizon update; no second 1.5× multiplier or fallback horizon is used by the unified entry.

Environment videos follow `save_rollout_mp4` / `--[no-]save-rollout-mp4`; initial PNGs follow `save_init_png`. Generated video modes are `none`, `first` (first prediction **per episode**) and `all` (separate file per replan). Actions and prediction JSONL are mandatory even if videos are off. In `all` mode every generated file records replan, source step and frame count. Enabled media are checked for nonempty, actual decoding; matching filenames alone cannot complete a task.

## Evidence and bounded failure

An exclusive manifest claim and nonblocking namespace lease prevent concurrent writers. Output is structured as:

```text
<output_root>/<run_name>/
  evaluation_manifest.json
  .run.lock
  _invocations/<timestamp>_<pid>/
    resolved-config.json
    runtime_probe.json
    previous_screening_summary.json  # present on subsequent invocations
  _workerNN_gpuN/action_server.log
  <Task>/attempt_0001/
    attempt.json                     # RUNNING / FAILED / COMPLETE
    commands.json, server_info.json, server_process.json
    runtime_attestation.json         # in-process recheck before Kitchen creation
    eval.log, episode_progress.jsonl, process_cleanup.json
    results.json
    rollout00_episode.json, rollout00_cleanup.json
    rollout00_actions.jsonl, rollout00_predictions.jsonl
    rollout00_init.png, rollout00.mp4 # only when enabled
    rollout00_generated.mp4          # first mode
    rollout00_generated_manifest.json
    # all mode: rollout00_generated_replan0000.mp4, ...
  screening_summary.json
```

Task rows and the overall summary report environment recordings in `rollout_mp4s` and model-prediction recordings in `generated_mp4s`. Turning off environment recording leaves the former empty even when generated videos are enabled; failed/partial attempts retain the same classification.

Manifest identity binds Root, Child/Gitlink, checkpoint model metadata+shard stat witnesses (not full payload hashes), frozen model Config hash, selected task metadata, dependency source/native identity, interpreter/import context, seeds, horizons, video settings, timeouts and GPU mapping. Inference requires model DCP files, not `optim/`; it never reads training optimizer state. The actual simulator reruns the vendor probe and must reproduce the expected digest before creating an environment. Its witness is required for task completion/resume.

Recorded data-generator versions/unknown Git commits and actual evaluation runtime are separate manifest fields. RoboCasa1.0.1 is the chosen evaluation runtime; equivalence with the recorded 0.5.1 generator is **not proven**. Historical diagnostic SRs remain diagnostic.

Server startup, request, episode wall, task wall and terminate-grace deadlines have distinct meanings. Task timing includes server startup, rollout and final evidence/media validation. Cancellation or failure reclaims only owned process groups, TERM then KILL/reap if necessary; it does not kill foreign listeners or training processes. Some cleanup can extend beyond task wall by bounded terminate grace. Each task gets a new server, including after a previous failure. The default infrastructure-error policy is `stop`; explicit `continue_with_new_server` can collect screening evidence, while the entire run still reports INCOMPLETE and nonzero exit. Original errors and cleanup errors remain visible.

A COMPLETE summary requires every selected task, every expected episode, successful infrastructure cleanup, typed outcomes and required valid evidence. Episode progress must contain exactly the ordered start/end pairs with the same Run and Task/Attempt identity. Each episode must also have a Local-TTT cleanup witness with a valid slot0 session ID, successful reset and no rollout/media/cleanup error; process termination alone does not substitute for that witness. Behavioral failure counts in the denominator. Runtime errors never silently disappear from SR: formal `sr` is null for incomplete runs, and `partial_sr` is labeled separately. Keep all partial actions, JSON, videos and logs for review.

## Resume whole tasks only

Use the exact frozen source/runtime/config/parameters and original run name, adding `--resume`. The execution flag itself is excluded from immutable protocol identity. Do not pull code or change GPU mapping, task selection, timeouts or video policy between attempts.

```bash
bash scripts/run_robocasa_eval.sh \
  --config /path/to/eval.yaml --gpus 2,3 \
  --tasks CloseFridge,TurnOnSinkFaucet --episodes 5 \
  --run-name iter8900_demo --save-generated-video first --resume
```

Only an entire COMPLETE task with matching identity, valid in-process runtime, per-Episode Local cleanup, complete progress and media/audits is skipped. The same strict checks apply again during resume; missing or damaged progress/cleanup evidence rejects the skip. A RUNNING/FAILED task receives a new exclusive `attempt_0002` directory and restarts from episode 0 with the original seed and sequential reset protocol. Earlier episodes are never stitched across attempts. Result, action, prediction and generated-video records bind the `Task/Attempt` ID, so copied episodes from another attempt reject validation. Corrupted COMPLETE evidence or ambiguous multiple complete attempts fail closed for investigation; they are not overwritten. Unknown legacy task output is not imported. Old cross-source runs require new namespaces and cannot be presented as same-identity resume.

## Review boundary

Author CPU cases use real Git/process/socket/media primitives with synthetic policy/simulation boundaries. They cannot prove policy loading, 8×H100 inference, real PandaOmron physics, vendor installation on DS_PRO's host, Local-TTT effectiveness or benchmark SR. DS_PRO independently verifies the exact new pair read-only; GPT issues the verdict. Owner manually starts the separately authorized real run. No command in this runbook is automatic execution authorization.
