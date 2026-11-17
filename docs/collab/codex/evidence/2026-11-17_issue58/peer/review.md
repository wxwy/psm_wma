# Issue58 local read-only peer review

Reviewed Root `3b13e6a5e511bd2cae448f3c6f40233b88a99413`, Child/Gitlink
`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`; parent base29f9993d.
Local technical verdict: **REQUEST_CHANGES**. This is not GPT independent
server acceptance. Reviewer changed no product/test/ledger/ref files and used
only the existing CPU interpreter, synthetic inputs and own peer evidence.
No server/private data/network/install/native/Wan/GPU/full production/merge.

## P1: prepared plan is handed to the executor in plan-only mode

`g2/offline/full_production.py:558` constructs `producer_args(cfg,"plan")`.
`prepare_plan()` returns the same object at583. `run()` passes it to
`Supervisor.execute()` at913; that calls the original `schedule(args)` at770.
The original scheduler returns from its `args.action=="plan"` branch before
worker dispatch. On a fresh ordinary run this means zero renderers, then the
final audit fails with `queue drained without all strict episode COMPLETE`.
Resume also fails to dispatch missing episodes. This blocks the official
one-shot entrypoint even though the direct original queue test passes.

Direct CPU probe `test_review_dispatch.py` calls the actual unmodified
`prepare_plan()` and original `schedule()`. Only source discovery/plan inputs,
completion state and native worker are simulated; it does not replace the
adapter or scheduler. Observed `prepared_action="plan"`, selected1,
worker_calls0; it printed the original PLAN event twice. The required run-mode
assertion failed. Ensure the returned execution args also have manual-start /
allow-experimental flags; merely assigning action without those flags will
still fail the original scheduler guard. Returning a fresh run-mode args
object while retaining the validated immutable plan is a minimal solution.

The current author child-consumer integration test replaces prepare_plan()
with `producer_args(cfg)` (default run action), hiding this wiring defect.
Add coverage using the real prepare_plan adapter through the dispatch path;
mock native/VAE computation/resources rather than that adapter.

## Execution and observations

Working directory `/workspace/psm_wma_issue52`; existing Python
`/workspace/.venvs/g2-view-vae-52/bin/python`. Environment:
CUDA_VISIBLE_DEVICES empty, PYTHONDONTWRITEBYTECODE1, COSMOS_DEVICEcpu,
PYTHONPATH selected Root/cosmos-framework + Root. CPU synthetic only.

Exact first command (initial probe retained as initial_dispatch_probe.txt):

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 COSMOS_DEVICE=cpu \
PYTHONPATH="$PWD/cosmos-framework:$PWD" \
/workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider \
g2/tests/test_one_shot_*.py \
docs/collab/codex/evidence/2026-11-17_issue58/peer/test_review_dispatch.py \
--junitxml=docs/collab/codex/evidence/2026-11-17_issue58/peer/review.xml \
> docs/collab/codex/evidence/2026-11-17_issue58/peer/review.log 2>&1
```

Observed exit1:22 new author cases PASS,1 independent probe FAIL,39.37s.
These22 overlap author totals and must not be added to487. The probe's fake
worker return handling was then made runnable after a correction; its initial
text and raw result were preserved. Final probe was separately rerun:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 COSMOS_DEVICE=cpu \
PYTHONPATH="$PWD/cosmos-framework:$PWD" \
/workspace/.venvs/g2-view-vae-52/bin/python -m pytest -q -p no:cacheprovider \
docs/collab/codex/evidence/2026-11-17_issue58/peer/test_review_dispatch.py \
--junitxml=docs/collab/codex/evidence/2026-11-17_issue58/peer/dispatch_red.xml \
> docs/collab/codex/evidence/2026-11-17_issue58/peer/dispatch_red.log 2>&1
```

Observed exit1:1 expected RED,3.09s. Final probe SHA256
`0fcb570fc6b34a2d7ea6a1e019c4be2f99adb91498b6f2ce2966d466b974f788`.
dispatch_observed.json records the actual action and zero worker calls.
No product changes relative to exact Root at review completion.

## Remaining scope

No other reproducible P1/P2 found in the reviewed archive/lease/GC and process
ownership paths. Existing new tests independently cover their stated CPU
contracts. This is not proof of actual GPU throughput or server asset behavior.
An explicit output-disk admission reserve and an open ViewReader held across
GC would be useful hardening/coverage; they are not additional confirmed
blocking defects in this review. Real F27/Wan sample, resource A/B/full32-slot
layout and Owner manual start remain separate GPT gates. P1 microbatch stays
deferred. Please correct the entrypoint in a new fixed SHA and rerun this final
probe unchanged for narrow closure.
