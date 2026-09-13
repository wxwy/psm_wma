# ChatGPT Review — Authority-root Causal Owner Identity Execution Design v0.3

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## Exact formal pair

- root docs SHA: `781824f4ed2682b1347126a58f645ef0702117bd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. At that exact root, `cosmos-framework` is a submodule/Gitlink to exactly `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior ChatGPT-reviewed v0.2 pair `de1d12f194030067a4afa656379378713b151734 / 93a89ba61306d840a008813f62f26a34d54850f4`. The current formal commit adds the docs-only v0.3 design plus task records; child/runtime is unchanged.

Requested verdict:

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`

or `REQUEST_CHANGES(file:line)`.

Approval at this Gate would authorize only root-only stdlib temporary-fixture CPU/static implementation/tests. It would not authorize production/main execution, real materialization, project-path authority artifacts, source/checkpoint I/O, collection/receipt/publication, child/runtime changes, GPU, training, evaluation, inference, or LIBERO4IN1.

## Authority chain used

This review applies the inherited frozen source/raw/config/route and backing `{3,4,5}` contracts, the approved v0.8 authority-root static/fail-close contracts, the prior v0.1/v0.2 causal-owner reviews, and v0.3 only where it explicitly refreezes them. Causal owner identity must survive into the actual post-exec consumer; no implementation-significant authority/inheritance choice may be invented after design approval.

## Prior blocker disposition

- Prior HIGH-1 (`clean_owner_fd` collision/lifecycle): **CLOSED**. v0.3 reserves `{3,4,5,6,7,8,9}` pre-mutation, fixes long-lived `clean_owner_fd=9`, freezes temporary-open → `dup2(...,9)` → `fstat` identity proof → source close, keeps FD9 unchanged across backing/Git/bootstrap operations, and requires direct low-FD/adversarial witnesses.
- Prior HIGH-2 (FD8 reached bootstrap but not the actual adapter transaction): **PARTIALLY CLOSED / STILL BLOCKING**. v0.3 correctly refreezes child-visible `--cwd`, `--index`, `--bootstrap-project-root`, and `--bootstrap-owner-root-fd` to FD8/procfd bytes and explicitly puts root adapter source changes in the next implementation scope. However the design still stops short of freezing two authority-critical details required by the existing bootstrap/adapter source: descendant subprocess FD8 inheritance, and procfd-safe route/module/config identity checks that do not canonicalize back into global pathnames.

## Blockers

### HIGH-1 — FD8 is frozen only for the bootstrap/adapter process, not for Git subprocesses that must dereference `/proc/self/fd/8/.authority-root.index`

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.3.md:71-72` (section 3, `NativeAuthorityGit` contract); current source `tools/psm_wma/materialize_immutable_source_authority_root.py`, `NativeAuthorityGit._run_bytes()` / `_mutation_succeeded()` and bootstrap `grun()`.

v0.3 freezes final child inheritance to exactly `{3,4,5,8}` and then freezes adapter argv to:

- `--cwd /proc/self/fd/8`
- `--index /proc/self/fd/8/.authority-root.index`

The existing `NativeAuthorityGit` launches every real Git command through `subprocess.run(..., cwd=self.cwd, env=self.env, ...)` with `GIT_INDEX_FILE=str(index)` and no `pass_fds`. The bootstrap payload likewise launches Git with `cwd=root` and no descendant FD contract.

`/proc/self/fd/8/.authority-root.index` is an FD-relative pathname only while FD8 exists in the process that opens it. The current design says which descriptors reach the bootstrap/adapter child, but says nothing about which descriptors reach the Git grandchildren that actually consume `GIT_INDEX_FILE` and repository paths. With the current source shape, implementation would have to invent whether FD8 is inherited by those subprocesses, whether only cwd is allowed to survive by `chdir`, or whether another authority translation is permitted. In particular, a Git process that receives `GIT_INDEX_FILE=/proc/self/fd/8/.authority-root.index` without FD8 cannot use the frozen index authority.

This is an authority/lifecycle contract, not a test-detail omission. The owner capability must remain causally live through the actual consumer, not just through Python argument parsing.

**Violated frozen contract:** causal owner continuity through the actual consumer; exact descriptor inheritance; no global CLEAN fallback/reconstruction; no implementation-significant authority choice after design approval.

**Why current Evidence plan does not close it:** the v0.3 end-to-end seam requires bootstrap→adapter behavior, but the design does not specify the descriptor contract of the Git subprocesses inside that seam. A future test could accidentally pass by depending on platform-specific subprocess/chdir behavior while the `GIT_INDEX_FILE` authority is still absent in the Git process.

**Exact acceptance:**

1. Freeze the descendant descriptor contract for every post-exec subprocess that dereferences an FD8-derived pathname, including bootstrap Git probes and all `NativeAuthorityGit` commands.
2. If procfd strings remain the authority, require an exact `close_fds` / `pass_fds` policy that keeps FD8 live in those consumers (for example `close_fds=True, pass_fds=(8,)`, or an explicitly equivalent frozen mechanism), while preventing unintended `{3,4,5}` leakage.
3. Freeze pre/post subprocess identity checks proving descendant FD8 still denotes the same bound CLEAN inode; failures must occur before foreign worktree/index/Git consumption.
4. Extend the temporary isolated witness through an actual Git operation that consumes the FD8-derived index after the global CLEAN entry has been replaced; it must use the held inode or fail closed before foreign consumption.

### HIGH-2 — The existing bootstrap/adapter identity checks are path-canonicalization based and are incompatible with the new procfd authority unless their replacement semantics are explicitly frozen

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.3.md:68-72`; current source `bootstrap_payload()`, `_bootstrap_identity_from_runtime()`, `_verify_loaded_identity()`, `NativeAuthorityGit._repository_directory()` / `verify_configuration_authority()`.

v0.3 correctly forbids `_bootstrap_identity_from_runtime()` from applying `Path.resolve()` to FD8-derived cwd/root. But the actual frozen root adapter has additional global-path canonicalization in the authority chain that v0.3 does not refreeze:

- the import-free `bootstrap_payload()` rejects module and route paths unless `os.path.realpath(path) == path`;
- `_verify_loaded_identity()` resolves `(cwd / repo_path)`, `__file__`, and loaded authority module paths;
- `NativeAuthorityGit._repository_directory()` resolves returned repository directories, and `verify_configuration_authority()` calls `self.cwd.resolve()` before repository-root checks.

For a frozen argv root of `/proc/self/fd/8`, `realpath`/`resolve` dereferences the procfd link into a global pathname. At minimum, the current bootstrap module check `os.path.realpath(full) != full` is directly incompatible with a `full` path rooted under `/proc/self/fd/8`; unchanged source therefore rejects the proposed procfd route before `runpy`. Simply deleting these checks in implementation would also be unacceptable because they currently enforce anti-symlink/route constraints. The design must freeze the procfd-safe replacement authority, not leave that security semantic to implementation invention.

**Violated frozen contract:** no post-exec global CLEAN fallback; causal object identity through the actual consumer; source/module/route/config identity must remain fail-closed; only explicitly refrozen source semantics may replace prior checks.

**Why current Evidence plan does not close it:** the witness table says the adapter must reject `resolve/global fallback`, but does not define the replacement mechanism for the existing bootstrap/module/config anti-symlink and repository-boundary checks. The same test could be made to pass by weakening or deleting those checks while silently losing the prior route/config authority.

**Exact acceptance:**

1. Explicitly refreeze the procfd-safe bootstrap route/module identity algorithm that replaces every `realpath(path)==path` check affected by FD8. The replacement must preserve non-symlink, exact inode/bytes, repository-route, and fail-closed semantics without turning `/proc/self/fd/8` into a mutable global CLEAN pathname.
2. Explicitly refreeze the corresponding adapter-side loaded-module and Git configuration/repository-boundary checks (`_verify_loaded_identity`, `_repository_directory`, `verify_configuration_authority`) so they remain anchored to the FD8 owner capability rather than `Path.resolve()` of FD8-derived paths.
3. Freeze what path values may legitimately be global (for example Git administrative paths outside the owned CLEAN inode) versus which values must remain owner-FD anchored; no ambiguous runtime canonicalization/fallback is allowed.
4. Add direct replacement/rename witnesses at the bootstrap module check and adapter configuration/module check seams, proving foreign paths are neither consumed nor accepted and prior anti-symlink/route guarantees are preserved.

## Blocker summary

- current blockers: `2 HIGH`
- design/authority blockers: `2 HIGH`
- child/runtime blockers: `0`
- prior FD collision blocker: `CLOSED`
- remaining blockers: descendant FD8 inheritance into the actual Git consumer, and procfd-safe replacement of the existing global-path canonicalization authority checks

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.3.md:71)`

This verdict binds only exact pair `781824f4ed2682b1347126a58f645ef0702117bd / 93a89ba61306d840a008813f62f26a34d54850f4`.

No CPU/static implementation is authorized from this pair. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
