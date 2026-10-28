# Evaluation V2 Stage2 — production candidate and CPU runbook

2026-10-28. Owner-authorized implementation only; GPT Code Gate, DS independent CPU and separately authorized native Canary remain required. This document does not authorize GPU use or a900-Episode run. Exact implementation pair and frozen author logs are recorded in the Stage2 handoff, not inferred from this document's later documentation HEAD.

## Authority and changes

Implements the approved Stage1 Root `1fd3ad42075032bd0137ac9a76306169aaa45032` / Child `746c5cf2f2324104a62fb71510343aa40d3976c5`, GPT `APPROVE_DESIGN`, under the latest Owner D1–D5 contract. Stage2 authorization is the Owner's explicit `授权` following the Stage2 scope. Prior Task replay, fixed per-Episode derived seeds, video-gated SR and old431 migration are superseded. No old results are adopted.

Root `scripts/robocasa_eval_v2/` provides strict configuration, scientific input identity, resource admission, the actual runtime and CLI. `robocasa_eval_v2_processes.py` provides owned-process supervision. Child `cosmos_framework/evaluation/robocasa_v2/` contains the production contract, Store, Episode-major scheduler, Core evidence validator, socket framing and bounded media encoder. `eval_v2_worker.py` constructs the real pinned RoboCasa environment; `eval_v2_adapter.py` calls the existing native `run_policy`, HTTP codec, raw15→env12 conversion and Local client. Optional native hooks preserve legacy defaults. There is no production dependency on the isolated `tools/v3/eval_v2_prototype`.

No model, action transform, Local-TTT algorithm, optimizer, training launcher, DCP implementation, vendor lock or legacy evaluation entry is changed. Root/Child candidates remain separate from V3 and `v3-local-ttt` until explicit merge approval.

## Operator interface, after the required Gates

Use a clean detached worktree of the exact reviewed Root/Child pair. Copy the example configuration **outside that worktree**; edit readonly input paths and a completely new output namespace. The source guard rejects untracked production configuration/scripts and tracked edits. `PSM_REPO` is supplied by the shell wrapper for the vendor-lock path. Other paths should be absolute. Training config, Checkpoint and dataset roots are protected inputs, never destinations.

```bash
# CPU preview only; this does not attest installed runtime or load a model.
PYTHON=/path/to/coordinator/python bash scripts/run_robocasa_eval_v2.sh dry-run \
  --config /external/eval_configs/eval_v2.yaml

# Native commands below require separate Owner execution authorization.
PYTHON=/path/to/coordinator/python bash scripts/run_robocasa_eval_v2.sh fresh \
  --config /external/eval_configs/eval_v2.yaml
PYTHON=/path/to/coordinator/python bash scripts/run_robocasa_eval_v2.sh resume \
  --config /external/eval_configs/eval_v2.yaml

# A subset Canary needs its OWN new namespace; it cannot become the formal900 run.
PYTHON=/path/to/coordinator/python bash scripts/run_robocasa_eval_v2.sh dry-run \
  --config /external/eval_configs/eval_v2.yaml --gpus 4,5 \
  --tasks CloseFridge,NavigateKitchen --episodes 2 \
  --output-dir /external/eval_runs/eval_v2_subset_canary
```

`fresh` refuses an existing output namespace. `resume` requires the same frozen scientific plan, source, model, training configuration, runtime identity, Task order, Episode count, horizons and Seed. Runtime GPU/resource/media settings are invocation diagnostics and cannot change an already committed Core. No legacy catalog or prior V1/V2 prototype run is imported. The original Owner contract for flexible legacy Resume is not an authorization to combine a new V2 formal run with old results.

`tasks: all` requires exactly the18 Target Atomic-Seen classes from pinned RoboCasa1.0.1. Explicit subsets retain their specified order. Only exactly18×50 is labeled `formal900`; a synthetic CPU test's formal-shaped manifest is explicitly synthetic evidence, never a native benchmark. Action horizon16, raw15/state15, left_wrist, Local-required and success latch1 are fixed.

## D1–D5 execution and recovery

- D5 dispatches `episode_index` first, then frozen Task order. Three workers may execute different Tasks in the same round; all prior-round slots must become valid Core or Owner-pending before the next round. Sticky Task/GPU ownership retains one Task environment object across rounds. Resume rescans the same plan, skips valid success **and** normal failure, and executes only missing eligible slots. A missing ep37 does not invalidate valid ep38.
- D4 checks a strict boolean `env._check_success()` immediately after reset, before any prediction or Local begin. Initially successful scenes are rejected. A legal precheck, even True, breaks the initialization-error streak. Fourth consecutive recoverable initialization error produces `skipped_init_error`; total32 admission samples without admission produce `scene_admission_exhausted`. Known sampling/type errors require positive finite-physics/forward probes for retry; unknown/EGL/device errors stop safely. Native action-loop predicate errors are Invalid, not normal failure.
- D3 an interrupted slot retries in a new stream from a newly sampled legal scene; no promise to reproduce the old scene or RNG stream. Literal manifest Seed initializes each Task environment; consecutive resets within that live stream retain native RNG semantics. Every row records actual Seed, reset index, stream and attempt; restart is explicitly a new sampling stream, not a recreated old scene.
- D2 Task/slot intent, directory and ready transitions are recoverable. Claims include lease, worker, stream and attempt identity. Native writes into an exact private attempt directory. After Core chronology and cleanup validation, sealed inventory plus result and all evidence are fsynced and the whole directory is atomically renamed into the empty public slot. No existing Core can be replaced; stale/misrouted/duplicate responses reject. A crash before publication leaves private diagnostics; a crash after publication leaves the entire valid Core. Derived summary corruption is rebuilt; Core corruption fails closed with a non-success report.
- D1 immutable process faults are scoped to the Task/stream/exact attempt and remain in history. Resume first proves all prior owned process groups closed. Resolving a pre-Core fault requires a fresh healthy stream and valid replacement for the same slot. A post-Core/Task fault requires fresh health and cleanup, without rerunning valid Episodes. Faults and scientific outcome are independent: valid results may remain present while `results_qualified` is false. No open stream qualifies as clean execution.

Generic Resume never retries an Owner-pending slot. The Owner can supply an external, targeted decision:

```json
{
  "schema": "psm_eval_v2_owner_release_v1",
  "approved_by": "Owner",
  "owner_decision_ref": "Owner's explicit decision reference",
  "manifest_digest": "copy the exact current manifest digest",
  "slots": [{"task": "CloseFridge", "episode": 37}]
}
```

```bash
PYTHON=/path/to/coordinator/python bash scripts/run_robocasa_eval_v2.sh authorize \
  --config /external/eval_configs/eval_v2.yaml \
  --owner-decision /external/owner_decisions/retry_ep37.json
# authorize only records the decision; a separately invoked resume executes it.
```

All targets must be blocked missing slots, with the exact manifest; valid Core cannot be released for retest. The file/ref/SHA are retained. This is an explicit manual decision interface, not cryptographic proof of who authored the decision; the execution principal must actually hold Owner authorization.

## Native identity, lifetime and finite budgets

Before a model starts: cold full Checkpoint hashing/header admission, training config and Task metadata identities, reviewed vendor-lock bytes, pinned runtime source/asset attestation and official horizons. Subsequent Resume uses the existing approved fingerprint cache for trusted readonly model inputs (device/inode/size/mtime/ctime unchanged); changed fingerprints trigger full verification. It is not an adversarial filesystem attestation. Source guards reject code/Gitlink drift and dirty/untracked production files; documentation-only Root changes may retain the same frozen implementation identity.

The actual simulation interpreter verifies module origin/source SHA, library versions, runtime digest and Task metadata before environment creation. READY is nonce/PID/Task/stream bound. Action Server arguments explicitly select16 and Local-required; loopback `/info` is checked against exact Checkpoint/model directory, Config and inference protocol plus listening-process ownership. HTTP simulation requests disable ambient proxies.

One model server per selected GPU is retained. At most18 Task actors and declared maximum6 per GPU are admitted by the default configuration. Each GPU is inspected for foreign compute processes,85% VRAM threshold and20GiB initial headroom; owned RSS has a128GiB default cap. Foreign workloads are never killed. Thread-safe scheduling serializes environment use per physical worker. Linux process identity includes PID, start time, PGID and session; registry cleanup uses only proven owned groups. Parent-death protection covers server, Task actor, encoder and FFmpeg. Unreapable old groups or ambiguous PID ownership block Resume; they do not yield fake cleanup receipts.

The configuration bounds server startup900s, total Episode reset/admission+execution1800s after actor readiness, per HTTP request600s, process termination grace10s and encoder grace2s. A total Episode deadline spans all initialization attempts and execution rather than restarting after every reset. Cancellation interrupts actor sockets, terminates/reaps owned groups and preserves diagnostics. Exceeding a budget fails the run and retains the missing slot; it does not classify the policy as a failure.

**Resource limits are admission guards, not measured capacity evidence.** Retaining18 Python environment objects does not prove18 constant EGL contexts: native RoboCasa reset may reconstruct MuJoCo models/contexts. Actual EGL lifetime/churn, CUDA device mapping, RSS/VRAM growth and startup/round costs must be measured in the separately authorized Canary. No eviction/pooling of Task environments that would silently change the approved sampling stream is implemented. If the proposed18 retained environments are infeasible, stop and revise that resource policy explicitly.

## Public results, media and progress

The run contains `manifest.json`, `summary.json`, Episode-major `episodes.jsonl`, and `tasks/<Task>/episodes/ep_NNN/{result.json,actions.jsonl,predictions.jsonl,local_memory.json,scene_provenance.json,core_inventory.json,media/}`. Failed/uncommitted attempts remain under `_internal/tasks/<Task>/slots/ep_NNN/work/<attempt_id>/`. Logs are under `logs/`; processes, leases, decisions, invocations, cache, progress, faults and receipts are private management evidence. Episode result names remain stable; no default duplicate videos directory is created.

Environment success is only a typed `_check_success()` after completed action(s); horizon exhaustion with no success is normal failure. Runtime/predicate/Local/Core errors are Invalid or Interrupted, never policy failure. Full SR is null until complete coverage; `partial_sr_valid_only` is separately labeled. Clean qualification also requires resolved current process errors and every stream closed. All summary counts/index rows derive from verified Core and ledger, never MP4 existence or UI progress.

Native raw15/state15, completed-action provenance, prediction16, Local acknowledgements/session/frontiers and end+reset are checked. The callback reuses the original action/Local sequence. Media uses a spawned CPU encoder, queue capacity4, bounded frame/prediction sizes and drop/error diagnostics. Generated video means one optional diagnostic clip per selected replan. Encoder completion is after native Local cleanup. Missing/corrupt/dropped video does not change SR or rerun Core; uncertain forced process cleanup separately blocks clean execution while preserving Core. No automatic strict MP4 decode, no video copy, and no media inventory in Core qualification.

The terminal prints each finished slot immediately and current worker/GPU/task/Episode/steps/replans/last latency/stage about every5s. Non-authoritative progress may lag during model/environment startup or encoding. `_internal/coordination_metrics.json` records bounded p50/p95/max samples for claim, Core commit, summary rebuild and scheduler lock wait plus JSON read/cache counters. Immutable-record caches are guarded by file stat witnesses, including Core and private provenance; changed files are revalidated.

## Author CPU Gate and later acceptance

Author commands and environments are frozen in `docs/collab/codex/evidence/2026-10-28_eval_v2_stage2_author_cpu/`. CPU tests import production Store/Scheduler/CLI/Runtime/Worker/Native adapter. External simulator/model/GPU boundaries are synthetic. The17-action native-loop witness uses real loopback HTTP and actual action/Local client codecs, with fake environment and fake model responses. Tiny DCP-shaped headers test identity/cache admission only; no real distributed Checkpoint save/load is performed. Tiny FFmpeg **encoding** verifies optional media, not full-video decode or native rendering.

Required results: D1 scoped failures and recovery; D2 crash windows and stale/duplicate identities; D3 sparse Resume success/failure preservation; D4 reset filtering, four-strike skip and explicit retry; D5 exact900 order, same-round concurrency and50 barriers; process ownership/cancellation/deadlines/parent loss; strict native checks and Local cleanup; media faults independent of SR; cold/warm input identity; legacy default-hook regressions. Ruff0.12.7 check, format check, Python syntax and shell syntax must pass for changed files. Logs retain failures rather than replacing them with a final green count.

After GPT Code Gate: DS runs the frozen commands independently in a clean exact-pair worktree. Then Owner may separately authorize a tiny real Canary to verify actual Cosmos loading/`/info`, pinned RoboCasa reset/step, raw15/state15/Local-TTT behavior, device/EGL capacity, media bounds, resource growth and process interruption→Episode-only Resume. A Canary must use its own namespace. Only all required Gates plus explicit Owner execution authorization can permit a fresh formal900 run. Old431 data and all active training worktrees remain untouched.
