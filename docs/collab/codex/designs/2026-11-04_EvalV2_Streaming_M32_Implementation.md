# Issue17 — EvalV2 streaming implementation and CPU replay

Baseline: Root ea0828c7d45a443cc74ae2582419f14e7782a17e; Child 1069fe78841228cadbbfbe6afbd767eaed6225da. Candidate only: `v3-evalv2-streaming-m32-b32-20261104` in both repositories. No V3 promotion, R04 operation, remote file transfer, hardware run or real dataset/checkpoint access is authorized by this document.

## Explicit new Run

Use `execution_profile: phase_b`, `scheduling_protocol: streaming_task_affinity_v2`, `sims_per_gpu: 32`, and independently `max_infer_batch_size: 8` or `16`. B32 is a supported API ceiling, not a hardware recommendation. `local_memory_mode: off|required` remains explicit and must match the model. Two Policy GPUs produce 64 distinct physical Slot identities even with only 18 Task names; a Run with fewer eligible Episodes creates only useful Sim processes. Dry-run distinguishes physical capacity from executable capacity and does not claim processes were started.

The old default protocol keeps M/B<=8, Task-count useful Slots, original sampling literal, strict Episode-major round barrier, and unchanged old Manifest construction. Phase A stays M=B=1. No historical Run silently switches to streaming. New schedule, sampling, M/B, GPU layout, `max_rss_bytes`, and startup budgets are bound into the immutable Manifest. Scene order across old and new protocols is not an exact matched-scene comparison.

New Runs must supply all six integer `streaming_resources` fields:

| Field | Meaning |
| --- | --- |
| `max_owned_gpu_bytes` | Hard per-selected-GPU memory ceiling for owned compute and graphics PIDs |
| `sim_startup_rss_bytes` | Additional RSS reserved while constructing/resetting a Slot environment |
| `sim_startup_gpu_bytes` | Additional memory reserved on its physical Render GPU (zero allowed for CPU rendering) |
| `server_startup_rss_bytes` | Additional Policy Server startup RSS reservation |
| `server_startup_gpu_bytes` | Additional memory reserved on its physical Policy GPU |
| `initialization_concurrency` | Explicit 1..32 bound on concurrent Slot construction/Task switches |

Select reservations and `max_rss_bytes` from deployment measurements and Owner budgets. The implementation never raises them automatically. Admission combines real owned-process measurements with outstanding startup reservations, then measures again before transferring startup ownership. Unknown meters or exceeded budgets produce `BLOCKED_RESOURCE` and owned cleanup. Foreign GPU occupancy is not a rejection rule. NVML must provide both compute and graphics process measurements; PID/device visibility must be independently verified during the later hardware Gate. RSS uses one `/proc` scan for all owned process groups. CPU fixtures explicitly replace these hardware measurements.

## Ownership and progress

`StreamingScheduler` reuses the current coordinator lease, dispatch tickets, Core validation, finish and cancellation authority. It allocates the earliest pending Episode for a Task, permits multiple different Episodes of the same Task, and never permits duplicate `(task, episode)` or busy physical workers. Task affinity lasts at most four consecutive dispatches before fair selection by dispatched count/rotation. A slow physical Slot does not hold an Episode round barrier.

V2 attempts bind the physical Slot UUID. Environment grants are durable and serially numbered under a Store metadata RLock; actual environment seed/reset provenance remains distinct from the logical Task stream/reset count. Attempt/grant/SimSlot/admitted sampling/Core identities must agree. Short ledger transactions are locked; GPU calls, HTTP, READY, vendor hashing, environment construction and cleanup probes are outside that metadata lock. Task-stream faults remain fail-closed, and cleanup receipts are issued only after all invocation ownership has quiesced. Completed Core is immutable; pending/Owner-pending Resume rules remain in force. Multiple old failed Episodes resolve only through their own replacement Core; concurrent identical health-only resolution is safe and idempotent.

Per-GPU locks cover the complete Server handshake and publication. Invalid identity or startup failure stops the invocation, never automatically spawns a replacement. Every durable spawn is counted in owned resource measurements even before READY. Per-worker locks protect individual physical Slots, with bounded parallel initialization instead of the global startup lock. The closing gate prevents new spawns, reaps unpublished owned processes, waits for in-progress jobs, then publishes cleanup proof. Registration retries observe coordinator cancellation. Full per-worker source/vendor/asset/runtime/render verification remains enabled in production; CPU doubles are selectable only from test code, not the CLI.

The same existing Batch owner serves 32 Sessions per Policy GPU. Explicit `streaming32` capacity is checked in Server startup options, `/info`, registration/assignment ACK and Client; default `legacy8` retains prior limits. Queue, response cache, ACK/frontier, Local update publication, End/reset and strict media durability stay shared across both model modes. Strict media and Ready inference alternate when both have work, preventing an unbounded run of decodes. With rollout disabled, NativeEpisode passes `on_frame=None`; Policy observation and required Local evidence composition are retained.

Bounded telemetry includes owned Slot count, initialization/ready/execution/predicting states, completed Episodes/requests, queue wait p50/p95, recent native generation time and Batch histogram. Worker startup markers split imports/render/vendor/READY; coordinator timers split Server start, make_env assignment, reset and Session register. These diagnostics do not authorize scheduling or certify GPU performance.

## CPU replay and handoff

After freezing the complete Root/Child pair, use the existing read-only Gate engine through:

```bash
CUDA_VISIBLE_DEVICES='' LD_LIBRARY_PATH='' /workspace/.venvs/psm-wma-cpu/bin/python \
  tools/v3/run_eval_v2_streaming_cpu_gate.py \
  --root-worktree /workspace/work/psm-wma-streaming-m32 \
  --expected-root FULL_ROOT_SHA --expected-child FULL_CHILD_SHA \
  --evidence-dir NEW_DIRECTORY_OUTSIDE_WORKTREE
```

The entry point checks clean exact identities, pinned Ruff0.12.7, import origin, Ruff/format/AST, full existing Phase A/B and strict-media suites, and new streaming tests. It saves raw JUnit/logs/environment/commands/source SHA256 and requires shell0, `gate.status=PASS`, zero failure/error/skip, and `source_unchanged=true`. It uses no CUDA or real RoboCasa/model assets. New tests prove two 18×50 runs with 64 distinct actual SimSlot objects and 900 unique public Core results at B8/B16; public Client→dispatcher→native CPU H16/B32 shapes/routing and real CPU Local fast-state isolation; real OS four-Sim overlap at READY/make_env in both modes; Server exit23 with two same-Task Slots, all owned cleanup and external process isolation; public CLI Fresh/Resume; deterministic concurrent fault recovery, startup cancellation, metadata and media fairness. Physics, process/device and diffusion boundaries in the 64-Slot fixture are explicit doubles; separate four-Sim tests use real OS processes.

The common CPU runner also freezes `MUJOCO_GL=osmesa` and `PYOPENGL_PLATFORM=osmesa` in its recorded environment overrides. The first formal replay at Root9869046d/Child82fa270e passed182 inference cases, then stopped at100PASS/1FAIL in Phase A: the legacy CPU Slot fixture inherited the default EGL path without a physical render proof (`core_invalid: KeyError('GPU0')`, followed by its rendezvous timeout). This was a CPU invocation environment omission; production rendering/proof checks and legacy assertions are unchanged. Original `author-formal-01` artifacts remain outside source and must accompany the final evidence.

The targeted OSMesa rerun then exposed the same old fixture's incomplete resolved configuration (`KeyError('save_generated_video')`); the baseline production runtime already required that field. `CpuSlotRuntime` now merges the shared `DEFAULTS` and explicitly selects OSMesa/no-media before applying caller values. Only the test fixture and CPU-runner environment change; old assertions and production defaults stay intact. The targeted failure is retained as `cpu-render-env.*`.

After this fixture correction the unchanged controlled progress test passed1/1 in2.87s: snapshot held the writer lock and both physical workers finished during file I/O, yielding2 valid Core. `cpu-render-env-02.xml/log` preserves this narrow proof; the new Root must still pass the complete unified Gate.

Development evidence is retained outside the source tree at `/workspace/work/eval-streaming-m32-evidence`: capacity80 PASS; initial concurrency11 PASS/3 FAIL due to an incorrectly wired test-only resource probe; corrected initial streaming54 PASS (394.15s); an initial Ruff E731 and its correction; augmented focused60 PASS/2 explicitly deselected completed 900 cases (94.88s). These overlapping development counts must not be added together or represented as final exact-pair/DS evidence. Final pair, counts and evidence location belong in the later handoff receipt.

Independent read-only source review found five actionable concurrency/resource risks, all corrected and re-read: same-Task multi-EP recovery scope/idempotency, unpublished Server accounting, terminal Server startup failure, cleanup fault attempt snapshot, and NVML unavailable-meter handling. No new reachable HIGH was found in that read-only review; it is not a substitute for GPT Code Gate or independent DS execution.

Next authority sequence: exact pair + author CPU evidence → fresh GPT review → DS independent CPU/authorized hardware Gate. Both G2 and EvalV2 require their own approvals; integration later uses the latest V3 without overwriting either history or Gitlink. No candidate is automatically promoted.
