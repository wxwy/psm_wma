# PSM-WMA V3 — D1 paired GPU Pre-step Evidence-only incremental review: rank collision

**Date:** 2026-10-12
**Formal implementation pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`. **Formal pair UNCHANGED**; do not repeat implementation/design technical review, C1, Dataset Index or VAE.
**Formal numeric-gate verdict:** `REQUEST_CHANGES` (**Evidence-only**) / `D1_PRESTEP_UNVERIFIED`.
**Prior frozen execution contract:** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_paired_8H100_shadow_prestep_numeric_execution_authorization_444c232b_e9b8a41.md`.
**Owner-relayed incident evidence:** `docs/collab/chatgpt/evidence/2026-10-12_V3_D1_gpu/DS_PRO_2026-10-12_paired_prestep_rank_collision_owner_relay.md` (raw server Python/JSON/tensors not accessed by GPT).
**Next action authority:** `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_artifact_collision_conditional_clean_pair_rerun_authorization_444c232b_e9b8a41.md`.

## 1. What DID and DID NOT pass

DS reports both 8-rank, one-GA-window no-step **runtime** invocations succeeded, no optimizer/scheduler step and no Error, and bit-identical `member_losses` for Reference/Optimized. Reported original formal Job manifest unchanged and Local candidate fast-state file SHA consistent. **These observations remain valid within DS reported evidence scope**; no reason to mark production loss calculation or model as broken.

Full-gradient parity is **NOT established**. All computed values that depend on overwritten `grad_tensors/*.pt` are **invalid for gate closure**. Prior apparent `layer13 v_proj` numeric FAIL and `net.action2llm.bias.weight` BLOCKED produced from contaminated files **must not be reported as true model gradient failure**. `H3_GPU_RUN_PASS` is only a run-completed assertion, not `D1_PRESTEP_PASS`.

## 2. Finding D1-E1 — Cross-rank output filename collision

- **Severity HIGH / Evidence defect.**
- **File:line:** **external /tmp-only** `/tmp/ds_pro_v3_d1_r1/h1/no_step_harness.py:231`, reported `rel = f"grad_tensors/{_sanitize(fqn)}.pt"`.
- **Root cause:** No rank namespace in output, so multiple FSDP2 rank-local tensor shards of same FQN write the identical path, corrupting saved full-tensor evidence. The DS claim that each mismatching SHA matches another rank provides supporting source attribution; GPT cannot independently verify their /tmp data bytes.
- **Frozen contract violated:** D1 requires each rank/FQN real `.grad` complete payload and digest+dtype+shape/identity preserved for all-element `BIT_EXACT/WITHIN_TOLERANCE`; mode evidence must be immutable with no overwrites.
- **Acceptance:** Rank- and FQN-collision-free filenames, exclusive no-overwrite writes, per-rank manifests and CPU readback SHA verification, negative collision tests; existing attempt01 evidence remains untouched. With unequal in-memory gradients and missing full payload, both modes need one fully clean matched rerun from same iter800 source to test tolerance; only one mode rerun cannot repair counterpart.

## 3. Finding D1-E2 — Frozen external diagnostic-tool hash drift

- **Severity MEDIUM / Execution provenance and authorization.**
- **Evidence:** Reported current H1 `ae428da4…` and H3 `8d633889…` do not match frozen authority `e854f7a4…` H1 and `9b615b01…` H3; full hashes are not supplied. Production Formal Pair remains intact, but external scripts are an independent experimental artifact identity.
- **Frozen contract:** Pre-GPU script SHA identity check must fail closed on unexpected bytes; no undocumented code patch/self-retry after launch.
- **Acceptance:** Supply exact actual executed SHA256, diff of current against frozen or last independently logged scripts and run timeline; prove changes do not alter input data/model/optimizer/RNG or loss/gradient semantics. If a material unaccounted change occurred, `BLOCKED` and return to GPT with existing logs before any new GPU. Narrow allowed patch concerns only evidence-writing collision + related isolated tests, preserving numerical paths.

## 4. Decision: Choose A, with a cheap pre-retry SHA exactness screen

- **B rejected** as routine waiver: sampled values + matching member loss do not prove all local FSDP2 gradients.
- **C rejected**: Reference also has overwritten output files (85/296), so optimized-only retry leaves an asymmetric, unverifiable comparator.
- **A selected** if necessary: one clean **pair** on separate new immutable attempt02 directories, after CPU collision-proof/manifest integrity tests, no production code changes, same C1 Shadow checkpoint.
- **Optimization before GPU:** In parallel with fixing the /tmp writer, use the existing per-rank JSON in-memory hashes to compare **all** required (rank,FQN,grad_present,shape,dtype,sha256) pairs, input RNG/GA/segment IDs, and candidate hashes against the two modes' records. The printed `296` denominator must be reconciled against the frozen selected-parameter inventory, not silently taken as full coverage. Every required gradient SHA equal with valid provenance means full **captured in-memory bytes** are bit-exact; this is a stronger comparison than sampling. Because full persisted payloads were lost, record the Evidence-retention protocol deviation explicitly. If all required bytes+input/fast state match exactly, stop and return a **`NO_RERUN_BIT_EXACT_CANDIDATE`** report for GPT final review; do not silently label Gate PASS.
- **If ANY required gradient SHA differs, a gradient is absent, coverage is incomplete, source/hashes are questionable, or full evidence needed for frozen tolerance comparison is missing**, repair and rerun **both** modes under the conditional GPU authorization. Do not rerun optimized only. If actual executed script provenance cannot be resolved, no GPU.
- This is a **new explicit, narrow exception** to the prior one-launch-per-mode authority for postmortem correction of a documented diagnostic artifact defect. It does NOT permit an automatic retry on model failure, parameter mismatch or new OOM. No second retry beyond attempt02.

## 5. Rerun invariants

- Copy / preserve `reference_attempt_01` / `optimized_attempt_01` and associated H3 logs without deletion/overwrite, retain old corrupted files as forensic evidence.
- Same Formal Root/Child; same physical C1 Shadow Root and Job `formal_verified_index_30k_shadow`, latest→`iter_000000800`; strict `warm_start=False` five-component state and exact digest. Each mode fresh process from identical state with frozen flags Reference OFF/OFF then Optimized ON/ON.
- Single 8×H100 distributed job at a time, never both concurrent; each mode attempt02 only once; `--max-restarts=0` and fail immediately on first error. Require owner GPU-sharing permission, stable robotwin_server and each GPU free≥25,000MiB at launch, no external process termination.
- No production code, dataset, index, VAE or source DCP mutation. No `trainer.train`, final `trainer.training_step`, `window.finish`, optimizer/scheduler step, or DCP save. Original Formal30k must stay STOPPED and files unchanged.
- Each rank must save immutable complete gradient tensors to unique locations; comparator must read back every expected tensor with matching SHA, dtype, local shard shape and FQN/slot identity. Local Candidate actual tensors and loss/grad comparison follow frozen H2 tolerances, no post-hoc relaxation; comparator may only report `BIT_EXACT / WITHIN_TOLERANCE / FAIL / BLOCKED / UNVERIFIED` with truthful scope.
- Record real per-rank allocated/reserved and NVML global memory; `H3_GPU_RUN_PASS` means the process ran, **not numeric parity**.

## 6. Gate status

`D1_PRESTEP_UNVERIFIED / D1_CLEAN_EVIDENCE_RECOVERY_AUTHORIZED_CONDITIONALLY / C1_CLOSED / E_F_HOLD / FORMAL30K_STOPPED`.
No original Formal30k iter800 Resume authority. One owner-relayed DS consolidated report after the CPU screen and, if required, one clean paired retry. No multiple GPT intermediate round-trips.
