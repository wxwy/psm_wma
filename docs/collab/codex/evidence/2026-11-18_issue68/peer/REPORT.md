# Issue68 local read-only peer review

Formal Root: `29e4623e1875a2363a46ce210e2543aa1e08bffb`.
Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.
Scope: implementation code review and separate CPU probes. This is not GPT
independent server acceptance, a GPU Gate, corpus approval or merge approval.

Verdict on this formal code: **REQUEST_CHANGES**, one P1 and two P2 findings.
The author is addressing them in a new candidate; that later candidate is not
covered by this verdict. No implementation or old test/evidence file was edited
by the peer. Only this peer directory was written.

## P1: numeric capacity can create an endless circular wait

`g2/latent_cache/batch_queue.py:138–141`, with completion and GC conditions at
lines300–324 and424–430; `batch_engine.py:618–625` suppresses idle while a job
exists. When the next immutable batch cannot fit, `claim()` just returns None.
If earlier complete batches belong to the same unfinished episode, those
reservations cannot be collected until that episode is finalized. It cannot
be finalized until the remaining records are encoded. No worker is running,
no job is failed, all future claims return None, and the active job disables
the idle timer forever. Worker timeout does not apply to an unclaimed batch.

Independent reproduction in `probes.py`, with a valid finite configured
`max_result_bytes=3505536` set at spool construction (no config mutation):

- Admit35 actual PNG events through the existing EventSpool API.
- Claim a B32, perform actual CPU-fixture numeric writes/fsync/ACK and complete.
- The B32 reservation occupies the budget; three unassigned members remain.
- Three subsequent claims return None; `finalizable(job)` is false.
- SQL states: `complete=1`, pending members3, no running/ready/failed batch,
  active jobs1, acked32/pending3, failed jobs0.

See `observed.json` and `probes.log`. A bounded explicit capacity failure with
source/results retained is sufficient; do not silently expand the budget or
resize an already assigned numerical batch. Allow genuine source-ready/GC or
running-worker progress before declaring a stall.

## P2: a newly visible task directory aborts continuous discovery

`g2/latent_cache/batch_engine.py:66` assumes every entry under tasks already
has an episodes directory. Ordinary parent-first mkdir exposes a brief legal
state `tasks/NewTask/` before `tasks/NewTask/episodes/`. `discover_published()`
raises `CacheError: cache path is missing: NewTask/episodes`, terminating the
watcher instead of ignoring unpublished state. This contradicts the continuous
publication contract and the runbook's explicit assertion about task folders.

The direct independent probe creates only that incomplete task directory;
`observed.json` records the actual exception. Missing intermediate production
directories should be skipped; symlink or existing non-directory paths should
still be rejected. Add coverage before episodes exists, not only an episode
directory whose manifest is partially written.

## P2: direct episode roots ignore explicit task/episode selection

`g2/latent_cache/batch_engine.py:56–57` returns a direct root with COMPLETE
before applying the task and episode selectors. For a fully valid published
NavigateKitchen/0 fixture, both calls return that episode:

```python
discover_published(episode_root, tasks=["DifferentTask"])
discover_published(episode_root, episodes=[999])
```

This can encode an explicitly excluded episode and differs from the legacy
scanner's direct-root filtering. `scope_probe.py` executes the exact formal29
function AST, so this result does not accidentally review the author's later
uncommitted repair. `scope_observed.json` and `scope_probe.fixed.log` record the
two results. The first probe's missing Python relative-import context was a
peer harness setup error, retained in `scope_probe.log`; only its module globals
were corrected, and no product logic or assertions were changed.

Apply selectors using the direct root's authoritative manifest identity before
admission. The normal strict profile/source validation still follows.

## Real-Gate evidence caution

`engine_metrics.gpu` counts the card completing/ACKing a batch, including an
all-files-reused replay where `native_called=false`. Therefore the real Gate's
`len(engine["batch"]["gpu"]) >= 2` condition alone cannot prove two GPUs
actually encoded. Use distinct physical GPU records with `native_called=true`
or the durable native-start/completion attempt audit, and overlapping execution
intervals when reporting parallel encoding. This is an evidence requirement;
the peer did not inspect or invalidate the separate real A math probe.

## Other reviewed behavior

The implementation uses one native BCTHW call, preserves the full FP32 spatial
grid, distinguishes the new numerical recipe, pins ordered membership and
fences ACKs. Partial replay compares existing numeric values before publishing
missing members. Whole-batch replay inputs remain until durable completion.
The reader's batch metadata validator is JSON-only. Sync and independent
entrypoints both call the shared engine and preserve distinct completion and
retirement lifecycles. No other P1/P2 issue was established in this review.

Read-only Git comparison confirmed no changes from the PR67 baseline to:
legacy `encoding.py`, original producer/episode, `final_source.py`,
`source_retirement.py`, `posthoc.py`, or Cosmos Gitlink. The peer did not rerun
the author's whole646 suite, nor reinterpret its CPU fixture results as GPU
acceptance.

## Executed peer commands

Workdir `/workspace/psm_wma_issue52`; no network, installation, new environment,
GPU, server or dataset production access. Existing local CPU interpreter:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' \
PYTHONPATH=/workspace/psm_wma_issue52:/workspace/psm_wma_issue52/cosmos-framework \
/workspace/.venvs/g2-view-vae-52/bin/python \
docs/collab/codex/evidence/2026-11-18_issue68/peer/probes.py

PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' \
PYTHONPATH=/workspace/psm_wma_issue52:/workspace/psm_wma_issue52/cosmos-framework \
/workspace/.venvs/g2-view-vae-52/bin/python \
docs/collab/codex/evidence/2026-11-18_issue68/peer/scope_probe.py
```

Both final probe commands exited0 and reproduced the findings, not product
acceptance. Fresh fixed-source review is required to close them. Both real
mandatory E2Es and all9126 production remain outside this peer's evidence.
