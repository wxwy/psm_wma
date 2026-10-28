# RoboCasa Evaluation V2 r2 — D1–D5 design and isolated CPU prototype

2026-10-28 Asia/Shanghai. Status: REVIEW CANDIDATE, not a production framework.

## Authority and scope

The unique latest requirements are `docs/collab/chatgpt/requests/2026-10-28_V3_RoboCasa_EvalV2_r2_CANONICAL_LATEST_OWNER_CONTRACT.md` at latest V3 `b59d1faf486765271295a00ee5e20e4d239e0163` (initial D1–D4 ACK bound9858e70b; D5 ACK published separately before its source edits). Reading ACK was committed/published BEFORE changes to the prototype. Prior formal r1: `dc750f8e258d10a33e7a195cf907926b1c98bd7f` / Child `746c5cf2f2324104a62fb71510343aa40d3976c5`, REQUEST_CHANGES. New r2 isolated candidate, no merge to V3.

This r2 explicitly supersedes r1 whole-Task replay and the old Owner addendum requiring fixed per-Episode SHA seeds, RNG snapshots or scene reproduction. It also supersedes automatic skipped-slot retry and all media-completeness gating of SR. Old reviews and r1 evidence remain immutable. Existing431 results are not inputs, migration targets or acceptance dependencies. Production/Child/vendor/train/model/DCP/simulator source is unchanged. This is only a design + pure CPU fake-environment prototype; no runtime/GPU/Canary authorization.

## Scientific contract and public structure

Fresh immutable namespace, versioned new sampling/admission protocol,18 Tasks×50 logical slots. The manifest locks model/Checkpoint, source pair, runtime/config/Task metadata hashes, Task horizon, raw15/state15,16 Action Chunk,17 observation frames,left_wrist, Local mode and success_latch1. The prototype schema is v2 and rejects v1/old431 admission. Synthetic Task names/horizons/Hashes are explicitly not real robot identities.

Only typed `env._check_success()` observations AFTER completed `env.step()` establish success; first True latches. No success at the official horizon is valid `failure` (behavioral failure), forever immutable like success. Predicate/runtime/required Local cleanup/core persistence errors are Invalid/Interrupted, never policy failures. Initial-success admission is separate and cannot supply these post-action observations. `result.json` is published ONLY for valid success/failure after core/Local chronology; invalid details remain in private attempt evidence.

- `manifest.json`, `summary.json`, `episodes.jsonl`: public experiment definition and rebuilt reports.
- `tasks/<Task>/episodes/ep_NNN/result.json`: one immutable valid Core outcome, exact actual instruction, steps/checks/replans, sample seed/reset index, stream/worker/attempt/manifest identity.
- Stage2 native writer will place actions/predictions/Local evidence, scene provenance and `media/{rollout.mp4,generated/...}` directly in each logical Episode directory; the isolated prototype does NOT implement these writers.
- `_internal/tasks/<Task>/`: immutable task/slot init intent+ready, streams, numbered per-slot attempt claims/events, explicit Owner permits, process errors, cleanup/recovery/resolution receipts. Diagnostic artifacts of failed attempts stay private; never overwrite a completed public slot. Stage2 must route uncommitted native core/media into attempt staging and publish/move the selected attempt once (no duplicate videos).
- Logs/control state stay private and out of scientific result authority. No legacy Batch/Invocation/Attempt catalog scans or adoption. No `videos_view` copying. Public summaries/indexes are reproducible derivatives; corrupted derivatives cannot complete a slot.

No automatic ffmpeg decoding in admission, Resume, final summary, revalidation or SR. Missing/bad videos cannot invalidate, resample or retry a Core outcome. Encoder process isolation, bounded queue/spool/drop policy, timeouts and Local cleanup independence are required Stage2 native work; `try_media` here only checks synchronous callback/RNG behavior, not real resource bounds/CUDA equivalence.

## D1: scoped fault state and explicit resolution

Error records are immutable and bind Task, worker, stream, exact attempt when relevant, phase/message/time and whether Core was committed at fault time. The prototype uses logical CPU worker IDs; Stage2 must add real PID/start identity/owned process groups and exact server/session identity rather than pretending the coordinator PID is a simulator PID.

`OPEN -> RESOLVED_BY_VALID_RETRY` requires all of:

1. An immutable positive cleanup receipt from the owned process/session probe for the failed stream (processes gone AND Local sessions closed). Lease acquisition alone is not cleanup.
2. A different stream/worker, created after cleanup; independent positive runtime health receipt. Other-task/old/predating receipts reject. Unsafe/negative probes never produce a receipt.
3. A valid atomically committed replacement for precisely the same previously missing logical index, from the certified new stream and a different attempt. The old fault is retained; a separate immutable resolution links all proofs. No global clear flag, no summary refresh as resolution, no deleting diagnostics.

For faults AFTER a valid result, the result cannot be rerun. `OPEN -> RESOLVED_EXECUTION_ONLY` requires the same verified cleanup/new-stream health sequence and an explicit execution-resolution receipt. It does not change success/failure/SR. A complete Task may create a recovery-only stream without executing any Episode. An attempt-scoped fault before Core commit cannot use this health-only shortcut. A Worker/task-scoped fault still requires cleanup+fresh health; any missing slots continue to block coverage.

Current unresolved faults stop further dispatch on that worker stream. Safe restart requires owned cleanup before creating a new stream. Other Tasks remain independently inspectable/qualified; global clean qualification remains false while any current unresolved fault exists. Later faults on a recovery stream are new blockers, not erased by an earlier resolution. All resolution files are verified against their immutable error/certificate/replacement; no content is assumed trusted merely because a filename exists.

Clean qualification additionally requires positive owned-worker/session cleanup receipts for every stream; all results committed while Workers remain open are provisional, not clean-qualified. Critical fault evidence is published BEFORE an unsafe/Invalid terminal attempt event, so a crash between those records cannot lose the fault.

`scientific sr` is numeric only when all900 Core results valid. A late fault can therefore coexist with numeric SR, but `results_qualified=false`, and must be explicit in reports. History counts include resolved and unresolved faults. Core scientific values are not rewritten because of process faults. Every output remains `prototype_only=true`, `runtime_gate_approved=false`, even when synthetic `results_qualified=true`.

## D2: initialization and Core commit transactions

One coordinator holds the original run lease, with inode/source/manifest checks. Worker responses are accepted only through the current leased stream and exact persisted slot attempt token. Lease re-acquisition never automatically revives an old worker token.

Task and slot initialization both use **immutable intent -> directories -> immutable ready**. Intent and ready bind exact manifest/Task/index. No producer token is issued before ready. If interrupted after intent or directory creation, Resume may finish ONLY while no producer evidence exists. Nonempty unready structures, foreign identity, contradictory intent/ready or lost directories after ready are explicit BLOCKED, with all bytes preserved. This fixes r1's state-before-directory permanent crash gap for provably empty initialization. Task/Episode directory creation/fsync and ready publication have injected crash tests.

Slot attempt claims are immutable generation-numbered records. A crash after claim but before returning token leaves a known abandoned attempt; after owned cleanup, a new attempt can be claimed for only that slot. Claims contain actual stream/seed/worker/lease and an exact Owner permit when a prior skip requires it. Core/ledger JSON remains limited to256KiB, strict UTF8/duplicate-key/nonfinite rejection. Only derived `summary.json` writers have a separate finite16MiB limit so50 skipped slots with long four-error diagnostics cannot break final PARTIAL publication. This is not a larger Core admission limit; oversize Core and report-limit misuse remain rejected. Histories remain private/immutable and can be indexed by future production reporting if exceptional retry history exceeds this reporting bound.

Pending temporary files are never commit authority. Ambiguous state cannot be repaired by deleting files or accepting a different manifest.

Initialization events are numbered, checksum-protected, exclusively published and contain full attempt identity and timestamps. `INIT_BEGIN` is durable BEFORE calling reset. Crash before completion leaves an unknown reset outcome, never an invented error, success or preserved scene. After cleanup, a new attempt records interruption and samples a new scene. Completed initialization errors and budget consumption survive restart. No ad hoc in-memory counter is authoritative.

Valid Core Commit is a single immutable exclusive publication (`write+fsync -> link O_EXCL semantics -> parent fsync`), checksum/typed-schema/admitted-scene identity validation, under the coordinator lease. Crash before publication leaves the slot incomplete; crash after publication means it is complete even if no acknowledgement or summary followed. Reopening cannot rerun or overwrite it. Cross-slot/worker/attempt/stream/seed/reset mismatches, stale asynchronous results, duplicate commits and out-of-plan paths reject. This prototype transaction is NOT proof of real DCP/filesystem/runtime behavior.

## D3: sparse logical slots, not stream replay

A normal fresh Task may retain one environment with literal Task seed and perform its resets/steps across Episode-major rounds. This does NOT permit dispatching all50 episodes as one Task batch. No per-Episode derived hash seeds, mandatory environment reconstruction, RNG snapshots or reset-only prefix replay.

On interruption at logical37: valid0..36 keep original paths, bytes and inodes;37 gets a fresh attempt and legal new scene, then38..49 continue. A new Task stream records actual seed (explicit caller value or generated resume seed), stream/worker identity and `resume_new_stream_no_scene_reproduction`. Reset index restarts at0 in this new stream; it is NOT falsely reported as37 or as original continuous RNG. Multiple accepted scenes/rejected resets in a stream have monotonically increasing actual reset indices. Seeds and boundaries remain per-result and are explicitly listed per Task in `sampling_streams`; a mixed-stream Task cannot be advertised as uninterrupted scene-equivalent execution.

Storage accepts valid slots after a gap. Dispatch selects the smallest eligible missing index, skipping blocked slots without authorization. A valid behavioral failure is never eligible; neither media loss nor desire for a higher score can authorize its replacement. Extra workers/lease restarts cannot commit a stale attempt into the right-looking logical directory.

## D4: initial-success admission and four consecutive errors

Before model inference, action or Local Episode begin:

1. Persist `INIT_BEGIN` with actual reset index and slot sampling count, then call reset and a STRICT typed initial `_check_success()`.
2. False -> `ADMITTED`; now native policy/Local episode may begin. True -> `DEGENERATE_INITIAL_SUCCESS`; reject without Core success/failure, model/action/Local update. Any legal precheck, including rejected True, resets the consecutive initialization error streak.
3. Reset/predicate exception or illegal type -> explicit phase/type/message/time/Task/index/attempt/seed/stream/sample evidence. A recovery callback must positively establish a safe environment; no blanket Exception swallowing or class-name-based EGL retry. Safe recoverable error increments consecutive count; fourth -> `SKIPPED_INIT_ERROR`. Count is NOT combined with degenerate rejections and survives restart. Error recovery can rebuild a safe env; the CPU ledger records an explicit `ENV_REBUILT` event. Reset indices are worker-stream sampling ordinals, with environment-lifetime boundaries recorded separately. Native Stage2 must preserve those boundaries and the observation returned by the admitted reset; it must not reset a second time before querying the policy or call rebuilt state continuous original RNG.
4. Unsafe resources, unknown ownership, failed Local cleanup, destroyed EGL/hardware or process death -> Invalid + Process Error, safe stop; never use four-strike skip to hide resource damage.

Proposed frozen prototype limit: **32 total initialization samples per logical slot authorization round**, counting every persisted INIT_BEGIN, including aborted/unknown attempts. This finite constant is in the manifest. Reaching the budget without a legal scene gives `SCENE_ADMISSION_EXHAUSTED`, not policy failure or initialization skip. Initial successes and errors are counted separately. r2 asks GPT to accept this concrete limit; no Owner statement is misquoted as specifying32.

After the fourth consecutive recoverable error, stop that slot, preserve all four diagnostics, safely continue38..49. A skipped slot cannot automatically Resume. An explicit Owner reference creates a one-use persisted permit bound to exact prior attempt/manifest/Task/index; only that missing slot can start a new budget round. Scene-admission exhaustion is conservatively also manual-authorized before retry, rather than bypassing a run-wide budget by repeated restarts. Existing valid outcomes remain immutable even with an Owner permit API call. Authorization here records an external Owner decision; it is not an authentication UI or self-granting permission for an agent.

Reports list missing/skipped IDs and diagnostic references/details, actual seeds/streams, initialization errors/rejection counts and admission denominators. Any skipped/Invalid/Pending/Interrupted/exhausted slot => full `sr=null`; `partial_sr_valid_only` is explicitly conditional on the smaller valid denominator. Rejection filter is a new benchmark protocol, not equal to old unfiltered historical SR. Final episodes index has exactly one position per Task/index even with gaps.

## D5: Episode-major scheduler, actual admission and round barrier

The manifest preserves **Owner-provided Task order** (never alphabetically re-sorts it), with `task_order` and versioned schedule bound into the digest. The single logical plan is `(ep0,Task0..17), (ep1,Task0..17), ... (ep49,Task0..17)`. Public `episodes.jsonl` uses the same order. Both Fresh and Resume start at the beginning of that same plan, reading authoritative Core+attempt+admission evidence for each position.

The new isolated `RoundScheduler` actually calls the Store to acquire attempt tokens and commit responses. It is not just a sorted task list. `dispatch()` skips typed valid success/failure and unresolved Owner-pending slots, then issues one token-bound message to an idle worker. Same-round Task dispatch follows frozen index order; completion may be asynchronous. Physical workers have sticky Tasks (`task_order_index % worker_count`). If the next Task's GPU is busy, another free GPU waits rather than changing dispatch order. This bounded head-of-line cost preserves strict ordering and still allows three active same-round Episodes.

Each worker holds at most one in-flight slot. A round cannot advance until all18 positions are validated Core commits or explicit Owner-pending deferred holes AND all issued claims have been returned. `RUNNING`, directories, videos, missing Core, Interrupted and Invalid are not terminal success dispositions. A failure without a valid result requires explicit cancellation/safe stop; the scheduler never promotes it to DONE to pass a barrier. Dispatch/Finish/Barrier/Cancel records are immutable invocation/lease-scoped diagnostics. They are not authority to skip a slot on restart: Core and Owner authorization state are rechecked from the original plan.

Store claim and Core entrypoints require scheduler-issued slot tickets while a scheduler is attached; direct calls, stale invocation replies and two GPUs claiming one slot reject. Same-round claims commit through one coordinator's lock/lease. Atomic Core commit before crash wins even without a FINISH acknowledgement; Resume skips it. Before-commit crashes retry only missing positions after owned cleanup. All previous coordinator streams require explicit cleanup before a replacement scheduler can dispatch. Cancellation is logged with the in-flight list and does not simulate process death/cleanup or advance the barrier. Native runtime cleanup remains Stage2.

### Bounded model, environment, EGL and Local lifetimes

Proposed runtime for GPU4/5/6: **three persistent checked Action Servers/model loads**, each with at most one active Episode Local session. At a Task/Episode switch, require confirmed `end`/reset/zero-active-session acknowledgement before starting the next session; failed ack quarantines the server/stream, never blindly reuses it. Task environment state and model Local state are separate. Do not transport a previous Episode's Fast State to another Task or reuse the same unended Local session.

Keep a bounded **18 persistent Task environment processes**, six assigned to each GPU for3 workers; one runnable Episode per GPU, other Task processes wait for coordinator commands. Each environment is constructed lazily on its first dispatched eligible slot and retained across rounds, so no900 model loads or900 routine EGL rebuilds. Independent environment processes isolate Python/NumPy/MuJoCo RNG and retained simulator state; paused Task scene streams can continue their resets without sharing process-global RNG with other Tasks. Model-server RNG can legitimately interleave across Tasks; do not call this bitwise-equivalent to prior Task-major policy RNG.

This is an explicit resource proposal, NOT proof18 real environments fit. Stage2 config must cap total resident Tasks, contexts per GPU (6 for18/3), total environment RSS, GPU renderer+model memory and active processes. Before formal use, an independently authorized Canary must measure construction/steady RSS, VRAM/EGL contexts and Local isolation, including all18 retained Task contexts and clean teardown. If required retention cannot fit the declared bounds, report `BLOCKED_RESOURCE` and seek an explicit revised resource/sampling design; do not silently evict every round or build900 contexts. Larger GPU count can reduce per-GPU retention, but must not change plan order. Bounded exceptional environment reconstruction must record a new environment/stream boundary and actual seed, with legal new scene admission; Owner does not require previous scene reproduction.

Resume can change the available GPU set only after cleanup of all old owned processes/sessions. Task positions remain identical; completed Core stays untouched; only missing/released positions get new streams/actual seeds and new sticky assignments. Runtime server reuse, task context retention/rebuilds, GPU assignment, sampling reset indices and boundaries belong in manifest/provenance/runtime logs. The sampling/schedule version is a new Episode-major filtered protocol; do not advertise the unfiltered historical Task-major results as the same benchmark.

The CPU lifecycle witness counts three **mock** model starts and18 mock environment constructions for900 actual prototype dispatches; it is not a model/EGL performance measurement. Actual environment/process allocation, RPC, resource admission and Local end/reset probes are not implemented by this isolated scheduler.

## Acceptance and next boundary

| Requirement | Isolated CPU evidence | Native/DS evidence still required |
| --- | --- | --- |
| D1 old retry resolves; current/late fault blocks; cross-Task isolation | immutable fault, negative cleanup, health-only refusal, valid retry, explicit late recovery | PID/start/group ownership, Local ack and runtime health |
| D2 Task/slot claim before/after intent/dir/ready; attempt/coordinator crash; Core before/after publication | injected boundaries; prefix/other Task bytes and inodes unchanged, ambiguity BLOCKED | native actions/Local evidence staging and real FS failure |
| D3 Episode37 retry only; later valid gap slots; duplicate/stale result refusal |0..36 preserved;37 only if uncommitted,38..49 not replayed | real legal resampling and stream reporting |
| D4 three errors then legal scene; fourth skip and38..49; legal True resets streak | phase/type/time/seed events, persistent counters, explicit Owner permit | RoboCasa strict precheck before inference/Local; environment recovery policy |
| D4 all initial True bounded; unsafe stop; crash during init |32 cap, no fake success, no fabricated init error, null SR | actual NavigateKitchen/PandaOmron canary |
| D5 frozen900 order /3 asynchronous Workers/round barriers/crash Resume | actual Store claim/commit path, success+failure skips, skipped37+valid38, stale/duplicate ticket rejection, cancellation | resident models/envs, EGL/Local/RNG isolation, measured context capacity |
| SR/media/storage/identity regression | fake900, conditional partial SR, media error no retry, exact source/lease, corrupted/symlink/foreign data | bounded media worker/spool, Local chronology, raw15->env12 native path |

New exact Design/Prototype Root and unchanged Child must be published with raw JUnit, static checks, commands, source hashes, real r1->r2 diff and ACK. Prior65 tests are old r1 evidence, not added to r2 counts. Removed r1 assertions specifically require withdrawn whole-Task replay/continuous prefix/permanent fault poisoning/missing-init permanent BLOCKED; their r2 replacements cover new Owner contracts. Environment authority, identity, no legacy adoption, atomicity, lease and media/RNG checks remain.

STOP after candidate publication/readback. GPT D1–D5 incremental Design Gate first, then separately authorized production implementation, DS independent CPU, actual small Canary, and Owner new900 execution authorization. No native production entry or real rollout is delivered at this stage.
