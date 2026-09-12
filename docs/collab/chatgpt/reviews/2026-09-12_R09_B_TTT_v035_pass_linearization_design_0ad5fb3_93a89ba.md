# ChatGPT Review — Authority Root PASS Linearization Design v0.8

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-PASS-LINEARIZATION-DESIGN`

## Exact formal pair

- root design SHA: `0ad5fb3379456f485fd861595e3db4ab62c3555f`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.8.md`

The formal root resolves to `docs: refine authority pass lifecycle`. Its formal tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

This is a fresh incremental design review against:

- approved v0.3–v0.6 authority-root design contracts;
- ChatGPT v0.7 exact-pair review `c396ad298057810c04016e9d6116b7f9e5ac16d4 / 93a89ba...`;
- exact v0.8 text and its stated supersession/retained contracts.

The architectural direction remains correct: public filesystem pathname state is not acceptance authority, `AcceptedPass` is private to the authority transaction, and the public ABI stays the v0.6 `PublicationWitness` return. v0.8 fully closes the previous return/lifetime ambiguity. The remaining blockers concern whether the proposed state transition and crash/ref semantics are mechanically implementable without recreating split-brain.

## Prior blocker closure status

1. **v0.7 HIGH-1 (public ABI / capability lifetime): CLOSED.** v0.8 explicitly retains the v0.6 `publish_candidate(...) -> PublicationWitness` ABI, keeps `AcceptedPass` private, and consumes it before return. No externally live capability window remains.
2. **v0.7 HIGH-2 (fallible issuance after `committed=True`): PARTIALLY CLOSED.** v0.8 pre-allocates/binds `AcceptedPass` and forbids I/O/allocation/validation during the final transition, but the transition is still described as several independent in-memory writes plus a second `consume()` state write; see HIGH-1 below.
3. **v0.7 HIGH-3 (crash/closure): PARTIALLY CLOSED.** v0.8 chooses permanent fail-stop, but the inherited guard transition and the issuance/consume crash windows are not modeled consistently or detectably enough; see HIGH-2 below.

## Current blockers

### HIGH-1 — the proposed “total transition” is not frozen as one indivisible authority state change, so async `BaseException` / process interruption can still split `AcceptedPass`, `EvidenceCommit.committed`, and preserve-refs selection

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.8.md` §2

v0.8 says the final transition is non-throwing because it performs only writes to existing enum/boolean fields, and then performs an immediate internal `consume()` as another total state flip:

`prepared AcceptedPass -> issued AcceptedPass + committed EvidenceCommit + preserve-refs branch -> consumed AcceptedPass`.

That removes allocation and validation failures, but it does not make the semantic transition indivisible. In the approved implementation language/runtime, multiple attribute/enum/boolean writes remain distinct execution steps. `KeyboardInterrupt`, signal delivery, cancellation, or process termination can occur between those writes even when there is no callback or I/O.

A reachable split therefore remains unless the implementation invents its own stronger primitive:

- `AcceptedPass.state` can become `issued` while `EvidenceCommit.committed` or preserve-refs selection is still old;
- `EvidenceCommit.committed=True` can become visible before the authoritative `AcceptedPass` state is consumed;
- process interruption can occur between the stated `total_transition` and the separately specified `consume()`.

The stated invariant `consumed AcceptedPass <=> issued AcceptedPass <=> committed EvidenceCommit <=> preserve-refs branch selected` is not mechanically implied by “no I/O / no allocation / no validation.”

**Exact acceptance:** freeze one canonical authority state cell / immutable prebuilt state object / equivalent single semantic commit primitive such that one state change is the sole source of truth for all of: accepted-pass issued/consumed, `EvidenceCommit.committed`, rollback disabled, preserve-refs branch selected, and witness-return eligibility. All other properties must be derived from that one authority state rather than independently mutated. If a separate `consume()` state remains, it must not affect rollback/ref/acceptance semantics and all crash/BaseException points between issue and consume must be explicitly classified. CPU/static tests must inject `BaseException` at every implementation-visible boundary of the transition and prove no partially committed combination is representable.

### HIGH-2 — v0.8 crash table contradicts the inherited guard-transition ordering and omits the durable “guard transitioned, no AcceptedPass issued” crash state

**Location:** `...authority_root_pass_linearization_design_v0.8.md` §§2–3, with v0.7 retained guard-transition contract

v0.8 supersedes v0.7 only for `AcceptedPass` external return/lifecycle. Therefore v0.7's frozen ordering still applies unless explicitly replaced:

`sealed FD verification -> exact refs -> authority-owned guard transition -> committed -> AcceptedPass issuance`.

v0.8 simultaneously states:

- all fallible work finishes before the non-I/O `total_transition`;
- the pre-issuance crash row has `guard可见`;
- the issuance→consume window is “理论不可观察”.

These cannot all hold. The guard transition is filesystem I/O/fallible, so under the retained ordering it must occur **before** the non-I/O issuance transition. After a successful guard transition and before `total_transition`, the guard is no longer visible. A process can terminate in exactly that interval. The resulting durable state can contain candidate refs and final evidence with no live `AcceptedPass`, while the design table claims the pre-issuance state has a visible guard.

Likewise, issuance→consume is not literally unobservable under process loss: process termination can happen between any two runtime instructions even if no callback/I/O/cancellation API is invoked.

v0.8 does choose permanent fail-stop after successful consumption, which is a valid policy, but it does not freeze the exact restart/detection rule for these ambiguous pre-return windows. “Process loss is fail-stop” is not enough unless a new process can deterministically classify the durable state and prohibit retry/close/train.

**Exact acceptance:** explicitly replace the inherited guard-transition ordering and enumerate every durable crash window, including at minimum:

1. before guard transition;
2. after guard transition but before the single authority-state commit;
3. after authority-state commit but before any internal bookkeeping/consume/return;
4. after return.

For each row freeze exact durable refs/evidence/guard state, whether acceptance exists, whether rollback is legal, and the next-process detection predicate. If any non-live process cannot distinguish the state, require deterministic fail-stop on restart (for example, exact fixed-ref/evidence/guard combinations) and route only to the named manual recovery Gate. Do not call issuance→consume “unobservable” unless it is collapsed into the single semantic authority-state transition from HIGH-1.

### HIGH-3 — local/remote “exact-candidate witness” is still only an observation before the in-memory issuance transition; concurrent ref drift can make `AcceptedPass` authoritative while the actual refs are no longer exact candidate

**Location:** `...authority_root_pass_linearization_design_v0.8.md` §§1–2

v0.8 pre-binds `AcceptedPass` to a local/remote exact-candidate ref witness and requires exact refs before `total_transition`. But the final transition is intentionally non-I/O. Therefore the actual Git refs must be observed **before** the authority-state flip.

Nothing in v0.8 serializes or freezes either ref namespace between that last observation and the in-memory commit. Exact-old CAS proves this activation created/owned the refs earlier; it does not prevent another actor from changing or deleting a ref after the final observation.

A reachable sequence remains:

1. authority freshly observes local and remote refs == candidate;
2. foreign actor changes/deletes one endpoint;
3. authority executes the non-I/O `total_transition` and consumes `AcceptedPass`;
4. rollback is disabled and the exact `PublicationWitness` becomes returnable even though the durable ref state is no longer the asserted exact candidate pair.

That violates v0.8's own binding/invariant and the retained authority-root contract.

**Exact acceptance:** choose and freeze one of two semantics:

- **strong current-ref invariant:** provide a mechanical coordination/ownership rule that makes the final exact-ref witness valid through the semantic commit point, and test adversarial local/remote drift exactly between the last observation and authority-state transition; or
- **observation-only witness:** explicitly weaken `AcceptedPass` so it certifies only the last exact observation, classify any post-observation ref drift as external corruption/fail-stop rather than accepted exact refs, and remove claims that successful authority commit implies the current durable refs are still exact candidate.

The next implementation must not invent which interpretation was intended.

## Non-blocking observations

- Keeping the public v0.6 return ABI and consuming `AcceptedPass` internally is the correct resolution of v0.7 HIGH-1.
- Preallocation before commit is the correct direction; the remaining requirement is to collapse semantic truth into one authoritative state transition.
- Permanent fail-stop after process loss is acceptable if restart detection and every crash window are frozen exactly.
- Demoting `verify_evidence_path()` to content/audit observation remains the right architectural choice.
- Evidence-v1 bytes ABI, four-file CPU/static scope, exact raw-byte/OID binding and exact-old CAS rules can remain unchanged.

## Blocker summary

- design/contract blockers: `3 HIGH`
- total blockers: `3 HIGH`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_pass_linearization_design_v0.8.md:24)`

This verdict binds only the exact formal pair `0ad5fb3379456f485fd861595e3db4ab62c3555f / 93a89ba61306d840a008813f62f26a34d54850f4`.

No implementation token is granted. Real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, and LIBERO4IN1 remain prohibited.
