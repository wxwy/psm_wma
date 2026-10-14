# Independent evidence review — V3 Packed128 Gate B1 numerical-criteria DS_PRO read-only facts

**Date:** 2026-10-14
**Role:** GPT, independent design/evidence reviewer (DS_PRO is read-only executor)
**Verdict:** **REQUEST_CHANGES — B1_NUMERIC_CONFIG_EVIDENCE_NOT_FROZEN** (does **not** rescind B0 CPU PASS and is **not** a review of GPU implementation, which does not exist)
**Frozen B1 production SOURCE:** Index8 Root \`b159f45906f7261d028aecc226ab7f2bb9807eb9\` / Child/Gitlink \`937066ffd90f2bf783ad4fbb4909e9c0b8922982\`
**Frozen B1 production TARGET:** Packed128 Root \`c4731bca1a590663db88bd6cd74dbcf9fd513a85\` / Child/Gitlink \`c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686\`
**Out-of-scope current V3 child:** \`8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1\` Full Segment Prefetch; no formal pair changed.
**Evidence under review:** Owner-pasted DS_PRO \`2026-10-14 V3 Packed128 Gate B1 数值判据冻结·只读证据准备\` (source citations independently checked through GitHub).
**Applicable design:** \`docs/collab/chatgpt/designs/2026-10-14_GPT_V3_Packed128_GateB1_real_FSDP8_transient_comparator_design_r1.md\` and 2026-10-13 Round2 §6. Owner D1–D4 still frozen; B1 thresholds remain candidate; GPU HOLD.

## Correct provenance & findings

### B1-EVID-01 — HIGH: wrong digest/recipe authority for actual frozen comparison

- **DS claim:** Section 8 attributes B1 configuration authority to \`examples/psm_wma_robocasa_h100.py:213–224\` and H3F geometry/checkpoint values while citing Index8 \`70e9867f…\` and Packed128 \`1ab2bbe4…\`.
- **Verified source:** both pinned child trees contain *unchanged* \`examples/psm_wma_robocasa_h100.py\` and \`examples/psm_wma_robocasa_h3f.py\`. \`h100.py:213–224\` hashes Stage-A/H3E config+model metadata and \`geometry\` but **does not include a native layout identity**; it cannot be the independent source of the layout-dependent old/new digest mapping. \`h3f.py:146–162\` wraps this H3E digest in different authority. Actual B0 DCP writer and frozen Comparator pair are **\`examples/psm_wma_robocasa_corrected_phase5.py\`**; its \`config_digest:186–235\` hashes cache/manifest/source, \`native_batch_layout\`, model, optimizer incl \`weight_decay\`, mesh and 30k schedule. \`preflight:408–507\` builds that resolved Config and native exact-window cache authority.
- **Violation:** 2026-10-13 B1 Round2 §1 precise SOURCE/TARGET implementation lineage; numerical-criteria freeze cannot mix H3-F/FSE recipes and the exact-window Phase5 DCP and assert their config values are interchangeable.
- **Acceptance:** both legs individually derive exactly one \`corrected_phase5.preflight\` fully resolved config, prove old/new digests \`70e9867f…\` / \`1ab2bbe4…\` from actual CPU authority with independent frozen Root/Child/module paths, and distinguish H100/H3F as **historical background only**.

### B1-EVID-02 — HIGH: wrong optimizer decay and loss scale assumptions

- **DS claim:** Section 5 \`weight_decay=0.0\` by generic \`sft_config.py:438–439\`; Section 10 \`loss_scale=1.0\` by generic default.
- **Verified source:** \`cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_robocasa_nano.py:84–96\` sets optimizer **\`weight_decay=0.05\`** and \`lr=5e-5\`, betas \`[0.9,0.99]\`, eps \`1e-8\`. Actual \`action_policy_robocasa_edge.py:34–50\` inherits this optimizer and adds \`weight_decay_skip_patterns\` for action-head projections. \`cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py:101–110\` sets **\`loss_scale=10.0\`**, \`action_loss_weight=10.0\`, \`independent_action_schedule=False\`, \`train_time_video_distribution="waver"\` (image/action distribution \`logitnormal\`). \`examples/toml/sft_config/psm_wma_robocasa_native_smoke.toml:5–15\` resolves \`experiment="action_policy_robocasa_edge"\`. \`corrected_phase5.py:239–281\` overlays Local, optimizer selected keys and schedule **without setting \`weight_decay=0\` or \`loss_scale=1\`**.
- **Impact:** wrong decoupled weight decay materially changes \`ΔParameter\`, and wrong 10× vision scaling alters loss/gradient numerical comparisons; cannot pre-register reliable optimizer/Loss tolerances using those DS values.
- **Acceptance:** report actual *resolved* per leg optimizer \`weight_decay\` and \`weight_decay_skip_patterns\`, per-param-group effective decay/LR multipliers, \`rectified_flow_training_config\` loss scales and precision and \`lbl\` config; record actual param-group states from later B1 8-rank real load before computing numerical metrics. Do not infer from generic default or Nano doc alone.

### B1-EVID-03 — MEDIUM: unconditional loss mathematical equivalence is unproven

- **DS claim:** Section 3 treats weighted \`Σ n_i/N * loss_i\` as complete native objective mathematical equivalence on its own.
- **Verified source:** \`cosmos_framework/model/generator/algorithm/loss/flow_matching.py:95–166\` defaults to per-instance mean but if \`exclude_fully_conditioned_items\` it normalizes by *batch active-item count* instead; \`omni_mot_model.py:2010–2040\` optionally applies cross-rank \`sample_level_loss_averaging\` before MoE load-balancing \`aux_loss_und/gen\`. Condition-mask and action-slot weights can vary. The rank-local \`count/plan.n_window\` formula alone does not eliminate these cases.
- **Acceptance:** resolve \`normalize_loss_by_active\`, \`exclude_fully_conditioned_items\`, \`sample_level_loss_averaging\`, LBL coefficients and actual active auxiliaries; B1 native run must prove every loss component and true consumer/sample mean reduction. Make all non-additive cases BLOCKED until a matching proof, never silently call full outer objective algebraically equal.

### B1-EVID-04 — MEDIUM: dtype statements overclaim runtime tensor storage

- **DS claim:** Section 4 says every optimizer gradient is BF16, every scalar loss FP32, and every moment FP32, based on FSDP reduce dtype and \`tensor_kwargs_fp32\`.
- **Verified source:** \`h100.py:257–263\` checks base BF16 precision/FP32 master/BF16 reduction in *H3-E* and \`edge_model_config.py:76–92\` provides baseline \`precision=bfloat16\`, \`fsdp_master_dtype=float32\`. BF16 reduce does **not** by itself prove final \`parameter.grad\` storage dtype. A FP32 noise/target helper does not prove every native Loss scalar dtype. Optimizer moments default to FP32 in FusedAdam \`utils/fused_adam.py\`, but actual optimizer container state, master-weight flag, sharding and tensor groups must be inspected after real restore.
- **Acceptance:** CPU preflight dumps fully resolved config; B1 GPU diagnostic separately outputs each optimizer-selected FQN \`param.dtype\`, \`grad.dtype\` after full GA2/unscale/clipping, any FP32-master dtype/shape, Loss component tensor dtype and moment \`exp_avg/exp_avg_sq\` dtype. Choose numeric policy per **observed tensor's actual dtype and role**, never blanket BF16.

### B1-EVID-05 — MEDIUM: diff scope includes changed examples, not only five framework modules

- DS correctly named the **five** changed \`cosmos_framework/**/*.py\` paths. However GitHub exact compare \`937066ff..c8dabbb3\` includes **11 total changed files:** those five plus \`examples/psm_wma_robocasa_corrected_phase5.py\`, its tests, \`corrected_telemetry.py\`, telemetry tests, formal monitor and monitor tests (six example files). Thus \`only five .py\` is only true if explicitly restricted to \`cosmos_framework/\`.
- **Acceptance:** B1 Source→Target diff manifest accounts for all 11 files, clearly labels training semantics vs telemetry-only code and identifies actual \`NATIVE_BATCH_LAYOUT\` authority change. May not silently infer telemetry changes are harmless without reviewing their runtime effect.

### B1-EVID-06 — MEDIUM: CFG dropout ≠ clean/noise condition mask

- \`cosmos_framework/data/generator/augmentors/text_tokenizer.py:52–54,101–106\` explicitly does **caption CFG dropout** with \`random.random() < cfg_dropout_rate\`; recipe \`action_policy_robocasa_nano.py:180\` sets \`cfg_dropout_rate=0.1\`. This is a **text conditioning dropout** producing blank-caption/tokens. \`condition_mask\` in \`algorithm/loss/flow_matching.py:90–129\` marks **clean/conditioning vs noised generation** vision/action tokens and normalizes loss. These are different stochastic/deterministic sites.
- **Acceptance:** B1 separate per-consumer CFG random/caption/token hash witness from sigma/epsilon RNG and from vision/action condition-mask/valid-count equality. No assertion that CFG training = CFG inference guidance-scale operation.

## Verified facts retained

- Exact source/target \`GroupedLocalMemoryWindow\`: Index8 16 native index calls/member vs Packed128 one slot-major native call/member; same real \`n_member/n_window\` weight with Terminal Partial. But numerical equality and FSDP collectives are B1 GPU questions.
- Trainer GA2 order from \`cosmos_framework/trainer/local_memory_grouped.py:203–348\`: begin; member0 native F/B; member1 native F/B; gradient finite and callbacks; optimizer/scheduler once; Local candidate commit; zero grad. No surrogate loss.
- Configured bf16 Edge model, FSDP master FP32 baseline, 8-way shard, Local T=16, B=8, GA=2, K=4 and data raw15; actual runtime tensors must still be witnessed.
- B0 remains **APPROVE / CLOSED**, diagnostic \`ec9d162b926c4f197f5cfb692499b4dbda888686\`; no CPU B0 rerun.

## Gate disposition

**REQUEST_CHANGES pertains only to DS B1 numeric *evidence authority***, not rejected production code and not a reversal of B0. **B1 thresholds NOT frozen** and \`B1_GPU_NOT_AUTHORIZED\`. Minimum evidence to close these corrections: **one CPU-only DS readout** of both pinned \`corrected_phase5\` resolved configs, SHA/config digest and source-of-truth fields (see linked request). GPT then proposes/finalizes numeric threshold freeze for Owner signoff, with all optimizer delta/moment policy specified *before* any GPU run. No B1 implementation/runtime GPU assertions are authorized by this document.
