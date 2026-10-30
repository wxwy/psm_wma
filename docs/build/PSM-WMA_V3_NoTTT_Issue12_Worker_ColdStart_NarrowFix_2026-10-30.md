# Issue #12 — verified-index worker source, isolated implementation plan

2026-10-30 (Asia/Shanghai). Owner authorizes a narrow isolated candidate and
targeted synthetic CPU tests, then submission to GPT. No canonical promotion,
real source/model/DCP access, GPU, training, or new DS diagnostic is authorized.

## Authority and baseline

- Latest request/review read from advertised and fetched V3
  `9344198a5abf4964a4997bf7e9268b8e5ccc73e8`.
- Frozen No-TTT source: Root `e0fe911dfb9fd34957234828195cf051713f6c3d`,
  Child/Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`.
- This branch starts from its published bookkeeping head
  `2260f2a6f89368301ba50a686676994af90a2ca5`, with the same source.
  Canonical V3's later EvalV2 production promotion is a separate line; do not
  replace its Gitlink, merge that work into this fix, or promote this whole tree.
- Prior Code APPROVE and DS CPU301 PASS stay historical, not new test results.
- Installed/pinned LeRobot fork: `mli0603/lerobot`
  `1a4316c6845330bc552fb982dbc44bdb4f66f2f1` (Child uv.lock).

## Minimal patch

Add a worker-only, verified-index-backed non-visual LeRobot reader. Keep the
official `LeRobotDataset.__getitem__`, delta calculation/query, padding and task
caption methods; replace only eager full-dataset construction and row storage.
Use the already accepted absolute/relative mmap and metadata to route reads.
Load only the requested Episode's non-visual parquet rows, using the official HF
feature casting and Torch transform, with bounded LRU storage. Reject inconsistent
metadata/mapping and missing/changed data; do not build a new index or download.

`AsyncRecipe.build()` injects this reader into the unchanged SourceReader factory
seam. The original synchronous SourceReader/default dataset factory remains
unchanged. Real Source, Cache and Transform continue inside spawned workers.
No model, optimizer, RNG policy, Frontier or DCP changes, no full dataset pickle,
no fork, no change to the 120-second data timeout.

Expected production files: new `trainer/no_ttt_worker_source.py` and narrow
`trainer/no_ttt_async_recipe.py` injection. Tests: new worker-source tests and
focused additions to existing recipe/loader fixtures only if needed. Root:
runbook/evidence, Gitlink, SESSION/TODO and append-only review request.

## Targeted CPU acceptance

1. Real temporary synthetic parquet, metadata and verified index: compare all
   source/LeRobot fields to the unchanged official eager path at first, middle,
   terminal and multi-Episode/subset windows, including captions and padding.
2. Spy/fault the eager constructor/full-load hooks: worker build must perform
   neither full source scan nor full data materialization; first read loads only
   requested rows. Show structural improvement and report synthetic wall only.
3. Bounds, eviction, shared parquet files, mapping/path/data corruption, offline
   failure, parent/worker RNG, true spawn ownership and cleanup.
4. Target existing recipe RNG/order tests plus selected cross-Window overlap and
   CPU model/frontier Resume cases. Do not rerun old CPU301 or real data probes.
5. Ruff 0.12.7 check/format, AST, source fingerprints, exact clean Formal Pair,
   targeted JUnit/raw logs and diff. No assertion weakening or skipped failures.

CPU evidence cannot prove first real packet <120s or GPU throughput. After a new
GPT Code Gate, separately authorized DS checks one real worker first packet;
then a separately authorized matched full-DCP exclusive-GPU A/B must validate
C+1 commit and steady-state end-to-end step wall/current-stream gap. No shared
GPU old A versus exclusive new B speed claim.
