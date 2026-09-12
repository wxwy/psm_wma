# ChatGPT Review — Authority-root Materialization Execution Request v0.2 Runtime-authority Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `15e665576c8af37dbbbaf15cd05d2b4bf6af2f63`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and the child commit is independently reachable in `wxwy/cosmos-framework`.

The delta from prior reviewed pair `cfdd2fc79142b500910613759d316b283bfe372a / 93a89ba...` is docs/bookkeeping only. No production root tooling or child/runtime code changes are introduced.

## Prior HIGH closure

### Prior HIGH — competing v0.1/v0.2 runtime authorities: CLOSED

The remediation now explicitly narrows inheritance from v0.1 to only:

- one-shot transaction semantics;
- evidence semantics;
- PASS/FAIL semantics;
- rollback semantics;
- prohibition boundaries.

It explicitly removes v0.1 runtime paths, executable identity, remote, environment, metadata, input, bootstrap and argv declarations from authority.

Section 4 now makes the future snapshot annex the **sole authority** for every runtime field it enumerates, while preventing the annex from overriding v0.2 §2 formal parent/Gitlink/fixed ref/four-module identities or §3 routing-authority contract.

The stale `remote=origin` ambiguity is closed: the annex must carry the exact credential-free canonical HTTPS endpoint string and SHA-256, and a remote alias (including `origin`) is explicitly forbidden as a substitute.

The annex field set also now covers the acceptance-required runtime ABI:

- fresh absolute clean-worktree/index/evidence and `.pending` paths;
- Python/Git absolute path, raw SHA and version;
- canonical sanitized environment raw bytes and digest;
- exact endpoint string and SHA-256;
- commit metadata;
- exact selection/config canonical bytes, raw SHA and native blob OID;
- bootstrap raw bytes/SHA;
- complete argv canonical bytes/SHA;
- all FD/open/inheritance semantics required by the current parser/launcher ABI.

Those annex values become immutable once approved. This removes the previous double-authority conflict and provides a unique future invocation identity for the later materialization approval.

## Scope assessment

The request remains strictly docs-only and read-only at this Gate. Approval permits only preparation of the snapshot annex. It does **not** authorize:

- creation of JSON, clean worktree, temporary index, candidate, ref or evidence;
- opening a source handle or checkpoint/source I/O;
- project-code/materialization execution;
- collection/receipt/publication/root audit;
- child/runtime changes;
- CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

The annex and complete execution command still require an independent same-pair three-party `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` before any execution.

## Blocker summary

- prior HIGH: CLOSED
- docs/request blockers: `0`
- implementation blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_SNAPSHOT`

This verdict binds only exact pair `15e665576c8af37dbbbaf15cd05d2b4bf6af2f63 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Approval is limited to preparing the read-only snapshot annex described by v0.2 §4. It is not an approval to materialize or mutate repository/source/evidence state.