# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity CPU/static Remediation

**Date:** 2026-09-14  
**Formal root:** `85a39d6243bb4bcc3e260ba3eb4279c52508d79f`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective remediation request binds exact pair `85a39d6243bb4bcc3e260ba3eb4279c52508d79f` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `85a39d6...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to prior reviewed implementation pair `94103f9e3b464541a027594f7858b87dc0110538` / same child, the production delta is limited to the approved root payload and its direct temporary witness; `SESSION.md` / `TODO.md` / coordination files are bookkeeping.
- Frozen design authority remains causal-worktree identity v0.5 (`019643a...` / same child): leaf add target `/proc/self/fd/6/.`, fixed parent owner FD7, fixed clean owner FD9, FD6 as a one-child consumer only, no direct FD9 inheritance, and non-destructive `ROLLBACK_INCOMPLETE` cleanup after any post-add failure.
- No real worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Prior HIGH disposition

The prior HIGH at `...v0.8.py:104` required exact owner ABI binding and collision-safe descendant inheritance.

**Disposition: substantially closed, but not fully closed.**

The remediation correctly adds:

- frozen descriptors `BACKING_FDS={3,4,5}`, `GIT_TARGET_FD=6`, `PARENT_OWNER_FD=7`, `BOOTSTRAP_FD=8`, `CLEAN_OWNER_FD=9`;
- `bind_owner()` using `F_DUPFD_CLOEXEC >=10`, source close, fixed `dup2`, directory identity proof, and non-inheritable owner FD;
- retained parent exactly FD7 and retained clean owner exactly FD9;
- `consume_leaf()` deriving transient FD6 from retained FD9 and closing FD6 afterwards;
- add target exactly `/proc/self/fd/6/.`, with `close_fds=True`, `pass_fds=(6,)`;
- handoff restricted to backing FD3/4/5, preventing direct overwrite of FD7/FD9;
- a low-FD occupancy witness proving owner mapping remains 7/9 and that a standalone `consume_leaf()` lease closes FD6 afterwards;
- non-destructive cleanup and foreign-B preservation remain intact.

These changes close the arbitrary-owner-FD / backing-collision portion of the previous HIGH.

## 3. Remaining blocking finding

### HIGH-1 — the frozen capability lifecycle is still not exact: FD6 spans two Git children in post-add validation, and FD7/FD9 are dropped before a potentially failing `execve`

**Primary location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py:176` (`assert_worktree`)

The remediation defines `consume_leaf()` as the FD9→FD6 one-child capability, but `assert_worktree()` wraps two distinct Git subprocesses in one `consume_leaf()` lease:

```python
def validate(target):
    run(... "rev-parse" ..., pass_fds=(6,))
    run(... "status" ..., pass_fds=(6,))
consume_leaf(fd, validate)
```

FD6 therefore remains open in the parent after the first Git child returns and is reused for the second child. This violates the frozen `FD6 only-child inheritance` contract and the prior exact acceptance that **each Git consumer** must re-derive FD6 from FD9 and close it immediately after that child returns. The new low-FD witness proves a single `consume_leaf()` call closes FD6 after the whole callback, but it does not prove closure between the two real post-add Git consumers.

There is a second lifecycle consequence at the success boundary. `main()` calls:

```python
close_to_keep({3,4,5})
os.execve(...)
```

so FD7/FD9 are explicitly closed in the parent before `execve()` is attempted. They are already `CLOEXEC`; they can remain open in the pre-exec process and be closed automatically on successful exec. Closing them manually first means an `execve()` failure reaches `cleanup()` with the retained owner capabilities already gone. The result still classifies as `ROLLBACK_INCOMPLETE`, but it can no longer perform the v0.5 retained-FD owner revalidation that the design freezes for every post-add failure path.

This is one authority-lifecycle blocker: the fixed descriptor numbers now exist, but their lifetime is still broader than frozen for FD6 and shorter than frozen for FD7/FD9.

## 4. Evidence gap

The reported `14 tests OK`, `py_compile`, and `git diff --check` are useful supporting evidence, but the direct witness matrix does not cover the remaining lifecycle seams:

- no witness proves FD6 is closed **between** the `rev-parse` and `status` Git children in `assert_worktree()`;
- no witness forces `execve()` to fail after handoff and proves FD7/FD9 are still intact for non-destructive cleanup identity proof;
- the low-FD occupancy test only inspects one callback-held `consume_leaf()` lease, so it cannot close either gap.

## 5. Exact acceptance

Preserve all newly-correct fixed ABI behavior and the approved non-destructive cleanup, then close the lifecycle seam exactly:

1. **Per-child FD6 lease:** each Git subprocess, including each post-add validation command, must independently execute `FD9 -> transient FD6 -> subprocess(close_fds=True, pass_fds=(6,)) -> close FD6`. `assert_worktree()` must not keep FD6 open across two Git children.
2. **Retain owner FDs until exec outcome is known:** keep FD7/FD9 open and non-inheritable/CLOEXEC through the `execve()` attempt. On successful exec they disappear automatically; if `execve()` raises, they must remain available to `cleanup()` for retained-FD identity proof before `ROLLBACK_INCOMPLETE`.
3. **Final pre-exec FD set:** close all unwanted descriptors while preserving backing `{3,4,5}` plus owner `{7,9}` in the parent immediately before exec; verify FD7/FD9 are non-inheritable so the successful child still receives only the frozen inherited ABI.
4. **Direct witnesses:** add temporary CPU/static tests that (a) instrument the two post-add Git consumers and prove FD6 is absent in the parent between them and after each return, and (b) force `execve()` failure after successful handoff and prove FD7/FD9 identities are still intact when cleanup classifies `ROLLBACK_INCOMPLETE`.
5. Do not reintroduce direct FD9 inheritance, global-path cleanup, `worktree remove`, unlink/rmtree/rename rollback, or any real-I/O/GPU path.

## 6. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py:176)`

Current blockers: **1 HIGH Production/Authority+Evidence**.  
Child/runtime blockers: **0**.

## 7. Scope reminder

This verdict binds only exact formal pair `85a39d6243bb4bcc3e260ba3eb4279c52508d79f` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`.

Remediation remains limited to the approved root-only launcher/payload and direct temporary-fixture CPU/static witness surface. No real worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config changes, GPU, training, evaluation, inference, or LIBERO4IN1 action is authorized.
