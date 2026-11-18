# Issue68 R1 narrow peer review

Formal Root: `87dd1bd8599003e2f6ea4d2b069c249d06d865e8`.
Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.

**REQUEST_CHANGES: all three original findings closed; two additional P1
coordinator/GC boundary defects independently reproduced.** This is local
read-only code/CPU review, not GPT server acceptance or a real GPU verdict.
The author's subsequent uncommitted R2 fixes are not covered by this report.
No product, old test or original evidence file was edited by this peer.

## Original findings: CLOSED

1. **Capacity cycle:** the original genuine B32-complete/3-pending state is
   still legitimate temporary queue backpressure, but now the real parent
   Engine loop detects sustained capacity pressure and exits with an explicit
   capacity error. The independent probe used an accelerated clock, preserved
   all35 source PNGs and32 persisted numeric files, and published no COMPLETE.
   Observed wall time0.54s. The configured production bound remains the existing
   worker timeout, not silently enlarged capacity or resized membership.
2. **Task mkdir race:** a new task directory without episodes is skipped;
   an existing non-directory episodes path is rejected. Direct probe passed.
3. **Direct-root selection:** a fully valid published NavigateKitchen/0 source
   is excluded for a different task or episode999 and accepted for its actual
   task/episode. Direct probe passed.

See `probe.py`, `probe.log` and `observed.json`. Related queue/engine regression
tests independently passed **25/25**,0fail/error/skip,35.93s (`pytest.log/xml`).
The original612 tests and their assertions were not modified by R1; only
Issue68's two new test modules were extended.

The real-evidence caution is also addressed: the classifier requires actual
native-called rows, positive CUDA timing, two physical GPUs and overlapping
encode API intervals. Independent **synthetic classifier-only** inputs reject
an ACK-only second card and nonoverlap. Accepted overlap explicitly says it
includes cold load/preprocessing and is not a CUDA kernel timeline. These
synthetic rows are not, and must never be cited as, actual GPU evidence.

## New P1: registered-but-not-offered Episode never resumes

`g2/latent_cache/batch_engine.py:321–331` only recovers done jobs;
lines383–391 skip every known target during discovery. An independent-mode
coordinator crash between durable `register()` and `offer_source()` leaves a
valid published Episode with `done=0,source_ready=NULL,sealed=NULL,error=NULL`.
On restart, discovery skips it, `_finish_jobs()` ignores it, and no event is
ever admitted. The active job suppresses idle; the new capacity watchdog sees
no pending members and therefore cannot bound this distinct wait.

`coordinator_probe.py` creates a fully valid published View-only fixture. A
real spawned child executes the public `register()` and then `os._exit(77)`.
Fresh `BatchEngine(resume=True)` recovery followed by three ordinary discovery,
finish and collection cycles leaves exactly the state above,0events,0batches,
active jobs1, no capacity pressure and no cache publication. Busy idle remains
false even at a large virtual time. No fake ACK/source was installed.

Evidence: `coordinator_observed.json`, `coordinator_probe.log`.

Minimum repair: revalidate and re-offer the same published source/scope for
independent unfinished registered rows lacking source-ready during recovery.
Leave sync's legitimate still-producing rows untouched; source/profile/episode
conflicts must fail closed. Release coordinator leases even if that startup
validation fails.

## New P1: legacy pixel sharing prevents distinct batch-chunk GC

`g2/latent_cache/streaming.py:773–784` retains the old B1 heuristic that a
pending event with the same `pixel_record_key` shares a numeric file. In the
new batch format, those events have different `records/<batch>/<position>.pt`
paths and cannot share that file. Consequently an archived job can leave its
own chunk behind, and `batch_queue.py:450–454` then fatally rejects the
nonempty completed-batch directory. Repeating/resuming reaches the same
condition. Identical static View images across episodes are valid input.

`gc_probe.py` performs genuine source packaging, five CPU-fixture numerical
writes/fsync/ACKs, full cache assembly/verification and an actual completed-job
tombstone. It then keeps a second legitimate producing job pending with the
same floor image bytes but a different Episode/event/record path. Episode A
fully publishes and archives, yet one A numeric chunk remains. Collection
raises `completed batch still has unverified numeric staging`. No source or
cache verifier was patched; no completed rows/ACKs were simulated. Critical
streaming and queue source bytes were compared with formal87dd before running.

Evidence: `gc_observed.json`, `gc_probe.log`.

Minimum repair: in the batch recipe only, remove the pending pixel-key sharing
heuristic; preserve genuine same-result ownership protection and all legacy B1
behavior. Test identical-image cross-episode pending work using real cache and
tombstone verification, rather than a monkeypatched proof.

## Boundary review and limits

The surrounding enqueue/refill/seal, cache-publication-before-done, reap
unlink-before-archive and atomic batch/member SQL collection windows were
reviewed. No further P1/P2 defect was established in this pass. Legacy B1
loader, batch math/recipe contract and PR67 retirement/Gitlink files are
unchanged by R1. This review does not extend the earlier real B1 or A math
approval to final dual production Gates.

Workdir `/workspace/psm_wma_issue52`; existing CPU interpreter only. Exact
probe commands use `PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''` and
`PYTHONPATH=/workspace/psm_wma_issue52:/workspace/psm_wma_issue52/cosmos-framework`:

```bash
/workspace/.venvs/g2-view-vae-52/bin/python docs/collab/codex/evidence/2026-11-18_issue68/peer/r1/probe.py
/workspace/.venvs/g2-view-vae-52/bin/python docs/collab/codex/evidence/2026-11-18_issue68/peer/r1/coordinator_probe.py
/workspace/.venvs/g2-view-vae-52/bin/python docs/collab/codex/evidence/2026-11-18_issue68/peer/r1/gc_probe.py
/workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider \
  g2/tests/test_batch_queue.py g2/tests/test_batch_engine.py \
  --junitxml=docs/collab/codex/evidence/2026-11-18_issue68/peer/r1/pytest.xml
```

All commands exited0: the two new probes intentionally reproduce defects,
not successful product recovery. No GPU, server, private data, network,
installation, production deletion or implementation mutation occurred.
