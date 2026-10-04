# V3 Phase 2 raw15/state15 + H_pred16 — GPT fresh source review

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE2-IMPLEMENTATION
- formal root：8b21e7b1eb01e229ab6152371ac4039d4e4905da
- formal child/Gitlink：826c7ca0fd5b6967d7199c0fefd144fe1fdd57e2
- design authority：docs/build/PSM-WMA_V3_phase2_raw15_state15_hpred16_design_v1.1_2026-10-05.md
- parent Phase1B child：21e60d6eb3a04846ffa7280aca18f6005399363e

## Verdict

REQUEST_CHANGES

当前 pair 不授权 ds。Phase2 的 action/state/sequence 核心语义未发现 blocker；唯一剩余 blocker 是 tokenizer contract resolver 会重建整份 base tokenizer config，从而可能覆盖 Corrected runtime 的非合同字段。

## PASS findings

1. formal child relative Phase1B parent only adds:
   - robocasa_exact_window_policy.py
   - robocasa_exact_window_policy_test.py
2. raw12 source layout正确按 base_motion4/control_mode/eef_pos/axisangle/gripper 处理。
3. adapter 不实例化 multi-shard RoboCasa loader，不复制 convert_rotation；直接调用 official private:
   - RoboCasaLeRobotDataset._build_frame_wise_action
   - RoboCasaLeRobotDataset._build_initial_state
4. raw15 = source base5 exact + official arm10；state15 = zeros5 + official state10。
5. synthetic tests使用非零 axis-angle / quaternion 并以 matrix semantic parity验证 rotation。
6. state token只消费 current/pre-action row；后续16帧变化不影响 state15。
7. [state15; 16x raw15] = [17,15]；official WAM SequencePlan得到 action condition=[0]。
8. official packer测试 row0 condition=1、noisy/mse indexes exclude row0；official flow-matching loss测试 row0-only error contribution=0，predicted rows error>0。
9. ActionProcessor测试 raw_action_dim=15、[17,64] first15 exact、tail zero、normalizer=None。
10. Corrected contract冻结 fps20/H_pred16/chunk16/obs17/raw15/state15/max64/left_wrist/raw/use_state，R范围1..16。
11. manifest VAE contract保留完整 exact-duration list，要求含17、bfloat16、chunk-frame capability与 fixed Edge兼容。
12. legacy Nano/Edge chunk32/[33] 和 runtime32被 corrected validator拒绝。
13. cx final-tree self-test: Phase1A+1B+2 targeted pytest 135 passed；Ruff check/format/diff-check PASS。该作者自测不替代 ds Evidence。

## MEDIUM blocker — tokenizer resolver 覆盖非合同 runtime 字段

### Location
child:
cosmos_framework/data/generator/action/datasets/robocasa_exact_window_policy.py:158-161

### Current behavior
resolved_tokenizer_config() 直接：

1. deepcopy(EDGE_MODEL_CONFIG["tokenizer"])
2. 仅把 encode_exact_durations 替换成 manifest list
3. 返回整份 tokenizer config

### Why this is unsafe
Corrected runtime 应该只由 Phase2 contract裁决：
- encode_exact_durations
- encode_chunk_frames compatibility
- compute dtype/capability

而不是重建所有 runtime tokenizer 字段。

当前 project Edge wrapper 已显式覆盖：
action_policy_robocasa_edge.py:23-24
- encode_exact_durations = [33]
- vae_path = "${oc.env:WAN_VAE_PATH}"

bare EDGE_MODEL_CONFIG 则是：
edge_model_config.py:126-136
- encode_exact_durations = None
- vae_path = "pretrained/tokenizers/video/wan2pt2/Wan2.2_VAE.pth"

因此未来 Phase3 若直接消费 resolved_tokenizer_config()，会把已经解析好的 WAN_VAE_PATH 等非合同 runtime 配置悄悄恢复成 base default。这个 helper 名称与 Phase2 输出语义会诱导这种错误接线。

### Frozen-contract violation
Phase2 v1.1 §12-14 的目标是：
- manifest决定完整 exact-duration contract；
- fixed Edge只提供 capability authority；
- legacy runtime config经 corrected overlay/validator后使用；
- 本阶段不应替换无关 runtime fields。

### Acceptance
只做最小 Phase2 修订：

1. 不再用 bare EDGE_MODEL_CONFIG 生成“整份 runtime tokenizer config”。
2. 改成下列任一等价安全接口：
   - resolve_tokenizer_config(candidate_config)
   - apply_manifest_tokenizer_contract(candidate_config)
3. 该接口必须：
   - deepcopy caller-supplied candidate tokenizer config；
   - 先/后验证其 encode_chunk_frames 属于 fixed Edge capability；
   - 只把 encode_exact_durations 设置成 manifest 的完整 list；
   - 保留所有非合同字段逐值不变，包括至少：
     vae_path, bucket_name, object_store_credential_path_pretrained,
     spatial_compression_factor, temporal_compression_factor,
     use_streaming_encode, keep_decoder_cache, chunk_duration。
4. formal test 使用 current action_policy_robocasa_edge tokenizer：
   - input vae_path == "${oc.env:WAN_VAE_PATH}"
   - input exact durations == [33]
   - resolve 后 exact durations == manifest完整 list
   - vae_path及其它非合同字段保持不变
   - resolve 后 validate_tokenizer_config PASS
5. legacy Edge dataset仍因 chunk32 fail corrected dataset validator；不得因此把旧 training route变成可用。
6. 删除/禁止 no-arg helper 产生裸 base runtime config，避免未来误用。
7. 最终 tree 重跑 Phase1A+1B+2 target pytest、Ruff check/format、diff-check。
8. 不扩大到 Phase3、old recipe、model/trainer/inference/server/eval。

## Boundary

本 review 不授权：
- ds execution
- Phase3 cached latent transport
- OmniMoT cache-hit
- Local-TTT
- GPU/training/simulation

cx 修复后形成 fresh child/root exact pair，再做 fresh review。