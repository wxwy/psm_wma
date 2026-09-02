# ChatGPT Independent Review — R09-B2 P4-v4 Execution-Request Lock Design v0.2

- Review date: 2026-09-02
- Prior ChatGPT anchor: `9581400dd0ad7cb73d5aee091648764c6dda700d`
- Design SHA: `8f0482732ca72544c007f054d2d303f2ddb5e83a`
- Formal request / ledger SHA: `d8869ff3e2971e7a39d35517e0d15d7c18c2f8b9`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

Reviewed only the new static `G0-R09-B2-P4-V4-EXECUTION-REQUEST-LOCK` v0.2 design against the already-closed P4-v4 full-request static contract, materialization static contract, frozen run/candidates lifecycle, and the existing P5 run-root roster verifier contract.

This review does **not** reopen the closed Execution Request FULL or Materialization static gates. It does not authorize real request generation, P4 preflight/materialization/staging, candidate/run-root creation, record/refreeze/evidence publication, P5 export/compose, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.

## What v0.2 correctly closes from v0.1

### PASS — lock-spec authority is no longer caller-selected

The new `AUTHORIZED_P4_V4_LOCK_SPEC=None` fail-closed model is directionally correct. The future authority is defined as a reviewer-owned exact commit/tree/Gitlink/spec-path/blob/current-byte/raw-SHA binding, and the caller is no longer permitted to inject a semantic dict/path/SHA. This closes the main v0.1 caller-owned `lock_spec` authority problem at the design level.

### PASS — output target now has a verifier-owned namespace and explicit poison terminal state

The output parent/basename are now authority-owned, parent traversal is intended to use an anchored no-follow FD chain, create uses `O_CREAT|O_EXCL`, and any post-create failure is terminal `POISONED_NOT_LOCKED` with no unlink/repair/rename/retry/overwrite. A poison file is explicitly not an execution authority. This closes the main v0.1 output-target/partial-file ambiguity in principle.

### PASS — real execution remains a separate Gate

The design preserves the required boundary that static request-lock closure is not P4 execution approval. A future exact raw/SHA still requires a separate `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY` review and does not authorize record/refreeze/P5/GPU/training.

## Blocking findings

### B1 — output FD contract is internally impossible, and exact mode setting is underspecified

**File:** `docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_lock_design_v0.2_2026-09-02.md`, section 3.

The design requires the output target to be opened with:

```text
O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW | O_CLOEXEC
```

but then requires **same-FD** `lseek` + read-back of the just-written canonical request bytes. An `O_WRONLY` descriptor is not readable, so the stated success path cannot be implemented as written.

Also, success requires the final file mode to be exactly read-only, while fixture requirements mention chmod failure, but the production primitive is not frozen. The mode supplied to `open(..., mode=0444)` is subject to the process umask and therefore does not by itself prove exact final mode `0444`.

**Required remediation:**

- if same-FD read-back remains required, freeze target open flags as `O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`;
- freeze an explicit `fchmod(fd, 0o444)` before final mode verification (or an equivalent umask-independent exact-mode primitive);
- verify final type/mode by `fstat(fd)`;
- short write / write / fsync / seek / read-back / `fchmod` / final `fstat` / close failures after create must all be `POISONED_NOT_LOCKED` with no cleanup/retry.

A separate read-back FD is also possible, but that would be a materially different authority contract and must be explicitly designed and reviewed; it must not be silently substituted for the current “same FD” promise.

### B2 — `planned_roster` digest is not frozen to the exact existing P5 roster object/hash contract

**Files/contracts:**

- Request-Lock v0.2 section 2;
- frozen P4-v4 run lifecycle;
- existing P5 run-root roster verifier.

The design currently says the tool computes:

```text
roster_sha256 = SHA256(canonical bytes(planned_roster records))
```

That is not sufficiently exact. The existing P5 contract verifies a specific roster object whose digest is over the canonical object containing its exact ordered `entries`, with each entry carrying the fixed path/type/mode/SHA grammar. The final request `run.<backend>.roster_sha256` must be byte-for-byte/hash-for-hash compatible with that existing verifier, not merely “a canonical hash of planned records.”

If the lock tool hashes a differently-shaped list/object or a differently-scoped serialization, the request may pass P4 full-request validation yet be impossible to satisfy at P5.

**Required remediation:**

Freeze the request-lock planned roster as the **exact P5 roster entry grammar and hash algorithm**, including:

- exact row key-set and value grammar;
- exact deterministic sort/order rule;
- exact path set derivation;
- directory mode/SHA semantics;
- regular-file mode/SHA semantics;
- exact canonical serializer;
- final digest exactly equal to the existing P5 definition (equivalent to the P5 verifier’s canonical hash of the exact `entries` object), not a newly invented parallel digest.

Permanent fixtures must prove that the digest inserted into `run.<backend>.roster_sha256` is exactly the digest the existing P5 roster verifier expects for the same planned entries.

### B3 — the design does not close how `preflight.json` gets an exact pre-execution SHA without circularity

The existing P5 final run-root roster includes `preflight.json` as a regular-file roster entry whose actual bytes/SHA are verified. Request Lock v0.2 occurs **before** real P4 preflight execution, but it claims to freeze the final executable `roster_sha256` from `planned_roster` records.

The design does not yet define where the exact bytes/SHA of `preflight.json` come from before execution, nor prove that those bytes are a deterministic pure function of already-frozen inputs. In particular, the contract must exclude circular dependence on:

- the final request’s own `roster_sha256`;
- execution result/outcome fields;
- runtime timestamps/random IDs;
- actual filesystem mutation outcomes;
- post-execution evidence identities.

Without this, the lock cannot truthfully claim to know the final P5-compatible roster digest before the preflight has run.

**Required remediation:** choose and freeze one coherent lifecycle:

1. **Precomputable-final-roster path:** define the exact canonical `preflight.json` schema and byte derivation entirely from pre-execution frozen inputs, prove it is non-circular, and bind its exact SHA into the exact P5 roster entries before request locking; or
2. **Two-stage roster lifecycle:** if `preflight.json` is inherently execution-derived, do not call the pre-execution digest the final `roster_sha256`; introduce a separately reviewed planned-roster commitment and keep the actual final P5 roster digest for a later immutable record/refreeze Gate. Any such redesign must remain consistent with the already-frozen `run`/P5 schemas and therefore requires explicit contract review rather than an implementation shortcut.

The current design is between these two models and is not implementable as a final immutable execution-request lock yet.

## Provenance note

The design should distinguish the P5 Evidence Git Authority implementation commit `3e3a853c61dd32888932041e6afbfac466818e09` from its ChatGPT static closure review `507a343154cb14239f25480927827a5fb05c9c30`. The latter explicitly keeps real future P4 evidence authority unpopulated until a separately reviewed record/refreeze closure. Static verifier capability must not be described as already-populated real evidence authority.

This is not the primary blocker for this design, but the v0.3 prerequisite wording should be corrected so future reviewers can audit the exact closure chain.

## Required v0.3 closure

A re-review can stay strictly within Request-Lock design and should freeze:

1. an executable same-FD output state machine (`O_RDWR` or explicitly redesigned safe read-back), exact `fchmod`/`fstat` mode semantics, and poison behavior for every post-create operation;
2. the exact existing P5 roster entry object/ordering/hash algorithm, with no parallel roster digest definition;
3. exact `preflight.json` pre-execution byte/SHA derivation with non-circular proof, **or** an explicitly redesigned two-stage roster lifecycle consistent with frozen P4/P5 contracts;
4. corrected P5 evidence-authority provenance wording;
5. unchanged execution prohibitions and separate future exact-request CPU-preflight Gate.

No implementation or real request generation is approved by this review.
