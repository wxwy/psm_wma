# PSM-WMA V3 — EvalV2 Split Render / Media Lifecycle 独立增量 Code Gate

- 日期：2026-11-01
- **Verdict：`REQUEST_CHANGES`**
- Formal Root implementation/design：`46d3a604e66ca139e2f060fd4caaaa0583a1035f`
- Formal Child / Gitlink：`d3b2a29b978ff4abef800b9e71fab4422b7a0d23`
- Canonical base Root：`7e2be5ca40891915a1e86eea935ed054ec1984dd`；Child：`8664267704da3206e719f3c7eef2b5ed86e2a417`
- 隔离候选分支：`v3-eval-v2-render-media-20261101`（后续 Evidence / Inbox / Receipt bookkeeping commits 不是 Formal implementation）
- 冻结合同：`docs/build/PSM-WMA_V3_EvalV2_Split_Render_Media_2026-11-01.md`，尤其 Media lifecycle 的 **unknown close errors remain blocking**；Owner 边界：仅 GPU4–7，不得触碰 GPU0–3，Server [4,5] / EGL [6,7]、M8/B2 可配置；Media 异常不能改变有效 Core/Local 事实，但真实资源不安全必须 fail-closed。
- 范围：隔离候选代码与作者合成 CPU Evidence；**未重跑 pytest、未访问运行服务器、未执行 GPU/EGL/RoboCasa/真实 FFmpeg**。

## 1. 已审核的实际变更与通过项

1. Root `scripts/robocasa_eval_v2/config.py`、`resources.py`、`runtime.py`、`identity.py`、`cli.py`：严格的 render backend / ordered render_gpu_ids 配置、Server 与 Render 分离、M1..8 / B1..8、selected GPU union + reserve + foreign CUDA admission，New Run Manifest rendering identity、Fresh invocation 约束、CPU dry-run 映射。示例仅使用 CUDA GPU4–5、EGL GPU6–7；GPU0–3 未被示例分配。资源预留值是预算，不代表实测峰值。
2. Child `cosmos_framework/simulation/robocasa/render_devices.py`、`eval_v2_worker.py`、`eval_v2_slot.py`：依据 NVML PCI 与 EGL DRM/sysfs PCI 映射，不信任 CUDA/EGL 序号相等；Worker 配置前设定环境，首次重置后再核实际 Context；OSMesa 保留，无法证明时拒绝。实际 EGL 扩展/DRM/驱动可用性只能通过后续硬件 Gate 确认。
3. Child `media.py`、`eval_v2_adapter.py`：Queue feeder / reader close 序列化、bounded close、forced cleanup 与 live encoder/feeder 状态分开；Root `robocasa_eval_v2_processes.py`：对 Actor-owned group 内剩余进程做有限等待、身份核对、pidfd 定向 SIGTERM/SIGKILL，仍禁止未验证外部进程的清理；未更改 Scheduler / Store / Server / Local 算法。
4. 已直接读取作者 `final/junit.xml`，计数 **192 tests, 0 failures, 0 errors, 0 skipped**；`final/gate.json` 精确绑定 Root / Child / Gitlink，Python3.13.5，Ruff0.12.7、format、语法、来源绑定通过。共有23个 formal source bindings 与53个 raw artifact hashes。两次 development / 早期 fixture/style stop 未与正式192重复累加。
5. DS 提交的运行日志只作为来源方观察；作者通过 CPython3.13 的注入对照覆盖 EBADF → QueueFeederThread semaphore 二次异常机制，但这不能证明 out2 的全部异常都由单一路径引起。本 Gate 不关闭真实硬件和真实视频编码验收。

## 2. 当前唯一确认 blocker

### RM-M01 — MEDIUM / Production：Queue 关闭异常被诊断化，但未传给 cleanup-failure authority

- **位置**：Child `cosmos_framework/evaluation/robocasa_v2/media.py:221-226, 251-259`；影响 Root `scripts/robocasa_eval_v2/runtime.py:680-683` 的资源/安全 Gate。
- **实际路径**：`MediaSink.close()` 对 `self.queue.cancel_join_thread()` 或 `self.queue.close()` 的 `OSError/ValueError` 只执行 `_diagnostic(self.errors, error)`，未设置 `fd_failed=True`。如果此时 encoder 已退出、feeder 也已退出，且随后 reader/writer 的 `close()` 正常，`process_cleanup_failed = encoder_alive or feeder_alive or fd_failed` 仍然为 False。
- **违反的 frozen contract**：设计明示“Unknown close errors, a live encoder, or a feeder that cannot stop remain cleanup failures”。未知 Queue 清理错误不能仅因为随后检查没有存活进程就被消解为“已证明成功清理”。本分支也未被当前192用例中的 Queue/reader fault 测试直接证明。
- **可验收条件**：为上述两个 Queue 关闭步骤的非预期异常记录明确、不可重置的 `fd_failed`（或等价 cleanup-failure）状态；在不造真实 FFmpeg/GPU 的情况下，用 fault injection 分别触发 `cancel_join_thread` 和 `queue.close` 的非预期 `OSError(EIO)`/适用 `ValueError`，断言 `process_cleanup_failed=True`，并验证 adapter/reporting 将故障与纯诊断 EBADF / successful forced-reap 区分。只需窄范围 Child production + 测试；不改进程架构和任何科学链路。

本 finding 是实际源码的控制流推导，不借用其他 reviewer 的 verdict。无需因它对 Split GPU、EGL 或整体架构重新设计。

## 3. Closure / 停止边界

- **Final technical verdict：`REQUEST_CHANGES`**；当前 formal pair 尚不能关闭 GPU 分离 + Media lifecycle 合并 Code Gate。
- 当前仅 1 个 MEDIUM Production blocker（RM-M01）；其余经查范围内未发现可证实的 code blocker。新的 implementation SHA（即使 tests-only）应 fresh incremental review；旧 SHA 的本 verdict 不继承到新 SHA。
- 未授权：合并/提升正式 V3 或 Child；在跑 `out2` / NoTTT worktree、Config、媒体、结果、DCP、日志、进程；启动真实 GPU/EGL、模型/Simulator/FFmpeg、Canary、训练、评测或 Resume。
- DS independent CPU Gate 仍需单独验收；GPU 硬件资源、8Sim 并发、真实 Context、视频编码和峰值吞吐一律未验证。必须由后续 Gate / Owner 另行授权。

Evidence：`docs/collab/codex/evidence/2026-11-01_eval_v2_render_media_author_cpu/`；作者交接：`docs/collab/codex/reviews/2026-11-01_V3_EvalV2_Split_Render_Media_Author_Handoff.md`。
