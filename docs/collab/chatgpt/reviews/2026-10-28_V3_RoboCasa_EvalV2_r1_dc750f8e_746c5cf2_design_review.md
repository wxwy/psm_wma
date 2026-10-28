# GPT independent Design Gate — RoboCasa Evaluation V2 r1 (2026-10-28)

## A. Scope, formal pair, verdict

- **Formal Design + isolated prototype Root**: `dc750f8e258d10a33e7a195cf907926b1c98bd7f`
- **Child/Gitlink**: `746c5cf2f2324104a62fb71510343aa40d3976c5` (unchanged)
- Base V3 at start: `5c1d78cbaa9d4449a471ce587afe89375292dc27`
- Candidate: `v3-eval-v2-design-20261028`; handoff/Evidence commit `23f2d3a1fda08b9c8214c22b12fbb0592c578dcd` is not formal design SHA.
- Canonical candidate: `docs/build/PSM-WMA_V3_RoboCasa_Evaluation_V2_design_r1_2026-10-28.md`.
- **Verdict: `REQUEST_CHANGES` (Design Gate, two unresolved failure-lifecycle design blockers).** This is not a negative finding on the scientific SR authority, media decoupling, or the conservative whole-Task restart choice, which are acceptable.

No V3/Child production edits, launcher, GPU, DCP, real simulator, training or previous431 Episode migration are in scope. The 900 records are *synthetic*.

## B. Independent evidence / exact source check

Directly fetched Root implementation diff against `5c1d78cb`: only `SESSION.md`, `TODO.md`, one new 116-line design doc, six `tools/v3/episode_eval_v2_prototype/` modules. No production `scripts/`, `configs/`, `cosmos-framework` or `third_party` modified.

Read original author `junit.xml` stored at `docs/collab/codex/evidence/2026-10-28_eval_v2_design_prototype_author_cpu/`: `tests=65, failures=0, errors=0, skipped=0, time=9.147s`, with per module `contract_test=32`, `scene_test=3`, `store_test=30`. Author static `ruff0.12.7 check/format`, syntax and `git diff --check` recorded PASS. Independent GitHub source Blob fetch checked **6/6** against `committed_source_binding.json`. Author's 18×50=900, 450 success +450 failure, SR0.5 is a synthetic store/index fixture, **not** robot rollouts or physics evidence. GPT did not rerun CPU pytest, inspect DS workstation or launch any real model/GPU.

### Contract -> observed prototype -> Gate

| Contract | Direct source | Result |
| --- | --- | --- |
| env `_check_success` first-success-latch1; horizon without success failure, predicate exception invalid | `contract.py:105-151`; `contract_test.py:57-102` | Design aligns; CPU mock covers typed bool and no reward-based success |
| Media-independent SR; no default ffmpeg, no default `videos_view` | `try_media:261-279`; `Store.summary:334-378`; `store_test.py:271-285` | Accept design principle; production media process isolation remains Stage2 |
| Exactly 18 Tasks×50, unique logical Task/Episode, SR numeric iff coverage complete | `contract.py:33-102`; `store.py:334-400` | Synthetic900 witness PASS; no actual Sim coverage |
| Single literal Task seed, one environment / 50 consecutive resets; interrupted Task restart whole Task | `scene_test.py:60-94`; `store.py:223-321` | **Recommend APPROVE this single choice**, with explicit GPU-cost caveat; gap-skipping cannot claim the same RNG stream |
| Atomic, exclusively leased result commits, no stale generation mixing | `store.py:122-161,227-322`; `store_test.py:90-175` | Synthetic lease, rename/fault boundaries, immutable result evidence supported |
| Process-error resolution / initial-claim crash recovery | `store.py:180-190,274-305,323-378` and design §5/§7 | **Open blockers D1,D2 below** |

## C. Actual blockers

### D1 — HIGH: Process errors are permanent unscoped qualification blockers

- **Where**: `tools/v3/episode_eval_v2_prototype/store.py:323-375`; `docs/build/PSM-WMA_V3_RoboCasa_Evaluation_V2_design_r1_2026-10-28.md` §5, §7. 
- **Root cause**: `record_process_error()` writes immutable `{task,stage,message}` without generation, stream, invocation/worker or final resolution identity. `summary()` unconditionally aggregates **all past errors** and sets `results_qualified = complete and not errors`; no close/recovery transition. `begin_task()` reuses an already-complete 50-Episode Task without clearing old unrelated errors. Even after an interrupted Task is wholly archived and rerun successfully, previous transient process failures permanently prevent a clean 900-Episode outcome.
- **Contract violated**: reliable explicit Resume → controlled new full Task stream → clean completed fresh900 (while retaining immutable error history), with process faults separated from scientific result. Current design only acknowledges this and postpones the disposition to Stage2, but does not define a consistent state machine.
- **Acceptance**: design a versioned **scoped and auditable** process-error lifecycle. Error binds to run/Task/generation/stream/execution attempt, records original error immutably; after verified ownership cleanup and a valid fresh full-Task restart, superseded old-generation errors remain history but cannot permanently disqualify clean active-generation results. Current-generation unresolved process faults remain visible and must block `qualified_clean`. Explicitly distinguish `scientific_sr` numeric from `clean_execution` and surface contaminated/failed generation counts. Do not silently delete fault records or mark a failed server cleanup as clean. Add tests for (a) previous error then successful full Task replacement yields qualified current generation, (b) current active error still blocks, (c) post-last-episode process error keeps numeric SR but remains unqualified, (d) cross-Task error isolation.

### D2 — MEDIUM: Initial Task claim has an unrecoverable crash gap

- **Where**: `tools/v3/episode_eval_v2_prototype/store.py:180-190,274-305`; `store_test.py:324-334`; design §7 (explicitly noted pending).
- **Root cause**: `begin_task()` writes `_internal/task_state/<Task>.json` **before** creating `tasks/<Task>/episodes/`. A crash between these operations leaves a valid published stream state pointing to a missing episodes directory. Subsequent `rows()` and `begin_task()` fail permanently even when **no Episode was ever committed**, forcing abandonment of the entire partly completed fresh900 Run. Existing test verifies only BLOCKED, not safe recovery.
- **Contract violated**: crash-safe Task startup and recoverable new900 without erasing other already-completed Tasks; the frozen goal includes reliable Resume/atomic state and no silent data loss.
- **Acceptance**: define and implement an idempotent **initial-claim transaction** (journal or creation order + atomic state publication), including crash at each boundary. Resume may safely finish creation if it can prove no Episode evidence existed, or conservatively archive only positively identified partial structures without overwriting. Any ambiguous prior data remains BLOCKED and auditable. Add failure injection before/after state publication and directory creation, restart preserving other Task results; no original data deletion.

## D. Accepted design decisions and implementation gates

1. **Recommend freezing Task-level restart for V2 r1**: a Task starts a fresh environment + Policy Server (including RNG lifecycle) at the original literal Seed and executes all 50 real reset/step cycles. Any incomplete/Invalid Task generation is archived and rerun from Episode0, with zero mixing of old successful Episodes. Existing fully valid Tasks reuse. This preserves sampling-protocol clarity without requiring impossible reset-only state replay; it **does not prove bitwise same scene/rollout on rerun**. Worst-case 49 repeated Episodes / Task (~hours). Owner should explicitly adopt this cost; no hidden seed changes or best-of-N repeated-run selection.
2. A distinct alternative of **fixed per-Episode independent scene seeds** could make Episode-level Resume efficient, but is a *new benchmark/sampler version* and must be evaluated consistently across all models, not silently injected into the original continuous-reset protocol.
3. V2 C requires no default ffmpeg video decode and no media-to-SR coupling. **Native Child currently raises media errors inside the rollout**; production opt-in hooks must separate or bound media without changing action/path/RNG. The prototype's Python/NumPy/Torch CPU RNG restore is not real CUDA/RoboCasa equivalence. Stage2 must explicitly validate native `env.step→_check_success` and Local-TTT beginning/end/ack/cleanup chronology, not merely fake environment tests.
4. Stage2 must specify actionable execution vs reporting timeouts and worker recovery, so 50-Episode Tasks are not endlessly re-run because prior 3-hour wall budget includes media/CPU postchecks. No background/unchecked infinite retries; per-attempt errors logged and bounded, GPU7 EGL status independent.
5. Retain process cleanup/port ownership, root/child/experiment config source identity, immutable Episode commits, run-private log/plan, canonical public `tasks/<Task>/episodes/ep_NNN`; no legacy431 import or scripts that touch old results. `summary.json` and `episodes.jsonl` are derivative views, not admission authority.
6. A revised **new formal design/prototype SHA** requires fresh incremental review against D1/D2 only. Stage1 accepted CPU tests remain author Evidence, not DS independent or real GPU. After design closes, implementation/DS independent CPU/real small Canary need separate gates.

**Persistence rule**: this detailed review becomes formal only after the canonical `docs/collab/chatgpt/CODEX_INBOX.md` append-only entry is successfully published and verified. Do not merge the candidate or launch real900.
