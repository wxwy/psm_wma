# EvalV2 split render mapping and Media lifecycle — author handoff

Status: **REVIEW — fresh GPT Code Gate requested**, author scoped CPU PASS.
No implementation approval, canonical merge or runtime authorization is inferred.

## Exact implementation

| Object | SHA |
|---|---|
| Formal Root | `46d3a604e66ca139e2f060fd4caaaa0583a1035f` |
| Formal Child / Gitlink | `d3b2a29b978ff4abef800b9e71fab4422b7a0d23` |
| Independent candidate branch, both repos | `v3-eval-v2-render-media-20261101` |
| Canonical base Root | `7e2be5ca40891915a1e86eea935ed054ec1984dd` |
| Canonical base Child | `8664267704da3206e719f3c7eef2b5ed86e2a417` |

Subsequent evidence/Inbox/receipt commits do not replace this Formal Pair. Earlier
renderer-stage commits91896fac/f1439ac3 and118 development passes were WIP,
not an approved code Gate. Review both items against the canonical base.

## Owner scope and resulting behavior

Target example: configurable2 Servers /16 Sim, Server GPUs4/5, EGL render GPUs6/7,
M8/B2, batch wait20ms, all rollout/generated videos. Quantities, IDs, backend,
budgets and batch settings remain configurable; GPU0–3 receive no target work.
Only this independent candidate and CPU checks are authorized. No active shared
worktree, out2, training Job, Config, DCP, model, data or server log is accessed.

1. Root config/CLI/resource/runtime/identity support ordered `render_gpu_ids` and
   `render_backend`, selected-device budget/admission checks and immutable
   Manifest/invocation rendering identity. OSMesa remains available. The example
   is `configs/eval/robocasa_eval_v2_split_render.example.yaml` with placeholder
   asset paths; it is not a ready-to-run GPU authorization.
2. Each Sim gets no CUDA visibility. Before vendor import, Child resolves the
   assigned NVML PCI identity to a unique EGL device via DRM/sysfs, sets the actual
   EGL enumeration index, then checks the actual current Context after reset.
   Missing/ambiguous proof blocks; no ordinal-equality fallback. Identity proofs
   use existing runtime records. Real extension/DRM/H100 availability is untested.
3. Media closes the feeder before reader/writer on the normal path and uses a
   parent-only serialized reader-close callback shared by parent and feeder.
   Full-pipe/dead-consumer cleanup is bounded. EBADF stays diagnostic; unknown
   close errors and live encoder/feeder state remain blocking. No global stdlib
   patch or independent encoder PGID is introduced.
4. `forced_encoder_cleanup` records history; `process_cleanup_failed`,
   `encoder_alive` and `feeder_alive` describe cleanup status. The adapter no longer
   mislabels a successful forced reap as a live-process failure. Core/SR/Local
   cleanup retain their existing behavior.
5. After Core commit, Root gives late exit/zombie reap a finite grace, then
   TERM/KILL only verified owned descendants using pidfd identity pinning.
   Actor/resource tracker/foreign processes are protected; actual survivors,
   ambiguous identity and unavailable safe signalling remain fail-closed. A live
   feeder/server media fault still blocks even if no OS descendant remains.

## DS observations versus analysis

The Owner supplied DS's Python3.13 QueueFeederThread traceback: sentinel
`reader_close()` EBADF followed by semaphore over-release, plus original ep006
media diagnostics and ep008 resume log references. These are DS-reported facts;
Codex did not read the training server. Frozen out2 results were not touched.

CPython3.13 source independently confirms that sentinel close is inside the
ordinary exception handler, **not a finally block**. The CPU control injects
reader EBADF into the real `_feed()` path, reproduces its secondary ValueError,
and verifies that the serialized diagnostic callback prevents it. This supports
the reachable failure mechanism; it does not prove every descriptor failure on
the server has the same origin. Merely swapping close/join is insufficient for
a blocked full pipe. EBADF never proves process death. DS's suggestion to relax
the residual check was not adopted: cleanup is bounded, verified and still fails
on genuine residuals. Optional encoder PGID separation was not implemented.

## Author CPU evidence

Evidence root:
`docs/collab/codex/evidence/2026-11-01_eval_v2_render_media_author_cpu/`.

| Check | Result |
|---|---|
| Final clean-Pair CPU |192 passed,0failure/error/skip |
| Python |3.13.5 |
| Ruff |0.12.7 check and format PASS, Root and Child scoped files |
| Syntax / diff-check |PASS |
| Formal source binding |23/23 Git blobs and SHA256 matched |
| Raw artifact hashes |53 files retained in SHA256SUMS.json |
| Model/inference/data/trainer/checkpoint/vendor subtree protection |Unchanged against base |
| Independent DS / real EGL / real FFmpeg / model / GPU |Not executed |

The192 consist of55 render mapping/device tests,31 Media/ownership tests,3 worker,
18 slot,8 process,50 rollout policy,17 configuration,8 native and2 optional-media
regressions. Existing assertions were not loosened. Actual CPU integration covers
eight fake encoder slots for two rounds, full pipe, ignored TERM, force kill,
feeder exit, descriptor closure, exact Local reset and immutable Core behavior,
late exit/zombie reap, PID reuse, new descendants, and a real owned orphan killed
and reaped while an unrelated process survives. No FFmpeg binary was launched.

Exact final command, cwd, explicit environment and child commands are retained
in `final/invocation.json` and `final/commands.json`. Author runner:

```bash
# cwd: /workspace/psm-wma-eval-render-media
/tmp/psm-eval-render-media-20261101/python313/bin/python \
  /tmp/psm-eval-render-media-20261101/combined_cpu.py \
  /tmp/psm-eval-render-media-20261101/final_author_cpu --formal
```

The runner explicitly clears CUDA visibility, uses CPU/offline settings and
external HF/Matplotlib/XDG/Ruff caches, verifies a clean exact Pair, and checks
source hashes and Git status before/after execution. Original JUnit, stdout,
Ruff/format/syntax logs and diffs are retained. The earlier fixture E731 stop
(before pytest), development29 and development192 passes remain separate; they
are not added to the final count. The stdlib RED control is an expected injected
error path inside a passing test, not a frozen historical-production RED Gate.

## Review focus and stopping point

Source anchors: Root `scripts/robocasa_eval_v2/config.py:235`,
`scripts/robocasa_eval_v2/resources.py:14`,
`scripts/robocasa_eval_v2/runtime.py:668`,
`scripts/robocasa_eval_v2_processes.py:48`; Child
`cosmos_framework/simulation/robocasa/render_devices.py:121`,
`cosmos_framework/evaluation/robocasa_v2/media.py:18`,
`cosmos_framework/simulation/robocasa/eval_v2_adapter.py:281`,
`cosmos_framework/evaluation/robocasa_v2/contract.py:33`.

Please review this exact new Pair for the two Owner items. Scheduler/Store,
Action Server, transaction deadlines/replay, model/native batch, Local-TTT
algorithms, training, Checkpoint and Vendor implementation are unchanged.
Evidence and append-only request are published only on the candidate branch.
Do not merge V3 or change an active run. After GPT Code Gate and independent DS
CPU, a separately authorized hardware Canary can check M1/B1, then M8/B2 and
B4/B8, actual EGL identity, memory and throughput. No old out2 Resume or formal
evaluation is requested. Stop after candidate publication/readback and wait for
GPT review under the current Owner workflow.
