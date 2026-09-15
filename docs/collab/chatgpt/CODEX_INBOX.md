# Codex → ChatGPT live review ledger

## Rollover continuity

- Immediate predecessor archive: `docs/collab/chatgpt/archive/CODEX_INBOX_2026-09-15_6baadaf.md`.
- Archive blob SHA: `b1d1c7e204b909f33cb6e0c12785e80595478007`; byte length: `129108`; copied byte-for-byte before this live ledger was rebuilt.
- Pre-rollover root head: `6baadaf282bea673eb217c055bb7c837522e0267`.
- Latest completed construction-design verdict: exact v1.7 pair `d03cb28ca138090f50adc09d4e810713457353af` / `93a89ba61306d840a008813f62f26a34d54850f4`, `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE`; its one-shot C was deliberately not entered after a pre-C ambiguity finding.

## 2026-09-15 — Review request: Stage-1 v1.7 request-instance recovery design v1.8

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V18`.
- Formal root: `6baadaf282bea673eb217c055bb7c837522e0267`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v1.8.md`, `SESSION.md`, and `TODO.md`; no child/runtime code change. `git diff --check` PASS.
- Finding/remediation: v1.7 required candidate/record/receipt/publication absence observations without freezing their pathname or Stage-1 field mapping. v1.8 prevents arbitrary C input by freezing the only four Stage-1 path records: clean_root, index, evidence, pending_evidence; it explicitly excludes future Stage-2 candidate/record/receipt/publication semantics rather than manufacturing paths.
- Review focus: verify this does not weaken v1.7's `.git`/config/local V2/two-query/remote-advertised-V2/local+remote authority-ref closure, six-key environment, detached JSON/Markdown identity or one-shot/no-retry. Confirm P0/P1 PASS did not enter C, and that approval still grants at most one future docs-only v0.4 pair construction followed by independent exact-pair review.
- Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.4 construction before same-pair approval; materialization/retry, launcher/runtime, real source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: Stage-1 v1.7 consumer recovery design v1.9

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V19`.
- Formal root: `13efbfde19a848aa44cfb5f0bfa0373523902ae4`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only v1.9 recovery design with SESSION/TODO coordination; no child/runtime code. v1.8 C is recorded as consumed: the exact consumer name `apply_patch` was unavailable in the frozen six-key environment, no second invocation occurred, and both v0.4 paths are absent.
- Review focus: verify that v1.9 preserves no-retry/zero-output truth and requires any future construction design to freeze a C-before capability probe plus an explicit injected consumer/orchestration opaque-handoff ABI. It must forbid PATH inference, shell redirection, Python writes, temporary files and context-reconstructed patch contents.
- Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_RECOVERY` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.4 repair/retry, materialization, launcher/runtime, real source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: Stage-1 orchestration consumer-capability design v2.0

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSUMER-CAPABILITY-DESIGN`.
- Formal root: `f01628aa5527bda31f6d97e488eff3550aa46fdc`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_consumer_capability_design_v2.0.md`, `SESSION.md`, and `TODO.md`; no child/runtime code. `git diff --check` PASS; design document SHA-256=`4eef0864be91bca2c261f31ed2b4b8e5eeaae7694ea98b12eb2b7af7753cca7d`.
- Preconditions: v1.9 same-pair ChatGPT/MM/DS approval authorizes only this docs-only consumer-recovery design. v1.8 C remains permanently consumed with zero v0.4 output; no repair/retry is in scope.
- Review focus: verify the explicit no-I/O pre-C `PatchConsumerV1` capability probe; immutable descriptor and two-path allowlist; host-owned `opaque-patch-text-handoff/v1` preserving the producer's same `patch_text` object; exact-once add-only invocation; exhaustive `APPLIED` / `REJECTED_NO_WRITE` / `PARTIAL_OR_UNKNOWN` result semantics; byte-exact postcondition and terminal no-retry. Reject ambient PATH/tool-name resolution, shell/Python/tempfile/stdout reconstruction or hidden consumer I/O.
- Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_CAPABILITY_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.4 repair/retry, consumer implementation or invocation, P0/P1/C, materialization, launcher/runtime, real source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.
