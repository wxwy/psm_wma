# No-TTT asynchronous data preparation — isolated candidate

Authority: Owner Issue #9 and
`2026-10-29_V3_NoTTT_Async_Data_GPU_Overlap_Codex_Implementation_Directive.md`.
Baseline Root `3d5806a2b702b42d3f24e7645aa7cec9cd70b0c7`, Child
`746c5cf2f2324104a62fb71510343aa40d3976c5`. Branch
`v3-nottt-async-overlap-20261029`; not merged into canonical branches.

## Actual execution path

`NOTTT_LOADER_WORKERS=0` retains the original `producer.produce` / native
Packed128 path. Defaults, job identity/digest, frontier format, Generation-only
optimizer and original native losses are unchanged. The cached-SFT builder only
retains constructor metadata; it executes the same transform operations.

Positive worker counts instantiate `NoTTTAsyncLoader` through the actual matched
trainer. One persistent official PyTorch DataLoader pool per rank owns local
Source Reader, mmap Cache Reader, tokenizer and deterministic full Transform.
The recipe contains paths and lazy configuration, never a live model, HF Dataset,
producer or tokenizer. Only the already staged local processor directory is
reopened; worker reconstruction does not invoke HF CLI downloads.

At Window begin, the main process freezes current requests and previews exactly
one next plan from the current candidate frontier. This is metadata planning and
two stat witnesses/request, not synchronous source payload reads. The sampler
contains at most 64 B8/GA4 request records; official DataLoader credits bound
in-flight work to `workers * prefetch_factor`. It returns in consumer order even
when workers complete out of order. Consuming a Member dispatches later work
before native forward/backward. At successful optimizer completion only the
active frontier is published. The next `begin` checks that the actual plan
equals the speculative plan before admitting another preview.

The explicit `persistent_workers=False` option remains supported: it discards
neutral speculative work and reopens the pool next Window. Default persistent
mode reuses prepared next-Window packages. Nonpersistent mode has no promised
cross-step throughput benefit and is not the preferred performance profile.

## RNG and data equivalence

The accepted production capability is the exact JSON `ActionTransformPipeline`,
ordinary single-caption `TextTokenizerTransform`, known local Edge processor,
and `legacy_global` RNG mode. Constructor fields, prompt formatting, resize,
ActionProcessor and tokenizer reconstruction metadata are checked. Unsupported
or mutated pipelines fail closed; no fallback is used for production nw>0.

JSON formatting disables the separate stochastic idle-text augmentation. Each
consumer's sole Transform random operation is the original CFG Python draw.
Workers run its conditioned Transform with CFG decision disabled, and prepare
the same processor's empty-caption tokens. Both Source and Transform must be
Python/NumPy/Torch CPU RNG-neutral in the worker. The trainer draws the original
`random.random()` at each original consumer position and, when selected, replaces
exactly caption and tokens with the precomputed empty branch. No future training
RNG is predicted or consumed, and model/callback draws may interleave normally.

Uncommitted Window failure restores its parent Python/NumPy/Torch CPU RNG
snapshot and, if already initialized, the rank's current CUDA RNG snapshot.
Successful `finish` releases that snapshot without restoring it. The failed
trainer remains poisoned: this is not an optimizer/model rollback or permission
to reuse it; recovery restores all state from a legal persistent checkpoint.
CPU tests exercise CPU RNG restoration; actual CUDA restoration awaits the
separately authorized native gate.

## Bounded memory, identity, failures and checkpoint

- Recipes: <=1 MiB production metadata (outer generic injection cap 64 MiB).
- Encoded segment packet: default <=32 MiB; conservative budget checked before
  cloning and exact encoded length checked afterward. Zero video geometry is
  transported as scalar storage without first expanding a dense pixel tensor.
- Default in-flight encoded cap: nw8/prefetch1 = 256 MiB/rank, plus current
  Member/native batch, worker preparation and PyTorch queue overhead.
- Mmap cache preserves the previous **per-worker** cap (default 2 GiB), with at
  most `max(1,8/workers)` Episodes/worker. Thus nw8 has <=16 GiB mapped-file cap
  per rank and <=8 cached Episodes. Mapped bytes are not a measured RSS bound;
  worker max RSS/mapped bytes are reported and actual world4 RAM remains a
  deployment measurement. Shrinking each worker to 256 MiB would newly reject
  valid previously accepted large Episode files, so is not done.
- Request token, generation, Window, actual owned worker PID, exact Segment
  chronology/provenance/shape and original CFG metadata are checked before RNG
  consumption. Source/Cache file dev/inode/size/mtime/ctime are frozen at admit,
  checked around worker work, and checked again before consumption. Original
  exact-window row, cache, action and latent checks remain in the real producer.
- Worker startup hides CUDA and rank variables before imports; it limits CPU
  threads and uses offline readers. No optimizer/frontier or model enters IPC.
- Worker errors, death, timeout, invalid packets and cancellation close the pool
  with the existing bounded terminate/kill/reap implementation. No implicit
  serial retry can masquerade as successful asynchronous execution.
- Checkpoint records only the original committed frontier format/bindings;
  active work is forbidden. Neutral speculative queues remain bounded and are
  never serialized. The callback does not alter RNG after DCP has captured it.

Runtime metrics report Source/Transform worker sums, parent wait/decode/CFG,
collate, worker RSS and queue/mmap limits. Full monotonic traces are sampled for
the first three Windows after pool creation and every 1000 Windows; inexpensive
aggregates continue each Window. These are host intervals, not measured CUDA
idle time. Compact-video and worker overlap benefits are not conflated.

## CPU replay and evidence contract

After freezing a clean exact Pair:

```bash
python tools/v3/run_no_ttt_async_cpu_gate.py \
  --root-worktree /workspace/psm-wma-nottt-async \
  --expected-root <FULL_FORMAL_ROOT> \
  --expected-child <FULL_FORMAL_CHILD> \
  --evidence-dir <NEW_EXTERNAL_DIRECTORY>
```

The runner sets CUDA hidden, CPU/offline execution and external Hugging Face,
Matplotlib and other caches. It records exact commands/env/source hashes, Ruff
0.12.7 check/format, syntax, raw JUnit/logs and unchanged source before/after.
Nonzero exit, skips, no tests, dirty source or identity mismatch prevent PASS.

New CPU tests use real spawn, production Loader/Trainer/Producer/Transform,
native Packed collator, temporary synthetic Source/Cache and a lightweight text
processor/model. They cover nw0/1/2/4/8, four logical ranks, GA4/T16 full/partial,
interleaved three-stream RNG, 0→8/8→0/8→8 full CPU state recovery, faults and
neutral checkpoint preview. Timeline requires actual next-Member and next-Window
Source **and** Transform overlap with a CPU fake-compute callback over three
Windows. An unchanged old RAW backend is recorded as expected RED for this goal.

Existing generic RAW worker/three-RNG Transform tests remain as regression tests.
Their reduced-B1 Resume fixture explicitly injects the old RAW backend because
an arbitrary stochastic transform is not the production JSON capability. Its
assertions are retained; it is not counted as evidence of the new async path.
The new full-B8 Trainer tests directly cover that path with noisy model RNG and
CFG-dependent losses. Frozen checkpoint schemas and old test assertions are not
relaxed.

## Stop boundary

Final CPU result and Formal Pair are supplied by the subsequent author handoff;
this implementation document does not claim an unexecuted PASS. Submit Child
then Root candidate and STOP for GPT fresh incremental Code Gate. Then DS
independent CPU, Owner-authorized isolated real DCP/GPU performance comparison,
and only later legal checkpoint-boundary switch of the existing formal Job.
No real Source/model/DCP/GPU, current Job change, fresh training, evaluation,
canonical merge or historical evidence operation is authorized here.
