# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity Design v0.3

**Date:** 2026-09-14  
**Formal root:** `56acad8f39241c8c03fa770aa39468a3e71a2349`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `56acad8f39241c8c03fa770aa39468a3e71a2349` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `56acad8...` resolves `cosmos-framework` exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to prior reviewed `c6ac4639d2abb6bb19263e1ee923902419844fd5` / same child, so fresh incremental review is required.
- Formal implementation authority remains docs-only design `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_causal_worktree_identity_design_v0.3.md`; task/session/review-ledger changes are bookkeeping, not implementation authority.
- No real Git/worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Prior blocker disposition

Prior HIGH from v0.2: `/proc/self/fd/6/<clean_name>` retained the parent inode but still re-resolved the mutable clean leaf entry at Git target-resolution time, so same-parent replacement could redirect Git into foreign inode B.

**Disposition: CLOSED at design level.**

v0.3 changes the consumer boundary from parent capability + leaf lookup to the leaf capability itself:

- launcher creates clean-root A and retains `clean_fd`;
- for the Git child only, `clean_fd` is duplicated to exact `git_target_fd=6`;
- the exact Git target operand is `/proc/self/fd/6`, with no appended `clean_name`;
- child inheritance is frozen to `close_fds=True`, `pass_fds=(6,)`, with FD6 identity/CLOEXEC checks and no parent/global fallback;
- parent owner FD7 and clean owner FD9 remain non-inherited owners outside the Git child.

This removes the fresh clean-entry lookup that caused the prior HIGH. Replacing `parent_fd/clean_name` with foreign B no longer changes the inode referenced by FD6.

## 3. Acceptance review

The v0.3 design satisfies the prior exact acceptance:

1. **Leaf capability is the actual mutation target.** Git receives `/proc/self/fd/6`, where FD6 is a duplicate of the retained `clean_fd`, rather than a global pathname or parent+name path.
2. **Exact descendant lifetime is frozen.** `close_fds=True`, `pass_fds=(6,)`, FD6 identity/CLOEXEC state, collision rules, and close point are explicit; FD3/4/5/7/8/9 are excluded from the Git child.
3. **No fallback is allowed.** If procfs semantics or Git support are unavailable, the route fails closed rather than falling back to v0.2 or global CLEAN.
4. **Pre/post owner proof is retained.** `fstat(6)`, `fstat(clean_fd)`, and parent-entry no-follow checks remain required after Git returns, so namespace drift prevents handoff even though it cannot redirect Git writes.
5. **Administrative metadata is constrained.** Worktree metadata must remain provable via retained owner capability and existing no-follow/raw-byte/route checks; a canonicalized/global/procfd string cannot become a substitute owner authority.
6. **Cleanup is owner-limited.** Any cleanup Git child must re-derive FD6 from retained `clean_fd`; foreign replacement is never read/written/deleted, and unprovable cleanup becomes `ROLLBACK_INCOMPLETE`.
7. **Direct implementation witnesses are frozen.** Required temporary local-Git fixtures cover normal leaf targeting, same-parent leaf replacement before Git resolution, global parent replacement, exact FD inheritance, post-Git drift and cleanup, while retaining the legacy v0.8 negative route.

The key required implementation witness is correctly stated: replace the namespace entry A with foreign B before the Git child resolves its target, then prove actual temporary `git worktree add` either populates retained A through `/proc/self/fd/6` or fails before writing B. If the platform/Git cannot satisfy that, implementation must fail closed.

## 4. Non-blocking implementation cautions

- Approval is for the design only; the future CPU/static implementation still has to prove the actual installed Git accepts the pre-created directory through `/proc/self/fd/6` and that worktree administrative metadata remains usable under the frozen capability contract.
- An implementation that reintroduces `clean_name`, global CLEAN, `realpath`-derived ownership, extra inherited FDs, or a fallback target would be outside this approval and require rejection.
- The cleanup re-dup path must preserve the same FD6-only consumer contract rather than relying on a stale procfd string after FD6 has closed.

These are acceptance checks for the next implementation Gate, not blockers in the current docs-only design.

## 5. Formal verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC`

Current blockers: **0**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This approval binds only exact formal pair `56acad8f39241c8c03fa770aa39468a3e71a2349` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.

It authorizes only the next root-only temporary-fixture CPU/static implementation/tests within the already frozen authority-root launcher/payload allowlist. It does **not** authorize real worktree/materialization, real source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, or any real materialization request.