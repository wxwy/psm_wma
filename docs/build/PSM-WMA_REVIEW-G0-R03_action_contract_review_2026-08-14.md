# PSM-WMA REVIEW-G0-R03 独立审查报告（2026-08-14）

审查人：Kimi（独立复核）
对象：`ee88c29 完成 G0-R03 action contract 审计`、`46498ba 兼容 R03 本地 LIBERO 数据布局`、`b895325 刷新 R03 Gate provenance`；交付物为 Runbook v0.1、`tools/g0/audit_r03_action_contract.py`、`artifacts/g0/r03/R03_action_contract.json`、cosmos-framework `59653c5`
基线：根仓库 `b895325`；cosmos-framework `59653c5`；数据 `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot`；checkpoint `/gemini/code/models/Cosmos3-Edge-Policy-DROID`

## 结论

**APPROVE**，附 2 个 MEDIUM 与 3 个 LOW。MEDIUM-1 转 DONE 前须关闭；MEDIUM-2 超出 R03 验收范围，登记为 R05 前置项。

审计可完整复现：审查人按 Runbook 命令重跑脚本（输出至 /tmp），除 provenance 外全部字段与 Gate JSON 逐字节一致，运行时实测值（数据集 379 episodes / 95,405 窗口、[16,7]→[16,10]→[16,64] action 链、domain 5/8、projection 64→2048→64、trainable 计数）全部独立复现。不存在"未验证却宣称 PASS"的漏洞；`action_raw` 命名与实际语义不一致的问题被 Codex 诚实披露在 limitations 中。

## 发现

### MEDIUM-1：`effective_transformer_parameter_count` 标签不实，分母含 vision encoder

- 问题：JSON `trainable_scope.effective_transformer_parameter_count = 3,782,306,736`，标签为 Transformer，但审查人复算确认该计数包含 `vision_encoder` 的 412,649,712 个参数（vision 键全部 net-mapped、0 键被丢弃）。纯 Transformer 分母应为 3,369,657,024，对应 selected fraction 42.24%，而非 JSON 的 37.63%。
- 依据：审查人用同一 `_diffusers_weight_map` + `_diffusers_to_net_key` 链路独立求和，总数复算一致（3,782,306,736），并单独分离出 vision 部分；`selected_parameter_count = 1,423,379,648` 本身精确（selector 不匹配任何 vision 键）。
- 位置：`tools/g0/audit_r03_action_contract.py:47-71`（未区分 vision 文件）；误导措辞已传播到 `SESSION.md:88`。
- 最小修复：字段改名 `effective_model_parameter_count` 或拆分 `vision_parameter_count`/`transformer_parameter_count`，重跑审计并同步 SESSION.md。
- 阻止 DONE：是（修复成本一个字段加重跑）。

### MEDIUM-2：归一化统计来源未记录、与本地数据分布的匹配未验证（登记为 R05 前置）

- 问题：pipeline 实际使用仓库内置 `normalizer_stats/libero_native_frame_wise_relative_rot6d.json`（`libero_lerobot_dataset.py:48,221-226`），recipe 注释称该统计匹配 `nvidia/LIBERO_LeRobot_v3`（v3.0，见 `action_policy_libero_nano.py:198-200`）；本地数据是 v2.1 `libero_10_no_noops` 布局。R03 验证了"统计被正确应用"（normalization trace PASS），未验证"统计与该数据分布匹配"；JSON 也未记录所用 stats 文件。
- 影响：若分布不匹配，R05 tiny-overfit / R06 closed-loop SR 会静默劣化且难以归因。不影响 R03 的 contract 结论本身。
- 最小修复：R03 JSON 补记 stats 文件路径与 sha256；R05 启动前做一次分布 sanity check（本地样本 action 分位数 vs 统计文件 q01/q99）。
- 阻止 DONE：否，但必须在 R05 前关闭。

### LOW-1：cosmos-framework `59653c5` 数据布局 fallback 无单元测试

- 问题：`base_dataset.py` / `libero_lerobot_dataset.py` 新增 JSONL 与 `episode_*.parquet` fallback，无对应测试；该仓库有测试惯例（如 `action_policy_server_robolab_test.py`）。
- 最小修复：补一个最小单测（构造 jsonl/per-episode 布局的临时目录，断言与原布局产出一致的 episode/task 表）。
- 阻止 DONE：否。

### LOW-2：R03 Runbook 状态仍为 `draft`

- 位置：`PSM-WMA_G0_R03_action_contract_runbook_v0.1.md:3`。审查项关闭后应流转为 reviewed/frozen，后续改动走新版本。
- 阻止 DONE：否。

### LOW-3：provenance.repo_commit 语义自指

- 问题：JSON 记录 `repo_commit=ee88c29`，即"包含该 artifact 的提交"本身；实际审计运行在 `46498ba`，事后由 `b895325` 刷新 provenance。审查人已核验 `b895325` 仅改动 timestamp 与 repo_commit 两行，未触碰任何实测值，且重跑复现全部数值，因此无诚实性问题；但字段名易被读作"审计执行时的提交"。
- 最小修复：字段注释或改名（如 `artifact_commit`），或在 Runbook 中说明该字段语义为"artifact 生效提交"。
- 阻止 DONE：否。

## 已核验的源码锚点

- `cosmos_framework/data/generator/action/domain_utils.py:12,15`：`libero=5`、`droid_lerobot=8`。
- `cosmos_framework/model/generator/mot/domain_aware_linear.py:17-47`：per-domain 权重存于 `nn.Embedding`——warm-start 决策中"零梯度不足以阻止 AdamW weight decay 改写其他 domain 行"的担忧在结构上成立，R04 的行级保护验证是必要的。
- `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:300-310` `_build_frame_wise_action`：7D axisangle → rot6d 10D 转换；`:314-335` concat_view = 第三人称左 + wrist 右；`:48,221-226` 归一化统计来自内置 JSON。
- `cosmos_framework/data/generator/action/transforms.py:422-433`：`resolution=None` 时自动检测 tier 并吸附到 16 倍数画布——解释实测 video `[3,17,192,320]`（192/320 均为 16 的倍数），且 recipe `action_policy_libero_nano.py:214` 同样传 `resolution=None`，审计路径与训练路径一致。
- `cosmos_framework/simulation/libero/closed_loop_eval.py:382-400,507-533,580-602`：图像 rotate_180/flip、gripper 三模式映射、rot6d→rotvec 7D delta，与 JSON `simulation_contract` 描述逐行相符。
- `cosmos-framework@59653c5`：原 parquet 布局优先、JSONL/per-episode fallback，不改变 action/video 语义；本地数据 `meta/info.json` 确认 v2.1、fps 20、379 episodes。
- `action_policy_libero_nano.py:83-97`：官方 substring selector 七项，与 JSON `trainable_scope.selectors` 一致。

## 已执行的只读/轻量验证

- 按 Runbook 命令重跑 R03 审计（CPU，无 GPU/外网，输出 /tmp）：PASS，非 provenance 字段与 Gate JSON 逐字节一致。
- 独立复算参数计数：net-mapped 总数 3,782,306,736 复现；分离出 vision 412,649,712（MEDIUM-1 依据）。
- `sha256sum tools/g0/audit_r03_action_contract.py` 与 JSON `script_sha256` 一致。
- `git show b895325`：仅刷新 timestamp 与 repo_commit 两行。

## 未执行的验证及原因

- checkpoint 数值 forward：R03 Runbook 明确划归 R04。
- DomainAwareLinear 真实权重加载：Runbook 声明 smoke 用随机权重，属既定范围。
- 归一化统计分布匹配：超出 R03 断言，已登记为 R05 前置（MEDIUM-2）。

## DONE 前关闭清单

1. MEDIUM-1：修正参数字段标签/拆分并重跑审计，同步 SESSION.md 措辞。
2. LOW-2 随收尾流转 Runbook 状态；LOW-1/LOW-3 可延后但建议同批处理。
3. MEDIUM-2 登记进 R05 前置条件（TODO.md G0-R05 或 SESSION.md 交接）。
