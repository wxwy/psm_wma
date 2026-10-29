# Issue #9 — No-TTT asynchronous Source/Transform author handoff

Date: 2026-10-29, Asia/Shanghai. **AUTHOR_CPU_PASS; requesting fresh GPT Code Gate.**
This is neither an independent DS verdict nor a GPU performance/real-DCP PASS.

| Object | Exact identity |
| --- | --- |
| Formal Implementation Root | `e0fe911dfb9fd34957234828195cf051713f6c3d` |
| Formal Child / Gitlink | `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7` |
| Baseline Root | `3d5806a2b702b42d3f24e7645aa7cec9cd70b0c7` |
| Baseline Child / Gitlink | `746c5cf2f2324104a62fb71510343aa40d3976c5` |
| Isolated Root and Child branch | `v3-nottt-async-overlap-20261029` |
| Task | `V3-NOTTT-ASYNC-OVERLAP-NWPOS-20261029` |

Subsequent peer-document merges, this evidence/handoff and publication receipts
are bookkeeping; they never replace the Formal Pair above. Canonical V3 and
v3-local-ttt are not updated by candidate publication.

## Authority, ACK and actual implementation

The complete Owner directive was read from baseline V3, together with AGENTS,
SESSION, Inbox, TODO, existing code and the legacy worker implementation. Actual
ACK was posted to [Issue #9](https://github.com/wxwy/psm_wma/issues/9#issuecomment-6495422587).
The Stage/Owner/RNG plan was committed and published first (`3007a5cd2f9f47413a7a1475737aea2733ea2092`).
Detailed implementation and CPU replay contract:
`docs/build/PSM-WMA_V3_NoTTT_Async_Overlap_Implementation_2026-10-29.md`.

- Positive worker counts use the actual `MatchedNoTTTTrainer → NoTTTAsyncLoader`
  path. Official spawn DataLoader workers now perform Source Read, Cache access
  and the full deterministic Action Transform. Main retains bounded metadata
  admission/stat checks, ordered CFG selection, Pack/Collate/H2D, model and
  optimizer/frontier ownership. There is no synchronous production fallback.
- One active and one candidate-frontier preview Window provide bounded
  next-Member and cross-Window preparation. Promotion requires the actual next
  plan to match the preview; speculative work never publishes a frontier.
- Workers prepare conditioned text and empty-caption tokens. Main performs the
  original one Python CFG draw at the original consumer position. No per-sample
  seed, speculative training RNG advance or RNG prediction is introduced.
  Unsupported transforms/processors are rejected rather than assumed safe.
- Source/Cache/Index roots are resolved before spawn, request file stat witnesses
  are checked around preparation and before consumption, and exact request,
  provenance, Window/generation and owned PID fences are retained. Compact video
  stays a scalar-storage carrier; transport limits are checked before cloning.
- Uncommitted close restores parent CPU RNG streams and the already initialized
  current CUDA RNG snapshot. Failed trainers remain poisoned; model/optimizer
  rollback is not claimed. Successful commit clears the rollback snapshot.
- workers0, original native loss/GA weighting, window planner, model, optimizer,
  scheduler, DCP and checkpoint schema are unchanged. Worker options remain
  runtime-only. The historical formal Job identity exception is not modified.

Production changes are confined to the new recipe/loader, matched Trainer wiring,
runtime profile provenance and cached-SFT reconstruction metadata. No root
production launcher/script, G1/Local-TTT, Vendor, model or DCP code changed.

## Frozen CPU results

Evidence root:
`docs/collab/codex/evidence/2026-10-29_nottt_async_overlap_author_cpu/`.

| Check | Actual final result |
| --- | --- |
| New recipe/loader/Trainer suites | 72 passed |
| Existing No-TTT/source/config/entry suites | 229 passed |
| Total | **301 passed, 0 failure/error/skip** |
| Real-data optional node | 1 explicitly deselected; NOT RUN, not counted as PASS |
| Ruff 0.12.7 check / format | PASS, 13 scoped files |
| AST syntax / import origin | PASS |
| Exact Root/Child/Gitlink; clean source before/after | PASS; `source_unchanged=true` |
| Internal protected-source audit | 51 checks PASS; not an external Code Gate |
| Frozen watched-source Git Blob bindings | 18/18 match |
| Artifact SHA256 entries | 81, excluding the manifest itself |

The new tests exercise actual CPU spawn, production Loader/Trainer/Producer and
Action Transform, native Packed collation, four logical ranks, T16/B8/GA4
full/partial windows, nw1/2/4/8 against workers0, interleaved Python/NumPy/Torch
model RNG, and same-job 0→8/8→0/8→8 full CPU state recovery. Source/Transform,
token/mask/SequencePlan, model, momentum, scheduler, iteration, RNG and frontier
comparisons remain exact. Physics, full Cosmos/model/diffusion, native CUDA and
real dataset/DCP are not executed; data and text/model boundaries are explicit
synthetic fixtures.

Faults cover errors/death/timeout/ignored SIGTERM, out-of-order completion,
stale/duplicate/foreign packets, Source/Cache changes after preparation,
pre-clone byte limits, NaN loss/gradient, skipped optimizer and native errors.
Owned workers are reaped and a foreign process is preserved. Speculative
checkpoint tests retain the original schema without consuming parent RNG.

Final command (all caches/output external, CUDA hidden/offline in Runner):

```bash
python tools/v3/run_no_ttt_async_cpu_gate.py \
  --root-worktree /workspace/psm-wma-nottt-async \
  --expected-root e0fe911dfb9fd34957234828195cf051713f6c3d \
  --expected-child f6a92d47b6dac7998ddc58b3da26ef93f8068dc7 \
  --evidence-dir /tmp/psm-nottt-async-overlap-20261029/locked03
```

Use a new external directory for any later independent replay. The additional
wrong-Pair probe returned exit1/BLOCKED before tests. A synthetic nw8 resource
probe captured eight actual worker PIDs, all exit0/reaped, approximately
503036–503280 KiB peak RSS per process and one 271437-byte segment envelope.
Default declared in-flight encoded cap is 256 MiB/rank (8×1×32 MiB); mmap cap
retains the old 2 GiB/worker meaning, at most eight mapped Episodes/rank.
These are synthetic observations and configured bounds, not native world4 RAM
qualification. Per-process RSS peaks must not be presented as live free memory.

## Timeline result and performance boundary

Three consecutive optimizer Windows use actual Source/Transform work and a
CPU hash-compute callback. Monotonic trace and commit times are retained:

| Intersection with current fake compute | Source | Transform |
| --- | ---: | ---: |
| Later Member | 96.257 ms | 160.573 ms |
| Next Window | 24.373 ms | 38.022 ms |

The original unchanged RAW backend has a separate expected
`RED_NO_FULL_PIPELINE_OVERLAP` witness. The serial control has no Source/Transform
intersection. Neither worker count nor merely starting processes constitutes
the positive assertion.

**No acceleration claim:** the three-Window asynchronous span including cold
spawn is 7760.856 ms versus 3315.156 ms for the serial control, with parent wait
5971.737 ms. This small CPU test proves concurrency and exact state, not steady
GPU throughput. Real Compact1 nw0 versus nw8 must still use matched checkpoint,
model/data and CUDA timing after separate authorization. Full Source Reader/
tokenizer startup, world4 RAM, I/O contention and actual GPU idle remain native
qualification items. Explicit nonpersistent mode may discard neutral previews;
default persistent mode is the intended cross-step performance profile.

## Failed attempts and old-test protection

Raw attempts are preserved separately and never summed into final PASS:

1. `66986d5f / 5124a2b7`: 55 pass/1 fail. A newly added per-GA test asserted
   initial frontier before lazy Resume applied; it now uses the persisted
   pending frontier and retains the no-early-commit assertions.
2. `e8c49c07 / d64e5c1d`: new72 PASS; regression122 PASS/1 FAIL/1 SKIP before
   stopping. An old config fixture used unsupported SimpleNamespace and lacked
   its receipt. It now uses supported structured records and temporary receipt;
   the production identity serializer is unchanged. Another old strict semantic
   test incorrectly selected the Owner-exempt historical formal Job; it now
   selects an ordinary strict Job with the same rejection assertions.

All **102 original assert ASTs** across the three adjusted old test modules are
retained. Normalization removes only the precisely listed test fixture changes;
unchanged functions remain exact. The one optional real-data node is retained
in source and explicitly excluded because this task forbids real assets.
The generic three-RNG/reduced-B1 RAW Resume fixture still injects its old backend
explicitly; it is not advertised as proof of the new production async route.
The new B8 noisy-model suites provide that proof directly.

Full technical diffs, source bindings, raw JUnit/logs, command/env snapshots,
initial RED records, timeline, bounds, internal static audit and artifact hashes
are published. Temporary cache/checkpoint-like test directories are not copied.

## Requested verdict and stop

Request **APPROVE_CODE / REQUEST_CHANGES for this new exact Pair**: actual
Source/Transform ownership/overlap, original CFG/RNG semantics, two-Window
frontier/checkpoint protocol, bounded worker/IPC lifecycle and preserved strict
contracts. Do not treat this as completion of GPU performance or real Resume.

After candidate Child→Root publication/readback, Codex **STOP**. Next steps remain
GPT Code Gate → separately directed DS independent CPU → Owner-authorized
isolated real DCP/GPU validation → only then a separately authorized legal
checkpoint-boundary switch of the existing formal Job. No current Job stop,
identity/config/checkpoint change, fresh training, DS dispatch, canonical merge,
real GPU/model/data/DCP, evaluation or historical-evidence operation occurred.
