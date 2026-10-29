# No-TTT asynchronous preparation: Stage / Owner / RNG plan

Task `V3-NOTTT-ASYNC-OVERLAP-NWPOS-20261029`, Issue #9. Owner authorization is
isolated implementation and synthetic CPU evidence only. Baseline Root
`3d5806a2b702b42d3f24e7645aa7cec9cd70b0c7`, Child/Gitlink
`746c5cf2f2324104a62fb71510343aa40d3976c5`.

| Stage | Owner | RNG / frontier contract |
| --- | --- | --- |
| Preview current + next Window | Trainer | Pure planner over committed/candidate frontier; never promotes speculative data |
| Source / Cache / full deterministic Transform | Spawned CPU DataLoader workers | Local offline readers and bounded mmap; no CUDA/model/optimizer; no global training RNG |
| Conditional + empty-caption token preparation | Same workers | Exact existing JSON ActionTransformPipeline; no stochastic choice yet |
| Ordered consumption and CFG choice | Trainer | Original `random.random()` at each original consumer position; no reseeding, no advance from prefetch |
| Pack / Collate / H2D / native compute | Trainer | Existing native outer loss and GA normalization; workers prepare later Members/Window concurrently |
| Optimizer / Frontier commit | Trainer | Only after all GA backward and successful optimizer; speculative plan must match actual predecessor |
| Checkpoint | Trainer | Original rank frontier schema; speculative packages excluded; no RNG changes in checkpoint callback |
| Failure / cancel | Trainer | Discard all unconsumed packages, bounded reap owned workers; never silently switch to synchronous execution |

The actual cached SFT JSON configuration has one stochastic operation per
consumer: CFG caption dropout. JSON formatting disables the separate idle-text
augmentor. The worker prepares the conditioned payload and the same processor's
empty-caption tokens. Main-process selection changes exactly the caption and
token fields which the original tokenizer changes. This preserves arbitrary
model/callback Python, NumPy and Torch RNG draws between Members without trying
to predict future RNG states. Unknown transforms/configurations fail closed.
The explicitly injected legacy synthetic raw recipe remains a regression seam,
not the production async implementation.

Bounded ownership: one active Window and one next-window preview; DataLoader's
worker/prefetch credits bound transported segment packages. Recipe metadata and
encoded packets have explicit byte caps; the original per-worker mmap cap is
retained (rank cap = workers × that cap, at most eight mapped Episodes/rank),
so nw8 does not newly reject valid Episodes by shrinking the per-file bound.
Parent consumption retains only the current Member plus bounded
DataLoader results. At optimizer completion the consumed plan is released before
another preview is admitted. No new fields enter training identity or frontier.

Planned files: Child `trainer/no_ttt_async_recipe.py`,
`trainer/no_ttt_async_loader.py`, `trainer/matched_no_ttt.py`, necessary
`trainer/no_ttt_cpu_loader.py` factory/seams, adjacent synthetic tests,
`utils/no_ttt_loader_profile.py`, and cached-SFT builder recipe metadata. Root
adds an exact-pair CPU gate, this plan, evidence/handoff and ledger entries.
No generic Trainer, DCP, RNG restoration, Local-TTT, model, optimizer, launcher
defaults, active Job or historical results are changed.

CPU evidence will compare workers 0/1/2/4/8, four ranks, GA4, partial/full and
three consecutive Windows; real Source/Transform intervals must overlap a fake
compute interval for both a later Member and next Window. Real GPU overlap,
throughput and real DCP Resume are NOT validated by synthetic CPU tests.
