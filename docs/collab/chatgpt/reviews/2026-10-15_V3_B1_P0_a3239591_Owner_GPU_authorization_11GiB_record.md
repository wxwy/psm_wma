# V3 B1 P0_GPU — Owner 新授权记录：a3239591 / 11GiB 共驻显存门槛

**Date:** 2026-10-15  
**Nature:** Owner execution authorization record; **not** fresh implementation Code Gate, numerical GPU PASS, or authority to modify production checkpoints.  
**User's explicit instruction:** “我授权，按照之前的经验，单卡11G就可以了”。  
**New authoritative receipt:** `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_a3239591_11GiB.json`; first recorded on V3 as commit `b340c5e3c942372f7928c6aa205dcd54433fb42d`.

## 1. Exact frozen authority

- Diagnostic B1 runner implementation Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Gitlink Child `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`. This diagnostic branch remains separate from production V3/its Codex optimization work.
- SOURCE Index8: Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`.
- TARGET Packed128: Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.
- Numeric freeze r2 SHA256 `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`.
- Authoritative iter1300 B0 DCP FP `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`.
- Previous Owner GPU receipt bound **only** old `46e9cc0e...`. It stays untouched in GitHub; cannot be copy-edited/reused as new approval. The new receipt is an independent, explicitly Owner-approved JSON for current exact code SHA.
- B1 CFG threaded Local-RNG CPU Gate has prior exact-pair `APPROVE_TO_CLOSE`; no reason to rerun unchanged 149 tests, B0 or full dataset.

## 2. Owner GPU scope newly ratified

**OWNER_GPU_AUTHORIZED_FOR_P0_REPEAT0_ONLY**, bounded to **two** independent, sequential 8×H100 `torchrun` jobs, **P0_FIXED** `repeat=0`, exact iter1301 and iter1302, no retries.

**Owner overrides one previous operational condition:** The old `min_free_gpu_memory_mib_at_launch=16384` is replaced by **`11264` MiB (11 GiB of free NVIDIA-reported memory on each of eight devices)** for this new receipt only. Clarification: 11 GiB is interpreted as **available/free VRAM**, not model `allocated` bytes; it is a launch gate, not a promise of sufficient future peak reserve as other co-resident processes fluctuate. The DS report's old min=13466/13588 MiB in two historical snapshots both exceed 11264, but they are not a valid **live** launch measurement.

All other safety conditions remain hard:
- Every separate job requires immediate **new** eight-card live free-VRAM check (each >=11264 MiB), exact frozen identity, new Owner receipt, validated non-ambiguous ASCII runbook, CPU-only prepare success, and isolated /tmp output. If any check fails, STOP without any torchrun.
- Source Index8 **first**; its eight ranks × two completed iterations' evidence/logs and DCP/latest immutability must be evaluated by a real human/GPT reviewer before an explicit `ALLOW_PACKED128` release. A typed shell confirmation without evidence review is not sufficient. Recheck all pre-launch gates for TARGET.
- Maintain original DCP/latest strictly read-only; don't invoke Checkpointer.save, fresh/resume Formal30k, Gate M, P1/repeat1, full B1, automatic retries, or another GPU job. Only stop user's own P0 process on OOM/nonfinite/CUDA/NCCL/DCP mutation or disruption; do not kill, pause, renice or modify other users' GPU processes. Shared-load throughput is not an isolation performance benchmark.
- New receipt's `approved_scope` extras are **not all enforced** by `v3_gateb1_run._owner_receipt`; DS executor must separately validate exact full approved_scope and manual human release.

## 3. Readiness versus authorization

The Owner has **granted permission**, not asserted actual runnable readiness or kicked off jobs. Prior independent launch-readiness review `docs/collab/chatgpt/reviews/2026-10-15_V3_B1_P0_a3239591_GPU_launch_preparation_DS_report_review.md` flagged missing authoritative new auth, an earlier 16GiB floor, runnable command NBSP bytes and missing fresh `--mode prepare` records. This approval resolves the **auth absence** and lowers the **VRAM threshold** but does not automatically certify corrected ASCII launcher, both prepare runs, comprehensive scope validation or the live eight-GPU condition. Those remain operational preconditions to be checked by DS_PRO, not changes requiring a new B1 production SHA.

**Permission when those checks succeed:** DS_PRO may execute **SOURCE Index8 P0_FIXED repeat0 iter1301/1302**, retain evidence in a unique /tmp namespace and **STOP**, hand off evidence for explicit SOURCE→TARGET human release. No independent Target launch before that review. No further Owner reauthorization for TARGET inside this same two-job receipt, assuming explicit human SOURCE review/release and all conditions still hold.

## 4. Gate states after Owner decision

- `B1_P0_THREADED_CFG_LOCAL_RNG_CPU_GATE`: CLOSED for `a3239591/8f3672d1`.
- `B1_P0_GPU_OWNER_EXECUTION_AUTHORIZATION`: **GRANTED**, conditional operational admission >=11264 MiB/free GPU ×8, exact bound scope.
- `B1_P0_SOURCE_EXECUTION`: NOT STARTED / DS readiness checks pending.
- `B1_GPU_NUMERIC_PARITY`: UNVERIFIED.
- `B1_FULL_P0/P1/REPEATS`, `Gate M`, `Formal30k`: HOLD.
- No production V3 Codex E1/E2/T1/P1 code affected; no full V3 repo re-review, no B0 or corpus repeated.

Detailed DS executor instructions are in `docs/collab/chatgpt/requests/2026-10-15_DS_PRO_V3_B1_P0_GPU_source_execute_owner_a3239591_11GiB.md`.
