# G2-N6-F1-A2：官方 object_cfgs.info.cat 最小修复

整改依据：[GPT 正式 REQUEST_CHANGES](https://github.com/wxwy/psm_wma/blob/gpt/review-g2-n6-f1a-7c12caea-20261108/docs/collab/chatgpt/reviews/2026-11-08_G2_N6_F1A_7c12caea_GPT_independent_review.md)（review 分支提交 `a79a8051eb9bf0faae920c8aa9d204c2e2934f02`，文件 blob `7defb0d480332dac1913e8319c9c2cc563e4c828`）；[Issue26 F1A-B1 指令](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6720601972)。

独立分支 `codex/g2-n6-f1-a2-info-cat` 从原 F1-A handoff `08a1bbb14db4aa5b05a51724f27a60c72f826c87` 派生，原 runtime `7c12caea`。本批仅修改 `g2/sim/prescan.py` 的类别解析，不改资产加载、状态恢复、颜色采样、native、完整 geom 审计或完成范围算法。

## 新行为

- 保留默认类别选择顺序 `obj_groups → obj_type → cls`。只有这些字段均不存在时才默认使用嵌套 `info.cat`。
- 显式 `source_category_field="info.cat"` 从原始 `record.info.cat` 读取，按原值严格比较 `source_category`。不接受伪造的顶层 `"info.cat"` 或任意 dotted path。
- `fine_category={"field":"info.cat","value":...}` 单列真实细类；已有 groups 保持原值和原含义。`type` 仅保存在 `coarse_type`，不能作为细类来源。
- 已提供但格式错误的 info/cat、空白/非文本细类拒绝；已有 groups 不能隐藏错误的细类。无 info 的合法旧字段仍兼容。
- strict JSON Pointer、官方唯一 name、类别/角色/body 校验和禁止 MJCF 静默替代不变。

公开复现结构是 `obj: groups=[tool,utensil], info.cat=whisk` 与 `distr: type=object, info.cat=soap_dispenser`。未读取服务器 ep_meta 文件。两者的使用示例：

```json
{
  "role": "visual",
  "source_kind": "ep_meta",
  "ep_meta_pointer": "/object_cfgs/1",
  "source_instance_name": "distr",
  "source_category_field": "info.cat",
  "source_category": "soap_dispenser"
}
```

实际 body 与分类理由仍按原 F1-A 合同补齐。新导出会将 fine/coarse 来源保留在 manifest 和每个相关 geom 的 source 中；完整 source-scope 复验仍逐项核对原始声明。请按新固定 SHA 重新导出并审查，不为旧工件补写字段或改哈希来代替复验。

## 本地作者证据

复用隔离 Python 3.12 / MuJoCo 3.3.7 / NumPy 2.3.5，无依赖新增。输入仅公开 schema 自建记录和自建双物体 MJCF，无原始服务器文件、模型推理或 GPU。

```bash
# 生产函数修改前，在原7c12 runtime运行相同新增测试：31项，6 FAIL/25 PASS。
python -m pytest g2/tests/test_object_category.py -q --junitxml="$RED_JUNIT"
# 修改后：160/160，零失败、零错误、零跳过；包括原129全部测试。
python -m pytest g2/tests -q --junitxml="$GREEN_JUNIT"
```

覆盖默认/显式 nested category、旧字段、独立细类/粗类型、缺失/错误 info、坏类别、重复 name、错误 pointer、顶层 dotted-key 冒充和 MJCF 替代拒绝。自建 MJCF 导出的完整 geom 审计保留两对象类别；声明子集 COMPLETE、training_ready=false、无独立 review 拒绝等门禁保持不变。详细原始 RED、JUnit、源码哈希与原129 case 保留核对见 `docs/evidence/g2_n6_f1_a2_2026-11-08/`。

## GPT 复验及停止条件

请在服务器现有隔离 CPU 环境和新的固定源码副本中复跑全套测试，并对原始 `object_cfgs[0]`/`[1]` 分别检查默认与显式 `info.cat`、真实祖先 body、错误类别/缺 info/重复 name/错误 pointer/MJCF 替代。复用既有场景与状态，不改服务器正式代码仓、不重建环境、不外传原始文件、图片、点云或报告。

原 `7c12caea` 的 fixture/source-scope 与局部四帧颜色 PASS 是 GPT 已发布的部分验收事实，不是本次作者重跑结果。新 SHA 的真实对象类别复验由 GPT 独立执行。`full_scene_review_eligible` 只表示形式上可审查，不能充当整屋认证；整屋材质、普通结构、真实模型、六图/Island 人工、PSS/Cosmos 和训练均未获本批批准。

本批形成新固定源码及 Issue26 交接后 STOP，等待独验；不关闭 F1-A、Issue26 或 native #8，不合并生产/V3/Gitlink/旧 PR。
