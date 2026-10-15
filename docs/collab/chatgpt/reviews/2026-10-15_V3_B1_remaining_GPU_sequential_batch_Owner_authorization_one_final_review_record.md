# V3 B1 — Owner 连续 GPU 验证授权记录（一次完整证据终审）

**Date:** 2026-10-15  
**Authority:** Owner 直接指示“给ds指令让其继续，不依赖的可以依次执行，一次审核。”  
**Nature:** 新的精确 SHA GPU execution authorization / workflow decision；**不是** GPU numerical parity verdict、CUDA benchmark，亦非新的 implementation Code Review。  
**Diagnostic formal pair unchanged:** Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` + Child/Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`.  
**Frozen original SOURCE/TARGET pairs unchanged:** SOURCE `b159f45906f7261d028aecc226ab7f2bb9807eb9` / `937066ffd90f2bf783ad4fbb4909e9c0b8922982`; TARGET `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`.  
**Owner r2 policy SHA:** `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`. **B0 iter1300 DCP FP:** `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`.

## 1. Two distinct authorizations, no scope blending

1. Previously issued P0 repeat0 receipt `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_a3239591_11GiB.json`, pinned commit `b340c5e3c942372f7928c6aa205dcd54433fb42d`, has already authorized SOURCE Index8 (completed) and GPT explicitly issued `ALLOW_PACKED128` for TARGET P0 repeat0. It is the exclusive authority for its **one still-pending TARGET**. Do not launch duplicate if TARGET happened to complete after last conversation report.
2. This Owner continuation separately authorizes **six additional** originally frozen B1 experiments, using a new non-mutating JSON receipt `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_remaining_six_GPU_jobs_Owner_authorization_a3239591_11GiB.json`, pinned commit `0ae4a1c87c9ff7850aaa9c0b45a1ac44c7392eae`. Only authorized pairs in order: index8/P0/r1 → packed128/P0/r1 → index8/P1/r0 → packed128/P1/r0 → index8/P1/r1 → packed128/P1/r1. Each is independent original iter1300 full same-job restore; these **six** are distinct from the prior two-job P0 repeat0 receipt.
3. Both receipts use the frozen original Owner r2 numerical limits unchanged and require original DCP/latest read-only, co-resident 8×H100 each >= **11264 MiB free** immediately before every independent job. They forbid other-user process interference, repeats of the same job, P0/P1 out-of-scope runs, Gate M, Formal30k and automatic retry. Current diagnostic `_owner_receipt` validates mandatory identity fields, but **not the full `approved_scope`**, so executor must also use a separate strict read-only scope/job-sequence validator. No code SHA change.

## 2. Why batch execution is legitimate

Pinned `tools/gates/v3_gateb1_compare.py` requires **P0_FIXED + P1_MATCHED_STOCHASTIC**, repeats `0,1`, SOURCE/TARGET, 8 ranks, iter1301/1302. Its complete comparison is read-only CPU and verifies exact per-consumer stochastic/text identities, full and terminal-partial windows, Owner r2 per-FQN gradient/optimizer/fast-state/loss metrics and cross-repeat identity/stability. The comparator internally returns `gpu_gate_approved=false` even for candidate metrics passing; **GPT** must issue the final scoped verdict separately.

These jobs may be run sequentially without intermediate GPT technical approvals because each loads the same immutable original DCP, has no trained state published and no dependency on changed model/checkpoints or Codex production optimizations. **Dependency respected:** do not start new six-job authority until existing TARGET P0 repeat0 has completed and DS verified it with SOURCE P0 repeat0. On runtime failure, rank/witness/immutability mismatch, or known frozen-r2 numeric failure, all remaining GPU work stops automatically. This is batching of **review**, not removal of **safety checks**.

## 3. Consolidated final evidence and scope

- After all 8 complete jobs (including previously finished SOURCE P0 repeat0), expected **128 JSON + 128 PT = 256 raw evidence files**; **64 SOURCE/TARGET rank-step numeric comparisons + 64 same-leg repeat audits**. Full/Terminal Partial must be present for P0 and P1; no missing FQN or unmatched stochastic.
- DS_PRO shall execute only the original frozen CPU comparator at end and submit machine-readable full result + clear rank/FQN worst metrics, complete per-job logs, DCP lightweight immutability, same input/repeat witnesses. One **independent GPT full B1 evidence review** when complete; not a repeated code review.
- Exact detailed execution request: `docs/collab/chatgpt/requests/2026-10-15_DS_PRO_V3_B1_finish_seven_GPU_jobs_one_final_review_a3239591.md`.
- At any failed safety gate, report partial evidence and stop without retry. Status remains `B1_GPU_PARITY_UNVERIFIED` until formal closeout. Gate M and Formal30k remain **HOLD** and need separate Owner decisions.
- B0/451GB/149 CPU tests, B1 CFG local RNG CPU Gate, frozen source/target, and eventual full V3 audit are **not** reopened. No Codex E1/E2/T1/P1 production code changes are involved.

**Formal execution authority disposition:** New Owner authorization **GRANTED** for exactly six listed B1 follow-on jobs, operationally conditional on completing existing P0 repeat0 TARGET, strict admission checks and fail-fast. There is **NO B1 GPU PASS** yet and no Gate M/Formal30k launch approval.
