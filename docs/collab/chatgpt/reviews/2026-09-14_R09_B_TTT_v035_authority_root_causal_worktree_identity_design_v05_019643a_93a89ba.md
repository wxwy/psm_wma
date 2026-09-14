# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity Design v0.5

**Date:** 2026-09-14  
**Formal root:** `019643a9b17ebdda8f74b5c5fac90cb37c23f18f`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `019643a9b17ebdda8f74b5c5fac90cb37c23f18f` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `019643a...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to prior reviewed `bfa10d345f2003a3a123f69dc836462fe05959d9` / same child, so a fresh incremental review is required.
- Formal authority change is docs-only v0.5 design plus task/session bookkeeping. No project implementation or child change is in formal scope.
- No real Git/worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Prior blocker disposition

Prior HIGH from v0.4: cleanup reintroduced mutable global `<clean>` as a destructive `git worktree remove --force <clean>` target. A same-parent replacement A→foreign B after the last owner check but before Git pathname resolution could therefore expose B to destructive cleanup, while post-remove checks could only detect the race after possible mutation.

**Disposition: CLOSED at design level.**

v0.5 removes that destructive consumer entirely from this Gate:

- the already-accepted add seam remains leaf-capability-derived as `/proc/self/fd/6/.`, with exact FD6 inheritance and no global fallback;
- once native `worktree add` has been invoked, any later failure path is explicitly forbidden from calling `git worktree remove`, `rmtree`, `unlink`, `rename`, or any other namespace-mutating cleanup;
- cleanup may only revalidate retained FD7/FD9/parent-entry identity, close its own descriptors, preserve A / Git administrative metadata / foreign B if present, and terminate as `ROLLBACK_INCOMPLETE`;
- residue cleanup is deferred to a separate future recovery-design Gate rather than silently weakening authority to regain a clean filesystem.

This directly satisfies the prior exact acceptance branch: if native Git cannot safely remove through a retained leaf capability, fail closed as `ROLLBACK_INCOMPLETE` and preserve residue rather than fall back to mutable global `<clean>`.

## 3. Acceptance review

The v0.5 design is internally consistent with the frozen authority model:

1. **Add authority remains unchanged and acceptable.** The only add target is exact `/proc/self/fd/6/.`, derived from retained `clean_fd`, with exact `close_fds=True`, `pass_fds=(6,)`, FD identity/CLOEXEC checks, and no appended `clean_name` or global-path fallback.
2. **No destructive cleanup authority exists in this Gate.** After `worktree add` has been called, every fail path is non-destructive. This removes the cleanup pathname-resolution race rather than merely detecting it after mutation.
3. **Foreign replacement is preserved.** If same-parent A is replaced by foreign B after the last owner proof, cleanup never launches a Git consumer and performs no namespace mutation. B therefore cannot be read/written/deleted by this cleanup path.
4. **Rollback status is conservative.** Even if A is still fully provable, the design does not report successful cleanup; it returns `ROLLBACK_INCOMPLETE` because worktree/admin residue remains. This avoids treating retained residue as successful rollback.
5. **Unsupported native leaf remove does not trigger fallback.** The isolated temporary-Git probe showing `git worktree remove --force /proc/self/fd/6/.` rejection is used only to select the fail-closed contract. The design explicitly forbids falling back to `<clean>`, canonical registration path, cwd, parent+name, or any procfd/global delete target.
6. **Recovery is explicitly separated.** Any future mechanism that deletes retained worktree residue requires a distinct recovery-design Gate with its own native fixture proof and exact authority contract.
7. **Required witnesses cover the prior blocker directly.** The future CPU/static implementation must prove unsupported leaf-native-remove handling, same-parent cleanup-resolution race with B marker preservation, normal post-add failure leaving A+metadata intact with `ROLLBACK_INCOMPLETE`, and descriptor/capability hygiene with no remove child spawned.

## 4. Non-blocking implementation cautions

- The next implementation Gate must preserve the semantic distinction between `FAIL` before any Git mutation and `ROLLBACK_INCOMPLETE` after `worktree add` has been invoked or may have mutated state.
- No implementation convenience path may reintroduce `git worktree remove --force <clean>`, global CLEAN, canonical registration path, parent+name, stale procfd strings, `rmtree`, `unlink`, or `rename` after post-add failure.
- Tests must assert that residue preservation is expected fail-closed behavior, not successful cleanup.
- Any later recovery implementation is out of scope and requires a new reviewed design/formal pair.

These are checks for the next implementation Gate, not blockers in the current docs-only design.

## 5. Formal verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC`

Current blockers: **0**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This approval binds only exact formal pair `019643a9b17ebdda8f74b5c5fac90cb37c23f18f` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-DESIGN`.

It authorizes only the next root-only temporary-fixture CPU/static implementation/tests within the already frozen authority-root launcher/payload allowlist. It does **not** authorize real worktree/materialization, real source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, or any real materialization request.