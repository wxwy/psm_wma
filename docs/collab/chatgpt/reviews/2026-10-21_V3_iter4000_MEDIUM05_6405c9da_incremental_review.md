# PSM-WMA V3 — iter4000 四任务 Queue MEDIUM-05 新 Pair 独立增量复审

日期：2026-10-21
Scope：Queue **CPU synthetic / static remediation review only**；不含真实 Action Server、RoboCasa Simulator、GPU、DCP、训练或真实 SR 结果。

## Formal target

- Root implementation SHA：`6405c9dae02e81be5f267e79e27995c3df7fb988`
- Child/Gitlink SHA：`2d128ed5a07601cdd424974f99b67832eafeeb41`（未改变）
- Implementation parent：`a5d743d1c2221dd4db21dfa61db814da51b286ed`
- 本轮 Queue blob：`e56eaafe8276aa40cb9e2fbc1110515e8fa19c25`
- 比对上一审核 implementation：`ca936c8eecd593133b1e6c61ba5691331958c592`；仅 root queue 的 Worker 入口及定向测试变化，SESSION/TODO 为事实记录。最新远端文档 HEAD `8a7fcae8f33a49339b7765cd53bdda31a3524986` 不能替代 implementation SHA。
- 上轮同 Gate review：`docs/collab/chatgpt/reviews/2026-10-21_V3_iter4000_HIGH02_ca936c8e_incremental_review.md`。

## Verdict

**`APPROVE` — 仅关闭当前 V3 iter4000 Queue MEDIUM-05 / HIGH-02 CPU 静态整改审核范围。**

MEDIUM-05 **CLOSED**；本轮没有新的 production blocker。HIGH-02 已在上一 Pair 被独立确认 CLOSED 且本次相关 helpers/原 Worker 体未改；HIGH-01 已撤销为 FALSE POSITIVE，不应再次整改。

**本 verdict 不授权 DS_PRO 启动 GPU/真实 Action Server/仿真，不等于 RoboCasa SR、DCP/实模型兼容性、E1 全链路 watchdog 或其他项目 Gate 的批准。** 后续真实执行须完成目标机独立 CPU/只读检查和 Owner 的单独 GPU release。

## Incremental implementation review

1. `scripts/eval_robocasa_18task_queue.py:341-518`：旧 `worker` 重命名为 `run_worker`，原函数体不变；外层线程入口 `worker` 位于 518 起、用 `try: run_worker(...)` 捕获早期 `worker_dir.mkdir` 与日志 `open` 的 `BaseException`。故障时设置 `stop`，在持锁状态写入 `results["_worker_<id>"]`，**退出 result_lock 后**调用 `publish()`。
2. `publish()` 原有 `worker_errors` 汇总将总 `status` 置 `INCOMPLETE`，完整 `sr=None`；主线程 `join` 后核验 `worker_errors` 非空返回1。即使4 Task ×5 episodes 已由另一 Worker 完成，也不会隐去失败。
3. 复核实际 root diff：生产代码仅函数改名 + 16 行外层 guard；Child/Gitlink、`scripts/v3_evaluation_identity.py`、HIGH-02 端口及 `/info` 校验 helpers、server/simulator 命令、原锁作用域不变。提交的 `scope_proof.json` 与实际 diff 一致。

## Direct behavioral Evidence review

依据作者提交的 `docs/collab/codex/evidence/2026-10-21_V3_iter4000_MEDIUM05_author_cpu/`：审阅 `gate.json`、`pytest.xml`、`pytest.log`、`baseline.log`、`regression_witnesses.json`、`scope_proof.json`、`manifest.json`，并对照新 `tools/v3/eval_robocasa_queue_identity_test.py` 实际用例。

- `mkdir_failure` 与 `log_open_failure` 两种 fault injection 均**等健康 Worker 完成全部四任务 20 条合成 episode** 后触发。旧代码 Red witness：`total_trials=20`、`worker_errors={}`、`status=COMPLETE`、`sr=0.6`、`rc=0`、存在未捕获线程错误；新代码 Green witness：`total_trials=20`、对应 `_worker_1` 报错、`status=INCOMPLETE`、`sr=null`、`rc=1`、`unhandled_thread_errors=[]`、`thread_names=[]`，健康 Worker 服务进程已终止。单测直接运行队列入口而非 helper-only。
- 作者终态记录：`30 passed, 55 deselected, 41 subtests passed in 30.77s`；JUnit 为 71 个 bookkeeping testcase（其中 41 subtests），不能误记为71独立测试方法。Ruff check/format、syntax、diff-check 为 exit 0。
- 作者测试在合成 stdlib HTTP、临时 Git、伪 metadata、伪 results/video 上运行，不包含真实 RoboCasa model/DCP、可解码 MP4 或真实 SR。
- **独立性边界**：GPT 已独立检查 GitHub 实现、测试及保留日志与行为契约，但未在训练服务器重新运行 CPU 测试；作者 CPU pass 不是 DS_PRO 现场独立 pass。

## Gate closure / subsequent permission boundary

- **MEDIUM-05 CLOSED**，没有新的 blocker；不再要求 Codex 修改此 Pair。
- DS_PRO 可遵循作者 handoff 中的最小 **CPU-only + 只读**新 Root 指令（把旧 runbook 的 Root 断言更新为 `6405c9da...`），核验目标服务器 `/proc/<pid>/fd` listener 归属、实际四个 `dataset_meta.json` 的 exact name set、iter4000 DCP 小文件、Config 推导的 H16/raw15/state/max-action64、空闲 GPU/端口和存储；缺项应 BLOCKED，不靠放宽生产断言绕过。
- `--resume` 仅完整 task 级别；partial episode 不可无损续接，需隔离新 namespace。1/2/4 GPU 对应当前 queue 的 1/2/4 Worker/Action Server/串行仿真 Session Slot，不是训练 B8 Slot。
- GPU、真实 Action Server / Simulator 与20条 RoboCasa episode **仍 BLOCKED，需后续单独授权**；该审核不关闭 E1 watchdog、G1训练或 Persistent Memory 项目 Gate。

审核来源：远端 GitHub V3 实际 pair/diff/相关源码与作者留存 Evidence；未触碰真实训练服务器或 GPU。
