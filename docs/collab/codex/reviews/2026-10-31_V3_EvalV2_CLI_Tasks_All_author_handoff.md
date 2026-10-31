# EvalV2 `--tasks all` — one-line fix / incremental Code Gate request

**REVIEW; author narrow CPU PASS.** Isolated branch only, no V3 merge or runtime.

| Identity | Full SHA |
| --- | --- |
| Formal Root | `f3fccc8f9ba99cbaf8ce5e3597edfce8b6fc4ce1` |
| Unchanged Child / Gitlink | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| Latest V3 base | `0ab13951d640d50ea2c9c8812817bf3009eae7b5` |
| Candidate | `v3-eval-v2-cli-tasks-all-20261031` |

Later evidence/ledger SHAs do not replace the Formal implementation identity.
Owner request: CLI `--tasks all` must mean the same as YAML `tasks: all`.

## Fix and contract

`scripts/robocasa_eval_v2/config.py` used `a.tasks.split(",")` for every CLI
value, converting `all` into `["all"]`. Unchanged `identity.discover` recognizes
only the string `"all"` as the 18-task wildcard and rejects that list as a task name.
The **only production change is one line**:

```python
cfg["tasks"] = "all" if a.tasks == "all" else a.tasks.split(",")
```

All other CLI values preserve original CSV splitting/order and validation. No
change to discover/catalog, sampling, scheduler, Manifest/Resume/source identity,
runtime, Child, training, model or DCP. The other 12,522 Root objects are unchanged.
`all,CloseFridge`, duplicates, empty/unknown/case-mismatched names still fail;
`all` still requires the complete 18-task Atomic metadata catalog.

## Frozen RED / GREEN evidence

Bundle: `docs/collab/codex/evidence/2026-10-31_eval_v2_cli_tasks_all_author_cpu/`.

- **RED, expected 1 failure**: same new frozen public dry-run test, exact old
  config.py Git blob loaded into sys.modules before unchanged production CLI/
  discovery import. YAML `tasks: all` succeeds; CLI `--tasks all` fails with the Atomic task
  validation error. Archived old module, bootstrap, old source/test hashes and
  traceback. This is an old-module reproduction, not an old whole-worktree Gate.
- **GREEN 29 passed, 0 failures/errors/skips**: 12 new tasks tests + 17 existing config/
  profile regressions. No prior full84 or GPU/OS Gate replay. Source stayed clean
  and unchanged during the run; Ruff 0.12.7 check/format and AST parsing of both changed Python files PASS.
- Actual `config.resolve` across dry-run/fresh/resume gives identical YAML and
  CLI wildcard configuration and discovered 18-task order. CSV preserves requested
  order and equals the same YAML list; the default wildcard matches both.
- Actual public CPU dry-run produces equal YAML/CLI 18-task and 36 Episode-major
  slot JSON plans. Both model and model-config files deliberately absent; model
  prepare/runtime callbacks forbidden; 0 models/0 environments/no runtime attestation,
  no output namespace. Fresh/Resume tests only resolve/discover config, not run it.

Raw command/environment, RED/GREEN logs/JUnit, full implementation diff, scope
audit, 19 artifact SHA256 and 5 formal source bindings are retained. Existing config
tests unmodified; no skip/xfail/threshold relaxation. No execution of real model,
data/DCP/Job/GPU/server/simulator/training, no active run directory/log changes.

## Review boundary

Request GPT fresh incremental review of this parser fix and narrow CPU evidence
only. Preserve existing strict source/Resume identity; do not treat the change as
cross-version Resume permission. Publish and read back the isolated branch, then stop; no
automatic V3 promotion, DS dispatch or real evaluation. The existing YAML `tasks: all`
workaround without the CLI flag remains valid until this candidate is accepted.
