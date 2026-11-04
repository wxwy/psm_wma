# G2 Gate C S1–S3 — exact three-episode execution contract

**Completion addendum (2026-11-04):** this bounded contract has been executed by
the connected server role and closed as `GATE_C_PASS` in final authority
`b68f14b0d73456c0710bbbffa2b3aa0fcef25244`,
[the separate external visual sign-off](../../chatgpt/reviews/2026-11-04_G2_GateC_ThreeEpisode_Owner_Visual_Signoff_FINAL_PASS.md).
The pre-execution text below is preserved as provenance, not the current runtime
state or permission to rerun. Machine VISUAL_PENDING reports remain unchanged;
no N100 production or V3 merge follows from this completion.

Date: 2026-11-04 (Asia/Shanghai). **Bounded execution authorized; NOT STARTED.**
Authority: `d3374c0e35c6d8bfc308b45c399b48cd3870f0f3`, decision
`APPROVE_BOUNDED_EXECUTION_CONTRACT_WITH_MANDATORY_TRIGGER_CORRECTION` in
[the formal execution review](../../chatgpt/reviews/2026-11-04_G2_GateC_S1_S3_Execution_Contract_Approval_With_Amendment.md).
The S0 report `cd143c4bf6322a39cb7855772a944d45a49ffcf8` alone did not authorize
export; this later review grants the exact S1–S3 scope below after fresh preflight.

This explicit amendment adopts that review's NPZ-only interruption trigger,
superseding the progress-row prerequisite in contract commit
`445d177365396bbc5952c3fdc9b59aea459c5caa`. The original contract/report remain
preserved in Git. No production implementation change, new Formal Pair or
repeated Code Gate is required. Authorization is not evidence of execution or PASS.

The same NPZ-only correction was separately published remotely as
`59beb9fe5b3e893d6b86254f00524672638bd49f` before the actual Gate C run.
Preserving the local amendment history does not assert that its previously failed
push succeeded before execution; the server used the remote reviewed contract.

## Frozen inputs and outputs

- Formal Root `3eb8b334150018212ae1f51afb5e954b83fa1186`;
  Child/Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`.
- Source checkout `/tmp/g2_spatial_v2_gpt_3eb8_20261104`; interpreter
  `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/robocasa_sim_venv_20261023/bin/python`.
- Raw root `/mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic`;
  Flat root `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic`.
- Mapping SHA256 `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed`.
- Server selection `/tmp/g2_gate_c_s0_20261104_1655_cst/selection_manifest.json`;
  SHA256 `10d668ee42b5145a8cad09878c331ef940b06d91a6a9666ae85434b61c225926`.
- New cache `/mnt/data1/data_v2_0617/g2_rgbd_pose/gpt_gate_c_candidate_s0_20261104`.
- New external evidence `/tmp/g2_gate_c_s1_s3_3eb8_20261104`.
  Both output paths must be absent before the first launch. Do not delete,
  clean, overwrite or repurpose an existing path to satisfy this precondition.

| Task | Local / global ID | Full frames | Physical samples: 0, floor(L/2), L-1 |
| --- | --- | ---: | --- |
| CloseFridge | 0 / 502 | 429 | 0,214,428 |
| NavigateKitchen | 0 / 2022 | 177 | 0,88,176 |
| PickPlaceCounterToCabinet | 0 / 4038 | 246 | 0,123,245 |

Successful committed output is exactly 852 source frames / 1704 camera-frames.
Both cameras are `robot0_agentview_left` and `robot0_eye_in_hand`, each 256×256.
Physical sampling is 9 source frames / 18 camera checks, not all-frame geometry.
Original source directories and row intervals are frozen in the S0 report.
The exact selection manifest remains server-only; do not regenerate its bytes.

## Resource/deadline contract

One sequential CPU/OSMesa replay process at a time, numeric libraries one
thread (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`). Preserve
the actually validated process-local OSMesa library route; use empty CUDA devices,
`MUJOCO_GL=osmesa`, `PYOPENGL_PLATFORM=osmesa`, `LIBGL_ALWAYS_SOFTWARE=1`, private
HF/MPL/XDG/Numba caches, and no package/global environment changes. Warm-cache
copies, if needed, stay server-local. No GPU/EGL fallback or other-job management.

**45 minutes is one shared machine-work ceiling for S1+S2+S3**, including
initialization, the planned interruption/retry, verification and preview creation.
Use one outer owned process group. `GATE_C_RUNNER` is the server-local temporary
validation runner path, whose contents and SHA must be recorded before launch:

```bash
env CUDA_VISIBLE_DEVICES='' MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa \
  LIBGL_ALWAYS_SOFTWARE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  timeout --signal=TERM --kill-after=15s 2685s bash "$GATE_C_RUNNER"
```

TERM is at 44m45s, hard kill by 45m. Do not reset the timer per episode, use `--foreground`, detach
children with setsid/daemonization, or let descendants escape that owned group.
Record runner/command hashes, owned PID/start-time/group and raw exit codes.
The temporary runner may implement only this validation contract; approved
production code and criteria stay unchanged.

S0 array estimate: 335313120 B; conservative disk proposal: 1744368064 B
(2×arrays + 1 GiB); observed free: 137937985536 B; available memory:
1691043225600 B. Capacity observations are from 2026-11-04 08:56 UTC.
Refresh capacity before launch; preserve the existing 1 GiB reserve and report
committed/staging/evidence usage separately. Compression, full-episode time and
peak RSS are measurements to obtain, not frozen performance claims.

Manual inspection need not keep a simulator alive. Machine work stops by the
shared deadline; visual review of saved server-local figures can finish later.
Until the actual visual evidence exists, Gate C remains pending, even if every
automatic command exits 0.

## Preflight and existing command forms

Under the recorded authorization, verify clean exact Root/Child, both input hashes and
the exact three-member set/lengths; refresh disk readiness and output absence.
Use existing approved source resolution, no sampling, state-index shifts or
corpus expansion. Read the server fetch skill before any necessary isolated fetch.
Do not re-run S0/121 tests or the already closed six-frame Gate B merely to repeat
those facts. S0's native full-episode source binding is the reference.

Execution may use the following existing single-episode CLI form, substituting
only the three frozen task/global-ID pairs. This stops at a failed episode before
starting the next task. The manifest remains the authoritative cohort and hash
guard. The approved cache identity contains source/mapping/code/cameras/frames/
storage, not the selector form; per-ID calls do not change episode payload identity.
Each command must have its own preserved stdout/stderr/time record.
The working directory for every Python invocation is the exact clean source
checkout above (`CODE_ROOT`); bind paths before running `cd "$CODE_ROOT"`.

```bash
"$SIM_PYTHON" -m tools.g2.export_robocasa_rgbd_pose \
  --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" --output-root "$CACHE_ROOT" \
  --task-class "$TASK" --global-episode "$GLOBAL_ID" \
  --cameras robot0_agentview_left,robot0_eye_in_hand \
  --state-index-policy frame_index --depth-format uint16_mm --chunk-frames 32
```

No `--frames`: export each full episode. Bind all variables to the paths/table
above inside the reviewed validation runner; do not execute unbounded selectors.
Output episode suffixes are 000502, 002022, 004038. Read-only offline and sampled
native verification use the same approved verifier:

```bash
"$SIM_PYTHON" -m tools.g2.verify_robocasa_rgbd_pose \
  --episode-dir "$EPISODE_DIR" --report "$NEW_OFFLINE_REPORT"
"$SIM_PYTHON" -m tools.g2.verify_robocasa_rgbd_pose \
  --episode-dir "$EPISODE_DIR" --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" \
  --state-index-policy frame_index --frames "$SAMPLE_FRAMES" --replay \
  --geometry-atol-m 0.01 --min-ray-samples 16 --rgb-mae-max 5 \
  --report "$NEW_NATIVE_REPORT"
```

All report names are new/immutable. Initially omit visual-review-ref while a new
review is pending; never cite a not-yet-written record as a completed inspection.

## S1 — full export plus one explicitly approved interruption/retry

The formal review authorizes **exactly one deliberate owned-process interruption**
below and one same-identity restart, as well as normal exports. It does not permit
retries of unexpected failures, repeated injection or partial-chunk continuation.

1. Fully export CloseFridge 502; verify its COMPLETE/manifest/hashes and save the
   committed episode hash snapshot before proceeding.
2. Start only NavigateKitchen 2022 in an owned export process and identify its
   unique new `.staging/<uuid>` against the prelaunch snapshot. Require the exact
   Python process alive, verified command/PID/start-time/cache ownership, and
   its committed episode destination/COMPLETE still absent. Wait for both cameras'
   first complete, closed, fsynced `chunk_000000.npz` files (indices 0–31);
   file stability/readability can be checked. Production `flush()` closes each
   chunk only after its own `fsync`. Then send one SIGTERM only to that confirmed
   Python PID. A shell/time wrapper PID is not automatically the Python PID.
   `frames.jsonl` is buffered and explicitly flushed/fsynced only at the end of
   the episode: an observed row is optional unverified buffered progress, never
   a durable trigger, checkpoint or required invariant. Record signal/raw exit
   (143 or subprocess -15 only if actually observed), stage/chunk identities and
   before/after COMPLETE states. Bound observation by process liveness and the
   shared deadline. Never target a reused PID, unrelated process or shared group.
3. Confirm the owned exporter has stopped and the 2022 result is not committed.
   Then make **one planned retry of 2022**, same arguments/cache identity. This
   implementation restarts an unfinished episode from frame 0; it does not reuse
   partial chunks. Old uncommitted staging/failure evidence remains preserved.
   SIGTERM may leave `.staging` without `.failed/failure.json` because Python
   exception handling need not run; retain it without manufacturing a failure file.
   Require a complete 177-frame result, no duplicate committed frames and unchanged
   CloseFridge 502 hashes. If 2022 committed before the signal, recovery evidence is
   INCONCLUSIVE; do not relabel it or automatically repeat the injection. The same
   applies whenever no safe trigger is observed. Completed exports can still be
   reported, but do not claim the full Gate C PASS without the recovery witness.
4. Export PickPlaceCounterToCabinet 4038 fully. Require all three full lengths,
   source/runtime/mapping identity and complete immutable outputs. No fourth
   episode/member is selected. The one interrupted attempt adds work only from
   the same 177-frame episode; record durable/observed progress without pretending
   it is an exact count of all in-flight rendered frames.

Any unplanned error, nonzero exit, drift or capacity/asset failure stops the run,
preserving all evidence. No source edits, environment repair, automatic reruns,
additional selection or deadline extension is authorized by this contract.

## S2 — complete integrity and 18 sampled native/visual checks

- Offline-verify each entire cache: full_episode=true, lengths 429/177/246,
  contiguous unique indices, both cameras, all payload/array hashes, calibrated
  K/poses, valid masks/ranges and quantization bounds across 852 frames.
- Native-verify the exact sample table. Require all 18 spatial groups PASS,
  cache/fresh parity and runtime match, at least 16 matching rays and max
  optical-Z error <=0.01 m, matrix/reprojection/codec bounds unchanged. Record
  actual eligible coverage and ray counts; do not raise the minimum to 128 or
  lower criteria to obtain a pass. Low coverage/unknown filtering is non-success.
- Keep all numeric RGB MAE/PSNR/SSIM and failures diagnostic/nonblocking. The
  source RGB remains original video, with no replacement or photometric fitting.
- Produce server-local original-RGB/Depth contour/occlusion views for these
  scenes. Owner or documented independent review must identify task/global ID,
  frames, cameras, cache/export digest, image/report hashes, reviewer/time and
  actual conclusion. Prior six-image acceptance is not blanket approval here.
  External review can link immutable machine reports without rewriting them or
  re-running physics merely to insert a reference. No automatic visual PASS.

## S3 — verified reuse, timing, memory and storage

Snapshot each committed episode's payload/manifest/COMPLETE hashes. Repeat the
same per-ID export commands once. Require 3/3 SKIPPED_VERIFIED and unchanged
episode hashes, with no replay/environment construction on that code path.
New `_runs` logs are expected and are not episode payload changes. A completed
cache skip alone is **not** evidence of unfinished-episode recovery; S1 provides
that separate witness.

Record 852 successfully committed frames, interrupted-attempt overhead separately, S1 elapsed
including initialization/retry, total machine elapsed, per-command peak RSS and
its measurement scope, committed compressed bytes/raw arrays/ratio, preserved
staging bytes, total cache/evidence footprint and final free space. Clearly label
export throughput versus total validation throughput; exclude neither retries
nor startup silently. Do not extrapolate old 28 ms/frame or promise full-corpus speed.

Final PASS requires S1 recovery evidence, full integrity, all 18 native spatial
checks, actual external visual acceptance and idempotent/resource measurements.
Missing/interrupted/unreviewed evidence is PARTIAL/INCONCLUSIVE, not complete
Gate C. Return bounded aggregate text/status/hashes and server-local paths only;
all RGB/Depth/NPZ/video/images/server scripts remain on the server.

No N100, V3 merge, nav_sg/Global PSS, training/Cosmos model/DCP, old-cache writes,
GPU/EGL operations or other-job interruption is authorized by this document.
