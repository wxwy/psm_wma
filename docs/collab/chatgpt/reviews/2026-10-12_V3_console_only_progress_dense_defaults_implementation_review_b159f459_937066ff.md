# PSM-WMA V3 — Dense默认关闭缓存优化 + 控制台抑制训练JSON：新 Implementation SHA 增量审查

**Date:** 2026-10-12
**New implementation Root SHA:** `b159f45906f7261d028aecc226ab7f2bb9807eb9`
**New Child/Gitlink SHA:** `937066ffd90f2bf783ad4fbb4909e9c0b8922982`
**Compared against:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` (former current Formal Child), Root此前仅文档后继HEAD，原实际训练Formal Root为 `444c232b976e80ac68cde9e7370e73b9f6410f0e`.
**Scope:** `V3_DEFAULT_OFF_CACHES_AND_QUIET_TRAIN_CONSOLE`
**状态:** **代码已提交、增量静态diff符合Owner限定范围；定点CPU真实测试尚未执行，因此 Implementation Gate保持 `TEST_EVIDENCE_PENDING`，不宣称最终训练验收或D1 Gate通过**。
**Diff证据:** `docs/collab/chatgpt/evidence/2026-10-12_V3_console_dense_defaults/2026-10-12_implementation_diff_receipt_b159f459_937066ff.md`。

## 定点审核（从当前仓库源码核验）

**C1: 两个功能缺省=0、显式=1仍启用 — 符合 Owner 裁决**
- `cosmos_framework/data/generator/action/utils/cached_pixel_geometry.py::compact_cached_video_enabled` 唯一改变为环境缺省 `"0"`，非法值的 `ValueError` 语义未变。
- `cosmos_framework/data/generator/action/datasets/robocasa_shared_episode_reader.py::install_rank_shared_reader` 唯一改变为环境缺省 `"0"`，显式 `"0"`直接返回None，显式`"1"`维持缓存安装，非法值验证未变。
- 没有按 `job_name` / `resume` 特判或新式训练入口阻断；这是与具体训练任务解耦的默认策略，而不是关停优化特性。

**C2: 日志只改变回显Sink，不改变指标载体 — 符合Owner裁决**
- `examples/psm_wma_robocasa_formal_monitor.py::TelemetryJournal.__call__` 保留完整 `TRAIN_PREFIX` 指标JSON在 `monitor/train_rank0.jsonl` 的顺序写入；继续在Raw日志存档（重复但不影响恢复/监控 schema）。
- 仅过滤该精确训练JSON前缀的console echo。其他`[progress]`, `[checkpoint]`, `[logging_error]`, Runtime warnings/errors 仍经过`_console`，原持久化/异常处理逻辑保持。根据已审核 `GroupedPlanObserver._post_commit`，普通训练每步完整train指标原本就只在rank0产生；这次没有修改observer其他rank计算路径。
- `--tee 3`为原生torchrun参数，**Owner已取消另一个命名Logger Launcher重构请求**；之前 `docs/collab/chatgpt/requests/2026-10-12_V3_formal30k_named_rank_logging_cx_implementation_request.md`仅作为历史提议，不再授权cx实施。此次没有编写launcher、改 torchrun。

**C3: 回归测试 — 源码覆盖已提交，Runtime Evidence未闭合**
- 两个缓存路径的 default与显式1 CPU检查，以及TelemetryJournal progress/train/checkpoint/error输出和JSONL追加检查已提交。
- 远端 GitHub `compare`仅5个Child文件（3 production +2 tests），主仓对应 implementation commit只更新Child Gitlink。
- **受执行环境限制，GPT没有运行完整pytest**；不能凭测试代码存在声称 tests PASS。必须由DS在新Child`937066ffd90f2bf783ad4fbb4909e9c0b8922982`隔离工作树CPU-only执行两个定点测试文件和必要ruff/py_compile，返回可追溯stdout/pytest summary、Child SHA、无GPU/Checkpoint触碰证明。
- 因此当前 `TEST_EVIDENCE_PENDING`，后续收到DS结果需按精确新Pair fresh Gate增量复核；不要重新审核已关闭的C1或旧D1。

## 新版本部署边界（重要）

当前正在运行/已启动的 Formal30k 仍使用冻结历史Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` /Child `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`，**不能为了启用本次小改动而在运行服务器 `git pull`/checkout改变生产工作树**，尤其不能假称运行进程会自动使用新默认值。若要在未来启动上应用此变更，必须另行审定新Formal Pair与部署时机（当前新Root Implementation = `b159f45906f7261d028aecc226ab7f2bb9807eb9`）。
运行中的ON/ON错误模式属于已有实验执行事实，不能用默认OFF修复已保存的DCP；Owner按真实模式控制停止、隔离与恢复。
本review不授权GPU启动、正式训练自动重启、或更新原任务DCP。

## 审核结论

**`CODE_COMMITTED / STATIC_DIFF_SCOPED / TEST_EVIDENCE_PENDING`**，尚不能标为完整实现 Gate APPROVE。等待 `docs/collab/chatgpt/requests/2026-10-12_V3_console_dense_defaults_scoped_CPU_validation_to_DS.md`的定点CPU结果再下最终正式 verdict；未发现代码diff直接违反Owner已确认的解耦策略。
