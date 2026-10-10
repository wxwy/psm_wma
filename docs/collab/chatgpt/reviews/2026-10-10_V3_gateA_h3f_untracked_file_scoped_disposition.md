# V3 Gate A historical H3-F monitor — scoped operational disposition

Date: 2026-10-10
Decision: **(a) AUTHORIZE TEMPORARY MOVE AND RESTORE**
Classification: **procedural/environmental gate-unblock only; NOT a technical verdict, Gate A PASS, production-code approval, or Resume authorization**.

## Pinned implementation target
- Formal Root: `cf0c92731197bfdd0de073a4c07ca93194f58968`
- Formal Child and Root Gitlink: `d41be4f5485dcd9321318840c8c278c1f7487924`
- Current V3 documentation/head commits are bookkeeping successors; DS_PRO must test the exact formal implementation pair, not a moving branch tip.
- Formal implementation/design pair unchanged: no duplicate technical review.

## Independent basis
1. In the pinned Root `tools/v3/run_migration_cpu_gate.py`, `allowed_root_records()` permits `SESSION.md`/`TODO.md` and narrowly scoped untracked Evidence but does not permit `?? scripts/plot_h3f_monitor.py`.
2. In the pinned Child `examples/psm_wma_robocasa_corrected_phase5.py`, `_audit_root_noncode_changes()` explicitly permits the single historical untracked file `?? scripts/plot_h3f_monitor.py`; `psm_wma_robocasa_corrected_phase5_test.py` verifies that different names or tracked modifications are rejected.
3. Existing review `docs/collab/chatgpt/reviews/2026-10-09_V3_verified_dataset_index_candidate_bb897_f7d089.md` explicitly requires preserving this historical local helper.
4. This is a mismatch of workspace allowlists. It does not establish any change to training behavior. It is not grounds to bypass other runner preconditions.

## Exact DS_PRO authorization
- Confirm Root HEAD, Child HEAD and Gitlink against the pinned pair and inspect full Root/Child porcelain status. Child must be clean. Do not touch files other than the exact untracked helper. If other unauthorized changes exist, report BLOCKED instead of hiding them.
- Confirm `scripts/plot_h3f_monitor.py` is an untracked **regular** file, not a symlink, and is not currently in use. Capture original mode, mtime, size, SHA256 and git-status snapshot; log them outside the worktree.
- Create a private temporary directory outside the worktree, store an **independent recovery copy** (with metadata) and verify its SHA256 *before* moving the original file out. Do not overwrite an existing destination.
- Temporarily relocate only the original file outside the worktree. Verify the precise path is now absent and that no other disallowed dirty status was concealed. Execute the pinned, unchanged Gate A CPU runner with a new external Evidence directory.
- Install an EXIT/INT/TERM restoration handler before the move. On success, failure, interruption, or abnormal runner exit, restore the file to its exact original path; never overwrite a file unexpectedly created at that path. Reverify SHA256, mode, and the expected untracked status. Retain recovery material if restoration is incomplete; report BLOCKED.
- Treat the Gate as PASS only if the original runner reports PASS **and** the file restoration and Root/Child/Gitlink postconditions are independently verified. Otherwise report FAIL/BLOCKED with raw logs and pre/post evidence; do not auto-retry.
- Do not change the runner, tracked code, tests, configs, git history, other agents' notes, DCP, or historical Evidence. No reset/clean/force/new worktree/GPU/training/Resume.

## Scope and next step
Authorization is **only** for a one-time Gate A execution in the existing worktree. The operator must preserve the full CPU/Ruff/pytest logs, `gate.json`, SHA256/mode witness, before-and-after status, and any restoration errors. Later Gate B-F require separate evidence/authorization. Original job `formal_verified_index_30k` remains stopped, latest complete DCP iteration unverified, frozen config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` not yet independently measured.
