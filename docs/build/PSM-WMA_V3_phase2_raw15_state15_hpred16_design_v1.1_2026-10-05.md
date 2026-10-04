# PSM-WMA V3 Corrected — Phase 2 Official raw15/state15 + H_pred16 Contract v1.1

日期：2026-10-05
状态：GPT frozen Phase2 design authority；允许 cx 实现与 CPU/static tests；不授权 ds/GPU/训练/仿真。

本 v1.1 取代并废弃未提交且已损坏的 v1.0 文件。Phase2 authority 只认本文。

## 1. Phase2 目标

Phase1A/1B 已正式关闭，当前稳定输入是：

ExactWindowRawSourceWindow
- action12: 16 x 12
- state16: 17 x 16
- ai_caption
- task_class
- cache/source exact identity

Phase2 只解决：
1. official raw12 -> raw15
2. official state16 -> state15
3. Corrected V3 H_pred/chunk_length = 16 与完整 VAE cache contract 的 project-level resolved authority

并证明 17 行 action stream 的 official 语义：
row0 = current state15 clean condition
row1..16 = 16 个 predicted raw15 actions

Phase2 不做视觉 cache 注入、不做 Local visual/TTT、不做训练。

## 2. Parent authority

- Corrected V3 detailed design v3.0
- Phase0 implementation mapping
- Phase1A closure
- Phase1B closure: root d7aa56730b8d04c50ed471179a0c08a038f3c07e / child 21e60d6eb3a04846ffa7280aca18f6005399363e
- cx read-only audit: docs/build/PSM-WMA_V3_phase2_source_seam_audit_v0.1_2026-10-05.md

official/latest host conversion authority:
cosmos_framework/data/generator/action/datasets/robocasa_lerobot_dataset.py

## 3. source raw12 layout

Phase1B action12 是 RoboCasa365 LeRobot source contract：

0:4   base_motion4
4:5   control_mode1
5:8   eef_pos3
8:11  eef_axisangle3
11:12 gripper1

注意：
- 这是 LeRobot source raw12 的 base-first layout。
- simulator env.step 的 env12 是另一个 arm-first layout。
- Phase2 只处理 source -> policy，不处理 policy -> env。
- 不得混淆 source raw12 与 simulator env12。

## 4. official raw12 -> raw15

禁止在 Phase2 module 中重新实现 axis-angle -> matrix -> rot6d。

唯一 arm conversion authority：
RoboCasaLeRobotDataset._build_frame_wise_action

推荐 project bridge：
- 不运行 RoboCasaLeRobotDataset constructor
- 创建 object.__new__(RoboCasaLeRobotDataset) 的最小 proxy
- proxy._chunk_length = 16
- 直接调用 official private method

arm10 = official _build_frame_wise_action(proxy, action12)

然后只做 official raw-base branch 已有的结构组合：

raw15 =
base_motion4 unchanged
+ control_mode1 unchanged
+ arm10

结果必须是 16 x 15。

不得实例化 latest multi-shard RoboCasa loader，也不得复制旋转公式。

## 5. official state16 -> state15

唯一 EEF-state conversion authority：
RoboCasaLeRobotDataset._build_initial_state

proxy._chunk_length = 16

state10 = official _build_initial_state(proxy, state16)

然后严格沿 official raw-base use_state branch：

state15 =
5 个 exact zero
+ state10

前 5 维必须 exact zero：
- 不填 base pose
- 不填 base velocity
- 不填 previous action

## 6. Phase2 canonical output

建议 frozen dataclass：
ExactWindowPolicyActionWindow

至少包含：
- key
- start_frame
- action15: 16 x 15
- state15: 15
- action_with_state15: 17 x 15
- ai_caption
- task_class
- cache/source binding digest

硬合同：
action_with_state15[0] == state15
action_with_state15[1:] == action15

所有输出必须 float32、contiguous、finite。

## 7. fail-closed

输入必须是：
- action12 shape 16 x 12
- state16 shape 17 x 16
- floating
- finite

错误 shape / nonfloating / nonfinite 一律 fail。

Phase2 不接受 horizon32 输入。

## 8. official 17-row sequence semantics

Corrected action stream：
row0 = current state15
row1..16 = raw15 actions

因此：
action_length = 17
logical video_length = 17

official build_sequence_plan_from_mode:
mode = wam
video_length = 17
action_length = 17

必须产生：
- condition_frame_indexes_vision = [0]
- condition_frame_indexes_action = [0]
- Case B / initial-state semantics

Phase2 不自己实现 SequencePlan。

## 9. row0 clean / sigma0 / no-loss

这条用 official CPU contract tests 锁死，不修改 host model。

Packing 应得到：
- action condition mask = [1,0,...,0] 共17行
- noisy action frame indexes = 1..16
- action mse loss indexes 不包含 row0

current OmniMoT noising:
sigma_action = sigma * (1 - condition_mask)

因此 row0 sigma = 0，保持 clean。

official flow-matching loss:
noisy_mask = 1 - condition_mask
所以 row0 不贡献 action loss。

Phase2 formal tests至少证明：
1. SequencePlan row0 conditioned
2. packing noisy/mse indexes exclude row0
3. synthetic loss 只有 row0 error 时 contribution = 0
4. rows1..16 error 时 contribution > 0

不需要构造完整 GPU OmniMoT。

## 10. ActionProcessor / max_action_dim64

Corrected host仍使用 max_action_dim = 64。

official ActionProcessor(max_action_dim=64)，action_normalizer=None。

对 17 x 15：
- action_raw exact == input 17 x 15
- raw_action_dim == 15
- padded action == 17 x 64
- first15 channels exact
- channels15:64 全0

padding 不得改变 state row 或 raw15。

## 11. CorrectedRoboCasaPolicyContract

Phase2 同一 project module 建立 frozen runtime contract，例如：
CorrectedRoboCasaPolicyContract

defaults：
- fps = 20.0
- action_horizon = 16
- chunk_length = 16
- observation_frames = 17
- source_action_dim = 12
- action_dim = 15
- source_state_dim = 16
- state_dim = 15
- max_action_dim = 64
- camera_set = left_wrist
- use_state = True
- use_base_action = True
- base_encoding = raw
- action_normalization = None
- mode = wam
- replan_default = 16

约束：
1 <= replan_steps <= action_horizon

TTT 的 T 不属于该 contract，不能和 horizon 绑定。

## 12. contract 必须由 cache manifest 构造

推荐：
CorrectedRoboCasaPolicyContract.from_cache_catalog(catalog)

读取 Phase1A frozen catalog.vae_encode_contract。

要求：
- cache chunk_length = 16
- fps = 20
- exact durations 非空且必须包含17
- compute_dtype == torch.bfloat16
- encode_chunk_frames 保留完整 manifest mapping

不得猜完整 exact duration list。
不得擅自改成 [17] 或 [17,61,73]，除非 manifest 本身如此。

## 13. fixed Edge tokenizer compatibility

fixed Edge model tokenizer authority：
EDGE_MODEL_CONFIG["tokenizer"]

当前能力：
- Wan encode dtype = bfloat16
- encode_chunk_frames 是 resolution mapping
- base encode_exact_durations = None

Phase2 validator规则：

### 13.1 encode_chunk_frames
对 manifest 中每个 key：
fixed Edge tokenizer同 key必须存在且 value相同。
manifest 有 fixed tokenizer 不认识的 key -> reject。
fixed tokenizer 多出的 capability key允许。

### 13.2 exact durations
corrected runtime tokenizer的 encode_exact_durations 必须设置为 manifest 完整 list。
不能只检查“含17”后继续使用旧 [33]。

### 13.3 compute dtype
manifest compute_dtype必须与 fixed Wan bfloat16一致。

不一致 fail-closed；禁止重编码 cache 来迁就 config。

## 14. legacy config contamination

历史路径：
- action_policy_robocasa_nano.py: chunk32 / 33 frames / [33]
- action_policy_robocasa_edge.py: inherited chunk32 / [33]
- examples/psm_wma_robocasa_h100.py: [33] guard + raw-dataset chunk32 catalog

Phase2 不把这些旧入口原地改成 corrected training route。

原因：Phase3 尚未接 video_latent transport / model cache-hit。

Phase2 必须提供 validator，使这些 legacy configs明确 FAIL corrected contract。

Phase3 再建立唯一 corrected training entry，消费：
- Phase1B cache/source binding
- Phase2 policy contract
- Phase3 cached-latent transport

这样避免“配置写16，但数据仍走旧 raw dataset”的假 corrected path。

## 15. corrected default16 的含义

Owner 已冻结：
action_horizon/chunk_length default = 16。

从 Phase2 起：
- 所有新 Corrected V3 module/entry 默认只能是16
- 禁止从 old official/Nano/Edge 继承32后依赖 caller 手动覆盖
- legacy 历史路径可保留32，但 corrected validator必须拒绝

server/eval 当前 fallback32 不在 Phase2 修改。
Phase6 必须让 corrected server/eval H_pred/R 默认16并 fail-closed。

Phase2 只冻结未来 contract，不越权改 simulation/inference。

## 16. 实现文件

Child 新增：
cosmos_framework/data/generator/action/datasets/robocasa_exact_window_policy.py

Formal test：
robocasa_exact_window_policy_test.py

允许 import：
- Phase1B source window dataclass
- Phase1A cache catalog
- official RoboCasaLeRobotDataset
- official ActionProcessor
- official build_sequence_plan_from_mode
- official sequence packing / flow loss helper用于 CPU contract tests
- EDGE_MODEL_CONFIG 用于 compatibility validator/test

不需要修改：
- official RoboCasa dataset core
- OmniMoTModel
- flow loss
- sequence packing
- old Nano recipe
- old Edge recipe
- H100 launcher

如果 cx 判断必须改这些 core文件，先停并回报 GPT。

## 17. official helper bridge 防漂移

因为 _build_frame_wise_action / _build_initial_state 是 official private methods，tests必须证明 adapter真实调用它们：

1. spy official methods，adapter call count正确
2. official method抛错时 adapter不 silent fallback
3. Phase2 module禁止 import/use convert_rotation
4. AST/source test禁止自实现 rotation math

未来 upstream private API drift时 tests应失败并重新审核。

## 18. raw15 数值验收

使用可区分 synthetic raw12：
- base_motion4 各维不同
- control_mode ±
- eef translation distinct
- axis-angle 非零
- gripper distinct

验证：
1. raw15[0:4] == source base_motion4 exact
2. raw15[4] == source control_mode exact
3. raw15[5:8] == EEF translation exact
4. raw15[8:14] official rot6d
5. raw15[14] == gripper exact
6. official rot6d->matrix 与 source axis-angle->matrix rotation semantic一致
7. source raw12不被 in-place 修改

不要只用全零 action。

## 19. state15 数值验收

synthetic state16：
- base pose故意非零
- EEF pos distinct
- EEF quaternion valid/nontrivial
- finger qpos distinct

验证：
1. state15[:5] exact zero
2. state15[5:8] == current EEF pos
3. state15[8:14] official rot6d matrix semantic一致
4. state15[14] == qpos0-qpos1
5. 后续16帧 state变化不改变 current state token
6. base pose不能泄露进前5维

## 20. VAE contract / legacy config tests

至少：
1. valid synthetic Phase1A manifest -> H_pred16 / 17 frames
2. exact durations缺17 -> fail
3. compute dtype非 bfloat16 -> fail
4. manifest chunk-frame key fixed Edge缺失 -> fail
5. same key数值不同 -> fail
6. fixed Edge额外 capability key允许
7. resolved tokenizer exact durations == manifest完整 list
8. old Edge [33] config fails corrected validator
9. old Nano chunk32 config fails corrected validator
10. H_pred32/chunk32 reject
11. replan default16
12. R > 16 reject

## 21. action/state/sequence CPU tests

至少：
1. valid Phase1B window -> action15/state15/action_with_state
2. input shape/dtype/nonfinite fail
3. raw base/mode/pos/gripper exact preservation
4. rotation matrix semantic parity
5. state first5 exact zero
6. state current-row only
7. official helper spy
8. no copied rotation implementation
9. official WAM 17/17 -> action condition=[0]
10. packer condition row0=1
11. noisy/mse indexes exclude row0
12. flow loss row0-only error =0
13. rows1..16 error >0
14. ActionProcessor raw_action_dim=15
15. 17 x 64 first15 exact + tail zeros
16. no action normalization
17. caption/task_class unchanged
18. Phase1A + Phase1B tests全部回归

## 22. Phase2 输出边界

Phase2 closure 后：

ExactWindowRawSourceWindow
 -> OfficialRoboCasaPolicyAdapter
 -> ExactWindowPolicyActionWindow
 -> CorrectedRoboCasaPolicyContract(H_pred16, obs17, full manifest VAE contract)

这仍不是最终 training sample。

Phase3 才接：
same cache window latent
+ Phase2 action/state/text
-> ActionSFT-compatible cached-latent sample
-> OmniMoT cache-hit seam

## 23. 非目标

Phase2 禁止：
- OmniMoTModel 修改
- video_latent model cache-hit
- Local visual96
- Local-TTT core
- grouped B_stream/T/GA
- trainer/DCP
- inference/server/eval
- raw15->env12
- executed-action canonicalization
- cache rebuild
- 训练服务器资产
- GPU/训练/仿真

## 24. Commit / Gate

cx：
1. 全文读 v3.0 + Phase0 mapping + Phase1B closure + 本 v1.1
2. root TODO/SESSION认领 exact files
3. child实现 + formal CPU tests
4. 回归 Phase1A/1B
5. Ruff check / format --check / diff-check
6. child v3-local-ttt commit/push
7. root Gitlink + TODO/SESSION + Inbox
8. root V3 commit/push
9. 不自授 approve

GPT：
fresh source review。

ds：
仅 GPT fresh exact-pair authorization 后运行 CPU/static Evidence。

Phase2 closure 后进入 Phase3：
cache-driven ActionSFT sample + video_latent transport + OmniMoT training cache-hit seam。
