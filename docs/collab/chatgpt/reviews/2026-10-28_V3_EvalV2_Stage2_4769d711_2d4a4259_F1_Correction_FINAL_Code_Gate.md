# GPT Stage2 Code Gate — Correction and final superseding verdict (2026-10-28)

## 1. Final formal decision and source freeze

**FINAL VERDICT: APPROVE_CODE — Stage2 source-level Production Code Gate only; DS independent CPU and native/GPU Canary are NOT approved/passed by this verdict.**

This new review explicitly **SUPERSEDES** the earlier erroneous REQUEST_CHANGES/F1 text in docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_Stage2_4769d711_2d4a4259_Code_Gate.md and the corresponding earlier Inbox entry. The old review is retained intact as historical evidence of the correction, NOT an active blocker; do not direct Codex to fix the withdrawn F1 or create a new implementation SHA without further real evidence.

- Exact Formal Implementation Root: 4769d711777c20a72dd7a3f6071a96f08ad8abb0; Root direct parent 1404c34e6cb46df68368d877c296bf95a5bcc9f4.
- Exact Formal Child / Gitlink: 2d4a42590fead00ea16f6ae5902e2bc8382b07e2; Child direct parent 746c5cf2f2324104a62fb71510343aa40d3976c5.
- Candidate: v3-eval-v2-stage2-20261028. Handoff/Evidence HEAD 089e083c266d1768d0a6154023d75249d500f039 is documentation, NOT the Formal implementation pair.
- Prior Design Gate approval: Root 1fd3ad42075032bd0137ac9a76306169aaa45032 / Child 746c5cf2f2324104a62fb71510343aa40d3976c5, APPROVE_DESIGN remains valid.
- Root direct-parent one-commit Diff: 27 files, new V2 CLI/runtime/identity/resource/processes/tests/config/runbook + Gitlink. Child one-commit Diff: 13 files, new V2 Store/Scheduler/media/evidence/native adapter/worker and narrow opt-in hooks, no training, vendor, old Queue change.

## 2. Precise F1 correction: cancellation and Core commit ARE serialized

The earlier reviewer described an interleaving in which TaskA fails, coordinator records TaskB as pre-Core faulty, while TaskB simultaneously commits its Core after that fault, leaving an unresolvable same-Attempt fault. This overlooked a critical synchronization step, so the asserted F1 is **NOT reachable through the described coordinator_stop path**:

1. Root scripts/robocasa_eval_v2/runtime.py:605–615: on a failed Future, the coordinator first executes stop.set() and **scheduler.cancel(repr(e))**, **before** iterating through active Tasks to call store.record_process_error(coordinator_stop).
2. Child cosmos_framework/evaluation/robocasa_v2/scheduler.py:154–160: scheduler.commit() holds **the same scheduler._lock** from ownership check all the way through store.commit and its Core publication. Scheduler.cancel() acquires **that same _lock** at scheduler.py:171–179 and marks scheduler.cancelled=True before returning.
3. Consequently, if TaskB scheduler.commit acquired the lock first, its Store.commit and os.replace complete *before* cancellation can acquire the lock; the subsequent coordinator_stop record observes already-published Core and correctly stamps core_committed_at_fault=True. Conversely, if cancel acquired the lock first, TaskB's later scheduler.commit fails ownership/check-cancelled and publishes no Core. The described mixed state cannot arise.
4. Root runtime.py:424–436 may record a native_episode fault in a Worker thread before the coordinator cancels, but it records the **same Task** whose run_slot is handling the exception. A given Task has one active logical slot per worker (Scheduler enforces worker/task exclusivity); that Task cannot also be independently in a Core commit during this exception handler. Other Tasks' valid commits remain unfaulted by that per-Task handler until the coordinator cancellation barrier.
5. Root runtime.py:438–489 process-cleanup faults occur after the cancelled scheduler gate (error path), or after normal round completion/valid Commit/Futures handling (clean path); they do not establish the earlier counterexample.

**Correction:** Withdraw F1 HIGH and WITHDRAW the earlier Stage2 REQUEST_CHANGES. This is a code-level synchronization proof by direct source review, NOT a claim that all conceivable race conditions or real process failures have been exercised on GPU.

A targeted deterministic independent CPU ordering regression remains useful as **nonblocking DS Gate coverage**, but **no current source defect or required fix** is supported by the earlier interleaving. Do not require Codex to change production code merely to satisfy that withdrawn hypothetical.

## 3. Verified current Stage2 positive source evidence

| Owner contract | Actual source reviewed | Source-level disposition |
| --- | --- | --- |
| D1 scoped process fault/recovery | Root runtime.py:68–127,424–489,605–645 and robocasa_eval_v2_processes.py:19–198; Child store.py:834–1000. Ownership binding, positive cleanup, immutable scoped errors, fresh health/retry, post-Core execution-only recovery. | ACCEPT source contract |
| D2 atomic Task/Slot/Core | Child store.py:309–346,586–664,689–833; evidence.py:15–111. Intent→ready, exact Attempt, sealed Core inventory and fsynced directory rename, no successful result overwrite. | ACCEPT source contract |
| D3 Episode-only Resume | Child scheduler.py:18–184, store.py:657–727; only missing eligible slot executed, valid success AND behavioral failure skipped, sparse later valid slots preserved. Real new scene allowed, recorded Stream/Seed. | ACCEPT source contract |
| D4 initial-success/4-strikes | Child eval_v2_adapter.py:35–70, eval_v2_worker.py:75–105, store.py:527–584,729–785. Strict pre-action _check_success, degenerate rejection, separately bounded fourth recoverable reset/precheck errors → skipped; Owner targeted permit only. Unsafe environment fails closed. | ACCEPT source contract |
| D5 Episode-major | Child scheduler.py:91–145; Root runtime.py:490–645, multi-worker same round, strict barrier, frozen Task order and valid-Core Resume skip. | ACCEPT source contract |
| Real native action and Local | Child closed_loop_eval.py opt-in initial_observation/success_check/http_client/on_frame; NativeEpisode.execute reuses real run_policy, raw15→env12, Local begin/ack/record_completed/end/reset; typed strict post-env.step success. | ACCEPT CPU-level wiring; real GPU/local behavior pending |
| Media C | Child media.py spawned bounded CPU encoder/drop/error; Core inventory excludes MP4; no automatic ffmpeg full-video decode. Failed video is diagnostic, unsafe encoder cleanup is execution-fault not behavioral failure. | ACCEPT source contract |
| Frozen experimental identity | Root identity.py source/checkpoint/config/Task+vendor/runtime verification, config.py, resource guard, fresh namespace and separate Owner permit CLI. | ACCEPT CPU-level wiring; physical system pending |

## 4. Original author evidence and independent reviewer boundaries

Original author final_cpu02/junit.xml was read from Evidence HEAD (not paraphrased): **tests=200, errors=0, failures=0, skipped=0, duration=86.725s**; 142 new production-path tests and58 existing Child evaluation regressions. Ruff0.12.7, format, AST34, shell syntax/help, whitespace: author-frozen logs report PASS. The reviewer independently fetched **all 34/34 frozen_in_test_runner source blobs** from the exact Formal Root or Child and verified Git Blob SHA equality with the 49-item formal_source_bindings.json; source consistency PASS. Reviewer **did NOT run pytest, Docker, actual DCP, GPU, real RoboCasa or independent DS tests**.

Synthetic production900 uses real production Store/Scheduler with fake task/model/physics,900 dispatches/50 barriers/450 fake successes+450 failures/41.070s. Author CPU p95 claim28.31ms/Core Commit4.01ms, max summary rebuild2.93s,8223 JSON reads and86814 cache hits; tiny real FFmpeg **encoding** test and real loopback HTTP/Local client with fake model/env, not real Cosmos inference/RoboCasa.

## 5. Remaining mandatory independent Gates; no authority expansion

- **Next DS_PRO independent focused CPU Gate**, on clean checkout of exact Formal Root 4769d711 and Child2d4a4259, read-only training/data, no GPU/simulator. Reproduce original200 focused test suite/source/static; optionally add a deterministic **cancel vs in-flight Core** ordering negative test to confirm the source proof, not a mandatory production source change. Verify process cleanup, Owner skip and normal behavioral failure immutable, real media encoder bounds and resource refusal. DS reports PASS/FAIL + preserved raw Evidence for incremental GPT Evidence review.
- **Later separately Owner-authorized tiny native Canary** must measure real Cosmos DCP load, model /info, actual RoboCasa reset+step, Local-TTT Session start/ack/end/reset, simulation camera/state/raw15-env12, NavigateKitchen initial-success rejection, real EGL contexts when retaining 18 Task actors, GPU4–6 availability/resource margins, process and media cleanup and interrupted Episode-only Resume. GPU7 historical EGL SIGABRT not assumed repaired. No claim that 18 retained real envs fit is made.
- No automatic V3/Child production merge, GPU/real Action Server/RoboCasa eval,900 Episodes, training/checkpoint mutation, old431 file migration/cleanup. Final Owner authorization remains separate. Document-only V3 review commits do not change the Formal production pair.

## 6. Final Code Gate

**APPROVE_CODE (Stage2 source only)** at unchanged Formal Root/Child pair **4769d711 / 2d4a4259**, **0 currently substantiated source-level blockers** following explicit F1 withdrawal. The previous REQUEST_CHANGES is explicitly superseded and not actionable; do not request a futile F1 code remediation. Next action is DS independent CPU, not native/GPU nor merge.

This is authoritative only when the new Review and a corresponding **latest append-only superseding entry in docs/collab/chatgpt/CODEX_INBOX.md** are both published and verified.
