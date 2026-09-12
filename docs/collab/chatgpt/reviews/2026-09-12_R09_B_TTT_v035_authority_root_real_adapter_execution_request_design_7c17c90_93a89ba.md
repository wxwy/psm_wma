# ChatGPT Review — Authority Root Real Adapter / Execution Request Design v0.1

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-EXECUTION-REQUEST-DESIGN`

## Exact formal pair

- root design SHA: `7c17c90a3b25182436fef89fbe063de9fcf1d67e`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh design review. The immediately preceding synthetic authority-root implementation was closed at root `0b18620f84959bf25379f3c227b796edc1097efd` with the same child/Gitlink. MM/Kimi state is coordination information only and is not inherited as ChatGPT's conclusion.

The formal tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. That child commit is reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed against:

- approved authority-root materialization/binding design v0.1 and ABI v0.2;
- approved authority-root CPU/static implementation design v0.1/v0.2 and the closed synthetic implementation;
- the actual existing injected `AuthorityGitTransaction`/publication state machine and the collection consumer contract;
- the new real-adapter/execution-request design v0.1;
- the claimed exact future selection/config bytes, their SHA-256, and their Git native blob identities.

The proposed two-stage route is directionally correct: real adapter/CLI CPU-static closure first, then a separately reviewed exact execution request before any real materialization. The two-file implementation allowlist is also consistent with reusing the already-closed production algorithm rather than reimplementing schema/tree/ref/rollback logic.

## Current blockers

### HIGH-1 — the two frozen Git native blob OIDs do not match the exact bytes being frozen

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.1.md:38,47`

**Root cause**

The design freezes exact selection/config raw bytes and gives correct byte lengths and SHA-256 values, but both claimed Git native blob OIDs are incorrect for those bytes.

Independent recomputation with the native Git blob formula `SHA1("blob <len>\0" + raw)` and with `git hash-object` gives:

- selection: length `516`, SHA-256 `8fe4585f366cb69ad9181e30c25b5f4e99040c83d8ffe66426897bfa9d331edd`, **Git blob OID `9f03614b691bca3ba834e16e65ee983fe95af74c`**;
- config: length `508`, SHA-256 `43b3b77b5934107c54b8bee157b46d07cb17b85ca89305ad6fb7405237e42d1d`, **Git blob OID `89b12047c50a3a924521200d1897b13bf30aacfe`**.

The design instead states `6c7d53c1...` and `d1b80b1c...`.

**Violated frozen contract**

Materialization/binding v0.1 §2-§4 requires raw bytes, raw SHA-256, native Git blob OID and committed tree/blob lookup to agree exactly. A wrong frozen OID makes the future execution request internally inconsistent before implementation even begins.

**Exact acceptance**

1. replace both native blob OIDs with the values recomputed from the exact no-trailing-newline bytes above;
2. retain the currently correct byte lengths and SHA-256 values;
3. require the real-adapter CPU/static tests to derive the native OID from the exact bytes and cross-check it with `git hash-object` in the temporary repository instead of trusting a copied constant.

### HIGH-2 — remote expected-zero / rollback CAS is not frozen to a safe, implementable Git primitive and conflicts with the blanket `force` prohibition

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.1.md:25-27`

**Root cause**

The design simultaneously says:

- remote ref operations must implement exact expected-zero / expected-candidate CAS semantics;
- `force` is prohibited;
- ordinary push overwrite/delete-recreate is prohibited.

For a real Git remote, an ordinary create push does **not** prove expected-zero under concurrency: if a concurrent foreign ref appears and happens to be an ancestor of the candidate, an ordinary push can fast-forward it and incorrectly succeed. The practical Git transport primitive for exact remote compare-and-swap is an explicit expected-old-value lease (for example `--force-with-lease=<ref>:<expected>` or an equally strict old-OID-checked mechanism). Rollback deletion likewise needs an exact candidate→absent expected-old-value operation.

The current wording does not distinguish prohibited unconditional force from the conditional lease-CAS needed to satisfy the already-frozen publication state machine. An implementation could therefore either violate the “no force” wording or fall back to unsafe ordinary push semantics.

**Violated frozen contract**

The closed synthetic implementation and materialization/binding design require remote expected-absent→candidate CAS, ownership-aware exact-candidate→absent rollback, preservation of foreign refs, and no force overwrite/retry.

**Exact acceptance**

1. explicitly prohibit unconditional `--force`, wildcard/general force, ordinary overwrite push, and delete/recreate;
2. explicitly permit only an exact-old-value remote CAS primitive whose semantics are frozen in the design, e.g. a per-ref `--force-with-lease=<fixed-ref>:<expected-old>` form or an equivalent mechanism that the adapter proves is atomic for the target remote;
3. freeze expected values: creation requires **absent**; rollback deletion requires **exact candidate revision**;
4. require fresh remote observation after each operation and preserve the existing `ROLLBACK_INCOMPLETE` behavior if absence/ownership cannot be proved;
5. add deterministic temporary-bare-remote tests where a concurrent foreign ref is an ancestor/fast-forwardable commit, proving ordinary push would be unsafe and the chosen CAS rejects it without deleting/overwriting the foreign ref.

### HIGH-3 — the claimed evidence writer has no frozen transaction evidence contract sufficient for the later three-party binding

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.1.md:55-67`

**Root cause**

The design says the current production lacks an evidence writer and the new adapter/CLI stage will provide one, but its acceptance only says evidence contains “the seven-key binding and necessary identity.” That is insufficiently defined for the real publication transaction.

The inherited materialization/binding contract requires the later review to reference, at minimum, the exact materialization formal root, child/Gitlink, candidate revision, verifier PASS, fixed-ref exact CAS result, tool/interpreter identities, and failure/rollback outcome. The seven-key tuple plus generic “identity” does not by itself prove:

- that both local and remote refs were freshly absent before publication;
- which endpoint CAS operations succeeded in this activation;
- that both refs were freshly re-observed at the exact candidate after CAS;
- that committed binding was reverified after publication;
- or, on failure, whether rollback was complete versus `ROLLBACK_INCOMPLETE` and which foreign/unreadable endpoint was preserved.

Without a frozen status/phase schema and atomic retention rule, the implementation review cannot distinguish a strong evidence writer from one that records only final tuple values, and the subsequent binding review would have to reconstruct transaction history from transient logs/current state.

**Violated frozen contract**

Materialization/binding v0.1 §4-§5 requires reviewable exact CAS/verifier evidence and fail-stop rollback semantics; the project review discipline separates production correctness from direct Evidence completeness.

**Exact acceptance**

Freeze a minimal exact evidence contract in this design before implementation. It need not include source bytes/paths/secrets, but it must mechanically distinguish PASS, ordinary pre/post-mutation FAIL, and `ROLLBACK_INCOMPLETE`, and must bind at least:

- execution formal root + child/Gitlink;
- exact seven-key authority mapping;
- candidate revision and verifier PASS/result identity;
- adapter/authority-module/interpreter/Git executable identities, cwd, sanitized-env identity, full argv identity, commit metadata policy, fixed ref and credential-free remote identity;
- fresh local/remote pre-publication observations;
- per-endpoint same-activation creation ownership/CAS results;
- fresh local/remote post-CAS observations and committed-binding reverify result;
- rollback attempts, conditional-delete results, final fresh endpoint observations, and final rollback status;
- stable failure code/phase for FAIL records;
- canonical serialization + digest and an atomic writer rule: normal return means one complete accepted record; writer failure must not leave a stale visible PASS.

CPU/static tests should directly verify the record for success, pre-mutation failure, one-endpoint conflict, foreign-ref drift, observation error, compare-delete failure, and `ROLLBACK_INCOMPLETE` using only temporary local/bare remotes.

## Non-blocking observations

- The exact selection/config byte lengths and SHA-256 values are internally consistent; only the native blob OIDs are wrong.
- The design correctly keeps the real source root out of the authority JSON and leaves it to the later controlled collection execution request.
- Re-observing Python/Git/tool identities in the later exact execution request rather than trusting design-time observations is correct.
- Keeping the candidate commit detached from `V2` and making the future execution formal root its unique parent is consistent with the inherited non-circular authority contract.

## Blocker summary

- production/design blockers: `3 HIGH`
- Evidence-only blockers: `0` (HIGH-3 is a design blocker because the implementation stage explicitly includes the evidence writer)
- total blockers: `3`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.1.md:38)`

This verdict binds only the exact formal pair `7c17c90a3b25182436fef89fbe063de9fcf1d67e` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation stays in the same real-adapter/execution-request design Gate. This verdict does **not** authorize implementation yet, and it does not authorize real selection/config files, candidate/ref creation, origin/remote mutation, source read, collection/receipt/source-evidence/publication, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
