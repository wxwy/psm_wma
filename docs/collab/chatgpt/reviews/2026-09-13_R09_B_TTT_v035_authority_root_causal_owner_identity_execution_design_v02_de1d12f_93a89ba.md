# ChatGPT Review — Authority-root Causal Owner Identity Execution Design v0.2

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## Exact formal pair

- root docs SHA: `de1d12f194030067a4afa656379378713b151734`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The exact formal root is independently reachable. At that root, `cosmos-framework` is a submodule/Gitlink to exactly `93a89ba61306d840a008813f62f26a34d54850f4`, and the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh replacement formal pair relative to the prior reviewed `64b706b7b97451fd90cb6e9292100e512952f28a / 93a89ba61306d840a008813f62f26a34d54850f4` pair. The current formal commit adds the v0.2 docs-only design plus task records; child/runtime is unchanged.

The requested verdict is exactly:

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`

or `REQUEST_CHANGES(file:line)`.

Approval at this Gate would authorize only root-only stdlib temporary-fixture CPU/static implementation/tests. It would **not** authorize production/main execution, real materialization, project-path worktree/backing/index/candidate/ref/evidence creation, source/checkpoint I/O, collection/receipt/publication, child/runtime changes, GPU, training, evaluation, inference, or LIBERO4IN1.

## Authority chain used

This review applies the inherited frozen source/raw/config/route and backing `{3,4,5}` contracts, the approved v0.8 static-witness/fail-close closure, and the prior exact-pair v0.1 remediation review. v0.2 may supersede only what it explicitly refreezes. In particular, exact descriptor ownership/inheritance, no post-mutation authority reconstruction, causal owner continuity through the actual consumer, and direct fixture evidence remain mandatory.

## Prior blocker disposition

- Prior HIGH-1 (root/clean owner FD lifecycle internally contradictory): **PARTIALLY CLOSED / STILL BLOCKING**. v0.2 correctly separates long-lived `root_authority_fd=7` from Git-only `git_root_fd=6`, removes stale `parent_fd`, and fixes cleanup to the owned CLEAN entry. However `clean_owner_fd` is left as an unconstrained “ordinary FD”, so its numeric identity can alias the already-frozen backing/Git/bootstrap descriptors and be destroyed by the very `dup2` operations the design requires.
- Prior HIGH-2 (owner continuity ended before exec/bootstrap): **PARTIALLY CLOSED / STILL BLOCKING**. Inheriting a verified `bootstrap_clean_fd=8` and using `/proc/self/fd/8` as bootstrap root is the right mechanism. But v0.2 does not refreeze all post-exec CLEAN-derived argv consumed by the existing adapter: `--cwd` and `--index` remain required adapter inputs and currently drive `NativeAuthorityGit` after bootstrap. Refreezing only the bootstrap project-root field does not eliminate the downstream global-CLEAN re-resolution path.

## Blockers

### HIGH-1 — `clean_owner_fd` has no collision-free numeric contract and can be clobbered by FD 3/4/5/6/8 operations

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.2.md:36` (capability table and section 2 lifecycle), together with the inherited backing `{3,4,5}` handoff contract.

v0.2 freezes `root_authority_fd=7`, Git-only `git_root_fd=6`, and `bootstrap_clean_fd=8`, but defines `clean_owner_fd` only as an “executor ordinary FD”. That is not a safe authority contract.

The inherited launcher handoff ABI materializes the three backing files into exact target descriptors `3`, `4`, and `5` via `dup2(reader_fd, target)`. v0.2 also requires `dup2(7,6)` for each Git child and later `dup2(clean_owner_fd,8)` for bootstrap. An unconstrained `open(...O_DIRECTORY...)` for `clean_owner_fd` can therefore legally return any of `3`, `4`, `5`, `6`, or `8` depending on the executor's current descriptor table.

This is not a theoretical corner case. In a minimal process with only `0/1/2` open, binding ROOT to fixed FD 7 and then opening CLEAN will normally reuse a low descriptor. If `clean_owner_fd==3/4/5`, a backing handoff `dup2(..., target)` destroys the only held CLEAN owner capability. If it is `6`, the required `dup2(7,6)` destroys it before Git. If it is `8`, `dup2(clean_owner_fd,8)` is a no-op, contradicting the design's distinction that the ordinary `clean_owner_fd` is not inherited while a separate bootstrap capability is.

The existing v0.8 production-shape handoff makes this exact risk concrete: target FDs are fixed `3/4/5` and are populated with `dup2` before the final descriptor-set proof. The v0.2 design cannot delegate collision handling to implementation because FD identity and lifetime are the authority mechanism under review.

**Violated frozen contract:** exact FD/inheritance ABI; causal owner capability must remain live through backing/handoff, child execution, and cleanup; no implementation-significant authority choice may be invented after design approval; prior HIGH-1 exact acceptance requiring distinct capability lifetimes and no authority reconstruction.

**Exact acceptance:**

1. Freeze a collision-free numeric/allocation contract for `clean_owner_fd`. A straightforward valid design is a fixed owner FD outside the reserved `{3,4,5,6,7,8}` set (for example FD 9), or an exact `F_DUPFD_CLOEXEC`/equivalent rule with a frozen lower bound and proof that the result is outside every reserved descriptor.
2. Freeze the source-open → rebind/duplicate → `fstat` identity proof → source-close chronology for that owner FD, including its `FD_CLOEXEC` state and exact close point after child exit/cleanup.
3. Freeze occupancy handling for reserved descriptors before any mutation. No required `dup2` may silently close `clean_owner_fd` or another retained authority capability.
4. Preserve the owner FD unchanged while targets `3/4/5` are populated, while Git-only FD 6 is created/closed, and while the separate bootstrap FD 8 is created.
5. Add temporary-only causal witnesses starting from both a minimal low-FD table and adversarial preoccupied descriptors, proving that `3/4/5/6/8` operations never alias or destroy the retained owner capability.

### HIGH-2 — FD8 anchors only bootstrap loading; post-exec adapter argv still reintroduces absolute CLEAN through `--cwd` / `--index`

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.2.md:24` and `:81-89`, together with frozen adapter `tools/psm_wma/materialize_immutable_source_authority_root.py` (`_parser`, `_bootstrap_identity_from_runtime`, and `main`).

v0.2 says pre-exec absolute `--cwd` / `--index` fields are no longer allowed to become a post-exec project-root source, then explicitly refreezes `BOOTSTRAP_OWNER_ROOT_FD=8` and supersedes the old `--bootstrap-project-root=/disk/.../CLEAN` bootstrap field. That closes the module-loader portion of the prior race, but it does not close the actual adapter transaction.

The frozen adapter source currently:

- requires `--cwd`, `--index`, and `--bootstrap-project-root` in its parser;
- compares `bootstrap_project_root.resolve()` to `cwd.resolve()` in `_bootstrap_identity_from_runtime`;
- constructs `NativeAuthorityGit(args.git, args.cwd, args.remote, args.index, ...)` in `main`;
- performs Git/config/module verification and later transaction work through that `cwd` and `index`.

The inherited frozen argv currently binds both `--cwd` and `--index` to the global CLEAN pathname. v0.2 item 4 explicitly supersedes bootstrap payload/hash, full argv digest, final FD set, and the old `--bootstrap-project-root` field, but it never freezes what the child-visible `--cwd` and `--index` become, nor does it authorize/refreeze an adapter ABI change. Therefore an implementation conforming literally to this design can load the bootstrap/module from held FD8 and then immediately hand the adapter a replaceable global CLEAN path again. That fails the prior exact acceptance to refreeze **every affected path-bearing field** or define an exact procfd-root derivation through the actual consumer.

This is also an implementability gap: the next authorized scope is root-only stdlib temporary-fixture implementation/tests, while source identity is declared unchanged. The implementation must not invent whether to rewrite child argv to `/proc/self/fd/8`, modify `sys.orig_argv`, change the adapter parser, or change adapter bytes. Those choices affect the frozen bootstrap digest, invocation identity, Git cwd/index, and evidence semantics.

**Violated frozen contract:** causal object identity through the actual consumer; no absolute CLEAN fallback after authority binding; exact argv/bootstrap ABI; source/module identity; prior HIGH-2 exact acceptance requiring every affected path-bearing argv/bootstrap field to be refrozen or derived from the retained owner capability.

**Exact acceptance:**

1. Explicitly refreeze the child-visible values/semantics of every CLEAN-derived post-exec field, at minimum `--cwd`, `--index`, and `--bootstrap-project-root`, so they derive from FD8 (for example `/proc/self/fd/8` and `/proc/self/fd/8/.authority-root.index`) and never re-resolve `/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8` after exec admission.
2. Reconcile this with the **actual frozen adapter**. Either prove the unchanged adapter works with the procfd-derived argv under its existing `_bootstrap_identity_from_runtime`, parser, `NativeAuthorityGit`, module-identity, and evidence rules, or explicitly move any necessary adapter/source change into an authorized design/refreeze with new exact module bytes/blob/hash authority. Do not leave argv rewriting or `sys.orig_argv` behavior to implementation invention.
3. Freeze the complete new child argv and digest, including which old absolute CLEAN fields are removed, retained for executor-only use, or replaced by procfd-derived values. “Bootstrap ignores the absolute root” is insufficient if the adapter later consumes it.
4. Extend the mandatory final-seam fixture through the **real bootstrap → adapter transaction boundary**: after the last executor pathname check, replace global CLEAN before child consumption. The child must use only the held owner inode for module/cwd/index access, or fail closed before any foreign worktree/module/index/Git consumption; the foreign replacement must remain untouched.
5. Preserve existing raw/config/route/backing and post-mutation cleanup contracts; no real materialization or production/main execution is authorized by this design review.

## Blocker summary

- current blockers: `2 HIGH`
- design/authority blockers: `2 HIGH`
- child/runtime blockers: `0`
- prior root-FD naming/cleanup contradiction: materially improved
- prior bootstrap owner-capability direction: materially improved
- remaining blockers are exact FD collision safety and end-to-end propagation of the owner root into the actual adapter transaction

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.2.md:36)`

This verdict binds only exact pair `de1d12f194030067a4afa656379378713b151734 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No CPU/static implementation is authorized from this pair. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
