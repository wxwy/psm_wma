# Fixed-source local peer review — View-first posthoc retirement

2026-11-18 CST. Verdict: **LOCAL_CODE_REVIEW_PASS**.

- Formal Root: `5c7ea400035e2727a2dae1d63dfe7d21b14b9ff2`.
- Child/Gitlink: `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`.
- Base: `b6311222c364543787f913215bf584065aa1c275`.
- Reviewer: `/root/view_first_retirement_peer`, different from the code author.
- Scope: repository code/source contracts, CPU synthetic probes and retained
  evidence. No server/GPU/Wan/native/full production, merge or private-data
  access was performed by this reviewer. This is not independent GPT real
  Gate approval or a release of9,126-episode VAE/retirement.

## Findings

No scoped P1/P2 finding identified. No production/test code was edited.

The new adapters preserve the intended dependency order. Working-source
access verifies the typed transport receipt, bounded exact raw/gzip bytes,
original source/readiness identity and explicit working schema. Final-source
dispatch materializes only the published compact views/projections and
existing product/state indices; it does not recreate the removed full audit.

The posthoc lifecycle is explicit in the existing spool, source binding and
CLI. Its consumer waits for cache completion rather than treating the already
published View-only COMPLETE as VAE success. It uses the existing B1/T1
numeric core, fsynced chunks/ACK, bounded refill, per-View writer, duplicate
protection and recipe checks. Stage B preserves the original spatial profile,
product states and completion files.

Stage C accepts a genuinely verified complete cache handoff. A C-only spool
does not invent streaming events or ACKs. The original collector's SQL-bound
intent, journal, target/cache locks, reader/writer leases, atomic writes,
fsync and scoped rename/unlink are reused. The dynamic retired inventory is
bound to the authenticated raw or gzip transport. The final reader checks
the proof/cleanup/historical hashes against the immutable capsule, retains
owner/recipe/projection/product bindings and does not depend on full JSON.

The posthoc receipt is separate from the original `view_vae=false` profile.
Recovery reaches the owned pending transaction before ordinary manifest
validation/discovery, which is necessary after multi-file index publication
or source deletion. Capacity bounds fail closed instead of truncating data.
The old raw JSON mode, default scanner refusal and old producer/encoder/core
code and tests remain unchanged.

## Independent CPU checks

Exact command, working directory `/workspace/psm_wma_issue52`:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0 \
PYTHONPATH="$PWD:$PWD/cosmos-framework" \
/workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q \
  -p no:cacheprovider --tb=short \
  docs/collab/codex/evidence/2026-11-18_view_first_retirement/peer/test_peer_adversarial.py \
  --junitxml=docs/collab/codex/evidence/2026-11-18_view_first_retirement/peer/pytest.xml \
  > docs/collab/codex/evidence/2026-11-18_view_first_retirement/peer/pytest.log 2>&1
```

Result: **4 PASS,0 FAIL/ERROR,0 SKIP;7.39s**. Temporary synthetic artifacts
and FakeEncoder only, no weights/network/install/new environment. These four
checks overlap the feature contracts and are not added to the author's599.

1. A self-consistently rehashed but wrong gzip receipt source ID after cache
   publication is rejected; full gzip stays and no compact index is published.
2. A damaged numeric payload after cache publication is rejected with gzip
   retained and no compact index/full-JSON workaround.
3. After valid retirement, changing the historical gzip hash and recomputing
   the outer retirement-receipt completion hash still fails the final reader's
   immutable capsule provenance checks.
4. Two actual concurrent processes are mutually excluded or observe completed
   state, then a public retry converges. PT bytes stay unchanged, the compact
   reader succeeds, the C spool has zero fake events and one completed job.

`identity.json` independently records the formal changed Git blobs, confirms
the tested working product files match them, and checks every baseline test
source file plus the protected encoder/core/producer files against fixed Git
trees. `pytest.log`, `pytest.xml` and the probe source preserve raw evidence.

## Limits and remaining Gates

The author's full XML/logs report599 PASS/13 inherited optional-dependency
SKIP, original560 identities and52 new cases. This reviewer did not rerun the
entire612-case suite. The first full-run old supervisor25s drain timeout is
preserved; unchanged focused and complete reruns passed. Its cause remains
unestablished, so original-server-environment regression and live resource
evidence remain useful. No old timeout/assertion was relaxed.

Real Gates A–D must still use fixed source, the existing PSM environment and
isolated on-server copies. Actual Wan parity/throughput, real final-source
consumer behavior/recovery and physical gzip-to-index storage changes cannot
be inferred from these CPU fixtures or the previous lifecycle's approvals.
The running View producer, raw data and production outputs must remain intact.
