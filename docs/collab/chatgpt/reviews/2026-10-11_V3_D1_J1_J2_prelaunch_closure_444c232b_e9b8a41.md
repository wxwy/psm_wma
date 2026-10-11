# PSM-WMA V3 — D1 J1/J2 最终 CPU Prelaunch 定点验收及 GPU Scope 裁决

**Date:** 2026-10-11
**Fixed Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`; **Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Formal Verdict:** `J1_PASS / J2_PASS / D1_CPU_PRELAUNCH_CLOSED / D1_PAIRED_GPU_PRESTEP_AUTHORIZED_WITH_GUARDS`
**Current state:** `C1_CLOSED / D1_NUMERIC_GPU_PENDING / E_F_HOLD / FORMAL30K_STOPPED`

## Sources and evidence boundary

- Frozen preceding finding: `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_prelaunch_H1_H2_H3_review_444c232b_e9b8a41.md`.
- Exact authorized CPU repairs: `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_prelaunch_final_two_CPU_corrections_authorization_444c232b_e9b8a41.md`.
- DS owner-relayed report in `docs/collab/chatgpt/evidence/2026-10-11_V3_D1_prelaunch/DS_PRO_2026-10-11_J1_J2_final_CPU_remediation_owner_relay.md` (the original external `/tmp` .py and JSON **not directly read/hashed by GPT**).
- Fixed Child previously inspected for `GroupedLocalMemoryWindow.begin/run_member/abort` and Checkpointer Same-job precedence. No implementation diff; no repeat full code/Checkpoint/Index audit.

## J1 closure

DS supplied corrected `torchrun` CLI with the actual `no_step_harness.py` as positional training script, not the venv Python executable; disabled elastic restart using `--max-restarts=0`; 21/21 CPU command/guard mock tests reported PASS. No actual GPU run happened. Resource Guard now fails closed when ANY card has free<25,000MiB. Owner GPU-sharing approval and stable robotwin_server remain mandatory at actual launch, **not presumed granted by this document**.

H3 Launcher itself is an **external /tmp diagnostic tool**, not a production launcher. Require SHA256 identity `9b615b01e9025f6925da50d5f70bd4448dbb7020f364e3212e876ff8990e49cd`, frozen working directory/Python environment, resolved torchrun venv, no accidental env change and unique per-mode/per-attempt logs before GPU run. A tool or launcher mismatch => BLOCKED before consuming GPU, **not** permission to patch/retry mid-run. Both modes are sequential and separate process groups, each loading the SAME frozen Shadow iter800 source.

**Verdict J1_PASS** for CPU readiness, not proof of actual job success.

## J2 closure

Original Comparator sampled only 256 values when full SHA differed, which could let changes outside sample escape. DS reports v2:
- For entire captured tensor, sha equal => BIT_EXACT.
- If hashes differ, require full independently stored CPU tensor payload and SHA-verified identity, compare **every** rank-local FSDP2 shard element in chunks of (1<<20); if values unavailable => UNVERIFIED, inconsistent evidence => BLOCKED; any violation => FAIL.
- CPU test including only index300 changed outside first256, plus missing full tensor and incorrect gradient-vs-weight witness gives 17/17 PASS.
- Four `w0_fast_*` use actual `.grad` source; Local candidate stores complete slot identities/provenance/four fast tensor identities+bytes.
- Frozen FP32/BF16 loss/gradient numeric tolerances unchanged. Near-zero and missing/NaN/Inf structural conditions are failure modes. `WITHIN_TOLERANCE` is not `BIT_EXACT`. Keep all data sorted/aligned rank→parameter FQN→actual local shard dtype/shape.
- Selected grads can be large: estimate /tmp disk space before run, store complete tensor files outside repo and ensure ownership/trust (CPU `torch.load(weights_only=True)` on known saved tensors); do not inline huge data in JSON. An unavailable all-value comparator makes overall numerical gate `UNVERIFIED/BLOCKED` instead of PASS.

**Verdict J2_PASS** for CPU comparator readiness; real numerical parity untested until GPU.

## GPU authority bounded to one paired Pre-step experiment

Explicit **conditional execution authorization** in `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_paired_8H100_shadow_prestep_numeric_execution_authorization_444c232b_e9b8a41.md`: one 8×H100 reference OFF/OFF **then** one 8×H100 optimized ON/ON, at most one launch per mode, one mode at a time, from same C1 isolated Shadow `iter_000000800`. Each mode restores 5 components/RNG/Local Fast/Frontier and computes one grouped GA window using production `window.begin() → run_member(GA0) → run_member(GA1) → capture → abort()`, **no `finish` and no optimizer/scheduler step/DCP save**. GPU resource monitor concurrent, comparator only after both succeed. Any first error, owner approval missing, GPU condition failure, content mismatch, OOM/NaN/NCCL => fail-stop; no retry, no second mode after first fails. No silent CUDA allocator changes.

Original Formal30k STOPPED, source original DCP and isolated Shadow checkpoint/Latest remain unchanged. Only Shadow config.pkl/yaml may be overwritten by Trainer constructors, and evidence in external /tmp new namespace. No D1 PASS implied by this authorization; no E/F, Fresh/Formal30k Resume or altered implementation.

## Only future handoff

DS returns a **single** paired-run report with 8 rank results per mode, per-FQN full-grad compare status, Local/outer loss parity, actual GPU peak allocated/reserved vs nvidia-smi device total, stage timing scope, exact env and resource guard/permission, first exception and per-attempt logs, original/shadow checkpoint immutability. GPT then adjudicates D1 and whether Original Formal30k iter800 Resume can be separately authorized. No more CPU re-review of J1/J2 absent actual new evidence.
