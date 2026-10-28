# PSM-WMA V3 RoboCasa Evaluation V2 — r1 design candidate

Date: 2026-10-28 Asia/Shanghai. **Stage1: design + isolated CPU prototype, not a production implementation, launch authorization or Benchmark PASS.** New Owner scope: next fresh18Task×50Episode only. Existing431 episodes are neither an input nor a dependency; no migration, conversion, repair, renaming, deletion or import is proposed.

Baseline Root `5c1d78cbaa9d4449a471ce587afe89375292dc27`; Child/Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`. Candidate branch `v3-eval-v2-design-20261028`. User roles remain Owner final authority, GPT design/review, Codex code/CPU, DS_PRO independent execution. Prior Issue6/Compact approvals do not authorize this new framework. This document separates Owner principles from proposed defaults needing this new Design Gate.

## 1. Owner principles and invariants

1. Success/failure authority is RoboCasa `env._check_success()` with unchanged per-completed-action observation timing and first-success latch1. Inference/environment/runtime errors are **Invalid**, never policy failure or silently excluded.
2. Environment MP4, model-generated MP4 and init PNG are diagnostic only. Missing, truncated, undecodable or failed media cannot determine success/failure/Invalid. No automatic ffmpeg strict decode at finalization, no default videos_view copy.
3. Public layout is Task→Episode, with one original copy of media. Model inference/raw15→canonical raw15→env12, state15/H16/17frames/20fps/left_wrist, Local-TTT algorithm and environment configuration stay unchanged.
4. Execution/progress/recovery/logs are distinct from scientific outcomes. Keep reliable locks, identity, atomic commits, unique logical episodes, failure cleanup and explicit sampling provenance.
5. Fixed fresh900 namespace. No legacy checkpoint/Episode bridge, source catalog, Invocation/Batch/Attempt result hierarchy or compatibility import. Old framework/431 and all training/checkpoints remain intact.

## 2. Current source facts motivating the new interface

At pinned Child, `cosmos_framework/simulation/robocasa/closed_loop_eval.py:216` wraps `_check_success` and returns False on any Exception. This hides predicate errors as ordinary non-success. Its `run_policy` records action/Local evidence before success checks, which is the timing to retain. However generated-video decoding/saving is inside the control loop and may raise; final media error is raised even after a successful return, while Local reset follows video saving. `cosmos_framework/utils/rollout_evidence.py:run_recorded_episode` converts any raised exception to policyFalse/runtime_error; this loses the distinction between already observed environment success and diagnostic media failure.

This is a read-only source audit, **not a change to legacy production**. V2 needs a narrow explicit opt-in observation/output contract; merely removing Root ffmpeg validation cannot fix these earlier failure paths. No evidence here establishes RoboCasa model/physics correctness or current431 outcomes.

## 3. Proposed public and internal layout

```text
<NEW_RUN>/
  manifest.json
  summary.json
  episodes.jsonl
  tasks/<Task>/
    summary.json
    episodes/ep_000/
      result.json
      actions.jsonl
      predictions.jsonl
      local_memory.json
      scene_provenance.json
      media/
        status.json
        rollout.mp4
        generated/replan_0000.mp4
  logs/gpu4.log
  _internal/
    .run.lock
    execution_plan.json
    progress.json
    resume_state.json
    verification_cache.json
    task_state/<Task>.json
    restart_pending/<Task>.json
    abandoned/<Task>/generation_<N>_<stream_id>/ep_000/...
    process_errors/<event_id>.json
```

`abandoned/` is explicit diagnostic retention for interrupted V2 task streams, not history migration. Files move by same-filesystem rename; no second video copy. Public tasks/episodes always show only the selected current Task generation. `_internal` is not required for ordinary analysis. No manifest/input may overlap output; Fresh requires a nonexistent namespace, even an empty old directory is refused. Canary and formal900 have distinct immutable manifests and cannot Resume into one another.

## 4. Identity and authority

Production manifest freezes full model identity (official accepted SHA/path/num_steps/action_horizon/guidance), Config SHA, Root/Child/Gitlink, runtime/vendor/physics protocol, separate dataset-generation metadata, per-task metadata SHA and authoritative horizons, exact18task set,50episodes, literal Seed, success latch and sampling/resume protocol versions. This new fixed experiment may use stricter identity than the old flexible four-parameter historical reuse; there is no compatibility promise with it.

GPU IDs/worker placement/log verbosity/media save mode are runtime options, not changes to model forward/RNG or scientific input. Input guards remain before load, after `/info`, before result publication and at finalization. Existing checked `/info`, checkpoint normalization, port availability/listener ownership and runtime probe are retained through small reviewed helpers. Issue6's approved pure model-hash/stat cache functions may be adapted to `_internal/verification_cache.json`; do not import legacy RunStore/history admission. Same trusted-readonly/stat boundary applies, no forged stat-derived model SHA. Actual adaptation is Stage2, not implemented by this prototype.

`result.json` is the terminal scientific authority. Flat fields include manifest digest, Task/logical Episode, Task generation/scene-stream ID, literal Seed/reset index, actual model prompt, environment success observations, outcome, termination reason, steps/replans/duration, runtime error and Local reset outcome. Atomic file carries a checksum for accidental corruption (not malicious resealing). A missing result is Pending; no amount of logs, progress, MP4 or convenience summary proves it completed. Actions/predictions retain existing raw15/canonical/env12 and Local evidence, but do not undergo repeated full historical rescans just to recompute SR.

The prototype schema is **`psm_eval_v2_design_prototype_v1` with `prototype_only=true`** everywhere. It cannot produce a production manifest or certify a real run. The real integration must introduce a separately reviewed production schema and observed runtime provenance.

## 5. Outcomes, denominator and process separation

| Condition | Outcome | Counts toward valid SR denominator |
| --- | --- | --- |
| Normal rollout reaches first environment success | success | yes |
| Normal rollout reaches official horizon without success | failure | yes |
| Predicate error/invalid predicate type, inference/step/reset error, interrupted control, early exit without success, required Local cleanup failure | invalid | no; explicit count, blocks full coverage |
| Media encoder/missing video/PNG write or optional browsing problem | diagnostic warning only | does not change episode outcome |
| Process/env close/coordinator error after valid result commits | process error | never rewrites valid outcomes; blocks clean qualification |

Legal environment booleans include Python bool and numpy boolean scalar. Never infer from reward, model confidence, generated frames or env_done. Predicate exceptions propagate to Invalid; no broad except→False. A Local cleanup failure keeps the observed environment_success field (possiblyTrue) but invalidates execution of that Episode, not a behavioral failure. Stop using that Server until safely retired/rebuilt. Do not claim normal terminal success before the action/Local chronology completed.

Each task has expected50 and total expected900. Publish success/failure/invalid/pending and valid counts. `sr` is **null until every planned Episode in the selected generation is valid**. `partial_sr_valid_only=success/valid` is separately labeled conditional coverage, not Benchmark SR. Full SR is successes/900 (same as task macro-average only when all18 have equal50). Exactly900 logical index rows, including Pending/Invalid, with no silent exclusion.

When all900 outcomes are valid but a process failed afterwards, preserve the numeric environment SR and mark `complete_with_process_errors`; no clean Benchmark PASS. The Stage1 prototype conservatively retains process errors as blockers; it has **no automatic error-resolution/forgetting policy**. Stage2 must present a separate execution-scope/resolution contract before allowing resumed clean execution to close an earlier infrastructure fault. Merely opening/rebuilding summaries must not erase it. `runtime_gate_approved=false` is constant in the prototype.

## 6. Sampling and proposed conservative Resume default

Fresh Task creates one env with original literal Seed/environment settings; existing native loop calls public reset50 times sequentially, with actual stepping between resets. No per-Episode derived Seed and no reseeding per reset. Keep real ep metadata/scene provenance + actual instruction. GPU count changes parallel Task allocation, not per-Task sequence or episode count. One fresh Server/session slot per assigned Task worker initially, preserving existing policy_seed=0 per Task; Task restart must restart that policy RNG lifecycle too, not merely reset Local sessions. Local session fresh/reset per Episode. This real Server behavior is a Stage2/Canary requirement, not implemented by fake CPU task drivers.

**r1 proposal: Task-level recovery.** Reuse a Task only when all50 contiguous results from one generation/stream are valid. Interruption/Invalid leaves an incomplete stream; explicit Resume archives that entire stream and reruns the whole Task0..49 from the original literal Seed with a new env/stream ID. It does not retain old successes while retrying only failures. Old generation remains diagnostic, is identified in restart records, and never mixes into final900 statistics. There is no auto-retry-until-success; runtime failures stop execution and require explicit Resume.

Replaying only preceding reset calls cannot establish the original random state: stepping/model/environment work may have consumed RNG. Do not label independently recreated gaps as the same continuous scene stream. Synthetic test demonstrates this counterexample; it is not proof of RoboCasa's exact RNG. A future per-Episode independent-scene or exact simulator/RNG snapshot protocol would need its own design/version and benchmark label, not a hidden optimization.

This default is deliberately more conservative than the old flexible Episode reuse. It is a **proposed r1 design choice for GPT/Owner**, not an existing production behavior. Worst-case recovery repeats49completed episodes of one interrupted Task; completed other Tasks stay untouched. Review this cost explicitly before Stage2.

## 7. Durable state machine

One coordinator owns `_internal/.run.lock`, validates immutable manifest before and after nonblocking exclusive lease, and serializes all result/index publications. Workers later send bounded events with assigned Task/stream token; they do not acquire independent result authority. Initialization, mkdir/log-open/server-start failures must be caught by the outer worker boundary and reported even if other workers finish all Tasks.

Episode state: Pending→Running→immutable success/failure/invalid. Commit requires active coordinator Task claim, current generation/stream, expected next reset index, legal environment observation/termination and no prior Invalid in that stream. Bounded strict UTF-8/JSON, duplicate-key/NaN rejection, checksum and namespace checks. File fsync→exclusive atomic publication→parent fsync; duplicate/out-of-order/stale producer results refuse. No overwriting an old terminal result in place.

Restart transaction: persist adjacent old/new generation journal→rename old Episode tree to deterministic archive→fsync parents→create empty active tree→atomically publish new Task stream→remove journal/fsync. Recovery handles before/after move and before/after state replacement idempotently. No producer allowed until journal completes. Malformed/foreign transition, conflicting nonempty trees or lost active+archive data are BLOCKED, not an invented empty success. A half-initialized Task claim without its Episode directory explicitly blocks in this prototype; do not silently reconstruct possibly lost evidence. Stage2 must define safe initialization recovery or retain an explicit blocked/new-run disposition.

`summary.json`, each Task summary and `episodes.jsonl` are derived conveniences, atomically rebuilt from current-generation results. Index uses replace rather than append, preventing duplicate/half-line authority. Views can lag or be interrupted independently; never use them for result admission. Read-only inspection does not repair/mutate views. Process/progress/errors do not rewrite scientific result files.

## 8. Stage2 production wiring (NOT implemented/authorized by Stage1)

- New explicit launcher/config/module (`run_robocasa_eval_v2.sh`, V2 example config/runner); original manual entry untouched, no legacy fallback. CPU preview lists resolved18tasks/horizons/model parameters/paths/GPUs/media/restart decisions and cannot start a model/env or write a run.
- Child narrow optional hooks/output sink on existing `run_policy`, default legacy behavior unchanged: strict success predicate + observed-step callback, Episode-specific evidence paths, explicit media-independent behavior. Keep actual predict/state/raw action decode/env.step/Local begin→payload→ack→record_completed sequence. Do not copy/reimplement Cosmos or modify training.
- Replace old `run_recorded_episode` archive adapter only in V2: terminal authority captured independently from media; language equals exactly what model received. Local cleanup must execute even when media fails/hangs; retire contaminated Server after cleanup failure, no next session. Local algorithm itself unchanged.
- Generated-video saving mode controls storage only; never disable/change native forward or alter RNG calls. Isolated bounded media encoder/spool, best-effort admission/drop diagnostics when overloaded, direct single original destinations; no unbounded RAM frame queue or duplicated MP4 exports. Main simulation/control state and RNG must not be mutated by diagnostic workers. Stage1 `try_media` tests restore already-loaded Python/NumPy/CPU Torch global RNG for synchronous callbacks, but is not a full encoder/process design.
- Preserve owned-process timeout/cancel/TERM→KILL/reap with initialization caught, exact listener ownership and `/info`. Cancel media separately; it cannot hold Local cleanup/result commit indefinitely. A leaked process is a process-health fault even if SR truth is known. No automatic ffmpeg decode or videos_view at task/final completion; explicit optional offline audit may be added later, cannot rewrite SR.
- Separate implementation/test-only SHA, GPT incremental review, DS independent CPU, then separately authorized small real Canary. Only after Canary model/ABI/Local/session/reset/output/process checks and explicit Owner GPU authorization can fresh900 start. No action to current431.

## 9. Stage1 acceptance and review request

Only new `tools/v3/episode_eval_v2_prototype/` + this design/evidence/SESSION/TODO/Inbox. Production `scripts/`, `configs/`, Child/Gitlink, vendor, old eval and training all zero diff from baseline. CPU injected fake environments only, no real DCP/model/server/Kitchen/GPU. Formal900 test uses18fakeTasks×50 and verifies450success/450failure,900unique rows and exact0.5 arithmetic; synthetic50reset test verifies literalSeed/no per-Episode seed and reset-only replay counterexample. Not900 real rollouts or full native model evidence.

Test matrix: success/horizon/error/Local failure and typed authority; media/RNG independence; strict identity/immutable outputs; every restart transaction boundary/stale producer/no-copy video inode; lock contender CPU process; duplicate/sparse/post-invalid results; corruption/oversize/symlink/schema/old namespace; read-only/rebuildable indexes; late worker error separate from valid SR; initial partial claims explicitly blocked. All prototype outputs retain prototype_only and deny runtime authorization.

Request GPT **APPROVE_DESIGN / REQUEST_CHANGES / BLOCKED** for exact Design Root + unchanged Child and these proposed defaults. Please decide conservative Task restart and outstanding process-error/initialization dispositions explicitly. This Gate is not approval to connect production, mergeV3, launch GPU, reset old eval, migrate431 or run Canary. Codex stops after this Stage1 review handoff.
