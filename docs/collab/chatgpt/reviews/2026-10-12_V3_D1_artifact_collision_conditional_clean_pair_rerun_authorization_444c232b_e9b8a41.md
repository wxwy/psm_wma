# DS_PRO — V3 D1: Evidence-corrupt rank collision decision + conditional one-pair clean retry

**Date:** 2026-10-12
**Scope:** `D1_CLEAN_EVIDENCE_RECOVERY` (existing JSON SHA screen, external /tmp Harness evidence-only repair, conditional one paired 8×H100 retry).
**Fixed Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e` / **Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Source review:** `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_paired_GPU_artifact_collision_evidence_review_444c232b_e9b8a41.md`; **Owner DS incident report:** `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_paired_prestep_rank_collision_owner_relay.md`.
**Original Formal30k:** STOPPED, its original DCP/config/latest immutable. **C1 remains CLOSED.**

## Current decision

**Select A rather than B/C**, but avoid a duplicate 8×H100 run if every captured in-memory gradient already matches bit-for-bit.

### Parallel CPU workstream 1 — Audit surviving in-memory gradient hashes

- Use existing **untouched** `/tmp/ds_pro_v3_d1_r1/gpu_run/reference_attempt_01` and `optimized_attempt_01` rank0..7 JSON. No torchrun/GPU/DCP Load.
- For each **required** (rank, param FQN, DTensor local shard, dtype, shape, grad_present) compare SHA256 originating from **in-memory .grad before file write** and actual Source/Optimizer selected parameter inventory. Compare all actual selected groups: Generation/Action/Local including w0_fast_*. Investigate why summary calls the denominator `296` vs prior inventory selected-count and identify exact inclusion/exclusion set; mismatched/missing/unknown entries do NOT count as equal.
- Compare mode pair's input source path, iteration800, strict source `warm_start=False`, config digest, rank RNG before/after, CFG decisions and frozen GA sample/segment/valid counts, plus real Local candidate identity and available in-memory fingerprints. Member losses already reported bitwise equal; verify field-level evidence.
- Output `all_required_grad_sha_equal`, per-rank `matched/missing/mismatched` and first failing rank/FQN (never fabricated), `provenance_verified`. Do not use overwritten external grad tensors for this comparison.
- **If ALL** required recorded in-memory grad hashes and all identity/candidate checks match, and provenance is reliable: label `NO_RERUN_BIT_EXACT_CANDIDATE`, **do not run GPU**, return consolidated report to GPT. Acknowledge full payload retention failure and make no autonomous final Gate PASS.
- Otherwise retain `D1_PRESTEP_UNVERIFIED`, proceed to the conditional clean retry below only if CPU workstream 2 passed, with required GPU permission/guard. Hash inequality **alone** is not true numeric tolerance FAIL.

### Parallel CPU workstream 2 — Fix and fully prove immutable rank-local artifact writer

- Existing external /tmp-only file: `/tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py:231`. Replace shared `grad_tensors/{sanitize(fqn)}.pt` path with a **mode/attempt/rank/FQN unique** relative path, e.g. `grad_tensors/rank_{rank}/{sanitize(fqn)}__{sha256(fqn)[:16]}.pt`; verify no cross-rank or sanitize-FQN collision. Output roots are already attempt02 unique; do not modify attempt01.
- Use file creation that fails on existing path (`open(path, "xb")` or equivalently proven exclusive scheme); no silent overwrite even within one rank. Save true `.grad`/local DTensor shard detached to CPU and embed its exact relative path, FQN, rank, dtype, shape, numel and in-memory SHA in rank JSON. Re-read *every* persisted tensor using trusted `torch.load(weights_only=True)` in CPU-only checksum inspection, require bytes SHA/dtype/shape match. Stable JSON/metadata naming and full candidate fast-state manifests must also be rank-safe. Keep original H2 tolerances unchanged.
- Run CPU-only synthetic **8 ranks writing the same FQN**, mixed FQN sanitize-collision case, duplicate-write refusal, 8-rank readback and single corrupted-byte/error detection; check full expected selected FQN inventory/completeness vs produced manifest. `py_compile` / AST / static preflight / existing J1 resource Guard and no-step forbidden-call checks PASS. No actual model/GPU in CPU work.
- **Independent provenance requirement:** Prior formally frozen H1 SHA `e854f7a4df27372863387b8706739601f16f44d1e68fb93e59755719815c50c5`, H3 Launcher `9b615b01e9025f6925da50d5f70bd4448dbb7020f364e3212e876ff8990e49cd`, H2 Comparator `3e84d2c676903bd471b38af6e04df3df4b18208f04c534cef91f19b2dcd06b60`. Incident reports executed H1 hash prefix `ae428da4…` and Launcher `8d633889…`. Document exact executed versions/full SHA and diff/timeline vs pinned authority. Narrow fix is evidence-only output disambiguation and accompanying checksum checks; if extra numerical/model/data changes or unknown provenance are found => `PROVENANCE_BLOCKED`, **do not launch** until GPT reviews. After the narrow fix, freeze new external script SHA and record in run manifest.
- Do not delete, rename, recycle or overwrite attempt01 or its logs, even if corrupted.

### Conditional GPU execution (only if NOT all hash-equal, and CPU workstream 2 PASS)

- This instruction expressly grants **one exception-controlled pair**: `reference_attempt_02` OFF/OFF then `optimized_attempt_02` ON/ON. Each mode at most one 8×H100 launch; sequential, not simultaneous, `torchrun --max-restarts=0`. **No auto retry** on failure, not even harness exceptions.
- Before launch: original Formal pair/Child/Gitlink lock, full config digest, C1 Shadow `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/`, Job `formal_verified_index_30k_shadow` with own latest→iter800, same-job `warm_start=False` all five components; no original Job writer; compare and store source/Shadow DCP metadata & latest hashes. Check *all* 8 H100 free≥25,000MiB, external robotwin_server stable, explicit user/owner GPU-sharing permission, enough CPU disk for **both** full-rank grads/candidate payloads and monitors. Do not terminate other workloads.
- Use exact frozen training parameters, environment flag pairs, seed/RNG, true FSDP2 and Local TTT pre-step only: `window.begin → run_member(GA0) → run_member(GA1) → capture → abort`, no finish/optimizer/scheduler/train/DCP save. Each mode **fresh 8-rank processes** loading the SAME iter800 and no reuse of candidate.
- Before accepting `LAUNCH_OK`, all 8 ranks must **re-read every expected tensor file** from their unique paths, check complete manifest 1:1, sha256 equals memory hash, FQN/rank/shard shape/dtype/numel valid, no overwrites or missing file, fast_state real values valid. One failure stops pair; if reference failed, optimized never starts. CPU NVML monitor concurrently; per-rank CUDA peak allocated/reserved, phase timings, foreign PID/mem recorded.
- After both passes, compare all required input identities, loss per member, all selected full tensors and all candidate local fast-state values using pre-frozen comparator/tolerances. `sha equal → BIT_EXACT`, hash different → all-element chunked comparison; any missing/inconsistent file `UNVERIFIED/BLOCKED`, no numeric gate pass.
- Do not run official Formal30k Resume. **Original Formal Job must remain STOPPED and checkpoint unchanged**. Only write new /tmp attempt02 Evidence; Shadow config.pkl/yaml may be rewritten by its Trainer constructors, Shadow DCP/Latest remain unchanged.

## One handoff; do not create new audit roundtrips

Submit `DS_PRO_V3_D1_PAIRED_GRAD_ARTIFACT_RECOVERY_2026-10-12.md` with both CPU workstream verdicts, original script provenance and all SHA, whether GPU was SKIPPED (all exact) or pair attempt02 performed, actual command/owner resource permission, per-rank completeness and SHA table, bit exact vs tolerant numeric outcomes, Local State, resource timings, checkpoint invariance and **first failure** if any.

**Stop immediately** for missing owner permission, unapproved numerical script drift, CPU synthetic collision test failure, source SHA mismatch, GPU OOM/NaN/NCCL, FQN identity mismatch, or artifact integrity failure. No additional pair retry without a separate explicit GPT review. C1/E/F and original Formal30k status unchanged.
