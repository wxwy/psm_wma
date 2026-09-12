# ChatGPT Review — Authority-root One-shot Materialization Execution Request v0.3

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `3b67d317de595ac8df2529eabfb239efbf988733`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and that child commit is independently reachable in `wxwy/cosmos-framework`.

The delta from the approved snapshot-annex pair `b2fc05489abb2a4c1bc7314844c94c197834b9ff` is docs/status/review bookkeeping only. No production root tooling or child/runtime code changes are introduced.

The approved annex v0.3 remains the sole frozen runtime authority for formal parent/Gitlink/fixed ref, endpoint, tools, selection/config bytes, FD numbers, bootstrap bytes/contracts, parser/bootstrap argv, launcher and transaction environments, metadata and module identities.

## Blocker

### HIGH-1 — the request asks for real materialization approval without the complete auditable launcher/command required by the approved annex

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.3.md:17`

The preceding approved annex explicitly states that the **complete execution request and command** must receive a separate exact three-party `APPROVE_TO_MATERIALIZE...` before execution. The present request freezes high-level transaction semantics but does not contain the actual launcher/command or an equivalent canonical executable launch artifact.

This is authority-critical because several operations necessarily occur before the already-approved production adapter can enforce its own bootstrap contract:

- proving the clean-worktree path is absent and creating the detached clean worktree at the frozen formal parent;
- provisioning the exact selection/config/bootstrap-contract backing objects;
- opening/validating them and binding them to exact FD 3/4/5 with the approved no-follow/regular/inheritance semantics;
- closing all non-authorized descriptors;
- constructing the exact `execve` invocation of frozen Python with `-I -S -B -c`, the frozen bootstrap payload, literal `--`, frozen parser argv, and the frozen six-key launcher environment;
- defining failure/cleanup semantics for launcher-owned worktree/admin metadata and backing objects before control reaches the project adapter.

The request only says these conditions must hold and that no shell/PATH/ambient authority may be used. It does not freeze how they are actually achieved. A post-approval operator/launcher therefore still has to make new authority-bearing choices. In particular, clean-worktree creation itself mutates the repository/worktree administration state before the production adapter runs; the current statement that any preflight drift is a “zero mutation FAIL” does not define how failures after such launcher-side mutation are cleaned up or classified.

This is not a request to add a new horizontal provenance Gate. It is the missing last-mile execution authority inside the same materialization Gate.

### Exact acceptance

1. Include the complete one-shot launcher/command in the reviewed request, or freeze an equivalent canonical launcher artifact/procedure whose exact bytes/identity and invocation are reviewable. It must not introduce shell, PATH, remote alias, ambient environment, caller mapping or any other authority outside the approved annex.
2. Freeze the exact pre-adapter sequence for:
   - clean-root absent check and exact detached-worktree creation at `9dd2fb8...` using the frozen Git executable/isolation;
   - creation/ownership of the three backing objects carrying the already-frozen selection/config/bootstrap-contract bytes;
   - exact FD 3/4/5 open/dup/inheritance/lifetime/offset handling and closure of every other inherited FD;
   - exact `execve`/process launch of the frozen Python/bootstrap/`--`/parser argv/environment.
3. Bind launcher-side mutations to explicit ownership-aware failure semantics. If clean-worktree/admin/backing-object mutation has occurred, ordinary FAIL is allowed only after exact cleanup/freshness recovery is proven; otherwise fail-stop as `ROLLBACK_INCOMPLETE` (or an already-frozen equivalent terminal) without ref/materialization retry or continuation.
4. The launcher/command may only reproduce authority already frozen by annex v0.3. If implementing the launcher requires new executable/payload bytes or other runtime authority not present in the annex, amend the annex/request within this same Gate and obtain a new exact-pair review before execution.
5. Preserve the current scope: this approval request must still exclude source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime changes, CUDA/GPU, training, evaluation, inference and LIBERO4IN1.

## Blocker summary

- docs/request blockers: `1 HIGH`
- implementation blockers: `0` (closed `9dd2fb8...` production implementation remains authoritative)
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.3.md:17)`

This verdict binds only exact pair `3b67d317de595ac8df2529eabfb239efbf988733 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization, JSON/worktree/index/candidate/ref/evidence creation, source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized by this review.
