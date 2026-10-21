# PSM-WMA V3 — iter4000 HIGH-02 新 Pair 独立增量审核

日期：2026-10-21
Gate：iter4000 四任务×5 Episode Queue — HIGH-02 Server Identity CPU Static Remediation
Scope：root queue 实现 + 定向 CPU Evidence，不授权真实 Action Server / Simulator / GPU / 训练

## Formal pair 与依据

- Formal Implementation Root：`ca936c8eecd593133b1e6c61ba5691331958c592`
- Child/Gitlink：`2d128ed5a07601cdd424974f99b67832eafeeb41`（未变）
- Base：`c62fad0ef6c729570ee936522ea4269021164c56`
- 新 Queue blob：`eec2702d5382358e131928db60ce75c93c0c55d5`
- 前一 review：`docs/collab/chatgpt/reviews/2026-10-21_V3_iter4000_4task_multiGPU_queue_launch_review.md`，含 HIGH-01 撤销勘误。
- 作者材料：`docs/collab/codex/reviews/2026-10-21_V3_iter4000_server_identity_HIGH02_author_handoff.md`；CPU evidence `docs/collab/codex/evidence/2026-10-21_V3_iter4000_HIGH02_author_cpu/`。
- 本人通过 GitHub Connector 读取实际 Implementation diff、root Queue、Child Action Server `get_info()/serve()` 与 OnlineLocalMemory `info()`、新测试源码、JUnit/日志、Gate/manifest、witness 与 DS 只读交接指令；**未在训练服务器运行 CPU/GPU 测试**，作者 CPU log 不当作第三方独立执行。

## Verdict

**`REQUEST_CHANGES`**。

已确认原 HIGH-02 的端口占用、`/info` checkpoint/config/协议、Linux `/proc` listener ownership 核验路径已实现，正常和多种异常的合成 CPU witness 可对应到实际 queue `main()`。但本次引入的“worker error preservation 必须 fail-closed”行为还有一个未覆盖的实际生产漏报路径。

## Blocker（new finding）

### MEDIUM-05 — Worker 进入异常捕获前的初始化错误可被忽略，假报 COMPLETE

- **File:line**：`scripts/eval_robocasa_18task_queue.py:341-375,499-508,518-539`。
- **Root cause**：`worker_dir.mkdir(...)` (344) 与 `server_log_path.open("ab")` (375) 在 `try/except BaseException` (377/499) **之外**。这些调用抛 `OSError` 时，`threading.Thread` 仅记录未处理线程异常，既不会写入 `results["_worker_<id>"]`，也不会触发 `stop`。`thread.join()` (525) 不会将子线程异常重新抛到主线程。
- **Violates frozen contract**：本 Gate 明确要求 Worker 启动/身份失败无论是否已有 20 条结果都必须保留 `worker_errors`、将总 `status` 设 `INCOMPLETE`、总 `sr=None`、并返回非零。若 Worker 0 早期目录/日志初始化失败，而 Worker 1 完成共享 Queue 的全部4个任务×5条结果，则 `missing=[]`、`failed=[]`、`worker_errors=[]`，`screening_metrics` 报 `COMPLETE`、main 返回0；这不符合“任何 Worker 失败不可宣告完整成功”的 Gate 行为。
- **Acceptance**：最小 root queue 修复，使 Worker 全部预启动 I/O 与服务运行异常都落入异常汇总（无需改任务协议或 lock）；保证 `publish()` 最终报告及退出码 fail-closed。新增 CPU 端到端负例：注入其中一 Worker 的 `mkdir` 或 `action_server.log` 打开失败，另一 Worker 能消费全部4Task×5条模拟结果，仍必须 `worker_errors` 非空、`status=INCOMPLETE`、`sr=None`、`RC!=0`，无残留线程、只清理属于本次的进程。测试必须证明真实队列入口行为，不是 helper-only。
- **Status**：OPEN；仅本轮新 finding。禁止变更 Child、DCP、trainer、Local-TTT、动作 ABI、已经证明正确的 HIGH-01 锁作用域。

## Closed findings / Evidence

- **HIGH-01**：先前已被勘误撤销（FALSE POSITIVE），本轮锁及 `publish()` 锁外关系未改，不得作为 blocker。
- **HIGH-02 (primary)**：现版 `require_free_ports()`（70-80）、`validate_server_info()`（83-112）、`require_owned_listener()`（115-141）、`wait_server()`（144-173）与 `worker()` 内配套调用（378-401）完成最小修复，原主要缺陷 **CLOSED**。Child `ThreadingHTTPServer` 仍在 Popen 主进程运行，`/info` 源码包含所检字段；实际目标 GPU 机器 `/proc` 同用户可读及真实模型最终 resolved H16/max_action_dim64 尚未测，必须单独 preflight，不得绕过 fail-closed。
- **作者 Evidence 核实**：`pytest.xml` 28 testcases、0 failure/error/skip，`pytest.log` 末行 28 passed / 55 deselected / 41 subtests passed，且 witness 含1/2/4 Worker 的20 synthetic episodes、旧监听服务、错误 checkpoint/config/mode、config 变化、worker 在 try 内失败、server 退出等。日志为作者执行，不是独立在本机重跑。synthetic rollout MP4 为占位文件，不证明真实仿真成功率。
- **MEDIUM-03/04**：保持后续 DS 独立只读 exact 4-task metadata 验证与 whole-task-only `--resume` 原样本边界。现有 DS 指令清楚区分真实路径前置与未来未执行 GPU 命令。

## 狭窄整改和 Gate 限制

Codex 仅补 `MEDIUM-05` 生产异常入口和定向 CPU 负例；已有 HIGH-02 逻辑和 Child 不动。提交新 Root implementation SHA + 原 Child/Gitlink、diff、CPU Evidence 后触发新 Pair fresh incremental review。DS_PRO 继续只读准备/独立 CPU；**当前不授权启动 GPU、真实 Server/Simulator 或进行 iter4000 的20条 Rollout**。本 verdict 仅针对该 CPU static Gate，不重开已关闭训练 Gate。
