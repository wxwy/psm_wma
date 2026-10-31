# EvalV2 CLI `--tasks all` — approved V3 promotion

This is promotion of already approved code, not a new implementation or review request.

| Identity | Full SHA |
| --- | --- |
| Approved Formal Root | `f3fccc8f9ba99cbaf8ce5e3597edfce8b6fc4ce1` |
| Child / Gitlink (unchanged) | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| Canonical V3 before promotion | `2e44cd70f343ebe8c1c7741cdbbc605485a4dd9a` |
| Candidate history preserved | `5bd1c354ec011fd2379862c378cb6989dbe6f662` |

The exact-pair GPT `APPROVE_CODE` report was fetched and read from canonical V3:
`docs/collab/chatgpt/reviews/2026-10-31_V3_EvalV2_CLI_TasksAll_f3fccc8f_6c83596d_Incremental_Code_Gate_APPROVE_CODE.md`.
Owner authorizes safe promotion in a new isolated cloud worktree. No runtime action
or update to any active shared code directory is authorized.

## Code and history preservation

The only production difference from canonical V3 is the approved line in
`scripts/robocasa_eval_v2/config.py`: preserve exact CLI `all` as the wildcard
string, while retaining existing comma splitting for other inputs. The new CLI
tests are identical to the approved tests. All 9,852 Root source objects match
the approved Formal Root; the whole Child Gitlink stays at `6c83596d...`.
Training, other EvalV2 modules, model, simulator and checkpoint code are unchanged.

Both canonical and candidate histories are merged. The sole merge conflict was
`CODEX_INBOX.md`: canonical content is retained byte-for-byte, followed by the
candidate-only tail after their shared base. Candidate evidence, all review
records and existing work are preserved. Promotion metadata adds no new Gate.

## Checks and execution boundary

Git/source checks passed, along with all 19 frozen artifact hashes and 5 formal
source bindings. The original author JUnit still contains 29 passed and zero
failures/errors/skips. Historical CPU tests, Ruff and GPU tests were not rerun.
These checks establish inheritance; they are not a new independent CPU/GPU result.

Work is restricted to `/workspace/psm-wma-eval-tasks-all-promotion` and remote Git
refs. Child is intentionally uninitialized in this new worktree; the unchanged
Gitlink and official Child branch were checked without updating Child files.
No existing runtime/shared directory, process, config, model, data, DCP or log was
accessed or changed. No training, Action Server, simulator, evaluation or DS
execution was started.

Receipt: `docs/collab/codex/receipts/2026-10-31_eval_v2_cli_tasks_all_v3_promotion/`.
The normal nonforce V3 push and remote readback will identify the promotion commit
in the completion receipt. Stop after publication; actual GPU evaluation still
requires separate authorization.

## Completion

Production promotion Root `68cba5640eae205445153808951145cac0912d8c` was published to V3 without force.
At 2026-10-31T23:11:17.089659+08:00, GitHub fetched and advertised Root matched this commit;
official Child and Gitlink both remained `6c83596d6a259e89c4cd3e79424024983426ac3d`.
Remote source and evidence checks passed; see `publication_readback.json`.
The completion successor only records this receipt. No runtime or active shared
directory was touched. Work is complete; real evaluation still requires its own
authorization.
