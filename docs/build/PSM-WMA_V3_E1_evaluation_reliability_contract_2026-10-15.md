# V3 Batch E1 — evaluation infrastructure reliability contract

Date: 2026-10-15 (Asia/Shanghai). Owner/GPT scope: E1 only. This contract is frozen with the candidate implementation commit; changes require a new implementation SHA/Fresh Review. Author checks are not DS acceptance or GPT approval.

## Scope and authority

Implementation parent: Root `72aeb3767b6123de0358d5d148d5c2c788179d3c`; production inspected source Root `2f4dec43eb6b1e35b33a99d844d67813df5922a6`. Child/Gitlink remains `1d56320c08c56b0f8dd248919d152d81ae12ea7b` throughout E1. Only production source modified is `scripts/eval_robocasa_18task_queue.py`; focused test is `tools/v3/eval_robocasa_queue_e1_test.py`. Identity implementation, Child, training, cache, B1 diagnostic/frozen comparisons, optimizer/DCP and all old reviews remain unchanged.

Authority: `docs/collab/chatgpt/requests/2026-10-15_CODEX_V3_production_six_findings_staged_remediation_order.md`, Batch E1; six-findings static triage review. Independent branch `v3-e1-evaluation-reliability-20261015`; no automatic V3 merge or E2/T1/P1 progression.

## Execution health and evidence

- Task counts/outcomes remain calculated from task rows using the existing strict validators. `task_statistics_status` independently reports COMPLETE/INCOMPLETE. In-flight execution_status/status is RUNNING; it can become COMPLETE only after workers and cleanup finish without errors and tasks are complete. Worker/infrastructure errors yield FAILED and nonzero process exit even if all planned task trials were completed.
- Structured `worker_errors[]` and append-only `worker_errors.jsonl` retain worker_id, gpu, phase, task, exception_type, message, traceback, available returncode, timestamp, execution_id, server_log and task_log pointers. Simulator failures after assignment also have a task row; complete business outcome/counts are retained. Partial/malformed results remain on disk and are NOT silently accepted or stitched together (E2 is separate).
- When health is invalid, official `sr` is null, `sr_valid=false`; an otherwise complete task rate may be exposed as `diagnostic_sr`, explicitly diagnostic. Completed trial/success counts are never fabricated to account for infrastructure failures.
- Each coordinator invocation has a UUID execution_id, final `execution_<id>.json`, and per-execution `server_info_<id>.json`. A later same-identity invocation may replace the latest screening_summary.json but does not overwrite prior execution/error/episode evidence; existing server/task logs are appended. This is execution metadata, not E2 episode/scene resume or attempt stitching.
- JSON summary publication is serialized under a lock, fsynced and atomically replaced from a unique temporary file. Encoding failure leaves the last readable summary intact.

## Deadlines and cancellation

- Existing `--timeout` remains HTTP/request and server-startup timeout, default600 seconds. New `--task-timeout` is total simulator-process wall time across all episodes of ONE task, default3600 seconds. `--shutdown-timeout` defaults5 seconds for EACH TERM and KILL/reap phase. All three reject nonfinite, zero and negative values; aggregate coordinator join budget must also be finite.
- The 3600-second default is an explicit new E1 execution policy, NOT a measured robot horizon or changed Seed/reset/action protocol. Larger trial counts may need an explicitly reviewed larger task budget. Both new timeouts and execution contract version `v3_screening_e1_owned_process_groups` are bound into the evaluation identity, in addition to the new Root SHA. Never reuse an older manifest as though it had this execution policy.
- Every owned action server and simulator starts a new POSIX session/process group. Cleanup signals only PGIDs obtained from those exact successful Popen calls. No borrowed/other user's process/server is signalled. The expected simulator/server tree must not daemonize/escape via setsid/setpgid.
- Simulator polling has a task wall deadline and watches the shared stop event. Any worker infrastructure failure or coordinator SIGINT/SIGTERM requests cancellation. Already-finished simulator outcomes are parsed/preserved; still-running simulators are cancelled. All cleanup follows TERM -> bounded grace -> KILL -> bounded reap, including live descendants after their parent exits.
- Linux PR_SET_CHILD_SUBREAPER is required to reap owned orphan grandchildren, including containers whose PID1 does not reap. The coordinator enables it before creating workers and restores the prior value only after cleanup. waitpid targets ONLY the exact owned process group and runs nonblocking; Popen reaps its direct child. Non-Linux or unavailable subreaper capability fails closed before launching any server.
- Coordinator join upper budget is startup timeout + task_count*(task_timeout+2*shutdown_timeout) +2*shutdown_timeout +10 seconds. It polls joins, cancels at its deadline, cleans registered groups and gives remaining workers a final bounded join. Unfinished workers or unsuccessful kill/reap produce explicit cleanup errors, never success. Daemon worker threads allow a failed coordinator to exit after the bounded cleanup attempt rather than await an unlimited thread join.

## Focused CPU matrix and acceptance

The root test uses only stdlib mocks and tiny Python subprocesses; no real simulator, server, checkpoint payload, robot dataset, GPU or network service runs. It checks:

1. Normal 18-task completion with concurrent atomic-summary readers.
2. Worker Popen/readiness failure after another worker has completed the tasks; nonzero exit, preserved counts, null official SR and complete error/traceback/log evidence.
3. Cleanup exception after task completion; simulator Popen failure after assignment; nonzero simulator with complete and partial results; malformed result JSON.
4. Wall deadline for a sleeping process; both parent/child ignore TERM, requiring real KILL and reaping; stop-event cancellation; coordinator SIGTERM; an injected stuck worker released only by coordinator join watchdog.
5. No surviving owned descendants, no signalling an unrelated live process, partial action/log bytes retained, normal-exit leftover descendants reaped, idempotent cleanup, explicit bounded-cleanup failure, prior subreaper setting restored.
6. All three CLI timeout fields reject NaN/Inf/zero/negative; actual CLI default and identity binding; JSON encoding failure/republication; prior execution record survives a subsequent same-identity invocation.

Author evidence is `docs/collab/chatgpt/evidence/2026-10-15_V3_E1_author_cpu/` (logs/JUnit, source hashes, exact commands). DS must independently rerun this E1 scope in a clean detached exact candidate worktree and return its own evidence outside the worktree. GPT Fresh Incremental Review then binds the new full Root/Child Pair. No Gate acceptance, GPU-performance improvement or real-server cancellation behavior is claimed from author tests. E1 stops at DS handoff.
