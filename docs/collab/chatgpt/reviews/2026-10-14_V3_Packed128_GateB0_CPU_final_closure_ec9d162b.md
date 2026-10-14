# PSM-WMA V3 — Packed128 Gate B0 CPU formal closure review

**Date:** 2026-10-14
**Reviewer:** GPT — independent Evidence/Gate reviewer (not DS executor)
**Verdict:** **APPROVE — B0_CPU_ACCEPTANCE_CLOSED (CPU ONLY)**
**Formal diagnostic implementation target:** Root \`ec9d162b926c4f197f5cfb692499b4dbda888686\` on isolated \`wxwy/psm_wma:v3-gateb-comparator-b0\` branch. This is NOT the V3 formal training Root SHA; the approval concerns the standalone comparator's **CPU B0**.
**Frozen comparator production SOURCE:** Index8 Root \`b159f45906f7261d028aecc226ab7f2bb9807eb9\` / Child/Gitlink \`937066ffd90f2bf783ad4fbb4909e9c0b8922982\`
**Frozen comparator production TARGET:** Packed128 Root \`c4731bca1a590663db88bd6cd74dbcf9fd513a85\` / Child/Gitlink \`c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686\`
**Current docs V3 child/Gitlink:** \`8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1\` — independent Full Segment Prefetch child, **not** an implementation leg of Gate B. No production SHA changes.
**Gate contract:** \`docs/collab/chatgpt/designs/2026-10-13_GPT_V3_Packed128_GateB_Round2_comparator_and_iter1300_migration_design.md\` §3–§4, §7–§8; \`docs/collab/chatgpt/decisions/2026-10-13_V3_Packed128_GateB_Owner_four_decisions_and_execution_plan.md\`.
**Prior review:** \`docs/collab/chatgpt/reviews/2026-10-14_V3_GateB_B0_dataclass_payload_hash_remediation_review_e3e6df04_ec9d162b.md\`.

## Evidence boundary and why this is not a repeat code audit

The exact diagnostic implementation SHA is **unchanged** since previous incrementally reviewed ec9d162b. This review evaluates **new executor evidence only**, not a duplicate implementation re-review. GPT locked remote diagnostic HEAD exactly ec9d162b and V3 production Gitlink exactly 8f3672d1; checked the native comparator's actual source behavior, especially \`snapshot_checkpoint\`, \`_frozen_manifest_from_plans\`, \`_stable_payload_hash\`, and \`compare_cpu_reports\`.

DS_PRO's final 2026-10-14 report was supplied by Owner in chat. GPT independently checked source contracts and the relationship between returned evidence and those contracts, **but did not personally execute DS's commands or read both raw /tmp JSON files**: DS's remote machine was offline to the available connector. The actual JSON equality, command exit codes and full-shard immutable hashes below are **DS executor-reported**, not fabricated or claimed as GPT-side byte verification. Receipt: \`docs/collab/chatgpt/evidence/2026-10-14_V3_gateb_b0/DS_PRO_ec9d162b_final_CPU_owner_relay_receipt.md\`.

## Contract → behavior → evidence → disposition

| B0 contract | Concrete executor evidence (DS_PRO report; independently mapped to source) | Disposition |
|---|---|---|
| Exact diagnostic & two production implementations, isolated and clean | Diagnostic \`ec9d162b...\` clean detached; Index8 \`b159f459/937066ff\`, Packed128 \`c4731bca/c8dabbb3\`; separate \`cosmos_framework.__file__\` under matching children | **PASS** |
| Static diagnostic quality & denied GPU | Three-file \`py_compile\` exit0; \`pytest -q\` **30 passed** exit0; Ruff \`All checks passed!\` exit0; forbidden \`paired-run\` returns2 + \`GPU_B1_NOT_IMPLEMENTED_OR_AUTHORIZED\` | **PASS** |
| Source source-checkpoint/sidecar authority | Source \`iter_000001300\`, four DCP components / 32 shards / eight rank sidecars (44 items); 17-field rank profiles, exact top-level 10 keys and nested provenance/4 fp32 fast-state tensors; trusted digests | **PASS in CPU static scope** |
| Correctly recomputed config authority | Old resolved digest \`70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37\`; Target resolved digest \`1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a\` (distinct), target sidecar translation in memory only, exact 10 keys preserved | **PASS CPU-only** |
| Eight ranks × two actual GA2 windows with partial segments | Both reports contain 16 exact-equal \`plan.rows\`; \`terminal_partial=true\`, all member_counts and Consumer identities agree; Index8 call rhythm 16 + 16 per member across 8 ranks | **PASS CPU plan/collective preflight** |
| **Real Native input / CFG witness**, not just plan | Both real CPU \`--verify-payloads --hash-all-shards\` legs exit0 and write JSON; both \`payload_witness\` nonnull, status \`CPU_TRANSFORM_PAYLOAD_HASHED_NOT_GPU_VALIDATED\`; 16 rank-window entries and 32 member 64-hex hashes. **Full witness dict equality** and \`compare-cpu-reports\` exit0; common fingerprint \`f4dd11b5903401d0f36d563b1955a6859a502bd4291cc79f31fbbcb1233ffcdd\` | **PASS, DS execution evidence** |
| Immutable old checkpoint | Each leg used \`--hash-all-shards\`, ran \`unchanged_checkpoint(before,after)\` exit0, 44-item source digest fingerprint same on both \`2e409afe…\`; frozen \`latest_checkpoint.txt=iter_000001300\`; historical Lane C 484-path source unchanged | **PASS in this CPU witness** |
| Strict scope | No GPU, torchrun, CUDA model load, Nsight, training/inference, Checkpoint migration/rewrites or official Formal30k worktree edits reported or authorized | **PASS CPU-only scope** |

### Apparent plan fingerprint change is not evidence of data drift

The previous reported \`6a4d9c6a…\` plan fingerprint used a source checkpoint hash calculated with \`hash_shards=False\` (source fingerprint \`faf63ff2…\`). This final run deliberately used \`--hash-all-shards\`, computing source checkpoint fingerprint \`2e409afe…\`, which participates in \`ConsumerKey\`, yielding \`d5c9b17e…\` plan fingerprint in **both legs**. Source code independently establishes the inclusion of \`checkpoint_fingerprint\` and conditionally included 32 shard SHA fields; there is no evidence in this difference of a changed source checkpoint or transformed consumer. Do not pin a partial checkpoint fingerprint as if it were the same input to SHA256.

### Historical blockers and final disposition

- \`B0-F401\` — Ruff unused imports: **CLOSED** on e3e6df04; ec9d DS Ruff exit0.
- \`B0-TMONITOR\` — metadata \`tqdm.TMonitor\` false background-thread blocker: **CLOSED** on e3e6df04; ec9d real CPU materialization both legs exit0.
- \`B0-DATACLASS-01\` — old real Native \`ActionProcessingRecord\` / \`SequencePlan\` unhandled leaf: **CLOSED** on ec9d162b; recursively typed dataclass hash plus positive/negative tests, both real payload legs exit0, no unknown leaf, matching witness dictionaries.

No residual **B0 CPU** blocker is supported by the submitted final evidence.

## Approval scope & remaining requirements

**APPROVE closes B0 CPU only**: deterministic CPU Native source/target transformed-payload parity under the diagnostic witness, 8rank ×2 window identity/frontier/terminal plan, source static sidecar/config & DCP immutability, static/negative diagnostic tests, and correct refusal to run unauthorized GPU. The exact comparator console legacy string \`CPU_PLAN_PARITY_ONLY\` is **not** an independent acceptance standard: actual non-null payload dictionaries were checked and compared by the executor. It would be clearer to rename before B1 tooling, but this is nonblocking for B0.

**This decision does NOT authorize B1 GPU** nor assert real model or FSDP8 gradient numerical equivalence, genuine 4-component 4B DCP runtime load, production Local restore, P1 production-distribution stochastic injection, any optimizer state/parameter delta parity, Gate M persistent migration, iter1301 resume, training, inference or Nsight. Owner D1–D4 remain frozen: B and M separate, P0/P1 both required, real-GPU terminal partial P0/P1 both required.

**B1 prerequisites not yet met:** Owner must freeze actual numeric FP32/BF16/near-zero/per-FQN thresholds before GPU comparisons; build and independently review separate real Cosmos3-Edge/FSDP8 8-rank two-step transient harness, native load/callback sequence, site-complete per-consumer stochastic witness and error handling; then receive *separate Owner authorization* for GPU. The B0 \`paired-run\` intentionally remains blocked.

**Nonblocking traceability note:** Preserve/archive the two raw \`/tmp\` JSON reports because this review relied on DS's independently executed result report, not GPT direct access to their bytes. Archival is recommended to support future B1 audit but does not expand B0 Gate.

**Formal persistence:** this detailed review and a matching append-only entry in \`docs/collab/chatgpt/CODEX_INBOX.md\` are required for formal closure. The docs commit(s) are bookkeeping and **never** replace the diagnostic Root SHA nor either production comparator pair.
