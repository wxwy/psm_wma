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
