# ChatGPT Review — Authority Root One-shot Materialization Execution Request

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root request SHA: `d3cd3c9b26cea021814c9f48bcd864183a811293`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The request commit is independently reachable. Its exact `cosmos-framework` entry resolves to the requested child `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair. The effective delta relative to the previous request-design pair is docs/status only; the closed production adapter remains the exact `ad9e011...` implementation.

## Prior blocker closure

### Prior HIGH-1 — extra request-design Gate: CLOSED

The new document is now explicitly the actual one-shot execution request and asks directly for `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`. No further request-design Gate is inserted.

### Prior HIGH-2 — transitive project source executes before identity proof: PARTIALLY CLOSED

The request correctly identifies the four project modules in the import closure before adapter preflight:

- `tools/psm_wma/materialize_immutable_source_authority_root.py`
- `tools/psm_wma/immutable_source_authority_root.py`
- `tools/psm_wma/immutable_source_collection.py`
- `tools/g0/audit_r09_b_ttt_root_gitlink_authority.py`

Their formal-tree blob identities exist at `ad9e011...`; the audit module itself imports only stdlib. This closes the earlier omission of collection/audit from the declared closure.

However the one-shot executable authority is still not fully frozen/provable, as detailed below.

## Current blockers

### HIGH-1 — this exact pair is not yet an immutable executable one-shot request; it explicitly leaves approval-critical values to be filled later

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.1.md:36-38`

The file asks this exact pair to receive `APPROVE_TO_MATERIALIZE...`, but §启动协议 still says the one-shot review **must later fill in** commit metadata, sanitized-environment canonical bytes/hash, bootstrap raw SHA, complete argv SHA, remote credential-free identity SHA, and exact input/index/evidence paths. The exact bootstrap bytes and actual full command are also represented only as `<frozen-stdlib-bootstrap>` / prose.

That is incompatible with exact-pair approval. A formal verdict cannot authorize values that do not exist in the reviewed formal tree and are intended to be substituted after approval. The request also does not freeze the actual FD numbers/open/inheritance mechanism or a concrete `sys.argv` projection for the `python -c ... -- ...` bootstrap.

The selection/config section similarly gives length/schema/digest but not a self-contained exact raw-byte payload or an immutable formal-tree path/blob from which the launcher is required to obtain those bytes.

**Exact acceptance:** the next formal target must itself contain every execution-significant byte/value before review: exact bootstrap UTF-8 source, exact command/argv and its canonicalization, exact commit metadata, exact sanitized environment, exact remote endpoint identity, exact input bytes or immutable source binding, exact FD numbers plus open/inheritance protocol, exact index/evidence/input paths, and exact failure/cleanup command semantics. No field may say it will be filled after approval. The requested verdict may remain `APPROVE_TO_MATERIALIZE...` only when the reviewed pair is directly executable without post-verdict substitution.

### HIGH-2 — the request's bootstrap/transitive-closure authority cannot be represented by the currently frozen production CLI/evidence ABI

**Location:** request `...materialization_execution_request_v0.1.md:36-38`; production `tools/psm_wma/materialize_immutable_source_authority_root.py::_parser`, `_EXECUTION_KEYS`, `_pass_evidence_record`

The request requires four module identities to be part of the execution authority and states that bootstrap identity must be retained in execution evidence. The closed adapter does not have that ABI:

1. `_parser()` accepts module identity arguments only for `adapter` and `authority-module`. It has no collection/audit identity arguments. Passing four module identity argument triplets to the adapter would fail parsing.
2. `_EXECUTION_KEYS` and `_validate_execution()` allow only `adapter` and `authority_module`; there is no collection/audit identity field and no bootstrap identity/hash field. Extra fields are rejected by exact-key validation.
3. `argv_sha256` is computed from the adapter's `sys.argv[1:]`; a `python -c` bootstrap source is not intrinsically part of that tuple. Therefore the existing Evidence-v1 cannot prove which reviewed pre-import bootstrap actually ran.
4. The request currently says bootstrap raw bytes/identity are to be written into execution evidence, while the frozen Evidence-v1 schema has no legal place for them.

This is not a documentation-only typo: the requested real-execution authority is stronger than what the closed production path can attest.

**Exact acceptance:** choose one coherent contract and make it executable. Either (a) reopen the approved root tooling scope in a fresh implementation formal pair so the parser/invocation/Evidence-v1 directly binds the exact bootstrap plus collection/audit identities, with direct CPU/static witnesses and exact-key validation; or (b) define a separately frozen, independently verifiable pre-import receipt/capability that is consumed by the unchanged adapter without adding an extra provenance Gate and that causally proves the exact bootstrap/four-module closure. Merely describing four checks in the request is insufficient. Any solution must include an adversarial witness that modifies a transitive dependency while adapter/authority files remain unchanged and proves rejection before project import and before authority/ref/evidence mutation.

### HIGH-3 — real Git destination/object semantics are not closed: `--remote=origin` binds only the alias, and the adapter does not disable replacement/config-driven Git semantics

**Location:** request `...materialization_execution_request_v0.1.md:36-38`; production `NativeAuthorityGit.__init__`, `remote_ref`, `cas_create_remote`, `create_detached_commit`; evidence `remote_identity_sha256`

The controlling real-adapter design required the future request to freeze the remote URL identity. The current request instead says adapter `--remote=origin` and leaves a credential-free remote identity digest to be filled later.

In production, `remote_identity_sha256` is literally `sha256(transaction.remote.encode())`. With `transaction.remote == "origin"`, Evidence-v1 binds only the five-byte alias, not the endpoint used by `git ls-remote` / `git push`. A changed repository config can redirect `origin` while producing the same evidence digest.

The same Git transaction environment also omits `GIT_NO_REPLACE_OBJECTS=1` and config-isolation variables used by the project's root source-audit tool. Formal-root `ls-tree/read-tree/show/commit-tree` therefore rely on ambient repository Git semantics rather than a frozen no-replacement authority. At a real-execution Gate, a clean worktree path is not sufficient proof that replace/config semantics cannot alter the object/ref view.

**Exact acceptance:** bind the actual remote transport endpoint used by every `ls-remote`/push, not the alias name, and make Evidence-v1 attest that exact endpoint identity. Also make the Git object view fail-closed against replacement/config drift for all formal-root/candidate commands; the simplest acceptable implementation is a fresh root-tooling formal pair that sets and tests explicit no-replace/config-isolation semantics in `NativeAuthorityGit` and verifies the exact remote endpoint. Add direct CPU/static adversarial witnesses for remote-alias retargeting and replace-ref/config drift. Do not authorize real materialization until the exact adapter path itself enforces these semantics.

## Scope / Evidence notes

- The current formal commit is docs/status only; no child/runtime production file changed.
- Prior CPU/static closure remains closed for the scope it approved. The new production blockers arise because this Gate is the first request to authorize real Git/remote execution, which the CPU/static closure explicitly did not authorize.
- No real JSON/candidate/ref/origin/source/evidence mutation, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## Blocker summary

- prior blockers: HIGH-1 CLOSED; HIGH-2 PARTIALLY CLOSED
- current blockers: `3 HIGH`
- production/real-execution authority blockers: `2 HIGH` (HIGH-2, HIGH-3)
- request completeness blocker: `1 HIGH` (HIGH-1)

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.1.md:36)`

This verdict binds only the exact formal pair `d3cd3c9b26cea021814c9f48bcd864183a811293 / 93a89ba61306d840a008813f62f26a34d54850f4`.
