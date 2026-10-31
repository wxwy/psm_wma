# Issue13 日志分界：已批最小修改的 V3 提升

Owner 已批准从隔离代码目录安全提升。本次只合并代码和核对 Git/冻结原件，
不更新正在运行 No-TTT Resume 的共享代码目录，不暂停或重启训练。
代码仅供后续启动使用。

| 身份 | 完整 SHA |
| --- | --- |
| 已批 Formal Root | `3cf7453777a693ac029a79ed8b19afc55df0d4fa` |
| 未变 Child/Gitlink | `6c83596d6a259e89c4cd3e79424024983426ac3d` |
| 最新 V3 起点 | `ec9d7b26391821d0eed34977e8d45ae90b346ba3` |
| 已发布候选 HEAD | `22ca7cc387dc41e001408026d42fe1fea799f922` |

已实际读取精确 Pair 的正式 `APPROVE_CODE` 及 canonical Inbox：
`docs/collab/chatgpt/reviews/2026-10-31_V3_NoTTT_Issue13_StartingTrainingBoundary_3cf74537_6c83596d_Incremental_Code_Gate_APPROVE_CODE.md`。
Review Blob：`4b35c2980bb4c0044557f9647731dd3f72c03795`。
此文为执行者提升记录，不是新的 Code Gate 或运行授权。

## 隔离合并与保全

在云端新建独立 `v3-nottt-boundary-promotion-20261031` 工作树，从最新 V3 合并
已发布候选历史。未访问训练服务器或对其它工作树文件作任何写入。仅
SESSION/TODO/Inbox 追加位置产生冲突，双方独有记录和共同历史均保留；
canonical Inbox 字节前缀完整保留，再追加候选尾部一次，容量低于131072字节。
不 reset、不 clean、不 force，不改写历史审核或 Evidence。

Git-only 审计确认：

- 唯一生产差异为 `scripts/no_ttt_console.py`，完整 mode/type/blob 等于已批
  Formal 版本。**9,851个 Root 源码对象全部等于已批3cf**，没有实施新修改。
- 两份训练启动器、整个 Child/Gitlink6c、Trainer/Loader/DCP/模型/EvalV2
  保持原样。正式 Child 分支无需移动，不创建新 Child 实现。
- canonical已有2,609个、候选已有2,657个文档对象（Inbox另按追加规则）原样
  保留。原43份工件 SHA256、8个源码绑定均匹配，原始 JUnit 46项零失败/错误/
  跳过仅作只读核对；**没有重新执行 pytest、静态工具、旧CPU或GPU实验**。

记录与审计脚本：
`docs/collab/codex/receipts/2026-10-31_nottt_console_boundary_v3_promotion/`。

## 发布与使用边界

普通非强推更新 V3 前再次检查远端祖先；如发生并发推进，先安全同步，绝不覆盖
其它工作。发布后以 GitHub advertised/fetched Root、Child 正式分支和 Gitlink
回验为准；实际提升 SHA 及回执随后补记，后续 docs-only HEAD 不替代获批 Pair。

后续启动默认完整显示初始化及 `Starting training...`，之后只显示 Rank0
Progress；完整 raw 与异常提示保留。若人为禁用 INFO 导致标志缺席，则仍完整
显示日志，这是已批准的非阻断行为；本次不加入 fallback 或改动训练日志级别。

所有工作限定在新云端工作树和 GitHub refs。没有改动、拉取或热更新正在训练
使用的共享工作树；没有访问或改变其进程、Checkpoint/DCP、配置、Job Identity、
输出目录或 `_launch_logs`，不发起 DS/GPU/训练/仿真。提升完成后停止。

## 并发文档同步

推送前保护检查发现远端从ec9d7b26前进到
`2667393e501a1ff7429bdff004e4806d45724e3f`，新增18×1评测准备审核和Inbox，
没有生产源码变化。先停止推送并合入该记录，只处理Inbox追加冲突：最新
canonical全文前缀加此前提升记录一次。保持该审核原文，不执行其中的仿真命令。
这次同步不改变日志实现、不触碰在训目录、不重复测试；源码再次按Git对象核对。
