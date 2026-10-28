# Evaluation V2 r1 — Stage1 design/prototype review handoff

2026-10-28 Asia/Shanghai. **Design Gate only. No production900-entry/Native rollout implementation or real evaluation authorization.**

| Identity | Exact SHA |
| --- | --- |
| Formal Design + isolated prototype Root | `dc750f8e258d10a33e7a195cf907926b1c98bd7f` |
| Unchanged Child / Root Gitlink | `746c5cf2f2324104a62fb71510343aa40d3976c5` |
| Development base V3 | `5c1d78cbaa9d4449a471ce587afe89375292dc27` |
| Candidate branch | `v3-eval-v2-design-20261028` |

Following evidence/docs HEAD is bookkeeping, not a new Design source. No V3 merge/Child change. Canonical design: `docs/build/PSM-WMA_V3_RoboCasa_Evaluation_V2_design_r1_2026-10-28.md`. Owner's new900 principles are recorded separately from proposed implementation defaults. Current431 is not input, acceptance dependency or migration target.

## Delivered now

New design + six isolated prototype/test files under `tools/v3/episode_eval_v2_prototype/`; production scripts/configs/vendor/entireChild have zero diff. Root design commit changes only these files and SESSION/TODO. Prototype is never imported by real launchers; schema/output always `prototype_only=true` and `runtime_gate_approved=false`.

Prototype tests environment predicate authority/first-success latch/horizon failure/Invalid, including strict predicate exceptions rather than false. Runtime/Local cleanup errors invalid, media errors diagnostic. Scientific outcomes and post-result process errors are separate; valid results never rewritten because a Worker later exits badly. Partial valid-only SR is explicitly conditional; full SR null when planned results include Invalid/Pending.

Flat immutable Task/Episode result commits, one coordinator lease, strict schema/checksum/source/seed/stream/reset-index validation, unique contiguous result index. Summaries/episodes.jsonl are rebuilt views, not admission authority. No automatic ffmpeg or videos_view. Missing/corrupt media does not affect outcomes, and media callbacks restore Python/NumPy/already-loaded Torch CPU global RNG; no CUDA initialization.

Proposed r1 Resume default: complete Task reused, incomplete/Invalid Task archived **by rename without MP4 copying** and whole Task rerun from the same literal Seed/new env/stream. Adjacent-generation restart journal recovers before/after move and before/after state publication. Stale/out-of-order/duplicate/post-Invalid results reject. Synthetic50-continuous-reset and reset-only replay counterexample explain why gap reseeding cannot pretend original scene continuity.

## Explicit design decisions/open limitations before Stage2

1. Task-level restart may repeat49 valid Episodes of an interrupted Task. This is the conservative proposed default, **not an Owner-approved per-Episode migration/seed protocol**. GPT/Owner must freeze that choice before real Native wiring.
2. Prototype process errors persist as clean-qualification blockers; no automatic execution-scope resolution/forgetting implemented. Even when all900 valid outcomes have numeric SR, a late process error blocks qualification. Stage2 needs an explicit reviewed error-resolution/clean-continuation policy; reopening summaries cannot erase faults.
3. Half-initialized Task state without its Episode directory explicitly blocks; no silent assumption that old data was empty. Stage2 must retain clear blocked/new-run handling or add reviewed safe initialization recovery.
4. Bounded media encoder/spool/cancel lifecycle, actual scene provenance, real policy RNG/Server lifecycle and native Local/ABI are design requirements, **not implemented by the CPU prototype**. Do not call this a ready-to-run900 framework.

Read-only actual-source audit found legacy `check_success` exceptions mapped toFalse and media error could override successful returns; final video save also precedes Local cleanup. Proposed opt-in Stage2 hooks/output adapter must fix these **only for V2**, preserving old defaults/predict/action/Local algorithms. No existing source was patched here and no old431 result was reassessed.

## Frozen author CPU Evidence

**65 passed,0failure/error/skip,9.15s**, three prototype test modules. Ruff0.12.7 check/format/syntax six Python files and six frozen/committed source SHA checks PASS. All tests new; no old suite rerun or inherited approval. One existing pynvml deprecation warning on CPU Torch import; no model/GPU execution.

-18fakeTasks×50 =900unique logical rows,450synthetic successes+450failures,SR0.5, per-task statistics/rebuilt indexes exact. **Not900 rollouts**, not RoboCasa model/physics results.
- Full/partial/Invalid/late-error classifications; illegal types/corrupted commitments/UTF8/oversize/symlinks/foreign old namespace; seed/config/model/runtime/source-plan identity; Missing/Pending files never complete.
- Restart four transaction fault points, bad journal path refusal, stale producer and exact no-copy MP4 inode preservation; read-only inspection and separate CPU lease contender; conservative partial initialization BLOCKED.
- One fake environment constructed for50literal-seed resets; stepping changes its private RNG, so reset-only skipping differs. Off/save/error media produces identical mock scene/action-draw/RNG/SR traces. This is a synthetic protocol witness, **not real RoboCasa RNG equality**.

Evidence `docs/collab/codex/evidence/2026-10-28_eval_v2_design_prototype_author_cpu/`: original final JUnit/log/commands/environment/source+Git blob SHA, static logs, protected-tree proof, exact patch, synthetic900 witness and actual test-generated new900 directory archive. Archive/examples retain design-only markers and omit Stage2 native action/prediction/Local/media writers; do not import them into production results. Prior59/63-case PASS iterations are preserved but not aggregated with65.

CPU reproduction from a clean detached exact Root/Child, outputs outside checkout:

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=<ROOT> HF_HOME=<CACHE>/hf MPLCONFIGDIR=<CACHE>/mpl XDG_CACHE_HOME=<CACHE> \
  <CPU_PYTHON> -m pytest --noconftest -c /dev/null --rootdir=<ROOT> -p no:cacheprovider \
  -q -s tools/v3/episode_eval_v2_prototype --junitxml=<NEW_EXTERNAL_DIRECTORY>/junit.xml
```

## Requested review / stop

Request **APPROVE (Design-only) / REQUEST_CHANGES / BLOCKED** for exact design/prototype pair above. Please decide restart granularity and conservative error/initialization dispositions explicitly; do not repeat Issue6/Compact implementation audits. After Design Gate, prepare separate production implementation pair + focused CPU/DS gate, separately authorized real Canary, then Owner fresh900 authorization. No real eval/server/GPU/Checkpoint/431 IO, no merge V3 and no automatic Stage2 execution. Codex STOP after candidate publication/readback under current Owner/GPT/DS roles.
