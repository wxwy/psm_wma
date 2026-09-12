# ChatGPT Review — Authority Root Real Adapter / Execution Request Design v0.3

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

## Exact formal pair

- root design SHA: `c4133389f856f5ab7a5ad01923f71c0c3892ce09`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `dd0ecdf19e3413be4f8dad5e7b069e106f88e8ad`; the child is unchanged.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is reachable in `wxwy/cosmos-framework`.

The latest delivery bookkeeping for this exact pair reports that MM/Kimi requests were delivered but no exact-pair final was yet present at that snapshot. Their eventual state is coordination evidence only and is not inherited as ChatGPT's conclusion.

## Review basis

Reviewed against:

- approved materialization/binding v0.1 + ABI v0.2;
- approved authority-root CPU/static implementation design v0.1/v0.2 and the closed synthetic implementation;
- real-adapter/execution-request design v0.1 and v0.2;
- prior ChatGPT review for `dd0ecdf... / 93a89ba...`, which left two HIGH blockers;
- current production `publish_candidate()` / private rollback state machine;
- the complete v0.3 finalizer/evidence ABI, chronology table and commit-point contract.

## Prior blocker closure

The v0.3 remediation materially improves both previous blockers:

1. **Prior HIGH — evidence failure could not re-enter the authority-owned rollback transaction: substantially closed in architecture.** The implementation allowlist is expanded to include the authority module and direct test. `publish_candidate(..., finalizer=...)` keeps finalization inside the same `try/except`, so adapter code need not import or duplicate private rollback logic. The opaque witness / sealed commit direction is appropriate.
2. **Prior HIGH — evidence v1 lacked exact nested ABI / chronology: substantially closed in structure.** v0.3 freezes nested key sets, types, observation tagged-union semantics, candidate partial states, phase names, null/false conventions and a first-failure table.

However, the current v0.3 text still contains two blocking internal inconsistencies, so the Gate cannot yet authorize implementation.

## Current blockers

### HIGH-1 — evidence acceptance has two incompatible commit points, making post-guard-delete failures ambiguous between rollback and preserved PASS

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.3.md` §2 and §5 (publication-finalization seam / evidence commit point)

**Root cause**

v0.3 defines two different linearization points for the same transaction:

- §2 says the finalizer's normal return declares that evidence reached the accepted commit point, and says **any finalizer exception** is caught inside `publish_candidate()` and enters ownership-aware ref rollback. It also requires a sealed `EvidenceCommit` to be returned to the authority module.
- §5 says successful **guard deletion itself** is the accepted commit point; after guard deletion the candidate refs must be retained and any later reporting-path failure must **not** trigger rollback.

But the §5 writer sequence still performs fallible steps *after* guard deletion and *before* `EvidenceCommit` / normal callback return:

1. delete guard;
2. fsync directory;
3. single-FD re-read / schema+digest verification;
4. only after the final step succeeds, produce sealed `EvidenceCommit` and allow finalizer return.

Therefore a directory-fsync error or final re-read error after guard deletion is simultaneously:

- a finalizer exception under §2, which requires authority rollback; and
- a post-commit error under §5, which forbids rollback and requires refs to remain at the exact candidate.

That ambiguity can produce the exact split-brain this design is intended to prevent: a final PASS may be verifier-visible while refs are rolled back, or refs may remain published while the authority module has no accepted `EvidenceCommit` capability.

**Violated frozen contract**

The inherited transaction contract requires one fail-closed ownership chronology: ordinary FAIL only when ref rollback is complete and no accepted PASS is visible; once PASS is accepted, the exact candidate refs must remain authoritative and must not be rolled back by later reporting failures.

**Exact acceptance**

Freeze exactly one transaction linearization point and make all three layers agree: writer visibility, `EvidenceCommit` capability, and `publish_candidate()` rollback behavior.

One acceptable shape is:

- **pre-commit:** guard remains present; every fallible write/fsync/read/validation step that may still cause authority rollback occurs before the linearization point;
- **commit:** one explicitly named operation is the sole PASS linearization point; at that exact operation the record becomes acceptable and the authority module can deterministically treat publication as committed;
- **post-commit:** no exception from reporting/durability diagnostics is allowed to flow back into the rollback path. Any such condition must have a separately frozen post-commit diagnostic/fail-stop treatment that preserves the exact candidate refs.

Alternatively, if normal finalizer return / sealed `EvidenceCommit` is the linearization point, then the guard must continue to make the final file non-acceptable until all fallible fsync/re-read checks are complete; guard removal must be the final non-failing/committing transition or be coupled to the capability in a way that cannot expose PASS before the callback can return successfully.

CPU/static tests must inject failures at every step immediately before and immediately after the chosen commit point and directly prove the invariant:

`accepted PASS visible  <=>  transaction committed  <=>  exact candidate refs preserved`

with no branch that both exposes accepted PASS and enters authority rollback.

### HIGH-2 — the “first-failure chronology” still permits impossible rollback records and loses the primary failure phase

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.3.md` §4 (`rollback` terminal row)

**Root cause**

The table claims an independent verifier can mechanically replay the **first-failure chronology**, but the terminal `rollback` row allows:

- `authority = A or N`;
- `candidate = V/P/empty according to origin`;
- partially concrete / null pre-publication fields;
- `failure.phase = rollback`.

Those states are not reachable under the already-frozen publication algorithm.

Ownership-aware rollback is only entered after a mutation-capable publication path has been reached. Under the current state machine, any rollback that can itself fail occurs only after request validation, candidate preparation, independent verification and creation of the exact authority binding. Therefore `rollback.required=true` cannot legitimately coexist with an all-null authority or an unverified/empty candidate. At minimum the record must already bind the concrete seven-key authority and verified candidate; for post-local-create rollback it must also bind the concrete successful pre-publication absent observations and the actual ownership bits reached before rollback.

The row also overwrites `failure.phase` with `rollback`. But rollback is a **secondary terminal failure**, not the first failure that caused rollback. Examples are `remote_cas`, `post_publication`, `binding_reverify`, or `evidence_write` followed by rollback failure. Replacing the original phase with `rollback` means the verifier can no longer reconstruct the advertised “first-failure chronology.”

This leaves the v0.3 validator contract permissive enough to accept fabricated `ROLLBACK_INCOMPLETE` records that omit authority/candidate provenance or erase the actual primary failure.

**Violated frozen contract**

The previous ChatGPT acceptance required an ordered first-failure table that mechanically determines every section's concrete/null/false shape for PASS, ordinary rolled-back FAIL and `ROLLBACK_INCOMPLETE`.

**Exact acceptance**

1. Make `rollback.required=true` carry invariants implied by the actual publication state machine. In particular, any rollback terminal record must have concrete verified authority/candidate provenance and must preserve the exact already-reached pre/publication ownership facts.
2. Do not permit `authority=N`, `candidate=P/empty`, or an unconstrained pre-publication shape for a rollback-required record unless the production algorithm is explicitly changed to make such a path reachable (which this design does not request).
3. Preserve the primary failure phase. Either:
   - keep `failure.phase/code` as the original first failure and let `rollback.complete=false` plus rollback observations encode the secondary failure; or
   - explicitly add separately named primary and rollback failure fields with exact key/type rules.
   A single `phase=rollback` terminal value cannot satisfy a table advertised as first-failure chronology.
4. Split the generic rollback row by origin phase, or freeze equivalent conditional invariants, so the independent validator rejects impossible combinations of authority/candidate/pre/post/publication/rollback fields.
5. Add direct validator negatives for at least:
   - `ROLLBACK_INCOMPLETE` with null authority;
   - unverified/empty candidate with rollback required;
   - lost/replaced primary phase;
   - ownership/delete bits impossible for the originating phase;
   - null pre-observations after a successful local create.

## Non-blocking observations

- The v0.2 corrected raw-byte SHA/native Git OID binding and exact-old remote lease-CAS remain binding and are not regressed by v0.3.
- Expanding the implementation allowlist to the authority module/test plus adapter/test is justified by the need to keep rollback authority inside the already-reviewed production state machine.
- The tagged observation object and the concrete candidate states are a meaningful improvement over v0.2.
- The two-stage route remains appropriate: CPU/static real-adapter implementation closure first, then a separately reviewed exact real materialization execution request.

## Blocker summary

- production/design blockers: `2 HIGH`
- Evidence-only blockers: `0`
- total blockers: `2`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.3.md:101)`

This verdict binds only the exact formal pair `c4133389f856f5ab7a5ad01923f71c0c3892ce09` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same real-adapter/execution-request design Gate. This verdict does **not** authorize implementation yet and does not authorize real selection/config JSON creation, candidate/ref/origin mutation, source read, collection/receipt/source-evidence/publication, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
