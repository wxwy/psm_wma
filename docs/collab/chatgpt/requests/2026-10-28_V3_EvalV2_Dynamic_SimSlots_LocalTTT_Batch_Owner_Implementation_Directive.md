# Owner implementation directive — Evaluation V2 Dynamic Sim Slots & Session-safe Microbatch (2026-10-28)

**Status: OWNER AUTHORIZES STAGED CODE DEVELOPMENT / CPU TESTS ONLY. This is NOT a GPT Code Gate approval, not an instruction to merge, and not permission to execute real GPU, Cosmos DCP, RoboCasa, simulation, native Canary or any part of the new 900-Episode run.**

## 0. Read first / source identity

- Project: `wxwy/psm_wma`, root branch `V3`; Child repo `wxwy/cosmos-framework`. Read current remote state and the latest canonical `docs/collab/chatgpt/CODEX_INBOX.md` before any work.
- Use last **source-level APPROVE_CODE** Stage2 formal implementation pair as the code baseline: Root `4769d711777c20a72dd7a3f6071a96f08ad8abb0`; Child/Gitlink `2d4a42590fead00ea16f6ae5902e2bc8382b07e2`. Stage2 candidate root branch `v3-eval-v2-stage2-20261028`, author Evidence HEAD `089e083c266d1768d0a6154023d75249d500f039` (bookkeeping, NOT formal code target). Do not accidentally use current `V3`'s older Child Gitlink as the implementation baseline.
- Previous correct final Code Gate: `docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_Stage2_4769d711_2d4a4259_F1_Correction_FINAL_Code_Gate.md`. Earlier D1 F1 concern was **withdrawn** and MUST NOT be 'fixed' without new evidence.
- Preserve the authority of `docs/collab/chatgpt/requests/2026-10-28_V3_RoboCasa_EvalV2_r2_CANONICAL_LATEST_OWNER_CONTRACT.md` (D1–D5) for success, error, Core commit, Resume, scene-admission, round-robin, media and safety. **Only the old fixed-Task resident-Sim resource architecture is superseded by this new Owner directive.**
- Use **isolated NEW root and Child candidate branches/worktrees** from the exact implementation pair. Do not merge to `V3`, `v3-local-ttt` or replace the prior Stage2 candidate; maintain full source/formal SHA provenance.

## 1. Frozen Owner architecture decision

The old default `G=3 GPU -> 3 resident Policy Servers -> 18 resident one-Task Sim processes (6 Sim/GPU, but only 1 executing per GPU)` is **no longer the target architecture**. Its resident-Sim capacity was never validated on real EGL/GPU and provides no Sim parallelism. Do not treat 6 permanent Task actors as a default requirement.

**New authority:** `G` dynamically selected GPUs, `N` dynamically selected Target Atomic Tasks (one or more, up to all18), `M=sims_per_gpu` configurable reusable physical **Sim Slots per GPU**, `B=max_infer_batch_size` independently configurable. Each GPU owns one long-lived Policy Server; a Sim Slot claims a logical `(run, task, episode, attempt)` from the global D5 Episode-major scheduler. The physical Slot and logical Task are decoupled. A Slot executes at most one Episode at a time. `M=1,B=1` MUST work without changing the old numerical model/Local-TTT semantics. `M>1` MAY only be marked supported once actual multi-Session / real batched server semantics are implemented and independently gated.

Keep global frozen D5 logical order: `for episode in [0..E-1]: for task in frozen_task_order` (for all18 ×50 exactly900). Same-round tasks may execute concurrently up to capacity; no later-round dispatch until ALL current-round logical slots are valid Core, explicit Owner-pending, or execution safe-stopped. Completion wall times need not equal dispatch order. Resume scans this identical plan; never re-executes any valid success or valid behavioral failure, including valid slots after a skipped hole.

## 2. Mandatory Sim Slot and Fast Weight lifecycle

**Episode/session ownership:** each Episode/Attempt has fresh globally unique `session_id`, `episode_id` and committed evidence frontier; Fast State is keyed on the server by **session_id**, never by GPU/Task/physical Slot. All Sessions share read-only slow weight W0 but maintain independent evolving fast weight W_i and Local Prefix P_i. No Fast Weight carryover between Episodes, including **same Task** and **different Task**. Fresh Episode starts from model W0, not the previous Episode's adapted state.

Slot state machine: `IDLE -> CLAIMED -> (TASK_SWITCH if required) -> ENV_READY -> RESETTING -> ADMISSION -> SESSION_OPEN -> EXECUTING -> SESSION_CLOSING -> CLEAN -> IDLE`; explicit `FAILED_QUARANTINED / PROCESS_RECOVERY` states are required. Do not allow Slot reuse after unacknowledged cleanup.

- Same Task/new Episode: reuse the task's environment object if safe, call real `env.reset()` and D4 strict initial-success precheck BEFORE opening a Local-TTT Session. RoboCasa `Kitchen` has `hard_reset=True`, so `env.reset()` may actually rebuild the MuJoCo model; do NOT claim constant-time reset or zero EGL recreation.
- Different Task/new Episode: FIRST verify previous Session has been ended/reset with Server ACK (and no unfinished batch/prediction), THEN `env.close()` previous task, create the new task-specific `native.make_env` from its real dataset metadata/official atomic-seen protocol, `env.reset()` and D4 precheck, THEN open a fresh Session. Task switch must never happen mid-Episode.
- `DEGENERATE_INITIAL_SUCCESS`: reject and resample a scene without any Session/Local update or model inference. Strict 4-consecutive recoverable init errors -> `SKIPPED_INIT_ERROR` and Owner-pending; unrecoverable EGL/process faults safe-stop; bounded total scene samples. Preserve exact D4 semantics.
- Each Episode after valid admission: begin with fresh session/W0; each completed causal observation/action updates only that session; reset/close its own Session in `finally`, including normal success, valid horizon behavioral failure, timeout/exception/abort. Require positive Server reset ACK before Slot returns to pool. Failure to prove reset/clean ownership -> quarantine Slot, fail-closed, recover/rotate owned Server as necessary, do not let next Episode inherit state.
- Keep immutable valid Core evidence and task/episode/attempt bindings. Failure of Local Session cleanup or source/physics integrity is not a behavioral failure and cannot silently enter SR denominator. Preserve process ownership and crash/Resume proof D1/D2.
- **Scene sampling under dynamic slots:** changing Task may recreate RoboCasa environments. Never instantiate every Episode with an identical Task seed and accidentally repeat the same scene. Codex must design and test a versioned seed/stream/reset protocol and record actual seed/stream/layout/style/fixture and Resume boundaries. D3 **does not require** old scene reproduction or mandatory fixed SHA-derived per-Episode seeds; choose an honest, diverse sampling scheme and disclose the impact on comparison with older contiguous 50-Reset Task streams.

## 3. Phase A — IMPLEMENT NOW: dynamic G/N, M=1, B=1

Authorize actual **isolated production candidate code changes and CPU-only tests** for Phase A now. Not merely a high-level proposal.

- Introduce stable Worker/Slot identities separate from logical Task IDs; one Sim Slot per selected GPU, one Policy Server per GPU; reusable worker process must support validated `switch_task(task_config)` (close old env, create new) and `start_episode(attempt)` without trusting arbitrary unverified paths/config.
- Replace Task-keyed persistent actor cache and sticky `task_idx % G` ownership with bounded Slot Pool. Global Scheduler pulls from ordered Task/Episode plan, dispatches to eligible idle Slot with exact Attempt/claim token and D5 barrier; no duplicate execution/commit or out-of-round dispatch. Preserve task provenance and run lease.
- Accept GPU lists of 1,2,3,4,8 (as physically present, no actual GPU test here), Task subsets 1,2,4,7,18 and arbitrary legal G/N; idle GPUs allowed. `M=1` -> **at most G Sim processes**, not `N` Sim processes; no fixed `max_resident_envs=18` / `max_contexts_per_gpu=6` resource assumption. Make settings and fail-closed resource guards explicit.
- Preserve a single Server process per GPU across Episodes; never reload the 13GB model merely due to switching Task or Episode (RoboCasa environment's own hard reset is separate). `--local-memory-max-sessions 1` remains sufficient in Phase A, but it is a **capacity setting**, NOT the Fast Weight isolation mechanism.
- Keep D1–D5, official Atomic Scene sampling, strict after-`env.step` `_check_success` latch1, raw15->env12/state/camera/policy, media/SR separation, and public Task/Episode output contract unchanged. Old431 outputs/checkpoints remain untouched.

### Phase A CPU acceptance — must be behavior-level, not mock-only declarations

1. Table of combinations `G in {1,2,3,4,8}`, `N in {1,2,4,7,18}`, `M=1`: exact logical plan, no deadlock, at most min(G,N) simultaneously running Episodes/Sim slots, max resident Sim count<=G. Cover `N<G`.
2. Reused Slot takes TaskA/Ep0 -> TaskB/Ep0 -> TaskA/Ep1: verify `close/make_env/reset` order, independent actual instruction/metadata, new Fast Weight Session W0, Server remains same. Same Task consecutive Episode needs `reset()` but not `make_env()` unless fault requires rebuilding.
3. Independent Session start/commit/End/Reset ACK and failure quarantine on success, valid behavioral failure, exception, and task switch. On reset failure the next Episode must NOT be admitted; after recovery new Session starts W0.
4. D5 barrier and Resume: one mid-round crash; ep37 invalid/missing retry only; valid ep38 unchanged; committed behavioral failure skipped; owner-pending not auto-retried; exactly one Core per logical index and original evidence bytes unchanged.
5. D4 3-errors-then-legal, 4-consecutive-errors skip, initial-success resampling, no Session creation before legal admission; D1 scoped faults and actual producer/consumer cleanup interleavings, no stale claim/late batch result able to commit.
6. Cross-Task seed/stream variation without forced scene replay; prove no identical-scene loop merely due to recreating Task environment with same seed. Run synthetic full18x50 scheduling and CPU resource/progress stats. CPU tests MAY use faithful fake env/server but must call the actual new production Scheduler/Slot/runtime APIs.

### Phase A handoff and STOP

Deliver concise architecture design note, implementation diff + tests, command/result/raw JUnit, source GitBlob SHA, and **new exact Formal Root implementation SHA + Child/Gitlink implementation SHA** (not Evidence docs HEAD). Clearly explain changed source/protocol and previous formally approved D1–D5 invariants. Then **STOP FOR GPT NEW-PAIR CODE GATE**; after reviewer approval the next independent DS CPU Gate remains separate. No GPU/real Sim/merge/900.

## 4. Phase B — scope agreed, but implement only AFTER Phase A Code Gate

Once Phase A has an explicit review/handoff decision, Codex shall begin **Phase B design first** for `M>=2`, dynamic microbatch, multi-Session Local-TTT. Phase B production code must pass a separate design Gate before edits because it changes tensor-level generation, transaction and concurrency; no claim that merely setting `max_sessions=M` enables batch inference.

- Implement truly concurrent independent Sim physics within each GPU Slot Pool, bounded pending inference queue, configurable `M`, `B <= M` as a preferred default but allow `B` independently configured subject to safe resource validation, and bounded batch wait (dispatch partial batch promptly, never wait for all M slots).
- Server per GPU tracks distinct `session_id` and per-session Fast State; each request's visual/action evidence causes **only its own Local-TTT scan**, then collate correct per-sample Local Prefix + observation/state/prompt/action conditioning. One **actual model batched generation call** for B>1 (not B sequential forwards passed off as batch); return ordered per-item actions/videos/status via immutable request/attempt/session IDs.
- Batch transaction: prepare/commit/abort semantics, no Fast Weight committed or action dispatched for a request whose generation/evidence validation failed; design all-or-none or independently provable partial-commit semantics explicitly. Handle mixed episode ends, stale response, retries, timeout, cancellation, Server crash/restart, media failures and out-of-order completions. Session reset must never delete/overwrite another Episode's state.
- Evaluate shape/mask/padding/Local Prefix batch mapping with model-owned scan; do not assume current `_local_memory_prefixes` already supports multi-item semantics. Existing `action_policy_server_robocasa.py::predict_policy_batch` explicitly rejects `mode=required`; remove only once Batch is genuine and CPU/then Owner-authorized GPU parity has been independently shown.
- Phase B CPU tests: W_A != W_B from distinct completed evidence, W0 fresh on each Episode, reset A preserves B, B=1/2/3 partial batches, exactly one generation call for B>1, request-to-result mapping when completion order differs, zero cross-session aliasing, abort/rollback under synthetic faults, D1–D5/Resume/fail-closed unchanged. Then fresh Formal design/code pairs and independent Gate reviews; **native GPU/EGL throughput and VRAM Canary only on separate Owner permit**.

## 5. Global prohibitions and process

- Do not modify training code, optimizer, DCP, checkpoint, dataset, physical task definitions, Vendor lock/patches, previous V1 evaluation semantics, old431 outputs, or production branches.
- No automatic GPU, server model load, RoboCasa simulator/native test, real 900 run, DS_PRO job, Code Gate closure, merges or destructive workspace command. Preserve independent stage gates and the Owner's earlier prohibition on unsolicited GPU action.
- Codex must explicitly ACK receipt of this request, cite exact source baseline, start Phase A code work in isolated branches, provide first formal pair and CPU Evidence, STOP. Publishing an issue/inbox is NOT itself proof the Codex agent is executing.

## 6. Owner decision / supersession

Owner approved staged implementation: **Phase A dynamic G/N + one Sim Slot/GPU first; Phase B multi Sim + multi Session + true dynamic Batch second**. New resource architecture supersedes the former unvalidated 18 Task-bound resident-Sim design only. The old Stage2 `APPROVE_CODE` remains a historical exact-pair source verdict; it does not transfer to a new Formal SHA or authorize the prior 18-Env native Canary. All D1–D5 scientific and evidence rules survive.
