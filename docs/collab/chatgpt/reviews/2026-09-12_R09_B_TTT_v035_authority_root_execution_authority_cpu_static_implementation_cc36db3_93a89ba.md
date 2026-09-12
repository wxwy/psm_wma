# ChatGPT Review — Authority-root Execution Authority CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root implementation SHA: `cc36db3a6b863d86d57f5eb0e3fcefb5aef3376d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` tree entry is a submodule/Gitlink resolving to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental implementation review against prior exact pair `bb17774ce6da4e4d14c57993fe97f813065de319 / 93a89ba...`. The effective remediation delta is limited to the approved root adapter/test files plus collaboration/status bookkeeping; child/runtime code is unchanged.

## Prior HIGH closure progress

### Prior HIGH — project modules were imported before the four-module closure was proved: PARTIALLY CLOSED

The remediation correctly moves substantial closure logic into the stdlib-only `-c` bootstrap before `sys.path.insert()` / `runpy.run_module()`:

- formal `HEAD` is checked;
- the formal tree is enumerated with the frozen Git executable/prefix;
- adapter/authority/collection/audit paths are compared against formal `100644 blob` identities and raw SHA-256 values;
- direct isolated-interpreter tests now modify collection/audit and prove rejection before the import sentinel, evidence path and refs.

That closes the main ordering defect from `bb17774...`. However the pre-import authority is still not identical to the approved design contract, and the remaining gaps are security-significant at the first real-execution boundary.

## Current blockers

### HIGH-1 — pre-import executable/module path identity remains incomplete: interpreter/Git full identity is not proved and the module non-symlink check is defeated by resolving before `lstat`

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:165-185`

The approved design freezes, before any project import, complete interpreter/Git identity plus four module regular/non-symlink + raw/formal-tree identity. The current bootstrap does not fully implement that contract:

1. The interpreter is checked only by comparing `realpath(sys.orig_argv[0])` with the declared interpreter path. Its regular/non-symlink type, raw SHA-256 and version are still verified later inside adapter preflight, after project import.
2. Git is checked for regular/non-symlink type and raw SHA-256, but its frozen version is also still verified only later after import.
3. For each project module the code first computes `full=os.path.realpath(os.path.join(root,path))` and only then calls `os.lstat(full)`. Resolving the path before `lstat` erases the original leaf symlink identity. A symlinked approved module path can therefore be inspected as its resolved regular target rather than being rejected for being a symlink, contrary to the frozen `lstat regular/non-symlink` contract.

The reported collection/audit drift witness does not cover module-path symlinks, interpreter raw/version drift before import, or Git-version drift before import.

**Exact acceptance:** before `sys.path.insert()` / `runpy.run_module()`:

- verify the actual interpreter path itself with `lstat`/non-symlink regular-file identity, exact frozen raw SHA-256 and exact frozen version;
- verify the actual Git executable with the same type/raw/version contract;
- for every module, inspect the unresolved `root/repo_path` authority first (or use an equivalent `open(..., O_NOFOLLOW)` / dirfd traversal), reject any symlink path/component before resolving/opening, then hash the bytes from the proven regular file and compare with the formal-tree `100644 blob` identity;
- add isolated-interpreter witnesses for module symlink substitution and interpreter/Git identity drift proving rejection before any project import, evidence/ref mutation or project callback.

### HIGH-2 — bootstrap executes native Git object/worktree commands before the common local-config authority is verified, so pre-import Git behavior is still ambient-config influenced

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:168-180`

v0.4 froze the common Git config authority specifically **before the first object/ref/transport action**. The current bootstrap creates a sanitized process environment but then immediately runs native Git commands including `rev-parse`, `status`, and `ls-tree` before `NativeAuthorityGit.verify_configuration_authority()` has run. Global/system config is disabled, but the repository's local config is still active at this point.

That is not equivalent to the approved authority contract. `git status` can consume behavior-changing local config before it has been admitted. For example `core.fsmonitor` is a local-config execution hook used by `git status`; a hostile local config can therefore execute external code during the supposedly import-free bootstrap, before common-config raw/parsed authority is checked. The fixed prefix currently does not disable or pre-validate all such local-config behavior.

The remediation's hostile **parent environment** witness and later common-config tests do not prove this earlier bootstrap phase is protected, because the local repository config is still unaudited when those bootstrap Git commands execute.

**Exact acceptance:** make the bootstrap's first Git/object/worktree observation obey the same config authority boundary as production:

- before any Git command capable of consuming repository-local behavior, deterministically identify/read the common config using a non-executing/fail-closed mechanism and apply the frozen allowlist, or otherwise invoke the bootstrap Git commands with an explicitly frozen configuration mode that cannot consume unaudited local behavior;
- do not run `git status`/`ls-tree` under an unaudited local config;
- add a direct isolated-bootstrap adversarial witness with hostile local config (at minimum `core.fsmonitor`, and an include/rewrite variant) proving no external/project sentinel executes and no evidence/ref path appears before rejection;
- retain the existing no-replace/global/system isolation, formal-tree/raw module closure and later common-config Evidence binding.

## Evidence / scope notes

- `92/92 PASS`, Ruff, py_compile and diff-check are supportive but do not replace the missing direct witnesses above.
- The child/Gitlink did not change.
- No real source/materialization, project remote, GPU, model/data or training action is authorized by this review.

## Blocker summary

- prior HIGH: PARTIALLY CLOSED
- current implementation blockers: `2 HIGH`
- design blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:165)`

This verdict binds only exact formal pair `cc36db3a6b863d86d57f5eb0e3fcefb5aef3376d / 93a89ba61306d840a008813f62f26a34d54850f4`.

Scope remains temporary CPU/static only. This review does not authorize real selection/config materialization, candidate/ref/origin mutation, source/checkpoint I/O, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.