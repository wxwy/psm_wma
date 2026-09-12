# ChatGPT Review — Authority-root Execution Authority CPU/static Implementation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root implementation SHA: `bb17774ce6da4e4d14c57993fe97f813065de319`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its `cosmos-framework` entry is an actual Gitlink resolving exactly to `93a89ba61306d840a008813f62f26a34d54850f4`; that child is independently reachable in `wxwy/cosmos-framework`.

This is a fresh implementation review against the approved design pair `9aba4460469ddab4640e90694e78968d497a9273 / 93a89ba...`. The implementation delta is confined to the approved root adapter/test files plus collaboration/status bookkeeping; child/runtime code is unchanged.

## What is correctly implemented

The implementation materially closes the later design items:

- parser/Evidence ABI now carries adapter/authority/collection/audit identities;
- bootstrap process identity uses Python 3.11 `sys.orig_argv` and binds declared/observed bootstrap source/argv digests;
- production remote is constrained to canonical HTTPS while temporary local transport stays test-only;
- Git commands use the frozen no-replace/config-isolation prefix and sanitized environment;
- common Git-dir/common-config authority is implemented with raw/config-view re-verification, `config.worktree` rejection, typed Evidence fields, linked-worktree direct witnesses and local-bare CAS coverage.

Those are not the blocking issue.

## Blocker

### HIGH-1 — the bootstrap imports project code before proving the frozen four-module closure

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:166` (`bootstrap_payload()` final `sys.path.insert(...); runpy.run_module(...)` transition)

The approved execution-authority design explicitly froze this order:

1. before any project import, the stdlib-only bootstrap must prove the interpreter/Git identity and the full project import closure;
2. adapter, authority, collection and audit modules must each be checked by regular/non-symlink path/type, exact raw SHA-256 and formal-tree `100644 blob` identity;
3. only after those checks may the bootstrap insert the project root into `sys.path` and call `runpy.run_module(...)`.

The current implementation does not do that. `bootstrap_payload()` validates only the invocation shape, bootstrap contract FD, declared/observed `-c` source digest, argv digest, project-root string and module name, then immediately executes:

`sys.path.insert(0,root); ...; runpy.run_module(module, run_name='__main__')`

The four module identities are checked later inside `preflight_authority_invocation()` via `_verify_module_identity()`. But importing `tools.psm_wma.materialize_immutable_source_authority_root` has already executed project code and its top-level imports of `immutable_source_authority_root` and `immutable_source_collection`; those modules transitively import the audit module. Therefore a drifted/shadowed collection or audit module can execute before the formal-tree/raw identity check that is supposed to reject it.

This reintroduces the exact pre-import authority gap that the v0.1 design existed to close. The reported `88/88 PASS` does not satisfy that frozen Evidence contract because the current bootstrap tests cover tampered `-c` payload/argv/flags/contract, while collection/audit raw-identity drift is exercised only through adapter preflight after project import.

### Exact acceptance

Before `sys.path.insert()` or `runpy.run_module()`:

1. extend the stdlib bootstrap contract with the exact formal root, frozen Git executable identity, project root, and all four module `(repo_path, blob_oid, raw_sha256)` identities;
2. using only stdlib plus the already-frozen Git executable/env/prefix, verify clean-root/formal-root identity and for adapter/authority/collection/audit verify:
   - path stays under the frozen root;
   - `lstat` is regular and non-symlink;
   - raw SHA-256 matches;
   - formal-tree entry is exactly `100644 blob <approved_oid>`;
3. fail before any project import, authority Git mutation, ref/evidence write, or project callback if any check differs;
4. add a direct isolated-interpreter adversarial witness that changes only `immutable_source_collection.py` (and separately the audit module), leaving adapter/authority bytes and declared bootstrap digest unchanged, and prove rejection occurs before the project module sentinel/import side effect and before any local/remote ref or evidence path exists;
5. retain all existing bootstrap process-observation, endpoint, Git isolation, common-config, Evidence ABI, CAS and CPU/static contracts.

No real materialization is authorized by this remediation.

## Blocker summary

- implementation blockers: `1 HIGH`
- design blockers: `0` (approved design remains authoritative)
- child/runtime blockers: `0` (not changed by this pair)

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:166)`

This verdict binds only the exact formal pair `bb17774ce6da4e4d14c57993fe97f813065de319 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Scope remains temporary CPU/static only. This review does not authorize real selection/config materialization, candidate/ref/origin mutation, source/checkpoint I/O, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.