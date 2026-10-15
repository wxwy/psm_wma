# GPT → DS_PRO: B1 P0 TARGET Packed128 人工放行（ALLOW_PACKED128）

**Date:** 2026-10-15  
**Exact release:** **`ALLOW_PACKED128`**. SOURCE Index8 success evidence has passed the **source-to-target human safety gate only**. TARGET is job #2 and **LAST** allowed under existing Owner GPU receipt. **No GPU numerical parity has yet been approved.**  
**Human-release review:** `docs/collab/chatgpt/reviews/2026-10-15_V3_B1_P0_a3239591_SOURCE_Index8_GPU_smoke_human_release_ALLOW_PACKED128.md` (commit `34227da89c60a852ecdb29ed4752678d3d86e7e3`).

## 1. Exact unchanged identities

- B1 Diagnostic executor Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`.
- SOURCE Index8 Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`: already completed P0_FIXED repeat0, SOURCE_RC=0, 8 rank × two iterations.
- **TARGET Packed128** Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
- Authoritative Owner new receipt exact GitHub auth commit `b340c5e3c942372f7928c6aa205dcd54433fb42d`, path `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_a3239591_11GiB.json`. Do not manually change receipt or reuse old 46e9 approval.
- Original B0 iter1300 DCP FP `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`; frozen Owner r2 policy SHA `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`.

## 2. HARD GATES immediately before TARGET (all required; failure => STOP with no GPU)

1. Re-confirm pristine diagnostic/SOURCE/TARGET Root and Child git HEADs and root Gitlinks, all worktrees clean, exact P0-only Owner receipt scope/approval reference, no job already executing. Frozen SOURCE is immutable, not a dynamic/current production HEAD.
2. **Verify SOURCE restoration witness** from its 16 JSON files: all `restore.status=STRICT_DCP_LOADED_TRANSIENT_NO_SAVE`, `restore.iteration=1300`, `restore.dataloader_state_load_calls=1`, `restore.runtime_shard_contents_rehashed=false`, authoritative original B0 FP fixed, all `runtime_lightweight_immutability_witness` valid and equal across 8 ranks×2 iterations. Use original B1 `strict_transient_load` contract: no shard-content rehash; compare cheap path/size/mtime and small metadata/sidecar hashes against authentic previously frozen authority. Any change / missing field => STOP and return evidence to GPT, no launcher edits to bypass.
3. Original `iter_000001300` DCP/latest immutable; `latest_checkpoint.txt=iter_000001300`; no writes, added files, or modified metadata/sizes/mtimes against accepted cheap witness. Do not rerun B0 full corpus or 32-shard SHA256.
4. Corrected **ASCII-only** TARGET launcher from pinned frozen Child CWD `cd "$TGT_ROOT/cosmos-framework"` (prevents Nemotron relative JSON failure), validate `bash -n`, no non-ASCII/NBSP. TARGET `--mode prepare` already PASS as reported; do not need to repeat if scope/worktree/assets unchanged.
5. Target output directory `/tmp/psm_v3_b1_p0_smoke_a3239591_20261015/packed128_P0_FIXED_repeat0` has no conflicting evidence files; SOURCE existing evidence is retained. Stop on collisions, do not overwrite or auto-retry.
6. **Immediately before TARGET** query all 8 pinned H100 devices, require each `nvidia-smi memory.free >= 11264MiB` (11 GiB). Do not substitute historical SOURCE snapshots. If any card under threshold, STOP until resources qualify; never kill/pause/nice foreign processes.

## 3. Allowed second job — TARGET only

Use existing DS exact-argument launch script, sanitized to ASCII, and existing `v3_gateb1_run.py` on pinned diagnostic Root. **Only permitted parameters:** `--mode execute --leg packed128 --profile P0_FIXED --repeat 0 --root-worktree "$TGT_ROOT"` plus exact previously validated assets/config, original iter1300 DCP **read-only**, same authorized `--owner-authorization-json`, `--output-root` under isolated /tmp, and `--nproc_per_node=8`. Required completed iterations: 1301 and 1302. One job only. Re-using `job-name` or targeting the wrong Child CWD must not bypass separate output collision/identity checks.

**Stop at TARGET completion**, even if exit0. Capture full log/exit code and 8 ranks×2 iterations source/target pair of JSON/PT; confirm native CFG+sigma/epsilon witnesses, selected FQN Gradient / FP32 master ΔP and Adam ΔM1/ΔM2, Local FP32 fast-state, losses and exact identity. Confirm eight-rank restore and no DCP/latest writes.

You may run *CPU-only read-only* existing P0 comparator on resulting collected source/target artifacts without changing Owner numeric threshold or invoking GPU. Report the actual first failing FQN/field and reproducibility limitations if compare cannot establish B1; **do not declare B1 GPU PASS solely from SOURCE/TARGET exit0 or equal loss**. Only the reviewed results determine next P0 or B1 stage.

## 4. Evidence report and STOP

Send to GPT: `DS_PRO_V3_B1_P0_a3239591_TARGET_Packed128_GPU_Smoke_2026-10-15.md`, including:
- pre-target SOURCE restore lightweight witness matrix (rank×step), pre/post DCP small-file hashes and shard size/mtime, current latest, new 8-GPU live memory gate, pinned receipts, clean SHAs;
- TARGET logs/RC, 16 JSON+16 PT, full-vs-terminal GA counts, source/target per-consumer witness hashes and selected FQN inventories, fast slots, optimizer state dtypes;
- any CPU-only P0 comparator result, exact r2 policy match, no posthoc widening;
- if no error: **TARGET COMPLETE — WAIT GPT NUMERIC REVIEW**. If any failure: **BLOCKED**, preserve artifacts and do not re-run; stop only own job.

**Explicit forbidden:** other GPUs/jobs, P0 repeat1, P1, Gate M, Formal30k, DCP/latest saves, Codex E1/E2/T1/P1, B0/451GB reruns, auto-retry, arbitrary threshold changes. This request is a human TARGET release, not a new code/GPU parity formal verdict.
