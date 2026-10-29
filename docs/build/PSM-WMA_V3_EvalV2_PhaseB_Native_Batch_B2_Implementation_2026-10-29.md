# Phase B increment2 — multi-Sim Sessions and native Batch production candidate

2026-10-29. Isolated Root/Child `v3-eval-v2-batch-b2-20261029`. **Author implementation; request new incremental Code Gate.**

## Frozen authority and limits

First increment Code Gate APPROVE_CODE: Root `dc7757922d7273f50f3de23363d41e12e157a07f` / Child `4a938e41b0c335baca1c1d8f1caabc433b0e2001`, detailed GPT report `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_B1_F1_dc775792_4a938e41_Incremental_Code_Gate_APPROVE_CODE.md`, fetched and read at V3 `66a5b99c0a23312525ccbdc0fadb4655bc7d0b19`. B1-F1 CLOSED, B1-P1 WITHDRAWN. Phase B r1+r2+r3 Design remains exact Root `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` APPROVE_DESIGN. No repeat audit or new verdict for those unchanged Pairs.

Owner authorizes this second isolated production increment and CPU checks, then new exact Root+Child/Gitlink/Evidence and GPT incremental Code Gate STOP. Independent DS CPU is consolidated on the final complete candidate. No canonical V3/Child merge, GPU/model weight/DCP/RoboCasa/EGL/900 run, training/Vendor/equation/history change or DS dispatch. Later docs/Evidence HEAD never substitutes for the formal implementation Pair.

## Production path and ownership

`run_robocasa_eval_v2.sh` → existing CLI/Config/identity → unchanged RoundScheduler/Store → independent persistent Sim processes → admitted coordinator registration → assigned transaction facade → bounded inference queue → **one** native `generate_samples_from_batch` invocation → all-or-none snapshot → exact per-Sim response/ACK → unchanged native raw15→canonical15→env12 loop and environment `_check_success()` → Core commit. Existing legacy and approved B1 service profiles remain available; Phase A M1/B1 is still the default. Phase B is explicit `execution_profile: phase_b`, never a guard-only enabling of legacy `/predict_batch`.

- Useful physical Slots are assigned `(slot_index outer, selected GPU order inner)`, at most `min(G*M,N)`. One Server/model per used GPU, M separate Sim processes/GPU, one environment per Sim. Same-Task Episodes reuse the environment; Task switches close/rebuild it in the same process. This bounds EGL contexts by useful Slots; it does not claim all18 environments are resident or eliminate required task-switch XML construction. Actual capacity/cost remains Canary evidence.
- The existing D5 scheduler still dispatches `(Episode Index, Task Index)` and has the same cross-round barrier. Existing success/behavioral-failure Core and Owner-pending skips are unchanged; interrupted37 only retries37, never all Task episodes. Same source/profile and same frozen plan are required. No old431 or historical catalog migration.
- M and native cap B are independently1..8, including B>M; actual size is bounded by eligible Slots. Batch wait defaults20ms, allowed1..1000ms; flush at cap or bounded oldest wait, including partial1/2/3. Every physical Slot owns at most one queued/inflight/undelivered ticket. Existing32MiB request/128MiB encoded credit/1MiB action response/last-response-per-Session bounds remain.
- The single model owner handles Local encode/scan, batch Generation and optional decode. Local preparation may iterate per Session; policy Generation does not. Same required raw15/state15/H16/17frames/K4/local32 model, action processing records, literal per-item sampler seed and native prefix APIs. No attention/diffusion/Local algorithm, slow W0, training, dataset, optimizer or checkpoint code changes.
- `commit_many()` validates every exact pending capability and predecessor, builds complete Fast/Visual/Response maps, then publishes a **single** snapshot. No loop of single-Session commits. After sealing, prepare/generation/cardinality/finite/serialization/allocation/deadline/cancel failure aborts every uncommitted member. Invalid/stale queued members are removed before sealing peers. Drain/abort failure quarantines and never fabricates End ACK. Counter/media-map allocations occur before publication.
- Original B1-F1 deadline is transmitted unchanged through Client→Dispatcher→Actor, including partial wait and retry. A shorter member's expired deadline aborts its whole sealed batch; neither backpressure nor repeated requests renew it. HTTP429/503 retry is bounded by that same original budget.
- Coordinator alone owns the private per-Server registration capability. It registers only after D4 scene admission, with run/manifest/physicalSlot/generation/Task/Episode/Attempt. Sim receives only its exact assignment ACK and binds it once. Each Episode gets fresh Session/Fast state; reset must ACK after executor quiescence. Facade never retries a failed prediction as a new invocation and refuses a second successful delivery of the same native frontier. Actual legacy evidence/action loop is reused, not reimplemented.

## Native carriers and delivery

Native batch carries B matching observation/state/action/SequencePlan/domain/prompt/action-processing-record rows; prefix tuple has B entries, including `None` for cold samples. Output cardinality/finite `[16,15]` actions are checked before any commit. Each response retains full assignment/key/payload/frontier plus immutable `{id,size,index}` batch correlation. Client validates cardinality/index and exact assignment before ACK or action execution. Batch IDs do not replace inference identity or alter Episode order. CPU tests use the actual prefix attachment/context helpers and verify `(hot,None,hot)` offsets `[0,4,4,8]`, disjoint Fast tensors, unchanged/grad-free W0, reset isolation and new B1 action/Fast state equality to the legacy reference.

Per prediction JSON retains transaction correlation and queue/preparation/generation timing. `/info` exposes batch histogram, queue/byte high-water/capacity, live Sessions, quarantine and media bounds; terminal progress periodically includes bounded per-GPU batch telemetry. Polling is diagnostic and does not rehash model weights.

## Optional media, independent of actions and SR

Generated video request is an optional `{media:{replan:index}}` payload extension for the new profile; B1 schema is unchanged. Action/status/response commits before model decode. At most2 CPU latent/response jobs and128MiB spool/GPU; bounded PNG response32MiB. Capture/copy/capacity or media mapping failure drops that media item and preserves valid actions. Decode uses the same single model executor only when inference has no queued work. No second GPU model, concurrent mutable VAE or unlimited latent retention.

Sim has a separate bounded background media fetcher and transport. It validates key/SHA, forwards frames to the existing bounded MediaSink once, ACKs the media item, and records per-replan fetch/drop/error/cancel status in non-authoritative media diagnostics. End fences delivery, cancels pending media, drains owned model work, and joins bounded helpers before sink/Core publication. A late response cannot write to the closed sink or recreate old staging. Video/PNG/decode/write errors are diagnostics; unproven device/worker cleanup is an infrastructure qualification fault. Ordinary media errors do not change environment SR. Environment MP4 and generated MP4 each have one original location; no videos_view copy or automatic strict FFmpeg decoding.

## Config, identity and manual entry

Example: `configs/eval/robocasa_eval_v2_phase_b.example.yaml`. Fill the explicitly named EVAL_* input/output/interpreter variables; use a new run namespace. Its2Task×2Episode plan is Canary-sized and **not execution permission**. Production defaults remain Phase A; explicit M2/B2 on the Phase A profile is still refused. Same-run Phase B identity freezes G/GPU IDs/M/B/wait/noise convention; runtime also checks against the manifest before any process creation. Changing these is a new run, not a hidden Resume conversion. Video options remain separate diagnostics.

From the exact candidate repository root, CPU preview after setting paths:

```bash
bash scripts/run_robocasa_eval_v2.sh dry-run \
  --config configs/eval/robocasa_eval_v2_phase_b.example.yaml \
  --gpus 4 --sims-per-gpu 2 --max-infer-batch-size 2
```

Dry-run creates no model/environment and performs no GPU probe; output shows selected/useful GPUs, physical Slots and Episode-major plan/Resume dispositions. `fresh`, `resume` and targeted Owner `authorize` use the same entry but require their separate existing approvals. No native command was executed in this delivery. Formal900 changes tasks to all18 and episodes50 only after all Gates and explicit Owner authorization.

Actual Root/Server/Sim are normal exec processes, with no in-process time namespace change. Before model startup Phase B read-only interpreter probes require actual active and children namespace identities equal and Client/Server CLOCK_MONOTONIC domains equal. Existing mandatory B1-F1 proof remains; no wall-clock or receive-time fallback. This cloud's missing timens file is still BLOCKED for native deployment. CPU tests explicitly double kernel bytes through the real parser; they do not validate this cloud for native execution. Namespace work is limited to that deployment condition, with no new namespace subsystem.

## Unified CPU acceptance and handoff

Use the target's existing CPU environment with Ruff0.12.7 in clean detached worktrees; external new evidence directory:

```bash
python tools/v3/run_eval_v2_batch_b2_cpu_gate.py \
  --root-worktree '<EXACT_ROOT_WORKTREE>' \
  --expected-root '<NEW_FULL_IMPLEMENTATION_ROOT>' \
  --expected-child '<NEW_FULL_CHILD_GITLINK>' \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

The new thin entry reuses the original read-only Gate, whose defaults remain B1-compatible; it extends static/source coverage and adds actual Batch/transport and production runtime tests. It runs all prior99 inference and255 Phase A regressions plus new cases, with zero skip/failure/error, exact SHA/import origin/clean-before-after checks, Ruff/format/AST and raw per-group/combined JUnit/logs/env/source hashes. Synthetic900 still proves only CPU scheduling/ledger behavior. No independent DS verdict is inferred from author execution.

New CPU coverage includes native B1/2/3/partial/B>M, cold/hot prefix carriers and output binding, atomic member faults, shorter member deadline, pre-seal/Generation/decode End, backpressure/retry/ACK/replay, immutable profile Resume, media faults/late delivery, and **real owned OS** Sim/HTTP subprocess overlap with exactly one synthetic model owner/used GPU, task switch, D5 barriers, Core results and completed Resume no-work. These processes use fake physics/diffusion/kernel-file evidence, CUDA hidden, no model weights or real RoboCasa. Explicit tiny inputs are fixtures, not historical training assets.

Publish Child first, then Root Gitlink/source implementation, then immutable author evidence/diffs/source bindings and canonical request on this candidate only; fresh remote readback and STOP. GPT reviews the second-increment delta; DS independently replays the final complete candidate once; only then separately authorized 1GPU/M2/B2 native Canary, then separately authorized900. Do not automatically merge or start those stages. Exact implementation Pair and measured final author counts are bound in the handoff, not guessed here.
