# ChatGPT Review — Authority-root Launcher Payload v0.6

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `80132197c29bd139e3e05ce6deb3cbcf8f525de6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior reviewed `8d1c10015a632c3c48eb46ad26b3180658cee0a1 / 93a89ba61306d840a008813f62f26a34d54850f4` pair. The effective remediation is root docs/tooling only: v0.6 launcher payload + annex/request + status bookkeeping; child/runtime is unchanged.

## Prior blocker disposition

- prior HIGH-1 (v0.2/v0.3 source documents looked up in a tree that does not contain them): **CLOSED**. v0.6 embeds the frozen selection/config/actual-argv bytes and no longer requires those historical annex paths to exist under candidate parent `9dd2fb8...`.
- prior HIGH-2 (FD handoff / exact backing-object identity): **NOT CLOSED**. Same-FD handling is fixed, but the exact backing pathname identity/mode contract is still incomplete.
- prior HIGH-3 (worktree postcondition and launcher-owned cleanup): **NOT CLOSED**. Post-add checks/cleanup exist, but the first possibly-mutating `worktree add` can still escape before ownership is captured.
- prior HIGH-4 (parent Git routing/common-dir authority): **NOT CLOSED**. `.git` and `.git/config` are retained no-follow, but `commondir` is neither rejected nor bound.

## Blockers

### HIGH-1 — partial/nonzero `worktree add` can still escape as ordinary failure without cleanup or `ROLLBACK_INCOMPLETE`

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.6.py:131-143` (`main`).

`owned` is assigned only after `run(s, "worktree", "add", ...)` fully returns. But `run()` itself performs the native Git command, the post-command `check_route()`, and the return-code rejection. Therefore either of these cases can occur after Git has mutated worktree/admin state but before `owned` exists:

1. native Git partially creates the worktree/admin entry and returns nonzero;
2. native Git succeeds, then the immediate post-command route revalidation detects drift and raises.

The outer exception handler only calls `cleanup(...)` when `'owned' in locals()`. In both cases above it skips cleanup and re-raises the ordinary `Stop` from `run()`. That directly contradicts annex v0.6 §2 item 3 and the prior HIGH-3 acceptance, which require every first-mutation failure path to either prove verified rollback or terminate explicitly as `ROLLBACK_INCOMPLETE`.

The submitted `py_compile` and handoff-only temporary checks do not close this causal path.

**Exact acceptance:**
1. Treat the first `worktree add` call itself as the mutation boundary; after any return/exception/post-route failure, inspect/bind the candidate clean-root/admin ownership state before deciding ordinary FAIL.
2. If launcher-owned state can be proved, run the frozen cleanup and prove clean-root/backing/index/evidence/worktree-list absence.
3. If ownership or rollback cannot be proved, return only explicit `ROLLBACK_INCOMPLETE`; never ordinary `native git`/`route drift` with possible residual mutation.
4. Add direct temporary-repo witnesses for nonzero/partial add and successful-add + post-route-drift.

### HIGH-2 — parent `.git/commondir` authority remains unbound

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.6.py:48-74` (`route_snapshot`, `check_route`).

The launcher accepts an ordinary non-symlink `.git` directory, retains that directory FD and `.git/config`, and rejects `.git/config.worktree`. It never checks whether `.git/commondir` exists, never retains/rejects it, and `check_route()` never revalidates its absence/identity.

Git can honor a `commondir` file even when the top-level `.git` is a directory, redirecting common repository authority away from the `.git/config` path the launcher actually bound. Thus the annex statement that accepting only an ordinary `.git` directory means the launcher "cannot unbound enter common-dir authority" is not established by the code.

This is the same authority class explicitly required by prior HIGH-4 acceptance: bind `.git`/git-dir/common-dir/common config or fail closed on `commondir`.

**Exact acceptance:**
1. For the ordinary parent route, no-follow check and freeze `commondir` absence before the first Git command, or resolve/bind its exact file + resolved common-dir directory + common config using retained FDs and raw/identity checks.
2. Revalidate the chosen `commondir` policy immediately before/after every native Git command, including cleanup.
3. Add causal temporary witnesses for `commondir` insertion/replacement before the first command and between pre/post command checks.

### HIGH-3 — backing pathname/mode identity is not retained through the FD handoff

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.6.py:107-122` (`handoff`).

v0.6 correctly fixes the `rd == target` close bug and compares writer/reader/target `fstat` identity plus raw SHA. However it never re-checks the backing pathname identity after the reader is opened or after `dup2`, and it never proves the resulting backing file mode is exactly frozen `0600`.

A pathname replacement after reader-open can therefore leave target FD 3/4/5 pointing to the original exact inode while the canonical backing pathname now names a different object; the current target checks still pass. This is precisely the same-bytes/path-replacement class that prior HIGH-2 required to fail closed. The fixed `0o600` create argument is also not a proof of final mode under all process umasks.

**Exact acceptance:**
1. Retain/revalidate writer-path-reader-target identity through the final handoff: no-follow pathname `lstat/open` identity must still equal the frozen writer/reader/target object after `dup2` and before exec.
2. Verify the final backing object is regular, non-symlink, and `stat.S_IMODE(...) == 0o600`.
3. Add direct same-bytes pathname-replacement and mode-drift witnesses in addition to same-FD/different-FD success cases.

### HIGH-4 — required causal Evidence is incomplete even apart from the production blockers

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.6.md:31-36` (static acceptance) and current formal-pair request evidence.

The annex explicitly requires temporary-only causal witnesses for: same/different FD handoff, extra inherited FD closure, route/config replacement, post-add drift, foreign clean-root replacement, cleanup failure, and successful cleanup.

For the exact `80132197... / 93a89ba...` pair, the live request reports `py_compile`, embedded-byte checks, raw payload digest, `git diff --check`, and only temporary same/different-FD handoff. No direct witness is supplied for the remaining required authority/rollback cases. Test counts or prose claims cannot substitute for those causal witnesses.

This blocker is **Evidence-only**; child/runtime production remains unchanged. It would remain a closure blocker even after the three launcher semantics above are corrected.

**Exact acceptance:** provide direct temporary-only witnesses, bound to the replacement exact formal pair, for every annex v0.6 required case. Each witness must exercise the exact payload path or the smallest faithful extracted production seam and must fail if the corresponding ordering/authority rule regresses.

## Blocker summary

- current blockers: `4 HIGH`
- child/runtime production blockers: `0`
- launcher/execution-request production blockers: `3 HIGH`
- Evidence-only blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.6.py:131)`

This verdict binds only exact pair `80132197c29bd139e3e05ce6deb3cbcf8f525de6 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization is authorized. No source/checkpoint I/O, JSON/worktree/index/candidate/ref/evidence creation, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized by this review.
