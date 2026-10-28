# Evaluation V2 Phase A — dynamic reusable Sim Slots

2026-10-28 Asia/Shanghai. Owner Issue8 authorizes isolated production implementation and CPU tests only. Baseline exact source pair: Root4769d711777c20a72dd7a3f6071a96f08ad8abb0 / Child2d4a42590fead00ea16f6ae5902e2bc8382b07e2. The FINAL corrected Stage2 review is APPROVE_CODE; withdrawn F1 is not an actionable bug. New Phase A code requires a new pair/review. Prior D1–D5 scientific authority survives; the unvalidated18 permanent Task actors are superseded. No GPU/native/merge/900 or Phase B production authorization.

## Physical capacity and logical plan

A selected GPU provides one long-lived model Server and at most one reusable Sim process. Processes start lazily when work exists; selected idle GPUs need not load unused models. Config keys `sims_per_gpu:1` and `max_infer_batch_size:1` and matching CLI flags are explicit. Other values reject before runtime initialization; increasing max_sessions is not implemented batching. The old `max_resident_envs:18`/`max_contexts_per_gpu:6` keys reject rather than silently preserving the retired architecture. Dynamic G/N do not alter the frozen Task order or total logical slots.

The actual production RoundScheduler no longer assigns Task index modulo G. Any eligible idle physical worker consumes the next logical Task/Episode in exact Episode-major order. A worker has one outstanding claim; current-round claims must all become valid Core or explicit Owner-pending before the next round. N<G leaves extra physical workers idle; resident Sim count never follows N. Same Task can run on different physical Slots after a clean previous Episode. Per-GPU Server lifetime is independent of Task switching and no model reload is triggered by a switch.

## Slot ownership, cleanup and Task changes

Child `eval_v2_slot.SimSlot` implements the production lifecycle. Root caches actors by physical GPU worker, not Task; each process has a globally unique physical Slot ID. Immutable process registry PID/start/PGID/session plus inherited-socket nonce and request ID fence process ownership. Logical Task stream/attempt/lease IDs remain independent. The Worker accepts only Tasks in the Root-attested allowlist, verifies real metadata hashes before construction and accepts only persisted, exact environment seed grants. Arbitrary paths/config from requests are not accepted.

`IDLE -> CLAIMED -> TASK_SWITCH(if needed) -> ENV_READY -> RESETTING -> ADMISSION -> SESSION_OPEN -> EXECUTING -> SESSION_CLOSING -> CLEAN`. Unknown/unsafe initialization, rollout or cleanup failures enter `FAILED_QUARANTINED`; shutdown/recovery enters `PROCESS_RECOVERY`. Quarantined Slots refuse new claims. Root cancels further work and decommissions owned simulator/model processes; a later explicit Resume starts fresh processes and follows D1 proofs. Same-process automatic unverified recovery is not implemented.

- Different Task: previous CLEAN already proves native Local end/reset ACK and no pending action request; close old env, verify new metadata/grant, make the new Task env, then reset and strict initial precheck. A switch cannot occur during an Episode.
- Same Task: retain the environment object and native RNG, reset for the new Episode, and still create a new Local client/session. `Kitchen.hard_reset=True` can rebuild models/EGL even when the Python object is reused; no constant-time/zero-EGL claim is made.
- Native adapter/client/server action path is reused. Each native Episode client generates new session_id and episode_id; first request resets its session at consumer frontier0 with no evidence. Only completed evidence advances that session. Positive Server reset ACK is mandatory before CLEAN. Slot IDs/GPU IDs are never used as the server Fast State key. W0/model math and required-mode Local implementation are unchanged.
- D4 happens before any Local session/prediction. Initially successful scenes resample. Four consecutive recoverable init errors skip; legal boolean observations break the streak;32 total samples stay bounded. Explicit no-session release is allowed only for unadmitted scenes, never an admitted or unsafe one. Skip retains Owner-pending status and ordinary Resume never retries it.

## Honest seed and scene provenance

A logical Task stream is a coordinator evidence lifetime, **not a promise of one physical environment or one continuous native RNG after Task switches**. It may span several physical Slot assignments. The existing result `seed`/`reset_index` identify that logical stream and its sample order; the new versioned sampling protocol explicitly states this. Native public result and scene evidence additionally contain mandatory runtime-produced `sampling`: `environment_id`, `actual_seed`, `environment_reset_index`, `physical_slot_id`, and protocol. Actual layout/style/fixture metadata remains in `scene_provenance.json` when exposed by `env.get_ep_meta()`; unavailable fields are not invented.

Each Task's environment creation grants are immutable under `_internal/tasks/<Task>/environments/`. Grant ordinal k receives `(manifest.seed+k) mod 2^32`, unique for that Task until the seed space is exhausted (then fail closed). Grant publication precedes creating the environment. A crash/failed creation consumes the grant; Resume cannot reuse it. This is an environment-rebuild sequence, not mandatory fixed per-Episode SHA seeding. Same-Task reuse continues the existing environment's RNG and reset index; switching away and back or starting a new process uses the next grant. Recreated Task environments therefore do not blindly start at the same Seed each Episode.

Root verifies the actual start acknowledgement against its durable grant, snapshots the admitted sampling witness before opening a Local session, then requires the final response to match. Core Store checks the exact attempt-bound admitted witness and underlying grant; the Core scene file must match the result. The extra sampling data is included in the immutable index/result. Low-level contract tests can still construct direct non-Slot records to test unchanged D1–D5 invariants; the production Root runtime always requires the full sampling witness and cannot opt out through CLI/YAML. Source/config/protocol identity prevents adopting the former Stage2/old431 run as a new Phase A run.

Native reset/scene streams differ from the old one-env-per-Task50-reset evaluation when switching Tasks. D3 does not require recreating an interrupted scene. Each recreated environment and Resume boundary is disclosed; no strict scene- or result-equivalence claim with older sampling protocols is made.

## D1–D5 and media boundaries

Existing Core source/Task/attempt admission, strict `_check_success()` after completed actions, normal horizon failure, raw15/state15/camera/action transform, Local chronology, atomic staged directory commit and immutable success/failure remain unchanged. Same-round cancellation and commit still share the approved Scheduler lock; cancel returns before coordinator faults are recorded. The withdrawn F1 synchronization mechanism is not rewritten.

Fault scope follows currently producing Slot assignments/in-flight claims, not historical logical Task streams whose environment was switched out cleanly. A fault before valid Core requires same-slot valid replacement plus positive owned cleanup/fresh health. A post-Core fault retains the result and requires execution-only recovery. Final stream cleanup still requires all owned simulator/model process groups decommissioned; a logical stream is never marked `owned_processes_gone` merely because a live Slot changed Task. No relaxed cleanup receipt shape or global fault clearing is introduced.

Media remains independent: no automatic full MP4 decode, no duplicate videos, bounded encoder/queue. If encoder cleanup is uncertain after an otherwise valid native outcome, the Slot quarantines but returns the valid Core for atomic publication; Root then records a process fault and stops, preserving SR evidence. It cannot classify that valid result as a policy failure or repeat it on Resume.

## CPU and later native acceptance

Author tests must execute production Scheduler/Runtime/SimSlot APIs, with only process/model/GPU/physics boundaries replaced. The matrix G={1,2,3,4,8} × N={1,2,4,7,18} exercises dynamic dispatch, barriers and resident limits. Lifecycle tests use actual native run_policy, raw15->env12, HTTP/Local codecs and faithful fake env/server. They cover TaskA0→TaskB0→TaskA1, same-Task reset reuse, session IDs/frontiers/reset ACK, quarantine and recovery, metadata/grant/stale binding rejection, D4 and sparse Resume. Full18×50 CPU scheduling measures coordination costs; synthetic SR is not native benchmark evidence. No assertion about actual GPU W0/W_i numerics or EGL capacity is made from CPU tests.

After exact new pair/source blobs/raw JUnit/static/diff publication: STOP for GPT Code Gate, then DS independent CPU. Native model loading, actual Fast State isolation, GPU mapping, EGL/reset/switch resource growth and throughput require separately Owner-authorized Canary. Phase B must start with design review for M>1, multi-session transaction and ONE true batched generation call; no Phase B implementation is in this candidate.

## Commands after required approvals

Copy the updated example outside the clean reviewed worktree. Use a new namespace; do not migrate or edit current evaluation/training outputs.

```bash
PYTHON=/path/to/coordinator/python bash scripts/run_robocasa_eval_v2.sh dry-run \
  --config /external/eval_configs/phase_a.yaml --gpus 4,5,6 \
  --tasks CloseFridge,NavigateKitchen --episodes 2 \
  --sims-per-gpu 1 --max-infer-batch-size 1 \
  --output-dir /external/eval_runs/new_phase_a_canary
# fresh/resume use the same entry only after separate execution authorization.
```

No phase transition, merge, real simulator, model/server, DCP or GPU is started by this document. Exact pair and actual author results are in the Phase A handoff/Evidence.
