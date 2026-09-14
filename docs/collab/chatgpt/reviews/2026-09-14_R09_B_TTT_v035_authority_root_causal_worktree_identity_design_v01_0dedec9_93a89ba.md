# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity Design v0.1

**Date:** 2026-09-14  
**Formal root:** `0dedec97f1d5e2c62ec980b6daffb7f9da472cda`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `0dedec97f1d5e2c62ec980b6daffb7f9da472cda` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `0dedec9...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal scope is docs-only design `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.1.md` plus task-record bookkeeping. No real Git/worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
- This Gate exists specifically because the earlier v0.8 route could not prove causal ownership when native Git itself created the clean root. The proposed design attempts to repair that by precreating the clean root and retaining directory capabilities.

## 2. Positive design observations

- The design correctly freezes a retained parent directory capability before mutation and creates the clean root with `mkdirat(parent_fd, clean_name, 0700)`.
- It immediately opens the created clean root with `openat(..., O_DIRECTORY|O_NOFOLLOW)`, freezes `(st_dev, st_ino, type)`, and requires post-Git parent-entry / clean-FD identity agreement.
- It explicitly rejects fallback/retry/path switching and classifies owner/absence cleanup failures as `ROLLBACK_INCOMPLETE`.
- The proposed implementation acceptance includes parent/clean replacement, symlink, nonempty, metadata-drift, cleanup-ownership and legacy-route negative witnesses.
- These are all materially stronger than the v0.8 post-add pathname bind that motivated this Gate.

## 3. Blocking finding

### HIGH-1 — Git mutation target is still a mutable global pathname, so the design does not causally bind Git's writes to the retained clean-root inode

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.1.md:22` (section 2, step 3)

**Root cause**

The launcher creates and retains `clean_fd`, but the actual native Git operation is still specified as:

```text
git worktree add --detach <absolute-clean-root> <formal-parent>
```

That target operand is resolved by Git through the mutable global namespace. The retained `parent_fd` / `clean_fd` are not the authority Git consumes when selecting the directory it will mutate.

There is therefore a pre-consumption race:

1. launcher creates clean-root inode A and retains `clean_fd(A)`;
2. before Git resolves `<absolute-clean-root>`, the global parent/clean entry is renamed/replaced so the absolute path now names foreign empty directory B;
3. `git worktree add` resolves the absolute pathname to B and may populate B / register worktree metadata against B;
4. only after Git returns does step 4 compare the retained parent entry and `clean_fd(A)` and detect drift.

The post-Git identity check can detect that the intended owner path was replaced, but it cannot retroactively prove that Git did not mutate B. That contradicts the design's stated goal that Git "only" fills the already-bound launcher-owned directory. It is the same causal-authority class as the earlier post-add bind problem, moved from ownership observation after Git to target selection before Git.

**Why fail-close after Git is insufficient**

A fail-closed verdict after Git returns protects later adapter stages, but the native Git mutation has already happened. The foreign replacement may contain files or worktree metadata written by this launcher even though the launcher never owned that inode. The cleanup rule correctly says foreign replacements must never be deleted, which means the design can terminate with an externally replaced directory modified by Git and intentionally left in place. That is not causal owner continuity.

The already-approved causal-owner design chain uses a capability-derived descendant contract for consumers and explicitly rejects reopening global CLEAN as the operational authority. The same principle is required here at the first mutating Git boundary: the capability must govern the target consumed by Git, not merely the postcondition check.

**Violated design objective / authority contract**

- The Gate is specifically intended to recover causal worktree ownership before actual materialization can be requested.
- Section 1 states that precreating and retaining descriptor identity should make Git only fill the bound empty directory.
- Section 2 says pathname checks supplement capabilities and must not replace them; however step 3 still uses a pathname as Git's mutation authority.
- Cleanup acceptance requires foreign replacement never be deleted; therefore post-hoc rejection cannot safely erase a mutation that Git may already have applied to a foreign target.

**Exact acceptance**

The replacement design must bind the actual Git worktree target to a retained capability across Git's target resolution and mutation boundary.

An acceptable design should freeze one exact mechanism such as:

- a dedicated inherited Git-target FD whose procfd-derived path (for example `/proc/self/fd/<git_parent_fd>/<clean_name>` or another proven capability-derived target) is the exact target operand consumed by Git; or
- an equivalent primitive whose semantics prove Git cannot resolve a replaced global parent/clean entry as its target.

The design must also freeze the descendant lifetime/inheritance contract for that Git target capability (`close_fds`, exact `pass_fds`, CLOEXEC state, pre/post `fstat` identity barrier, and no fallback to the global absolute CLEAN target). If procfs/capability-target semantics are unavailable or Git rejects the capability-derived target, the route must fail closed; it may not silently revert to the mutable absolute pathname.

Future CPU/static implementation acceptance must include a direct temporary local-Git witness at the exact seam:

1. precreate the owner clean directory and retain its capability;
2. before the Git child resolves its target, rename/replace the global parent or clean entry with a foreign empty directory;
3. invoke the actual temporary `git worktree add` through the frozen capability-derived target mechanism;
4. prove Git either populates only the retained owner inode or fails before mutating the foreign replacement;
5. prove the foreign replacement is neither read as owner nor written/deleted by cleanup;
6. revalidate both retained owner identity and the frozen request pathname before handing off to any later stage.

The design should also explicitly freeze how Git's administrative worktree metadata is validated when the target operand is capability-derived, so later Git operations do not depend on an ephemeral procfd pathname after the capability lifetime ends.

## 4. Non-blocking / retained constraints

- Precreation itself is not rejected; the blocker is that Git still receives a mutable global pathname rather than the retained owner capability.
- Whether the installed Git accepts an already-existing empty directory can remain an implementation witness, provided rejection fails closed without fallback.
- The current cleanup ownership principle is directionally correct: only identity-proven owner entries may be removed; foreign replacement must remain untouched.
- The original v0.8 negative-route witness should remain, as requested.
- Child/Gitlink blockers: **0**.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.1.md:22)`

Current blockers: **1 HIGH Design/Authority**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact formal pair `0dedec97f1d5e2c62ec980b6daffb7f9da472cda` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.

Only a docs-only redesign is authorized by this verdict. No real Git/worktree/materialization, source/checkpoint/manifest/data/cache access, collection/receipt/publication, child/runtime/config modification, GPU, training, evaluation, inference or LIBERO4IN1 action is authorized.
