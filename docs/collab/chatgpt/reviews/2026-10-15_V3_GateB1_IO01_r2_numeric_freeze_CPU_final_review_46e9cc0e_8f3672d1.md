# PSM-WMA V3 — B1 GPU-IO-01 + Owner-r2 Numeric Freeze: Final Incremental CPU Gate Review

**Date:** 2026-10-15
**Reviewer:** GPT — independent Code / Evidence / Gate reviewer
**Verdict for `B1_GPU_IO_01_AND_R2_NUMERIC_FREEZE_CPU_INCREMENTAL`: `APPROVE_TO_CLOSE` — CPU code+fixture gate PASSED.**
**Owner GPU authorization:** **NOT GRANTED / `GPU_NOT_AUTHORIZED`**. The approval **only clears the outstanding GPU Readiness CPU-level remediation**, not actual FSDP8 or numerical parity.
**Formal diagnostic implementation Root:** `46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a`
**Formal diagnostic Child/Gitlink:** `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`
**Parent / last CPU Code Gate:** `dfeace66bbce549bf94a447c18f3d51e5dd2e376` / `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`, previously APPROVED (138 synthetic CPU tests/22 Ruff).
**SOURCE Original:** `b159f45906f7261d028aecc226ab7f2bb9807eb9` / `937066ffd90f2bf783ad4fbb4909e9c0b8922982`
**TARGET Original:** `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`
**Owner-ratified numeric policy:** `docs/collab/chatgpt/designs/2026-10-15_V3_GateB1_r2_numeric_Owner_frozen_preGPU.md`; SHA256 `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`.
**Original B0 authoritative full-shard checkpoint fingerprint:** `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`.
**Independent executor evidence:** Owner supplied `DS_PRO — V3 Gate B1 GPU-IO-01 + Owner r2 Numeric Freeze: Incremental CPU Verification (46e9cc0e)`, 2026-10-15 (91 lines). DS_PRO did not change repo code, open the real DCP, run GPU or rerun B0/451GB.

## 1. Exact-pair provenance and reviewed diff

GPT independently fetched GitHub branch ref, commit parent/tree, Child Gitlink, and `dfeace66..46e9cc0e` diff. The candidate branch HEAD is exactly `46e9cc0e...` with parent exactly `dfeace66...`; Gitlink remains `8f3672d1...`; original SOURCE/TARGET and V3 live Child are unmodified.

**Only 9 files, all within isolated `tools/gates/`:** added `v3_gateb1_authority.py`, modified `v3_gateb1_dcp_transient.py`, `v3_gateb1_native_driver.py`, `v3_gateb1_run.py`, `v3_gateb1_metrics.py`, `v3_gateb1_compare.py` and tests `test_v3_gateb1_dcp_transient.py`, `test_v3_gateb1_run.py`, `test_v3_gateb1_metrics.py`. No frozen Child, model, trainer, dataset code, original checkpoint, or startup V3 production code changed. GPT verified the actual changed implementation source, not only the DS prose summary.

## 2. Requirement → concrete evidence → decision

| Acceptance requirement | Corroborating exact-implementation behavior / DS independent evidence | Conclusion |
|---|---|---|
| Formal identity/scope | Exact branch/commit/Child and GitHub 9-file diff; DS clean detached Root+Child | PASS |
| 23-file syntax | 12 implementation + 11 tests py_compile exit 0 | PASS (DS) |
| 23-file Ruff | Ruff `--no-cache`, 0 findings, exit 0 | PASS (DS) |
| Full scoped CPU synthetic tests | **144 passed in 1.82s**, prior 138 + six newly introduced negative/policy tests | PASS (DS) |
| B1-GPU-IO-01: no shard rehash | `v3_gateb1_dcp_transient._lightweight_immutability_snapshot` calls original B0 `snapshot_checkpoint(hash_shards=False)`. Original `v3_packed128_gateb_compare.snapshot_checkpoint` hashes 4 small metadata + 8 sidecars, not `*.distcp`; verifies 32 shard paths/sizes/mtimes. New fresh fixture counted **24 small-file hash calls / two snapshots** and 0 shard-content hashes | **CLOSED** |
| Pre/post immutability fail-closed | Two lightweight snapshots compared with `unchanged_checkpoint`. DS synthetic fixture rejects modified metadata hashes and shard mtime, requires 44 entries (32 shards+4 metadata+8 sidecars). | PASS (CPU) |
| Full B0 authority separate from light runtime witness | `strict_metadata` and `strict_transient_load` insist on exact fixed B0 full-shard FP `2e409afe...`; load result retains it in `source_checkpoint_fingerprint`/`authoritative_b0_checkpoint_fingerprint`, separate from `runtime_lightweight_immutability_witness`, sets `runtime_shard_contents_rehashed=False`. Wrong B0 FP rejected before DCP read. | PASS |
| Strict same-job DCP + no-save | `v3_gateb1_run.py` scopes `exact_readonly_same_job_source` over build/load **and** both GA2 native steps; strict five components, source path `iter_000001300`, no `Trainer.train`, no `Checkpointer.save`; old 138 regression cases plus static byte checks still PASS | PASS in CPU scope |
| Owner numerical r2 frozen in actual comparison | New `v3_gateb1_authority.py` stdlib-only canonical pre-GPU JSON hash; DS independently recomputed exact `bcb9f8d6...`. `v3_gateb1_metrics.py` imports and validates frozen policy then uses those values (including BF16 scalar rule and fail-closed unsupported dtype); `v3_gateb1_compare.py` emits `OWNER_FROZEN_R2_NUMERIC_EVIDENCE_ONLY_GPU_GATE_NOT_APPROVED`, `numeric_thresholds_owner_frozen=true`, `gpu_gate_approved=false`. | PASS |
| Explicit GPU authorization still required | `v3_gateb1_run._owner_receipt` requires `gate=V3_PACKED128_B1_GPU_OWNER_APPROVED`, `authorized=true`, `numeric_thresholds_frozen=true`, exact `numeric_policy_sha256`, current exact diagnostic implementation SHA, both frozen pairs, B0 FP and a separate nonblank Owner approval reference. DS only used mock authorization negative tests, never an actual GPU approval. | PASS (barrier remains) |

This accepts **reported tests on the DS host**, not a GPT claim of executing DS commands or having access to the private training-machine artifacts. GPU performance, FSDP full-state load, selected FQN gradients and optimizer FP32 master/moment dtype, on-device stochastic site coverage, vision bucket 256 and numerical parity remain **GPU_UNVERIFIED**.

## 3. Detailed numerical signoff interpretation

Owner's `2026-10-15` approval freezes r2 **before seeing any CUDA discrepancies**: per-selected-FQN Gradient relL2 FP32 ≤0.2%, BF16 ≤3%; each Local FP32 Fast State tensor ≤0.2%; FP32 ΔP ≤3%, ΔM1 ≤3%, ΔM2 ≤5%, plus role-specific elementwise atol/rtol/cosine/norm-floor and one-sided-nearzero fail-close. Each active weighted loss component: FP32/FP64 atol1e-6 rtol1e-5, BF16 atol/rtol 2e-2; optimizer steps/discrete Consume/Mask/CFG/Sigma/Epsilon exact, run-to-run same-policy limits. All eight ranks, two consecutive post-1300 steps, two repeats per leg, both P0/P1, both Full and Terminal Partial. No posthoc tolerance relaxation.

Note: B1 native weighted loss capture converts to FP32; the comparator applies **strict FP32 loss thresholds** to the captured dtype, consistent with the frozen review. Actual native loss dtype is not claimed from this conversion.

## 4. Residual safety/launch conditions — not a reopened CPU bug

The code's lightweight witness is **not a cryptographic re-proof of all shard contents**. That is deliberate: prior B0 full-shard evidence is accepted; the B1 code asserts the authoritative B0 FP while its cheap snapshot checks path/size/mtime and small-file hashes. It is a valid optimization under a controlled read-only original iter1300 checkpoint, not a claim that new 32-shard content hashes were recomputed. For the eventual GPU analysis, independently require all emitted `runtime_lightweight_immutability_witness` values to be **identical across 8 ranks, both frozen legs, P0/P1 and repeats** as an additional provenance acceptance check (the current generic comparator does not itself cross-pair this newly added field). Mismatch => BLOCKED, not parity PASS. The original checkpoint/latest must remain unchanged.

Before **any** real B1 `torchrun`, the Owner must explicitly sign a *separate* GPU authorization with exact diagnostic SHA `46e9cc0e...`, frozen pairs and policy SHA `bcb9f8d6...`, the B0 fingerprint, bounded execution scope (8×H100, P0/P1, Full/Terminal and two repeats, output solely isolated /tmp), emergency stop on fail-closed condition, and no checkpoint save. GPU-time fail-close checks: actual Native Per-Consumer 256 vision bucket and noise site witnesses, disabled sound/attention dropout, FSDP master/moment dtypes and optimizer selected FQN inventories. Any ABI/hardware issue is reported, NOT silently fixed by DS or retroactively labeled pass.

No Gate M migration, Formal30k resume, 451GB dataset re-acceptance or full V3 audit is authorized here. B0 CPU, older B1 CPU and Legal Prepare/Config CPU receipts remain CLOSED; no need to rerun due to this bookkeeping review.

## 5. Final scoped formal verdict

- **`B1_GPU_IO_01_AND_R2_NUMERIC_FREEZE_CPU_INCREMENTAL`: `APPROVE_TO_CLOSE`, blocker `B1-GPU-IO-01` CLOSED.**
- **Owner r2 numeric standard: `FROZEN`** as a separate human approval, enforced in diagnostic code and bounded comparator.
- **B1 GPU execution: `OWNER_GPU_AUTHORIZATION_REQUIRED` / `GPU_NOT_AUTHORIZED`**; runtime behavior and numeric parity `GPU_UNVERIFIED`; no `B1_GPU_PASS` declaration.
- **Gate M and Formal30k:** HOLD.

This Gate review is persisted under `docs/collab/chatgpt/reviews/` and must have an append-only `CODEX_INBOX.md` entry referencing this exact report. A V3 review/Inbox docs commit is bookkeeping, not a replacement for the validated diagnostic Code SHA.
