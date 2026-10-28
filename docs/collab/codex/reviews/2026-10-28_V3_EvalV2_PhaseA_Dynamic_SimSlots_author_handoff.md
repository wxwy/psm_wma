# Evaluation V2 Phase A — Issue8 implementation / new Code Gate request

2026-10-28 Asia/Shanghai. **Author CPU complete, request GPT Code Gate. No native execution or merge authority.**

| Object | Exact identity |
| --- | --- |
| Formal Root | `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` |
| Formal Child / Gitlink | `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Both isolated candidates | `v3-eval-v2-slots-a-20261028` |
| Full Phase A review base | `4292905afcf6dfd0ce4f00e336c35a7c09e319b0` (ACK before edits; source equals4769d711) |
| Root intermediate, unreviewed implementation | `1ac82af40a95587dd3f5e016dbc6a7e73ebeb9c2` |
| Approved source baseline | Root `4769d711777c20a72dd7a3f6071a96f08ad8abb0` / Child `2d4a42590fead00ea16f6ae5902e2bc8382b07e2` |
| Owner directive consumed | `0c424c830968cf447f5bd36c438d46325d12a557`, Issue8 |

Read the FULL4292905a..fd7e43f6 Phase A diff, not only finalRoot's small last commit. Prior Stage2 FINAL corrected `APPROVE_CODE` and explicit F1 withdrawal were read. That verdict remains historical on4769/2d4 and is not inherited by this pair. The original Stage2 candidates are preserved; neither canonical `V3` nor `v3-local-ttt` was pushed. D1–D5 science/evidence remain; only the old18 permanent Task-Sim architecture is superseded.

## Actual production changes

- Child `evaluation/robocasa_v2/scheduler.py`: remove sticky Task-index modulo GPU routing; any idle physical Slot consumes the next exact Episode-major item, retaining existing ordered claims/commit/cancel lock/barriers/Resume. Root runtime caches by physical worker and limits useful workers to min(G,N); selected extra GPUs remain idle. One lazy persistent policy Server and one Sim process per used GPU; no model reload on Task switch.
- Child `simulation/robocasa/eval_v2_slot.py:14`: explicit lifecycle, fenced `switch_task` (`:81`) and `start_episode` (`:93`). Verify persisted claim, current coordinator lease, logical stream, Task allowlist/metadata and immutable environment grant before creation. Same Task uses reset without make_env; different Task closes old env only after prior CLEAN, makes new env and resets/prechecks. Task switch mid-Episode or an unclean/quarantined Slot rejects.
- Original native policy/action/raw15→env12/state15/camera/Local client code is reused. Fresh session_id/episode_id/frontier0 per admitted Episode; no Local Session or inference for rejected scenes. Local end/reset ACK precedes CLEAN. Unacknowledged cleanup/unsafe initialization quarantines and stops; explicit Resume decommissions/rebuilds owned runtime and starts a new Session. No model/Local math, Server batching, training, optimizer, DCP or vendor edits.
- Child Store `allocate_environment` (`:407`) persists per-Task environment creation ordinals and unique `(manifest Seed+ordinal) mod2^32` seeds; unused grants survive crashes. Same-env reset retains native RNG. `bind_sampling` (`:445`) snapshots admitted actual seed/environment/reset/physical Slot against its grant before Local begins; response/Core scene must match. Manifest versions the new sampling/resource protocol; logical stream seed is distinct from actual environment seed. Root/Child scientific identity rejects adopting old runs. Actual layout/style/fixture metadata is retained when the environment supplies it, never fabricated.
- Root `_start_assignment` (`scripts/robocasa_eval_v2/runtime.py:303`) validates acknowledgement, records physical GPU/Slot/Task/attempt source and checks resources after assignment. Worker config is attested once, selected metadata is rechecked on switch, inherited-socket nonce/IDs fence responses. M=1/B=1 explicit config+CLI; all other values reject, retired18-env capacity keys reject. No serial loop is described as batch inference.
- D1 scope follows current physical Slot assignments and in-flight claims; switched-out historical Task streams are not globally faulted. Full stream cleanup still requires owned processes gone, not merely a successful Task switch. During final audit, a new Phase A edge was closed: unexpected Slot exit0 after the final Core must block clean qualification. Same scheduler cancel/commit serialization remains; affected scopes are recorded only after cancellation. Core stays valid/immutable and a fresh execution-only health recovery never retests it. This is unrelated to the withdrawn Stage2 F1.
- Media remains diagnostic-only: uncertain encoder cleanup quarantines the Slot but returns a valid native Core for publication before recording process fault; no automatic full MP4 decode or duplicate copies. Existing Task/Episode storage and Owner-only retry commands remain.

The initial Phase A source is in1ac82af4; finalfd7e43f6 closes late-exit qualification. Root full-range patch, final-commit-only patch, Child patch and file lists are in the Evidence directory. A convenience last-commit diff cannot represent all Phase A changes.

## Author CPU results and what they mean

`docs/collab/codex/evidence/2026-10-28_eval_v2_phase_a_author_cpu/`: raw **255 passed =197 production-path +58 legacy,0 failure/error/skip,178.04s pytest**; runner179.811s.37 frozen Python files pass Ruff0.12.7 check/format/AST; shell syntax/help pass.52 Git Blob/source/config/test/shared-helper/runbook bindings match the exact pair, and the actual committed source guard passed clean. Original draft failures are retained separately, not counted or suppressed.

Behavior coverage includes all25 G={1,2,3,4,8}/N={1,2,4,7,18} combinations; actual default Root pool + real Worker socket serve; TaskA0→TaskB0→TaskA1, same-Task reuse, distinct real client Session IDs/frontiers/reset ACK, toy W0/evidence update state, metadata/grant/lease/stale claim negatives, strict D4 resampling/three-then-legal/four-errors clean release, owner-pending Resume skip, quarantine→explicit new Slot/Session Resume, sparse valid success/failure preservation, mid-round cancellation and deterministic both-order Core/cancel lock tests.

Synthetic full900 uses actual production Runtime/Scheduler/SimSlot/native HTTP/Local codecs with fake model/physics/process boundaries: **900 dispatches,50 barriers,3 physical Slot objects/3 mock model loads,900 fake env creations,450 success+450 normal failure,87.985s**. This does not claim a real SR or900 actual RoboCasa episodes. p95 claim76.89ms/Core commit27.14ms/lock wait65.54ms, summary max3.00s;10023 JSON reads/118688 cache hits. Whole CPU test peak child process RSS351012KiB (~342.79MiB), user126.14s/system51.71s. No speedup claim versus earlier lighter tests or extrapolation to native resources.

Targeted late-exit RED restores ONLY1ac82af4 `Runtime.run` in CPU memory and fails the new assertion; current GREEN preserves the Core, blocks qualification and resolves via a no-prediction/no-retest explicit Resume. Raw RED, GREEN and runner snapshot are retained. No working-tree rewind was used.

## Limits, next review and STOP

Architecture note and commands: `docs/build/PSM-WMA_V3_EvalV2_PhaseA_Dynamic_SimSlots_2026-10-28.md`. Sampling changes are explicit: Task switches recreate environments and use new seed grants, so the run cannot claim to reproduce old contiguous50-reset scenes. One Sim/GPU may require900 environment creations under the required round order; the model is retained, not the18 Task envs. Kitchen hard resets may rebuild MuJoCo/EGL even on the same Task.

CPU tests do not prove actual W0/W_i tensor numerics, physical GPU/renderer capacity, close/reset driver behavior or GPU throughput. Default model serving remains required-mode B=1/max_sessions1. Native GPU/RoboCasa/Canary, DCP, real900, old431, active training and canonical branches were not operated. Resource feasibility and real semantic continuity need a separately Owner-authorized Canary after code and independent CPU Gates.

Request GPT fresh **full Phase A Code Gate** on fd7e43f6/d2c1bda6, then DS independent CPU in a clean exact-pair worktree. STOP after publication/readback. Phase B remains design-first after Phase A decision; no M>1, multi-session transaction or batched model implementation is included or authorized here.
