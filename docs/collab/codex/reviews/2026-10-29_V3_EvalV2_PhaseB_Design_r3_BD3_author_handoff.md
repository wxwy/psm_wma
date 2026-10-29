# Phase B r3 — B-D3 replay admission author handoff

Date: 2026-10-29. **REQUEST INCREMENTAL APPROVE_DESIGN / REQUEST_CHANGES.** Author report only, not a reviewer verdict.

| Identity | Exact SHA / ref |
| --- | --- |
| **New Formal Design Root** | `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` |
| **Unchanged Child / Gitlink** | `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Reviewed r2 Design Root | `8f94b67ef3f049f5905ee35d54083d5f69534975` |
| Unchanged Phase A production Root | `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` |
| Isolated candidate | `v3-eval-v2-batch-b-design-20261029` |

Fresh V3 fetch/advertised/tracking `70aebb5cc69f9b2f65b20440d0fa093eb31bcbe8` and exact r2 detailed review+canonical Inbox were read; pre-publication recheck unchanged. B-D1 and B-D2 are formally CLOSED in that r2 review; only B-D3 is remediated here. Later evidence/handoff/receipt HEAD is bookkeeping, not the new Design Root. No new Child source commit exists.

## Narrow change

`ProtocolModel.submit` now validates retained response identity/payload **before allocator invocation**. It preserves attachment to unresolved exact Tickets. Once the old Ticket is released, a matching retained response returns the same immutable `Response` without new count/bytes/deadline/generation. Same-ID changed payload rejects before admission. Without retained response, stale/evicted Frontier rejects before registry access.

This closes the author-side path that previously re-created an unfinishable QUEUED R0 after its Delivery ACK. Replaying/ACKing R0 while R1 owns the Slot leaves R1 and another Session untouched. Existing bounded response/ACK window, cancelled delivery fences and End quiescence are retained. No unbounded history or new HTTP implementation is added.

Only existing `submit()` changes:12 inserted/2 removed lines. AST comparison proves all other model code unchanged from r2. Five previous nonmodel Python files, including Registry and all prior74 tests, are byte-identical; no assertion is weakened. Direct source commit changes5 files: model, new16-case test, r3 design addendum, SESSION and TODO. Root `scripts/`, `configs/`, `third_party/`, Child/Gitlink and frozen r1/r2 designs/evidence remain unchanged.

Full normative addendum: `docs/build/PSM-WMA_V3_EvalV2_PhaseB_Design_r3_PostACK_Replay_2026-10-29.md`.

## Actual author evidence

Evidence: `docs/collab/codex/evidence/2026-10-29_eval_v2_phase_b_design_r3_author_cpu/`.

- Same16 new tests on exact frozen r2: **11 expected RED failures +5 passes**,0 errors/skips. Model Git Blob `b0890dfe8b8f550ce29b8fc65662a83dd6c29b04`, copied raw source, test SHA256, command/log/JUnit retained. This is intentional old-version evidence, not r3 failures.
- New targeted suite: **16 passed**,0 failures/errors/skips. The exact same test source is used before/after the fix.
- Final full isolated suite: **90 passed**,0 failures/errors/skips, raw JUnit0.246s (pytest0.25s): original74 unchanged plus16 new cases.
- Ruff **0.12.7 check + format --check PASS**, AST7 PASS;16 production Git Blob/hash bindings match, protected production diff ZERO, Child clean. Raw final/targeted/red JUnit/logs, exact commands/environment, narrow-scope proof, source/formal diff/bindings and SHA256 manifest included.

Tests cover the complete public submit→generation→ACK→late submit→replay→ACK→R1 sequence, old R0 replay/ACK while R1 is queued, changed payload before allocation, evicted identical/mutated R0 before/after R1 ACK, current credits/other Session isolation, unresolved duplicate budgets and closed/epoch fences. A stale ACK outside the bounded retained response window keeps the prior fail-closed behavior and cannot release current ownership.

These remain stdlib symbolic state/fake vector/fake clock tests. No real model, torch Local tensor, HTTP, CUDA/OS quiescence, GPU/EGL/physics/throughput proof is claimed. No Phase A255 rerun or DS execution occurred.

## Review request and STOP

Please incrementally review only B-D3 on the new exact Design Root/unchanged Child and issue `APPROVE_DESIGN` or precise `REQUEST_CHANGES`. Codex stops after candidate publication/readback. Phase B production implementation remains unauthorized; Phase A source APPROVE_CODE remains unchanged with independent DS CPU pending. No merge-to-V3/Child, GPU/model/real RoboCasa/DCP/900, DS job, training/checkpoint/Vendor/old431/history operation was performed.
