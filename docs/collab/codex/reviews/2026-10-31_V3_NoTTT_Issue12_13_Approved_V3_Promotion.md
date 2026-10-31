# No-TTT Issue12+13 — 已批组合的 V3 代码提升记录

本次按 Owner 最新指令执行第一步：安全合入 V3。正式训练恢复属于第二步，
需要 Owner 另行授权；本次没有运行训练、GPU、真实数据、模型或 DCP。

## 精确来源

- 已批 Formal Root：`57e36decbec0e00ecb94dc1c080fd8976afff25d`。
- 已批且保持不变的 Child/Gitlink：`baf1b5bf46853e9849a91518803b9738fc216235`。
- 已发布组合候选 HEAD：`cf1065bab335b7f268a183f302bf8b953e3e5e94`。
- 本次实际获取的最新 V3：`692b7ed467b04b016d609a17d91a8631c867710e`。
- GPT 正式 `APPROVE_CODE`：
  `docs/collab/chatgpt/reviews/2026-10-31_V3_NoTTT_Issue12_13_Integrated_57e36dec_baf1b5bf_Composition_Incremental_Code_Gate_APPROVE_CODE.md`。
  Review Blob：`d23c345da4ccd77de20589ee2ea2e8cf1ad2003a`。

实际读取完整 Review，核对完整 Pair 和 canonical Inbox 同步记录后，建立独立
promotion 工作树。保留最新 V3 和已批候选的提交历史，以合并提交承载原样代码，
不 reset、不 force、不整树覆盖。包含本记录的合并提交是生产提升提交；后续
回执可以是 docs-only 后继，不替代上面的获批 Formal Pair。

## 合并与对象验证

- 生产行为相对最新 V3 仅两份 No-TTT launcher、一份 console helper，以及
  指向已批 Child 的 Gitlink。原始 torchrun argv/defaults、算法、模型、损失、
  Optimizer、DCP/RNG 和配置实现均未进一步修改。
- 按排除 docs/SESSION/TODO 的完整 Root 对象集验证，**9,848 个源码对象**
  （包含文件 mode/type/blob）全部等于获批 Formal Root。测试代码也原样保留。
- 整个 Child 是原已批 baf commit，没有新 Child 实现或分支覆盖；受保护的
  evaluation/inference/simulation/model/checkpoint/configs 子树与 canonical
  原 Child 一致。Root configs、vendor 及其它实现保持获批版本。
- 唯一冲突为 SESSION/TODO/Inbox。canonical Inbox 原字节前缀保留，再追加
  候选独有尾部一次；两边 SESSION 新增块与共同历史均保留；TODO 保留任务并
  记录本轮状态。容量低于131072字节，无 rollover、无历史 Evidence 删除。
- 最新 V3 的1f79组合审核、563e/692b的另一项 EvalV2 OSMesa 审核与交接均保留。
  不把另一个 Canary 的 Evidence REQUEST_CHANGES 关闭或改写为已通过。

原始机器可读记录：
`docs/collab/codex/receipts/2026-10-31_nottt_issue12_13_v3_promotion/`。
包括实际远端观察、交接文件合并块 SHA、Git-only 源码审计及其脚本。

## 验证边界与运行边界

本次只读取 Git 对象和冻结 Evidence：45份原工件 SHA256、15个源绑定匹配，
原始 JUnit 仍是6项通过、0失败/错误/跳过。**没有重新执行 pytest、Ruff、
历史49/43/58/301套件或1.61× GPU A/B**；这些结果与审批仍绑定原始来源。
没有将读取原 JUnit 表述为一次新的 CPU 或 GPU 实验。

world4/GA4 路线具备已批 nw8 Async Loader；world4/nw0 和 world8/nw0 同步入口
保持原样，默认 progress-only 日志包装在两份入口生效。不新增 world8 多 Worker
能力，不改变默认 Worker 数或当前正式 Job 参数。

生产提升成功以 GitHub advertised V3 SHA、fetch 后的 Root/Child Gitlink 和
已批源码对象回验为准；若远端并发前进，重新安全同步，普通非强推不得覆盖。
最终精确提升 SHA、V3 HEAD 和回验结果另记 publication receipt。

完成代码提升后停止。未访问或修改任何原始 C12200 Checkpoint、冻结配置、
Job Identity、数据或历史运行；没有启动 Action Server、RoboCasa、训练或 DS
任务。后续正式训练只能经 Owner 单独授权，从**原正式完整 iter12200**恢复，
使用已验证的 nw8/prefetch1/persistent1/timeout120；不使用 A/B 生成的 iter12220。

## 并发同步补记

提交本地提升合并 e65f1b2010557f2d982a6c2d22fa162382d28077 后，
推送前发现远端新增7fb45b78、2ee690b0两笔文档提交。重新同步到
`2ee690b0c3b0a6d9219db12096813ef4eb26de2b`，完整保留 Owner 采信 DS
OSMesa Canary 报告的最新决策及原先历史，不把过期的取证要求恢复为阻断项。
本任务没有重开或改变该 Canary 裁决，正式训练授权仍单独保留。

只有 Inbox 追加位置冲突：先完整保留最新 canonical 前缀，再追加此前候选及
本轮提升的独有记录。重新核对源码对象，仍与已批57e3完全一致。Child正式
分支原746c5cf2是baf1b5bf的祖先，可非强推快进；Child先、Root后提升。
