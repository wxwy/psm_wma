# Phase B Transaction/B1 — B1-F1 original-budget author handoff

Date2026-10-29. **Request fresh incremental APPROVE_CODE / REQUEST_CHANGES for B1-F1 only.** Author evidence is not a reviewer verdict or DS acceptance.

| Identity | Exact value |
| --- | --- |
| **Formal Implementation Root** | `dc7757922d7273f50f3de23363d41e12e157a07f` |
| **Formal Child / Root Gitlink** | `4a938e41b0c335baca1c1d8f1caabc433b0e2001` |
| Isolated Root/Child candidate | `v3-eval-v2-transactions-b1-20261029` |
| Prior reviewed Root / Child | `9a3f88e55893491ea68d16b3f23680ae6941d106` / `1bece52ee419d12119c1b3d0b75e0ae5c5139ae9` |
| Effective GPT review | V3 docs `e57f0263757c65521acac7a2c24e7fdbdaa78cfb`; Recheck_P1_WITHDRAWN_F1_OPEN report |
| Approved design | Root `b9c7cf1607ffd38f6e3349bdde0b35703a6d7684` / Child `d2c1bda62880dbeee196f70945e5bc430b73f4b6` |

Review the incremental Child **1bece52e..4a938e41** and Root **9a3f88e5..dc775792** technical delta. Evidence/readback commits after the Formal Root are bookkeeping. Earlier Phase A source APPROVE_CODE and Phase B APPROVE_DESIGN remain at their own Pairs; neither implies approval of this new code. Prior B1 Code Gate is REQUEST_CHANGES. B1-P1 is WITHDRAWN, not a pending remediation.

## Minimal production correction

Only3 Child production files and2 test files changed; no new model or simulation implementation.

- Client freezes started_at/deadline at `predict()` entry before serialization. The mandatory wire budget is `{clock_domain, started_at, deadline}`, identical across retries. Poll/ACK retain the same local deadline. Late transport or JSON decode cannot return client success.
- Shared Linux CLOCK_MONOTONIC domain is derived from bounded, validated kernel boot UUID and monotonic namespace offset. Registration verifies equality before the lease is usable; B1 server options reject missing kernel proof before model initialization. Foreign domains, future start, expired/invalid/nonfinite/oversized/bool times and excess duration reject without allocation. Client timeout must not exceed Server cap. Legacy profile is unchanged.
- Production Dispatcher requires budget and passes it through. Actor stores the transmitted original deadline; it never adds a new timeout at receipt. It rechecks after payload validation/serialization and lock wait. Existing prepare/generate/post-device-drain commit fences check this same value. Expired uncommitted work aborts without changing Fast/Visual/Response; executor ownership/End/quarantine semantics are retained. HTTP expiry is explicit408.
- Inflight retry attaches to the original Ticket/deadline. In-budget lost response/ACK and ACKed response replay never recompute. A new read budget may retrieve an ACKed cached result but cannot renew an expired undelivered Ticket or change committed inference. A genuine in-budget commit is not falsely rolled back merely because delivery/ACK arrives late; End remains the recovery boundary.

Full wire/runbook and limits: `docs/build/PSM-WMA_V3_EvalV2_PhaseB_B1_F1_Original_Deadline_Addendum_2026-10-29.md`. Original frozen implementation/design documents and old raw evidence were not rewritten.

## Final clean exact-pair author CPU

Raw evidence: `docs/collab/codex/evidence/2026-10-29_eval_v2_b1_f1_original_deadline_author_cpu/`.

- **354 passed =99 inference/transaction tests +255 unchanged Phase A CPU regressions;0 failures/errors/skips.** Ruff0.12.7 check/format, AST9, actual import origin, source fingerprints before/after and clean source checks PASS. All67 prior inference JUnit test identities remain present, with32 new cases; old assertion semantics were not relaxed.
- The actual old1be production code failed the new delayed-first-arrival regression in2 expected cases (cold and hot), at the snapshot preservation assertion. Client started at0 with1s budget, upload arrived at0.8, client expired at1, generation completed at1.2 and old server committed. Raw RED logs/JUnit retained. These tests were newly appended/uncommitted when first run; no pre-run byte hash was captured for that draft test file. Frozen old production source bindings and final committed regression source are provided; this limitation is not disguised as a clean old-pair gate.
- New tests traverse real Client→Dispatcher→Actor with controlled clocks/transport/generation: first arrival and retries consume original time; before-accept and inflight loss preserve original budget/Ticket; generation/device-drain past deadline preserve old snapshot; expired upload allocates nothing; encoding charged; in-budget success, lost ACK and committed replay; late response/ACK does not report success; actual handler408; domain/namespace/malformed/absent kernel negatives.
- Real CPU Local encoder/scan/Fast tensors, real state publication, and actual B1 preprocessing/service API are used. Wan/diffusion/network boundaries and kernel file streams are explicit doubles. No live Action Server port/model weights/GPU/RoboCasa/EGL/DCP. Phase A synthetic900-slot regression is not real SR or capacity evidence.

### Actual environment limitation — must remain visible

This cloud exposes boot_id but **does not expose `/proc/self/timens_offsets`**. The unmocked production clock probe is therefore **BLOCKED_KERNEL_IDENTITY_UNAVAILABLE**, retained in `actual_cloud_kernel_probe.json`; production validation was not bypassed. The initial exploratory test run failed at this live kernel read and is kept separately. Final tests explicitly supply bounded boot/offset byte streams to the **actual parser**, and verify absence/invalidity/mismatch separately. CPU protocol PASS is not proof that this cloud can run the B1 profile.

Before any separately authorized native run, DS must execute the addendum's CPU-only `monotonic_clock_domain()` command from the actual Client and Action Server environments, without fixtures, and require equal domains. If either environment lacks kernel evidence or they differ, that runtime remains BLOCKED; no receive-time/wall-clock fallback. Native model/device/network/host compatibility still requires independent acceptance. This read-only prerequisite does not dispatch a DS job or authorize GPU work.

## Replay command and review request

```bash
python tools/v3/run_eval_v2_transactions_b1_cpu_gate.py \
  --root-worktree '<EXACT_CLEAN_ROOT_WORKTREE>' \
  --expected-root dc7757922d7273f50f3de23363d41e12e157a07f \
  --expected-child 4a938e41b0c335baca1c1d8f1caabc433b0e2001 \
  --evidence-dir '<NEW_EXTERNAL_EVIDENCE_DIR>'
```

Retained: raw final gate/combined and per-group JUnit/logs/commands/environment/source hashes; explicit intermediate runs and old RED2; incremental and full Child diffs, Root technical diff, protected-path inventories,15 frozen source GitBlob bindings and artifact hashes. Source untouched during the final replay. The existing CPU gate itself and all Root scripts/configs/Vendor/Phase A tests are unchanged.

Canonical V3 collaboration additions were imported into this isolated candidate, preserving both complete live tails and immutable130996-byte archive Blob `d702c44dd68529e93a491c5353e866ab7be92a07`. No old Inbox restoration or history deletion. Unrelated Compact evidence was preserved without acting on it.

Request **fresh GPT incremental Code Gate for B1-F1 only**. After candidate publication/readback, STOP. Phase B second increment remains NOT_STARTED; Phase A independent DS CPU remains PENDING. No canonical V3/Child merge, DS dispatch, GPU/model/native simulation/DCP/900, training/checkpoint/RNG/optimizer/Vendor/G1/old431/result operation occurred or follows automatically.
