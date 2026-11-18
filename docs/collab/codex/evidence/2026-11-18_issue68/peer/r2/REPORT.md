# Issue68 R2 final narrow peer closure

Formal Root: `778022c8fcf431fa16e83a67256ba58b4b464052`.
Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.

**LOCAL_CODE_REVIEW_PASS.** Both P1 findings from the87dd review are closed;
the three earlier findings remain closed. No remaining P1/P2 issue was
established in the reviewed local code/CPU scope. This verdict does not certify
the two mandatory real GPU/F27 Gates, full9126 production, deployment or merge.
No original report, counterexample, product or historical test file was edited.

## Independently executed closure

`probe.py` uses actual public source/queue/cache APIs, real spawned process
exits and the explicitly marked CPU-only encoder fixture. Critical implementation
source bytes were compared to formal778022 before the probe. No verifier,
completed receipt or numeric ACK was faked or monkeypatched.

- **Register-before-offer crash:** a child executes durable `register()` and
  immediately `os._exit(77)`. A new `BatchEngine(resume=True).run()` now offers
  the verified published source, encodes all5 owners, publishes the cache,
  creates the genuine completed receipt and finishes with0active jobs/events.
  Every original View-first product/source file remains byte-identical.
- **Conflicting source:** a registered different source fingerprint is rejected
  by the existing source verifier. No cache is completed, all original files
  remain unchanged, and the target coordinator lock can immediately be
  reacquired after the startup failure.
- **Sync still producing:** recovery leaves a legitimate sync row with no
  published source unoffered; the independent-only repair does not read or
  prematurely certify it.
- **Equal-pixel GC:** two complete published Episodes deliberately share actual
  PNG bytes. Episode A's B5 is assigned first while Episode B's5 events remain
  pending. A's genuine cache and tombstone publish and its batch directory is
  removed successfully. B then completes its own distinct B5 and tombstone.
  Both verify5records, preserve all original source files, and leave0active
  jobs/events/batch rows/numeric PT staging. The former pending-pixel-key
  heuristic no longer pins an unrelated batch path.
- **ACK-only telemetry:** a real child writes/fsyncs a B1-tail numeric file and
  exits77 before ACK. Another worker reclaims that immutable context and reuses
  the file with0encoder calls. Its completion counters show1record but
  `native_batches=0`, `native_records=0`, `native_cuda_ms=0`; its result states
  `native_called=false`. This is CPU-only telemetry verification, not evidence
  that either named physical GPU was used.

Raw results: `probe.log` and `observed.json`. The grouped probes are separate
from the pytest count and must not be added as disjoint regression cases.

## Independent related regression

Queue and Engine tests: **29/29 PASS**,0fail/error/skip,39.81s. Raw output and
JUnit: `pytest.log`, `pytest.xml`. Read-only `git diff` confirmed the executed
g2/tools sources still match the fixed formal tree after the run. The peer did
not rerun all655 tests or reinterpret the author's server results as its own.

Narrow code inspection confirmed:

- The pending source re-offer uses the original verifier and applies only to
  unfinished independent jobs with no source-ready binding.
- Startup recovery/spawn now sits inside the existing `try/finally`, releasing
  leases/owned workers on failure.
- The pixel-key-sharing exclusion is batch-schema-only; the actual same-result
  ownership check and legacy B1 behavior remain in place.
- Legacy B1 loader, batch numerical adapter/recipe, PR67 retirement core and
  Cosmos Gitlink are unchanged in87dd..778022. New native telemetry describes
  completed-call work accurately; attempt audits retain separate history.

## Exact commands and boundaries

Workdir `/workspace/psm_wma_issue52`; existing local CPU environment only:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' \
PYTHONPATH=/workspace/psm_wma_issue52:/workspace/psm_wma_issue52/cosmos-framework \
/workspace/.venvs/g2-view-vae-52/bin/python \
docs/collab/codex/evidence/2026-11-18_issue68/peer/r2/probe.py

PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' \
/workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider \
g2/tests/test_batch_queue.py g2/tests/test_batch_engine.py \
--junitxml=docs/collab/codex/evidence/2026-11-18_issue68/peer/r2/pytest.xml
```

Both commands exited0. No GPU, server, private source/data, network access,
installation, production cleanup or product change occurred in this review.
The author's final real dual-chain evidence and GPT independent acceptance are
separate gates; this local PASS does not mark Issue68 DONE.
