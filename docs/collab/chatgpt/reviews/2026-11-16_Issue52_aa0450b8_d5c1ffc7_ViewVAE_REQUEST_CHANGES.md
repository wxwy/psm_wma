# Issue #52 / PR #53 — 独立 CODE/CPU 审核

- 审核日期：2026-11-16（北京时间）。
- **Verdict：REQUEST_CHANGES — 两项限定的编码入口 P2 问题。**
- 固定实现 Root：`aa0450b8e36b2cb833beda96256a29c3db95db23`。
- 固定 Child/Gitlink：`d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2`。
- 基线 V3：`55cc5181abf8ca4b1e2a3a6b415699c457cc080b`。
- 交接 HEAD：`ee6eb750655eac681c22828e76d50315ce392beb`；GitHub compare 确认它只修改 SESSION、TODO 和 canonical Inbox，不替代实现 SHA。
- 关联：[Issue #52](https://github.com/wxwy/psm_wma/issues/52)、[Draft PR #53](https://github.com/wxwy/psm_wma/pull/53)。
- 本文及同提交证据是独立审核记录，不是新实现、V3 合并或真实 VAE/GPU 验收。

## 结论及推进范围

已独立确认逐 View 缓存的核心结构符合 Owner 最后决定：**所有有效 View 编码；每个 episode 内每个逻辑 View 一个数值文件；引用复用；只读 selected View；保留完整单帧空间 latent。**

同版本独立 CPU 复跑 **224/224 PASS，0 failures / errors / skips，9.831 秒**；Ruff 选定规则和13个新 Python 文件格式通过。原作者绑定的21份文件 SHA256全部一致；本轮39份作用域源码在最终执行前后未改变。

本轮提出的两个 P2 发现均位于编码入口边界，不推翻已核实的存储/索引结构。需要在现有 PR 上最小修正并提交新实现 SHA 后做窄增量复审；当前固定实现暂不获得最终 CODE 批准。无需重构 G1、扩大存储后端或引入新调度系统。

## F1 / P2：外部 Cosmos 父包导致混合 checkout 导入仍被接受

### 精确位置

- `g2/latent_cache/encoding.py:317-331`：只验证五个受控叶子模块的预加载状态。
- `g2/latent_cache/encoding.py:346-386`：finder强制加载选定叶子，临时插入sys.path，但没有检查已导入父包和非受控Cosmos依赖的来源。

[固定源码](https://github.com/wxwy/psm_wma/blob/aa0450b8e36b2cb833beda96256a29c3db95db23/g2/latent_cache/encoding.py#L317-L386)

### 触发和实际证据

同一进程先从另一个 checkout 导入 `cosmos_framework` 父包，尚未导入五个受控叶子；随后指定新的 `cosmos_root`。Python保留旧父包的`__path__`，后加sys.path不能更改它。受控finder能从选定目录载入叶子，其非受控helper却沿旧父包路径载入。

独立探针使用**固定实现的真实导入函数及未经修改的五文件清单**，仅将临时Cosmos包内容替换为轻量合成模块；调用descriptor后再导入受控vision_encoder。没有实例化Wan或加载真实模型。

观察结果：

```json
{
  "rejected": false,
  "bound_leaf": ".../selected/cosmos_framework/model/generator/vision_encoder.py",
  "parent_package": ".../old/cosmos_framework/__init__.py",
  "helper_file": ".../old/cosmos_framework/utils/helper.py",
  "helper_source": "OLD_CHECKOUT",
  "accepted_source_binding": true
}
```

真实Wan还会导入未列入五文件清单的`utils.generator.image_resize`等辅助模块。因此当前检查不足以支持“依赖只来自指定Child”的来源约束。这是受控导入边界复现，**不是已经观察到真实Wan latent受污染**；完全干净进程的默认CLI不受该前提影响。

### 最小整改及关闭条件

沿用现有拒绝策略：在受控导入前验证已载入的`cosmos_framework`父包/子包/模块实际来源；其他checkout或无法确定来源时明确拒绝，不热重载、不混用。检查包的搜索路径，不能只检查五个叶子的`__file__`。

新增异目录父包和未绑定helper的负例，保留干净进程及同实例重复Encode1用例。此项不要求支持未来在线集成或新增动态导入平台。

## F2 / P2：plan接受固定Wan无法支持的画布

### 精确位置

- `tools/g2/build_spatial_view_vae_cache.py:113-114`：只检查正数和16倍数。
- `g2/latent_cache/encoding.py:39-48`：有效构造映射只提供256、480、720。
- `g2/latent_cache/encoding.py:493-500`：实际编码前仍只检查16倍数，随后载入模型。
- 固定Child `cosmos_framework/utils/generator/image_resize.py:24-38` 将1024×1024分类为768。
- 固定Child `wan2pt2_vae_4x16x16.py:1014-1016` 在T=1处理前直接索引`self.temporal_window[resolution]`。

[入口](https://github.com/wxwy/psm_wma/blob/aa0450b8e36b2cb833beda96256a29c3db95db23/tools/g2/build_spatial_view_vae_cache.py#L109-L118)；
[原生分辨率分类](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/utils/generator/image_resize.py#L24-L38)；
[原生编码索引](https://github.com/wxwy/cosmos-framework/blob/d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2/cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py#L1014-L1016)。

### 触发和实际证据

用CPU合成episode、只作身份计算的占位权重文件调用真实build CLI：

```text
--device cpu --dry-run --height 1024 --width 1024
```

实际返回0，输出含1024×1024有效plan，且没有创建cache。独立执行固定Child的实际resolution函数，得到768；该键不在固定constructor中。

```json
{
  "native_resolution_tier": "768",
  "constructor_tiers": ["256", "480", "720"],
  "cli_exit": 0,
  "plan_returned": true,
  "cache_created": false
}
```

在成功加载真实模型的前提下，随后沿固定Wan源码必然在该索引处得到`KeyError("768")`；这一最终异常是**源码路径推导**，本轮没有执行真实Wan来制造它。默认256×256不受影响。

### 最小整改及关闭条件

plan和encode共享与固定Wan一致的尺寸支持性预检，在加载VAE前明确拒绝当前constructor未支持的分辨率档位。不要自动改变用户画布，也无需在本次增加768档支持。

回归覆盖默认256、一个已有支持档、1024×1024及超过原生分类范围的尺寸；拒绝不依赖GPU/模型加载。保持plan不import Torch/Wan的既有要求，可用轻量纯函数和与固定Child分类的CPU对照证明一致。

## 已通过的结构与实现审查

| 范围 | 本轮结论 |
|---|---|
| 模块职责 | 薄CLI位于tools/g2；contract/source/encoding/storage/builder为可复用g2库。source独立拆分合理。 |
| 覆盖与身份 | 全状态view并集；完整相对view路径；多房间/多Island不合并；source ordinal、logical ID/frame、owner、record独立。 |
| 时间复用 | 用现有resolver解析owner；全引用无目录合法；absent返回缺席，不回用旧图，不重新决定运动阈值。 |
| 空间latent | 独立B=1/T=1、完整CHW；FP32归一化、BF16计算和FP32输出分别记录；无Visual96池化。 |
| 按需读取 | 只打开选中view；mmap＋有上限LRU；只clone选中记录；返回metadata深复制；不在训练每次read扫描全源。 |
| 写入与恢复 | 私有临时文件、校验、fsync、原子拒绝覆盖发布、持久inode文件锁；完整view恢复；recipe/source冲突拒绝。 |
| 原产物共存 | 既有v2/v3打包器/validator回归通过；原PNG/SG/manifest/COMPLETE不变。 |
| 验证边界 | 普通reader/plan不载入Wan；B>1明确拒绝；没有把fake encoder结果称为真实VAE数值通过。 |

## 独立运行和原始证据

证据目录：`docs/collab/chatgpt/evidence/2026-11-16_issue52_aa0450b8/`，与本文同提交。

### 环境和源码

独立工作目录：`/workspace/scratch/720989c43529/pr53_review/source`。通过GitHub读取固定Root及固定Child的作用域文件，逐文件Git blob SHA校验；没有使用活动服务器工作树。使用独立venv：

- Python3.12.14；
- Torch2.15.0+cpu；
- pytest9.2.0、NumPy2.5.5、Pillow13.0.0、Ruff0.17.5；
- CUDA_VISIBLE_DEVICES为空、PYTHONDONTWRITEBYTECODE=1。

本轮并非全仓/全G2测试；精确范围为作者交付的8个测试文件与两个独立反例。新模块及必要既有依赖均来自固定提交，未修改生产代码或候选测试。

### 主CPU Gate

```bash
cd /workspace/scratch/720989c43529/pr53_review/source
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$PWD/cosmos-framework:$PWD" \
../venv/bin/python -m pytest \
  g2/tests/test_view_vae_builder.py \
  g2/tests/test_view_vae_contract.py \
  g2/tests/test_view_vae_encoding.py \
  g2/tests/test_view_vae_source.py \
  g2/tests/test_view_vae_storage.py \
  g2/tests/test_scene_view_event_index.py \
  g2/tests/test_scene_view_index_package.py \
  g2/tests/test_scene_graph_compact_v3.py \
  --junitxml=../evidence/pytest.xml -q
```

结果：**224 passed，9.83s，exit0**。来源日志/JUnit：`pytest.log / pytest.xml`。

第一轮隔离快照漏取既有`atomic_6views_catalog.py`，得到222PASS＋2个ModuleNotFoundError；这是审核环境组装问题，非候选实现缺陷。按固定Git blob补齐该依赖后重跑上述完整Gate。首次原始结果保留于`pytest_bootstrap_missing_dependency.log/.xml`，没有计入最终224或隐藏为作者问题。

### 定向反例

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH="$PWD/cosmos-framework:$PWD" \
../venv/bin/python -m pytest ../evidence/test_review_edges.py \
  --junitxml=../evidence/review_edges.xml -q
```

结果：**两个“应拒绝”断言均失败，exit1**，分别对应F1/F2；这是新增反例的RED结果，和原224项PASS分开报告。保留测试源码、日志/JUnit和两份观察JSON。测试脚本按本轮临时目录布局读取相邻source目录；复现时将固定候选工作树置于source、脚本置于同级evidence即可。

静态：`ruff check --select E4,E7,E9,F,I` 对13个新Python文件PASS；`ruff format --check`同13文件PASS。日志见`ruff.log / format.log`。源码前后清单及作者21份SHA对照见`independent_gate.json / source_before.json / source_after.json`。

## 后续最小动作

1. Codex在现有PR53修正F1/F2，补对应回归，提交新的固定实现SHA；Child/Gitlink可保持不变。
2. 重跑编码入口聚焦测试与现有224项回归，给出新SHA和原始证据。两项关闭后即可窄增量复审，不重开已通过的存储方案。
3. 真实Wan权重/GPU数值、decode视觉、小物体/箭头保真、读取性能、生产recipe冻结及全量编码，均仍为后续独立验收；本报告没有执行或批准它们。
