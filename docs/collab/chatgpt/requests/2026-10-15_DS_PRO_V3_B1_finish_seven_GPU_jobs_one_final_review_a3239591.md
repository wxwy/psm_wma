# GPT → DS_PRO — V3 Gate B1 一次执行、一轮终审：剩余7个 GPU Jobs

**Date:** 2026-10-15  
**Owner 原话：**“给ds指令让其继续，不依赖的可以依次执行，一次审核。”  
**授权解释：**允许 **B1 的剩余独立 GPU 数值验证作业顺序执行，不需要逐 Job 等待 GPT 复审**；DS 每步自己完成 fail-closed 运行门控和结构/快速数值检查。全部证据统一提交 GPT 作一次 **Full B1 independent final review**；一旦硬错误或发现违反冻结 r2 阈值，必须即刻停止，不得以“一次审核”为由跳过安全门。此授权 **不允许 Gate M / Formal30k**。

## 0. 精确版本与两份 Owner 授权，严禁混用

**Diagnostic runner:** `wxwy/psm_wma` Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / `wxwy/cosmos-framework` Child/Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`. 不使用 live V3 较新 Child。  
**SOURCE Index8:** Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.  
**TARGET Packed128:** Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.  
**Original checkpoint:** `iter_000001300`, strict same-job **five-component** load; B0 fingerprint `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`.  
**Owner r2 numeric policy:** `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda` — cannot widen.

**Authorization A — outstanding P0 repeat0 TARGET only:**
- Existing Owner approval commit `b340c5e3c942372f7928c6aa205dcd54433fb42d`: `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_a3239591_11GiB.json`.
- Previous GPT `ALLOW_PACKED128` recorded in `docs/collab/chatgpt/reviews/2026-10-15_V3_B1_P0_a3239591_SOURCE_Index8_GPU_smoke_human_release_ALLOW_PACKED128.md`.
- P0 repeat0 SOURCE **has already completed**, DO NOT rerun. If P0 repeat0 TARGET **has not run**, it is Job 0 below under authorization A; if its already existing artifacts show that it completed, just verify identity and skip execution. Do not ever run the same job twice or overwrite its evidence.

**Authorization B — next six B1 jobs only:**
- **NEW Owner approval** `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_remaining_six_GPU_jobs_Owner_authorization_a3239591_11GiB.json`, pinned V3 commit **`0ae4a1c87c9ff7850aaa9c0b45a1ac44c7392eae`**.
- `approval_reference=OWNER_CHAT_2026-10-15_B1_COMPLETE_REMAINING_SIX_JOBS_ONE_REVIEW`, full `approved_scope.allowed_jobs_in_order` binding. Use this receipt for **only** the six exact combinations below; **never use the old P0 receipt** for them. This allows skipping intermediate GPT human reviews **only for nominal, internally validated** jobs.
- Both receipts bind the same a3239591 diagnostic code, frozen SOURCE/TARGET Root/Child pairs, B0 FP, r2 policy. Runner `_owner_receipt` checks top-level identity but not all `approved_scope`, so a separate DS `/tmp` fail-closed validator MUST reject job/profile/repeat/memory/order/limits not explicitly authorized. Do not edit or fabricate receipts; read originals from pinned V3 commits into /tmp and verify blob/sha.

## 1. Execute in this order: at most 7 more 8×H100 torchrun Jobs

| Sequence | Leg | Profile | Repeat | Authorization | Action |
|---|---|---|---|---|---|
| 0 | TARGET `packed128` | `P0_FIXED` | 0 | A | Only if not already completed; prior human release `ALLOW_PACKED128` applies |
| 1 | SOURCE `index8` | `P0_FIXED` | 1 | B | New job, independent original iter1300 restore |
| 2 | TARGET `packed128` | `P0_FIXED` | 1 | B | Paired with #1 |
| 3 | SOURCE `index8` | `P1_MATCHED_STOCHASTIC` | 0 | B | New independent original iter1300 restore |
| 4 | TARGET `packed128` | `P1_MATCHED_STOCHASTIC` | 0 | B | Paired with #3 |
| 5 | SOURCE `index8` | `P1_MATCHED_STOCHASTIC` | 1 | B | Independent rerun of P1 source |
| 6 | TARGET `packed128` | `P1_MATCHED_STOCHASTIC` | 1 | B | Paired with #5 |

**None of these runs depend on an intermediate GPT sign-off** after Job0 (SOURCE r0 release already granted), but all require normal fail-closed safety gates. Each run is precisely `--mode execute --profile <profile> --repeat <repeat> --leg <leg>`, `--nproc_per_node=8`, and **two native completed optimizer steps iter1301,1302** after full same-job iter1300 restore. Jobs must execute **serially**; do not run two 8-GPU jobs concurrently.

**Do not use the same authorization for different scopes.** Auth A Job0 only; Auth B jobs1–6 only, with exactly six independent torchrun launches maximum. If an artifact directory is already complete, verify and count it as previously executed; NEVER initiate a duplicate Job. The history is append-only.

## 2. Mandatory PRE-JOB checks (DS autonomous, no interim GPT request)

Before each independent job:
1. Refresh/read **exact** pinned diagnostic, SOURCE, TARGET Root and Child/Gitlink pairs, all clean; ensure no unexpected concurrent B1 job or foreign modifications. Existing Codex six-item production optimization must NOT be mixed into frozen trees.
2. Validate correct **original pinned receipt** against the exact job being launched, including `allowed_jobs_in_order` for B, order, six-job maximum, profile/repeat pair, fresh per-leg original iter1300 resume, original policy hash and B0 FP. Validate all no-save/no-latest/no-retry flags; do NOT merely rely on `v3_gateb1_run._owner_receipt`.
3. Retain original immutable DCP/latest. Use cheap original B1 lightweight read-only witness: all 44 paths; shard path/size/mtime only; small metadata and sidecar SHA; do NOT re-hash 32 shard bodies or B0/451GB dataset. Latest must still be `iter_000001300`. Verify `restore.status`, iter=1300, callback count=1, checkpoint FP, no shard rehash. Exact 8-rank witness values must be identical (and consistent with previous accepted source/target authority) or STOP.
4. Verify original input, index/cache receipt, model/tokenizer/VAE, two frozen config digests and all 8 Root+Child worktree identities. Only cheap `--mode prepare` if identity/config changed or prior valid source/target prepare cannot be referenced; do not repeat old accepted CPU suite or 451GB scan.
5. Use ASCII-clean `bash -n` validated command and launch from **that leg's frozen Child cwd** (`cd "$SRC_ROOT/cosmos-framework"` for index8, `cd "$TGT_ROOT/cosmos-framework"` for packed128); prevents Nemotron relative JSON failures. `$DIAG_ROOT/tools/gates/v3_gateb1_run.py` must remain from a3239591. No mixing PYTHONPATH with production V3.
6. **Fresh `nvidia-smi`** immediately before *every* Job: GPU0..GPU7 same 8×H100 physical mapping, each **driver-reported free >=11264MiB = 11GiB**. If any under, STOP without torchrun; never kill/pause/renice or alter other users. Contended throughput is NOT performance parity evidence.
7. `--output-root` MUST be the **same original consolidated** `/tmp/psm_v3_b1_p0_smoke_a3239591_20261015` (so the full comparator sees all profiles/repeats); exact per-job native artifacts go to `<leg>_<profile>_repeat<repeat>/`, each distinct and collision-free. Use a fresh unique `--job-name` for the internal Cosmos diagnostics per leg/profile/repeat. Do not overwrite old log or tensor files; `source_P0_repeat0` is already present. Keep Owner receipts separate on disk and record exact approval_ref per job.
8. No automatic job retries, no fallback to other Child, no changing r2 numeric thresholds, no DCP save, no writes to formal job/ckpt/latest.

If **any** precondition fails, return `B1_BATCH_BLOCKED_PRELAUNCH` with exact last-completed job + reason. Stop; don't continue to later jobs.

## 3. Mandatory POST-JOB checks and fail-fast

After **each** job, before launching next:
- Exit code **0** with rank0 `EVIDENCE_WRITTEN_NOT_B1_PASS`, no OOM, NCCL/CUDA, nonfinite, unexpected DCP/hardware error or traceback; process tree exited, no blocked ranks.
- **16 JSON + 16 PT** unique evidence files (8 ranks × iter1301/1302); all `schema=psm_v3_b1_native_capture_v1`, correct leg, profile, repeat, exact SHA, approval_reference, resolved config digest and B0 FP; full required `losses`, `fqn`, `fast`, `model_site_witnesses`, `cfg_transform_witnesses`.
- `iter1301: case=full / ga_counts=[128,128]`; `iter1302: case=terminal_partial / ga_counts=[122,128]` (require matching actual frozen baseline or STOP). Confirm FQN inventory is complete (action, generation, Local) and FP32 master/moments; `fast` is four tensors per selected slot.
- Original DCP/latest 44-file lightweight invariants unchanged from prelaunch and across ranks/legs. Record both before/after evidence, without full-shard rehash.
- For a newly completed matched `SOURCE/TARGET` pair, DS may use a narrow **read-only** CPU prefix check leveraging frozen `v3_gateb1_compare.validate_pair` and `_compare_numeric` to fail fast on obvious identity, stochastic-witness or r2 numeric mismatches, but does **not** declare formal `B1_GPU_PASS` or require intermediate GPT sign-off when no failure. If any necessary check establishes failure, **STOP all further GPU jobs** and send current evidence for GPT root-cause analysis. No posthoc thresholds or silent waiver.
- In all cases append a per-job immutable manifest with argv, SHA, receipt blob, prelaunch VRAM, start/end time, RC, expected artifacts, per-rank summaries, DCP immutability and status. Preserve stdout/stderr, JSON/PT, no overwrite.

**If previous P0 repeat0 TARGET had already run before this instruction:** do not redo it; verify that existing 16 JSON+16 PT and immutable DCP meet all checks; then start Job1.

## 4. After ALL jobs succeed — one read-only complete comparator + ONE GPT review

Run the existing pinned `tools/gates/v3_gateb1_compare.py` once **CPU-only** using:
```bash
"$DIAG_PY" "$DIAG_ROOT/tools/gates/v3_gateb1_compare.py" \
  --evidence-dir "$SMOKE_ROOT" \
  --output-report "$SMOKE_ROOT/b1_all_p0_p1_r0_r1_r2_owner_frozen_comparison.json"
```
Ensure the comparison output does not preexist; no overwrite. **Do not change** this comparator or numeric authority and do not launch GPU for the comparison.

Expected complete evidence:
- 2 profiles × 2 repeats × 2 legs × 8 ranks × 2 iterations = **128 JSON + 128 PT = 256 original native evidence files** (8 jobs total, including prior SOURCE P0 repeat0).
- Comparator **64 cross-leg rank-step pairs** plus **64 same-leg repeated-run numeric audits**, Full and Terminal Partial per profile.
- Exact Consumer identities/CFG/Sigma/Epsilon/masks, r2 Loss/Grad/Local-Fast-State/ΔP/Adam ΔM1/ΔM2; verify **all** FQN, elementwise, relative L2, cosine, nearzero handling and strict policy hash.
- `all_candidate_thresholds_pass=true` is required but **NOT** a B1 final verdict (script explicitly emits `gpu_gate_approved=false`). Check all 16 reports per job and rank-local restore/DCP witnesses; note the comparator itself doesn't globally compare lightweight immutability witnesses across all jobs, so DS must include separate audited matrix.
- If comparator raises, returns a mismatch or `all_candidate_thresholds_pass=false`, **STOP** with full first failing profile/repeat/leg/rank/iter/FQN metric, no new jobs/threshold widening. Do not label parity PASS.
- Bring one comprehensive `DS_PRO_V3_B1_full_GPU_r2_numeric_batch_a3239591_2026-10-15.md` report to GPT with machine-readable comparator JSON, complete all-eight-job manifest table, first/worst metric and outlier FQNs, all repeat-input hashes, all rank/iter DCP witnesses and original latest integrity, full stdout/stderr/RC. Supply attached JSON or accessible file bytes for independent review; a brief high-level summary alone is not sufficient for formal closure.

**Only GPT will do one fresh full-B1 evidence review at end** (or earlier if an error stops the batch), against exactly the unchanged diagnostic implementation pair and Owner r2 policy. This is not a fresh code re-review of the unchanged a3239591; code changes in the middle make a new formal pair and require a fresh independent review. If B1 formally passes, Gate M checkpoint migration becomes the next **separately authorized** stage, and Formal30k remains HOLD.

## 5. Strict non-authorizations

- No Gate M or automatic Checkpoint migration.
- No Formal30k Fresh/Resume, data scan, RoboCasa task eval, or launch based on this request.
- No B0 repeat/451GB offline dataset rerun; no re-run of passed 149 CPU tests.
- No changing B1 Source/Target/Diagnostic/Owner r2 code SHA, no merge with Codex E1/E2/T1/P1.
- No CUDA warm-start/caching workaround that changes stochastic witnesses, strict restore or checkpoint authority.
- DS_PRO only executes GPU and read-only CPU evidence checks; DS never commits production code or edits GitHub.
