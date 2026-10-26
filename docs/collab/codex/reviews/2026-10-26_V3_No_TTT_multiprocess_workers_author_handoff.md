# Issue #4 — Matched No-TTT multiprocessing implementation handoff

2026-10-26 Asia/Shanghai. **Author CPU candidate, not GPT verdict/DS acceptance/training authorization.**

| Object | Exact identity |
| --- | --- |
| Root implementation | `76d1cc70622d3b456a3c388ad98917b7d532890b` |
| Child and Root Gitlink | `3e5bf90b4eb5fa5cbad9fa7ab62e86bf44c6b07b` |
| Both candidate branches | `v3-nottt-process-workers-20261026` |
| Base production Root | `e6ae2084305a8c24d763d82b517984660cc73c30` |
| Base Child | `923d9c3fd392e6bafbdb1771a292c7b313e6b3dc` |
| Task registration docs base | `0beaeacd7d00b0b5826b3eac12b86676eb8b7db3` |

Implementation is **not merged to V3/v3-local-ttt**. Evidence/Inbox commit following the implementation does not replace the formal Root above. Owner request96b453c4/Issue4 supersedes earlier direct-V3 publication and legacy three-reviewer polling: GPT incremental code review → DS independent CPU → separately authorized runtime gates; STOP after publication.

## Change and contracts

Real PyTorch DataLoader uses spawn CPU processes, immutable frozen-window sampler requests, prefetch1/2, persistence on/off and pin_memory=False. Parent owns sole Planner/Frontier/SourceReader, all stochastic transforms, native collation/model/outer loss/Generation optimizer. Cache mmap and raw policy preparation execute in workers; no live LeRobot/Arrow/model/tokenizer/optimizer is pickled. Source reads remain serial, so performance improvement is **not established**.

`NOTTT_LOADER_WORKERS=0` default remains exact legacy argv/data path/schema/identity; opt-in1/2/4 requires new `no_ttt_*_mpwN_world4_ga4` job. B8/T16/GA4/world4 and nominal2048, terminal consumer weighting and native loss untouched. Worker options bind config/semantic identity and opt-in frontier state; same-job count/options/layout/rank/seed/source drift rejects. Owner world4 source-SHA/dirty admission waiver remains unchanged. No Local-TTT, training model/general trainer/DCP/Queue/vendor changes.

Bounded source/result bytes and mmap metadata/LRU prevent whole-Episode storage IPC. CPU/no-rank/thread environment applies before interpreter startup. Private PyTorch iterator/PID/queue seam is isolated for bounded owned-only cleanup incl partial startup; target PyTorch version must be independently validated. Full ownership/RNG/memory/metrics/commands are in [candidate design/runbook](../designs/2026-10-26_V3_No_TTT_process_workers_candidate.md).

Three original fixture defects were reproduced from original923d9c3 code and minimally repaired: escaped comment swallowed world4 catalog initialization; stale Owner diagnostic regex; bytes operand against text stderr. Assertions remain strict. New gradient-oracle tests explicitly scope enable_grad and restore earlier global mode so a prior inference fixture cannot disable their mathematical oracle. Intermediate failures retained, never aggregated into final PASS.

## Author CPU Evidence

Frozen20module run: **601 passed, 0 failures, 0 errors, 5 pre-existing real-asset skips;42 successful subtests**. New worker/Resume/entry modules: **62 passed,0 skipped**. Ruff0.12.7 check/format, syntax11Python and Bash, source SHA and protected paths PASS. Not whole-repository pytest and not DS independent execution.

- Worker0 vs1/2/4: real child PID, single/four logical ranks, full/terminal B8/T16/GA4, Source/action/state/latent/masks, stochastic main Transform/RNG, actual native collator, weighted toy generation gradient.
- 30 rank/config witness rows, 70 unique child PIDs; all witnessed PIDs absent after exit. Persistent on/off, bounded prefetch/packet, startup/crash/exception/timeout/ignoredSIGTERM/SIGKILL/order/ABI/source/cancel/restart tests and unrelated-process survival.
- Actual raw dataset/policy/cache factory on temporary synthetic `.pt` and parquet; mmap/window/header/bounds validation. No production datasets/assets read.
- Actual No-TTT training_step/frontier callback, four logical CPU ranks separately: Fresh100 vs exact same-state Resume101→500, model/momentum/scheduler/frontier/consumer/RNG continuity. Uses **reduced T1/B1/GA4 toy model**, not real DCP/CUDA/FSDP/NCCL/Gloo. Full B8/T16/GA4 tested separately.
- Existing G1/No-TTT/F0/F1/data/outer loss contracts and Owner world4 source exemption regressions retained. Five optional real-asset skips are enumerated in STATUS; they are **not PASS**.

Evidence: `docs/collab/codex/evidence/2026-10-26_nottt_multiprocess_workers_author_cpu/`: final original JUnit/log/command/environment, source hashes, STATUS, static logs, PID witness, exact Root/Child baseline patches, protected path proof, artifact SHA256SUMS. `iterations/` contains failed iterations including original baseline RED and earlier fixture failures, not additional success counts. Reproduction command/env/cwd in `command.json`; frozen harness `run_final.py` captures full20module argv. CPU PyTorch2.10.0+cpu, Python3.12.14; independent DS environment must be reported separately.

## Usage after gates

Existing paths/venv options are inherited. New namespace is automatic; do not point at an existing formal job:

```bash
NOTTT_LOADER_WORKERS=2 NOTTT_PREFETCH_FACTOR=1 NOTTT_PERSISTENT_WORKERS=1 \
  NOTTT_LOADER_TIMEOUT_S=120 \
  bash scripts/train_v3_matched_no_ttt_4gpu.sh fresh 100
```

This is documentation, not execution authorization. Existing job defaults0. Changing workers/prefetch/persistence/timeout requires another namespace; this candidate does not auto-migrate current checkpoints.

## Review request / remaining gates

Request GPT fresh incremental review of exact pair above, scoped to Issue4. If approved, DS clean detached synthetic CPU replay (no production mutation), then separately authorized real-source RAM/IO and target-PyTorch lifecycle checks. Physical concurrent world4/FSDP/CUDA/native loss gradients, strict real DCP/CUDA-RNG Save→Resume, official DROID model load and matched worker0/1/2/4 H100 performance remain runtime Gates. No GPU speedup/GPU-ready claim. Do not merge candidate into V3 or start any job before required approval. G1/No-TTT live training and historical evidence remain untouched.

Publication readback observed other work advance V3 to97753e9dd7fc885b3bdeade903e61b6f55c7d746 (four evaluation-only commits), canonical Child923d9c3 unchanged. That work is preserved and outside this baseline-bound candidate; no V3 merge/write. See remote_provenance.json. For a portable replay use `PSM_ROOT=<detached-root> NOTTT_CPU_EVIDENCE_ROOT=<new-external-dir> <CPU_PYTHON> reproduce_cpu.py <new-run-name>`; unlike original author run_final.py, reproduce_cpu.py embeds the complete20module list and needs no prior external runner. Reuse an appropriate independently provisioned CPU environment.
