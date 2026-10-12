# DS_PRO → GPT — torchrun --tee/--redirects 魔数重构申请（Owner转交）

**日期:** 2026-10-12
**当前冻结 Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**任务阶段:** Formal30k Dense OFF/OFF 同模式正式 Resume；该代码质量请求不阻塞已经获得授权的 Owner 手动命令。

Owner/DS 的实际问题：
- 错误的 `--tee 0,1,2,3,4,5,6,7` 报 `ValueError: ... does not match ...`。
- 正确临时命令是 `--tee 3`，对所有本地 Rank 都同时持久化 stdout/stderr 并回显终端。
- PyTorch `Std` 对应 `NONE=0, OUT=1, ERR=2, ALL=3`；torchrun CLI 接受单值 0..3 或 `local_rank:std` 映射，不接受纯 Rank 逗号列表。
- Owner 要求避免让操作者记忆魔数。DS 申请 GPT 设计/审核、cx 实现，DS 只取证/运行验证。

候选：
A. 独立命名 CLI Launcher 负责 PyTorch Std 映射（DS 推荐）。
B. 改训练脚本收集逐 Rank stdout/stderr。
C. shell 包装脚本隐藏固定 `--tee 3`。

**独立来源核验：** PyTorch [torchrun 官方日志文档](https://docs.pytorch.org/docs/main/elastic/run.html)明确 `--tee` 已包含写文件和回显，`--redirects` 只写文件；PyTorch [Elastic multiprocessing](https://docs.pytorch.org/docs/stable/elastic/multiprocessing.html) 的 `Std.ALL` 和 `DefaultLogsSpecs` 明确写日志目录及Rank路径。原报告不等于生产代码变更。GPT 设计裁决 `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_ranklog_named_launcher_design_decision_444c232b_e9b8a41.md`。