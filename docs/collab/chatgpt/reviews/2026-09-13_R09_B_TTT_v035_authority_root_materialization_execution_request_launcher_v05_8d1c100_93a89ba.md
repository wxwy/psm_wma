# ChatGPT Review — Authority-root Launcher Payload v0.5

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `8d1c10015a632c3c48eb46ad26b3180658cee0a1`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior reviewed `11950c953d7c3e781f821ab648d45af83e60d340 / 93a89ba61306d840a008813f62f26a34d54850f4` pair. The effective remediation adds the immutable launcher payload artifact plus annex/request v0.5 and normal status/review bookkeeping; child/runtime is unchanged.

## Prior blocker disposition

The prior v0.4 gaps are materially narrowed:

- prior HIGH-1 (launcher payload bytes absent): **CLOSED as a representation gap** — v0.5 now provides a formal-tree launcher artifact and freezes its length/SHA identity;
- prior HIGH-2 (ambiguous final `execve.argv`): **CLOSED** — the payload now constructs the full `[python,-I,-S,-B,-c,bootstrap,"--",*actual]` argv;
- prior HIGH-3 (pre-first-Git routing authority): **NOT CLOSED** — the new implementation is still weaker than the already-approved no-follow retained-FD routing authority and additionally has post-mutation cleanup gaps.

The new exact payload must itself satisfy the inherited v0.4 launcher procedure. It currently does not.

## Blockers

### HIGH-1 — frozen v0.2/v0.3 source documents are looked up in a tree that does not contain them

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.5.py:120` (`frozen_blob`), consumed at `main()` lines 163–164.

`FORMAL` is fixed to `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`. `frozen_blob()` first requires `git ls-tree FORMAL -- <path>` to return the v0.2/v0.3 annex path before it will `cat-file` the frozen blob OID.

Independent tree inspection of `9dd2fb8...` shows neither `...execution_snapshot_annex_v0.2.md` nor `...v0.3.md` exists in that tree. The frozen blobs (`6510d6...` and `332beb...`) do exist in the repository, but they were introduced outside that formal-parent tree. Therefore `inputs = frozen_blob(...)` / `argv_doc = frozen_blob(...)` deterministically fail with `formal blob identity` before worktree creation.

The submitted `py_compile`/extractor evidence does not close this because it does not execute the exact payload source-resolution path against the declared `FORMAL` tree.

**Violated frozen contract:** annex v0.5 §§2–3 require the reviewed payload to deterministically reconstruct the already-frozen v0.2/v0.3 bytes without new runtime authority and to be the executable one-shot launcher.

**Exact acceptance:**
1. Bind those source bytes to an authority that actually contains them: e.g. use the already-frozen blob OIDs directly with exact path/OID/raw-SHA checks that do not falsely require membership in `9dd2fb8...`, or embed the exact canonical bytes in the reviewed payload.
2. Do not change the candidate parent (`9dd2fb8...`) merely to make the lookup succeed; source-document authority and candidate-parent authority must remain distinct.
3. Add a direct static/temporary-repo witness that the exact frozen payload resolves both source authorities successfully and rejects wrong OID/path/raw bytes.

### HIGH-2 — FD handoff is not the frozen FD=3/4/5 procedure and can close the target descriptor itself

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.5.py:180-198`, especially line 197.

The payload performs:

`os.dup2(rd, target); os.close(rd); os.lseek(target, 0, os.SEEK_SET)`.

If `rd == target` (the ordinary clean-process case can yield reader fd 3 for target 3, then 4/4, 5/5), `dup2` is a no-op and the following `os.close(rd)` closes the target itself; `lseek(target, ...)` then fails with `EBADF`. Thus the exact launcher can fail even after correct backing bytes are created.

Even when `rd != target`, the implementation omits inherited v0.4/v0.2 requirements: retained writer/path identity equality, reader/path identity recheck, target `fstat`/full-byte verification after `dup2`, explicit inheritable/CLOEXEC proof, and `/proc/self/fd` enumeration/closure so the final process inherits only FD 3/4/5.

**Violated frozen contract:** annex v0.4 §3 steps 3–4 and annex v0.2 §4, which v0.5 says it does not supersede except for the three named remediation gaps.

**Exact acceptance:**
1. Make same-fd handoff correct (`rd == target` must not be closed) and prove targets 3/4/5 remain open, seekable at offset 0, inheritable, and bound to the exact backing-file identity/raw bytes.
2. Retain and compare writer/path/reader/target identities as frozen; reject replacement even when replacement bytes are identical.
3. Enumerate actual open FDs and close every inherited descriptor except 3/4/5, then re-enumerate and prove the exact set.
4. Add direct temporary-process witnesses for same-fd and different-fd cases and for an injected extra inherited FD.

### HIGH-3 — worktree postcondition and launcher-owned cleanup/`ROLLBACK_INCOMPLETE` semantics are missing

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.5.py:175-203` (`main`).

The first `git worktree add` occurs at line 175 **before** entering the `try/finally`. If native Git partially mutates and returns nonzero, or if the wrapper's post-command route recheck detects drift, the exception escapes before the cleanup block exists. A launcher-owned worktree can therefore remain without the required cleanup/terminal proof.

After a nominal add, the payload also skips the frozen v0.4 checks that the clean root is the exact new worktree, `HEAD == formal_parent`, status is clean, and `worktree list --porcelain` binds exactly that path. On later failure, cleanup unconditionally runs `git worktree remove --force CLEAN` without a retained clean-root/path ownership identity, and it does not prove clean-root/backing-path absence plus worktree-list absence afterward. No code distinguishes ordinary launcher FAIL from `ROLLBACK_INCOMPLETE`.

This is not a documentation-only omission: annex v0.5 §4 explicitly claims post-add drift uses frozen cleanup or reports `ROLLBACK_INCOMPLETE`, but the exact payload does neither reliably.

**Violated frozen contract:** annex v0.4 §§3–4 inherited by v0.5; system reviewer contract for post-mutation failures preserving ownership evidence and forbidding ordinary abort when cleanup cannot be proven.

**Exact acceptance:**
1. Put the first possibly-mutating `worktree add` inside an ownership-aware transaction whose failure path runs even if Git returns nonzero or the immediate post-Git route check fails.
2. After add, directly prove exact clean-root identity, detached `HEAD == FORMAL`, clean status, and exact worktree-list binding before any backing file is created.
3. Retain clean-root/admin ownership identity; only remove when ownership still matches. Never `--force` a foreign replacement.
4. After cleanup prove clean root + backing paths absent and no worktree-list entry. Any uncertain/mismatched cleanup must terminate as explicit `ROLLBACK_INCOMPLETE`, preserving evidence and forbidding retry.
5. Add causal temporary-repo witnesses for partial/nonzero add, post-command route drift, foreign clean-root replacement, cleanup failure, and successful verified cleanup.

### HIGH-4 — parent Git routing/config authority is still TOCTOU-prone and weaker than the already-closed authority

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.5.py:57-116` (`route_snapshot`, `check_route`, `git`).

The launcher checks `.git` with `lstat`, but does not retain a no-follow directory FD/identity for it. It checks `config` with `lstat` and then reads it through a separate pathname `open(...)` (without `O_NOFOLLOW`), and later reopens the pathname again for byte comparison instead of reading from a retained FD. It also does not bind/resolve the Git common-dir routing authority (`commondir`/common directory identity) before the first native Git command.

The already-closed execution-authority implementation at `9dd2fb8...` is stricter: it retains no-follow FDs for routing files/directories and rechecks path identity + FD identity/raw bytes before/after each Git observation. v0.5 therefore regresses the exact authority that prior HIGH-3 required it to match or strengthen.

A same-bytes replacement or routing replacement can occur between `lstat` and pathname `open`, and a `commondir` route can change the objects/refs authority consumed by `git worktree add` while the current checks still focus only on `.git/config`.

**Violated frozen contract:** prior v0.4 HIGH-3 acceptance; annex v0.5 §4 promise of parent `.git`/common-config identity and no-follow authority revalidation; authority hierarchy forbidding regression from the closed execution-authority contract.

**Exact acceptance:**
1. Before first Git, bind `.git`/git-dir/common-dir and common config using no-follow retained FDs and exact `(dev,ino[,size])` + raw-byte authority; explicitly reject or resolve/bind `commondir` according to the already-approved routing policy.
2. Read config bytes from the retained no-follow FD, not a later pathname reopen; bind `config.worktree` absence and strict allowlist in the same snapshot.
3. Immediately before and after every native Git observation/mutation (including cleanup), revalidate both pathname identities and retained FD identities/raw bytes.
4. Add direct route/config replacement-race witnesses analogous to the already-approved bootstrap routing tests.

## Blocker summary

- current blockers: `4 HIGH`
- production child/runtime blockers: `0` (child unchanged)
- execution-request/launcher blockers: `4 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.5.py:120)`

This verdict binds only exact pair `8d1c10015a632c3c48eb46ad26b3180658cee0a1 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization is authorized. No source/checkpoint I/O, JSON/worktree/index/candidate/ref/evidence creation, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized by this review.