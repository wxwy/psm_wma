# cx 实现任务 — V3 Formal30k 命名日志参数 Launcher

**来源：** DS_PRO→GPT 2026-10-12 魔数重构申请，Owner明确不希望手填 `--tee 3` 等数字。
**GPT设计审查：** `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_ranklog_named_launcher_design_decision_444c232b_e9b8a41.md`。
**本任务仅 Code Quality / Operator UX：非Formal30k恢复阻塞项**。
**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`；**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`。

## cx 执行范围

- **在 GitHub 主仓 V3** 的 `tools/v3/formal30k_ranklog_launcher.py` 新建不侵入 production 的独立 Python日志启动封装和 `tools/v3/test_formal30k_ranklog_launcher.py`。不要修改 Child、训练入口、Torch/DDP/FSDP、数据集、优化器、Checkpoint、config digest。
- 使用同一 venv 的 `from torch.distributed.elastic.multiprocessing.api import Std`，以命名 `--rank-log-mode tee --rank-log-streams all` 来表达 `--tee Std.ALL`，并支持 `files` 模式对应 `--redirects Std.ALL`。Formal30k两路流 **all** 固定强制；不允许 none、只stdout或只stderr模式作为正式任务选项。不要将 `0,1,2,3,4,5,6,7` 误当 streams CLI值。
- 用列表拼装最终 torchrun argv，保持 `--max-restarts=0`、8 Rank、原 Job Resume、当前 Root/Child/Index/数据/模型/Digest参数，`PYTHONPATH` 指向 V3 Child而非父仓 editable package，Dense0/0、raw prefetch0。没有 `--launch` 时只执行只读 `--dry-run` + 命令验证。
- 日志必须同时保存8 Rank stdout/stderr且tee回显；独立、拒绝覆盖的 `--log-dir` attempt路径，使用PyTorch真实目录树，不假定直接的 `rankN.log`。
- **不要部署到训练服务器的冻结Root**；提交后提供单独精确SHA和可安全侧载于Root之外的方案，须待新的实现Gate审核通过才启用，不许DS/cx替Owner启动GPU训练。
- 覆盖CPU unit tests：命名映射、非法值、torchrun positional、单一日志选项、不自动重启、不覆盖、参数锁定/路径身份、日志路径、dry-run无副作用及失败时保留日志；必要时仅mock spawn。请勿实际 torchrun GPU。
- 交付：提交到 V3 的**代码 implementation commit SHA**、源码diff、CPU验收报告、建议部署位置/哈希、对历史手动 `--tee 3` 当前可用的保留说明。新Gate必须 fresh review；旧Formal Pair不因新Tool自动变更。

## 暂不做

不采纳方案B（训练内部Rank日志重构），不做生产管道/TelemetryJournal改造，不改变原 Formal30k的Resume授权和20GiB显存策略，不自动部署、不触碰Original DCP/Shadow/训练服务器工作树，不修改cx或DS其它任务。

**如实现需修改上述 Scope，停止并先返 GPT 重新评审设计。**