# Issue54 / Draft55：A1 F1/F2 窄增量修复

日期：2026-11-17（Asia/Shanghai）。作者实现/CPU 交接，不是 GPT 真实数据验收。

## 依据与保留范围

审核对象 Root `27ccadb051a71adf348ee14206d7ac59e9195d36` / Child `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。已从原分支快进读取 `691c5303`、`8a23a912` 两份审核资料提交及完整正式 REQUEST_CHANGES 报告、三条行内意见和原始合成反例。

GPT 独立执行的原283 + A1 50 + 关联45 =378 PASS/0skip 仍有效；另外三条反例 RED 表明真实 caption 布局和任务角色不完整。不能用前者覆盖后者。原审核文件、探针、日志和已通过的第一批机制保留不改。

本轮只修改三个生产模块：`language_context.py` 的源表规范化、`task_entities.py` 的两个角色及版本、`stage_a.py` 的角色版本 resume 门禁。未修改 #53 cache 核心/CLI、renderer/成员/双变体/选图算法、旧 compact 校验、nav、Child/Gitlink、G1、训练或 A2 消费者。

## F1：真实 Parquet 布局

`normalize_task_table` 在生产 `load_flat_captions` 的真实 `read_table().to_pylist()` 后统一规范化以下明确字段：

| 源列 | 内部 ID | 内部原始文本 |
|---|---|---|
| task_index + task | task_index | task |
| task_index + 字符串 __index_level_0__ | task_index | __index_level_0__ |
| 整数 __index_level_0__ + task | __index_level_0__ | task |

字符串索引与显式 task 文本同时出现时必须相等；列名重复、缺少明确 ID、重复/非法 ID、无效文本或冲突别名均拒绝。有显式 task_index 时，数字 Pandas 行索引只作无关行元数据，不能替代 task ID。测试使用非顺序 ID/不同物理行序，防止把行号当身份。

原文不 strip/改写/格式化；frame→task_index、episode/frame 身份、ep_meta.lang 一致性和原文件哈希复核均保留，没有从 ep_meta 兜底。候选语言模板/预算/VAE 预处理不变。

## F2：独立来源角色及下游消费

- CloseBlenderLid 同时要求 Blender 本体和独立 BlenderLid：`target` / `manipulated_lid`。空 fixture_refs 时仅通过唯一官方 class 找源实例；缺失或多义显式 UNRESOLVED，不把本体 part 当作另一实例，也不按名称前缀猜。
- CounterToStove 明确区分 `obj` 被移动物体、`obj_container` 源容器、`container` 目标容器；保留 stove reference，排除真实干扰物。只有精确官方 object_cfgs 身份和 SG source 映射可绑定，缺失/重复/不在 SG 都不能返回 BOUND。
- 公开固定源码中，任务 `_get_obj_cfgs` 请求 `try_to_place_in`，Kitchen 工厂在满足初始化分组条件时以 `cfg.name + '_container'` 建立真实源容器。不能从这个命名规则自行虚构不存在对象。本修复保守要求对应声明/SG 证据；未知或无此源记录的变体保持 UNRESOLVED，不声称所有历史/可选变体都通过。来源摘要更新于既有 `PSM-WMA_G2_Stage_A_task_rule_sources_2026-11-17.json`，公开 factory blob `f7f50935c8acc421090537e73e276033503031c6`，不取私有资产。

角色规则升级为 `robocasa_atomic_initialization_roles_v2_candidate`；每个实例所有 part→全部 SG IDs 仍保留。profile validator 拒绝旧规则结果，避免 `--resume` 继续使用旧版不完整 TaskEntitySet；这不改变旧 compact schema，也不重写旧输出。新 profile 使用独立 staging，原生图像工作阶段仍可在既有身份合同下复用。

新增18类角色预期由测试里的独立任务定义表手工列出，不读取产品 FIXTURE_RULES/OBJECT_RULES 生成预期。共同输入包含大量无关 fixture/object，断言全部预期角色、精确源实例与多 part/多 SG ID 集合、干扰物/初始化 src 排除和非唯一 counter 语义。该表是合成语义回归，不代替18类全部真实 Episode 变体认证。另有 lid/plate 缺失、多义和下游增强文本/额外关联 View 的用例；额外方向是显式合成成员集，不宣称实测了真实 Episode 漏图数量。

## 测试与环境边界

只用现有 `/workspace/.venvs/g2-view-vae-52/bin/python`，CPU、无网络执行测试；没有新环境、依赖安装或 overlay。两个现有本地解释器 find_spec(pyarrow) 均为 None。

- 两条原始 F2 函数体从未修改的审核文件 AST 加载，源文件 SHA256 固定 `860424fa81b6447cb361d7272ff0a365dfef6ef6087b0a3f51ab97f63fd306e0`。加载时只排除与这两条无关的顶层 Arrow import；不改断言或替身模拟 Arrow。作者复现 RED2→GREEN2，单独计数。
- F1 的原始实际 Parquet 反例及新增10项真实临时 Parquet 用例在本地 **NOT_RUN / dependency skip**；不能称三条原始断言已全 GREEN。新19项纯源表/身份/冲突检查可在无 Arrow 下执行；它们不能代替真实 Parquet I/O。
- 原50案例身份全保留；旧 Blender fixture 改为本体多 fragment + 独立 BlenderLid，纠正将 lid 塞入本体 source 的失真输入，没有放松期望或删除测试。

完整命令、各组原始日志/JUnit、环境和源指纹、原例回放 adapter 在 `docs/collab/codex/evidence/2026-11-17_issue54_f1_f2/`，最终数量以其 gate.json 为准。开发/RED/回放覆盖不与完整回归相加。

```bash
cd /workspace/psm_wma_issue52
ISSUE54_F1F2_OUT=/tmp/issue54_f1f2_cpu_new \
  bash docs/collab/codex/evidence/2026-11-17_issue54_f1_f2/commands.sh
```

## GPT 窄复审入口

从新的固定实现/原 Child 的隔离 checkout，在服务器已有环境执行；不安装依赖、不切换生产 checkout、私有文件留服务器：

```bash
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$PWD/cosmos-framework:$PWD"
export COSMOS_DEVICE=cpu COSMOS_TRAINING=0 COSMOS_INTERNAL=0
PY=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
OUT=/path/to/new/isolated/evidence
"$PY" -m pytest -q -p no:cacheprovider \
  docs/collab/chatgpt/evidence/2026-11-17_issue54_27ccadb0/test_review_source_contracts.py \
  --junitxml="$OUT/original_probes.xml"
"$PY" -m pytest -q -p no:cacheprovider g2/tests/test_stage_a_*.py \
  --junitxml="$OUT/stage_a.xml"
```

首个命令应由原 RED3 转 GREEN3；本地没有验证这一结论。随后复验真实四条 caption、独立 BlenderLid、CounterToStove/004540 源盘子及18类初始化语义。修复通过后才继续既定真实 producer/双变体像素/空间元数据 gate，不关闭语言来代替通过。

A2 worker/ACK/恢复/新来源补编码仍不在本次补丁。真实 PyArrow/RoboCasa/native/F27、GPU/VAE、全量、state15/联合对齐、训练和合并未运行。PR55 保持 Draft；V3、PR53、nav、Child/Gitlink 和旧数据不改。
