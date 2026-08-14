# PSM-WMA REVIEW-G0-R02 独立审查报告（2026-08-14）

审查人：Kimi（独立复核）
对象：`defdb19 完成 G0-R02 checkpoint 元数据审计` 交付的 Runbook v0.1、`tools/g0/audit_r02_checkpoints.py`、`artifacts/g0/r02/R02_edge_policy_checkpoint_audit.json`
基线：根仓库 `baa046f`；cosmos-framework `ad9158e`；checkpoint `/gemini/code/models/Cosmos3-Edge-Policy-DROID`

## 结论

**APPROVE**，附 1 个 MEDIUM（转 DONE 前须关闭）与 4 个 LOW 收尾项。

R02 的核心事实主张全部经独立复核属实，审计脚本可逐字节复现 Gate JSON，脚本的索引合并语义与受支持加载入口 `_diffusers_weight_map` 完全一致。不存在"未实际验证却宣称 PASS"的漏洞：所有 index/config 事实均为脚本实读，LIBERO 契约值经审查人与官方 recipe 逐一比对确认。

## 发现

### MEDIUM-1：R02 Gate JSON 缺少 provenance 字段

- 问题：`R02_edge_policy_checkpoint_audit.json` 无审计时间戳、仓库提交、脚本版本/哈希、执行命令记录。
- 依据：R01 审查已确立 Gate JSON 必须带 provenance（`repo_commit`、`run_config` 等）的标准，见 `docs/build/PSM-WMA_REVIEW-G0-R01_execution_review_2026-08-13.md` 与 `tools/g0/collect_r01_gate_json.py` 的 commit 断言；AGENTS.md 要求 Runbook 含回填字段。
- 位置：`tools/g0/audit_r02_checkpoints.py:72-141`（result 字典无 provenance 块）。
- 最小修复：在 `result` 中增加 `provenance` 字段（UTC 时间戳、`git rev-parse HEAD` 输出、脚本路径与命令行），并在 collect/assert 侧复用 R01 的断言模式。
- 阻止 DONE：是。

### LOW-1：LIBERO 契约值在脚本中为硬编码常量

- 问题：`libero_contract`（fps 20、chunk 16、frame_wise_relative rot6d、quantile_rot、agentview+wrist concat）是 `audit_r02_checkpoints.py:116-123` 的字面量，脚本并未从官方 recipe 读取。
- 依据：审查人已对照 `cosmos-framework/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_nano.py:202-210` 逐一核实，值全部正确；但 recipe 变更时审计不会报警。
- 最小修复：在 JSON 中为每个契约值附 `action_policy_libero_nano.py` 的 file:line 引用，或改为解析 recipe 配置。
- 阻止 DONE：否。

### LOW-2：vision_encoder 6 个 extra header 键只计数未列名

- 问题：JSON 记录 `extra_header_key_count: 6` 但未给出键名。
- 依据：审查人实读确认 6 个键为 `model.projector.linear_fc1/linear_fc2/norm` 的 weight/bias（`vision_encoder/model.safetensors` header），属未被根索引引用的 projector 权重，不影响加载。
- 最小修复：`files[...]` 增加 `extra_header_keys` 列表。
- 阻止 DONE：否。

### LOW-3：Runbook 要求"补做真实 checkpoint load smoke"，实际复用 R01 证据，文档与实践不一致

- 问题：`PSM-WMA_G0_R02_checkpoint_audit_runbook_v0.1.md:57` 写明 R02 进 REVIEW 前须"补做真实 checkpoint load smoke"；实际未单独补做，`SESSION.md:83` 记录复用 G0-R01 的 Policy 实际加载/推理证据。
- 依据：R01 Policy server 经受支持入口完整加载该 checkpoint 并产出 finite action，强于一次裸 load smoke，复用合理；但 Runbook 文字未给这个豁免。
- 最小修复：将该句改为"补做真实 checkpoint load smoke，或显式引用 G0-R01 的实际加载/推理证据"。
- 阻止 DONE：否。

### LOW-4：R02 Runbook 状态仍为 `draft`

- 问题：Gate 已 PASS 且进入 REVIEW，Runbook 头部仍为 `状态：draft`（v0.1 第 3 行）。
- 最小修复：审查项关闭后标记为 reviewed/frozen，后续改动走新版本。
- 阻止 DONE：否。

## 附带更正（非 R02 交付问题）

R02 的索引审计数据暴露出 Kimi 此前 D009 记录的一处错误：曾称"base Edge 完全没有 `k_norm_und_for_gen`，Policy-DROID 新增 28 个参数"。实读 base shard header 确认 base 同样含 28 个规范 K-Norm 键（`layers.N.self_attn.k_norm_und_for_gen.weight`）；Policy-DROID 多出的仅是 overlay 文件中的重复存储与根索引陈旧别名。Codex 原结论"规范参数名 549/549 完全一致"在规范键集层面成立。D009 已于 2026-08-14 修订，见 `MEMORY/DECISIONS.md` D009 修订条目。

## 已核验的源码锚点

- `cosmos-framework/cosmos_framework/inference/model.py:198-222` `_diffusers_weight_map`：剔除根索引 `.k_norm_und_for_gen.` 条目（:210）+ setdefault 合并 transformer 子索引（:216-219）——与审计脚本 `tools/g0/audit_r02_checkpoints.py:37-41` 语义逐行对应。
- `cosmos-framework/cosmos_framework/inference/model.py:74` `_DIFFUSERS_DROP_WEIGHT_PATH_RES`：仅保留 `transformer/`、`vision_encoder/` 路径；有效索引不含其他前缀，故审计与加载器行为一致。
- `cosmos-framework/cosmos_framework/scripts/_convert_model_to_diffusers.py:234` `_remap_language_model_state_dict`：model.py:204 注释引用属实。
- `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_nano.py:202-210`：fps=20、chunk_length=16、concat_view、frame_wise_relative、6d、quantile_rot。
- `artifacts/g0/r01/R01_edge_policy_droid_smoke.json` `repo_commit=3f63265`：包含 tools/g0 代码，R01 复核 MEDIUM-2 已关闭；Runbook §7.2 已补记 `run_r01_policy_client.py` 替代与 RoboLab 豁免，MEDIUM-1 已关闭。

## 已执行的只读/轻量验证

- 重跑 `audit_r02_checkpoints.py` 输出至 `/tmp` 并与 Gate JSON 比较：逐字节一致（REPRODUCED IDENTICAL）。
- safetensors header 实读：根索引 1014 键、K-Norm 56=28 陈旧别名+28 overlay；transformer 子索引 28 个规范 K-Norm 指向 shard 00001 且 header 实含；shard1/2 header 431/118 与索引完全吻合；vision header 443 vs 索引 437；overlay 文件 28 键物理存在。
- `config.json`：`action_gen=true`、`max_action_dim=64`、`num_embodiment_domains=32`、`use_und_k_norm_for_gen=true`；`checkpoint.json` policy：chunk 32、fps 15.0、`droid_lerobot`。
- base Edge shard header：549 键含 28 个规范 K-Norm（更正 D009 的依据）。

## 未执行的验证及原因

- 全量张量数值 diff：R02 明确界定 metadata-only，抽样数值结论沿用既有记录；非本 Gate 范围。
- `inference2/_model_io.py` 实际加载测试：JSON limitations 已声明其未兼容、禁止作为入口；修复属另立项。
- 未重新跑 GPU 加载 smoke：R01 已有同入口实际加载+推理证据，强于裸 load。

## DONE 前关闭清单

1. MEDIUM-1：JSON 增加 provenance 块并重跑审计。
2. LOW-1/2/3/4 可同批处理；LOW-3 的 Runbook 措辞修订建议与 LOW-4 状态流转一起完成。
