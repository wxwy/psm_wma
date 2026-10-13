# PSM-WMA V3 — Packed128 Native Gate A CPU Evidence Closure

Date: 2026-10-13
Exact formal implementation Root: c4731bca1a590663db88bd6cd74dbcf9fd513a85
Exact formal Child/Gitlink: c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686
Docs-only HEAD advancement is not a new implementation SHA.
Previous same-pair incremental review: docs/collab/chatgpt/reviews/2026-10-13_V3_packed128_native_implementation_incremental_review_c4731bca_c8dabbb3.md
New Owner-relayed DS_PRO execution evidence: docs/collab/chatgpt/evidence/2026-10-13_V3_packed128_native/DS_PRO_2026-10-13_Packed128_GateA_CPU_acceptance_owner_relay.md

## Formal verdict and scope

**APPROVE / GATE_A_CPU_ACCEPTANCE_CLOSED** for V3 Packed128 Native CPU-only Gate A. This closes only the previous Evidence-only Finding C on the unchanged implementation pair: test runtime was missing. **The whole Packed128 implementation Gate remains REQUEST_CHANGES** because real MoT loss/gradient parity, FSDP8 GPU runtime, memory/performance and resume/migration evidence remain unverified. No authority to run Gate B, GPU profiling, full formal training or alter existing Job. No existing code tests repeated merely because docs advanced.

## Independent verification and evidence basis

- Fresh remote GitHub fetch confirms Root V3 HEAD at evidence `16492ca31546d5312eaecc52841a988d302029d6`, Child branch and Root gitlink both `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`. Root implementation is `c4731bca1a590663db88bd6cd74dbcf9fd513a85`.
- GitHub compare baseline Index8 Child `5ac9a904c46da658e1b3e0816d3a7d95ce99c945` to current exactly9 changed paths with 346 additions, 125 deletions; no new code SHA.
- DS_PRO executed five isolated test modules, 151 passed / 2 skipped / 0 failed, each exit0; 9/9 py_compile and Ruff0.12.7 clean exit0. DS actual venv and import path aligned to isolated Child, HF_HUB_OFFLINE=1.
- The two skips concern external fixtures; no optional real GPU MoT gradient-equivalence evidence is implied. GPT independently cross-checked relevant source implementation + telemetry labels (not original remote stdout). This is sufficient for the frozen **CPU** Gate; the original stdout/ filesystem remain DS/Owner-supplied evidence.
- Gate A1 full/partial consumer/S0 packing, A2 precise GA-loss weights/synthetic gradient oracle, A3 create_graph and Local Slow gradient reachability, A4 optimized member calls/optimizer/abort and same-version resume CPU tests, A5 audit SHA/observer/digest checks all PASS per DS report.

## Outstanding risk/decision register

**Finding C (previous MEDIUM / CPU execution evidence): CLOSED.** 151 tests and compile/lint have run on exact pair. Do not request them again unless code SHA changes.

**Finding A (previous HIGH / real native numerical parity): OPEN.** Synthetic FP32 relative-error tests cover loss algebra/Slow graph, not actual production MoT Batch8-index vs Batch128 packing. Need identical real consumer/source/weights; frozen per-consumer sigma, epsilon, dropout; vision/action/aux/outer loss; per-FQN generation/action/local slow grads and candidate fast states; FSDP8 and one optimizer update with norm/cos/relative-L2 thresholds declared *before* examination. The old V2 5% threshold is not inherited automatically.

**Finding B (previous HIGH / GPU runtime + performance): OPEN.** Batched128 native collate/MoT/FSDP may change kernel packing, activation memory and collective behavior. Need separately authorized isolated H100 GPU smoke with full256/rank and2 native F/B, strict DCP and throughput comparison; Owner accepts direct128 but no silent batch reduction or consumer skipping.

**Non-blocking Observation O1 / inconsistent labels:** `NATIVE_BATCH_LAYOUT` in config digest is `v2_a2_member_packed_slot_major_v1`; telemetry field string is `v2_a2_slot_major_packed_member`. Values mean the same execution layout but do **not** match byte-for-byte. No current code requirement for equality was identified; changing this now would create a **new formal implementation pair and invalidate exact SHA Gate A**. Keep unchanged for Gate B with an explicit mapping in evaluator; unify on the *next authorized implementation pair* if downstream log joins need it, then revalidate corresponding scope. Do not mark as code blocker without a proven equality-dependent contract.

**Operational Observation O2 / iter1400 vs iter1300 pointer:** DS observed `iter_000001400` directory but `latest_checkpoint.txt=iter_000001300`, while no active Formal30k training process detected after 1400 progress. This is not Gate A failure, but a separate HIGH **checkpoint-selection safety gate**: no claims that iter1400 DCP is complete/valid or that it can be resumed. Request DS read-only checking all DCP .metadata / rank_0..rank_7.pkl, checkpoint writer finalization/timestamps, latest pointer semantics and run provenance. If incomplete, use only last independently validated pointer, never alter latest or overwrite DCP without Owner decision.

**Operational Observation O3 / cross-layout continuation:** Packed128 changed `config_digest`, so existing old Index8 checkpoint (iter1300 or iter1400) is **not** currently compatible with native `same-job --phase resume`. Preserve model, optimizer, scheduler, RNG, all eight rank Local sidecars only through an independently designed migration gate after GPU mathematical compatibility proof. Do not silently rewrite provenance or bypass strict checks. Owner can decide which original complete iteration to use after pointer audit.

## Next gate

Only if Owner explicitly authorizes: separate 8×H100 Gate B on isolated Root/Child worktree and distinct namespace; full real MoT matched-index/packed gradient parity, Memory/collective evidence, strict DCP and wall-clock comparison. DS does not change production and must stop on first failure. No live Formal Job source mutation.

Final scope: Gate A CPU closed, **Packed128 overall HOLD** pending the above GPU & checkpoint/migration checks. `APPROVE` never means formal runtime deployment.