# GPT independent incremental Phase B r2 Design Gate — Ticket Quiescence and Replay (2026-10-29)

## 1. Exact Formal Pair and verdict

**Final technical verdict: `REQUEST_CHANGES` — Phase B r2 DESIGN / isolated symbolic protocol Gate ONLY.**

- **New Formal Design Root:** `8f94b67ef3f049f5905ee35d54083d5f69534975`.
- **Unchanged Formal Child/Gitlink:** `d2c1bda62880dbeee196f70945e5bc430b73f4b6`.
- **Previous reviewed r1 Design Root:** `fac029c83eb94fdafcc26d030ca5942542d740a3`, verdict `REQUEST_CHANGES`.
- **Phase A production source:** Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` + same Child, its prior `APPROVE_CODE` remains valid **only on its own exact pair**; DS independent CPU remains pending.
- **Isolated candidate branch:** `v3-eval-v2-batch-b-design-20261029`. Later evidence/docs HEAD `3e469d74322e737e20cab294bc8162579369b073` is not the Formal Design target.
- **Author handoff:** `docs/collab/codex/reviews/2026-10-29_V3_EvalV2_PhaseB_Design_r2_BD1_BD2_author_handoff.md`.
- **r2 normative addendum:** `docs/build/PSM-WMA_V3_EvalV2_PhaseB_Design_r2_Ticket_Quiescence_2026-10-29.md`; retained r1 design is still binding where not explicitly superseded.
- **Previous Gate:** `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_r1_fac029c8_d2c1bda6_Design_Gate_REQUEST_CHANGES.md`.

I freshly read the actual Formal target, its `fac029c8..8f94b67e` changed-file inventory, the r2 addendum, modified `ProtocolModel`, new `TicketRegistry`, both new test files, final author Evidence and the **exact frozen old findings**. The Git tree at Formal Design Root has Gitlink mode `160000` pointing to exactly `d2c1bda6`; comparison to r1 proves `scripts/`, `configs/`, `third_party/` and Child Gitlink remain byte-identical. No Phase B production implementation or native GPU permission is implied.

## 2. Closed prior blockers

### B-D1 — HIGH, **CLOSED** (in this symbolic Design Gate)

Old failure: `reset(leaseA)` returned a successful ACK while A+B's generation still owned the transaction.

Actual r2 source: `tools/v3/eval_v2_batch_design/protocol_model.py:136–189` now distinguishes `request_cancel()` (intent only), `request_end()` (explicit `EndReply(False)` if still busy) and `poll_end()` (positive ACK only when no busy executor or nonquiescent owned Ticket). `execute():282–345` retains single executor ownership, runs the cancellation fence and only invokes `TicketRegistry.finish()` in its post-unwind `finally`. The physical Slot cannot open a new generation before its prior one is closed. Queued cancellation is drained via an explicit executor event. No `End` callback fabricates GPU quiescence.

Behavior-level synthetic evidence: `lifecycle_test.py:53–116` injects End at SEALED, individual PREPARED items, GENERATING/inside generator, GENERATED/VALIDATED and before publication; checks negative ACK, unchanged Fast/Visual/response bundle, zero credit reuse, then positive ACK after abort/quiescence. `lifecycle_test.py:184–214` covers postcommit-but-still-owned End: defer ACK until Executor leaves, discard A only, keep B intact. `:235–260` covers lost End ACK / new Slot generation / foreign lease; `:283–296` tests idle co-member End while the single executor is busy. The corrected test in `protocol_model_test.py:118–126` uses `request_cancel`, not `reset`, as a cancellation injection.

**Closure limited to symbolic authority.** Real HTTP concurrency/CUDA kernel drain and process death remain implementation/native Gate requirements.

### B-D2 — MEDIUM, **CLOSED** (original pop / in-flight-credit defect)

Old failure: `BatchQueue.pop()` removed a Ticket completely, losing same-Slot ownership and queued+inflight bytes.

Actual r2 source: `tools/v3/eval_v2_batch_design/ticket_registry.py:29–117` owns canonical Tickets/Slot credits and counts ALL unresolved Tickets, not only `rows`. `:130–185` seals `pop()` without deleting Tickets; `:187–246` allows only ordered executor stage transitions and releases at an exact quiescent terminal boundary, drops released member references from batch metadata, and prevents double credit return. `:248–262` separates cancel intent and outstanding ownership. `ProtocolModel` uses **the same** registry object for submission, execution and Session End.

Behavior-level synthetic evidence: `ticket_registry_test.py:45–85` checks exact duplicates and new-frontier rejection at all in-flight stages, plus byte caps after pop; `:88–108,110–180` covers committed-undelivered credit, timeout without fake quiescence, co-member preservation; `:183–220` checks exact seal adoption and stale/fake capability; `lifecycle_test.py:131–181,262–319` integrates registry and model for after-pop End, timeout, and seal-failure cleanup. Three frozen r1 counterexamples are included under `evidence/.../red/`; their actual pytest/JUnit reported 3 expected failures against the precise old `fac029c8` protocol source.

**Closure limited to the claimed queued→inflight→delivery boundary.** One new but adjacent post-ACK replay defect is separately recorded below; the original B-D2 source issue is not carried forward as unresolved.

## 3. New finding B-D3 — MEDIUM — post-delivery ACK replay can re-admit an already committed old Frontier as an unfinishable QUEUED Ticket

**Scope:** Phase B **symbolic ProtocolModel / API contract**, not Phase A production.

**Exact file:lines:**
- `tools/v3/eval_v2_batch_design/protocol_model.py:130–135` — `submit(request)` checks ONLY `request.key not in self.registry.tickets`, then calls `registry.submit` without checking the already-published response cache.
- Same file `:191–216` — `cached()/deliver()/acknowledge()` support replay and `acknowledge` releases a *currently registered* Ticket.
- Same file `:244–265` — `execute()` returns an existing cached reply **before sealing or terminalizing** any newly re-admitted Ticket.
- `tools/v3/eval_v2_batch_design/ticket_registry.py:92–117` — once the old Ticket was removed from `tickets`, `submit` can allocate it again, despite the same immutable response remaining in `ProtocolModel.bundle.responses`.
- Same file `:218–235` — a QUEUED, nonquiescent re-admitted ticket is not releasable as `delivered`.

**Source-reachable counterexample (no production execution claimed):**

1. Open Session A, `submit(R0)`, `execute([R0])` and `acknowledge(R0)`. The registry now has **no** R0 Ticket, but `bundle.responses[R0.key]` still contains its committed response for bounded replay (as designed).
2. The client retransmits the exact same POST R0 after its delivery ACK was lost or was retried late: `ProtocolModel.submit(R0)` does **not** first route through the cached response; it allocates a **fresh QUEUED Ticket** and reserves the physical Slot + bytes again.
3. `ProtocolModel.execute([R0])` returns the cached result without advancing the new Ticket. A subsequent `acknowledge(R0)` tries `registry.release(new_ticket, 'delivered')` and fails `ticket cannot release before terminal executor quiescence` (state QUEUED). The old Ticket cannot naturally reach a terminal executor state via this replay path.
4. A legitimate next `R1(frontier=1)` is blocked by the now-stranded same-Slot QUEUED reservation. A **changed-payload, same-key** replay can likewise reserve this slot before `cached()` later rejects the mismatch.

**Frozen-contract violation:** r1 design `docs/build/PSM-WMA_V3_EvalV2_PhaseB_MultiSim_Transactional_Batch_Design_r1_2026-10-29.md:68–74,84–90` requires `POST /v2/inference` to return already-committed results and cached Tickets to bypass new batching; r2 addendum `docs/build/PSM-WMA_V3_EvalV2_PhaseB_Design_r2_Ticket_Quiescence_2026-10-29.md:52–61` explicitly promises bounded exact replay **after ACK/release**, duplicate HTTP attachment, one Slot reservation and no regeneration. This public-entry sequencing is not covered by the existing 74 tests: `lifecycle_test.py:215–232` retries `submit()` **before** the first delivery ACK, tests a repeated `acknowledge()` after ACK, then advances to R1; it never resubmits R0 **after ACK** through the same admission API.

**Severity rationale:** MEDIUM — a benign late duplicate or lost-delivery-ACK sequence can leak/re-reserve a physical Slot and stop an otherwise valid Episode's next Frontier, with no demonstrated cross-Session numerical corruption. It is still a Design Gate blocker: r2 explicitly claims idempotent post-ACK replay as a lifecycle invariant.

**Minimum remediation / acceptance:**

1. Use a **single replay-aware admission path** for the real `POST /v2/inference` model: for an already committed, exact matching R0 still present in the bounded cache, return its immutable response or an explicit `ALREADY_COMMITTED` result **without allocating a new QUEUED Ticket, changing credit, resetting deadline, or calling generation**. Same-key changed-payload replay must fail *before* any ticket allocation; old evicted Frontier must reject safely without re-registering stale work.
2. Preserve existing r2 behavior for still-unresolved Tickets: exact duplicate attaches to same Ticket; new Frontier blocked until ACK/discard; after valid ACK and new R1 only R1 owns new capacity. A second ACK of R0 remains idempotent and cannot release R1.
3. Add a deterministic integration **negative + positive** against `ProtocolModel.submit → execute/cached → acknowledge`, not just `Bundle.cached`: R0→commit→ACK→late identical POST→cached replay→ACK→R1; plus changed-payload R0 after ACK and after R1 advancement/old replay eviction. Assert no second generation, no ghost QUEUED Ticket, no altered byte/Slot credits and no effect on another Session.
4. If Codex instead intends a separate HTTP pre-cache router, specify and test the *actual complete public operation* so no exposed `submit` path can bypass replay authority; do not silently redefine POST retries as invalid when the frozen protocol explicitly permits them.

No additional production-code blocker is inferred. This is a narrow newly found **design/protocol evidence mismatch** following correct remediation of both old blockers.

## 4. Evidence and limitations

- Confirmed Formal Design Root Git tree and exact Child Gitlink. `scripts/`, `configs/`, `third_party/` and Child tree/gitlink SHA are unchanged from r1 and thus from Phase A source. Technical diff includes design r2 addendum, `ticket_registry.py` and `ticket_registry_test.py`, `lifecycle_test.py`, updates to old protocol model/tests, and SESSION/TODO. No Phase B production code was modified.
- Independently fetched author `final/junit.xml` on candidate Evidence branch: **74 tests, 0 failures/errors/skipped, 0.213s**; author `final/pytest.log` says `74 passed in 0.21s`. Verified author `final/ruff_check.log` = `All checks passed!`, `final/ruff_format.log` = `6 files already formatted`, AST6 author evidence, and expected r1 RED3 raw test/logs. These are author-side evidence, **not** a GPT independent execution.
- Independently fetched all **8/8 new formal Design Root Git Blobs** and matched `formal_design_bindings.json`. Previous frozen Phase A production source was already reviewed on exact unchanged Gitlink/tree; author records 16/16 production bindings. A new full 16-file production technical review is neither needed nor claimed. No model, torch tensor, HTTP, process, GPU, EGL, real RoboCasa, real Cosmos, DCP or 900 benchmark work was executed here.
- The symbolic model and fake vector proof do **not** by themselves authorize real tensor/session implementation or assert B>1 native numeric parity.

## 5. Verdict and next authorized action

**`REQUEST_CHANGES` on Design Root `8f94b67ef3f049f5905ee35d54083d5f69534975` / unchanged Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6`.** Prior **B-D1 and B-D2 are CLOSED**, **new B-D3 MEDIUM is OPEN**. The overall architecture does not require redesign.

Authorize **only a narrow isolated Phase B design/protocol/test remediation** for B-D3 with a *new exact Formal Design Root SHA*, unchanged Child, retained old RED/author Evidence plus new focused tests, Ruff/AST and source identity. STOP for incremental GPT Design Gate. Do not edit Phase A/Phase B production Root/Child, merge `V3`, launch DS jobs, GPU/native Cosmos/RoboCasa/900, train or mutate Checkpoints/Vendor/old431.

**Phase A independent DS CPU remains pending**; Phase B production implementation must not start until the **new** exact Design Gate is approved, and future Code/DS/Owner native Canaries remain separate.

This technical verdict becomes **formal** only once this detailed review and matching append-only `docs/collab/chatgpt/CODEX_INBOX.md` entry are both published and independently read back.
