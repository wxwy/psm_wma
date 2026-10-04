# Corrected V3 Phase 2 源码接缝审计 v0.1

- 日期：2026-10-05；性质：**cx 只读技术输入，不是 Phase 2 设计或实现授权**。
- 上游 authority：Corrected V3 v3.0 详细设计 §15–17/§42–44/§60、Phase 0 mapping、Phase 1B closure review `2026-10-05_V3_phase1b_closure_d7aa5673_21e60d6e.md`。
- 当前实现基线：root `a3156bb7927770c453719fc578e76ba23e78df87`、child/Gitlink `21e60d6eb3a04846ffa7280aca18f6005399363e`。Phase 1B 已正式关闭；当前 `docs/build/` 未见 Phase 2 专项 frozen design。

## 已核对源码事实

1. Phase 1B `robocasa_exact_window_source.py` 的 `ExactWindowRawSourceWindow` 输出 `action12[16,12]`、`state16[17,16]`、caption、task class 和 global-row witness；不转换 action/state，不接视频 latent。
2. 官方 `cosmos-framework/cosmos_framework/data/generator/action/datasets/robocasa_lerobot_dataset.py:400–412` 的 `_build_frame_wise_action` 将 raw12 的 EEF axis-angle3 经 `convert_rotation` 转 rot6d6，生成 arm10；当前函数体未读取实例字段。
3. 同文件 `:509–527` 的 `__getitem__` 在 `use_base_action=True, base_encoding="raw"` 时原样保留 base_motion4/control_mode1，并与 arm10 拼成 raw15。该 `__getitem__` 的 `_fetch_sample` 隶属现有 latest multi-shard loader，不能直接以 Phase 1B flat-source 相对索引调用。
4. 同文件 `:414–441,529–546` 的 `_build_initial_state` 从 state16 的当前帧提取 EEF pos3、xyzw quat→rot6d6、双指 qpos 差；raw15 路径前补五个零，作为第 0 行形成 `[17,15]`。该方法依赖实例 `_chunk_length`。
5. 官方 `cosmos-framework/cosmos_framework/data/generator/action/utils/transforms.py:345–395` 的 17 video / 17 action WAM 布局为 Case B：第 0 action 行进入 `condition_frame_indexes_action=[0]`。仍须由 Phase 2 CPU 测试证明 clean/noise0/no-loss 与不可执行行的完整链路。
6. 项目 `action_policy_robocasa_edge.py:23` 固定 `encode_exact_durations=[33]`；官方 Nano recipe `action_policy_robocasa_nano.py` 固定 chunk32；项目 `examples/psm_wma_robocasa_h100.py:265,275` 检查 `[33]` 并建 chunk32/raw-source catalog。这些入口不能直接充当 corrected H_pred16/cache-first 配置。

## 需 GPT 在新的 Phase 2 Gate 冻结

| 问题 | 需要明确的合同 |
|---|---|
| 官方转换复用 | Phase 1B flat-source 窗口如何调用官方 raw12→raw15 与 state16→state15 权威方法，避免实例化 latest multi-shard loader，也不复制转换公式；允许的最小 helper/adapter 文件范围。 |
| 行语义 | `state15_t + 16×raw15` 形成 `[17,15]` 后，何处验证第 0 行 clean/noise0/no-loss/non-executable，padding 到 max_action_dim64 不改变 canonical raw15。 |
| 配置与 manifest | corrected Edge overlay 如何从指定 cache manifest 校验完整 `vae_encode_contract`、H_pred16/17帧、fixed tokenizer 能力与 resolved config；缺 manifest、旧 `[33]`、chunk32、dtype/时长/chunk-frame 冲突均 fail-closed。实际完整 exact-duration 列表不得猜测或重编码。 |
| R 范围 | v3.0 把 H_pred/R 默认16列于 Phase 2，但 server/eval 实现位于 Phase 6；需界定 Phase 2 只冻结/静态验证 R 合同，还是允许修改 server/eval wrapper。 |
| 验收 | synthetic raw12/state16 对官方方法逐值 parity；base/mode/translation/gripper 保真、旋转矩阵语义一致；`[17,15]` state 行与 padding/mask；caption/class 不混用；非法 shape/非有限值/旧配置拒绝；Phase 1A/1B 回归。 |

本审计只读取设计与本地源码；未访问真实 cache/source/训练服务器，未运行项目代码、测试、GPU、训练或仿真；不声称 Phase 2 已获实现授权。
