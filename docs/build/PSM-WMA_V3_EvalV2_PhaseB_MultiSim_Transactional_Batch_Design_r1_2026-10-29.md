# Evaluation V2 Phase B r1 — multi-Sim, isolated Sessions, transactional native Batch

Date: 2026-10-29. **DESIGN CANDIDATE — REQUEST APPROVE_DESIGN.**

This document specifies future implementation. It does not declare Phase B implemented, a DS CPU Gate closed, or native Batch/EGL capacity validated. The accompanying executable protocol model is isolated under `tools/v3/eval_v2_batch_design/`; it uses symbolic scalar state and a fake vector generator, imports no production module, and is unreachable from launchers.

## 1. Authority and frozen source

- Phase A implementation Root: `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1`.
- Child/Gitlink: `d2c1bda62880dbeee196f70945e5bc430b73f4b6`.
- Exact source verdict: `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseA_fd7e43f6_d2c1bda6_FINAL_Code_Gate.md`, `APPROVE_CODE`, read after fresh V3 fetch at `36a5f157933d2f3f053023cd40796f81e6d60abb`. Independent DS CPU/native results remain pending. No repeat technical review of that unchanged pair is requested.
- Owner architecture: `docs/collab/chatgpt/requests/2026-10-28_V3_EvalV2_Dynamic_SimSlots_LocalTTT_Batch_Owner_Implementation_Directive.md`, section 4. D1–D5 canonical Owner contract remains authoritative.
- New design branch: `v3-eval-v2-batch-b-design-20261029`, based on the exact Phase A code, its author evidence and the latest canonical review documents. Current V3's older Child is **not** the development baseline.
- This delivery changes design, isolated protocol examples/tests and handoff records only. `scripts/`, `configs/`, `third_party/`, Child source and Gitlink must be byte-identical to the Phase A formal source.

Old training, V1 evaluation, old431 results, checkpoints, physics definitions, Vendor, DROID initialization and Local-TTT algorithm are outside scope. No merge, DS dispatch, GPU/model/real RoboCasa execution or900 run is authorized by this design delivery.

## 2. Actual source audit and reuse decisions

Line references below refer to the frozen pair, not upstream main. `source_audit.json` in the author evidence will freeze exact Git Blobs; source inspection alone does not prove native behavior.

| Frozen source | Existing capability / limitation | Phase B decision |
| --- | --- | --- |
| Root `scripts/robocasa_eval_v2/config.py:26`, `:118` | M1/B1 fields and explicit reject of other settings | Keep rejection until the new profile has genuine queue/Session transaction wiring; no guard-only patch |
| Root `scripts/robocasa_eval_v2/runtime.py:35`, `:177`, `:303`, `:564` | Physical Slot reuse, claim/fault fencing, owned-process cleanup, one executor per useful GPU | Extend physical identities to `(gpu, slot_index, generation)`; one Server per GPU, M separate Sim processes and concurrent control futures |
| Child `evaluation/robocasa_v2/scheduler.py:18`, `:46` | Episode-major plan and synchronized claim/commit/cancel | Reuse D5 and D1/D2 Core authority; no second scheduler or speculative lock fix |
| Child `simulation/robocasa/eval_v2_slot.py:81`, `:93`, `:130`, `:154` | Task switch, sampling grants, D4 admission, one Episode per reusable Slot | Reuse per physical Slot; fresh Session after admission, same task/changed task lifecycle preserved |
| Child `simulation/robocasa/eval_v2_adapter.py:26`, `:72` | Real env reset/step, strict success latch, raw action/session evidence | Add the Phase B client transport facade and media-ticket sink; retain action conversion and environment success authority |
| Child `evaluation/robocasa_v2/wire.py:6` | Inherited control socket, maximum frame 1 MiB | Keep small control messages. Do not tunnel16 composite RGB images/base64 predictions through it |
| Child `scripts/action_policy_server_robocasa.py:949`, `:1014`, `:1028` | Native batch collation exists; required mode explicitly rejected; non-Local batch has no per-Session result transaction | Reuse preprocessing/action-processing carriers. Add a required-mode transactional queue path, not a loop over serial `predict_policy()` |
| Same server `:1170–1252` | Serial path prepares under model lock, decodes video, then validates actions and commits one Session; no full HTTP response replay | New Batch path must separate action commit/delivery from optional video; include replay cache in atomic publication |
| Same server `:1390–1408` | HTTP handler overwrites legacy numeric `request_id` | Add a separate immutable inference identity; never use HTTP logging ID as idempotency key |
| Child `inference/robocasa_local_memory_policy.py:129`, `:202–249` | Canonical composite RGB/raw15, visual evidence cache and one-Session commit/abort/reset; prefix tuple has one item | Preserve parsing/model-owned encode/scan; introduce one transaction owner for fast, visual, frontier and response state |
| Child `inference/local_memory_online.py:139` | Independent Session records, cloned fast state, pending capability, lazy W0, contiguous evidence | Reuse algorithm and checks. Capacity alone is not Batch support; do not implement batch commit as a fallible loop of single commits |
| Child `model/generator/omni_mot_model.py:3698`, `:3728`, `:3883–3905` | Native generation accepts per-item seed list and optional prefix per sample; any prefix disables batched CFG | Keep model/generation authority. One call per policy microbatch; diffusion steps/CFG can entail multiple neural forwards internally |
| Child `model/generator/mot/memory_prefix.py:50–128` | Per-sample prefix mapping, compressed non-None carrier and offsets, mixed cold/hot support | Reuse; cold is `None`, not a zero token marked present. Validate mapping with real carriers in implementation CPU tests |

The native generator has useful Batch primitives. The HTTP service, two independent Session stores, replay semantics, resource admission and media delivery do **not** yet form a Phase B implementation. No change to denoising, attention equations, W0 initialization, evidence features, normalization or simulator ABI is proposed.

## 3. Resource and dispatch contract

`G=len(selected_gpus)`, `N=len(task_order)`, `M=sims_per_gpu`, `B=max_infer_batch_size` are distinct. One long-lived Cosmos Server/model per **used** GPU; at most M independent Sim processes per GPU, at most `min(G*M,N)` useful simultaneous Episodes in one round. Each Sim process owns one environment/EGL context and executes one Episode at a time. Threading only the existing single Sim process is insufficient.

Allocate useful physical slots in order `(slot_index outer, GPU order inner)` to distribute the first N assignments. Logical dispatch still uses `(episode_index, task_index)` only. Completion can be out of order; next-round claims are forbidden until all current-round positions are valid Core, Owner-pending, or the run has safe-stopped. There is no same-task parallel Episode in a round; N=1 cannot demonstrate Batch>1 under D5. Valid success and valid behavioral failure are immutable Resume skips; ordinary Resume also skips D4 Owner-pending entries.

First proposed implementation bounds, subject to Design Gate and later real capacity evidence:

| Field | Proposal / validation |
| --- | --- |
| Default profile | Existing default remains M1/B1; M2/B2 is explicit opt-in and NOT a validated launch recommendation |
| M and B | Each integer1..8 for initial implementation; independently configurable, including B>M. Actual batch <=min(B,M,eligible compatible requests). Caps are validation bounds, not H100 capacity claims |
| Batch wait | Default20 ms, configurable1..1000 ms, monotonic clock; earliest compatible ticket owns flush timer; never wait for all M Sessions |
| Outstanding work | One unique queued/inflight inference ticket per physical Slot; at most M total unique tickets/GPU, duplicate HTTP/poll calls share it |
| Wire limits | Bound encoded request32 MiB; bounded parsing/decoded image/evidence count (<=16 completed steps here); queue+inflight encoded bytes <=128 MiB/GPU; refuse/backpressure before allocation when no credit |
| Response cache | At most last committed action response per active Session, <=1 MiB/item; advancing frontier evicts prior response, older frontier is then rejected, never regenerated |
| Optional media | Max2 outstanding jobs/GPU and128 MiB CPU latent spool; explicit per-job expiry <=existing request timeout. No unbounded GPU latent cache |
| Timeouts | Existing prediction/actor/episode/run hard deadlines remain. A single absolute prediction deadline covers upload, queue, prepare, generation and response fetch; retries/polling do not reset it. Batch wait never extends it |
| Memory admission | Model/fast-state/activation/EGL/CPU spool and all in-flight payloads budgeted separately, scaled by M/B; keep explicit RSS/GPU-fraction guards. No claimed safe M from GPU count alone |

Expired/cancelled tickets are not silently removed while their Episodes keep running. They become explicit infrastructure faults. Queue admits oldest compatibility class first; flush when ready capacity reached or max wait reached, including partial B1/2/3 and when B>M. A deadline-expired ticket fails; do not launch a generation that can only complete after its already-expired budget. Backpressure is bounded under the same absolute deadline.

Preflight reports all selected GPUs and which are useful. The Phase A conservative all-selected-GPU admission behavior remains until explicitly changed and reviewed; do not silently weaken it as a Phase B performance adjustment.

## 4. Data plane, identities and correlation

Keep Root inherited-socket commands small (claim, task switch, admission, execute, cancel, cleanup proof). Each Sim Slot uses direct bounded HTTP to its GPU Server for observations/completed evidence. Add a **versioned Phase B endpoint** instead of changing V1 response semantics. Future interface:

1. Root registers an assignment capability after valid D4 admission; identifies run lease, Server epoch, physical Slot/generation, logical task/episode/attempt, session_id and episode_id. Sim creates fresh Session identifiers before registration. No Session can auto-open using only an arbitrary caller string.
2. `POST /v2/inference` validates envelope/payload bounds; queues once and returns a ticket (`202`) or the already committed result. `GET /v2/inference/<key>` polls that same ticket/result; native blocking client facade handles this without changing policy action execution.
3. `POST /v2/session/end` validates exact ownership, revokes the assignment, drains/aborts unfinished work and ACKs cleanup. `/info` exposes actual profile, Server epoch, capacity, frozen model/config/Checkpoint identities and supported protocol.

Inference identity is a canonical digest of `(protocol, run lease, server_epoch, physical_slot, assignment_generation, task, logical_episode, attempt_id, session_id, episode_id, consumer_frontier)`. Distinct payload fingerprint covers image/state/prompt, completed evidence, inference parameters, requested media and version. Same identity/different payload is an error; retries must resend the frozen payload. Full values are retained in predictions/status so a hash alone is not the only provenance. The isolated model uses a smaller equivalent identity for its limited symbolic scope.

Each native sample has an immutable ticket -> batch index -> response key mapping. Replies include the original identity, session/frontier and batch ID/index/size; client checks all before advancing its local evidence frontier or executing action. HTTP thread order, task name, physical GPU and legacy numeric request_id are not correlation authorities. Duplicate result deliveries do not cause a second `env.step` or Local update. Ticket polls never run a new generation.

Each physical Slot has a monotonic assignment generation and closed/open state in the Server epoch. Closing a Session permanently closes that generation; an old `reset=True` request cannot resurrect it after records/cache are released. Only Root can grant a strictly newer assignment. A Server restart uses a new epoch; old pending HTTP/results/ACKs are invalid. All active Sessions on that Server require owned process cleanup and explicit missing-Episode recovery, not reattachment to lost Fast State.

## 5. Session state and atomic Batch transaction

Share slow W0 read-only. Session state is `(episode_id, committed_frontier, fast tensor tuple or lazy None, local prefix, visual cache/fingerprint, last action response, version)`. Candidate tensors must be detached/cloned or otherwise proven non-aliasing; no in-place mutation of old committed tensors. Preserve model-owned Local scan (including FSDP registration when relevant). No independent reimplementation of Local update equations. A single GPU model executor serializes Local preparation, VAE encode, generation and optional decode; HTTP handlers do not run CUDA/model methods. This also protects current core telemetry/cache mutation. Sim physics in the M separate processes really runs concurrently.

Transaction state: `QUEUED -> SEALED -> PREPARED -> GENERATED -> VALIDATED -> COMMITTED -> DELIVERED`, or `ABORTED` before commit. No inference result is externally consumable before COMMITTED.

1. **Preflight:** verify active lease, parameters/compatibility, shape, finite state/actions and exact evidence frontier. Reject malformed independent tickets before choosing a batch. Duplicate pending tickets attach; cached committed tickets bypass batching entirely.
2. **Seal:** select ordered compatible tickets, at most one per Session; freeze participant ownership, predecessor versions, deadline and cancellation generations. After sealing, failure of any participant aborts every uncommitted participant. Previously cached replies are not participants.
3. **Prepare:** call existing model-owned visual encode/Local scan for each Session, producing candidate Fast/visual/prefix state without publishing. A serial loop of Local scans is allowed initially; a loop of policy generations is not. Cold request frontier0 has no completed evidence and supplies `None` prefix.
4. **Collate/generate:** construct ONE native generation batch; call `generate_samples_from_batch` ONCE with ordered prefixes and seed list. No B calls to serial `predict_policy`; no claim of one neural forward across all diffusion steps.
5. **Validate/allocate:** require cardinality, identity mapping, finite action values, exact horizon/raw width, valid Local status/frontier and unchanged W0. Pre-serialize ALL action/status responses and prepare a complete immutable replacement state bundle, including response replay entries. Any serialization/allocation/shape error aborts without dispatching actions.
6. **Final fence/publish:** under one transaction-owner lock, recheck all active capabilities, cancellation/deadline and predecessor versions; publish a single replacement bundle. All reads/updates/reset use this authority. Preallocate so no fallible per-item operation follows the commit point. A loop calling today's adapter.commit cannot provide this contract.
7. **Deliver:** futures/HTTP poll readers see committed serialized replies. Failure writing to the network does not roll back committed state; re-fetch returns the identical serialized result without encoding, Local scanning or generation again. Last-response eviction never permits recomputing an old frontier.
8. **Abort:** release every pending reservation/candidate, retain old committed Session state and fault diagnostics; release no new action. The bundle includes fast/visual/frontier AND response cache so a crash cannot leave an observable one-sided in-memory commit. A full Server process death loses all ephemeral state and is handled as a new epoch, not durable mid-Episode recovery.

Implementation must consolidate the two existing fast/visual store publication points behind one owner (new inference-only coordinator with prepared immutable bundles). Adapt old serial public API to one-element transactions where safe, retain its tests and off-mode behavior; no public get/commit/reset can bypass the new authority. Low-level state preparation may be reused. This is an inference lifecycle refactor, not a training/algorithm refactor.

## 6. Native Batch shape, mask, RNG and action contracts

| Item | Required mapping |
| --- | --- |
| Observation | Existing corrected composite uint8 RGB `[3,256,512]`, reflection padding/profile, left_wrist; per-item video carrier `[B][1]` with17 observation frames for chunk16 |
| State/action input | Actual per-item state15, existing clean state row; native action carrier `[B][1][17,max_action_dim]` via current `_build_action_input`, normally max_action_dim64, verified from loaded config rather than hard-coded |
| Prompt/task | Actual Episode instruction, domain, per-item SequencePlan and action processing record stay indexed together; differing legal text lengths use native packing |
| Local prefix | Exactly B entries, each `None` or `[K4,local_dim32]` for this frozen model; mixed positions preserved. Non-None compact carrier still maps via has_local_memory and native sample offsets |
| Guidance/masks | Same guidance/num_steps/H16/use_state/image profile/normalization/domain/shape configuration in a microbatch; compatibility key includes scientific model/config/runtime identity. Preserve native SequencePlan/masks; no unconditional padding sample that enters loss/action output |
| Seeds | Preserve existing literal per-item inference seed (current server uses cfg.seed for each item). Never add batch index, completion order or GPU ID to it. Simulation scene sampling seed is a separate recorded identity |
| Native output | Associate `samples['action'][i]` with original sample i, invert existing normalization/action processing, remove only clean state row0, enforce finite `[16,15]`; retain raw15 -> env12 ABI at the existing adapter |
| Caches/CFG | Keep current generator behavior: any Local prefix disables unsafe fast paths/batched CFG. Cold None is semantically distinct from a present zero prefix; mixed cold/hot mask/offset tests mandatory |

Only model/config-identical requests share a batch; no cross-checkpoint/model/Local-required/off mixing. Native compatibility of mixed cold/hot, text lengths, parameter dtypes and batch-size-dependent kernels remains a CPU/native GPU acceptance item, not a proven fact from the signature. B1 must retain Phase A numerical semantics. B>1 need not be bitwise identical to B1, but evidence, prefix/sample mapping, action ABI and Local updates must be correct. New tolerances require explicit review; historical frozen B1 Source/Target/thresholds are untouched.

## 7. Cancellation, cleanup and D1–D5 recovery

- Pending one-Session reset cannot race a CUDA call or delete a co-member's Fast State. Cancel is an independent flag observed by the single executor before publication; sealed-batch cancellation aborts all members. Reset ACK is issued only after pending work is absent, only that Session's state/response ownership is reclaimed and its generation closed. Retain one exact closed-generation ACK receipt per physical Slot, so a lost end ACK can be re-fetched idempotently; it never reopens a Session or closes a newer assignment. Root grants no new assignment before verified cleanup.
- A GPU kernel may not be safely preemptible. Deadline expiry does not justify starting another batch concurrently or declaring the Slot clean. Quarantine the affected Server and all its Slots; terminate only owned process groups with existing bounded SIGTERM/SIGKILL/reap proof. Recreate only during explicit Resume/recovery with a new epoch. Unknown cleanup is a fault, not a positive ACK.
- Initial implementation uses existing global safe-stop on uncommitted batch/Slot infrastructure failure. All uncommitted affected logical assignments receive scoped faults; other GPUs' already valid Core stays immutable. Do not transparently retry a failed batch while pretending the same Episode never faulted.
- Resume first proves owned processes/Sessions are gone, obtains fresh independent health and uses D1 resolution rules. Pre-Core failures require new Attempt of the SAME missing logical Episode; valid earlier/later success or behavioral failure are skipped. Post-Core process faults require health-only recovery and do not cause rerunning that Core. Preserve the Phase A final zero-exit qualification fix.
- D4 initial-success filtering and4-consecutive-recoverable-init-error Owner-pending happen before Session/inference registration. Illegal boolean/physics/EGL/process faults retain their current classifications; error must not become behavioral failure or enter SR denominator. Owner-pending release is explicit, ordinary Resume skips it.
- Scene grants use the reviewed Phase A diverse stream/reset protocol; extra Slots consume coordinator grants atomically, never clone identical task RNG state. Record physical Slot, actual seed/stream/grant/reset/layout/style/fixture where available. No requirement to reproduce an interrupted scene, no whole-task replay and no mandatory newly invented per-Episode seed scheme.
- Existing simultaneous commit/cancel lock is retained; the previously withdrawn Stage2 finding is not reopened. Phase B's new inference bundle transaction is a separate boundary upstream of immutable Episode Core commit.

## 8. Optional media cannot gate actions or SR

Do not copy today's serial decode-before-action-commit order into Phase B. Validate/commit/release action/status first. Optional generated-video jobs use committed ticket identity and a bounded media spool; response contains a media ticket/status, not mandatory PNG frames. The native adapter's media fetcher associates each result with exact Episode/attempt/replan and writes one original MP4. No videos_view duplication, automatic FFmpeg strict decode or media requirement for Core/SR/Resume.

Use the same serialized GPU model executor for model-owned Wan decode, at lower priority when inference is idle, with bounded per-job time and CPU latent byte credit. No unreviewed second GPU model, concurrent mutable VAE calls or unbounded latent retention. Preparing an optional CPU spool must not become a prerequisite for committing valid actions: if no credit or conversion fails, drop/report that media item. Native feasibility/latency is still a Canary question.

On Episode end, cancel/expire outstanding media and join its bounded sink before staging/Core directory publication. A late media response cannot recreate an old staging directory, overwrite a new attempt or block round progression indefinitely. Media decode/write errors are diagnostics; fatal CUDA context/Server loss is an infrastructure fault affecting qualification, while already valid Core remains preserved. Off/first/all policies are explicit; 'all' requests every replan, with any failed/dropped media listed honestly rather than changing SR. No promise that optional media will always be available.

## 9. Manifest, observability and compatibility

New Phase B runs use a new protocol/profile and independent namespace. No old431 migration, no rewriting historical manifests and no implicit cross-source Resume. Scientific identity includes exact source pair, Checkpoint/config fingerprint, task protocol/order, action/state/camera/Local contract, inference settings, scene protocol and effective execution profile (G/M/B, batching wait, per-item noise convention). Freeze it for same-run Resume; changing concurrency/profile is a new-run decision until separately designed. Record actual physical GPU IDs and ownership epochs as execution provenance. Do not silently reinterpret Phase A runs as Phase B.

Per committed prediction record: correlation fields, batch ID/index/size, prefix presence, evidence range and pre/post frontier, prepare/encode/scan/generate/action validation/queue latency, response-replay bit, media ticket/status. Periodic bounded telemetry: queue depth/bytes/high-water mark, batch histogram/flush reason, oldest request age, live/closed Session count, quarantine/reset ACK counts, fast/response/media memory bytes, actor count, VRAM/RSS, model-load count and throughput. Do not hash full checkpoints per batch or scan all Core files per scheduling decision. No per-step full tensor/hash dump by default; first bounded diagnostics can hash frozen candidates without altering state.

Terminal progress keeps separate Slot/Session/Task/Episode identity and phase; batch telemetry must not misreport B diffusion calls as one. Assertions on ownership, mapping, finite actions, cardinality, exact frontier and reset ACK are hard stops. Throughput, batch utilization and normal task failure can be observed without stopping if safety remains intact.

## 10. Minimal future code boundaries

Only after APPROVE_DESIGN:

1. Root evaluation config/resources/runtime: M Slot IDs/futures and per-GPU Server registry, new profile/limits/identity and progress fields; preserve D1–D5 Store authority. No changes to training or existing V1 Queue required.
2. Child inference-only queue/transaction coordinator plus bounded HTTP Phase B endpoints: request registry, single model executor, canonical idempotency, all-or-none bundle. Adapt existing Local adapter/online-memory storage to common publication owner with B1 regression coverage.
3. Child server native collation: reuse prep/action normalization, native prefix carriers and generation; no model-core equation changes. New per-item result validation/status/async media.
4. Child V2 native client/Slot transport facade and media sink: exact tickets/deadline/cancel/end ACK, no cross-Session state, concurrent independent Sim processes. No robot/controller/physics/vendor edit.
5. Production CPU tests exercise actual modules and existing Phase A regressions. New exact Child then Root candidate commits; static/CPU evidence; GPT Code Gate, then independent DS CPU. No direct V3 merge.

Prefer two reviewable implementation increments within the approved design: (i) inference transaction/queue/client with real CPU tensors/fake generation, M1 native compatibility, (ii) M>1 runtime and native batch collation/media integration. Each has its own exact pair/evidence and no 'supported' flag before complete wiring. Stop and seek incremental design review if atomic owner consolidation or native generator requires materially different semantics.

## 11. Acceptance matrix and stop conditions

| Gate | Minimum evidence | Meaning / stop |
| --- | --- | --- |
| B-DESIGN (this delivery) | Source audit, this complete contract, symbolic CPU protocol tests with finite queue clock/transaction faults | GPT APPROVE_DESIGN only; no native claim |
| Implementation CPU: transaction | Real tensor W_A!=W_B, disjoint storage, W0 unchanged; reset A preserves B; fresh returns lazy W0; stale lease/epoch; prepare/member1/member2/generate/finite/serialize/publication failures; no partial fast/visual/cache commit | Any mismatch blocks Code Gate |
| Implementation CPU: true collation | Actual production batching API with fake generator observes exactly one call for B1/2/3, partial and B>M; actual native prefix carrier/mask offsets including `(hot,None,hot)`, state/prompt/domain/action rows, reordered transport completion | Fake call counter alone does not prove native generator works |
| Implementation CPU: deadlines | Fake clock wait/backpressure; real owned-process bounded timeout/cancel/reset ACK; replay after socket loss; reset/cancel before/after commit; Server death affects every live Session; no orphan, unrelated process untouched | No budget enlargement to hide cleanup failure |
| Implementation CPU: D1–D5 | Existing Phase A production regressions, G/N/M combinations with N<G*M, real OS Sim-process overlap and one model owner/GPU, full900 synthetic order/barriers, sparse37 retry, later38 preserved, valid behavioral failure skip, Owner-pending skip | Full900 here remains synthetic, never real SR |
| Implementation CPU: media | Decode/PNG/disk/spool failure and late response, off/first/all, independent core commit, no auto-FFmpeg, no duplicate files or stale staging resurrection | Media missing alone does not fail SR |
| GPT Code + independent DS CPU | New exact Root/Child, raw JUnit/logs/source hashes, then DS replay of frozen commands in separate environment | Neither source nor author pass substitutes for DS |
| Native Canary (separate Owner permission) | Begin M1/B1 on new pair; M2/B1 concurrent Sim and independent fast state; M2/B2 real native generation B=2; mixed cold/hot and early terminal/partial batches; task switch/reset/session cleanup; bounded media | Native API, EGL contexts, real tensor offsets and CUDA memory not proven today |
| Native quantitative checks | One generation invocation contains B>1, prefix enters action path, W0 unchanged, evidence-isolated W_i, reset A preserves B, B1 fixed-input reference under reviewed tolerance, queue tail latency/RSS/VRAM, finite actions, no state drift, Save-independent evaluation Resume | Stop on NaN, mapping/lease/frontier/cleanup errors, OOM or context failure; preserve evidence |
| Formal benchmark | Prior gates + separate Owner authority + new namespace | No automatic900 launch; completed Core determines SR, not video |

Use the smallest native experiment set: M1/B1 reference and resource baseline, M2/B1 isolates physics/Session concurrency, M2/B2 demonstrates actual batching; one bounded M3/B3/partial probe only if M3 support is requested. No old Index8/Packed128 equality rerun, retraining or frozen B1 threshold adjustment.

## 12. Isolated protocol model scope and reproducible CPU command

The model covers immutable symbolic fast/visual/response publication, finite-output and mapping abort, cancellation before publication, exact response replay, bounded eviction, retrievable end ACK, closed generations/epochs, literal noise-seed mapping and fake-clock partial-batch queues. Canonical symbolic keys include lease and frontier; the production canonical JSON digest includes the fuller identity in section4. The model intentionally does not implement HTTP threads, tensor math, actual scan/encode, FSDP, physics, scheduler/Core filesystem transactions, memory estimates or media delivery. Production CPU tests in section11 remain mandatory; symbolic seed mapping is not proof of native CUDA RNG independence.

Working directory `/workspace/psm_wma`; CPU/offline only, no Checkpoint or dataset inputs. Existing CPU tool environment, external writable caches. Example exact check (author evidence records the executed argv/environment separately):

```bash
env CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  HF_HOME=/tmp/psm-eval-v2-phase-b-design-20261029/cache/hf \
  MPLCONFIGDIR=/tmp/psm-eval-v2-phase-b-design-20261029/cache/mpl \
  XDG_CACHE_HOME=/tmp/psm-eval-v2-phase-b-design-20261029/cache/xdg \
  /workspace/.venvs/psm-wma-cpu/bin/python -m pytest \
  --noconftest -c /dev/null --rootdir=/workspace/psm_wma \
  -p no:cacheprovider -q tools/v3/eval_v2_batch_design/protocol_model_test.py \
  --junitxml=/tmp/psm-eval-v2-phase-b-design-20261029/final/junit.xml
```

PASS requires zero failed/error/skipped tests, Ruff0.12.7 check and format, syntax checks, exact frozen production tree/Gitlink comparison, and source/evidence hash readback. Any failure is preserved and corrected only within design/protocol scope. No full Phase A255 rerun is needed for a design-only diff. Evidence path: `docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_design_author_cpu/`.

## 13. Design verdict request

Request GPT **APPROVE_DESIGN / REQUEST_CHANGES** for the new Design Root and unchanged Child/Gitlink, not APPROVE_CODE. In particular review the single-bundle atomicity, bounded idempotency, closed-lease fencing, queue/deadline policy, asynchronous media, profile identity and inherited D1–D5 behavior. Once published, Codex stops for that verdict. Phase A independent DS CPU can proceed on its existing exact pair without inheriting this design or invoking any Phase B code.
