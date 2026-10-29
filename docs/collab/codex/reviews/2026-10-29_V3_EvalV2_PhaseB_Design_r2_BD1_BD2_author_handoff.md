# Phase B r2 — B-D1/B-D2 author design handoff

Date: 2026-10-29. **REQUEST INCREMENTAL APPROVE_DESIGN / REQUEST_CHANGES.** This is an author report, not a reviewer verdict.

| Identity | Exact SHA / ref |
| --- | --- |
| **New Formal Design Root** | `8f94b67ef3f049f5905ee35d54083d5f69534975` |
| **Unchanged Child / Gitlink** | `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Reviewed r1 Design Root | `fac029c83eb94fdafcc26d030ca5942542d740a3` |
| Unchanged Phase A production Root | `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` |
| Isolated Root candidate | `v3-eval-v2-batch-b-design-20261029` |

The evidence/handoff/receipt HEAD is bookkeeping and never replaces the Formal Design Root. No new Child commit or production support is claimed. Exact r1 detailed review and canonical Inbox were freshly fetched/read at V3 `b4cd955ab5b139ce344afd5e9a34750db215ca6d`; pre-publication recheck confirmed unchanged advertised/tracking SHA. Candidate publication does not merge into V3 or update the V3 Inbox.

## Narrow remediation

**B-D1 — deferred End ACK:** dedicated `request_cancel()` records intent only. `request_end()` and `poll_end()` return an explicit non-ACK while the model executor or owned Ticket is nonquiescent. Only executor return/unwind can finish an aborted/committed batch; a timeout cannot fake this proof. End then releases/discards only its own settled ownership and state. Lost positive End ACK replays only for the exact closed generation. Root cannot reuse the Slot before that ACK. Cancellation before/inside/after Generation and pre/postcommit are exercised, including co-member preservation and an unrelated Session End waiting for the single model owner.

**B-D2 — one queued+inflight registry:** Queue and Session model share the same `TicketRegistry`. Pop seals but retains Ticket, Slot and byte credit through committed-undelivered state. Exact duplicates join the original object without renewing budget; changed payload/new Frontier are rejected until release. Delivery ACK, owned End discard or settled abort returns credit once. Partial release removes registry references to freed payload; a failed seal cleans only new admissions. Timeout cancellation after commit also fences response delivery/replay without regenerating or changing committed co-member state.

New normative addendum: `docs/build/PSM-WMA_V3_EvalV2_PhaseB_Design_r2_Ticket_Quiescence_2026-10-29.md`. The frozen r1 design is retained; only lifecycle/release sections are superseded. Independent Fast State, one true native Generation, model math, shape/action ABI, D1–D5, scene sampling, optional media, resources and prior scope are not redesigned.

The source commit directly changes8 files: new r2 design, two existing isolated model/tests, three new isolated Registry/lifecycle files and SESSION/TODO. `scripts/`, `configs/`, `third_party/`, all Child source and Gitlink remain exact Phase A production bytes. The r1 design/evidence are preserved. The isolated model is not imported by production.

## Author evidence actually executed

Evidence: `docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_design_r2_author_cpu/`.

- **Expected RED on exact frozen r1 only:**3 tests,3 intended failures,0 errors/skips. Demonstrates premature positive End ACK/Slot reuse, duplicate recreation after pop, and second same-Slot Frontier admission. Frozen Git Blob/SHA256, counterexample source/command/JUnit/logs included. These are not r2 failing tests.
- **Final r2 isolated CPU:** **74 passed,0 failures/errors/skips**, raw JUnit0.213s (pytest0.21s):29 prior protocol +24 Registry +21 integrated lifecycle. Earlier73 draft log is retained and marked unfrozen, not final evidence.
- Ruff **0.12.7 check + format --check PASS**, AST6 PASS.16 frozen production source Git Blob/hash bindings verified, production diff ZERO, Child clean. Raw final logs, source bindings, exact formal diff, commands, environment and artifact hashes included.
- Codex helper authored Registry and statically cross-checked integration. It identified seal-failure cleanup and postcommit registry-timeout delivery; both were corrected/tested before final74. This is author work, not independent DS execution or GPT approval.

All tests use symbolic tuples, fake vector generation and fake clock; no production imports/model/dataset/Checkpoint inputs. They do not establish real Local tensor/aliasing/RNG, HTTP concurrency, native CUDA quiescence, OS cleanup timing, EGL/physics, resource capacity or throughput. No Phase A255 rerun or native Canary took place.

## Requested decision and STOP

Please review **B-D1 and B-D2 incrementally on the new exact Design Root/unchanged Child**, including cancellation versus ACK, shared registry authority, quiescent versus committed-undelivered, exact credit release, duplicate/timeout/epoch behavior and source preservation. Request `APPROVE_DESIGN` or precise `REQUEST_CHANGES`; neither source Code nor real-execution approval is requested.

Codex stops after candidate publication/readback. Phase B production implementation remains blocked pending Design Gate. Phase A's source `APPROVE_CODE` remains valid; its independent DS CPU still awaits execution. No V3/Child merge, GPU/model/real RoboCasa/DCP/900, DS job, training/history/old431 operation was performed or authorized.
