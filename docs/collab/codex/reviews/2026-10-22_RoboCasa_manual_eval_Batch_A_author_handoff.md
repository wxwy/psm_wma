# RoboCasa manual evaluation — Batch A author handoff

Date: 2026-10-22. Author result: **AUTHOR_CPU_PASS / independent implementation Gate pending**.
This delivers Batch A only. It does not approve a simulator dependency, a real benchmark,
GPU execution, or the future unified Batch C launcher.

## Exact isolated implementation

| Item | Value |
|---|---|
| Root implementation | `7646d41488a55d5a44ab193520a42c48cf5acc90` |
| Child / Root Gitlink | `e42a2468672d3ef8fcba708fc19e70daec7c790e` |
| Root candidate ref | `v3-robocasa-manual-eval-20261022` |
| Child candidate ref | `v3-robocasa-eval-lifecycle-20261022` |
| Root baseline | `c6d6dab11c97f87e94b8b8bd3601bab02dce33f8` |
| Child baseline | `35b0ea1ccee9ee26653ed6589c484f0997d1c586` |
| Design | [Frozen Contract](../../chatgpt/requests/2026-10-22_V3_RoboCasa_Owner_Manual_Eval_Framework_Frozen_Contract.md) |
| Design review | [Design APPROVE / runtime REQUEST_CHANGES](../../chatgpt/reviews/2026-10-22_V3_RoboCasa_18task_Session_Vendor_ManualEval_Design_Gate.md) |

The implementation is published on isolated refs. A later evidence/ledger HEAD does not
replace this implementation Root. No G1 candidate code was merged into this branch;
the previous G1 cross-pair candidate refs and evidence are preserved.

## Behavior and scope

- Queue defaults to `--server-lifecycle per_task` and `--on-infrastructure-error stop`.
  Every task creates a new Action Server with the unchanged Local required/max_sessions=1
  contract. Both Server and Simulator are reclaimed before another task on that worker.
  No cross-task reuse option, TTL, Local disable, or capacity increase is introduced.
- Explicit `continue_with_new_server` is screening-only: it rebuilds the Server after
  each task, retains every task/worker error, returns nonzero, marks the run INCOMPLETE
  and sets formal SR to null after infrastructure failure. Any cleanup failure always
  stops the queue, including in this continue mode. Partial SR remains explicitly partial.
- Independent finite positive budgets: server startup, HTTP prediction request, episode
  wall time, task wall time, termination grace. Old `--timeout` remains the startup/request
  default, **never** the task wall limit. Defaults: startup/request 600s, episode1800s,
  task10800s, grace20s. These choices and lifecycle/error policy enter protocol identity.
- Owned `Popen(start_new_session=True)` groups are supervised with monotonic clocks.
  SIGINT/SIGTERM cancels workers; a dead Server, process exit, task deadline or episode
  deadline fails the task. Cleanup sends SIGTERM, waits grace, escalates to SIGKILL and
  performs bounded reaping. Linux `PR_SET_CHILD_SUBREAPER` permits reaping descendants
  after leader death without depending on container PID1. Reaping uses only the owned
  PGID; no global process kill, foreign listener kill or training-process inspection.
  `/proc` and Linux subreaper support are prerequisites; inability to establish/reap them
  fails closed. Cleanup may consume its bounded grace intervals after a wall deadline.
- Simulator appends ordered, digest-bound start/end progress records. Start precedes
  `env.reset()`; end follows episode evidence, media and Local cleanup. Queue independently
  bounds first environment construction and post-episode shutdown even without progress.
  Missing, malformed, foreign, oversized, duplicate or out-of-order events cannot validate
  successful completion. Progress timestamps cannot extend Queue deadlines.
- Child keeps the existing finally and moves reset/begin under it. Reset/media/cleanup
  errors receive a separate `rolloutXX_cleanup.json` witness. Original rollout or encoder
  failure wins over a later reset failure. A failed episode stops that task; the same
  contaminated Server is never used for another task.
- Per-task `commands.json`, `server_info.json`, `server_process.json`,
  `episode_progress.jsonl`, `process_cleanup.json`, eval log and existing raw action,
  prediction/partial-media files preserve failure evidence. Worker logs remain append-only.
  A hard kill can leave an interrupted file undecodable; it is not a complete episode.
- Port preflight matches the Child HTTP Server's `SO_REUSEADDR` behavior and performs
  `listen()` while checking all ports. This tolerates TIME_WAIT after a stopped owned
  Server and continues to reject active listeners. Exact `/proc` PID ownership after
  startup remains mandatory, including the foreign-listener race.

Production changes: Root Queue plus `scripts/robocasa_processes.py`; Child
`simulation/robocasa/closed_loop_eval.py`. New focused tests accompany each repo.
No training, checkpoint, RNG, optimizer, config-truth, Local-TTT algorithm or vendor files
changed. Exact AST proof preserves Queue checkpoint/config/protocol validation helpers
and the entire Child `for step in range(max_steps)` action loop.

Same-source whole-task resume still uses existing strict identity. Batch C must add
independent attempts for incomplete-task reruns; Batch A does not claim that feature.
Likewise the old generated-video behavior is unchanged here, not relabeled as `first`.

## Author CPU evidence

[Evidence directory](../evidence/2026-10-22_RoboCasa_manual_eval_Batch_A_author_cpu/)
contains `gate.json`, raw logs/XML, exact zero-context patches, source hashes/protection,
versions, 30 complete synthetic Queue witnesses and the prior failed attempts.

| Run | Result |
|---|---|
| Final focused Queue/process/Child lifecycle + existing contract/client/decoder regressions | **72 methods +61 subtests passed**, 0 failed/error/skipped, 36.44s; JUnit133 records |
| Existing identity/episode/media regressions | **20 passed**, 50 unrelated deselected, 0 failed/skipped, 2.73s |
| Ruff0.12.7 check + format with Child `.ruff.toml` | PASS, all6 changed Python files |
| Python syntax and source diff checks | PASS |
| Original Child negative reproduction | Expected RED:2 real cleanup-contract failures |

Final total is **92 passed methods/cases +61 passed subtests**. Do not count JUnit133
as133 independent methods, or combine intermediate runs into the final total.

Queue tests run the actual main/identity with real tiny Git repos, local standard-library
HTTP processes, `/proc`, process groups and real signals. Only the model/server executable
and simulator executable boundaries are replaced with synthetic processes/results.
The session test intentionally leaves an occupied HTTP session after each task; every
next task succeeds only with its new Server. Normal1/2/8 workers complete4 tasks×5 episodes
(idle workers are allowed when tasks<workers). Faults include kill, startup failure,
HTTP400, actual urllib request timeout, missing results, reset/media errors, server death,
Owner cancellation, ignored SIGTERM, live descendants of a dead leader, foreign listeners
and late worker directory/log initialization errors. An unrelated process survives cleanup.
Injected cleanup errors occur **after real group reaping**, to avoid intentional leaks.

Child lifecycle tests compile the original production function body, with only env/network/
media boundaries doubled. Existing Phase6/client/decoder tests import original lightweight
modules; robosuite/robocasa are registration doubles in the original Phase6 fixture.
No real Cosmos model, simulator, GPU, DCP or G1 data was accessed.

Failure history is retained, not hidden: initial process fixture failed to forward
`start_new_session`; port TIME_WAIT exposed an actual restart preflight issue; the old
late-Popen test assumed all20 trials could finish while a per-task worker already held
one task. Its new correct expectation is15, with failed task+worker error mandatory.
Separate late mkdir/log-open tests still require20 valid trials plus INCOMPLETE/nonzero.
`revision3` was59+58; later new fault coverage supersedes it. First extended collection
failed on missing requests/Pillow/SciPy; `cpu-dependencies.log` records fixed CPU venv
package installation. No skip, xfail or deleted regression masks these failures.

## Reproduction for DS after GPT incremental review

Use a clean independent detached worktree of the exact Pair above, not a document HEAD.
Do not reset/clean an existing tree or write production training paths. All inputs are
synthetic and temporary; no real model/server/simulator or GPU command is involved.

Set `ROOT_WORKTREE` to that worktree, `CPU_PYTHON` to the existing complete CPU-capable
Python and `NEW_EVIDENCE` to a new external directory. Verify the Root, Child, gitlink and
clean source first. Keep every command's return code and raw output. These are templates,
not executed target-server commands:

```bash
cd "$ROOT_WORKTREE"
git rev-parse HEAD
git -C cosmos-framework rev-parse HEAD
git ls-tree HEAD cosmos-framework
git status --short
git -C cosmos-framework status --short
mkdir "$NEW_EVIDENCE"
export CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export HF_HOME="$NEW_EVIDENCE/hf" MPLCONFIGDIR="$NEW_EVIDENCE/matplotlib"
export PYTHONPYCACHEPREFIX="$NEW_EVIDENCE/pycache"
export PYTHONPATH="$ROOT_WORKTREE/cosmos-framework:$ROOT_WORKTREE/scripts"
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q -s \
  tools/v3/eval_robocasa_queue_identity_test.py \
  tools/v3/robocasa_processes_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_contract_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_phase6_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/local_memory_client_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/eval_utils_test.py \
  --junitxml="$NEW_EVIDENCE/focused.xml" > "$NEW_EVIDENCE/focused.log" 2>&1
"$CPU_PYTHON" -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tools/v3/remaining_optimizations_test.py \
  -k 'screening or identity or episode or runtime_error or partial_video' \
  --junitxml="$NEW_EVIDENCE/regression.xml" > "$NEW_EVIDENCE/regression.log" 2>&1
"$CPU_PYTHON" -m ruff check --config cosmos-framework/.ruff.toml \
  scripts/robocasa_processes.py scripts/eval_robocasa_18task_queue.py \
  tools/v3/eval_robocasa_queue_identity_test.py tools/v3/robocasa_processes_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py
"$CPU_PYTHON" -m ruff format --check --config cosmos-framework/.ruff.toml \
  scripts/robocasa_processes.py scripts/eval_robocasa_18task_queue.py \
  tools/v3/eval_robocasa_queue_identity_test.py tools/v3/robocasa_processes_test.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval.py \
  cosmos-framework/cosmos_framework/simulation/robocasa/closed_loop_eval_lifecycle_test.py
```

Author used `/workspace/psm_wma` and `/workspace/.venvs/psm-wma-cpu/bin/python`;
external raw logs were `/tmp/psm-v3-eval-a-20261022/`. See `versions.json` for fixed
packages. Baseline red command runs the versioned `baseline_red_test.py` beside its
original source snapshot and must yield exactly2 failures/exit1; this is separate from
the green implementation suite. A failure, surviving owned PID or lost infrastructure
error is FAIL and stops validation; missing dependencies are BLOCKED, not a skip.

## Remaining ordered work / stop boundary

**B is BLOCKED on real target dependency identity**: DS must read the actual RoboCasa
full Git SHA, robosuite baseline/patched diff and MuJoCo version. Owner was asked for these
facts. Upstream robosuite v1.5.2 SHA alone does not determine the Kitchen/data-generation
physics contract. No guessed master/fork pin, alias of LEGACY, signature-only compatibility
patch, or modification of the dirty target editable repository was made.

C remains queued for the strict YAML/CLI launcher, tasks/list/dry-run, media modes,
vendor-bound identity and whole-task attempt recovery. The requested manual command is
**not yet implemented**. Historical SR0.05 stays diagnostic_unverified_physics.

Request GPT fresh incremental review of **Batch A exact Pair only**, then DS independent
CPU recheck. Stop after handoff; no source merge into V3, dependency rollout, GPU/server/
simulator, training resume or G1 asset modification is authorized by this author report.
