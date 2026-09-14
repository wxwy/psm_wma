# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity CPU/static Lifecycle Remediation

**Date:** 2026-09-14  
**Formal root:** `71c4a2524e350509f8048bfb65ea1cc8180a1c57`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective remediation request binds exact pair `71c4a2524e350509f8048bfb65ea1cc8180a1c57` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `71c4a25...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to prior reviewed pair `85a39d6243bb4bcc3e260ba3eb4279c52508d79f` / same child, the production delta is limited to the approved payload plus its direct temporary witness; `SESSION.md`, `TODO.md`, coordination/review files are bookkeeping.
- Frozen authority remains causal-worktree identity v0.5 plus the prior same-Gate exact acceptance: fixed FD7/FD9 owners, per-Git-child transient FD6, leaf add `/proc/self/fd/6/.`, non-destructive `ROLLBACK_INCOMPLETE`, and owner FDs retained through the `execve()` attempt.
- No real worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized.

## 2. Prior HIGH disposition

The previous HIGH had two lifecycle components:

1. `assert_worktree()` kept one FD6 lease across both `rev-parse` and `status` Git children.
2. `close_to_keep({3,4,5})` dropped FD7/FD9 before `execve()`, so failed exec could not reach cleanup with retained owner identity.

**Production disposition: CLOSED.**

The remediation now:

- calls `consume_leaf(FD9, ...)` independently for `rev-parse` and for `status`, so each child gets an exact FD6 lease and FD6 is closed before the next consumer;
- replaces the old pre-exec close with `prepare_exec_fds()`, preserving `{3,4,5,7,9}` in the parent while verifying FD7/FD9 are non-inheritable/CLOEXEC;
- therefore successful `execve()` drops FD7/FD9 automatically, while failed `execve()` leaves them available to the existing non-destructive cleanup path.

The new FD6-lifetime witness directly observes FD6 absent before and after each of the two validation consumers, so that portion of the previous evidence gap is also closed.

## 3. Remaining blocking finding

### HIGH-1 Evidence — the new pre-exec witness does not exercise the frozen `successful handoff -> execve failure -> except cleanup` seam

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8_witness_test.py:182`

The prior exact acceptance required a direct temporary witness that **forces `execve()` to fail after successful handoff** and proves FD7/FD9 remain intact for the `main()` failure path's retained-owner cleanup.

The new test `test_payload_preexec_failure_retains_owner_identity_for_cleanup` instead:

- manually occupies backing FDs 3/4/5 with `/dev/null`;
- binds FD7/FD9 owners;
- calls `prepare_exec_fds()`;
- directly calls `assert_owned_identity()` and `cleanup()`.

It never performs the payload's backing `handoff()` sequence and never invokes a deliberately failing `execve()`. Therefore it proves the helper-level pre-exec FD set is compatible with cleanup, but it does not directly witness the exact control-flow seam that was frozen in the previous HIGH acceptance:

```text
successful handoff -> prepare_exec_fds -> os.execve raises -> except -> cleanup -> retained FD7/FD9 identity proof -> ROLLBACK_INCOMPLETE
```

This distinction matters under the project's evidence rules: a nearby/helper-level test cannot substitute for the direct witness required to close a previously blocking production-authority seam. The production code now appears correct; the blocker is the missing exact evidence, not a newly observed implementation defect.

## 4. Exact acceptance

No production redesign is requested. Preserve the current code and add one direct temporary/fork witness that:

1. creates a temporary clean owner under retained FD7/FD9;
2. completes the real `handoff()` path for backing FD3/4/5 using temporary fixture bytes/paths;
3. calls `prepare_exec_fds()` and verifies the parent FD set includes the intended backing plus retained owners, with FD7/FD9 non-inheritable;
4. invokes an `execve()` that is guaranteed to fail (for example a deliberately nonexistent executable) and catches the resulting exception;
5. follows the same failure semantics as `main()`: proves FD7/FD9 identities are unchanged, then calls non-destructive `cleanup()` and observes `ROLLBACK_INCOMPLETE`;
6. proves no global/destructive cleanup was introduced and FD6 is absent outside Git-consumer leases.

The witness must remain entirely inside `TemporaryDirectory`/forked CPU/static fixtures and must not invoke real project materialization or external source/data access.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8_witness_test.py:182)`

Current blockers: **1 HIGH Evidence**.  
Production implementation blockers: **0**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact formal pair `71c4a2524e350509f8048bfb65ea1cc8180a1c57` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`.

Remediation remains limited to the existing root-only direct temporary CPU/static witness surface. No real Git/worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU, training, evaluation, inference, or LIBERO4IN1 action is authorized.
