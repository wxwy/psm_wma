# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity CPU/static Exec-Failure Witness

**Date:** 2026-09-14  
**Formal root:** `b3595395427114f73ff53a19a0c2b9180e39905f`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective witness-only remediation request binds exact pair `b3595395427114f73ff53a19a0c2b9180e39905f` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `b359539...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- The formal root commit changes only `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8_witness_test.py`; production payload bytes are unchanged from the previously reviewed lifecycle-remediated implementation.
- Frozen design authority remains causal-worktree identity v0.5 (`019643a...` / same child): exact leaf add `/proc/self/fd/6/.`, fixed owner FD7/FD9, per-child transient FD6, no direct FD9 inheritance, pre-exec retention of owner capabilities, and non-destructive `ROLLBACK_INCOMPLETE` cleanup.
- No real worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Prior HIGH disposition

Prior exact-pair review `71c4a252... / 93a89ba...` found production implementation blockers closed but retained one HIGH Evidence gap: the direct witness stopped at `prepare_exec_fds()` and helper-level cleanup; it did not exercise the exact control-flow seam `successful backing handoff -> execve failure -> retained-owner cleanup`.

**Disposition: CLOSED.**

The witness-only delta now directly covers that seam:

1. It creates and retains the frozen parent/clean owner capabilities.
2. It performs real temporary `handoff()` calls for all three backing targets FD3/FD4/FD5.
3. It runs `prepare_exec_fds()`, so the pre-exec descriptor set follows the production preparation path while preserving FD7/FD9 as non-inheritable owners.
4. It invokes `os.execve()` on a deliberately nonexistent executable and requires `FileNotFoundError`; this exercises the actual failed-exec behavior where CLOEXEC descriptors remain open because exec never succeeds.
5. It then enters the non-destructive `cleanup()` path. `cleanup()` itself calls `assert_owned_identity(owned)`, so a successful `ROLLBACK_INCOMPLETE` observation proves retained FD7/FD9 identity remained usable after the failed exec attempt.
6. The witness additionally verifies FD7/FD9 remain non-inheritable after the seam.

This is direct evidence for the exact previously blocking control flow rather than a helper-level proxy.

## 3. Production implementation status

No production payload change is present in this formal root. The already-reviewed production implementation remains acceptable:

- parent owner fixed at FD7 and clean owner fixed at FD9;
- every Git child independently derives transient FD6 from FD9, uses exact `close_fds=True`, `pass_fds=(6,)`, then closes FD6 before the next consumer;
- add target remains exact `/proc/self/fd/6/.`;
- `prepare_exec_fds()` preserves `{3,4,5,7,9}` in the pre-exec parent and verifies FD7/FD9 are non-inheritable;
- post-add failure cleanup remains non-destructive and does not invoke `git worktree remove`, global-path deletion, `unlink`, `rmtree`, or `rename`;
- foreign-B safety and retained-owner identity checks remain intact.

## 4. Evidence disposition

The reported direct suite (`16 tests OK`), `py_compile`, and `git diff --check` are consistent with the narrow witness-only change. The newly added handoff+failed-exec witness is the missing direct evidence needed to close the previous HIGH.

No new Design, Production, Evidence, child, or runtime blocker was found for this exact pair and Gate.

## 5. Formal verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_WORKTREE_IDENTITY_CPU_STATIC`

Current blockers: **0**.  
Production implementation blockers: **0**.  
Evidence blockers: **0**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This approval binds only exact formal pair `b3595395427114f73ff53a19a0c2b9180e39905f` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`.

It closes only the reviewed root temporary CPU/static implementation/witness Gate. It does **not** authorize real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, checkpoint write, or any real materialization request.
