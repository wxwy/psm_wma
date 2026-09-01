# R09-B2 P5 concrete CPU-only static-export execution review

- Request commit: `b87603d7b96400bd7eecae50708f43c7f461d30a`
- Reviewed exporter/static-tools revision: `9ad602f93f5975f9ec7d033783b41052ca09107e`
- Evidence-root revision named by request: `8bde8c12876219b1a36d50b604e05701bf550e3e`
- Frozen production revision: `ddb4e0eae97fb545d5239c1ddb6d4387170f3780`
- Reviewed Gitlink/submodule: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

This review is limited to the one-shot `APPROVE_TO_RUN_P5_STATIC_EXPORT` request. It does not reopen the already reviewed P5 static-tool semantics except where the concrete execution bootstrap can bypass the reviewed-code identity.

The requested run is otherwise narrow and concrete: one fresh CPU parent, exact production/evidence/exporter roots, a fresh canonical output path, two fresh children, pair-verifier PASS as the only success condition, and no retry after FAIL.

## Findings

### HIGH — the concrete bootstrap can import unreviewed exporter code before proving the approved exporter revision

Concrete request command in commit `b87603d7...`:

- sets `PYTHONPATH=/disk/rl/psm_wma_p5_exporter_9ad602f`;
- starts `/opt/conda/bin/python3.11`; and
- immediately executes `from tools.g0.export_r09_b2_p5_resolved_config import run_parent_export`.

The request text says that exporter root is frozen at reviewed revision `9ad602f93f5975f9ec7d033783b41052ca09107e`, but that identity is not machine-checked before the import.

`tools/g0/export_r09_b2_p5_resolved_config.py:216-232` (`bound_exporter_source`) proves that the executing exporter/verifier files belong to the *current* `exporter_root` and cross-checks their current file SHA values against the same root. It does not compare the root revision or file digests against the independently approved `9ad602f` identity.

`tools/g0/verify_r09_b2_p5_full_config_diff.py:135-139` (`_exporter_source`) likewise requires only tracked-clean state and then returns whatever `git rev-parse HEAD` and tool SHA values the current exporter root has. Those values are recorded as provenance, but they are not an immutable authorization anchor.

Therefore a clean checkout moved from reviewed `9ad602f` to another clean commit can be imported before any project-owned identity guard runs. The moved code can execute module-level code immediately, and a self-consistent moved exporter/verifier pair can subsequently report its own new HEAD/SHA values. This violates the narrow execution authorization boundary: `belongs to exporter_root` is not equivalent to `is the reviewed exporter revision`.

The current parent launch also exposes `exporter_root` through `PYTHONPATH` during Python startup. Because the project validators require tracked-clean rather than independently proving an empty untracked set before startup, an untracked `sitecustomize.py`/bootstrap-path injection would also execute before `bound_exporter_source()` is reached. The same concern applies to the production child bootstrap through the frozen production `PYTHONPATH`; a one-shot execution authorization needs the concrete preflight to prove the roots have no such untracked startup injection.

### Required fix

The frozen execution command must establish the approved identities **before importing any root-owned Python module**.

A sufficient pattern is:

1. start the parent with an isolated stdlib-only bootstrap (`/opt/conda/bin/python3.11 -I -c ...`) so `PYTHONPATH`/root-owned `sitecustomize` is not active during bootstrap;
2. before inserting `exporter_root` into `sys.path`, independently assert with stdlib/subprocess:
   - exporter canonical path is exactly `/disk/rl/psm_wma_p5_exporter_9ad602f`;
   - exporter `HEAD == 9ad602f93f5975f9ec7d033783b41052ca09107e`;
   - exporter Gitlink/submodule is `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`;
   - exporter root and submodule have no tracked **or untracked** changes;
   - production canonical path/HEAD/Gitlink/submodule equal the frozen P4 values (`/disk/rl/psm_wma_p4_d005_retry`, `ddb4e0eae97fb545d5239c1ddb6d4387170f3780`, `21d064f...`) and are fully clean;
   - evidence root is the requested `/disk/rl/psm_wma_p5_evidence_8bde8c1`, at the requested `8bde8c12876219b1a36d50b604e05701bf550e3e`, with Gitlink/submodule `21d064f...`, and fully clean;
   - canonical output is absent and is outside all three roots;
3. only after those assertions, insert the exact exporter path into `sys.path` and import `run_parent_export`;
4. retain the existing fail-closed child/pair-verifier/staging rules and the no-retry rule.

Equivalent shell preflight is acceptable only if it cannot import or execute exporter/production Python code before all identity/full-clean checks have passed. The resubmitted command must be complete and immutable; do not rely on a prose statement that the worktrees were checked earlier.

## Positive observations

- The request names exact production/evidence/exporter roots and a unique output path.
- The production root remains bound to `ddb4e0e...` / Gitlink `21d064f...`; the requested exporter and evidence revisions also carry Gitlink `21d064f...`.
- No exporter/verifier production code changed between the previously reviewed integration and `9ad602f`; the only later code change was the permanent internally-consistent forgery test.
- P4 evidence files were not modified on the path to the requested `8bde8c1` evidence revision.
- The requested success/failure semantics are narrow: verifier PASS promotes canonical output; any failure leaves attempt evidence, no canonical output, and no retry.

## Gate decision

`APPROVE_TO_RUN_P5_STATIC_EXPORT` is **not granted**.

After the concrete bootstrap is changed to machine-bind the reviewed revisions/full-clean roots before any project import, Codex may submit a new one-shot execution request. The static exporter/verifier semantics do not need another redesign if they remain unchanged.

Still not authorized: static export execution, production compose / `load_experiment_from_toml`, CUDA/GPU use, `torchrun`, model/dataloader/optimizer/checkpoint construction, weights/data/MP4 access, training, evaluation, inference, P5 closure, or B2-T.
