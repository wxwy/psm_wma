# ChatGPT Review — Authority-root Causal Owner Identity CPU/static Implementation

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `5a2a3207853cdbbe4dc8135080cd5fe5050b7787`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. At that exact root, `cosmos-framework` is a submodule/Gitlink to exactly `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh implementation pair relative to the approved docs-only design pair `76210e7bcbdc606e39775e2dae258542cf3c0d38 / 93a89ba61306d840a008813f62f26a34d54850f4`. The implementation delta is root-only: `tools/psm_wma/materialize_immutable_source_authority_root.py`, its direct stdlib CPU test, and task/reviewer bookkeeping; child/runtime is unchanged.

Requested verdict:

`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`

or `REQUEST_CHANGES(file:line)`.

This Gate is limited to root-only stdlib temporary-fixture CPU/static implementation/tests. It does not authorize production/main execution, real materialization, project-path authority artifacts, source/checkpoint I/O, collection/receipt/publication, child/runtime changes, GPU, training, evaluation, inference, or LIBERO4IN1.

## Frozen authority used

The controlling authority is the approved v0.4 causal-owner design. In particular:

- final post-exec owner ABI is exact FD8: `--cwd /proc/self/fd/8`, `--index /proc/self/fd/8/.authority-root.index`, `--bootstrap-project-root /proc/self/fd/8`, and mandatory `--bootstrap-owner-root-fd 8`;
- every post-exec Git consumer of an FD8-derived path uses exact `close_fds=True, pass_fds=(8,)` with pre/post owner/index identity barriers;
- project/module/index/cwd/repository-boundary authority remains FD8-anchored and must not be reconstructed through global CLEAN;
- bootstrap module closure and adapter module checks use component-by-component no-follow traversal from the retained owner FD;
- `_bootstrap_identity_from_runtime()` must not canonicalize FD8-derived owner paths with `Path.resolve()`;
- `_verify_loaded_identity()` must prove loaded module identity is the FD8-owner-tree object, not merely same bytes at an arbitrary pathname.

## Positive implementation findings

The implementation does correctly add several required pieces:

- `_read_regular_relative()` provides a useful component-by-component `dir_fd` + `O_NOFOLLOW` primitive for adapter-side module reads;
- `NativeAuthorityGit` stores owner/index inode identity and passes the owner FD to Git consumers with `close_fds=True` and `pass_fds=(owner_fd,)`, with pre/post identity barriers;
- direct tests include an actual temporary Git consumer using a procfd cwd/index and a changed-index rejection witness;
- owner-mode configuration handling removes the old unconditional `self.cwd.resolve()` repository-boundary dependency.

These improvements do not close the Gate because the remaining violations are in production source, not only Evidence.

## Blockers

### HIGH-1 — FD8 owner ABI is still optional and non-exact, so direct adapter/bootstrap invocation can bypass the frozen causal-owner route

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:1747` (`_parser`), plus `bootstrap_payload()` owner parsing and `NativeAuthorityGit.__init__`.

The frozen v0.4 ABI requires the final owner capability to be exactly FD8 and requires `--bootstrap-owner-root-fd 8` as part of the exact final argv. The implementation instead keeps the field optional:

- bootstrap uses `optional('--bootstrap-owner-root-fd')` and permits the field to be absent;
- argparse declares `--bootstrap-owner-root-fd` without `required=True`;
- `NativeAuthorityGit` accepts any integer owner FD as long as cwd/index are `/proc/self/fd/<that fd>`.

If the flag is absent, the code continues through the legacy pathname route (`owner_fd=None`) rather than failing closed. If another descriptor number is supplied, it can become the owner authority even though the design froze FD8 specifically. This creates a second admission/authority path and violates the exact post-exec ABI.

**Violated frozen contract:** v0.4 §2 exact final argv/FD mapping; inherited v0.3 requirement that parser add a required `--bootstrap-owner-root-fd`; activation/fail-closed rule forbidding fallback to global pathname authority when the owner route is active.

**Why existing Evidence does not close it:** current owner bootstrap tests append `--bootstrap-owner-root-fd 8` on the positive path, but do not prove missing owner, non-8 owner, or direct adapter invocation fail closed before project/Git/module consumption. Passing the positive path does not remove the alternate legacy route from production.

**Exact acceptance:**

1. make `--bootstrap-owner-root-fd` mandatory for this causal-owner implementation path;
2. require its exact value to be `8` in bootstrap, parser/admission, and `NativeAuthorityGit` owner binding;
3. require exact `cwd=/proc/self/fd/8`, `index=/proc/self/fd/8/.authority-root.index`, and `bootstrap-project-root=/proc/self/fd/8` before any owner-path project/Git/module consumption;
4. add direct negative witnesses for missing flag, non-8 flag, mismatched procfd cwd/index/root, and direct `main()`/adapter admission, proving no legacy pathname fallback occurs.

### HIGH-2 — Import-free bootstrap still verifies project modules through pathname strings rather than the frozen FD8 component-by-component no-follow primitive

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:335-339` (`bootstrap_payload()` project-module loop).

v0.4 §4.2 explicitly requires the bootstrap closure for adapter/authority/collection/audit modules to start from FD8 and traverse every relative component with `dir_fd` + `O_NOFOLLOW` (or an exactly equivalent no-follow FD-anchored primitive). The implementation added `_read_regular_relative()` for adapter-side Python code, but the import-free bootstrap still does:

- `full = os.path.abspath(os.path.join(root, path))` where `root=/proc/self/fd/8`;
- `os.lstat(full)` on only the resulting leaf pathname;
- `open(full, 'rb')` to hash module bytes.

`lstat(full)` does not provide component-by-component no-follow protection: an intermediate component under the held owner tree can be replaced by a symlink and pathname traversal can follow it before reaching the final leaf. Disabling the old `realpath(full)==full` check in owner mode therefore removes one old guard without installing the frozen replacement in bootstrap.

**Violated frozen contract:** v0.4 §4.2 bootstrap module closure; preserved anti-symlink/route authority; causal owner object identity through actual bootstrap consumer.

**Why existing Evidence does not close it:** `test_no_follow_relative_module_reader_rejects_component_symlink` exercises the Python helper `_read_regular_relative()`, not the import-free bootstrap module loop. `test_bootstrap_rejects_module_symlink_before_import` covers a leaf module symlink, not an intermediate-component symlink through the actual FD8 bootstrap path. The contract requires the production bootstrap itself to be causally protected.

**Exact acceptance:**

1. implement an import-free FD8-relative component traversal in `bootstrap_payload()` (or an exactly equivalent frozen primitive) that opens each directory component with `O_DIRECTORY|O_NOFOLLOW`, opens the leaf with `O_NOFOLLOW`, validates types by `fstat`, and hashes bytes from the opened FD;
2. use it for all four formal project modules before `sys.path`/`runpy`;
3. retain formal-tree blob/raw-SHA checks and fail before import/Git/Evidence consumption on any component/leaf drift;
4. add a direct isolated bootstrap witness replacing an intermediate module path component with a foreign symlink after owner binding; foreign module bytes must never be imported or accepted.

### HIGH-3 — Adapter-side owner verification still canonicalizes procfd paths and does not prove loaded-module path identity belongs to the FD8 owner tree

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:374` (`_bootstrap_identity_from_runtime`) and `:517-533` (`_verify_loaded_identity`).

Two v0.4 requirements remain only partially implemented.

First, `_bootstrap_identity_from_runtime()` still performs:

`args.bootstrap_project_root.resolve() != args.cwd.resolve()`

on FD8-derived owner paths. v0.4 explicitly named this function and prohibited `Path.resolve()` from canonicalizing the procfd owner route back into a global pathname authority. The correct check is the exact raw procfd ABI plus FD8 identity, not a global-path equality proof.

Second, `_verify_loaded_identity()` now reads expected bytes from the owner FD tree, which is useful, but it validates the actually loaded adapter/authority modules only by hashing `Path(__file__).read_bytes()` and `Path(authority_module.__file__).read_bytes()`. It never maps those loaded-module paths back to the frozen FD8-relative component sequence and proves they are the same owner-tree objects. A foreign pathname containing identical bytes can therefore satisfy the loaded-module check even though v0.4 requires owner-tree object identity, not same-content equivalence.

**Violated frozen contract:** v0.4 §4.1 and §4.3 exact procfd-safe replacement semantics; no post-exec global CLEAN canonicalization; loaded-module identity must remain FD8-owner anchored.

**Why existing Evidence does not close it:** the tests demonstrate FD-relative helper reads and selected replacement behavior, but do not make `_bootstrap_identity_from_runtime()` fail if procfd is canonicalized through `resolve`, nor do they prove a same-bytes foreign loaded module is rejected by `_verify_loaded_identity()` because its loaded path is outside the owner tree.

**Exact acceptance:**

1. replace the `bootstrap_project_root.resolve()==cwd.resolve()` owner check with exact raw `/proc/self/fd/8` field equality plus live FD8 directory/identity validation, while retaining any legacy non-owner behavior only if a separate already-authorized route truly requires it;
2. make `_verify_loaded_identity()` bind actual loaded adapter/authority module paths to their FD8-relative component sequences and revalidate through the no-follow owner traversal/object identity contract, not only SHA equality;
3. add a direct same-bytes foreign-module witness proving a module loaded from outside the FD8 owner tree is rejected even if bytes/hash match;
4. add a direct owner bootstrap witness proving no `Path.resolve()`/global CLEAN equivalence is needed for acceptance.

## Evidence assessment

The reported `62/62` CPU tests, `py_compile`, and `git diff --check` are useful auxiliary signals, but they do not close the above production violations. The test suite contains real temporary Git coverage for FD inheritance/index drift, but the missing-owner/non-8 admission, import-free bootstrap intermediate-component traversal, and same-bytes foreign loaded-module identity are not directly witnessed.

This is therefore a **production-blocking** review, not an Evidence-only review.

## Blocker summary

- current blockers: `3 HIGH`
- production/authority blockers: `3 HIGH`
- Evidence-only blockers: `0`
- child/runtime blockers: `0`
- FD8 Git-consumer `pass_fds` + pre/post index barrier: materially implemented
- remaining blockers: exact FD8 admission/fail-closed, import-free bootstrap no-follow traversal, and complete procfd/loaded-module owner identity

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:1747)`

This verdict binds only exact pair `5a2a3207853cdbbe4dc8135080cd5fe5050b7787 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No Gate closure is authorized from this pair. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
