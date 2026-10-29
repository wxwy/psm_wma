# GPT Phase B r3 independent incremental Design Gate — B-D3 post-ACK replay (2026-10-29)

## 1. Formal decision and exact source identity

**VERDICT: `APPROVE_DESIGN` — ONLY Phase B multi-Sim / multi-Session Local-TTT / transactional-batch DESIGN Gate (r1+r2+r3 frozen contract and isolated symbolic protocol).** No production source Code Gate, DS independent CPU, real GPU/native RoboCasa/Model/EGL/900/merge authorization follows from this verdict.

- **Formal Design Root**: `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684`.
- **Formal Child + Root Gitlink**: `d2c1bda62880dbeee196f70945e5bc430b73f4b6` (unchanged).
- Previous reviewed r2 Design Root: `8f94b67ef3f049f5905ee35d54083d5f69534975`, previous `REQUEST_CHANGES`: `docs/collab/chatgpt/reviews/2026-10-29_V3_EvalV2_PhaseB_r2_8f94b67e_d2c1bda6_Incremental_Design_Gate_REQUEST_CHANGES.md`.
- Previous r1 Design Root: `fac029c83eb94fdafcc26d030ca5942542d740a3`. r1/r2 frozen design remains authoritative except for the explicit newer addenda.
- Prior Phase A production **source-only** approval stays exact pair Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6`. Phase A DS_PRO independent CPU remains **PENDING**.
- Isolated candidate branch: `v3-eval-v2-batch-b-design-20261029`. Later author handoff/evidence/readback HEAD `36defe8c0217e7a1c70b2812a3d7ef0e6dda5918` is **bookkeeping, not Formal Design Root**.
- New r3 addendum: `docs/build/PSM-WMA_V3_EvalV2_PhaseB_Design_r3_PostACK_Replay_2026-10-29.md`.
- Source target and evidence were read directly through GitHub; branch identity and Gitlink checked. Root `scripts/`, `configs/`, `third_party/` and Child Gitlink tree entries are identical to reviewed r2, so no production/Child code change is being approved.

The scope of this incremental gate is the single previously open finding **B-D3**. Earlier B-D1/B-D2 were already CLOSED on r2, and their model/registry/test files did not change in r3 outside the reviewed `ProtocolModel.submit` method. Prior withdrawn Stage2 F1 is not reopened.

## 2. B-D3 MEDIUM — CLOSED on exact r3 Design Root

**Previously reachable bug:** `submit(R0)` after `R0→execute→DeliveryACK` re-created a fresh QUEUED Ticket because only live registry entries were checked. A cached `execute(R0)` returned without settling this new Ticket, and a repeated ACK then failed; a valid R1 could become blocked by the ghost reservation.

**Actual patch reviewed:** `tools/v3/eval_v2_batch_design/protocol_model.py:130–144`. The new public admission order is:

1. `_owned(request)` checks active lease/epoch/slot authority.
2. Look up retained committed response by canonical request key. If the payload disagrees, **reject before any allocator call**.
3. For a live unresolved Ticket, attach through `TicketRegistry.submit` (which preserves exact identity, arrival, deadline, bytes and Slot reservation).
4. For no live Ticket, check `_available` (closing/cancel fence), then return the exact `cached(request)` immutable Response **without creating a Ticket** when retained.
5. If cache has evicted a prior committed frontier, reject `request.frontier <= current.committed_frontier` before allocator. Only eligible new frontier requests reach `registry.submit`.

This is consistent with frozen r1 replay/idempotency authority and r2 Ticket ownership/End-quiescence authority. It does not turn a request replay into a new action execution or regenerate the prior result, and does not re-open closed Session generations.

**Behavioral evidence directly inspected:** `tools/v3/eval_v2_batch_design/replay_admission_test.py:49–79` executes full `R0→submit/execute→ACK→late submit→same replay/duplicate ACK→R1` with the other Session's ticket/state/response and byte count unchanged; `:81–110` injects changed noise/evidence/profile after ACK **with allocation spy**, `:112–149` exercises evicted R0, stale ACK and new R2 after R1; `:151–186` covers QUEUED/SEALED/GENERATING/COMMITTED duplicate attachment and closed/restarted lease rejection. The public `submit` operation is exercised, not merely a private cache helper. I independently inspected `ProtocolModel.cached/deliver/acknowledge` and the retained Registry semantics to ensure no new Ticket is created by these replay paths.

**Disposition:** `B-D3 MEDIUM CLOSED`. No fresh substantiated r3 Design Gate blocker was found. This closure is **symbolic design/protocol**, not proof of actual network concurrency, CUDA synchronization or native generator batching.

## 3. Source and author Evidence check

- Independently compared GitHub formal `8f94b67e..b9c7cf16`: technical changes are new r3 addendum, narrow `protocol_model.py::submit`, and a new `replay_admission_test.py`, plus SESSION/TODO. Previously frozen `TicketRegistry`, old 74 tests, and production/Child source remain unchanged. No out-of-scope production changes.
- Independently fetched the **5/5 actual Formal Design Git Blobs** from r3 and matched them to author `formal_design_bindings.json`, including updated model and new test.
- Author's **expected RED** on frozen r2 source: `red/junit.xml` `tests=16, failures=11, errors=0, skipped=0`; source binding points to old model blob `b0890dfe...`, and unchanged new test blob is `e7ba87ec...`. The five r2 controls passed; these 11 failures are deliberately historical, not r3 failures.
- Author's targeted r3 `targeted_green/junit.xml`: **16 tests, 0 fail/error/skip**. Full final `final/junit.xml`: **90 tests, 0 fail/error/skip, 0.246s**, `final/pytest.log` = `90 passed in 0.25s`. This includes 74 previous tests plus 16 new ones.
- Original author Evidence `final/ruff_check.log` + `ruff_format.log`: Ruff `0.12.7` check/format PASS; `final/syntax_and_source.json`: 7 isolated Python AST/source bindings. `final/narrow_scope.json` states prior non-model protocol files unchanged and model AST outside submit unchanged. These are author run results, **not GPT independent pytest/GPU reruns**.
- Formal source GIT tree and direct blob confirmations provide source provenance; I do **not** claim a fresh independent full production CPU/DS run or individual rehash of every Evidence artifact.

## 4. Exact Gate scope, implementation authorization, and next steps

**`APPROVE_DESIGN`** closes the Phase B Design Gate on exact pair **`b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / `d2c1bda62880dbeee196f70945e5bc430b73f4b6`**. B-D1 CLOSED, B-D2 CLOSED (previous r2), B-D3 CLOSED (r3). Full frozen design is r1 plus r2/r3 addenda.

Consistent with Owner Issue #8 and its staged directive, **Codex may now begin Phase B isolated production candidate implementation and CPU-only author tests**, subject to separate new formal source Code Gates. Suggested reviewable increments from frozen r1 §10: (a) inference ticket/session transaction + genuine per-sample tensors/compatibility B1 CPU gates, then (b) M>1 runtime + real native batch collation/client/media CPU integration. Each increment must deliver new exact Formal Root and Child/Gitlink SHAs, production-path focused behavior/JUnit/source Evidence and STOP for GPT Code Gate. No unreviewed semantics change is preapproved; if actual tensor/native API proves incompatible with frozen design, stop for new Design Gate instead of silently relaxing it.

**Still NOT authorized by this approval:** V3/Child production merge, DS independent CPU dispatch, real GPU / Cosmos / DCP / RoboCasa / EGL / any actual evaluation or 900 episodes, training, checkpoint changes, vendor changes or old431 manipulation. Phase A DS_PRO independent CPU remains open on its exact Phase A implementation pair, and is not implicitly replaced by Phase B symbolic CPU.

Formal persistence requirement: Detailed Review at this path **AND** a new append-only entry in `docs/collab/chatgpt/CODEX_INBOX.md`, both read back, are required before calling this a formal verdict.
