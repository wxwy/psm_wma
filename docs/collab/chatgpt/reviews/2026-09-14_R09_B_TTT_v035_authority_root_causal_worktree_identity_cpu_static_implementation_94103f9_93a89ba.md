# ChatGPT Independent Review — R09-B TTT v0.3.5 Authority-root Causal Worktree Identity CPU/static Implementation

**Date:** 2026-09-14  
**Formal root:** `94103f9e3b464541a027594f7858b87dc0110538`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective implementation request binds exact pair `94103f9e3b464541a027594f7858b87dc0110538` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `94103f9...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal implementation scope is limited to `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py`, its direct stdlib witness, and task/session bookkeeping. Child is unchanged.
- Frozen design authority is approved causal-worktree identity v0.5, exact pair `019643a9b17ebdda8f74b5c5fac90cb37c23f18f` / same child. It preserves the v0.4 leaf add contract and explicitly retains the fixed owner/consumer capability model: parent owner FD7, clean owner FD9, Git consumer FD6 only, no global fallback, plus non-destructive `ROLLBACK_INCOMPLETE` after any post-add failure.
- No real worktree/materialization/source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Positive implementation observations

- `git worktree add --detach` now uses exact leaf target `/proc/self/fd/6/.` with `close_fds=True` and `pass_fds=(6,)`.
- Directory continuity uses `(st_dev, st_ino, S_IFMT)` instead of `st_size`, so legitimate Git population does not invalidate the owner identity.
- Post-add cleanup is non-destructive: `cleanup()` only revalidates owner identity and returns `ROLLBACK_INCOMPLETE`; it does not run `worktree remove`, `unlink`, `rmtree`, or `rename`.
- Direct witnesses cover owner residue, foreign-B preservation, post-add replacement rejection, the leaf-remove behavior as diagnostic-only, and reported `13 tests OK` plus `py_compile` / `git diff --check`.

These correctly implement the central v0.5 add/cleanup semantics.

## 3. Blocking finding

### HIGH-1 — fixed FD7/FD9 owner ABI is not implemented; owner capabilities use arbitrary low FDs and can collide with backing / Git-consumer FDs

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py:104` (`add_and_capture`)

The approved design does not merely require a retained parent and clean FD; it freezes the capability mapping and inheritance boundary: parent owner FD7, clean owner FD9, with FD6 reserved as the transient Git child target and backing ABI `{3,4,5}` kept collision-free.

Current implementation instead does:

```python
parent = os.open(ROOT, ...)
...
clean = os.open(name, ..., dir_fd=parent)
...
os.dup2(clean, 6)
...
return (value, clean, parent, name, parent_value)
```

`parent` and `clean` therefore remain whatever descriptors the kernel happens to allocate. There is no fixed bind to FD7 / FD9 and no proof that the frozen owner descriptors are collision-free.

This is not a cosmetic ABI mismatch. With the live launcher state, route snapshot descriptors can already occupy low FDs. `parent` / `clean` can therefore land on backing targets 3/4/5 or on FD6 itself. The implementation then has several authority consequences:

1. **FD6 is not guaranteed to be child-only.** If `clean` itself is allocated as FD6, the post-child restore leaves the retained owner on FD6 rather than keeping FD6 transient.
2. **Backing handoff can close an owner capability.** Later `handoff(..., target=3/4/5, ...)` uses `dup2`; if `parent` or `clean` happened to occupy one of those targets, the owner capability is overwritten before the launcher has completed all failure/cleanup-sensitive stages.
3. **Post-add Git validation can inherit the owner FD directly.** `assert_worktree()` builds `/proc/self/fd/<fd>` from the arbitrary retained clean descriptor and passes that descriptor through `pass_fds=(fd,)`. Under the frozen design, retained FD9 is an owner capability and must not itself become the descendant consumer ABI; Git consumers must receive the explicitly derived transient FD6 contract.
4. **The direct witnesses do not prove the frozen mapping.** They exercise functional add/cleanup behavior but do not assert parent==7, clean==9, FD6 child-only lifetime, or immunity to low-FD occupancy/collision.

Thus the implementation can pass all 13 fixtures while violating the exact authority separation that the design froze to prevent descriptor aliasing and inheritance ambiguity.

## 4. Exact acceptance

The remediation must preserve the already-correct leaf add and non-destructive cleanup behavior, while implementing the fixed capability ABI exactly:

- Before the mutating Git seam, bind the retained parent capability to exact FD7 and retained clean capability to exact FD9, using temporary-open → `dup2`/rebind → `fstat` identity proof → source close semantics, with explicit collision checks against backing `{3,4,5}`, Git target FD6, bootstrap FD8, and owner FDs `{7,9}`.
- FD6 must be derived from FD9 only for each Git child consumer, with exact `close_fds=True`, `pass_fds=(6,)`, identity/CLOEXEC proof, and must cease to be the consumer descriptor after the child returns. Retained FD9 must not be inherited directly by Git.
- All post-add Git validation that consumes the clean worktree must re-derive the transient FD6 consumer from FD9 rather than passing arbitrary owner FD values.
- Handoff to FD3/4/5 must not overwrite FD7 or FD9; failure after any handoff stage must still have intact retained owner capabilities available for v0.5 non-destructive identity proof / `ROLLBACK_INCOMPLETE`.
- Add direct temporary witnesses that deliberately perturb low-FD availability and prove the mapping remains exactly parent=7, clean=9, Git child inheritance exactly `(6,)`, no FD3/4/5/7/8/9 leakage beyond the frozen ABI, FD6 is not retained as owner after child return, and cleanup/failure retains FD7/FD9 identity.

No global-path cleanup or destructive rollback may be reintroduced.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.8.py:104)`

Current blockers: **1 HIGH Production/Authority+Evidence**.  
Child/runtime blockers: **0**.

## 6. Scope reminder

This verdict binds only exact formal pair `94103f9e3b464541a027594f7858b87dc0110538` / `93a89ba61306d840a008813f62f26a34d54850f4` and Gate `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-WORKTREE-IDENTITY-CPU-STATIC-IMPLEMENTATION`.

Remediation remains limited to the already-approved root-only launcher/payload and direct temporary-fixture CPU/static witness surface. No real worktree/materialization, source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime/config change, GPU, training, evaluation, inference, or LIBERO4IN1 action is authorized.