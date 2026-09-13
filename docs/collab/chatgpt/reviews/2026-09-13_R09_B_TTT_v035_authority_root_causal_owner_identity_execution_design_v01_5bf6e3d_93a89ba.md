# ChatGPT Review — Authority-root Causal Owner Identity Execution Design v0.1

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## Exact formal pair

- root docs SHA: `5bf6e3d033d2ad6d9f68483c629f2d852f6a8b9d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and the child commit is reachable in `wxwy/cosmos-framework`. This is a fresh formal pair relative to the prior reviewed `145f0d4af0b75165569e7b241841cd078e8359dd / 93a89ba61306d840a008813f62f26a34d54850f4` pair.

This Gate is docs-only design. It requests only `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`; it does not authorize real materialization, project-path source/checkpoint I/O, child/runtime changes, GPU, training, evaluation, inference, or LIBERO4IN1.

## Authority chain used

The review applies the inherited v0.2/v0.3 frozen launcher/bootstrap ABI and exact raw argv/path authorities, the v0.4 mutation/cleanup fail-stop rules, the v0.8 static-witness closure, and this v0.1 document only where it explicitly supersedes those clauses. Untouched exact path authority, FD 3/4/5 handoff ABI, post-mutation fail-stop, and direct causal evidence requirements remain in force.

I independently probed the proposed Linux `/proc/self/fd/<parent_fd>/CLEAN` mechanism in a temporary local Git fixture. The mechanism itself is feasible in principle: native Git can add and remove a worktree through the proc-FD path and resolve the worktree to the underlying real directory. That feasibility does not close the design gaps below.

## Prior blocker disposition

The prior v0.8 HIGH concerning post-add pathname ownership is **CLOSED for the prior static-witness Gate** by fail-closing after native add. This new design correctly attempts to move the ownership bind before the Git mutation instead of inferring ownership after Git returns. No prior launcher blocker is mechanically carried forward; the findings below are new design blockers in this execution-capable successor.

## Blockers

### HIGH-1 — the new private authority parent is incompatible with the still-frozen CLEAN/bootstrap path ABI and is itself not anchored to an explicit canonical authority path

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md`, §2, especially step 1 (around line 23).

The design states that the `authority parent` is a mode-0700 private directory newly created by this executor and that the fixed-name `CLEAN` is created underneath it. However the inherited launcher/bootstrap authority has not been superseded: `CLEAN` is still frozen as `/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8`, and the embedded raw argv still freezes `--cwd`, `--index`, and `--bootstrap-project-root` to that same absolute directory.

Those two authorities cannot both be true without an explicit mapping/refreeze. If `parent` is a newly created private directory, `parent/CLEAN` is not the inherited absolute CLEAN. If `parent` is intended to be `/disk/rl/psm_wma`, it is not a newly created private 0700 directory. The design therefore leaves the execution target ambiguous and would allow an implementation to satisfy the causal-owner mechanism while pointing Git at a directory different from the one the frozen bootstrap later validates and imports from.

There is a second authority problem in the same step: the design says the private parent is created by this executor, but does not define the already-trusted directory FD/path authority under which that private parent is created and bound. Without that anchor, the design merely moves the create→first-bind ownership problem up one directory level.

**Violated frozen contract:** inherited exact launcher/bootstrap path ABI; authority hierarchy rule that later documents supersede only explicit clauses; causal owner identity requirement.

**Exact acceptance:**
1. Freeze one canonical authority anchor and one canonical CLEAN path. Preferably bind the already-authoritative project `ROOT` directory as the stable parent FD and create the existing fixed child `.authority-root-materialization-9dd2fb8` directly under it, preserving `CLEAN`, `--cwd`, `--index`, and `--bootstrap-project-root` byte-for-byte.
2. If a new private parent is truly required, explicitly supersede and refreeze every path-bearing launcher/bootstrap/raw-argv field that changes, including CLEAN/cwd/index/bootstrap-project-root, and define how the private parent itself is causally anchored to a pre-existing trusted FD. Do not leave the mapping to implementation choice.
3. Freeze the exact parent-entry names, modes, absence predicates, and identity transition used before first Git mutation.
4. Add CPU/static witnesses for parent-entry replacement/drift before and after CLEAN creation, and for the positive proc-FD add/remove path using the exact frozen path mapping.

### HIGH-2 — causal owner authority is not carried through backing-file handoff and final bootstrap/exec; a post-validation pathname replacement can still redirect later mutation/consumption

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md`, §§2–4.

The design freezes proc-FD authority for native Git add/status/list and cleanup, but stops before defining how the retained `clean_fd` governs the later backing-file handoff and final bootstrap transition. The inherited v0.8 launcher still creates backing files through the global expression `CLEAN + "/" + name` and passes an absolute `--bootstrap-project-root`/`--cwd` string. Therefore a replacement after the design's post-add identity check but before backing creation or final exec can again redirect mutation/consumption to a foreign inode even though the earlier Git worktree checks passed.

This is the same class of authority discontinuity the new Gate is supposed to eliminate; moving only Git operations to proc-FD paths is insufficient unless the owner capability remains authoritative until the last irreversible handoff.

The design also says `parent_fd` has a fixed inherited FD number but does not freeze that number, prove it cannot collide with the inherited exact backing FD ABI `{3,4,5}`, or define the retirement order for `parent_fd`/`clean_fd` before the final exact-FD check and `execve`.

**Violated frozen contract:** exact-object/authority continuity through mutation; inherited FD 3/4/5 ABI; post-mutation fail-stop; no pathname fallback for causal authority.

**Exact acceptance:**
1. Freeze that every backing-file create/open/readback/mode/identity check is relative to the retained `clean_fd` (or an equivalently exact held owner capability), never by reopening global `CLEAN` pathname.
2. Immediately before bootstrap/exec, prove that the frozen absolute CLEAN/bootstrap path still resolves to the same `(dev, ino)` as `clean_fd`; any replacement/missing/symlink/drift is `ROLLBACK_INCOMPLETE` before exec.
3. Freeze `parent_fd` and `clean_fd` numeric/lifecycle constraints: neither may alias FD 3/4/5; `clean_fd` must not leak to Git unless explicitly required; both owner FDs must be retired at a precisely defined point before the inherited exact `{3,4,5}` final descriptor-set proof and `execve`.
4. Extend the CPU/static matrix with direct witnesses for replacement after successful Git validation but before backing handoff, replacement after backing handoff but before exec admission, and FD-number/CLOEXEC/pass_fds collision cases. The witnesses must prove no foreign inode receives backing files and no extra owner FD reaches final exec.

## Blocker summary

- current blockers: `2 HIGH`
- child/runtime blockers: `0`
- design/authority blockers: `2 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md:23)`

This verdict binds only exact pair `5bf6e3d033d2ad6d9f68483c629f2d852f6a8b9d / 93a89ba61306d840a008813f62f26a34d54850f4`.

No CPU/static implementation is authorized from this pair. No real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.
