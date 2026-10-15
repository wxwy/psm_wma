# GPT → DS_PRO: 新 Owner 授权后执行 V3 B1 P0 SOURCE GPU Smoke（11GiB live-free Gate）

**Date:** 2026-10-15  
**Owner says:** “我授权，按照之前的经验，单卡11G就可以了”。  
**Owner authorization receipt (new):** `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_a3239591_11GiB.json`, pinned **authorization document** commit `b340c5e3c942372f7928c6aa205dcd54433fb42d`. `V3` documentation HEAD is NOT the diagnostic implementation SHA.  
**Exact frozen diagnostic implementation:** Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child/Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`.
**Source Index8:** `b159f45906f7261d028aecc226ab7f2bb9807eb9` / `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.  
**Target Packed128:** `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.  
**B0 FP:** `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`. **Numeric r2 SHA256:** `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`.

**Authority granted:** Two jobs at most, **P0_FIXED repeat0 only**, 8×H100, same original read-only iter1300 DCP, complete iter1301/1302. Launch order strictly **SOURCE first → return all source evidence for explicit human review/release → TARGET**. NO P1, repeat1, Gate M, Formal30k, save/latest write, auto-retry, or other GPUs; do NOT interfere with co-resident processes. CPU Local-RNG Gate already CLOSED; **do not rerun B0/451GB/149 tests**.

## A. Owner's new live-memory condition

- Old `16384 MiB` historical approval floor **does not apply to this NEW a3239591 receipt**. New Owner floor is **`11264 MiB per card` = 11 GiB of DRIVER-REPORTED FREE device VRAM** on **each** of GPU0–GPU7.
- A prior GPU snapshot above threshold is **not** a real-time launch check. Immediately before **each** job query all eight; refuse torchrun if any <11264 MiB, the query fails or the GPU mapping changes. Do not pause/kill/renice another user's work.
- Co-resident GPU loads may rise dynamically: a pass at 11GiB free is not a guarantee of no OOM. Monitor for own OOM, NCCL/CUDA/nonfinite errors or DCP mutation and safely halt own run only. Under 11GiB at preflight => STOP, do not bypass or treat model `allocated` memory as `free`.

## B. Close earlier RUNBOOK-only findings; these checks MUST pass before SOURCE

1. Read the new authorization JSON **verbatim** from the pinned V3 GitHub authorization-commit SHA into **/tmp only** (not a synthetic copy of the old 46e9 receipt). Example source URL:
   `https://raw.githubusercontent.com/wxwy/psm_wma/b340c5e3c942372f7928c6aa205dcd54433fb42d/docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_a3239591_11GiB.json`
   If unavailable, use an authenticated GitHub checkout at this exact commit. Don't manually rewrite JSON or use old local receipt. Inspect `auth.implementation_sha=a3239591...`, `diagnostic_child_gitlink=8f3672d1...`, frozen four pairs, Owner policy/FP.
2. Build and **check** a pure-ASCII shell runbook in `/tmp`: initial pasted DS report contained NBSP `U+00A0` in executable command lines. Use `bash -n` and a byte-level ASCII / whitespace validator for actual shell script, with explicit flags and path quoting. Do not launch from those uncorrected copy/pasted lines.
3. Validate **all** `approved_scope` fields of the new actual receipt, not merely the subset the runner's `_owner_receipt` checks: `gate_stage=B1_P0_FIXED_2_STEP_SMOKE_ONLY`, `profiles=["P0_FIXED"]`, `repeats=[0]`, `legs_in_order=["index8","packed128"]`, `completed_iterations=[1301,1302]`, `world_size=8`, `maximum_independent_torchrun_jobs=2`, `require_source_success_before_target=true`, `require_manual_source_to_target_release=true`, `co_resident_with_other_users_approved=true`, `min_free_gpu_memory_mib_at_launch=11264`, output under `/tmp`, protect DCP/latest, no rerun/other stages/foreign-user interference. Missing/mismatched field => STOP.
4. Execute only the **two cheap CPU-only `--mode prepare` calls** for pinned SOURCE and TARGET: log real exit0, `PREPARE_ONLY_NO_GPU_OR_DATASET_SCAN`, resolved config digests (SOURCE `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`, TARGET `1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a`), no data/DCP payload reads; `checkpoint_write_authorized=false`. Previous prepare reports may be retained for reference, but new-SHA launch readiness requires direct execute evidence. Do not repeat old large CPU suites.
5. Revalidate exact three Root/Child pairs and Gitlinks/clean worktrees; original `latest_checkpoint.txt=iter_000001300`; all immutable assets; new unique `SMOKE_ROOT` below /tmp, with no pre-existing evidence file collisions.
6. Immediately before SOURCE torchrun, capture 8-device read-only **live** `nvidia-smi` memory.free and enforce >=11264 MiB **on every device**. Use a small validator such as this, against the actual GPU mapping (ASCII-only):

```bash
python - <<'PY'
import subprocess
raw = subprocess.check_output(
    ["nvidia-smi", "-i", "0,1,2,3,4,5,6,7",
     "--query-gpu=index,memory.free", "--format=csv,noheader,nounits"],
    text=True,
)
seen = {}
for line in raw.splitlines():
    index, free_mib = (int(x.strip()) for x in line.split(","))
    if index in seen:
        raise SystemExit(f"duplicate GPU index: {index}")
    seen[index] = free_mib
print("GPU_FREE_MIB:", sorted(seen.items()))
if set(seen) != set(range(8)):
    raise SystemExit("HARD STOP: wrong GPU set")
if any(v < 11264 for v in seen.values()):
    raise SystemExit("HARD STOP: below 11GiB free on at least one GPU")
print("P0_OWNER_11GIB_LIVE_VRAM_GATE_PASS")
PY
```

## C. Allowed GPU execution after all B guards PASS (NO automatic TARGET)

1. Source only: from `$SRC_ROOT/cosmos-framework` CWD (fix for CWD-relative Nemotron JSON), using existing pinned `$DIAG_ROOT/tools/gates/v3_gateb1_run.py --mode execute --profile P0_FIXED --repeat 0 --leg index8`, with `--owner-authorization-json` pointing to the **new** 11GiB Owner receipt; all remaining file/options identical to previously frozen DS runbook, except a **fresh** /tmp output namespace. Eight ranks, exactly two completed native iterations: 1301/1302; original DCP/latest read-only. Before actual command: ensure any script from report was sanitized of NBSP and validates with `bash -n`.
2. **Immediately STOP after SOURCE.** Return 8 ranks × 2 iterations' all JSON/PT native/stochastic/CFG witnesses, launch logs, exit code, actual free-VRAM snapshot, original DCP/latest postcheck, no save/overwrite evidence and any errors. Human GPT/Owner reviews the real SOURCE output and issues an explicit, separately recorded `ALLOW_PACKED128` before TARGET. Do not self-release based on merely typing the string.
3. After explicit manual release only: recheck the same source/target identity, receipt, corrected ASCII command, latest/DCP, **new** all-eight live free-VRAM >=11264 MiB; then one independent TARGET Packed128 torchrun in its own frozen Child CWD. Same P0/repeat/iters and receipt. No automatic retries or fallback changes.
4. P0 numerical comparison under unchanged Owner r2 thresholds follows **only after** both legs succeed. Gate M/Formal30k remain HOLD pending full B1 GPU verdict and separate approval.

## D. Evidence response required

`DS_PRO_V3_B1_P0_a3239591_Owner11GiB_SOURCE_GPU_Smoke_2026-10-15.md` with:
- exact diag Root/Child, source & target pairs; approval **document commit SHA**, new Owner JSON path and scope-check outputs;
- bash ASCII check, **both CPU prepare** logs/exit codes and frozen resolved digest;
- all-eight GPU free snapshot immediately prior to SOURCE; job time and co-resident protection;
- SOURCE 8 ranks × iter1301/1302 raw reports/tensors, no OOM/CUDA/NCCL/nonfinite, actual exit code, checkpoint/latest immutability check;
- explicit **SOURCE complete → WAIT HUMAN RELEASE**, or FAIL/BLOCKED with exact error and stop. No fabricated TARGET outcome.

If operational gates cannot be passed, report `AUTHORIZED_BUT_BLOCKED_PRELAUNCH` and STOP without GPU execution. This new permission **does not** mean `P0_GPU_PASS`. DS does not modify GitHub, B1 Source/Target or unrelated Codex production improvements.
