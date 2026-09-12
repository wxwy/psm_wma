# ChatGPT Review — Authority-root Materialization Execution Request v0.2

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `cfdd2fc79142b500910613759d316b283bfe372a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` tree entry is a submodule/Gitlink to `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is independently reachable in `wxwy/cosmos-framework`.

The delta from the closed authority implementation parent `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5` is docs/status/review bookkeeping only. No production root tooling or child/runtime code changes are introduced by this pair.

## What is correctly rebound

v0.2 correctly makes `9dd2fb8b...` the sole materialization formal parent and preserves the exact child/Gitlink and fixed authority ref. The four formal module blob OIDs in the request match the closed `9dd2fb8...` tree, including the current adapter blob `da782754...` and the unchanged authority/collection/audit blobs.

The request also correctly carries forward the closed routing-authority boundary: frozen stdlib bootstrap, pre-import four-module closure, real `git_dir`/common-dir authority, actual `config.worktree` absence, and before/after routing/config revalidation. The requested verdict is explicitly limited to preparing a read-only snapshot annex; §4 states that neither the annex nor this review authorizes materialization, and a separate exact `APPROVE_TO_MATERIALIZE...` remains mandatory before execution.

## Blocker

### HIGH-1 — v0.2 creates two competing authorities for runtime execution identity

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.2.md:12`

v0.2 says that, except for the formal-tree identity it explicitly replaces, v0.1's inputs/transaction/evidence/rollback/prohibitions continue **verbatim**. But §4 then says the annex must “re-freeze” v0.1 §2–§3 runtime facts such as paths, tool identities, environment, remote identity, metadata, input identities, bootstrap and argv.

Those two statements are not equivalent, because v0.1 contains stale execution ABI values that cannot remain authoritative under the now-closed production adapter. Most importantly, v0.1 explicitly requires adapter `remote=origin`, while current production preflight rejects production remotes that are not a canonical credential-free HTTPS endpoint. v0.1 also freezes old execution paths and the old `ad9e011...` launch context that were written before the execution-authority/routing closure.

Therefore an annex cannot currently be both:

1. compliant with the v0.2 statement that v0.1 runtime inputs remain verbatim; and
2. compliant with the current production ABI that must be used for the later one-shot execution.

The ambiguity is authority-critical, not editorial: the future approval would not have a unique answer to which exact remote/path/argv/tool identity controls the invocation. The fact that this Gate only authorizes preparing the annex does not remove the problem, because the purpose of the annex is to become the single frozen runtime authority for the subsequent `APPROVE_TO_MATERIALIZE` review.

### Exact acceptance

1. Narrow the v0.1 inheritance clause. State explicitly that only v0.1 transaction semantics, PASS/FAIL/rollback semantics and prohibition boundaries survive unless restated by v0.2; stale runtime values/paths/tool identities/remote/argv/bootstrap declarations do **not** remain authoritative.
2. State that §4 annex is the sole authority for every runtime field it enumerates, while it may not replace v0.2 §2 formal parent/Gitlink/fixed ref/four-module identities or §3 routing-authority contract.
3. Replace the v0.1 `remote=origin` inheritance with an annex requirement for the exact credential-free canonical HTTPS endpoint string **and** its SHA-256. A remote alias is not acceptable.
4. Require the annex to freeze exact fresh absolute clean-worktree/index/evidence(+pending) paths, exact Python/Git path/raw-SHA/version, canonical sanitized environment bytes/digest, commit metadata, exact selection/config canonical bytes + raw SHA + native blob OID, bootstrap raw bytes/SHA, complete argv canonical bytes/SHA, and all FD/open/inheritance semantics needed by the current parser/launcher ABI.
5. State explicitly that those annex values supersede the corresponding stale v0.1 runtime values and may not be changed after annex approval.
6. Preserve the current docs-only/read-only boundary: no JSON/worktree/index/candidate/ref/evidence/source handle creation and no project-code/materialization execution before the later exact three-party `APPROVE_TO_MATERIALIZE...`.

## Blocker summary

- docs/request blockers: `1 HIGH`
- implementation blockers: `0` (closed `9dd2fb8...` implementation remains authoritative)
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.2.md:12)`

This verdict binds only exact pair `cfdd2fc79142b500910613759d316b283bfe372a / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization, JSON creation, clean worktree/index/evidence creation, ref/origin mutation, source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.