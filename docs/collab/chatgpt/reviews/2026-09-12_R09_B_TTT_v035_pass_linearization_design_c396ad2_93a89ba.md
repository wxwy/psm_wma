# ChatGPT Review — Authority Root PASS Linearization Design v0.7

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`

## Exact formal pair

- root design SHA: `c396ad298057810c04016e9d6116b7f9e5ac16d4`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.7.md`

The formal root is reachable (`docs: design authority pass capability`). Its formal tree was independently checked and `cosmos-framework` remains mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

This is a fresh design review. It does not reuse the previous implementation verdict as a design verdict. The review is incremental against:

- the approved v0.3–v0.6 authority-root design chain;
- the latest implementation review `1440fd3391d46ef383d60387da8d7e7aa8238d5f / 93a89ba...`, which required returning to a design Gate rather than adding more implicit pathname coordination;
- the exact v0.7 text and its claimed supersession/retained contracts.

The central design direction is sound: filesystem pathname state is demoted from acceptance authority to observation/audit, and the intended acceptance authority moves back into an authority-owned opaque capability. That is the correct architectural direction. The current v0.7 contract is not yet exact enough to implement safely, however.

## Current blockers

### HIGH-1 — the `AcceptedPass` return/lifetime contract is internally inconsistent with the retained v0.6 API

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.7.md:23-35`

v0.7 says all of the following:

1. only `AcceptedPass` is authoritative acceptance;
2. callers that execute/close the Gate must consume the `AcceptedPass` directly returned by the same transaction;
3. `AcceptedPass` is activation-bound and becomes invalid when the activation ends;
4. v0.7 only supersedes the old pathname-based linearization statements while retaining the rest of the v0.3-v0.6 contract chain.

But v0.6 explicitly froze normal `publish_candidate(...)` completion to return the exact `PublicationWitness`, with finalizer return values ignored. v0.7 does not explicitly supersede or replace that return ABI and gives no function signature or result object showing how `AcceptedPass` leaves the authority transaction.

The activation lifetime is also undefined at the only point that matters. Under the inherited finalizer activation model, activation ends when the finalizer invocation/authority dispatch ends. If the capability becomes invalid at activation end, a capability that is only useful after being returned can be invalid by the time the caller receives it. Conversely, if activation is extended beyond return, the design does not define who owns that epoch, when it ends, what exact consume operation ends it, or how replay is rejected after successful downstream use.

This is not an implementation detail: the next Gate cannot know whether `publish_candidate` returns `PublicationWitness`, `AcceptedPass`, a pair/result object, or keeps `AcceptedPass` internal and calls a closure consumer before return.

**Exact acceptance:** explicitly supersede the v0.6 return contract and freeze the public authority ABI and state machine. At minimum define:

- the exact function signature/result type of `publish_candidate` (or a replacement authority entrypoint);
- whether `PublicationWitness` remains externally returned and, if so, how it relates to `AcceptedPass`;
- the exact `AcceptedPass` states (`prepared/issued/consumed/expired` or equivalent), one-shot consume operation, replay behavior, and identity binding;
- the exact activation lifetime and the event that invalidates it;
- proof that the caller has a valid capability during the complete allowed consume window and that no valid capability exists outside that window.

### HIGH-2 — `AcceptedPass issuance` is declared the linearization point, but the frozen order permits `committed=True` before capability issuance without freezing issuance as a non-throwing state transition

**Location:** `...execution_request_design_v0.7.md:33-39`

The frozen order is stated as:

`sealed FD verification -> exact refs -> guard transition -> mark EvidenceCommit.committed -> issue AcceptedPass -> preserve refs`

while another bullet states that the linearization point is `AcceptedPass issuance`, and that `committed=True` plus ref preservation must be in the same non-rollback authority dispatch.

That ordering leaves the exact split-brain class the preceding designs were built to eliminate. If issuing `AcceptedPass` involves object allocation, construction, field binding, validation, or any other operation that can raise after `EvidenceCommit.committed=True`, the system can reach:

- commit marked committed;
- guard transition already performed;
- no authoritative `AcceptedPass` was issued;
- rollback forbidden or semantically ambiguous.

The requested CPU/static invariant says that without `AcceptedPass`, refs must never be preserved, but the current ordering does not mechanically guarantee that.

**Exact acceptance:** freeze an exact non-throwing issuance protocol. A valid design is to pre-allocate/pre-bind the opaque `AcceptedPass` object while still pre-commit, validate all request/candidate/binding/FD/ref fields there, then make the final authority transition only a total state flip that simultaneously makes the pre-created capability `issued`, marks `EvidenceCommit.committed`, and selects the preserve-refs branch. No allocation, validation, file/ref read, logging, callback, or other fallible operation may occur inside or after that state flip while rollback is still reachable. Equivalent machinery is acceptable if the same invariant is explicit and mechanically testable.

The design must also specify post-issuance exception semantics: every exception after the issuance transition is outside the rollback boundary and preserves refs/capability state.

### HIGH-3 — an in-memory, non-serializable, activation-bound capability is the only acceptance authority, but v0.7 does not define durable closure/crash semantics

**Location:** `...execution_request_design_v0.7.md:23-39`

v0.7 intentionally demotes `verify_evidence_path()` to non-authoritative observation and declares that only `AcceptedPass` proves accepted PASS. At the same time the capability is non-copyable/non-pickle/non-replay and expires with its activation. No durable acceptance receipt, reconstructible authority, or crash-recovery rule is frozen.

This creates an unresolved terminal state after an otherwise successful authority commit:

1. `AcceptedPass` is issued and refs become preserve-only;
2. before the designated consumer completes, the process exits, is cancelled, or a post-commit error prevents the caller from receiving/consuming the capability;
3. durable candidate refs and Evidence-v1 bytes remain;
4. pathname verification is explicitly non-authoritative;
5. the only authoritative capability is gone and cannot be reconstructed.

The next process therefore cannot prove accepted publication and also cannot safely replay the transaction because the fixed refs may already be present. That is an authority/liveness dead end, not merely a logging gap.

**Exact acceptance:** freeze the closure and recovery model. One of the following must be made exact:

- the capability is always consumed inside the same authority call before control returns, and successful consumption creates a fixed durable closure/receipt whose independent authority is defined and can be re-verified later; or
- a specific durable Git/root/receipt state becomes the post-consumption authority, in which case v0.7 must explicitly revise the statement that only the ephemeral capability is authoritative; or
- process loss after issuance is a permanent fail-stop terminal, with exact detection, prohibited retry semantics, and an explicit manual recovery Gate that downstream logic can use.

Whichever option is selected, define crash windows before issuance, after issuance-before-consume, and after consume, and define the exact state of refs/evidence/authority in each window.

## Non-blocking observations

- Demoting pathname verification to content audit is the right design direction and should be retained.
- Explicitly rejecting further implicit sidecar/marker/pathname coordination avoids repeating the previous implementation loop.
- Existing Evidence-v1 bytes ABI, exact raw-byte/OID binding, exact-old CAS semantics, and the four-file CPU/static boundary can remain unchanged once the capability state machine is made exact.
- The next design version should identify every current consumer that previously treated `verify_evidence_path()` success as authorization and prove that the approved implementation allowlist is sufficient to migrate them; if any required consumer lies outside the four-file allowlist, scope must be reopened explicitly rather than changed implicitly.

## Blocker summary

- design/contract blockers: `3 HIGH`
- total blockers: `3 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_real_adapter_execution_request_design_v0.7.md:23)`

This verdict binds only the exact formal pair `c396ad298057810c04016e9d6116b7f9e5ac16d4 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No implementation token is granted. Real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, and LIBERO4IN1 remain prohibited.
