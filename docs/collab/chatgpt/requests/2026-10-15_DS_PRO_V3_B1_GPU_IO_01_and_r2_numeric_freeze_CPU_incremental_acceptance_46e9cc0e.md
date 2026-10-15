# GPT → DS_PRO — V3 Gate B1 GPU-IO-01 修复 + Owner r2 数值冻结：增量 CPU 验收

**Date:** 2026-10-15  
**Executor:** DS_PRO independent **READ-ONLY** tests/evidence (may build its own temporary scripts under /tmp; **MUST NOT modify GitHub code**).  
**Scope:** `B1_GPU_IO_01_AND_R2_NUMERIC_FREEZE_CPU_INCREMENTAL` only. **NO GPU/torchrun/model instantiate/real DCP load/451GB dataset walk/B0 rerun/Gate M/Formal30k**.
**NEW exact candidate diagnostic CODE SHA:** `46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a` (`wxwy/psm_wma:v3-gateb1-numeric-implementation-20261014`), Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`.  
**Previously accepted diagnostic code SHA:** `dfeace66bbce549bf94a447c18f3d51e5dd2e376` — its 138 CPU tests and 4× legal Prepare were accepted for that **old** formal pair. The new SHA must receive FRESH incremental evidence; do NOT repeat unrelated B0/451GB/whole-V3 audits.  
**Owner frozen numeric policy:** `docs/collab/chatgpt/designs/2026-10-15_V3_GateB1_r2_numeric_Owner_frozen_preGPU.md`; `numeric_policy_sha256=bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`. This is **NOT** GPU authorization.

## 1. First lock formal identities and diff

Detached clean checkout at exactly `46e9cc0e...`; independently report `git rev-parse HEAD`, `git ls-tree HEAD cosmos-framework`, child HEAD and `git diff dfeace66..46e9cc0e --name-only`. Expected **9 paths** all in `tools/gates/`: added `v3_gateb1_authority.py`, changed `v3_gateb1_dcp_transient.py`, `v3_gateb1_native_driver.py`, `v3_gateb1_run.py`, `v3_gateb1_metrics.py`, `v3_gateb1_compare.py`, and 3 corresponding tests. **Frozen original production SOURCE/TARGET pairs and live V3 production Child are unchanged**.

## 2. One CPU-only verification batch

Use the same formerly passing DS venv, no `ruff --fix`, no real DCP:
```bash
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
mapfile -t GATE_IMPL < <(find tools/gates -maxdepth 1 -type f -name 'v3_gateb1_*.py' | sort)
mapfile -t GATE_TEST < <(find tools/gates -maxdepth 1 -type f -name 'test_v3_gateb1_*.py' | sort)
test "${#GATE_IMPL[@]}" -eq 12
test "${#GATE_TEST[@]}" -eq 11
python -m py_compile "${GATE_IMPL[@]}" "${GATE_TEST[@]}"
ruff check --no-cache "${GATE_IMPL[@]}" "${GATE_TEST[@]}"
python -m pytest -q tools/gates/test_v3_gateb1_*.py
```
Expect **23/23 py_compile and Ruff 0 findings**, previous 138 tests + **6 added negative/policy tests = at least 144** (report actual count, no inventing PASS). If ANY FAIL, STOP and return exact file:line/errors; no DS production fixes.

## 3. Functional acceptance — must establish contract, not just green count

A. **No repeated 32-shard data hashing.** The real `strict_transient_load` calls `_lightweight_immutability_snapshot` before/after; `snapshot_checkpoint(...,hash_shards=False)` MUST NOT call `sha256_file` on `*.distcp` content. Real small fixture = 32 fake shard files + 4 `.metadata` + 8 rank sidecars. Verify file path, size, mtime for shard entries and SHA256 of 4 metadata + 8 sidecars, required 44 entries, before/after equal; changes (mtime or small metadata content) fail closed. Do NOT touch the real iter1300 checkpoint.

B. **Full B0 fingerprint stays distinct** from light witness: authoritative `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999` remains ConsumerKey/restore `source_checkpoint_fingerprint`; cheap witness is a DIFFERENT field `runtime_lightweight_immutability_witness`. Wrong supplied original B0 FP rejected before actual DCP load. No Owner GPU approval file is generated.

C. **No-save, strict DCP, same-job Local** remain intact: `exact_readonly_same_job_source` scope still covers both GA2 steps, never invokes `Trainer.train()`/`save()`, actual DCP loader contract still requires model/optim/scheduler/trainer/dataloader with original frozen source. No writes to latest/checkpoint/formal directories.

D. **Owner numeric freeze real code binding**: `v3_gateb1_authority.py` must have exact hash `bcb9f8d6...` and all r2 numbers; Grad FP32/BF16, Local 4 FP32, Master ΔP, Adam ΔM1/ΔM2, loss FP32/BF16, one-sided near-zero + missing FQN failure semantics. Compare report now says `OWNER_FROZEN_R2_NUMERIC_EVIDENCE_ONLY_GPU_GATE_NOT_APPROVED` while `gpu_gate_approved=false`. Invalid `numeric_policy_sha256` in a synthetic Owner receipt MUST be rejected; do not test with an actual signed approval. `--mode prepare` remains standard-library-only, no Torch/CUDA/Cosmos, and requires exact B0 checkpoint fingerprint; note this intentional stricter metadata check.

E. **Still unknown at CPU scope**: real FSDP8/native DCP loading, CUDA stochastic parity and dtype/master/moment runtime coverage, vision shift bucket 256, GPU time/memory. Mark as `GPU_UNVERIFIED`, not PASS. Original DS Readiness Lane A/B/C CPU evidence accepted at old SHA; new strict fingerprint guard may be verified via synthetic/cheap CPU tests rather than redoing 4 legal prepares.

## 4. Report/STOP behavior

Write ONE consolidated report (in DS /tmp or pasted back to Owner; no GitHub edits):
`DS_PRO_V3_B1_46e9cc0e_IO01_FrozenR2_CPU_Verification_2026-10-15.md`

Include exact formal Root/Child SHA, 9-file diff, command exit codes, actual test count, API/snapshot shape, 32 fake shards never content-read, mutation/wrong B0 FP/owner policy negative cases, remaining GPU-unverified ABI hazards and **clear PASS/BLOCKED**. All DS fixes/waivers require a separate GPT-reviewed source patch. GPT will review new exact formal pair on DS results and update the canonical review/Inbox.

**Owner has frozen numerical thresholds but HAS NOT authorized 8×H100.** Never execute GPU, torchrun, actual DCP restoration, checkpoint writes, migration or formal training under this request.
