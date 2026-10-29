# V3 EvalV2 Phase B B2 — Store.mkdir F3-P1 Production Remediation Narrow Code/Evidence Gate

日期：2026-10-29

**当前 Formal Pair：** Root `657061e6893bd61e685685089a1cf1f61e9eb1fe` / Child+Gitlink `0ae313e329d290fc6b8a50fda1112820fb7ac485`。Root 分支 `v3-eval-v2-store-mkdir-f3-20261029`。

**正式 verdict：`REQUEST_CHANGES`（仅剩作者完整 CPU Acceptance Evidence 未通过；对新增 Store 生产修复本身未发现 code blocker）。**

这是一轮**新 Formal Pair 的最小增量审核**，不是重新审核 Batch/Local-TTT/D1-D5/历史版本。上一 F3-P1 子模块生产 mkdir race 为本轮源码已修复项（source-level CLOSED）；正式 Code/Evidence Gate 因完整作者 CPU FAIL 暂不关闭，旧 DS Evidence Gate 仍 `REQUEST_CHANGES`。不得把 58/34 组 focused PASS 当作完整 434 项 PASS。

## 1. 远端身份和实际改动

GitHub 实际 commit 已读取、与 Gitlink 精确核对：

| 组件 | old | new | 直接改动 |
| --- | --- | --- | --- |
| Child | `774c2edb93ec5a6ba85ba1124757064d7cc779a5` | `0ae313e329d290fc6b8a50fda1112820fb7ac485` | 只改 `cosmos_framework/evaluation/robocasa_v2/store.py`（+7/-1） |
| Root | `c724cb8b1ac74c8b1748bdaac95450fb0635a095` | `657061e6893bd61e685685089a1cf1f61e9eb1fe` | 只改 Child Gitlink 与新增 `tools/v3/eval_v2_batch_tests/store_mkdir_test.py`（136行，8项回归） |

GitHub 新 Root direct parent = 上表 old Root；新 Child direct parent = old Child。未发现对 `runtime.py`、`Batch`、`Local-TTT`、`F1/F2/F3` 或训练路径的本轮代码改动。V3 生产 Gitlink 尚未更新到新 Child。

## 2. F3-P1 — 源码层面 CLOSED：并发创建 fault 目录

**实际修复：** [Child store.py:49-64](https://github.com/wxwy/cosmos-framework/blob/0ae313e329d290fc6b8a50fda1112820fb7ac485/cosmos_framework/evaluation/robocasa_v2/store.py#L49-L64)

```python
    mkdir(path.parent)
    try:
        path.mkdir()
    except FileExistsError:
        # A concurrent creator may have won; accept only a real directory.
        path = safe(path)
        if not path.is_dir():
            raise ValueError("directory required")
    sync_dir(path.parent)
```

审核发现：并发创建真实目录的败者能够安全继续发布其**独立随机 UUID** fault 文件；插入普通文件、链接目录和悬挂链接时 `safe`/revalidation 仍 fail-closed；与 `FileExistsError` 无关的 I/O 异常不会被吞掉；`sync_dir(parent)` 对两名争用者都保留。保留原有递归父目录创建，未新增全局锁或改变 Store fault authority。

**新真实路径测试：** [Root store_mkdir_test.py](https://github.com/wxwy/psm_wma/blob/657061e6893bd61e685685089a1cf1f61e9eb1fe/tools/v3/eval_v2_batch_tests/store_mkdir_test.py) 包含 8 项。一个双线程 Barrier 在同一缺失 `errors/` 目录撞车，分别使用真实 `Store.finish_invalid` 与 `Store.record_process_error`，断言两个故障记录的 UUID 唯一、`core_invalid` 与 `coordinator_stop` 均持久化、parent fsync 2 次、没有 Core/result 成功误判；其余覆盖现存 file/symlink/parent-symlink、竞争插入 file/symlink/dangling-link 及 unrelated EIO 传播。确定性 old RED/new GREEN 是**作者报告**，GPT 未独立运行原始 JUnit/多线程试验。

**当前源码增量无新 blocker**。继续保留现有 F3 OS Server exit23／两个真实 active Tickets／owned process-group 清理／foreign isolation 原测试，不允许用 mock 规避。

## 3. 作者 CPU 证据与未关闭 Gate

作者提供：focused CPU `58 passed`，Phase B 单独 `34 passed`（原26+新增8），Ruff/format/AST PASS。并报告在同一新 Pair 的作者**完整统一 CPU**：inference 145 PASS；phase_a_regression 执行73，其中72 PASS /1 FAIL；phase_b_runtime **尚未进入**（因 `-x`）。完整总期望 `145+255+34=434`，不能记为完整 434 项跑过。

**唯一现场 FAIL：** 作者称未改 Phase A 发生 **150ms READY 握手超时**。新 Formal Pair 并未修改 Phase A 测试和 Root `Actor` 生产实现；GPT 无原始作者 `phase_a_regression.xml/log` 或确切 traceback，因此不把故障草率定性为“环境问题已证实”“Store 回归”或“Batch Bug”。

### A1-E1 — MEDIUM，验收证据／Phase A 测试脆弱性待核实

- **具体源码见证：** [Root `tools/v3/eval_v2_production_tests/process_test.py:28-50, 81-87`](https://github.com/wxwy/psm_wma/blob/657061e6893bd61e685685089a1cf1f61e9eb1fe/tools/v3/eval_v2_production_tests/process_test.py#L28-L87)：`test_stalled_actor_request_is_bounded_and_unrelated_process_survives` 使用 `actor(tmp_path, timeout=0.15)`；`actor()` 在**尚未发送故意 stall 请求前**就启动 Python 子进程并 `value._receive()` 等待 `READY`。
- **运行机制确认：** [Root `scripts/robocasa_eval_v2_processes.py:129-151`](https://github.com/wxwy/psm_wma/blob/657061e6893bd61e685685089a1cf1f61e9eb1fe/scripts/robocasa_eval_v2_processes.py#L129-L151)：`_receive()` 把同一个 `self.timeout` 用作socket timeout和截止监控。因而该测试将**初始化/导入/READY 的150ms启动预算**错误耦合到**故意 stall 请求的150ms操作预算**。在共享 CPU 上可能出现初始化 READY 先超时，而根本没有进入被测 stall 分支。
- **限制：** 这是源码独立确认的 *test fragility*；当前失败是否精确落在该测试与该调用行，仍须第一条原始错误栈和 JUnit test id 佐证，不能仅凭作者的一句“150ms READY”完成归因。
- **验收标准：** 先由 Codex/作者提交本次原始 `phase_a_regression.log` 失败前后最小片段及 `.xml` 唯一失败 testcase/traceback；若确认为上述 READY 初始化，应只在原 Phase A 测试内把**子进程启动 READY deadline** 与 **实际 stall 请求的150ms deadline** 分离。保持 `Actor` 生产 timeout、总 wall bound、foreign/owned cleanup/timeout assertion 不变；聚焦 old/new 证据或限定条件重现，再一次作者完整统一 Gate。若 traceback 指向其它路径，不得猜测/擅改此测试，应先回报真实首错。禁止在生产 Actor 层扩大 timeout 或跳过/xfail 该用例。
- **后续 Formal SHA：** 任何 test-only 补丁均须提交新 Root 完整 SHA、Child 保持 `0ae313e329d290fc6b8a50fda1112820fb7ac485`，仅针对该文件做新 Pair 最小增量审核；此前 F3 生产修复不得反复重审。

## 4. Verdict 与下一阶段

**`REQUEST_CHANGES`：Evidence-only／作者完整 CPU Gate FAIL；当前 Root/Child 生产代码增量无独立可确认 blocker，F3-P1 修复在源码层面 CLOSED。** 此时不能授权 DS 以已完成的名义关闭独立 434 Gate，也不宜在未确认首错前反复整套 rerun。待针对单个 Phase A READY 问题补齐异常证据与必要时单文件 test-only 修复、作者完整 CPU Gate PASS，再按已有流程由 DS 在新干净 Pair 一次独立统一 CPU 验收。

不批准 V3/Child 生产合并、GPU/真实 Cosmos/RoboCasa/Canary、DCP、900集、训练、checkpoint、vendor 更改；不影响当前运行训练。无新架构设计或 Batch 参数扫表。
