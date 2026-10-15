# PSM-WMA V3 B1 P0 — SOURCE Index8 GPU Smoke Independent Evidence Review / TARGET Human Release

**Date:** 2026-10-15  
**Reviewer:** GPT, independent Code/Evidence/Gate reviewer  
**Stage:** SOURCE→TARGET human execution-safety release **within** the existing Owner P0_FIXED repeat0 GPU receipt.  
**Human release literal:** **`ALLOW_PACKED128`** (TARGET execution ONLY, after its own live preflight).  
**NOT an overall B1 GPU numerical verdict:** `B1_GPU_NUMERIC_PARITY_UNVERIFIED`. Full B1, P1, repeat1, Gate M and Formal30k remain HOLD.  
**Basis:** Owner-pasted `DS_PRO — V3 B1 P0 SOURCE GPU Smoke · a3239591 · Owner 11GiB · 2026-10-15` plus independent pinned-GitHub source/authorization check. DS host's `/tmp` JSON/PT/log files were not directly reachable by GPT (Desktop Commander device offline). Therefore source-side evidence completeness is accepted **as reported by DS_PRO**, not represented as an independently executed hash/count verification by GPT.

## 1. Exact unchanged frozen implementation and authorization

- Diagnostic B1 executable Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0`, Child `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`; independent GitHub lookup confirms diagnostic branch HEAD unchanged.
- SOURCE Index8 frozen Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- TARGET Packed128 frozen Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`. New production V3 Gitlink must never be substituted.
- Owner authorization new SHA `b340c5e3c942372f7928c6aa205dcd54433fb42d`, authoritative JSON `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_a3239591_11GiB.json` (blob `84e71ce0e4d0bb947b975f2af62eaeb2cf7fb250`); scope: two jobs maximum, 8 H100, `P0_FIXED`, `repeat=0`, `iter1301/1302`, SOURCE then human release then TARGET. All eight devices require **>=11264MiB driver-reported free** immediately before **each** GPU job, without interfering with other users.
- Owner frozen r2 policy SHA `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`, original B0 DCP full-shard FP `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`.
- B1 CFG Local-RNG CPU Gate is already `APPROVE_TO_CLOSE` for this pair and is NOT re-reviewed.

## 2. SOURCE execution evidence: contract → DS observation → scope judgment

| Contract | Executor's actual-source report | Judgment for human SOURCE release |
|---|---|---|
| Pinned pair, clean worktrees and Gitlink | All three pairs checked before and after, porcelain-empty | PASS (DS evidence) |
| Owner receipt provenance / scope | Pinned receipt blob matched; `ALL_SCOPE_FIELDS_PASS` | PASS (DS evidence, receipt GitHub-confirmed) |
| Prelaunch ASCII/prepare | Runbook ASCII, `bash -n` zero; both `prepare` exit0 with expected digests `70e9867f...`/`1ab2bbe4...` | PASS (DS evidence) |
| Launch memory gate | 8 cards free `35430/35511/35511/24294/24295/24293/34290/34277` MiB; each >=11264MiB | PASS at SOURCE launch (DS evidence) |
| Frozen CWD / strict original resume | Launched from SOURCE frozen Child; original iter1300 strict DCP restored, no warm-start, no unexpected save | PASS (DS evidence and verified diagnostic guards) |
| 8 ranks × 2 completed optimizer iterations | `SOURCE_RC=0`; iter1301 Full GA counts `[128,128]`, iter1302 Terminal Partial `[122,128]` on all 8 ranks; 16 JSON +16 PT loaded | PASS for SOURCE completion (DS evidence) |
| Required witness categories | JSON schema, `weighted_outer`, full native per-consumer model-site/CFG, 16 PT contain FQN gradients/master/moments, 4 fast states/slot | PASS for SRC capture availability as reported; actual values/coverage and dtype are to be compared at full B1 comparator stage |
| Non-finite/driver failures | No OOM/CUDA/NCCL/nonfinite/traceback, only `destroy_process_group()` cleanup warnings; no residual job | PASS; warning non-blocking without residual process |
| Original DCP/latest protected | No saved checkpoints, no new paths, `latest_checkpoint.txt=iter_000001300`, 44 files with path/size baseline concordance; `checkpoint_write_authorized=false` | PASS for transition operational-safety with **residual evidence limitation** below |

**Residual checkpoint caveat:** DS's final 44-file comparison reports path/size, **not** an independent bytewise re-hash of all 32 DCP shards or an explicit post-run full path/mtime/small metadata-hash inventory. Full re-hash is intentionally forbidden as repeated B0 work. Pinned diagnostic `v3_gateb1_dcp_transient.py` performs before/after load lightweight snapshot (size/mtime for shards + small metadata/sidecar hashes), `unchanged_checkpoint` fail-closed; `exact_readonly_same_job_source` blocks `Checkpointer.save` through both native steps. SOURCE report claims successful strict load and no writes. Before TARGET DS must additionally verify source JSON `restore.status=STRICT_DCP_LOADED_TRANSIENT_NO_SAVE`, `restore.iteration=1300`, `dataloader_state_load_calls=1`, `runtime_shard_contents_rehashed=false`, and all 16 `restore.runtime_lightweight_immutability_witness` are nonempty, identical 64-hex values; compare small metadata hashes + sizes/mtimes with the **same previously accepted original authority** in a cheap fresh no-shard-content-hash read-only witness. If any provenance discrepancy occurs, STOP and return to GPT. These are preservation requirements for TARGET's run, not a new B0/full DCP recertification.

**Evidence provenance caveat:** GPT did not directly open DS host log or PT data. Any discrepancy identified during TARGET preflight or final B1 comparison overrides the human release and is BLOCKED. The SOURCE release only allows the already-approved second job, not numerical equality.

## 3. Literal human release decision

**`ALLOW_PACKED128`** — Explicit independent human SOURCE→TARGET release, scoped strictly to:

- TARGET `Packed128`, Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`, using original iter1300 DCP **read-only**.
- Diagnostic runner `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`, `P0_FIXED` / `repeat=0`, 8×H100, iter1301/1302. SOURCE consumed job1; TARGET is the **second and last** permitted job on this receipt. NO retry.
- Immediately before TARGET: recheck exact SHAs/worktrees/Owner JSON scope, corrected ASCII launch command, `cd "$TGT_ROOT/cosmos-framework"`, no output collision, SOURCE restoration witnesses above, DCP/latest and all-eight **live** free VRAM >=11264MiB per card. Non-compliant => STOP and report blocked, no TARGET torchrun.
- Stop only user's own diagnostic job on any OOM/CUDA/NCCL/nonfinite/incorrect identity/DCP change; never interfere with co-resident processes. Preserve original checkpoint/latest; all outputs isolated in /tmp.
- After TARGET complete, **STOP**, deliver 8 ranks×2 iteration JSON/PT, raw log/RC, source and target DCP lightweight witnesses, current checkpoint/latest and two-leg inputs/witnesses; run read-only P0 numeric comparator under unchanged Owner r2. **Do not** automatically run repeat1/P1, Gate M, Formal30k.

## 4. Gate states

- CPU B1 threaded CFG: CLOSED, no revalidation.
- SOURCE Index8 P0 smoke: **COMPLETE, HUMAN SAFETY RELEASE PASSED** (DS-reported evidence, pinned GitHub safeguards).
- TARGET Packed128 P0 smoke: **`ALLOW_PACKED128` authorized** for *one* job only, strictly preflight-gated; NOT YET EXECUTED.
- B1 P0 GPU numeric equivalence: **UNVERIFIED** until two-leg comparator accepted.
- Full B1 GPU, Gate M, Formal30k: **HOLD**.

**This is a human release record, not approval of numerical parity or an expansion of the Owner's GPU receipt.**
