# ChatGPT Review — Authority Root Real Adapter / Execution Request Design v0.2

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

## Exact formal pair

- root design SHA: `dd0ecdf19e3413be4f8dad5e7b069e106f88e8ad`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `7c17c90a3b25182436fef89fbe063de9fcf1d67e`; the child is unchanged. The formal tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to the child SHA above. The child commit is reachable in `wxwy/cosmos-framework`.

The latest polling records also show MM and Kimi independently retained the exact-pair final `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_REAL_ADAPTER_CPU_STATIC`. Those results are coordination evidence only and are not inherited as ChatGPT's technical conclusion. No pre-existing ChatGPT exact-pair review was found before this review.

## Review basis

Reviewed against:

- materialization/binding design v0.1 + ABI v0.2;
- the closed synthetic authority-root implementation and its exact publication/rollback API;
- prior ChatGPT review on `7c17c90... / 93a89ba...`;
- current v0.2 remediation;
- the existing production `prepare_candidate -> verify_candidate -> publish_candidate` implementation, including its private rollback lifecycle;
- the future exact execution/binding evidence requirements.

## Prior blocker closure

### Prior HIGH-1 — wrong frozen native Git blob OIDs: CLOSED

v0.2 corrects both native Git blob OIDs to the values independently recomputed from the exact no-trailing-newline bytes:

- selection: `9f03614b691bca3ba834e16e65ee983fe95af74c`;
- config: `89b12047c50a3a924521200d1897b13bf30aacfe`.

It also requires temporary-repository `hash-object --stdin` cross-checks rather than trusting copied constants.

### Prior HIGH-2 — remote expected-old CAS was ambiguous: CLOSED

v0.2 now freezes a narrowly scoped per-fixed-ref exact-old lease:

- create: expected absent -> exact candidate;
- rollback: expected exact candidate -> absent;
- unconditional/general force, normal overwrite, delete/recreate and retry-to-win are explicitly prohibited;
- each mutation is followed by fresh remote observation;
- fast-forwardable foreign-ancestor races are required tests.

This is consistent with the already-closed ownership-aware publication state machine.

### Prior HIGH-3 — evidence contract: PARTIALLY CLOSED

v0.2 materially improves the record by adding a fixed top-level schema, transaction observations, endpoint ownership/CAS outcomes, rollback fields, stable failure phases/codes, digesting and a filesystem writer. However, two blocking issues remain below.

## Current blockers

### HIGH-1 — evidence-write failure after successful publication cannot satisfy the frozen rollback contract within the inherited API/allowlist

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.2.md:61-63`

**Root cause**

The design requires:

- a PASS record to contain post-publication observations and committed-binding reverify;
- `evidence_write` as a failure phase;
- every failure after publication mutation to perform complete rollback, otherwise `ROLLBACK_INCOMPLETE`;
- the real adapter to reuse the closed publication/rollback algorithm rather than copy it;
- an inherited two-file implementation allowlist containing only the new adapter/CLI and its test.

But the currently closed production API cannot implement that state machine. `publish_candidate()` performs rollback only inside its own exception path. Once it succeeds, it returns a `PublicationWitness`; the ownership-aware rollback function remains private inside `immutable_source_authority_root.py` and there is no public one-shot recovery/finalization API for a subsequent evidence-writer failure.

Therefore, if both refs are successfully published and the evidence writer then fails, the adapter has only three choices under the current design, all invalid:

1. leave the successfully-created refs behind despite an `evidence_write` FAIL;
2. copy/reimplement the rollback algorithm in the adapter, violating the reuse rule;
3. import/use the private `_rollback` as a new cross-module contract, which is not frozen and conflicts with the project's public-interface discipline.

There is a related post-rename ambiguity. The writer says a failure after rename must re-read the record and that stale PASS must not remain visible, but it does not freeze an ownership-aware cleanup/commit-point rule for a PASS file that is already visible when directory fsync or a later step fails. Rolling refs back while a valid-looking PASS record remains visible would create an auditable false positive.

**Violated frozen contract**

- prior HIGH-3 acceptance: writer failure must not leave a stale visible PASS;
- closed publication contract: post-mutation failure must use the same ownership-aware remote->local conditional rollback and fresh final observations;
- v0.1 inherited rule: adapter must reuse, not duplicate, ref/rollback logic.

**Exact acceptance**

Keep remediation in this same design Gate and choose one explicit architecture before implementation:

1. **Preferred:** expand the implementation allowlist to include `immutable_source_authority_root.py` plus its direct test and expose a public one-shot publication-finalization/recovery seam bound to the returned `PublicationWitness`; evidence finalization failure must enter the already-frozen remote->local conditional rollback using same-activation ownership.
2. Or integrate evidence finalization into the authority publication transaction through an explicit callback/orchestrator owned by the authority module, so an evidence failure remains inside the existing rollback try/except boundary.

In either case:

- do not duplicate rollback logic in the adapter;
- freeze the evidence-file commit point and ownership rules;
- ordinary `evidence_write` failure after ref mutation may return `FAIL` only if both refs are freshly proven absent **and** no accepted PASS evidence remains visible;
- if evidence cleanup, ref cleanup, or final observations cannot be proven, return `ROLLBACK_INCOMPLETE` and fail-stop;
- deterministic tests must cover writer failure before rename, immediately after rename, file fsync failure, directory fsync failure, cleanup failure, and prove consistency between final refs and accepted evidence visibility.

### HIGH-2 — `evidence v1` is called exact, but nested schemas/types and phase-derived nullability are not frozen enough for an independent verifier

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.2.md:50-61`

**Root cause**

The document fixes top-level and section names but leaves important nested ABI and chronology choices implementation-defined. Examples:

- `execution.adapter`, `authority_module`, `interpreter`, `git_executable` and `commit_metadata` do not have exact nested key/type sets;
- `local_observation` / `remote_observation` have no exact representation for `absent`, concrete revision and unreadable/error states;
- there is no exact per-phase table specifying when `authority`, `candidate`, pre/post observations, publication booleans and rollback fields must be concrete, `null`, or fixed `false`;
- `prepare`/`verify` failures can occur after a candidate object exists but before a verified seven-key mapping exists, yet the allowed partial shape is not frozen;
- the document says `status-reachability` drift must be rejected without defining the mechanical reachability relation the verifier must enforce.

That means two implementations could emit materially different records for the same first-failure point and both claim conformance. A later reviewer cannot mechanically derive chronology from the record alone, which is the purpose of freezing this evidence before real execution.

**Violated frozen contract**

The prior HIGH-3 acceptance required an exact canonical PASS/FAIL/`ROLLBACK_INCOMPLETE` evidence schema that mechanically distinguishes transaction history rather than relying on transient logs or current state.

**Exact acceptance**

Freeze, in the design itself:

1. exact nested key sets and primitive types for tool/module/executable identities and `commit_metadata`;
2. one exact observation type, for example an exact object whose state is `absent|revision|unreadable` with revision/error fields having fixed nullability;
3. one ordered phase/state table with **first-failure identity** and, for every phase, the exact concrete/null/false shape of `authority`, `candidate`, `pre_publication`, `publication`, `post_publication`, `rollback` and `failure`;
4. exact candidate partial-state rules for `prepare` versus `verify` failures, with no placeholder revision/tree/binding values;
5. exact `PASS`, ordinary rolled-back `FAIL`, and `ROLLBACK_INCOMPLETE` terminal invariants;
6. direct validator tests that mutate every section across representative phases and prove malformed chronology/nullability is rejected.

This does not require a new horizontal Gate; it is the remaining closure of the existing evidence-design requirement.

## Blocker summary

- production/design blockers: `2 HIGH`
- Evidence-only blockers: `0` (both are design blockers because the next stage implements the real adapter/evidence writer)
- total blockers: `2`

## Non-blocking observations

- The v0.2 raw-byte identities are now internally consistent.
- The exact-old remote lease design is sufficiently narrow and preserves foreign refs.
- The two-stage route remains acceptable: CPU/static real-adapter closure, then a separately reviewed exact execution request before any real materialization.
- The source root remains correctly outside authority JSON and deferred to controlled collection execution.

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.2.md:61)`

This verdict binds only the exact formal pair `dd0ecdf19e3413be4f8dad5e7b069e106f88e8ad` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same real-adapter/execution-request design Gate. This verdict does **not** authorize implementation yet and does not authorize real selection/config files, candidate/ref creation, origin/remote mutation, source read, collection/receipt/source-evidence/publication, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
