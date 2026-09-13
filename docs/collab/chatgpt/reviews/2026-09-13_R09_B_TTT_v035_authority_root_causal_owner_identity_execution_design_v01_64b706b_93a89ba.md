# ChatGPT Review — Authority-root Causal Owner Identity Execution Design v0.1 Remediation

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## Exact formal pair

- root docs SHA: `64b706b7b97451fd90cb6e9292100e512952f28a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The exact formal root is independently reachable. Its `cosmos-framework` entry is a submodule/Gitlink to exactly the stated child, and the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh replacement formal pair relative to the prior reviewed `5bf6e3d033d2ad6d9f68483c629f2d852f6a8b9d / 93a89ba61306d840a008813f62f26a34d54850f4` pair. The earlier malformed `64b706b7d8dc...` request is explicitly superseded by live `CODEX_INBOX.md` and is not reviewed here. The effective formal delta is docs/coordination only; child/runtime is unchanged.

The requested verdict is exactly:

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`

or `REQUEST_CHANGES(file:line)`.

Approval at this Gate would authorize only root-only stdlib temporary-fixture CPU/static implementation/tests. It would **not** authorize real materialization, project-path worktree/backing/index/candidate/ref/evidence creation, source/checkpoint I/O, collection/receipt/publication, child/runtime changes, GPU, training, evaluation, inference, or LIBERO4IN1.

## Authority chain used

This review applies the inherited v0.2/v0.3 frozen execution/bootstrap/input ABI, the v0.4 launcher ownership/cleanup and post-mutation fail-stop rules, the approved v0.8 static-witness/PREPARE closure, and the prior exact-pair causal-owner design review. The new v0.1 remediation may supersede only what it explicitly refreezes; unchanged path bytes, bootstrap bytes, FD ABI, fail-closed rules, and causal Evidence requirements remain authoritative.

## Prior blocker disposition

- Prior HIGH-1 (private parent conflicted with frozen absolute CLEAN/cwd/index/bootstrap root): **CLOSED**. The replacement design now explicitly keeps authority parent at frozen `ROOT=/disk/rl/psm_wma`, keeps CLEAN at `/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8`, and states that `--cwd`, `--index`, and `--bootstrap-project-root` bytes remain unchanged.
- Prior HIGH-2 (owner authority did not cover backing handoff and final bootstrap/exec): **PARTIALLY CLOSED / STILL BLOCKING**. Backing create/open/readback is now specified relative to `clean_fd`, which is the correct direction. The design still does not preserve an unbroken owner capability through the final exec/bootstrap consumer, and its root-FD lifecycle is internally inconsistent.

## Blockers

### HIGH-1 — root/clean owner FD lifecycle is internally contradictory and leaves security-critical implementation choices unfrozen

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md:27` (section 2 steps 2–4 and the implementation matrix/lifecycle paragraph).

The remediation correctly chooses the frozen project `ROOT` as the authority parent, but the exact FD contract is not coherent enough to implement without inventing semantics:

1. Step 1 creates `root_fd` with `O_CLOEXEC` and says all child operations use that `root_fd` as `dir_fd`.
2. Step 2 immediately switches to the undefined/stale name `parent_fd` for `mkdir`, `open`, and `stat`.
3. Step 3 says to make **`root_fd` itself fixed FD 6** and pass only FD 6 to Git.
4. The matrix/lifecycle paragraph later says `root_fd=6` is inherited only during Git and is **closed after Git**, but in the same paragraph says **every handoff and exec admission must use `root_fd`** to revalidate absolute CLEAN.
5. Section 3 still speaks of `clean_fd/parent_fd` dual verification and says cleanup should revalidate an “empty parent”. After the remediation the parent is the live project `ROOT`; it must never be emptied or treated as a disposable owner directory.

This is not merely naming polish. A security-sensitive implementation must know whether there is a long-lived root-authority FD plus a temporary FD-6 duplicate, or whether FD 6 is the only root capability; it must also know the exact duplication direction, identity checks, `FD_CLOEXEC` state, `pass_fds` behavior, and close points. As written, one conforming implementation could close its only root authority after Git while another could retain a second undeclared capability. Those are materially different authority models.

**Violated frozen contract:** exact authority/object identity; fail-closed chronology; no post-mutation authority reconstruction; exact FD/inheritance ABI; design must freeze implementation-significant security choices before CPU/static implementation is authorized.

**Why current evidence is insufficient:** the cited temporary Git probe only shows that Git accepts a precreated empty directory. It does not resolve which root capability remains authoritative after Git, and this Gate is design-only; implementation/tests cannot be allowed to choose an unreviewed FD lifecycle themselves.

**Exact acceptance:**

1. Freeze distinct names and lifetimes for every capability. If intended, define e.g. a long-lived `root_authority_fd` and a temporary `git_root_fd=6` duplicate; specify the exact `dup2`/rebind direction, pre/post `fstat` equality, `FD_CLOEXEC` state, `pass_fds`, `close_fds`, and the exact point where FD 6 is closed while the long-lived authority remains valid.
2. Use one name consistently (`root_authority_fd` or equivalent); remove every stale `parent_fd` reference.
3. Freeze `clean_fd` lifetime through all owner-relative backing operations and all cleanup/admission checks that require it; no authority may be reconstructed from a global pathname after its retained capability has been closed.
4. Correct cleanup semantics: `ROOT` is never an “empty parent” to remove or empty. Freeze cleanup around the owned CLEAN entry/worktree only, then verify the CLEAN entry is absent or unchanged according to the terminal state while preserving the project root.
5. Specify exact pre-mutation vs post-mutation failure classification for FD duplication/inheritance/revalidation/close failures. Once native Git may have mutated state, uncertainty remains `ROLLBACK_INCOMPLETE`.

### HIGH-2 — causal owner continuity still ends before `execve`; frozen absolute bootstrap root reopens the replacement race

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md:71` (final FD lifecycle / exec-admission paragraph), together with the inherited frozen bootstrap/root ABI.

The remediation improves backing handoff by making backing file create/open/readback relative to `clean_fd`. However the final consumer is still outside the retained owner capability:

- the design freezes the final durable descriptor set as exactly `{3,4,5}`;
- therefore `root_fd`/its authority duplicate and `clean_fd` are closed before final descriptor-set proof and `execve`;
- the design says the last absolute-CLEAN→`clean_fd` identity check occurs immediately before exec admission, but after those owner FDs are closed the check is only historical;
- inherited argv still freezes `--bootstrap-project-root=/disk/rl/psm_wma/.authority-root-materialization-9dd2fb8` and related absolute path fields;
- the inherited bootstrap then resolves the project root / `.git` / module files from that absolute root and eventually inserts that root into `sys.path` before `runpy.run_module(...)`.

Consequently a replacement after the final FD-based check but before or during bootstrap pathname/module lookup can redirect the consumer to a foreign CLEAN inode. “Revalidate immediately before exec” does not establish object continuity across `execve`; it is a classic check-then-use gap. The design therefore still does not satisfy the prior acceptance that causal owner authority must survive through the actual backing/bootstrap/exec consumer rather than stop at an admission check.

This also conflicts with the new matrix row that claims “exec前绝对CLEAN与`clean_fd`重验” is sufficient. That witness can prove detection **before** the FDs are closed, but cannot prove what object the post-exec bootstrap actually consumes after the retained owner handle is gone.

**Violated frozen contract:** causal object identity through the consumer; prior HIGH-2 acceptance; no pathname fallback after authority binding; exact bootstrap/FD ABI; direct causal Evidence principle.

**Exact acceptance:**

1. Freeze an execution ABI in which owner authority survives across the actual consumer lookup, not merely up to a pre-exec check. A valid design can, for example, explicitly refreeze a verified owner/root FD as an inherited bootstrap capability and make bootstrap/root/module resolution use `/proc/self/fd/<owner-fd>` (or an equivalent immutable-handle mechanism) with **no absolute-path fallback**.
2. If the final FD set must change from `{3,4,5}`, explicitly refreeze the exact FD numbers, purpose, inheritance/CLOEXEC behavior, argv/contract mapping, closure chronology, and all affected bootstrap bytes/hashes. Do not silently weaken the existing exact FD ABI.
3. Refreeze every affected absolute path-bearing argv/bootstrap field or define an exact procfd-root derivation so the final consumer cannot re-resolve a replaceable global CLEAN pathname after owner authority is dropped.
4. Add CPU/static temporary-only causal witnesses around the **actual exec/bootstrap seam**: after the last pre-exec pathname check, replace the absolute CLEAN entry before the consumer root/module lookup. The consumer must either remain anchored to the originally held owner inode or fail closed before foreign module/code consumption. A witness that stops at pre-exec revalidation is insufficient.
5. Preserve all existing route/config/raw-input/backing FD and post-mutation cleanup rules; this design Gate still authorizes no production/main execution or real project-path mutation.

## Blocker summary

- current blockers: `2 HIGH`
- child/runtime blockers: `0`
- prior private-parent/frozen-path mismatch: `CLOSED`
- owner-relative backing handoff: materially improved but final exec/bootstrap continuity remains blocking

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_owner_identity_execution_design_v0.1.md:27)`

This verdict binds only exact pair `64b706b7b97451fd90cb6e9292100e512952f28a / 93a89ba61306d840a008813f62f26a34d54850f4`.

No CPU/static implementation is authorized from this pair. No real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
