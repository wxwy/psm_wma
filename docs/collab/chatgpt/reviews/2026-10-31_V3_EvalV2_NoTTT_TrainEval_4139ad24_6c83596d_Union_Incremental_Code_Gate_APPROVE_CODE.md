# PSM-WMA V3 — EvalV2 Dual-mode + No-TTT Async Lazy 训练线统一组合增量 Code Gate

**审核日期：2026-10-31。正式 Verdict：`APPROVE_CODE`（仅新组合 Formal Pair、Git 源码并集、当前作者轻量 CPU 84用例 Evidence）。**

- **正式审查 Formal Root：`4139ad245b73cc1c16c9d4954241cecb81478992`；Child/Gitlink：`6c83596d6a259e89c4cd3e79424024983426ac3d`**。这两个 SHA 与下一轮 Evidence/Receipt 文档提交**不同**。
- Canonical 基线：Root `369f3f4d82b8694b7efee5d5b16589d82aa00547` / Child `baf1b5bf46853e9849a91518803b9738fc216235`（No-TTT 已完成生产 Git 合入，未恢复正式训练）。
- 已审 EvalV2 来源：Root `d18b420c02cfc51a1b85e9f1d6ce5d26f7bd3163` / Child `2f7334c4ada6ace1d21185985aae90539052bf18`，曾 `APPROVE_CODE`；已审 NoTTT 来源：Root `57e36decbec0e00ecb94dc1c080fd8976afff25d` / Child `baf1b5bf46853e9849a91518803b9738fc216235`，已 `APPROVE_CODE`；本Gate**不重审以上源Pair**。
- Owner当前决定**统一训练、仿真和评测代码均在V3长期维护/在本会话统一组织审核与下一步计划**，并询问是否将能同时保留二者的Child `6c83596d`合入V3。旧Eval-only Child精确`2f7334c4`与现有训练Child`baf1b5bf`不可同时作为一个Gitlink，必须以新并集Child替代原2f的旧pin。本Verdict**认可新Child 6c作为目标**，但审核不等于执行代码合并或任何GPU。

## 1. 直接GitHub证明：不存在训练/仿真源代码覆盖

| 核对对象 | 独立真实对象/差分 | 结论 |
| --- | --- | --- |
| Canonical 当前Root/Child | 直接读取V3 HEAD、Root Git Tree mode160000，确认为 `369f3f4d`→`baf1b5bf` | 旧 NoTTT 已合并；不能复位 Gitlink 2f |
| 合并Child拓扑 | GitHub `git/commits/6c83596d`：**两个真实parents**分别为`baf1b5bf`、`2f7334c4` | 是真双历史merge，而非重写任一来源 |
| Child自训练parent到union | GitHub compare `baf... → 6c...`：ahead3 / behind0，**只涉及13个EvalV2 files**；无训练目录变更。直接检查6个训练核心生产Git Blob（Loader/Recipe/LazySource/Trainer/Profile/CachedSFT）与baf逐项相同 | 训练路径完整保留 |
| Child自Eval parent到union | GitHub compare `2f... → 6c...`：ahead2 / behind0，**只涉及13个NoTTT training/test files**；无EvalV2目录变更。直接检查Eval的contract/session/server三个核心生产Git Blob与2f一致 | EvalV2双模式源码完整保留 |
| Root新合并 | GitHub `git/commits/4139ad24`两个parents，沿袭当前Root和已批Eval Root；compare `369f → 4139` ahead5、behind0；Git Tree Gitlink为`6c...`。直接检查已批Root Eval队列/config/identity/runtime **4/4 Blob**与d18一致，现有NoTTT Console及两Launcher+对应测试 **4/4 Blob**与369一致 | Root训练/仿真入口均未改写 |
| 其它对象 | Root configs/third_party tree SHA与基线完全一致；新Child的 `model/checkpoint`不在13+13变更之内；作者object_audit记录Root 12407与Child1270 Tree objects并集无源码重叠/损失 | 本审核将作者全对象计数视为附加Evidence，不伪称GPT逐个枚举所有对象 |

**关键判定：** `2f7334c4` 是旧已批Eval-only Child，不再是合法的V3统一训练+Eval目标；`6c83596d6a259e89c4cd3e79424024983426ac3d` 是同时包含上述两个已审来源的唯一被测union Child。将V3直接重置/强推到2f会丢掉NoTTT已经提升的13条训练改动，违反Owner保存训练的目标。

## 2. Contract → Behavior → 原始Evidence

- 作者新Formal被测Root/Child：`4139ad245b73cc1c16c9d4954241cecb81478992` / `6c83596d6a259e89c4cd3e79424024983426ac3d`，源Evidence地址：`docs/collab/codex/evidence/2026-10-31_eval_v2_current_v3_composition/`，Evidence docs SHA为`6bfb05f8a916aad51e619c557231463ed6e3f1ce`，**不取代Implementation Pair**。
- GPT直接读取作者`raw/light-cpu/junit.xml`并逐Test Case按classname+name检查：**84不同用例，84 PASS/0failure/0error/0skip**。原始执行命令 `pytest ... -k 'not real_OS'`，真实 OS 集成有**1个planned deselected**，没有计入84；不能称未运行OS测试PASS或skip。
- 84 case来自 Eval config17、entry15、Root dual-mode11、Child dual-mode35、NoTTT integrated-entry6；包含off|required/Manifest/Resume CPU模拟、Server/Session/Batch/timeout/End流程、Local CPU fast、NoTTT shell→Progress console→Profile/Trainer/AsyncLoader绑定。**这里的CPU tiny DCP和fake torchrun不等于真实训练/真DCP/真实OSMesa仿真**。
- 直接读取`raw/static-and-entries/checks.json`，作者Ruff check24files、format23+Queue changed-range、compile24、bash-n3、source diff check、真实source import-origin、`run_robocasa_eval_v2.sh --help` off|required 模式CLI均exit0。作者曾有两次**外部静态脚本scope计数问题，均在项目测试执行前停止**，其错误记录保留；修的是external checker，不是正式源码，不视为被掩盖的生产失败。
- GPT独立实现SHA-256校验`artifact_sha256.json`与6份原始关键文件：`object_audit.json`、`summary.json`、`raw/light-cpu/junit.xml`、`raw/light-cpu/execution.json`、`raw/static-and-entries/checks.json`、`README.md`，**6/6字节摘要一致**。原执行 `source_before`正式pair身份、clean、`source_after`及`source_unchanged=true`已从原始执行记录核对；没有在GPT容器内直接跑这84条、真实GPU、DCP或仿真。
- 作者提供`object_audit.json`，Root与Child各自目标path的并集无交集，冲突只出现在 `SESSION/TODO/CODEX_INBOX` 等交接文档；报告保留Canonical原字节前缀并追加记录。此次代码Gate未发现新的Source/Contract/Evidence blocker。

## 3. Verdict、执行权限与统一V3下一步

**`APPROVE_CODE`** — 本Formal Root `4139ad24` / Child `6c83596d` 的Train+Eval源并集、受保护对象保全及轻量84项 CPU组合测试；无已确认阻断项。**授权目标选择：Owner明确希望统一V3维护，Code Gate认可使用6c安全提升；Codex应按最新V3远端状态无force快进/必要安全合并，先Child正式`v3-local-ttt`、再Root V3，并核 exact Gitlink、源码对象和文档历史。** 旧指定Child2f不允许覆盖baf。

**本Approval不自动授权：**重新跑CPU84/旧324/435/301、执行真实GPU/模型/数据/正式NoTTT DCP Resume、18 task/900真实评测、LocalTTT多集Canary、修改原C12200 Checkpoint或覆盖A/B实验DCP。下一步真实实验仍由Owner明确授权，DS仅执行实机测试，Codex维护源码。

**合并后统一工作机制（不新增工具链）：** 一本V3当前Root+Gitlink作为训练/仿真/测试公共源码状态；本会话负责每次新FormalPair的**增量**代码/Evidence Gate和下一步计划，Code/Review记录仍在`docs/collab/chatgpt/reviews/`与append-only `CODEX_INBOX.md`。训练与Eval分开冻结运行合同/Checkpoint/数据/结果，不能相互污染。旧Formal Pair未改时不重复审核。优先执行：① Codex完成这次基于6c的V3代码提升并回验；② 经Owner单独授权，DS恢复原正式NoTTT C12200（world4、nw8/prefetch1/persistent1/timeout120，原完整DCP、不用A/B C12220）；③ EvalV2在已批准的OSMesa recipe下先NoTTT 18 underlying task ×1 fixed seed screening，失败诊断后再考虑规模900；LocalTTT先自己的Canary，另行审核。共享GPU排程互斥，不为本次组合再做无关全回归。

**Review本身只是 docs-only Canonical提交，不能误认为union生产Gitlink已提升。**