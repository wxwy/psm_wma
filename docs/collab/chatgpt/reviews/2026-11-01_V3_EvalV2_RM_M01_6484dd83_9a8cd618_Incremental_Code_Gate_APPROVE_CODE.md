# PSM-WMA V3 — EvalV2 RM-M01 Queue close 增量 Code Gate 复审

**日期：2026-11-01**  
**Final verdict：`APPROVE_CODE`** （仅关闭 RM-M01 及所对应 Split Render / Media Lifecycle 候选的源码 + 作者定向合成 CPU Code Gate）

- **Formal Root implementation/design SHA**：`6484dd83efc512e6801470790eb84ac7349c127a`
- **Formal Child/Gitlink SHA**：`9a8cd6183424bfce245fbca393ca25ed59919ea6`
- **上一 Formal Pair**：Root `46d3a604e66ca139e2f060fd4caaaa0583a1035f` / Child `d3b2a29b978ff4abef800b9e71fab4422b7a0d23`，对应已落盘 `REQUEST_CHANGES`
- **隔离候选分支**：`v3-eval-v2-render-media-20261101`
- **上一详细审核**：`docs/collab/chatgpt/reviews/2026-11-01_V3_EvalV2_Split_Render_Media_46d3a604_d3b2a29b_Incremental_Code_Gate_REQUEST_CHANGES.md`
- **冻结设计**：`docs/build/PSM-WMA_V3_EvalV2_Split_Render_Media_2026-11-01.md`（“unknown close errors remain blocking”）
- **作者交接 / Evidence**：`docs/collab/codex/reviews/2026-11-01_V3_EvalV2_RM_M01_Queue_Close_Author_Handoff.md`；`docs/collab/codex/evidence/2026-11-01_eval_v2_rm_m01_queue_close_author_cpu/`

## 1. Remote SHA + scope

已直接读取 GitHub 新 Root/Child commit、相对前一 Formal Pair 的增量以及实际源文件。新 Root 对前次 GPT review/Inbox 后的 Root 只新增 `tools/v3/eval_v2_batch_tests/media_queue_close_fault_test.py`、更新 Gitlink、SESSION/TODO；Child 仅修改 `cosmos_framework/evaluation/robocasa_v2/media.py`：**2 additions / 1 deletion**。未修改 Root 生产代码、render GPU 映射、Process owner Runtime、Adapter、Store/Scheduler、Local-TTT、模型 / Action Server / 训练或 Vendor。Review 和设计源文件保持上一版。

当前实际候选 SHA 有新实现增量，必须按本 Pair fresh incremental review；旧 `REQUEST_CHANGES` 不自动继承。

## 2. RM-M01 closure：CLOSED

**旧 blocker**：Child `media.py:223-226,241-245` 中，Queue `cancel_join_thread()` / `close()` 的未知 `OSError / ValueError` 只记录 diagnostics，不把 `fd_failed` 置 True；下一步仅容忍 EBADF 的 writer close 还可能重写 `fd_failed=False`，导致 `process_cleanup_failed=False` 漏报。

**新 Formal Child 实际修改**：

- `media.py:226`：在 Queue `except (OSError, ValueError)` 中设置 `fd_failed = True`，再记录诊断。
- `media.py:245`：在后续 descriptor `except OSError` 中使用 `fd_failed = fd_failed or error.errno != errno.EBADF`，保持未知 Queue 错误 sticky；后续 `_reader_guard.failed` 本来就采取 OR 合并。
- `media.py:256` 的 `process_cleanup_failed = encoder_alive or feeder_alive or fd_failed` 未改；`eval_v2_adapter.py` 的既有 `media_process_fault` 传播和 Core/Local 语义未改。

**独立判断**：这两处修复直接覆盖原控制流漏洞，未知 Queue 关闭故障不能再被随后健康 / 可容忍 EBADF 的 descriptor close 覆盖。已有正常 EBADF 与成功强制 reap 仍可作为非致命 media diagnostic；真实未知 shutdown fault 继续进入清理失败 authority。**RM-M01：CLOSED，无当前 blocker。**

## 3. 原始 Evidence 核查

- 已查看新 committed test 的实际 116 行、`old_red/frozen_test_before_red.py` 原文件，并独立逐字节比较 GitHub 返回内容：**完全一致**（Git blob `e1d89606cd4b2734d27dadf8d0e8214f773f857f`）。对应测试 SHA256 `2ff48caeb197c5a4e04a04a686ebcdb28944d3e12c4d0968629726b774c56c5c`。
- 旧提交 Child `d3b2a29b978ff4abef800b9e71fab4422b7a0d23` + frozen new tests：原始 `old_red/junit.xml` 有 **14 cases / 10 expected assertion failures / 4 pass / 0 errors / 0 skip**。10 个 `<failure>` 消息都是 `assert False is True`；不是 test fixture 崩溃或缺失测试。
- 新 clean Formal Pair：原始 `final/junit.xml` 有 **29 cases / 29 passed / 0 failure/error/skip**；构成为 14 新测试 + 13 既有 Media lifecycle + 2 既有 Core/native 回归；原始 `final/gate.json`、`pytest.log` 相符。
- 新用例直接覆盖 `cancel_join_thread`、`queue.close` 两个 fault point，EIO 与 ValueError、后续 writer EBADF、有界无异常控制、重复 close 幂等；使用真实 `NativeEpisode.execute` + synthetic 环境/HTTP，检查 `media_process_fault`、`media_diagnostics` 与 valid Core/Local reset 的独立语义。
- 读取并核对作者 clean-Pair Gate 身份、source binding（6 项）、历史192/53 evidence preservation、定向 Ruff0.12.7 / format / syntax / diff-check 通过记录。**未重跑旧192**，历史结果不计入新 Pair 的29。
- 审核读取源码、原始 JUnit、RED/GREEN 以及 GitHub diff；**没有独立重新执行 pytest**。测试仍是作者合成 CPU，非 DS independent CPU 验收。

## 4. Gate 边界

**Verdict：`APPROVE_CODE`。** 仅批准精确 `6484dd83efc512e6801470790eb84ac7349c127a` / `9a8cd6183424bfce245fbca393ca25ed59919ea6` 对应的 RM-M01 修复及完成此前 Split Render + Media Lifecycle 的增量 Code Gate；原唯一 RM-M01 Medium production blocker 为 CLOSED，未发现新的当前代码 blocker。

本代码 Gate **不授权**：

- 合并/提升正式 V3 / 官方 Child；或修改当前共用训练/仿真 worktree。
- 实际 GPU/EGL/OSMesa、真实 MuJoCo/FFmpeg/Action Server、Canary、M8/B2/B4/B8、完整900EP、out2 Resume。
- 修改旧 out2 数据、视频、Core、DCP、No-TTT 训练、日志或进程；**GPU0–3 属其他人资源，不允许测试/占用**。
- 宣称 10GiB Server / 800MiB Sim 预算得到真实证明、真实 EGL 设备可用、MP4 输出完整或解决了长跑故障。

**下一独立 Gate**：DS_PRO 定向 CPU 独立验证；随后经 Owner 单独授权的真实 EGL/FFmpeg、进程清理、资源/吞吐 Canary。此审批不替代独立硬件验证。

本详细 Review 与 canonical Inbox 同时落盘之后才形成 Formal verdict；后续文档 bookkeeping SHA 不更改上述正式 implementation pair。
