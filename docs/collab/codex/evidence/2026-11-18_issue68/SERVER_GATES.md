# Issue68 author fixed-source dual-chain Gate

Formal implementation **778022c8fcf431fa16e83a67256ba58b4b464052**.
Child/Gitlink **d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2**.
nav **70eb7b447e65d793b0ebe18b258291ce46f057c1**.
Stacked [Draft PR69](https://github.com/wxwy/psm_wma/pull/69) on unmerged PR67.
Later documentation/evidence commits do not replace this implementation SHA.

**AUTHOR_SAMPLE_PASS: INDEPENDENT_VAE_E2E=PASS; SYNC_VIEW_VAE_E2E=PASS.**
This is author execution, not GPT independent acceptance or a corpus release.

## Actual environment and identity

Existing server PSM Python3.13.11, Torch2.10.0+cu128, NumPy2.2.5, Pillow12.2.0;
no installation or new environment. Weights SHA256:
`20eb789667fa5e60e7516bf509512f6cb61f01b0aa0695eadaea930c13892b36`.
CUDA_VISIBLE_DEVICES=4,5,6,7 in the manager; each spawned worker binds one
physical card and uses cuda:0. Owner explicitly authorized sharing GPU4–7;
GPU0–3 and their training jobs were excluded. No current view process was
stopped or reconfigured. Existing native binaries were reused; the isolated
Root's raster artifact has SHA256
`20784e6d5fba4538a963060e34babc54ac424625a4262f5c9af6b52db7a56255`.
Its C++ source matches the protected production source byte-for-byte; no nav
build/source or production checkout was changed.

Final server CPU: **655/655 PASS, 0fail/error/skip**, static/19file format PASS.
All612 historical test identities and old test-source bytes remain.43 new
cases executed.258 source hashes match formal Git blobs and remain unchanged
through both actual GPU/native/F27 Gates. Legacy B1 loader bytes and original
encode_record AST remain unchanged. Earlier fixed29 server646 and fixed87dd
server651 also passed; final655 is the authoritative expanded run.

Local initial full633PASS/13 inherited dependencySKIP is separate evidence;
those dependencies were available and all cases ran in the server environment.
Initial new-fixture mkdir failure and earlier peer REQUEST_CHANGES reports are
retained. The final read-only peer exact778022 verdict is
**LOCAL_CODE_REVIEW_PASS**,29 related cases PASS0skip plus independent real OS
crash/public-API probes. It closes all five established findings; it does not
claim the peer ran these server/GPU Gates.

## Both actual chains, same engine

Both use CloseBlenderLid/000000 and CloseFridge/000502:37+44 states,4+8
logical Views,89+80 physical encoded records. Room/Island, marked/clean top,
missing directions, object changes, physical owners and compact references
are covered. Each episode/logical View has one PT containing all its versions.

| Check | Independent View-first | Fresh synchronous producer |
|---|---|---|
| Input | Verified existing publications; second copied publication appears after watcher starts | Actual original MuJoCo/native snapshots then F27, fresh output/work/run/spool |
| Physical GPUs performing native encoding |4,5,6,7|4,5,6,7|
| Actual B per native call, T always1 |9,32 (6calls)|2,3,4,6,8 (39calls)|
| Configured per-card maximum |32|32|
| Mixed-episode batches |1|4|
| Native API-call overlap pairs |11|9|
| Real fault |Coordinator register followed by os._exit77 before offer, then resume|Worker os._exit77 after first durable ACK, fenced same-batch recovery|
| Completion |IDLE_TIMEOUT after configurable5s sample idle; resume works|Original full-profile producer DONE; engine DRAINED|
| Exact same-context GPU replay |169/169, max_abs=0, atol=rtol=0|169/169, max_abs=0, atol=rtol=0|
| Final numerical staging/active SQL jobs/events |0/0/0|0/0/0|

The small synchronous producer supplies fewer than32 ready images within its
1s Gate wait; these are genuine multi-image calls, not B1 loops. Actual B32 is
proved by the independent shared engine and the native math probe. Production
default wait remains500ms. Do not describe every synchronous call as B32.
Overlap is measured around encode API calls, including cold load/preprocessing;
it is explicitly **not** a CUDA-kernel overlap trace. Native CUDA timing and
shape counters corroborate actual encoding. ACK-only recovery does not count
as native GPU work; final peer separately verified zero native counters for it.

The independent Gate initializes a real recipe/spool, registers a published
episode in a process that exits77, then resumes. A second episode is published
atomically while that engine runs. It writes its own verified cache without
changing the original View-only products/profile/COMPLETE, explicitly runs
existing posthoc Stage C on only the copies, resumes after retirement without
encoding, and replays the original ordered contexts.

The synchronous Gate uses the original full_production and renderer path.
Durable ACKs were observed while source_ready was still NULL, before episode
packaging ended. Source-ready seals final owner mappings; the original writer,
full profile, v2 source retirement and owned work GC then complete. Real worker
restart count1. All500 state/View image-hash bindings and the View set match
the original publications. Source, SG, task, language, projection and other
profile products pass final validation.

Both final datasets have no full spatial_source.json/gzip, old gzip receipt,
old READY or pending retirement transaction. Both readers work using compact
indices. Historical cache-manifest hashes were reconstructed **in memory for
verification only** and match pre-retirement receipts; all24 final PT file
hashes across the two modes match those historical indices. No working JSON
was restored. Independent pre/post C PT hashes were also directly compared.

## Numerical recipe and timings

Batch recipe:
`b1c6e1f6b2a6b69ae1ffdc5afa47d3454f4d3289d22854a5ed2645ebc130fad1`.
Legacy B1 recipe stays
`3ee9c48399143866b2a0061f3cee01bff35842228f639380d60602d6402e2fc1`.

Fixed-A302885d5 true H100/Wan probes used40 existing real View inputs across
both tasks/variants/Islands. Original B1 re-encoding matches40 cached references
exactly. Two GPUs4+6 ran the matrix concurrently. New-policy B1/8/16/32 vs
legacy B1: maxabs.07421875, RMS.0062556457, relativeL2.0075516306. Same ordered
B32 replay/cross-GPU replay, reverse/unpermute and changed-member other31 each
have maxabs0. Tail7 vs legacyB1 maxabs.046875. Four decoded-image comparisons
have max RGB-byte difference6–8, PSNR53.81–55.20dB. This is a measured visual
difference, not new human approval. Even new-policy actualB1 is a different
recipe from legacyB1. No B1 cache is silently promoted/reused as B32.

The batch adapter and legacy loader are byte-identical from that fixed-A
numerical probe through final778022. Native module hooks retain actual B and
T1 (Wan's internal spatial patchification changes channel3→12 and256→128,
not the batch/time meaning). Final dual Gates independently re-encode all338
selected records under their respective original ordered contexts.

| Measured interval | Seconds / scope |
|---|---|
| Independent execute CLI |94.97, engine portion86.79; includes source/discovery/load/write/validation/5s idle|
| Independent explicit C CLI |63.10|
| Independent retired resume CLI |21.25, no native encoding|
| Synchronous producer CLI |627.52; supervisor portion603.74 includes native/F27/VAE/publication/GC|
| Successful native CUDA aggregate |10.81 independent /12.48 sync; sum across cards, not wall time|
| Encode API aggregate incl. cold loads |65.60 independent /65.91 sync; sum across cards|
| Queue wait P50/P95 sample |4.72/11.33 independent;1.06/1.57 sync (one cold-restart wait18.39)|

Independent Gate wait10s intentionally exercises cross-episode batches; sync
Gate wait1s exercises live production. Real idle shortened5s; default600s and
busy reset are checked with virtual time. IDLE_TIMEOUT never means ALL_COMPLETE.
Math matrix warmed timing varies with shared-GPU load: B32 processed32 images
in medians2.49s/1.85s on GPU4/6; new-policy B1 loop32 medians2.54s/3.02s.
No universal speedup or 9126EP completion-time promise is made. These full
pipeline seconds are **not** a single six-view render latency.

## Space and recovery

| Mode / episode | Before MiB | Final MiB | Compact index bytes |
|---|---:|---:|---:|
| Independent Blender |23.78|22.32|162962|
| Independent Fridge |28.59|27.25|158146|
| Sync Blender |54.63 observed|22.49|162448|
| Sync Fridge |56.13 observed|27.33|157632|

Independent before/after totals are measured with the cache present and use
actual gzip bytes, yielding1.46/1.34MiB net reduction. Sync before totals were
observed while the cache was complete and the full raw source still existed;
they may include retirement staging, so they are not a clean-room capacity
forecast. Raw source sizes33871474/30364595B; final no raw/gzip. Every index
remains below the strict1MiB limit. Sync peak owned work2406803093B, pending
PNG2273902B; after GC only333B work-root ownership metadata remains. Spool
after GC3107452B is control/audit data, with0temporary PTs/events/active jobs.

CPU faults include partial fsync/ACK, exact replay mismatch, stale leases,
OOM-style failure/retry, bounded capacity deadlock failure, actual register
hard exit, changed-source rejection/lease release, identical-pixel distinct
batch cleanup, and unchanged PR67 retirement failure windows/readers. True
GPU OOM, machine power loss, heterogeneous GPU numerical equivalence, a real
10minute idle wait and full9126/32renderer resource/throughput Gates are NOT_RUN.
No full production/retirement, training, merge or old-data deletion occurred.

## Evidence and reproducibility

Exact commands: `server_commands.json`, `cpu_commands.sh`; executed numerical
probe and dual Gate driver: `math_probe.py`, `real_gate.py`. Derived results:
`server_math_cpu_summary.json`, `server_dual_summary.json`,
`historical_payload_audit.json`. Local raw logs/XML live in a/, b/, full/,
r1/, r2/; all original failures/reviews remain. Final peer:peer/r2/REPORT.md.

Server raw logs/JUnit/private pictures/models/states/source/PTs remain only at:

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.g2_issue68_dual_20261118/
  source_d/                       # fixed778022, Childd5
  server_cpu_d/                   # all655, source before/after hashes
  independent_d/                  # copied publications, actual B/C/replay
  sync_d/                         # fresh original producer and actual GPU B/C
  math_baseline/ math_gpu_4/ math_gpu_6/
```

Original selected publications' complete file inventories are unchanged.
Production Rootb631, Childd5, nav70 and fixedRoot778022 remain tracked-clean;
tmux view is alive. No private raw artifact was exported, no server commit or
push, no model A/B/C/D/G1/Child/nav/training/checkpoint/cache edit, no new env.
Keep Draft/training_ready=false. GPT independently reviews this fixed pair;
Owner controls production release. Runbook contains draft commands only.
