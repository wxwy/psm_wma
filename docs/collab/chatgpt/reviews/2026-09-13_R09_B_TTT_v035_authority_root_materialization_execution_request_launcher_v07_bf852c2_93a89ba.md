# ChatGPT Review — Authority-root Launcher Payload v0.7 Static Closure

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `bf852c233b2c2e31eb33dc859188a9a4b41c50df`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior reviewed `80132197c29bd139e3e05ce6deb3cbcf8f525de6 / 93a89ba61306d840a008813f62f26a34d54850f4` pair. `V2` was re-locked before review at bookkeeping/delivery HEAD `2b6ab250298408e5959131879a48d9074db2c258`; live `CODEX_INBOX.md` names the exact pair above. The effective delta is root docs/tooling only: immutable v0.7 payload, remediation/witness plans, witness core/tests, annex/request and normal status/coordination records. Child/runtime is unchanged.

## Authority chain used

The review applies the inherited v0.2/v0.3 frozen runtime bytes/FD ABI/tool identities, the v0.4 launcher mutation/cleanup semantics, the prior v0.6 exact-pair review, and v0.7 annex only where it explicitly supersedes the launcher artifact. v0.7 does not supersede the post-mutation fail-stop rule or the requirement for direct causal Evidence.

The formal v0.7 request itself states that approval is not requested until the full temporary native-Git witness matrix has been completed and independently reviewed; the v0.7 annex likewise says the remaining full native-Git causal witnesses are mandatory before any materialization verdict.

## Prior blocker disposition

- v0.6 HIGH-1 (first `worktree add` mutation boundary): **PARTIALLY CLOSED / STILL BLOCKING**. v0.7 correctly converts every exception raised by the exact `run(... worktree add ...)` call to `ROLLBACK_INCOMPLETE`, but there remains a post-success ownership-capture gap immediately after that call.
- v0.6 HIGH-2 (`.git/commondir` authority): **CLOSED**. Ordinary `.git` now rejects `commondir` and `config.worktree` and revalidates both absence predicates before/after native Git commands.
- v0.6 HIGH-3 (backing pathname/mode identity): **CLOSED**. v0.7 revalidates non-symlink regular pathname identity and exact `0600` mode after reader-open and after target handoff.
- v0.6 HIGH-4 (causal Evidence matrix): **NOT CLOSED**. The 6/6 witness suite is still helper/classifier-heavy and does not exercise all frozen payload seams required by the witness plan/annex.

## Blockers

### HIGH-1 — exact FD close-set check deterministically observes its own `/proc/self/fd` enumeration FD and fails before `execve`

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7.py:147-152`.

After the three backing FDs are installed, the payload enumerates `/proc/self/fd`, closes every descriptor not in `{3,4,5}`, and then performs:

`if {int(x) for x in os.listdir("/proc/self/fd")} != keep: fail("fd closure")`

On Linux, enumerating `/proc/self/fd` itself requires an open directory descriptor while the directory entries are read. That transient descriptor is visible in the directory listing. Once the first loop has closed 0/1/2 and every non-kept descriptor, the second `os.listdir()` can reuse the lowest free descriptor (normally 0); the returned names therefore include that transient descriptor in addition to 3/4/5 even though it is closed when `os.listdir()` returns. The raw name-set comparison consequently rejects a process whose durable inherited set is exactly `{3,4,5}`.

The current witness does not close this. `witness_core.require_exact_fd_set()` only checks an already-constructed Python set, and the test merely asserts `{3,4,5}` passes while `{0,3,4,5}` fails. It never exercises the exact `/proc/self/fd` enumeration/close/re-enumeration seam, so it misses the transient enumeration FD that the production payload itself creates.

**Violated frozen contract:** v0.4 launcher FD close policy and inherited v0.2 FD ABI require the final process to inherit exactly FD 3/4/5 and reach the final `execve`; Evidence must directly witness the production close-set behavior.

**Exact acceptance:**
1. Replace the raw directory-entry equality test with a method that proves the durable open descriptor set while excluding the enumeration descriptor itself (for example, after the listing has closed, validate candidate descriptors with `fstat` and ignore `EBADF`, or use another causally correct scheme).
2. Preserve the exact invariant that only 3/4/5 are inheritable/open at `execve`; do not simply weaken the expected set.
3. Add a forked temporary-process witness that exercises the exact v0.7 close-set seam with 0/1/2 plus injected extra FDs, and proves that the child immediately before exec has exactly the intended durable 3/4/5 set.

### HIGH-2 — successful `worktree add` can mutate state and then lose CLEAN before `owned` is bound, escaping as ordinary failure

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7.py:137-144`.

v0.7 wraps only `run(s,"worktree","add",...)` in the inner `try/except`, converting exceptions from the native command, its post-route check, or its return-code check to `ROLLBACK_INCOMPLETE`. That is an improvement.

However, after `run()` returns successfully, the next statement is `owned=os.lstat(CLEAN)`. If the just-created CLEAN path disappears or lookup otherwise fails after the Git mutation but before this assignment completes, the exception is handled only by the outer block. Since `owned` does not yet exist, the outer handler skips `cleanup(...)` and re-raises the ordinary `OSError`/lookup failure. This is a post-mutation uncertainty path that is neither verified rollback nor explicit `ROLLBACK_INCOMPLETE`.

The v0.7 remediation plan itself said the success path would immediately retain a no-follow CLEAN directory FD/identity; the exact payload does not do that. The current tests also do not inject successful-add followed by CLEAN disappearance/replacement before ownership capture.

**Violated frozen contract:** inherited v0.4 launcher-owned cleanup contract and the project post-mutation rule: once first irreversible mutation may have occurred, no ordinary abort is allowed unless rollback/absence is directly proved.

**Exact acceptance:**
1. Treat ownership capture as part of the mutation-boundary helper. After native add returns, immediately acquire/bind CLEAN with no-follow directory FD + identity (and the corresponding worktree/admin binding) before the path can be treated as owned.
2. Any failure to bind/verify ownership after a possibly successful add must terminate as `ROLLBACK_INCOMPLETE`; it must not escape as ordinary `OSError`/`Stop`.
3. Preserve the existing rule that foreign replacement is never force-removed.
4. Add causal temporary-repo witnesses for successful add followed by CLEAN disappearance/replacement before ownership capture, in addition to nonzero/partial add and post-route-drift cases.

### HIGH-3 — formal target is not eligible for `APPROVE_TO_MATERIALIZE`, and the supplied Evidence still does not satisfy its own native-Git witness matrix

**Locations:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.7.md:3-5`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.7.md:14-16`
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7_witness_test.py:80-95`

The formal request explicitly says approval is **not requested** until the full temporary native-Git witness matrix has been completed and independently reviewed. The annex separately says remaining full native-Git causal witnesses are mandatory before any materialization verdict. Those are part of the exact formal target and cannot be overridden by a live-Inbox sentence asking for `APPROVE_TO_MATERIALIZE`.

The current 6/6 suite is not that matrix:

- the native Git test covers only a happy-path temporary `worktree add --detach` / `remove --force` with manual `check_route()` calls;
- add failure is represented by a pure classifier, not the exact payload `run/add` seam;
- cleanup success/failure is represented by a pure classifier, not `payload.cleanup()` with real temporary worktree/admin state;
- the FD test is a pure set helper and misses the production `/proc/self/fd` enumeration behavior described in HIGH-1;
- there is no causal injection for partial/nonzero add, successful-add + post-route drift, route/config replacement during the native-Git seam, foreign CLEAN replacement, or cleanup failure/verified cleanup across the exact payload ordering.

There is also an Evidence-model inconsistency: `classify_add_failure(clean_absent, listed=False)` is asserted to return ordinary `FAIL`, while the v0.7 annex and exact payload freeze every exception from the first `run(... worktree add ...)` call to `ROLLBACK_INCOMPLETE`. A helper that models a different failure contract cannot close the exact production contract.

**Violated frozen contract:** direct causal Evidence principle; current v0.7 request/annex admission condition; formal-pair authority hierarchy.

**Exact acceptance:**
1. If this is intentionally only a **static-closure** review, create a dedicated non-materialization Gate/verdict literal and make the formal request + CODEX_INBOX agree that no materialization approval is being requested.
2. If the target is `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`, first complete the full v0.7 witness matrix on the replacement exact pair, then submit a new formal request that explicitly requests that literal.
3. Replace helper-only classifier Evidence with direct temporary-only witnesses against the exact payload seam or the smallest faithful extracted seam; the witness must fail if production ordering/authority regresses.
4. Reconcile add-failure semantics across payload, annex, witness core and tests.

## Blocker summary

- current blockers: `3 HIGH`
- child/runtime production blockers: `0`
- launcher/execution-request production blockers: `2 HIGH`
- Gate/Evidence blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_launcher_payload_v0.7.py:152)`

This verdict binds only exact pair `bf852c233b2c2e31eb33dc859188a9a4b41c50df / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization is authorized. No source/checkpoint I/O, JSON/worktree/index/candidate/ref/evidence creation on the real project, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized by this review.
