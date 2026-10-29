# Phase B increment1 — transaction/B1 author Code Gate handoff

Date2026-10-29. **REQUEST FRESH APPROVE_CODE / REQUEST_CHANGES.** This is author evidence, not an independent reviewer verdict.

| Identity | Exact value |
| --- | --- |
| **Formal Implementation Root** | `9a3f88e55893491ea68d16b3f23680ae6941d106` |
| **Formal Child / Root Gitlink** | `1bece52ee419d12119c1b3d0b75e0ae5c5139ae9` |
| Root/Child candidate | `v3-eval-v2-transactions-b1-20261029` |
| Approved Design Root / Child | `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |
| Phase A source baseline | Root `fd7e43f6630a436ab3d83edcd3ce9d1516b342d1` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |

Review the **whole** Child `d2c1bda6..1bece52e` and Root technical delta `fd7e43f6..9a3f88e5`, not just the last Root Gitlink/ledger commit. Later evidence/readback HEAD is bookkeeping, never the Formal Implementation Root. The formal source review at V3 `3f37df1f` authorizes this isolated increment; no default branch merge is made.

## Implemented first increment

- One immutable publication of real Fast State + visual cache + serialized response. Shared lock and exact pending capabilities prevent fast-only paired commit/reset. Existing standalone APIs and model-owned scan remain; candidate cloning protects committed Tensor storage.
- B1 model-owner executor with epoch/run/manifest/physical-slot/generation/task/episode/attempt binding. Session IDs/capabilities are fresh per assignment. Tickets retain count/bytes across queue/inflight/committed-undelivered; bounded replay admission checks committed results before allocation. No ghost post-ACK tickets or budget renewal.
- Cancel and End ACK are separate. Generation/evidence/shape/finite/serialization/publication faults abort before snapshot publication. Real device drain is mandatory before commit; quiescence is marked only after model mutex release. Unproven drain or abort quarantines, retains ownership and never ACKs cleanup. Bounded traceback evidence is kept; an invalid accepted Episode requires End/new Attempt.
- Explicit opt-in service profile and versioned register/submit/poll/delivery-ACK/end. Default remains legacy. This CLI profile enforces one Slot, native B1, required Local, raw15/state15/H16/K4/local32, one visible GPU/rank, complete private identity and no developer training validation. Existing official preprocessing/normalization/generation/prefix API is reused; no model/attention algorithm changes.
- Bounded RPC client validates full result/Local/action identity, retries frozen requests under an absolute deadline and handles lost registration/inference/delivery/end ACKs. Unresolved registration cannot be treated as clean. HTTP body, concurrency, chronology, response and pending-byte limits are explicit.

This profile's generated media is explicitly off. The existing Root Eval V2 Launcher/Sim runtime still uses the Phase A legacy profile and still refuses M!=1/B!=1. **No multi-Sim scheduler, native B>1, batched result distribution/media or complete evaluation entry was implemented or claimed.** That is increment2, not authorized to begin automatically after this handoff. The generic owner is tested with two sequential B1 Sessions for Tensor isolation, not concurrent real Sim capacity.

Child delta is8 files (6 inference/service,2 tests). Root adds exact-pair CPU gate/runbook and Gitlink/bookkeeping. Root `scripts/`, `configs/`, `third_party/` and Child model/training/checkpoint/data/simulator/vendor/optimizer source are unchanged. G1, checkpoints, previous evaluations and old431 were not accessed or modified. Runbook: `docs/build/PSM-WMA_V3_EvalV2_PhaseB_Transaction_B1_Implementation_2026-10-29.md`.

## Final author CPU evidence

`docs/collab/codex/evidence/2026-10-29_eval_v2_transactions_b1_author_cpu/`

- Final clean exact-pair gate: **322 passed,0 failure/error/skip**, comprising67 inference/transaction/native-B1/client tests +255 unchanged Phase A CPU regressions. Ruff **0.12.7 check/format**, AST9, import origin, before/after source fingerprints and clean Root/Child all PASS. Raw group JUnit/logs and combined JUnit are included.
- Tests use actual CPU Local encoder/core/model-owned scan and real Fast State Tensors: W_A!=W_B, non-aliasing storage, W0 byte/numeric unchanged/grad-free, fresh/reset, abort/rollback, input freezing, finite/shape/chronology bounds, delivery credit, epoch/lease/cancel/End, old frontier/replay/ACK. B1 actions and fast state compare exactly to legacy under identical CPU fixture inputs and actual preprocessing/carriers.
- Wan/diffusion/transport boundaries are doubles. Production dispatcher/client/parser are called in process; no Cosmos weight load, real server binding, RoboCasa/MuJoCo/EGL or GPU occurred. Phase A's synthetic900/OS lifecycle tests are fake model/environment evidence, not benchmark SR or new GPU performance proof.
- Source self-check found that a GPU service must not skip drain when `cuda.is_available()` becomesFalse. Intermediate method RED1, explicit mandatory-sync GREEN1; CPU mocks only. Final actor already quarantines the propagated drain failure. Older clean Pair `a3ca1b2f/d0ce64f3` passed321 before this added guard; its logs remain clearly separate and are not final-pair evidence.
- Wrong exact Root negative is BLOCKED before tests. Full command, environment/cache overrides, protected-file inventory, full Child diff, Root technical diff and14 Git Blob/source bindings with artifact hashes are provided. Prior130996-byte live Inbox was archived byte-for-byte (Blob `d702c44dd68529e93a491c5353e866ab7be92a07`); historical review and other agents' records remain intact.

## Independent replay and review request

In clean detached worktrees at this exact pair, using the target CPU Python environment:

```bash
python tools/v3/run_eval_v2_transactions_b1_cpu_gate.py \
  --root-worktree '<EXACT_ROOT_WORKTREE>' \
  --expected-root 9a3f88e55893491ea68d16b3f23680ae6941d106 \
  --expected-child 1bece52ee419d12119c1b3d0b75e0ae5c5139ae9 \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

Request fresh GPT `APPROVE_CODE` or precise `REQUEST_CHANGES` on this **first production increment only**, with particular attention to snapshot publication, generation/cancel/End ordering, device-loss proof, replay/credits, numerical B1 input/state compatibility and preserved defaults. No independent DS or GPU approval is claimed. Codex stops after candidate publication/readback. Phase A DS CPU remains pending; new Code Gate → separately authorized DS CPU precedes any native stages. No increment2, V3/Child merge, DS job, GPU/model/real simulation/DCP/900, training/optimizer/Vendor/history action follows automatically.
