# ChatGPT Review — Authority-root Execution Snapshot Annex v0.1

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `29c8aaa2a048f538892295afa6bc6d49031b0d0c`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is independently reachable in `wxwy/cosmos-framework`.

Relative to the approved snapshot-preparation authority at `15e665576c8af37dbbbaf15cd05d2b4bf6af2f63`, the effective delta is docs/bookkeeping only: the new snapshot annex, SESSION/CODEX coordination, and prior review persistence. No production root tooling or child/runtime code changes are introduced.

## What is correct

- The annex preserves materialization formal parent `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`, child/Gitlink, fixed ref and current adapter identity.
- The canonical credential-free HTTPS endpoint is explicit and its stated UTF-8 SHA-256 matches the endpoint string.
- The selection/config SHA-256 and native OID values align with the previously frozen materialization request identities.
- The annex explicitly remains non-executing: no JSON/worktree/index/candidate/ref/evidence/source handle is created, and execution still requires a later exact three-party `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT`.

## Blocker

### HIGH-1 — the annex does not itself freeze the complete runtime authority required by the approved v0.2 contract

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.1.md:22`

The immediately preceding approved v0.2 contract at exact pair `15e66557... / 93a89ba...` states that the snapshot annex is the **sole authority** for its runtime fields and must itself freeze/display:

- canonical sanitized-environment raw bytes **and digest**;
- commit metadata;
- exact selection/config canonical bytes + raw SHA + native blob OID;
- bootstrap raw bytes + SHA;
- complete argv canonical bytes + SHA;
- all FD/open/inheritance semantics required by the current parser/launcher ABI;
- with annex values immutable after annex approval.

The current annex instead provides only a partial snapshot and explicitly defers authority-critical fields to the **later execution request**:

> “实际 FD numbers、bootstrap raw bytes、完整 argv canonical bytes/SHA 与 commit metadata 必须在后续 execution request 中…冻结”

It also lists sanitized environment key/value pairs but does not freeze canonical environment bytes or their digest, and it gives selection/config length/hash/OID without the exact canonical bytes required by the approved contract.

This is not merely missing documentation. If this annex were approved, the later execution-request review would still be allowed to choose previously-unfrozen authority-critical values after the annex approval. That contradicts the v0.2 guarantee that the annex is the single immutable runtime authority and defeats the purpose of the separate snapshot-preparation Gate.

## Exact acceptance

1. The annex itself must freeze the canonical sanitized launcher-environment bytes and SHA-256. If launcher/bootstrap env and the deterministic `NativeAuthorityGit.env` are distinct authorities, state that distinction explicitly and freeze the complete derivation/binding for both.
2. Include the exact selection and config canonical bytes themselves, or bind them to exact immutable annex-owned artifacts whose path/blob/raw identity makes the bytes uniquely recoverable; retain byte length, raw SHA-256 and native blob OID.
3. Freeze actual selection/config/bootstrap-contract FD numbers and the exact open/inheritance/lifetime/offset/no-follow/regular-file semantics required by the current launcher/parser ABI. No FD number or FD policy may first appear in the later execution request.
4. Freeze the exact bootstrap raw UTF-8 bytes and SHA-256 in this annex.
5. Freeze the complete parser argv canonical bytes and SHA-256 in this annex, including the exact canonical HTTPS endpoint string rather than an alias.
6. Freeze exact commit metadata in this annex.
7. State that the later execution request may only reproduce/assemble an execution command from these already-frozen annex values; it may not introduce, substitute or mutate any runtime field. Execution-time freshness/expected-zero/routing checks must still be re-observed before mutation.
8. Preserve the current read-only boundary: no project-code execution, FD backing-file creation, clean worktree/index/evidence creation, candidate/ref mutation, source read, collection/receipt/publication, child/runtime, GPU or training before later exact three-party materialization approval.

## Blocker summary

- snapshot-annex blockers: `1 HIGH`
- implementation blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.1.md:22)`

This verdict binds only exact pair `29c8aaa2a048f538892295afa6bc6d49031b0d0c / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization, JSON/worktree/index/candidate/ref/evidence/source-handle creation, source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.