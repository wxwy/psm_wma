# ChatGPT independent review — V27 host-owned continuation CPU/static remediation

Formal pair:
- root: `c4a3b985cfd8a576ab114431f8ee2ae4df6f2681`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_host_boundary.py:42)`

Blockers: `3`
- Design/Authority: `0`
- Production/implementation: `2 HIGH`
- Evidence: `1 MEDIUM`
- Scope/child/runtime: `0`

## Re-lock / target validity

- Latest pre-review `V2` is request/delivery bookkeeping beyond the declared formal implementation root; the technical target remains `c4a3b985cfd8a576ab114431f8ee2ae4df6f2681`.
- `CODEX_INBOX.md` explicitly requests this exact pair for the same fake-host CPU/static Gate.
- Formal root resolves `cosmos-framework` exactly to Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.
- Child `93a89ba61306d840a008813f62f26a34d54850f4` resolves independently in `wxwy/cosmos-framework`.
- Previous reviewed implementation pair was `2b7429f2a1eb6cd50f5c5da15e3691a5128f50c1 / 93a89ba61306d840a008813f62f26a34d54850f4`, verdict `REQUEST_CHANGES(tools/psm_wma/stage1_host_boundary.py:54)`. Root changed, so this is a fresh incremental review.

## Frozen contract used

The approved V27 design and prior implementation review remain the authority. For this fake-host closure, the implementation must model:
- a detached canonical non-reconstructive ReviewRecord covering the complete inherited review authority surface;
- exact Gate/root/child + generation/session/plan/lease/binding + nonce/counter approval;
- a privileged orchestration attestation side distinct from client protocol behavior;
- serialized atomic `PENDING_REVIEW -> APPROVED -> CONSUMING -> TERMINAL` admission before freshness/apply;
- complete record drift rejection, prior-session/prior-generation replay rejection, duplicate/pipelined loser-zero behavior, terminal failure branches, at-most-one apply and exact one-shot success.

Real host/IPC/pre-C/C remains outside this Gate.

## Positive closure from `2b7429f...`

Two of the three prior implementation HIGHs are materially closed:
- exact approval authority: `approve()` now checks the full Gate literal, host-owned root, child/Gitlink and session/binding fields; nonce/counter are checked; attestation minting is moved behind a distinct test-only `FakeStage1OrchestratorV27` harness;
- serialized admission: an `RLock` now serializes approval and `APPROVED -> CONSUMING`, with the state transition performed before freshness/apply; the parallel-resume test provides at-most-one observed apply in the current suite.

The prior free-form ReviewRecord finding is improved but remains open in two independent ways described below.

## HIGH 1 — ReviewRecord category names are frozen, but category schemas are still arbitrary string tuples

Location: `tools/psm_wma/stage1_host_boundary.py:42-48` (`_validate_rows`).

The implementation now defines twelve ordered category names, which is useful progress. However each category is still represented only as `tuple[str, ...]`, and `_validate_rows()` checks only:
- the top-level category names/order;
- that each category has at least one non-empty string.

It does **not** freeze or validate the canonical shape/cardinality of the authority represented by those categories. Examples:
- `consumer_provenance`, `guard_provenance`, and `verifier_provenance` may each be a single arbitrary string rather than the frozen provider/module/path/source-blob/callable/ABI/transport identity surface;
- `contract_c01_c15` may contain one arbitrary string rather than the C01--C15 literal set;
- `freshness_domain` may contain one string rather than the nine-entry freshness identity domain;
- query/absence/replay/target/descriptor/source/argv categories likewise have no per-category field grammar.

The default fixture path reinforces the problem: `_default_rows("review-a")` synthesizes one placeholder string per category, so the passing suite never constructs the real canonical authority shapes.

Why this matters: the fake host can accept structurally incomplete or semantically malformed ReviewRecord categories and compute a self-consistent digest. A fixed category name plus opaque arbitrary strings is not yet the complete typed/canonical ReviewRecord required by V27 or by the previous review's acceptance criteria.

Acceptance:
1. define an exact canonical primitive schema for every ReviewRecord category, including required field count/order/type/format and nested ordered tuples where applicable;
2. encode the inherited authority surface explicitly: full consumer/guard/verifier provenance, C01--C15, nine freshness identities, query stdout/stderr/predicate identities, local/remote authority absences, designated absences, replay binding, targets, descriptor/source/argv identities;
3. reject missing/extra/reordered **and per-category malformed/partial** fields before a session is created;
4. make the canonical digest derive only from that fully validated schema plus exact Gate/root/child/binding values.

## HIGH 2 — client-visible ReviewRecord is the same object stored as host authority, and record/binding integrity is not revalidated

Locations: `tools/psm_wma/stage1_host_boundary.py:108-116, 119-127, 132-151, 159-176`.

`create()` constructs one `ReviewRecordV27` object, stores that exact object in `self._sessions[session]["record"]`, and returns the same object to the caller. The later privileged attestation, approval, and resume paths trust fields from that same aliased object. None of those paths recomputes the canonical row digest, live-plan digest, binding digest, or record digest from host-private creation-time primitives.

`@dataclass(frozen=True)` only blocks ordinary assignment; it does not create a host boundary. A direct standard-Python base mutation on the returned object changes the exact object held by `_sessions`.

Concrete causal examples:
- after review/attestation, `object.__setattr__(record, "authority_rows", drifted_rows)` leaves `record.digest` unchanged; `approve()` never recomputes rows -> digest and can still accept the already-minted approval;
- after approval, `object.__setattr__(record, "host_lease_id", attacker_lease)` changes the lease that `resume_once()` compares, because resume reads the same aliased record object; there is no creation-time binding revalidation before CONSUMING.

This directly violates the V27 model that host-private authority is not mutable through client objects and that reviewed authority/binding drift terminalizes before freshness/apply. The fake-host is allowed to be same-process, but it must still *model* this boundary rather than alias client-visible witness objects into authoritative state.

Acceptance:
1. host-private session state must store its own detached canonical immutable snapshot/primitives; client/audit `ReviewRecordV27` must be a copy/value witness, never the authoritative object reference;
2. privileged attestation and approval must verify the presented record against the host-private creation snapshot and recompute/check the canonical record digest;
3. resume must validate current host-private generation/session/plan/lease/binding authority from that private snapshot before consuming admission;
4. client-side mutation of returned record fields, including `authority_rows`, digest, lease, plan/session ids and binding digest, must never mutate host authority and must be rejected/irrelevant with zero extra freshness/consumer/apply;
5. add direct base-mutation witnesses using `object.__setattr__` on the returned audit record before attestation, after attestation and after approval.

## MEDIUM 3 — evidence is broader but still not causal for the remaining ReviewRecord contract

Location: `tools/psm_wma/test_stage1_host_boundary.py`.

The suite grows from 4 to 8 tests and now usefully covers exact approval-field drift, prior session/generation cases, parallel resume, terminal freshness/apply/verify branches and foreign lease. That closes substantial portions of the prior Evidence gap.

However the ReviewRecord witnesses do not prove the two remaining HIGHs:
- `test_every_record_category_drift_is_rejected` does not mutate the host's reviewed record category and test revalidation; it only substitutes `approval.record_digest` with `_digest_rows(drifted_rows)`, which is simply a wrong approval digest and would fail even if category validation were deleted;
- malformed-record testing covers top-level missing/extra/reordered category names, but not malformed/partial field grammar inside any category;
- there is no client-visible-record alias/base-mutation witness;
- the parallel test starts two threads but does not deterministically force overlap at the admission boundary, so it is weaker as a regression witness for the lock than a barrier/hook that proves one request remains inside the critical/CONSUMING window while the other attempts resume.

Acceptance:
- add per-category malformed-field tests tied to each exact schema;
- mutate the returned ReviewRecord itself and prove host-private snapshot/digest remains unchanged and admission rejects or is unaffected appropriately;
- make the category drift test causal: removing per-category validation or record-digest revalidation must make it fail;
- strengthen the duplicate/pipelined witness to deterministically exercise overlap around `APPROVED -> CONSUMING` if practical for the fake-host model.

## Blocker lifecycle

From the previous implementation review:
- complete typed/canonical ReviewRecord: `PARTIALLY CLOSED / STILL OPEN (HIGH)` — category names/order exist, but category grammar is still opaque arbitrary strings;
- exact Gate/root/child + privileged test attestation separation: `CLOSED`;
- serialized/atomic admission: `CLOSED` at implementation level;
- CPU/static Evidence matrix: `PARTIALLY CLOSED`; approval/replay/concurrency/failure coverage is much better, while ReviewRecord causality remains incomplete.

New completed-sweep finding:
- client-visible ReviewRecord aliases host-authoritative state and permits base-mutation drift/rebinding: `OPEN (HIGH)`.

## Scope reminder

This verdict binds only the exact formal pair above and `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`. It does not authorize real Stage1Host process/OS identity, real IPC, privileged real attestation transport, real envelope/pre-C/C, real consumer or `apply_patch`, request pair/materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference or LIBERO4IN1.
