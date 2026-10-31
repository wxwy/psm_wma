# No-TTT verified async/lazy path — canonical-based isolated port

Owner continuation after the exact-pair Issue12 `APPROVE_PERFORMANCE` review at
V3 `2bcc27e94576837167cacd190af7dc837e6129cd`. Prepare code and targeted CPU
evidence for a NEW incremental Code Gate; do not update canonical branches or
restart training. Original12200 DCP remains the only proposed formal Resume
source; no A/B checkpoint promotion. Issue13 stays a separate output-only task.

## Exact source identities

- Current V3 Root baseline `2bcc27e94576837167cacd190af7dc837e6129cd`.
- Current Child baseline `0ae313e329d290fc6b8a50fda1112820fb7ac485`.
- Approved/performance-tested donor Root
  `fd9021b0908b4b2763b3d02508b1f34df377dc97`, Child
  `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`.
- New isolated Root/Child branch `v3-nottt-async-lazy-port-20261031`.

The formal review was actually read after a fresh V3 fetch and advertised SHA
check. It approves n18 steady Step Wall1.6116x from DS reported data, not a new
run by Codex. No repeat GPU A/B, no new interpretation of data/stall metrics.

## Necessary dependency closure discovered in current code

The current V3 Child still binds `NoTTTCpuLoader`, has no AsyncRecipe/AsyncLoader,
and lacks transform reconstruction metadata. Copying only the two Issue12
worker-source/recipe files would leave the approved path unused. Do not claim
integration based on their mere presence. The minimal executable closure is SIX
production files, ALL byte-identical to the already approved donor:

1. new trainer/no_ttt_async_loader.py (original Issue9 pipeline).
2. new trainer/no_ttt_async_recipe.py (including the approved lazy injection).
3. new trainer/no_ttt_worker_source.py (approved Issue12 reader).
4. matched_no_ttt.py (positive-worker binding and checkpoint-boundary guard).
5. utils/no_ttt_loader_profile.py (runtime-only async provenance/limits).
6. data/generator/action/datasets/robocasa_exact_window_cached_sft.py (constructor
   metadata retention for the same existing transform).

Copy only those explicit files and seven donor test/support paths (async loader,
recipe, trainer and worker-source tests, async support, two old CPU fixture
adjustments). No whole-commit cherry-pick/merge or donor Gitlink reset. All other
Child objects, especially EvalV2 inference/simulation/evaluation, model,
optimizer/DCP/Local algorithms and configs, must remain current-canonical exact
Git objects. Root launchers/configs/Issue13 output helper remain unchanged.

## Targeted integration acceptance

- Freeze an inventory of base/donor/selected blobs and entire outside-allowlist
  tree equality. Prove every ported file is an exact approved donor object.
- New Root integration sentries: actual MatchedNoTTT binding selects the new
  class at workers1/2/4/8, keeps workers0 synchronous, does not create workers at
  bind time; async identity remains runtime-only; protected EvalV2 objects and
  Root launchers unchanged, no Issue13 helper is pulled in.
- Selected donor CPU tests: official source payload/caption/padding at different
  file layouts, no eager worker build, bounded source cache, corrupt evidence,
  original RNG, real2-worker Source+Transform/CFG three-window path, T16/B8/GA4
  full/partial, CPU fullstate Resume and failure/cleanup at representative ranks.
  No full301 or previous58 replay; use new targeted selection on the new Pair.
- Scoped Ruff0.12.7 check/format/AST, clean exact Root/Child/Gitlink evidence,
  source fingerprints before/after, raw JUnit/log/commands and full narrow diff.
- Submit Child then Root only to isolated branches, remote readback, GPT fresh
  integration review and STOP. No GPU, real data/model/DCP access, DS dispatch,
  canonical promotion, change to current Job/Config/identity/checkpoint/history,
  Index8/Packed128 numeric comparison, performance retest or automatic Resume.
