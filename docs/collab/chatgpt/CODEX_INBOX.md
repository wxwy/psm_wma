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

### Canonical correction — formal root SHA

- The immediately preceding v2.0 request transcribed the full root SHA incorrectly. Its **only** valid formal root is `f01628aad9775cfb327822c038a5b49e1a393ea9`; the formal child/Gitlink remains `93a89ba61306d840a008813f62f26a34d54850f4`.
- All review focus, requested verdict and forbidden scope in that request are unchanged. The invalid string `f01628aa5527bda31f6d97e488eff3550aa46fdc` is not an object and must not be reviewed.

## 2026-09-15 — Review request: Stage-1 orchestration consumer-capability design v2.1

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSUMER-CAPABILITY-DESIGN-V21`.
- Formal root: `e1def003a645bf63da0e3e0007f2a7c4313325d9`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only v2.1 design with `SESSION.md` and `TODO.md`; no child/runtime code. `git diff --check` PASS; v2.1 SHA-256=`826c8160569b82311f4f8642971fe1ff4427c518e14b7ba6cf17ca86fce64369`.
- Remediation: ChatGPT v2.0 HIGH correctly found that a future construction cannot reuse terminal v0.4. v2.1 makes v0.4 permanently forbidden as input/output/readback/cleanup and binds every future descriptor/consumer/result/readback only to fresh non-overlapping v0.5 JSON/Markdown paths.
- Review focus: confirm the v0.5 freshness/non-overlap closes that issue without weakening the pre-C no-I/O `PatchConsumerV1` probe, explicit descriptor, same-object opaque handoff, one add-only invocation, exhaustive result semantics, byte-exact postcondition or terminal no-retry.
- Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE_CONSUMER_CAPABILITY_IMPLEMENTATION` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.3/v0.4 repair/retry/reuse; v0.5 construction; consumer implementation/invocation; P0/P1/C; materialization, launcher/runtime, real source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: Stage-1 v0.5 unified pre-C rehearsal implementation design v3.0

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-IMPLEMENTATION-DESIGN`.
- Formal root: `6677343ff7bcc931d2c141ada46ced11de2fc318`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only v3.0 implementation design with `SESSION.md`/`TODO.md`; no child/runtime code. `git diff --check` PASS; design SHA-256=`352b6f48e41c50d559bda0b8b8f5a4cfa2dca961fbccf460d051f16496fde237`.
- Review focus: it deliberately collapses all future C failure points into one non-consuming `rehearse_v05()`—unique host capability/callable identity, canonical JSON/Markdown/patch bytes, v0.5 paths, six-key environment, `.git`/local V2/two remote queries/authority ref/designated absences, dry-run patch seam and post-write verifier—then seals them. C has only freshness compare → one opaque add-only write → byte equality → hard stop. Verify v0.3/v0.4 remain forbidden and no hidden C-time resolution remains.
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 construction or consumer invocation; P0/P1/C; materialization, real source/checkpoint/manifest/data/cache I/O, collection/receipt/record/publication, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: v0.5 lifecycle-refreeze pre-C rehearsal design v3.1

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-IMPLEMENTATION-DESIGN-V31`.
- Formal root: `e4764a3c7bf8f99bf8726e011b6ea779c779aeef`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only v3.1 docs/status; no child/runtime code. `git diff --check` PASS; v3.1 SHA-256=`ae0fa7dc5380e6e33c01ed9deb11952c3ed1390505eed90bbee270f4c399e4b8`.
- User-directed remediation: V3.0 reviewers found inherited lifecycle placed live observations inside C. User explicitly required all future C risks be found by one non-consuming pre-C rehearsal. V3.1 makes a narrow v0.5-only lifecycle refreeze: the single rehearsal seals all live inputs and final bytes without writes/consumer; C remains freshness compare → one opaque write → byte verify → hard stop. It reasserts permanent v0.3/v0.4 prohibition across all roles.
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: implementation, v0.5 construction/consumer/P0/P1/C, materialization, real source/checkpoint/manifest/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: pre-C rehearsal consumer CPU/static implementation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`.
- Formal root: `034cbc43f0178e2e472bd642991311cc6116ee49`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no child/runtime code. CPU test=`5/5 PASS`; `py_compile` and `git diff --check` PASS.
- Review focus: `rehearse_v05()` must seal injected capability identity, raw bytes/strict UTF-8 patch text, output pair, six-key environment, frozen snapshot/absence and fake verifier without I/O or consumer invocation. `consume_once_v05()` must have only frozen freshness comparison → exactly one opaque fake callback → post-write byte verification → hard-stop. Confirm v0.3/v0.4 are rejected and no filesystem/Git/network/dynamic-import/real consumer entrypoint exists.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 request pair/C, materialization, source-evidence, real consumer/Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: pre-C rehearsal CPU/static remediation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`.
- Formal root: `e870b903c570359fb7641837ea9b5e64c2aed9e3`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no child/runtime change. `unittest=6/6 PASS`; `py_compile` and `git diff --check` PASS.
- Remediation focus: closes ChatGPT/DS same-pair findings in one static core: exact v0.5 pair; exact six key/value environment; typed closure with required raw facts and ordered query argv/predicates; canonical JSON, Markdown five-field sibling and line inverse witnesses; descriptor/capability/verifier identity and non-copy/serialization; C-admission latch consumed before the single fake opaque call, with explicit APPLIED/REJECTED_NO_WRITE/PARTIAL_OR_UNKNOWN terminal behavior.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 request pair/C, materialization, source-evidence, real consumer/Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: complete pre-C closure remediation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`.
- Formal root: `bc7857492dec64a629ecb7684e6d307d146aca24`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only static core/test/SESSION. It closes all current ChatGPT+DS items: typed two-query records with timeout/rc/stdout/stderr/advertised value; typed authority absences and four designated paths; sealed structures, C admission consumption before freshness, typed byte readback verified internally, and producer-raw inverse patch witness. `unittest=6/6`, `py_compile`, `diff-check` PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 C/materialization/source-evidence/real I/O/child/GPU/training.

## 2026-09-15 — Review request: exact absence-closure remediation

- Formal root: `08a4dee0e85084a110f1c642513dd32583efb72e`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only CPU/static. Binds exact four V18 absence paths, output absence tuple, typed authority identities, and empty qualified authority-ref stdout semantics. Tests/py_compile/diff-check PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 C/materialization/source-evidence/real I/O/child/GPU/training.

## 2026-09-15 — Review request: sealed typed pre-C observation remediation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`.
- Formal root: `c2174dd00e11b96f7ff1b187a2ea84853bfd8f42`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no child/runtime code. `unittest=7/7 PASS`; `py_compile` and `git diff --check` PASS.
- Remediation focus: closes the complete same-pair ChatGPT/DS findings in one static core. `QueryFactV1` freezes and verifies raw stdout/stderr/advertised-V2 values with individual length/SHA identities; both output absences and all four V18 designated absolute paths are ordered typed `lexists=false` canonical raw records with predicate/boolean/length/SHA; `AUTHORITY_ARGV` now uses the frozen `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1` literal. New direct tests mutate every query and absence identity field and prove fail-close before consumer invocation.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 request pair/C, materialization, source-evidence, real consumer/Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: full inherited pre-C closure remediation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`.
- Formal root: `1bf4dc5315ac37a360e850dc5d0baf799287b58c`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no child/runtime code. This formal SHA was safely rebased onto the newly published prior ChatGPT review ledger, so prior `c2174dd` verdict is not reused. `unittest=8/8 PASS`; `py_compile` and `git diff --check` PASS.
- Remediation focus: one static closure now includes typed `.git`/config/local-V2 raw identities; all P0 root/path/blob/raw identities; ordered P1 injected records (`selection`, `config`, parser/bootstrap argv, bootstrap, bootstrap contract, outer, adapter); complete literal `ReplayBindingV1` plus ordered rows and owner-FD; and frozen cwd/index/evidence/output targets. Direct drift tests cover every added raw/source/binding/target field and fail before consumer invocation.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 request pair/C, materialization, source-evidence, real consumer/Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: exact authority-object binding remediation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`.
- Formal root: `6c4e395f38591c4b27a5627c184fc739af968669`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no child/runtime code. `unittest=9/9 PASS`; `py_compile` and `git diff --check` PASS.
- Remediation focus: resolves the complete same-pair ChatGPT/DS request changes. P0 now pins each raw length/SHA and requires computed Git blob OID equality; P1 pins all eight ordered source identities. `ReplayBindingV1` pins base SHA, owner pair, the exact ordered 8 parser and 8 source rows, plus `parser_argv_items` derived from and compared to the already pinned parser raw JSON. Foreign-but-self-consistent drift coverage exercises every P0/P1 category and binding literals, all before consumer invocation.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 request pair/C, materialization, source-evidence, real consumer/Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: consolidated ContractV05 pre-C closure

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`.
- Formal root: `8bc6e93547a5a3f7db541f3843a6d36a32d23181`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: cumulative root-only fixture/contract closure at `1d44e995` + `8bc6e935`: `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_pre_c_contract_matrix_v1.0.md`, `SESSION.md`, and `TODO.md`; no child/runtime code. `unittest=10/10 PASS`; `py_compile` and `git diff --check` PASS.
- Consolidated acceptance: follows `USER_DIRECTIVE_STAGE1_CONVERGENCE_2026-09-15.md` without adding a lateral Gate. `ContractV05` is the sole `rehearse_v05()` input; C01--C15 matrix covers P0/P1/replay literals, observations/query/absence/environment/targets, capability/verifier/canonical pair, exactly-once and zero-real-source-I/O. The replay-helper fixture is frozen in-memory gzip/base64 bytes and verifies `5582/8f55dc32...d5e82`; no `Path.read_bytes`, Git, network, source/data/cache or consumer call occurs. New sealed foreign-but-self-consistent drift matrix proves git/config/local-V2/query/P0/P1/binding/target freshness fails before consumer invocation.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 request pair/C, materialization, source-evidence, real consumer/Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: fixed authority-absence ContractV05 closure

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-PRE-C-REHEARSAL-CONSUMER-CPU-STATIC`.
- Formal root: `c99506295fed887a87670fc80fbdaf639baf5444`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only pre-C core/test/C01--C15 matrix plus state ledger; no child/runtime code. `unittest=11/11 PASS`; `py_compile` and `git diff --check` PASS.
- Remediation focus: closes the same-pair ChatGPT C08/C15 fixed-authority-ref finding in one class-wide pass. `AUTHORITY_REF` freezes `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`; both local and remote `AuthorityAbsenceV1` require exact target and predicate before their raw identity may be accepted. Tests mutate each target/raw/length/SHA into a foreign-but-self-consistent record and prove pre-consumer `closure_query` fail-close. Matrix C01--C15 now has exact expected and positive/negative witness columns.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_PRE_C_REHEARSAL_CONSUMER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: v0.5 request pair/C, materialization, source-evidence, real consumer/Git/network/source/data/cache I/O, child mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: request-instance recovery construction authority V20

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V20`.
- Formal root: `0ed2be7e27d7219f29f7d3601e6a3a0399ae6bfa`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v2.0.md` and `SESSION.md`; no runtime/child/config change. The prior ContractV05 root CPU/static Gate was closed separately at `c99506295fed887a87670fc80fbdaf639baf5444`; V20 neither reuses v1.8's permanently consumed C authority nor authorizes execution.
- Review focus: whether one future v0.5 request pair can be safely governed by a single full non-consuming pre-C rehearsal: injected opaque `PatchConsumerV1` ABI/no-call proof; C995 ContractV05 C01--C15 typed live snapshot; canonical JSON/Markdown/patch bytes and same-object strict-UTF-8 handoff; simulated capability/readback; and sealed plan. Verify C is exactly `freshness equality -> one opaque apply -> byte-for-byte readback -> hard stop`, with no C-time discovery/generation and terminal no-retry after any call. This is the user's requested consolidated recovery boundary, not a lateral field Gate.
- Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C, future request pair write, materialization, source-evidence, real consumer/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V21 sealed freshness-guard CPU/static implementation design

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-RECOVERY-DESIGN-V21`.
- Formal root: `27f188c6cd13db2e257dc2951b0b744b2ff3dd64`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_recovery_design_v2.1.md`, `SESSION.md`, and `TODO.md`; no runtime/child/config change. This is the single docs-only remediation authorized by complete V20 reviews: ChatGPT `REQUEST_CHANGES` requires a non-tautological frozen C-time freshness ABI; MM/DS approved V20. No real construction is proposed.
- Review focus: verify `FreshnessGuardV1`/opaque `FreshnessLeaseV1` resolve the exact V20 blocker without a lateral field Gate. Immutable facts stay sealed; mutable local facts/output absences are checked only by a pre-C-bound host guard; remote V2/authority queries are explicitly pre-C-only. Future `consume_once_v05(plan)` accepts no externally reconstructed `ClosureV1` and is strictly guard -> one opaque apply -> byte readback -> hard stop. Confirm the planned standard-library tests prove drift stops before apply, no C-time query/reconstruction occurs, and terminal no-retry is retained.
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_FRESHNESS_GUARD_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C, future request pair, materialization, source-evidence, real guard/consumer/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V21 freshness-guard CPU/static closure

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-FRESHNESS-GUARD-CPU-STATIC`.
- Formal root: `94030f90cc4de2d5b2c1dd60a412fb10768d71f9`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no child/runtime/config change. `unittest=11/11 PASS`; `py_compile` and `git diff --check` PASS.
- Review focus: `FreshnessGuardV1`/`FreshnessLeaseV1` are sealed and non-copyable; `consume_once_v05(plan)` no longer accepts arbitrary `ClosureV1`; guard `STALE`/`UNKNOWN` terminate before apply; FRESH retains one opaque apply, byte readback and no retry. No real I/O is present.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_FRESHNESS_GUARD_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C, request pair, materialization, source-evidence, real guard/consumer/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: freshness absence-domain remediation closure

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-FRESHNESS-GUARD-CPU-STATIC`.
- Formal root: `db6c4f93473e7ef58a294cff3fb8c692b100badd`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only pre-C module/test plus SESSION; no child/runtime/config change. This is the complete same-pair ChatGPT HIGH remediation: lease domain now deterministically binds git/config/local-V2, two output absences and four designated absences by name/path/predicate/length/SHA. `unittest=12/12 PASS`; `py_compile` and `git diff --check` PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_FRESHNESS_GUARD_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C, request pair, materialization, source-evidence, real I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: causal absence-drift remediation closure

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-FRESHNESS-GUARD-CPU-STATIC`.
- Formal root: `37eca204a2144d9e191c4f995d881749a9a9d218`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only unittest evidence remediation; no production/child/runtime/config change. The fake guard now derives FRESH/STALE from sealed-vs-simulated-live domain comparison. It sweeps both output and all four designated absence identities, proves consumer count zero before apply, and proves a second call is `already_consumed`. `unittest=12/12 PASS`; py_compile/diff-check PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_FRESHNESS_GUARD_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C, request pair, materialization, source-evidence, real I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V22 future request-pair construction authority

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-CONSTRUCTION-AUTHORITY-V22`.
- Formal root: `36f5216428a28027ac4d33c17ba4456fb93eb359`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only construction-authority design; no runtime/child/config change and no construction executed. It inherits the closed C01--C15/9-entry guard contract and freezes one full rehearsal followed only by `FRESH -> one opaque apply -> exact readback -> hard stop`.
- Requested verdict: `APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C/request pair before same-pair approval, materialization, source-evidence, real I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V23 exact-plan non-consuming pre-C authority

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-EXACT-PLAN-PRE-C-AUTHORITY-V23`.
- Formal root: `04fd92eea3506ffe1de0ef8cce12377f81e2e75f`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only v2.3 authority remediation plus `SESSION.md`/`TODO.md`; no real pre-C/C or request-pair construction executed. It directly addresses V22 ChatGPT HIGH by authorizing only one real non-consuming pre-C that seals the actual PatchConsumerV1, FreshnessGuardV1 and post-write verifier provider/module/path/blob/callable/ABI/transport identities. It then hard-stops for one exact sealed-plan review; it does not add field/path serial Gates.
- Review focus: verify that the two-stage model closes the authority gap without weakening C01--C15, nine-entry freshness domain, remote-pre-C-only rule, canonical bytes/paths, same-object patch handoff, no-retry semantics, or the future four-step C. Confirm V23 cannot authorize C, materialization, source evidence, child mutation, GPU or training.
- Requested verdict: `APPROVE_TO_EXECUTE_R09_B_TTT_V035_STAGE1_V17_EXACT_PLAN_PRE_C` or `REQUEST_CHANGES(file:line)`.
- Forbidden: C/request-pair write, materialization, source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V24 live-plan continuity authority

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-REQUEST-INSTANCE-LIVE-PLAN-CONTINUITY-AUTHORITY-V24`.
- Formal root: `936e0fb09a2fe529d5aec8b9e42c79ce54a6fec9`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only v2.4 docs remediation plus `SESSION.md`; no execution. This answers V23 ChatGPT HIGH: the non-copyable sealed plan, opaque lease and host session are a same-lifetime triple; the review record binds all three identities; only a resume-only entrypoint can pass that same live object to C; death/loss/replacement/drift invalidates authority, with no reconstruction.
- Review focus: verify this proves reviewed-record to live-plan continuity without weakening C01--C15, nine-entry freshness, immutable bytes/paths, future C atomicity, or terminal no-retry. Confirm it remains docs-only and does not authorize real pre-C/C.
- Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C/request-pair write, materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V25 live-plan continuity CPU/static implementation design

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`.
- Formal root: `d1a25398d1a5ea563c862c4e6ebbf7f702f1d051`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only docs design; proposed future change is limited to existing pure-memory pre-C module/unittest. It implements V24’s approved session/plan/lease same-instance contract, pending quiescence, resume-only identity proof and terminal invalidation; no real host capability or I/O.
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C/request pair/materialization/source evidence, child/runtime/config, GPU/CUDA/torchrun/training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V25 approval/snapshot remediation closure

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25-REMEDIATION`.
- Formal root: `9c027a346320b0cb8e8445ada1e1a277efb0b875`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only pure-memory module/unittest plus SESSION. Approval/state and binding moved out of the session object into live registries; binding freezes an identity-only full authority snapshot and resume verifies it before owner release. Tests include base-mutation approval forgery and capability callable drift, both zero-apply. `19/19 PASS`; py_compile/diff-check PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C, request pair, materialization, source-evidence, I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V25 live-plan continuity CPU/static closure

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25`.
- Formal root: `9a3c9c3fb2f6184eff8d651fae4f48a624afe040`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only existing pre-C module and its stdlib unittest. Implements `LivePlanSessionV1` / opaque lease, pending direct-consume rejection, same live-plan resume-only handoff and terminal identity failure. `unittest=14/14`, `py_compile`, `git diff --check` PASS; no I/O.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-15 — Review request: V26 host-owned continuation boundary design

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-HOST-OWNED-CONTINUATION-BOUNDARY-DESIGN-V26`.
- Formal root: `ed5bd4c5a5261ece1950362f8346d8834dd2b990`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_host_owned_continuation_boundary_design_v2.6.md`, `SESSION.md`, and `TODO.md`; no child/runtime/code change. `git diff --check` PASS.
- Context: user explicitly chose an independent host-owned capability boundary after the V25 review proved that same-interpreter module registries are caller-mutable. V26 replaces that implementation premise with a distinct low-privilege Stage1Host, private anonymous IPC, host-only approval/binding/latch and a detached complete ReviewRecordV26. It explicitly rejects a same-interpreter fallback if OS isolation is unavailable.
- Review focus: verify that the trust model, lifecycle and complete record close both V25 HIGHs in one pass: no caller-reachable mutable authority; approval only through orchestration attestation; detached full consumer/guard/verifier/C01--C15/freshness/query/absence/replay record; all client tamper paths terminalize before freshness/consumer/apply. Confirm staged implementation starts only with a fake-host CPU/static protocol and that real host/IPC integration remains a separate review.
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C, request pair/materialization/source-evidence, real host process/IPC/apply_patch, child/runtime/config change, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V27 host-owned continuation boundary remediation

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-HOST-OWNED-CONTINUATION-BOUNDARY-DESIGN-V27`.
- Formal root: `94c436d50d2caded43410052e720fbdbf3f37b7b`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only V27 docs design, SESSION/TODO; no code/child/runtime. V26 complete three-party review authorized one docs-only remediation. `git diff --check` PASS.
- Remediation: explicitly maps V24 continuity to host-private `HostSession/LivePlanEnvelope/HostLease`; makes ReviewRecord non-reconstructive; binds ReviewApproval to host generation/session/plan/lease/binding/nonce/counter; freezes atomic serial `PENDING_REVIEW -> APPROVED -> CONSUMING -> TERMINAL` before freshness/apply.
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: fake-host/real host/IPC/pre-C/C/request pair/materialization/source-evidence/child/GPU/training.

## 2026-09-15 — Review request: V27 fake-host CPU/static implementation

- Formal root: `2b7429f2a1eb6cd50f5c5da15e3691a5128f50c1`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only `tools/psm_wma/stage1_host_boundary.py` and unittest plus SESSION/TODO. CPU=4/4, py_compile/diff-check PASS. No process/IPC/filesystem/consumer.
- Review focus: host-private state, generation-bound approval, atomic terminal resume and at-most-one apply fake-host conformance.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C/request pair/materialization/source evidence, child/runtime/config, GPU/CUDA/torchrun/training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V25 live-plan continuity remediation closure

- Formal root: `079186e4c9b6ce1c221447119397c03ae11a8188`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only two-file remediation of all V25 final feedback: terminal retirement on close/invalidation, duplicate live-owner rejection, read-only audit witness. `15/15` stdlib tests, py_compile and diff-check PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-15 — Review request: V25 approval-state remediation closure

- Formal root: `ccada85a50be8e541d8c618752986e2cf088f05e`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only state-machine remediation: explicit pending/approved/consumed states and `approve(identity)` transition; pending public consume remains blocked; no I/O. `15/15` stdlib tests, py_compile, diff-check PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-15 — Review request: rebased V25 internal-entry remediation closure

- Formal root: `14d059d940b1b9a6d1af59105e2a38c90c97c78a`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only rebased V25 internal-entry remediation; adds live lease-token verification to the C primitive and direct bypass witness. `15/15` tests, py_compile, diff-check PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-15 — Review request: V25 module-entry removal closure

- Formal root: `1e1e2909476dc6b154a37e5ec8592355031ab74a`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only removal of module-level internal C callable; session resume now uses the sole public route after releasing live ownership. `15/15` tests, py_compile, diff-check PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-15 — Review request: rebased V25 session sealing closure

- Formal root: `23087f8274567a99ee9751a63ba105f48c2f1845`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- Scope: root-only session sealing remediation: immutable live bindings plus copy/serialize/mutation negative witnesses; `16/16` CPU tests, py_compile, diff-check PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-15 — Review request: V25 sealing and triple-binding remediation closure

- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LIVE-PLAN-CONTINUITY-CPU-STATIC-V25-REMEDIATION`.
- Formal root: `0a36cdd85a97289ec6a2ff6ce0e62d8fe7419090`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only `tools/psm_wma/stage1_v17_pre_c_rehearsal.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no child/runtime/config change. This is the complete response to V25 ChatGPT `REQUEST_CHANGES`: removes caller-writable/deletable `_locked` and dead `_LIVE_TOKENS`; creates a non-copyable, ordinary-set/delete sealed creation-time session/plan/lease binding with token-backed SHA-256 digest; exposes triple identities plus digest in the read-only audit record; and verifies the binding before `resume_once()` releases the original plan to the sole C primitive.
- Evidence: all capability/guard/lease/continuation/retirement authority fields are ordinary-set/delete fail-close; tests cover unlock/rebind/delete, plan/lease/session binding drift, deepcopy/serialization, audit digest, and zero apply before rejected resume. `python -m unittest tools.psm_wma.test_stage1_v17_pre_c_rehearsal` = `18/18 PASS`; `py_compile` and `git diff --check` PASS.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_STAGE1_V17_LIVE_PLAN_CONTINUITY_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real pre-C/C, request pair, materialization, source-evidence, real host/consumer/guard/Git/network/source/data/cache I/O, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V27 fake-host CPU/static remediation closure

- Gate: `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`.
- Formal root: `c4a3b985cfd8a576ab114431f8ee2ae4df6f2681`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only `tools/psm_wma/stage1_host_boundary.py`, its stdlib unittest, `SESSION.md`, and `TODO.md`; no real process, IPC, filesystem, consumer, child/runtime/config, GPU or training change. CPU=`8/8 PASS`; `py_compile` and `git diff --check` PASS.
- Remediation: complete V27 fake-host conformance in one pass. The detached `ReviewRecordV27` now has exact ordered typed identity categories for consumer/guard/verifier, C01--C15, freshness/query/absence/replay/targets and descriptor/source/argv rows; its canonical digest binds exact Gate/root/child. Exact session-bound approval is only minted through a clearly separate test-only privileged orchestration harness. `RLock` serializes approval and `APPROVED -> CONSUMING`; tests cover every category drift, malformed/reordered records, all attestation fields, session/generation replay, parallel resumes and consuming terminal branches.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real Stage1Host/OS identity, process/IPC, real pre-C/C/request pair/materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: V27 fake-host canonical-record remediation closure

- Gate: `G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC`.
- Formal root: `517bb9790985a2001f6778ad64ccfbe7fe5bce3d`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Scope: root-only `tools/psm_wma/stage1_host_boundary.py`, its stdlib unittest, and `SESSION.md`; no real process/IPC/filesystem/consumer/child/runtime/config/GPU/training change. CPU=`8/8 PASS`; `py_compile` and `git diff --check` PASS.
- Remediation: each of the 12 detached ReviewRecord categories now has fixed field order/count/identity grammar, including full consumer/guard/verifier provenance, C01--C15, 9-entry freshness, query/absence/replay/targets and descriptor/source/argv identities. Host state stores an independent private immutable snapshot; client receives a detached audit copy. Privileged attestation schema-validates and recomputes canonical record digest against the private snapshot; resume consumes only private state. Tests causally cover every field drift, per-category malformed grammar, pre/post-attestation `object.__setattr__` mutation, replay, atomic parallel resume and consuming failures.
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_HOST_OWNED_CONTINUATION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Forbidden: real Stage1Host/OS identity, process/IPC, real pre-C/C/request pair/materialization/source-evidence, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1.

## 2026-09-15 — Review request: pragmatic immutable-commit Stage-1 v0.5 exact request

- Gate: `G0-R09-B-TTT-V035-STAGE1-PRAGMATIC-REQUEST-PAIR` under `USER_OWNER_OVERRIDE_STAGE1_PRAGMATIC_EXECUTION_2026-09-15.md`.
- Formal root: `44aa8760630751668a5ec340ef017575c65e311d`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4` (unchanged).
- Formal scope: root-only v0.5 JSON/Markdown request pair, pure byte emitter/unittest, and TODO. Candidate materialization root is explicitly `db6c4f93473e7ef58a294cff3fb8c692b100badd`, not historical `08d5828...`. `unittest=5/5 PASS`, `py_compile`, `diff --check`, pair byte/SHA/git-blob verification and unified-patch SHA all PASS.
- Review focus: independently verify the request's exact root/child, four frozen tool blobs, mechanically retargeted launcher/argv/bootstrap identities, exact FD input bytes, six-key environment, same-round `.git`/config/remote V2/fixed-ref/absence preflight facts, and JSON/Markdown binding. Confirm it is reproducible and that its requested next authority is limited to exactly one Stage-1 materialization attempt.
- Requested verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`.
- Forbidden: source collection/receipt publication beyond the materialization receipt, child/runtime/config mutation, GPU/CUDA/torchrun, training/evaluation/inference/LIBERO4IN1. V25/V26/V27 host/session/IPC continuity is superseded by the Owner Override and out of scope.
## 2026-09-16 — GPT runtime-failure diagnosis request

- Gate: `G0-R09-B-TTT-V035-STAGE1-RUNTIME-FAILURE-DIAGNOSIS`。
- Formal root: `5e59eb06dc323cdcf71fb4fbc3092071648dae30`；child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- 现象：MM/DS 已批准该 pair 的一次 materialization；执行时外层打印冻结 `bootstrap exec argv`，随后 bootstrap 以 `bootstrap-invocation`、退出码 1 终止；未生成 authority evidence/ref。CPU 静态测试 `24/24 PASS`。
- 诊断边界：不得执行真实 materialization、source-evidence、GPU、torchrun、训练/评测/推理。请 GPT 审核失败证据与最小修复方案，重点判断 bootstrap ABI/FD 继承/解释器版本守卫的真实根因，并给出 `file:line` 修改建议及修复后验收条件。
- 请求 verdict：`APPROVE_TO_DIAGNOSE_AND_REMEDIATE_STAGE1_RUNTIME` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-16 — Review request: Stage-1 v0.6 rebuilt exact pair (MM/DS active roster)

- Gate: `G0-R09-B-TTT-V035-STAGE1-PRAGMATIC-REQUEST-PAIR`；ChatGPT 暂停，不纳入本轮推进门。
- Formal root: `e67a57ffa2ec6f8cdeb2e1299ecdc4387f6aeff9`；child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- Scope: new v0.6 JSON/Markdown pair rebuilt by the approved regular-interpreter fix (`/opt/conda/bin/python3.11`), fresh clean suffix `a1c4e7d`; CPU static tests 5/5, py_compile and diff-check PASS.
- Review focus: exact pair identity, all launcher/parser/bootstrap/contract and preflight bindings, fresh suffix/absence facts, and one-shot materialization boundary. No materialization, source-evidence, GPU or training is authorized by this request.
- Requested verdict: `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT` or `REQUEST_CHANGES(file:line)`。

## 2026-09-16 — Review request: Stage-1 v0.6 candidate-root correction

- Formal review commit: `7ca2ecf7966c09489f17f993f88963c12995943d`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- 修复 MM 指出的 `formal_root` 绑定错误：pair 内候选物化根恢复为冻结值 `d5df7ef0988a9277bc657384fe8462dcdce2bca1`；仅更新 JSON/Markdown identity。
- CPU static builder tests 5/5 PASS；请求 MM/DS 重新核验 exact pair。ChatGPT 暂停；禁止 materialization/source-evidence/GPU/training。

## 2026-09-16 — Review request: Stage-1 v0.7 FD8 inheritance fix

- Formal review commit: `68fc12c45cb85bd3acbf7e59c03419c203b78ca4`；child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- Root cause fix commit `e52e14b9…` makes bootstrap owner FD8 inheritable across `execve`; v0.7 pair rebuilt with candidate root `e52e14b9…`, clean suffix `a1c4e7e`.
- CPU static builder tests 5/5 PASS；请求 MM/DS exact-pair final verdict。ChatGPT 暂停；禁止 materialization/source-evidence/GPU/training。

## 2026-09-16 — Review request: Stage-1 v0.8 fresh evidence path

- Formal review commit: `bed4c4a8a45aa451e70717ec6e06aa96e9a51d3b`；child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- 修复：builder 现将 `--evidence-path` 绑定到全新 `authority_root_materialization_evidence_a1c4e7f.json`，并以 `fd2feba7…` 候选根重建 pair；保留 FD8 inheritable 修复。
- CPU static builder tests 5/5 PASS；请求 MM/DS exact-pair final verdict。ChatGPT 暂停，禁止 materialization/GPU/training。

## 2026-09-16 — Stage-1 pair construction approval request

- Gate：`G0-R09-B-TTT-V035-STAGE1-REQUEST-PAIR-CONSTRUCTION`。
- Formal root：`8f170771e7a351ba99a3d656d2dc8d100e0f61e6`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 已完成：独立 producer CLI、事务发布核心、环境 allowlist；producer+builder `10/10 PASS`，`py_compile` 与 `git diff --check` PASS。
- 请求范围：仅批准一次使用明确冻结 payload 生成并验证一份新的 JSON/Markdown request pair；不批准 materialization、authority ref、source-evidence、GPU、torchrun、训练、评测或推理。
- 验收重点：producer 不修改 builder 纯函数合同；拒绝 divergent/symlink/secret environment；发布失败回滚；输出 byte/SHA/blob/pair identity 可复核。
- 请求 verdict：`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-16 — Stage-1 v1.2 exact pair construction review

- Gate：`G0-R09-B-TTT-V035-STAGE1-REQUEST-PAIR-CONSTRUCTION`。
- Formal root：`7796d054daac2d99713e57df6ebc870cf9be37e3`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- Pair：`docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v1.2.json`（38852 bytes，SHA-256 `cfd3c1de8f265d15d9b88a38c58ee079475fa3fed2a21691368fac1f5d202833`）及对应 Markdown（340 bytes，SHA-256 `d21da348d36fd168803b382dfbb72cbf31edc2c8f8c29376b78a274387cc260e`）。
- 已通过 `verify_pair`、Git blob identity、helper environment 非密校验；producer/builder CPU 测试 10/10 PASS。
- 请求范围：仅审核该 exact pair 的构造完整性并批准一次 pair construction follow-up；不授权 materialization、authority ref、source-evidence、GPU、torchrun、训练、评测或推理。
- 请求 verdict：`APPROVE_TO_CONSTRUCT_R09_B_TTT_V035_STAGE1_V17_REQUEST_INSTANCE` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-16 — GPT 建议请求：恢复 Stage-1 推进路径

- 当前根仓提交：`b57ad447c90317d48a21132f2d249ce9608c48e9`；child/Gitlink：`93a89ba61306d840a008813f62f26a34d54850f4`。
- 背景：旧 authority materialization 因隔离 Git 子进程缺少凭据在 `remote_cas` 失败；随后已提交 `/usr/bin/gh auth git-credential` 的最小环境绑定，并同步 request-pair builder 的 canonical environment。旧 pair 不能复用。
- 当前卡点：需要基于新 root 重新生成 byte-exact request pair，但仓库没有可直接执行的受控 pair producer；交接要求禁止手工拼接、临时脚本写入或复用旧 pair。
- 请 GPT 仅提供处理建议，不修改代码、不执行 materialization、不写 authority ref、不启动 GPU/训练。请明确回答：应如何在现有详细设计下补齐 producer；如何冻结 helper 环境而不泄露凭据；需要哪些 CPU/static witness、pair 字段和审核门，才能恢复 materialization→source evidence→LIBERO4IN1 latent cache 训练。
- 建议请给出可执行的最小步骤、涉及文件/行号、失败回滚语义和验收证据；不要给出绕过审核或 no-retry 约束的方案。
# 2026-09-16 — Stage-1 v1.5 materialization review request

- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-V15`
- Formal root: `cb6b675edc2ef4b019c1be4901c062a598fec271`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Request pair: `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v1.5.json` / `.md`
- Pair SHA-256: JSON=`4553e21d5211d36aeb3a7020250fe2fa8e8f6c3350466377d40034c8391bf814`; MD=`f57ea3a60b72321b1756c62d349371aa7d1ac5d5b9c3af324be267ffdd15c261`; clean suffix=`e8c7b2a5`.
- Evidence: prior v1.3 execution failed at `remote_cas` and rolled back; GitHub permission/ruleset read-only checks passed. v1.5 is a fresh pair and must be treated as one-shot.
- Requested verdict: `APPROVE_TO_MATERIALIZE` or `REQUEST_CHANGES(file:line)` for exactly one Stage-1 authority-root materialization. If approved, allow only the authority-root/local and fixed-ref transaction; forbid retry, child/runtime/config mutation, source-evidence, GPU/CUDA, training/evaluation/inference.
- Reviewers: frozen MM=`mm:0.0`, DS=`ds:0.0`, ChatGPT via exact formal-pair review file.

## 2026-09-16 — Stage-1 v1.6 materialization review request

- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-V16`
- Formal root: `cb6b675edc2ef4b019c1be4901c062a598fec271`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- v1.5 `REQUEST_CHANGES` 已采纳：v1.5 的 launcher 是半重建状态；v1.6 改由真实 `rebuild_launcher()` 从 formal tree bytes 重建。
- Pair: `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v1.6.json` / `.md`；JSON SHA=`cf72d5be120923dec093fcdea56b5c130563efc9f4a40fd71674c09b1080419`; MD SHA=`228e534ddb521b53cf37eeb7c58a54ab1ab82ef3ffa53f48c13bba09f03d5e18`; suffix=`e8c7b2a6`。
- Requested verdict: `APPROVE_TO_MATERIALIZE` 或 `REQUEST_CHANGES(file:line)`；批准仅限一次 authority-root materialization，禁止 retry、child/runtime/config、source-evidence、GPU/训练/评测/推理。

## 2026-09-16 — Stage-1 v1.7 materialization review request

- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-V17`；ChatGPT advice-only，本轮冻结 MM=`mm:0.0`、DS=`ds:0.0`。
- Formal root: `7d7ba235ec5be0208aedac2f9b2ed11f755d9ca6`；child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- v1.6 已在 `remote_cas` 因 thin-pack 上传失败并完整回滚；只读诊断证明同一对象使用 `git push --no-thin` 可创建并删除 authority ref。最小修复已写入 formal root 的 `tools/psm_wma/materialize_immutable_source_authority_root.py`，push/delete 均显式使用 `--no-thin`。
- v1.7 pair: `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v1.7.json` / `.md`；JSON SHA-256=`10eaa1f209633bb6830d7678c305aa422b9ec558e8c1264f8dba065d36ed625b`；MD SHA-256=`3cdb5480823ac2d385468e927fc133cec5cd38ca8ca715b66296bf80c9ead986`；clean suffix=`e8c7b2a7`。
- 已通过 pair producer/launcher 重建、JSON/Markdown identity 与当前 formal tree 绑定；请求仅批准一次 Stage-1 authority-root materialization。
- 允许范围：按 exact pair 执行一次 authority-root/local CAS 与固定 authority ref 事务，生成 materialization evidence。禁止 retry、child/runtime/config 修改、source-evidence、GPU/CUDA、torchrun、训练/评测/推理；失败必须保留证据并回滚。
- 审核重点：确认 `--no-thin` 对 remote CAS push/delete 的最小修复、lease/readback/rollback 不变、exact root/child/pair 绑定及 one-shot 边界。
- Requested verdict: `APPROVE_TO_MATERIALIZE` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-16 — Source collection real-binding CPU/static review request

- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-REAL-ADAPTER-CPU-STATIC`；冻结 MM=`mm:0.0`、DS=`ds:0.0`；ChatGPT advice-only。
- Formal root: `e2c8337b`（完整 SHA 以远端 exact tree 为准）；child/Gitlink=`93a89ba61306d840a008813f62f26a34d54850f4`。
- 最小修改：`tools/psm_wma/immutable_source_collection.py` 的 `main()` 将已绑定 argv/FD/authority/lineage 接入既有 `collect_synthetic()` injected seam；`NativeCollectionGit` 纳入同一 scoped `gh auth git-credential` 与 `GH_CONFIG_DIR`，供 fixed-ref lookup。缺少绑定仍 fail-closed。
- 验证：collection unittest `56/56 PASS`、py_compile、diff-check PASS。请求仅审核 CPU/static binding 与 identity/禁止范围；不授权真实 source/checkpoint I/O、collection/receipt publication、child、GPU、训练或评测。
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_REAL_ADAPTER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-16 — Stage-1 v2.0 materialization review request

- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-V20`；ChatGPT advice-only；冻结 MM=`mm:0.0`、DS=`ds:0.0`。
- Formal root: `342b7ccb3abe36462ad5eb233f50ce979aab5207`；child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- v1.9 已按 DS 意见废止：其 pair 手工注入 `GH_CONFIG_DIR`，但 canonical builder 未包含该字段，造成 builder/file identity 不一致。v2.0 已将 `GH_CONFIG_DIR=/root/.config/gh` 纳入 builder 正式 environment contract，并由 producer allowlist 校验；bootstrap、adapter env 与 `--no-thin` 同步保留。
- v2.0 pair JSON SHA-256=`b377972c540790a5b95baa5a950684d56d027f69a11960c3e54acdfb2fae40e6`；MD SHA-256=`3b7d69c6be9cdf9b56d9ea3e2aecf3159191360fb994776e447e6881d9fc8cc1`；suffix=`e8c7b2b0`。
- 已通过 builder/producer `10/10`、py_compile、diff-check；请求仅批准一次 materialization，禁止 retry、source-evidence、child/runtime/config、GPU、训练/评测/推理。Requested verdict: `APPROVE_TO_MATERIALIZE` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-16 — Stage-1 v1.9 materialization review request

- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-V19`；ChatGPT advice-only；冻结 MM=`mm:0.0`、DS=`ds:0.0`。
- Formal root: `a5d15f5e27d0d7268aec2f2a020baa2df5dd9f34`；child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- v1.8 被 DS `REQUEST_CHANGES`：bootstrap ENV 修复不影响实际 remote CAS 的 adapter env，且未验证无 HOME 时 helper。诊断已证实：无 `HOME/GH_CONFIG_DIR` 时 helper 返回 1；`GH_CONFIG_DIR=/root/.config/gh` 时返回 0；同 argv/`--no-thin` 本地 bare remote 成功。
- v1.9 最小修复：adapter bootstrap 与 `NativeAuthorityGit.env` 绑定非秘密 `GH_CONFIG_DIR=/root/.config/gh`；pair producer allowlist 接受该固定路径；保留 `--no-thin`。pair JSON SHA-256=`2c5c43cdefd47ac8935e26c2c2c5521ce45569e1206350237f9fb057066c8e9c`；MD SHA-256=`beddb5c5f4c2aeba98a7edd7ce4b3e3e87cf5e96947d553b034684f23046fd60`；suffix=`e8c7b2a9`。
- 请求仅批准一次 authority-root materialization；禁止 retry、source-evidence、child/runtime/config、GPU、CUDA、torchrun、训练/评测/推理。Requested verdict: `APPROVE_TO_MATERIALIZE` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-16 — Stage-1 v1.8 materialization review request

- Gate: `G0-R09-B-TTT-V035-STAGE1-AUTHORITY-ROOT-MATERIALIZATION-V18`；ChatGPT advice-only；冻结 MM=`mm:0.0`、DS=`ds:0.0`。
- Formal root: `35837c584b48315f8cda2c346d7e40ec08470942`；child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`。
- v1.7 唯一物化已在 `remote_cas` 失败并完整回滚。根因已定位为 bootstrap 丢失 `GIT_CONFIG_COUNT/GIT_CONFIG_KEY_0/GIT_CONFIG_VALUE_0`，导致已授权 `gh auth git-credential` 未传入 adapter；v1.8 将该三项纳入 bootstrap 冻结 ENV，同时保留 `--no-thin`。
- v1.8 pair: `docs/build/PSM-WMA_Local_Memory_v0.3.5_stage1_v17_request_instance_v1.8.json` / `.md`；JSON SHA-256=`6e16e0736a45f1061ed5f1bc8b895bbe13e4115d65b185536c37b7741b8bd0df`；MD SHA-256=`a1fb9079f3b6d7db3881f95d3941289f0d61c7f55b1689f45b2b045b647be476`；clean suffix=`e8c7b2a8`。
- 请求范围：仅批准一次 v1.8 authority-root/local CAS 与固定 authority ref 事务；失败保留 evidence 并回滚。禁止 retry、child/runtime/config 修改、source-evidence、GPU/CUDA、torchrun、训练/评测/推理。
- 审核重点：exact root/child/pair 绑定、bootstrap helper 环境传递、`--no-thin`、lease/readback/rollback 与 one-shot 边界。
- Requested verdict: `APPROVE_TO_MATERIALIZE` 或 `REQUEST_CHANGES(file:line)`。
# 2026-09-16 — Source-evidence producer/closure implementation design review

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-IMPLEMENTATION-DESIGN`
- Formal root: `b1ae3b9685631204680f03eb421c85bff5d8cffa`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_implementation_design_v0.1.md`
- Scope: 仅审核既有 collection seam 上 record/package/witness canonical bytes、identity、one-shot handoff 的 CPU/static implementation 设计；不得授权真实 source/checkpoint/manifest/data/cache I/O、record/publication 写入、child/runtime 修改、GPU、CUDA、torchrun、训练、评测或推理。
- Acceptance: exact schema/key/digest/non-circular binding、raw-byte identity、one-shot handoff 与 fail-closed 矩阵；后续实现仅限 `tools/psm_wma/immutable_source_collection.py` 及其测试。
- Requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
- Reviewers: frozen MM=`mm:0.0`、DS=`ds:0.0`；ChatGPT exact formal-pair review（advice-only）。

# 2026-09-16 — Source-evidence producer/closure CPU/static implementation closure review

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-CPU-STATIC-IMPLEMENTATION`
- Formal root: `3bf2427c28e69bb97c2bb2d192bee8c963471fc5`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Changed files: `tools/psm_wma/immutable_source_collection.py`, `tools/psm_wma/test_immutable_source_collection.py`；bookkeeping `TODO.md`/`SESSION.md`。
- Evidence: 57/57 collection tests PASS；target files `py_compile` PASS；`git diff --check` PASS。
- Scope: record/package/witness canonical-byte construction and validation、digest/identity/non-circular binding、one-shot in-memory handoff；未接入 native main，未打开 source FD，未写 record/publication，未修改 authority ref/child/runtime，未使用 GPU/训练。
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
- Reviewers: frozen MM=`mm:0.0`、DS=`ds:0.0`；ChatGPT exact formal-pair review（advice-only）。

# 2026-09-16 — Stage-2 source-evidence request instance schema design review

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-SCHEMA-DESIGN`
- Formal root: `0442c66f82450fd94f4aa027f4a31b3a05f2a24f`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_request_instance_schema_v0.1.md`
- Scope: 仅审核 Stage-2 instance exact top-level keys、资产字段来源、same-round identity 与 execution/禁止范围；不创建 instance，不执行 source/record/publication I/O，不启用 GPU 或训练。
- Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_SCHEMA` 或 `REQUEST_CHANGES(file:line)`。
- Reviewers: frozen MM=`mm:0.0`、DS=`ds:0.0`；ChatGPT exact formal-pair review（advice-only）。

# 2026-09-16 — Stage-2 request instance schema remediation review

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-SCHEMA-DESIGN`
- Formal root: `771633764096d7d2af2ff12d828bebc174daa6d1`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Remediation: 补齐 authority/source/executor/producer/record/receipt/publication/root_audit/preflight/execution 的 exact keys 与类型；定义顶层 sha256 排除自身的 preimage；引用既有批准 schema/formal roots；明确 producer 绑定已关闭 CPU/static helper identity。
- Scope: docs-only；不创建 instance，不执行 source/record/publication I/O，不启用 GPU/训练。
- Requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_SCHEMA` 或 `REQUEST_CHANGES(file:line)`。
- Reviewers: frozen MM=`mm:0.0`、DS=`ds:0.0`；ChatGPT exact formal-pair review（advice-only）。

# 2026-09-16 — Source-evidence producer/closure remediation closure review

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-CPU-STATIC-IMPLEMENTATION`
- Formal root: `ec6fd6b1650d9372034c6cb386c74748e51a6326`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Remediation: receipt-bound config/descriptor digest checks；package/witness symmetric verifier；non-copyable/non-serializable one-shot `SourceEvidenceHandoff` and fixture。
- Evidence: 57/57 tests PASS；py_compile PASS；git diff-check PASS；native main unchanged；no real source I/O/publication/GPU/training。
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
- Reviewers: frozen MM=`mm:0.0`、DS=`ds:0.0`；ChatGPT exact formal-pair review（advice-only）。

# 2026-09-16 — Source-evidence producer/closure final remediation review

- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-CPU-STATIC-IMPLEMENTATION`
- Formal root: `7b3bf58b27a55b1220b86eeeccb1db5659dd0500`
- Child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Remediation: `produce_source_package()` now invokes `verify_source_evidence_record(record_raw, receipt)`；added negative fixture rejecting record↔receipt digest drift；57/57 tests PASS；py_compile/diff-check PASS。
- Scope remains CPU/static only；no native-main integration、source/record/publication I/O、authority ref、child/runtime、GPU or training。
- Requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。
- Reviewers: frozen MM=`mm:0.0`、DS=`ds:0.0`；ChatGPT exact formal-pair review（advice-only）。
## 2026-09-16 — G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-REQUEST-INSTANCE-CONSTRUCTION-IMPLEMENTATION-DESIGN

- formal root: `7e587e1f00150ba74558e818ebac9ed036d2e42f`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_request_instance_construction_implementation_design_v0.1.md`
- scope: docs-only implementation design review. It freezes same-round identity observation, exact-schema canonicalization, JSON/Markdown byte readback, terminal partial-residue policy, and hard stop.
- evidence: `git diff --check` PASS; no instance created; no checkpoint/manifest/data/cache payload read; no source/record/publication I/O; no GPU/CUDA/torchrun/training.
- requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — request-instance writer remediation DS review

- formal root: `944c8119b9fda15d4edc7475e7384cbb0712253f`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- remediation: evaluated DS feedback; accepted fail-closed exact identity checks, short-write handling, structured mkdir failure, residue fields and Markdown sibling SHA; rejected writer-owned SESSION writes and fixed-path enforcement for the CPU/static writer boundary.
- evidence: 6/6 unittest PASS, py_compile PASS, git diff --check PASS.
- scope: DS-only review per user instruction; temporary fixture only; no real instance, source I/O, GPU/CUDA/torchrun or training.
- requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_WRITER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — ObservationBundle provider end-to-end remediation DS review

- formal root: `78fdacb18578222cfc8f6fb794f61cacf253d455`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- remediation: added unique `observe_and_assemble` entry; it requires same-round read-only Git observation, invokes explicit bundle builder, and immediately validates the flat bundle through the existing constructor; missing/failed Git or builder is `BLOCKED_AUTHORITY_NOT_CLOSED`.
- evidence: 17/17 joint unittest PASS, py_compile PASS, git diff --check PASS; no real source/cache payload reads or instance writes.
- DS-only per user instruction. requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_OBSERVATION_BUNDLE_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — ObservationBundle provider CPU/static implementation DS review

- formal root: `7786d2cdb8e54e3baebc9b887b02a99f6ccb3a98`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- implementation: `observe_source_evidence_bundle.py` provides no-follow file identity/fd hash, root/target snapshot, sanitized environment SHA and fail-closed errors; no payload reads or writes.
- evidence: 10/10 joint unittest PASS, py_compile PASS, git diff --check PASS; temporary fixtures only.
- DS-only per user instruction; forbidden: real instance write, source I/O, GPU/CUDA/torchrun and training.
- requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_OBSERVATION_BUNDLE_PROVIDER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — ObservationBundle provider constructor assembly DS review

- formal root: `57aef1eafa636ece55f68aa05c6e3db85e51ea51`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- remediation: connected `assemble_constructor_bundle` to the existing constructor; it requires the complete flat top-level bundle, forces `sha256=""`, returns canonical parsed output, and maps missing/invalid contract to `BLOCKED_AUTHORITY_NOT_CLOSED`.
- evidence: 15/15 joint unittest PASS, py_compile PASS, git diff --check PASS; no real source/cache payload reads or instance writes.
- DS-only per user instruction. requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_OBSERVATION_BUNDLE_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — ObservationBundle provider remediation DS review

- formal root: `134a1f44e80bd1d359f81cd156872b8ea4623d6c`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- remediation: added ten-section contract, `BLOCKED_AUTHORITY_NOT_CLOSED`, read-only Git metadata (HEAD/clean index tree/ref/blob OID), and fail-closed metadata combination.
- evidence: 12/12 joint unittest PASS, py_compile PASS, git diff --check PASS; no real source/cache reads or instance writes.
- DS-only per user instruction. requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_OBSERVATION_BUNDLE_PROVIDER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — provider-owned observation mapping DS review

- formal root: `fef695229ea32b85e6841a0fdf7f656feec526ca`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- remediation: moved observations→flat bundle mapping into provider-owned `observation_to_bundle`; `observe_and_assemble` no longer accepts arbitrary callback. Root/files/Git/argv/env facts are deterministically bound, then existing constructor validates the result.
- evidence: 17/17 joint unittest PASS, py_compile PASS, git diff --check PASS; no real source/cache payload reads or instance writes.
- DS-only per user instruction. requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_OBSERVATION_BUNDLE_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — source-evidence real-output write authorization DS review

- implementation authority: writer closure `944c8119b9fda15d4edc7475e7384cbb0712253f`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- request: review whether to authorize one controlled real source-evidence closure execution under the approved v0.2/v0.3 designs; exact formal root/child and canonical instance SHA must be preflight-bound, fixed versioned JSON/Markdown sibling paths used, and any failure must hard-stop with residue.
- verified read-only inputs: four LIBERO suites under `/disk/rl/data/LIBERO_LeRobot_v3`, latent cache `/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1` (54G), Edge checkpoint and Wan VAE present.
- forbidden in this request: training, GPU/CUDA/torchrun, child modification, retry, source payload publication beyond the approved closure sequence.
- DS-only per user instruction. requested verdict: `APPROVE_TO_WRITE_SOURCE_EVIDENCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — fixed-path writer closure re-delivery (DS-only)

- formal root: `152562f8ce50062169fa8644a4856bb2997966ad`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Scope: fixed-path publisher CPU/static implementation only; 7/7 writer tests, py_compile and diff-check PASS.
- Request DS-only final `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_WRITER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- No real instance write, source I/O, GPU/CUDA/torchrun, or training.

## 2026-09-16 — fixed-path publisher remediation DS review

- formal root: `152562f8ce50062169fa8644a4856bb2997966ad`; child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`.
- remediation: added `write_approved_request_pair` with separate target/staging directory fds, approved versioned JSON/Markdown sibling names, cross-directory no-overwrite link, ordered fsync/readback and structured residue.
- evidence: 7/7 unittest PASS, py_compile PASS, git diff --check PASS; all tests use temporary fixtures and do not write real `docs/build` outputs.
- DS-only per user instruction. requested verdict: `APPROVE_TO_WRITE_SOURCE_EVIDENCE` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — real-output writer implementation design review

- formal root: `f13c6f79d9257c742c167534e3b57a6b881e7607`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_request_instance_real_output_writer_implementation_design_v0.1.md`
- scope: writer CPU/static implementation design only; freezes entrypoint, staging/link/fsync/readback/cleanup and partial-residue tests. No real instance write, source I/O, GPU or training.
- requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_WRITER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — real-output execution design v0.3 amendment review

- formal root: `32e0486353754ff975c24f979076baf95f0d038a`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- amendment: replaces overwrite-prone publication with `os.link(..., follow_symlinks=False)` no-overwrite/EEXIST; staged and target modes are both `0644`; JSON then Markdown order and partial-publish terminal semantics are frozen.
- scope: design-only; no instance write, source I/O, GPU or training.
- requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_EXECUTION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — real-output execution design v0.2 amendment review

- formal root: `0ffe9597cdb8095ee9e9e0bb75a63aa3b66a7a2a`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- amendment: freezes filesystem (not Git) publication, staging directory and fd flags, mode/owner/readback, partial-residue schema, and constructor identity.
- scope: design-only; no instance write, source I/O, GPU or training.
- requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_EXECUTION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — real-output instance construction execution design review

- formal root: `59074d234a5c22e59efb316c3e515905eea0a6b8`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- design: freezes fixed JSON/Markdown paths, preflight absence, one-shot staged pair write, byte readback, partial-residue terminal policy and hard stop.
- scope: design-only; no instance write, source I/O, GPU or training.
- requested verdict: `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_EXECUTION` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — construction CPU/static v0.3 amendment closure review

- formal root: `e33c1c05013284039f82cd411a3398dceb45d781`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- amendment: adds five omitted 40-hex identity checks and freezes absent fixed-ref encoding as `ABSENT`.
- evidence: 3/3 unittest PASS, py_compile PASS, git diff-check PASS; root pushed to origin/V2.
- scope: CPU/static memory-only; no instance/output write, source I/O, GPU or training.
- requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — request instance construction CPU/static implementation closure review

- formal root: `32678cfa35fbc285b0aa2c53f000eb171c2fea8b`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- implementation: added `tools/psm_wma/build_source_evidence_closure_request_instance.py` and its stdlib test; constructor is in-memory only and verifies exact top-level schema, canonical terminal-LF JSON, self-excluding SHA-256, and fail-closed bytes.
- evidence: 3/3 unittest PASS, py_compile PASS, git diff --check PASS.
- forbidden: real instance/output writes, checkpoint/manifest/data/cache payload, source/record/publication I/O, GPU/CUDA/torchrun, training.
- requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — construction CPU/static v0.2 amendment closure review

- formal root: `0fc4217ba22dc31ed0ffaa131123cfc961755b3b`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- amendment: versioned v0.2 records memory-only construction boundary; implementation enforces nested exact keys/types, lowercase identities, ordered arrays, fixed package/witness keys, fixed execution order, and four-field `RECORD_KEYS[2:]` mapping.
- evidence: 3/3 unittest PASS, py_compile PASS, git diff-check PASS; root pushed to origin/V2.
- scope: CPU/static in-memory only; no instance/output write, source I/O, GPU or training.
- requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — construction CPU/static remediation closure review

- formal root: `9efafe212cda7ac38531503f1599a3c48deb94e4`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- remediation: nested exact section keys, fixed record/receipt keys and four-field digest mapping are now fail-closed; write/readback is explicitly deferred to a separate execution Gate.
- evidence: 3/3 unittest PASS, py_compile PASS, git diff-check PASS; formal root pushed to origin/V2.
- scope: CPU/static in-memory only; no instance/output write, source I/O, GPU or training.
- requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — construction implementation design remediation review

- formal root: `3b2f3a70` (full root is the submitted commit); child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- remediation: fixed JSON/Markdown output paths, constructor module/entrypoint and file allowlist, external read-only `ObservationBundle` provider boundary, and approved schema formal root/child reference.
- scope: docs-only design; no instance, source payload, record/publication I/O, GPU or training.
- requested verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_CONSTRUCTION_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.

## 2026-09-16 — request-instance real-output writer CPU/static implementation closure review

- formal root: `1c12964511070ff1568a0e7391daaed9eb6f0bb6`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- implementation: added `tools/psm_wma/write_source_evidence_closure_request_instance.py` and its stdlib test; writer verifies constructor bytes, exact formal root/child when supplied, self-bound JSON SHA, staged exclusive files, no-overwrite link, fsync, readback and structured residue.
- evidence: 5/5 unittest PASS, py_compile PASS, git diff --check PASS.
- scope: temporary fixture only; no real instance, source I/O, GPU/CUDA/torchrun or training.
- requested verdict: `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_WRITER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
## 2026-09-16 — observation bundle provider closure review (DS-only)

- Gate/task: Local Memory source-evidence closure request-instance provider整改。
- formal root: `decd2dd45dfe1e5a462ae4884abf2d9ab6387f4`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Changes: provider binds observed cwd/module/selection/config/interpreter/git identities, Git metadata and absent targets; added real multi-file observation fixture and missing-blob fail-closed negative test.
- Evidence: provider and constructor tests `15/15 PASS`; py_compile and git diff-check PASS.
- Review scope: DS-only per user authorization; MM removed; ChatGPT advice-only. No source I/O, request-instance write, GPU/CUDA/torchrun, or training.
- Request: review exact formal root/child and return final `APPROVE` or `REQUEST_CHANGES` with `file:line`; approve only the described provider/test scope.

## 2026-09-16 — observation bundle provider closure review v2 (DS-only)

- formal root: `78231622c0ea1e3daaf5af7f5420dbf81701d5cf`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Follow-up: separate local/remote ref observation via explicit `git_remote_ref`; encode missing remote as `ABSENT`; bind `preflight.absent_refs`; add remote positive fixture.
- Evidence: provider/constructor `16/16 PASS`; py_compile and git diff-check PASS.
- Request DS-only final `APPROVE` or `REQUEST_CHANGES(file:line)` for this exact pair. No source I/O, instance write, GPU/CUDA/torchrun, or training.

### Correction

- The preceding v2 entry contained a typographical formal-root SHA. It is superseded by this exact pair: formal root `78231622d5071cb12f8a711cd51461e0da008317`; child/Gitlink `93a89ba61306d840a008813f62f26a34d54850f4`.

## 2026-09-16 — observation bundle provider closure review v3 (DS-only)

- formal root: `3bf72e49593f1c21e61f783e724213c262df1a04`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Follow-up: explicit independent `git_remote_url`; `ls-remote --exit-code`; missing remote ref=`ABSENT`; read failure=`BLOCKED_AUTHORITY_NOT_CLOSED`; `preflight.absent_refs` bound.
- Evidence: provider/constructor `17/17 PASS`; py_compile and git diff-check PASS; positive/missing/unreachable remote fixtures.
- Request DS-only final `APPROVE` or `REQUEST_CHANGES(file:line)` for exact pair. No source I/O, instance write, GPU/CUDA/torchrun, or training.

## 2026-09-16 — fixed-path writer closure review v2 (DS-only)

- formal root: `a58bdb905d189c8f141cf356abdbba6c5aee101f`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- 整改：补 link/EEXIST、fsync、readback mismatch、JSON-only partial residue fixtures；增加 owner 校验与 staging parent fsync。
- 证据：writer/constructor `11/11 PASS`，py_compile、git diff-check PASS。
- 请求 DS-only 最终 `APPROVE_TO_CLOSE_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_REQUEST_INSTANCE_REAL_OUTPUT_WRITER_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`；禁止真实 instance 写入、source I/O、GPU/CUDA/torchrun、训练。

## 2026-09-16 — observation bundle provider closure review v4 (DS-only)

- formal root: `187768e4169bc98839b7d848e2d8ffc74a3fafe9`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Follow-up to DS `APPROVE_TO_CLOSE`: added mocked `rc=2` remote-ref absence assertion and mocked unreachable-ref fail-closed assertion; removed real network attempt from CPU/static tests.
- Evidence: provider/constructor `19/19 PASS`; py_compile and git diff-check PASS.
- Request DS-only final verdict for exact pair. No source I/O, instance write, GPU/CUDA/torchrun, or training.

## 2026-09-16 — observation bundle provider closure review v5 (DS-only)

- formal root: `786538f8f475d0f5a2708fda6be2c0b44a76ace0`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- Follow-up to v4 REQUEST_CHANGES: deleted the remaining real `example.invalid` network test; retained mocked remote-present, rc=2 absent, and unreachable fail-closed fixtures.
- Evidence: provider/constructor `18/18 PASS`; py_compile and git diff-check PASS.
- Request DS-only final `APPROVE` or `REQUEST_CHANGES(file:line)` for exact pair. No source I/O, instance write, GPU/CUDA/torchrun, or training.

## 2026-09-16 — source-evidence production entrypoints 实现设计 v0.1 (DS-only)

- formal root: `3324b3a0a4dc92b36882e23b4d9b42052554965c`
- child/Gitlink: `93a89ba61306d840a008813f62f26a34d54850f4`
- 回应 `source_evidence_closure_execution_request_design_v0.3` HIGH-1：Stage-2 exact request 需 production producer/record/receipt/root-audit entrypoints 实现并关闭后才可构造。
- 设计路径：`docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_production_entrypoints_implementation_design_v0.1.md`
- 内容：把已关闭 producer/closure library helper（produce_source_evidence_record/package/closure/verify）与 collect_synthetic 的 receipt/commit/post-check seam 提升为 producer/record/receipt/root-audit 四个 production entrypoint，argv 子命令分派、任一绑定缺失 fail-closed。
- 范围：只改 tools/psm_wma/immutable_source_collection.py 与其单元测试；不接线、不真实 I/O、不 GPU、不训练。
- 请求 DS-only 最终 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCTION_ENTRYPOINTS_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-17 — active window slot rotation 修复（已实现，送审）

- formal root: `5d527f3ea8db25f23482c9a3e13b5c7ca2fd6a99`
- child/Gitlink: `6dc25e0f8c3ba39525c8ba994b8d0c38c2ce5461`
- 设计路径：`docs/build/PSM-WMA_Local_Memory_v0.3.5_active_window_slot_rotation_fix_design_v0.1.md`
- Gate：`G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION`
- **缺陷**：`active_local_memory_driver.py` 的 `freeze_window` 按 category 计算 deficit，同一 category 的两条 slot deficit 恒等，tie-break 落到 `slot_id` 且恒取较大者。`canonical_segment_streams:166,176` 把每个 suite 的 episode round-robin 对半分给该 suite 的两条 slot，故 **slot 0/1/2/3 在任何 window 都不被选中，每个 suite 恰有一半 episode 永不参与训练**。真实生产链路（真实 dataset/producer/driver，CPU-only）实测：`window_slots_starved=[0,1,2,3]`、饿死 slot 独占 7190/14430 = **49.83% block**；每 suite episode 覆盖率 **50%**。可达唯一 block 上限 7240 ≈ 56.6 window，而正式训练计划约 5000 步 ⟹ **不会崩溃、不报错、loss 正常，静默用一半 episode 训完**。
- **改动**：`freeze_window` tie-break 第三项 `slot_id` → `-used[slot_id]`（本 window 内该 slot 已被选中次数）；同 category 内交替入选，跨 category 仍由 deficit 决定。仅改 `active_local_memory_driver.py` 与其 `_test.py`。
- **四步证据**：①新增 2 例 CPU fixture 在补丁前**失败**（`assert [4,5,6,7] == [0..7]`，与生产实测一致），证明非空转断言；②补丁后 driver 测试 `13 passed`、ruff/py_compile/`git diff --check` 全过；③生产链路复验 `window_slots_starved [0,1,2,3] → []`、`per_slot_members {4:32,5:32,6:32,7:32} → 8 slot 各 16`、`per_category_members` 各 32 与 `ga_effective` 128 **均不变**；④相邻契约测试 `production_active_wiring_test` + `local_memory_segment_test` + `canonical_segment_runtime_test` + `active_local_memory_launch_test` = `58 passed`。
- **为何判定为实现缺陷而非冻结语义**：①规范只把 deficit 定义为 category 级配额（`v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md:86`、`detailed_design_addendum_v0.3.5.md:229`），从未定义同 category 内 tie-break，更未授权 slot 永久饿死；②`production_active_wiring.py:88` 走 singleton 候选 `admit_next((identity,))`，`canonical_segment_runtime.py:105-108` 只校验候选等于冻结计划成员，故 `scheduler.admit()` 的多候选 tie-break **在 active 路径上不被行使**，`freeze_window` 顺序即唯一权威 ⟹ 修复自包含，不触及 owner/scheduler/sidecar/`GAWindowPlan` 任何接口。
- **请一并裁定**：设计文档 §2.3 的解读——现实现下 8 个连续 member 为 `[7,6,5,4,7,6,5,4]`（只跨 4 条 slot），是否已不满足 `functional_active_route_implementation_design_v0.1.md:129-138` 裁决 (B) 理由 #1「(A)/(B) 数值等价」所依赖的前提（(A) 的一个 member 持 `B_stream` 行 = 8 条不同 slot）。若裁定 (B) 只要求 member 数为 `8*GA`，则本缺陷定性降为「数据覆盖缺陷」，**修复动作与判据不变**。
- **测试缺口说明**：既有唯一涉及 slot 轮转的用例 `active_local_memory_driver_test.py:138` 用两个**不同** category（slots 0/1 分属 a/b），deficit 不等故 tie 不发生；生产形态 `b_stream=8`/4 categories 使同 category 恒有两条 slot，该分支此前从未被覆盖。
- 范围：CPU-only，无 GPU/torchrun/训练/checkpoint 写入。子模块 `uv.lock` 为遗留 dirty 文件，未纳入提交。
- 请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_WINDOW_SLOT_ROTATION` 或 `REQUEST_CHANGES(file:line)`。

## 2026-09-17 — active 路线 resume 接线设计（设计，送审）

- formal root: `8bb48f3507dda24090de41bbc4208dfc9e4538aa`
- child/Gitlink: `525f5066393cba044f00f1104b83f5eb424a9c49`
- 设计路径：`docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_resume_wiring_design_v0.1.md`
- Gate：`G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME`
- **状态：设计，尚无对应代码改动。** 当前 operative 行为是已落地的 fail-closed 守卫（见下）。
- **缺口**：active 路线的数据进度状态完全不入 checkpoint —— driver 的 `_stream_index`/`_active_stream`/`_active_cursor`/`_window_index` 与 scheduler 的 `cumulative_valid_consumer_exposure`/`stable_slots`/`terminal_slots`/`admission_order`/`committed_identities`/queue 系列，在 `on_train_start` 里全部从零重建。而 model(597 keys)/optim(180)/LR-scheduler(6)/trainer(7) 均正常恢复 ⟹ **数据回退、模型前进**的语义错乱。对 5000 步（≈11.9 天，必然中断）不可接受。
- **本次判定（推翻此前记录）**：本项**不是「机制未知需重新设计」，而是「接缝已完整建好、只差持久化接线」**。grep 核实：`CanonicalSegmentRuntimeOwner.snapshot()`（`canonical_segment_runtime.py:173-190`）与 `RankLocalSegmentScheduler.rebuild()`（`local_memory_segment.py:351-364`）**均已完整实现，但全仓零生产调用点**（`dcp.py:585`/`distributed.py:755` 的同名 `_rebuild` 是无关函数）。
- **同时更正两条此前的错误判断**：① `on_load_checkpoint(model, state_dict={})`（`dcp.py:943`）拿到的是**空 dict**，源码注释明言该回调从未被使用；② 在 `on_save_checkpoint` 往 `to_save_dict` 新增顶层 key 会让 resume 直接 `raise ValueError(f"Invalid key: {key}. not support to resume.")`（`dcp.py:939`）。**真正机制**是 `_DataloaderWrapper`（`dcp.py:112-153`）的 `checkpoint_component="dataloader"` 槽；该槽在 action/libero 配置链上**为空**（`DataLoaderStateCallback` 只注册于 reasoner 系列），本设计将是它的第一个占用者。wrapper 在**存/取盘时**构造（`dcp.py:1120`/`:934`）并每次重新遍历 callbacks，故 driver 只需在 `attach()` 后具备该接口。
- **无界列表的修剪证明**：`admission_order`/`committed_identities` 从不修剪，128 member/步 × 5000 步 = 每 rank 64 万条。此前记录的选项 (a)「排除二者（判定其为审计轨迹）」**已被证伪**——二者是活的守卫状态（`local_memory_segment.py:322-323`、`local_memory_segment_adapter.py:79`、`canonical_segment_runtime.py:86`/`:224` 均做成员判断）。**修剪安全的依据来自 `owner.snapshot()` 自身**：它只在 IDLE（窗口边界）可调用，`:181` 以 `committed_by_slot`（后写覆盖 = **每 slot 最近一条**）派生，`:182` 断言 `admission_order ⊆ committed_identities`，`:183-186` 要求 `committed_by_slot[slot]` 与 `stable_slots[slot]` 恰为 sidecar 的该 slot 已提交 identity ⟹ **resume 路径只咨询「每 slot 最近一条」，更早条目无任何读取点**。修剪只作用于 snapshot 输出，运行期活列表不修剪（`:86`/`:224` 的 skip/retry 守卫要求成员判断，而这些路径的 `_skipped_plan`/`_retry_plan` 均为内存态、resume 后为 None）。
- **请裁定三点**：① §3 的修剪证明是否成立；② §4.3 的三项 fail-closed 校验（`_by_slot` 重建确定性、恢复点须为窗口边界、`window_index` 单调）是否充分、是否还有「半对半错」的静默通道未被拒绝；③ §4.4 —— 本设计落地后 `iteration > 0` 应从「一律拒绝」收敛为「load 成功则放行、失败则拒绝」，是否正确。
- **验收判据**含 GPU 端到端 resume 短跑（跑至 `save_iter` → 杀进程 → auto-resume → 断言首窗 identity 序列与不中断跑的对应窗口一致、exposure 连续不归零）。
- 范围：设计文档 + 后续 `active_local_memory_driver.py`/`local_memory_segment.py` 最小改动。不改 `GAWindowPlan`/`SegmentIdentity`/`SegmentBatch` ABI，不改 admit/commit/terminal_rebind 守卫，不新增 DCP 顶层 key。
- 请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_ROUTE_RESUME` 或 `REQUEST_CHANGES(file:line)`。

### 附注（2026-09-17）——§6 的 BLOCKED 判据已由独立证据证伪，请按「无 BLOCKED 风险」阅读

**送审件未变，无需重新取件**：设计文档 blob 仍为 `a8dd24ca16d1b164ea54c1be9a4cbf0ee81617c5`，child/Gitlink 仍为 `525f5066393cba044f00f1104b83f5eb424a9c49`。父仓库根由 `8bb48f35` 前进至 `c48c0169`，但 `8bb48f35..c48c0169` 的 6 个提交**不含任何代码改动**（`git diff --name-only` 在排除 `docs/`、`artifacts/`、`SESSION.md`、`TODO.md` 后为空），故审核者手上的代码态与送审时一致。

**证伪内容**：§6 原写「**BLOCKED**：`_by_slot` 的重建被证明不确定（同 dataset 同 seed 下逐次不同）⟹ 本设计不落地」。该条件**不成立**，故本设计无 BLOCKED 分支。

**证据（直接观测，跨进程）**：两个独立进程各建一遍生产 producer 集合（`CanonicalLocalMemorySegmentProducer` × 4 suite，`ttt_tbptt_steps=16`），对**完整 stream 元组 + 每条 stream 的 `block_count` + `frame_source._ep_vals`/`_ep_starts`/`_valid_cum` 原始字节**求 SHA256：

```
P1: CATALOG_SHA256=f465db8e661a6fc4bfa79196c07d61238a073c23446c2ae5997150f06c9fd67c SLOTS=8 STREAMS=1676
P2: CATALOG_SHA256=f465db8e661a6fc4bfa79196c07d61238a073c23446c2ae5997150f06c9fd67c SLOTS=8 STREAMS=1676
```

逐位相同。代码层依据：`canonical_segment_streams`（`active_local_memory_launch.py:146-180`）只读 `frame_source._ep_vals`/`_ep_starts`/`_valid_cum`（`libero_lerobot_dataset.py:203-214`，`np.unique` + **seeded** 的 per-episode train/val split）与 `block_count`，不涉 RNG、不涉进程态；`ActionIterableShuffleDataset` 只打乱 block 迭代顺序，而 active 路线实测 `iterable_shuffle=False`（D8a 的 callback config dump）。

**据此向审核者提一项建议**：§6 删去 BLOCKED 后少一条把关，建议把「**跨进程重建 catalog 的 digest 逐位一致**」补为 PASS 判据第 6 项（证据已附上）；否则 §4.3 第 1 项 fail-closed 校验（`_by_slot` 重建确定性）在验收侧没有对应判据。

**本文档在 verdict 到达前不改**——避免送审件 SHA 漂移使审核引用失效。若裁定要求把上述内容并入 §6，我在实现记录（§9）中一并落。

---

## 2026-09-17 — catalog 容量换算：现有 catalog 只够 112 个优化步，两个在审 Gate 的共同前提需据此校正

**不改变任何送审件的 SHA，也不改变已提交的代码。** 本条是对 `G0-R09-B-TTT-V035-ACTIVE-WINDOW-SLOT-ROTATION` 与 `G0-R09-B-TTT-V035-ACTIVE-ROUTE-RESUME` 两个在审事项的**共同前提补充**，请三方审核者据此校正对「5000 步」的理解。

**新事实**：生产 catalog 的**总** block 容量 = `14430`，而一个 window 消耗 `grad_accum_iter = 128` 个 block，且 catalog 全程只建一次、只消耗不回收 ⟹ **整个 catalog 只够 112.73 个 optimizer step**。正式计划 `max_iter = 5000` ⟹ **缺口 44.4 倍**；第 113 个窗口的 `freeze_window()` 会 `raise RuntimeError("active Local window exhausted every segment stream")`（`active_local_memory_driver.py:230-231`）。

**证据**：探针 `tools/g0/probe_block_capacity.py` → 产物 `artifacts/g0/active_static_probe/probe_block_capacity.json`（CPU-only，真实 dataset+producer，同参数独立复跑读数逐位一致）。换算依据经代码核实，非推断：一个 member 恰好消耗一个 block（`_peek_block` 每 member 推进一格 cursor、走满 `blocks-1` 才换 episode，`_commit_block` 只增不减，`active_local_memory_driver.py:258-286`）；`block_count = valid_start_count // ttt_tbptt_steps`（`canonical_local_memory_producer.py:113-115`）；catalog 只在 `on_train_start` 建一次、`iteration > 0` 与重复建均 raise（`active_local_memory_launch.py:223-289`），**无 epoch 重建、无绕回**。`14430` 这一总数仓库内早有记录，但从未换算成可服务的训练步数。

**对 slot rotation Gate 的影响 —— 修复的正确性判定不变，但请勿以「够 5000 步」为前提**：
- 送审件原文「可达唯一 block 上限 7240 ≈ 56.6 window，而正式训练计划约 5000 步」所用的 window/步换算与本次一致；修复把可用量由 7240 提到 **14430（翻倍）**，**方向与判据均不变**。
- 但请一并注意：**14430 仍只够 112 步**，故该修复是必要而非充分条件。请勿据此认为修复落地后即可支撑正式训练。
- 送审的四步证据（`per_slot_members` 各 16、`slots_starved=[]`、`per_category_members` 各 32、`ga_effective=128`）**不依赖容量问题**，仍请按其本身裁定。

**对 resume Gate 的影响 —— 设计主体不变，但动机表述需修正**：
- 设计 §1 以「5000 步 ≈11.9 天，必然中断」论证 resume 必要性；在容量问题解决前，**5000 步计划本身不成立**，实际可跑上限是 112 步。
- resume 仍然必需（112 步亦可能中断；且容量方案落地后 resume 更必需），故**这一修正不推翻设计**，只是把「为 5000 步长跑而做」改述为「为任何超过单次会话长度的跑动而做」。
- §6 验收判据 4（GPU 端到端 resume 短跑至 `save_iter`）**不受影响**：生产 `save_iter=50 < 112`，对照跑与中断跑都在容量内。

**新增并行议题（尚未设计，仅提请知悉）**：使 `max_iter` 可被完整服务需要「catalog 多 epoch 复用」。当前 `local_memory_segment.py:322-323` 的守卫含 `identity in self.committed_identities`，复用同一 block 会因 identity 重复被 fail-closed 拒绝 ⟹ 触及 `SegmentIdentity` 唯一性语义（resume 设计 §7 明令不得改该 ABI）。此项将另出设计，**不在本次两个 Gate 的裁定范围内**。

> **上段的定性已于同日更正**：核实后判定该议题**不触及 `SegmentIdentity` ABI**，且**不是发明新机制而是接线**——详见下一条送审条目。

---

## 2026-09-17 — active 路线 catalog 多 epoch 复用（设计，送审）

- formal root: `bae3964776d3138d2a60d1b03cbabe0062fef75c`
- child/Gitlink: `525f5066393cba044f00f1104b83f5eb424a9c49`
- 设计路径：`docs/build/PSM-WMA_Local_Memory_v0.3.5_active_route_catalog_epoch_reuse_design_v0.1.md`（blob `c686ff3bf43a5e3b8cd36910ae8756d605c9e621`）
- Gate：`G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`
- **状态：设计，尚无对应代码改动。** 当前 operative 行为是 `freeze_window` 在 catalog 耗尽时 fail-closed `raise`（`active_local_memory_driver.py:230-231`）。
- **缺陷**：生产 catalog 总 block 容量 `14430`，一个 window 消耗 `grad_accum_iter = 128` ⟹ **只够 112.73 个 optimizer step**，而正式计划 `max_iter = 5000` ⟹ **缺口 44.4 倍**，第 113 个窗口即 `raise`。这与另两个在审项的关系：slot 轮转修复（7240→14430）**必要但不充分**；resume 恢复进度、**不增容量**。故本项是「具备正式训练条件」的独立且更靠前的阻塞。**不可靠参数绕开**：`block_count = valid_start_count // ttt_tbptt_steps`，总容量是「数据集 × TBPTT 宽度」的固有属性；`ttt_tbptt_steps` 16→8 只提到 225 步且改变语义，增大 `b_stream` 不改变总 block 数。
- **判定：不是新机制，而是接线**（与 resume 设计同性质）——五件部件均已存在并已冻结，缺 active 生产路线的调用：① epoch 快照契约 `QueueEpochSnapshot(queue_seed, epoch, catalog_digest, positions, permutations)`（`canonical_segment_adapter_scheduler.py:57-67`）；② 确定性排列 `queue_digest_preimage`/`queue_permutation`（同文件 `:76-110`，带 `PSM-WMA/queue/v1` 版本标记）；③ epoch 边界规则 `rollover_projected_if_safe`（同文件 `:546-549`）；④ `RankLocalSegmentScheduler.configure_queue(seed, epoch, permutation, provenance)`（`local_memory_segment.py:331-337`）**已实现但全仓零生产调用点**（仅 `local_memory_segment_test.py:113`）；⑤ `snapshot()`/`rebuild()` 已含 `queue_seed`/`queue_epoch`/`queue_permutation`/`segment_provenance`（`:362-365`、`:378-381`）。**单位已核实对齐**：契约 `_queue_for(category)` 以 episode 为单位（取 `cursor == 0 and consumer_step_start == 0`，`:471-477`），而 `canonical_segment_streams` 为每个 episode 建一个 stream（`active_local_memory_launch.py:169-182`），`_by_slot[slot]` 即该 suite 的 episode 列表 ⟹ epoch 重排 = 按新 epoch 排列重排 `_by_slot[slot]`。
- **epoch 边界定义（直接采用契约，不重新发明）**：两条**同时**成立才推进——① 每个 category 的游标都到达其 catalog 末尾；② **所有 stable slot 都处于 terminal**（无跨 epoch 的半截 episode）。动作：`epoch+1` + 对每个 category 生成 `queue_permutation(seed, epoch+1, category, size)` + positions 重置。
- **关键设计选择**：① **触发点在窗口边界（`_arm_initial`）而非 `freeze_window` 的 raise 点**——后者在循环内逐 member `_commit_block`（`:234`），中途 raise 时 `_stream_index`/`_active_stream`/`_active_cursor` 已被部分推进，即该函数**不是原子的**，在 raise 点重置会留下半推进状态；② **`cumulative_valid_consumer_exposure` 不清零**（`freeze_window` 用其**比例** `:226`，累计不清零时比例仍稳定收敛于 `target_distribution`；清零反而破坏该字段语义）；③ **不需给 identity 加 epoch 维度**——`_is_admissible` 在 `stable_slots` 无该 slot 时只要求 `cursor == 0`（`:309-311`），`terminal_rebind` 删除该条目（`:343`），故 epoch 边界重置守卫容器后，复用同一 identity 天然可准入，**不触及 `SegmentIdentity` ABI**；跨 epoch 产生的 identity **值**相等是刻意的（identity 描述数据段身份，复用同一段本就该是同一身份），由边界重置而非 identity 维度来管理守卫。④ `canonical_segment_runtime.py:181-182` 的一致性校验因 `admission_order` 与 `committed_identities` **同时**清空而保持成立。
- **与 resume 的顺序**：本设计的 `_catalog_epoch`（driver）与 `queue_epoch`/`queue_permutation`（scheduler）都必须入 checkpoint。scheduler 侧三个字段**已在 `snapshot()` 就位**，driver 侧只增 `_catalog_epoch` 一个字段 ⟹ **建议先落地 resume 接线，再落地本设计**；本设计不阻塞于 resume 的 verdict（设计与证据可先行），但**实现应在 resume 之后**。本设计**不修改 resume 设计 §6 的任何判据**（其判据 4 的 GPU 短跑至生产 `save_iter = 50 < 112`，落在单 epoch 内，与本设计正交）。
- **验收判据**：① CPU 契约一致性——重排结果与独立调用 `queue_permutation` 逐位一致、`queue_epoch` 恰好 +1；② CPU 纯规划层——连续推演越过 epoch 边界，断言可规划出 **> 112.73** 个窗口而不再 raise、第 113 个窗口成功规划、跨 epoch 无 identity 被 `commit` 拒绝；③ 原子性——窗口边界的探测**不修改** driver 状态，且探测与实际 `freeze_window` 共用同一选择规则（防两处规则漂移）；④ 边界条件两条各有独立用例（某 category 未到末尾 → 不推进；存在非 terminal 的 stable slot → 不推进）；⑤ GPU 短跑越过一个 epoch 边界，断言无 raise、loss 有限、每窗口 8 slot 仍均衡、`exposure` 单调不减；⑥ resume 交叉（resume 落地后）在 epoch ≥ 1 处存盘并 resume，断言 `_catalog_epoch`/`queue_epoch` 一致恢复、续跑窗口序列与不中断跑一致。
- **BLOCKED 判据**：若 §3 条件 2（所有 stable slot 均为 terminal）在真实链路**无法同时成立**，则 epoch 边界不可达，本设计不落地，须改为「按 slot 独立推进 epoch」的更强语义——那将触及 `GAWindowPlan` 的跨 member 一致性，属另一项设计。
- **请裁定三点**：① §3 采用契约既有的 epoch 边界条件是否正确，尤其**条件 2 在 b_stream=8 / 4 categories 的生产形态下是否恒可满足**（直接决定上述 BLOCKED 判据是否触发）；② §4.3 的重置清单是否完备——是否还有第四处状态会跨窗口残留、从而在第二个 epoch 造成**静默错误**（特别请审 `_rebind_terminal`（driver `:190-195`）在 epoch 边界的时序，以及 `owner` 的 `phase`/`transaction` 是否有未列出的残留）；③ §5 的顺序判断是否成立（实现排在 resume 之后，且 resume §6 判据无需因本设计修改）。
- 范围：设计文档 + 后续 `active_local_memory_driver.py` 最小改动（`local_memory_segment.py` 侧维持 `configure_queue` 的签名与语义不变，重排由 driver 执行）。不改 `SegmentIdentity`/`GAWindowPlan`/`SegmentBatch` ABI，不改 admit/commit/terminal_rebind 的守卫条件本身（只重置其所依赖的状态容器），不改 `queue_permutation` 字节序，不新增 DCP 顶层 key，不重建 catalog、不改 `on_train_start` 构建路径。
- 请求 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_ACTIVE_CATALOG_EPOCH_REUSE` 或 `REQUEST_CHANGES(file:line)`。
