# V3 统一训练与 EvalV2：已批并集代码提升

按 Owner 最新指令执行安全合并；V3 是后续唯一公共代码维护基线。
本轮不修改生产实现、不重复84项测试，不启动 GPU、训练或仿真。

| 身份 | 完整 SHA |
| --- | --- |
| GPT 已批 Formal Root | `4139ad245b73cc1c16c9d4954241cecb81478992` |
| 已批并集 Child/Gitlink | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| 最新 canonical 起点 | `b0c56553afcdd0cec99cdbae6bdef1043bb9c0bd` |
| 已发布候选及原 Evidence HEAD | `6bfb05f8a916aad51e619c557231463ed6e3f1ce` |
| 训练来源 Child | `baf1b5bf46853e9849a91518803b9738fc216235` |
| EvalV2 来源 Child | `2f7334c4ada6ace1d21185985aae90539052bf18` |

实际读取 canonical 正式 Review 并核对完整 Pair、live Inbox 和 advertised SHA：
`docs/collab/chatgpt/reviews/2026-10-31_V3_EvalV2_NoTTT_TrainEval_4139ad24_6c83596d_Union_Incremental_Code_Gate_APPROVE_CODE.md`。
Review Blob 为 `a71320cec17a48f5a5561012ac9a8da33825dc37`，正式 verdict
`APPROVE_CODE`。本记录是执行者的提升回执，不授予新的技术或运行批准。

## 无源码改写的合并

- Root 从最新 V3 创建独立 promotion 工作树，合并已发布候选，保留两路提交
  历史及既有审核/Evidence。只在 TODO、Inbox 追加位置发生冲突；SESSION 自动
  合并后也验证了新旧块保全。最新 canonical Inbox 保持完整字节前缀，再追加
  候选独有记录一次；未截断或覆盖原件，容量低于131072字节。
- 并集 Child 是真正双父提交，父分别为 baf（No-TTT）与2f（EvalV2）。从 baf
  到6c只增加13项 EvalV2 改动；从2f到6c只增加13项训练改动，两个集合无交集。
  **6c才是本次目标；不将 Gitlink 或 Child 正式分支回退到旧2f。**
- 按共同祖先和 mode/type/blob 逐对象计算，**1,270个 Child 对象**等于两侧
  原对象的完整并集；Root 源码也等于已批训练/Eval 来源的并集。待推送 Root
  的**9,850个非文档源码对象**全部等于获批 Formal4139，没有修改或混入其它
  代码。原 No-TTT Async Lazy Loader、Progress-only 和双模式 EvalV2 均保留。
- canonical已有2,479个文档对象、候选已有2,599个文档对象（Inbox另按追加规则）
  全部保留。详细记录和只读审计脚本在
  `docs/collab/codex/receipts/2026-10-31_train_eval_union_v3_promotion/`。

## 原 Evidence 仅核对，不重跑

完整校验原 `artifact_sha256.json` 的44份工件。原 JUnit 仍为84个不同用例，
0失败/错误/跳过；`real_OS` 的1项计划排除不算通过。没有执行 pytest、Ruff、
旧测试、真实 OS/GPU/模型/数据/DCP。原始作者 CPU Evidence 和 GPT 对其的批准
均保持原 SHA，不把一次 Git 读取声称为新的 CPU/GPU 实测。

原候选 README/summary 的“待Owner确认2f目标”属于当时历史，作为冻结工件
原样保留。本次 Owner 已明确选择6c，并由上述新组合 Code Gate 批准；该旧文字
不再是当前阻断项。没有重新审核两路先前通过的实现。

## 发布与后续维护

先将 Child 正式 `v3-local-ttt` 从 baf 非强推快进到6c，再普通非强推更新 Root
`V3`。推送前检查最新远端祖先，遇并发前进则先安全同步；发布成功后核对 GitHub
advertised/fetched Root、Child 正式分支和 Root Gitlink，并补记精确发布 SHA。
后续完成回执可以是 docs-only 后继，不替代获批实现 Pair。

此后公共源码以 V3 Root 加其精确 Gitlink 为准；训练与评测分别冻结运行合同、
数据/Checkpoint、资源安排、结果与 Gate，不混用运行目录或结论。历史 V2、
旧 Formal Pair、候选分支、审核及 Evidence 继续保留，后续不回退到 Eval-only2f。

本轮完成代码提升后停止。没有操作当前 Job、配置、Identity、原 C12200 或 A/B
Checkpoint，没有派发 DS、加载模型、启动 Server/OSMesa/Local-TTT 或训练。
正式 No-TTT 原 C12200/nw8 Resume、18×1 No-TTT screening 和 Local-TTT Canary
仍需 Owner 各自明确授权，并遵守各自独立的运行合同。
