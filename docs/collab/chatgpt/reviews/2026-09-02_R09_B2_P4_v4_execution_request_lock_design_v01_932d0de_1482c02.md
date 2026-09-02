# ChatGPT Independent Review — R09-B2 P4-v4 Execution-Request Lock design v0.1

- Review date: 2026-09-02
- Design SHA: `932d0debec5935cf88d9e90f2f20b7da054ec546`
- Formal request / ledger HEAD: `1482c02e0f0e334f4c45b2b82b31a28487fcdf5f`
- Prior ChatGPT anchor: `6910a72bd38780f3e584a7278c9568564c9517f2`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

Reviewed only the new static `G0-R09-B2-P4-V4-EXECUTION-REQUEST-LOCK` design. Existing Execution Request nested/full static validation and P4-v4 materialization static tooling remain closed and are not reopened. No real request lock generation, P4 preflight/materialization/staging, candidate creation, P4 record/refreeze/evidence publication, P5 export/compose, GPU, model/data/checkpoint I/O, B2-T, or Local Memory training is authorized.

The overall sequencing is correct: a canonical immutable request must be frozen before a later exact-SHA CPU execution Gate, and freezing that request must not itself authorize execution.

## Blocking findings

### B1 — `lock_spec` is called verifier-owned but its authority mechanism is not frozen

The design says the input is a verifier-owned exact-key-set `lock_spec`, but it does not define how that property is established. There is no exact `lock_spec` schema/version, no byte-level input contract, no verifier-owned expected SHA/commit/path/constant, and no explicit rule that the spec itself is read once as canonical bytes and bound before any request construction.

This matters because the values that are not independently fixed by the already-closed request validators — especially future run roots, candidate root, attempt id, run tokens, and roster SHA values — would otherwise still be chosen by the caller and merely made immutable by the lock tool. `load_execution_request(raw)` can prove schema/cross-bindings, but it cannot turn caller-selected future execution values into verifier-owned authority.

**Required remediation:** freeze one exact authority route for the spec. For example, define a canonical `lock_spec_v1` byte schema and require a verifier-owned expected SHA (and, if source-controlled, exact commit/blob/current-byte binding), read by single-fd/no-follow semantics. Alternatively embed the exact future values in verifier-owned code/constants. In either case, caller mutable dictionaries/CLI values may not supply semantic request authority.

### B2 — final `roster_sha256` authority is still missing

The closed `run` v0.2 contract explicitly states that its static `roster_sha256` is non-executable and only format/distinctness-checked. Before real preflight, a later Gate must deterministically compute each backend's **final** roster digest from an exact planned roster grammar and generate a new immutable execution request.

The current Lock v0.1 design instead lets `lock_spec` contain `roster SHA` values directly. It does not define the planned roster grammar, the exact ordered roster inputs, or an independent deterministic recomputation whose digest must equal `run.<backend>.roster_sha256`. Therefore the tool could freeze a well-formed but arbitrary digest and call the request final.

**Required remediation:** make the lock tool compute or independently recompute both final roster SHA values from a frozen deterministic roster grammar/input set; the spec may name the inputs but must not self-authorize the digest. Freeze the candidate-to-final-run equality at the same point. A mismatch must fail before output-file creation.

### B3 — output lock target and partial-write state are under-specified

The lock tool introduces the only new real side effect in this Gate: creating the request file. The design currently allows a caller-provided new target and says fixtures cover partial writes, but it does not freeze:

1. a verifier-owned allowed output namespace / parent authority, so the caller still controls where the tool writes;
2. the exact file creation primitive/FD verification contract beyond the phrase `nofollow create-new`;
3. what a short-write/fsync/read-back failure means when a partial target already exists, while cleanup/rename/retry/overwrite are forbidden.

A partially written file must never be observationally equivalent to `FROZEN_NOT_EXECUTABLE`.

**Required remediation:** freeze the output namespace/target authority (or a separately reviewed exact target), use create-new nofollow single-FD semantics, and define an explicit terminal `POISONED_NOT_LOCKED`/equivalent state for any post-create failure. Success should require full-byte write plus FD-based verification/read-back of exact canonical bytes/SHA (and any required durability check). Partial targets must be permanently non-authoritative and execution Gate inputs must require the exact successful raw/SHA, never mere file existence.

## Provenance note

The design names `3e3a853` as "P5 evidence Git authority". That is the implementation commit. The actual ChatGPT static closure is `507a343154cb14239f25480927827a5fb05c9c30`, and that closure explicitly leaves real future P4-v4 evidence authority unpopulated until a separate record/refreeze Gate. Do not treat the existence of the static verifier implementation as authority for future real evidence values. If this prerequisite remains listed, bind implementation and closure roles distinctly.

## What is already acceptable

- Canonical `r09_b2_p4_v4_execution_request_v1` followed by existing `load_execution_request(raw)` revalidation is the right final semantic admission step.
- The request lock must remain `FROZEN_NOT_EXECUTABLE` and must not call `_admit_execution_request`, materialization, P4 CLI execution, P5 entries, torch, GPU, or model/data/checkpoint paths.
- Future roots staying nonexistent during lock generation is correct.
- A later exact-request CPU execution Gate must separately bind raw/SHA, exact command, source revision, output roots/resource envelope, and stop conditions.

## Gate decision

`REQUEST_CHANGES`

Do not implement v0.1 yet. Submit a v0.2 design that closes B1-B3. No real request generation or execution is authorized by this review.
