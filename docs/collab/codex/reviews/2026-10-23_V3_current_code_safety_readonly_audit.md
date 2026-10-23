# V3 当前代码安全与结果可信度扫描

日期：2026-10-23（Asia/Shanghai）。性质：Owner 明确要求的代码扫描及聚焦 CPU 故障注入，不是新实现提交、正式验收或训练执行授权。

## 1. 版本、范围与结论

| 项目 | 精确身份 |
| --- | --- |
| 检查开始及提交前确认的远端 V3 HEAD | `81055c909d6547ed4eb607fd0cc746af4bee7c0a` |
| 当前生产 Implementation Root | `a4b22b929175e462b6a8db57ad2abee7e220dd37` |
| Child / Root Gitlink | `c9f21040f462a114d597fc83773cb9b6a9e96214` |
| Vendor 可重建产物 | `1ac174585293ed998ffc9cf73e47439798cf6f6c` |
| 本轮再次查询的 NVIDIA 官方 main | `9a70e64d2ad7ff1417484d12d10fb121b270baaf` |

Root 已 fetch、ls-remote、ff-only 同步；新增三提交仅文档，生产源码/Gitlink 未变。扫描覆盖当前 Queue/结果/进程管理、HTTP/Local Session/动作与 Rollout、Grouped Trainer/Window/Adapter、Exact-Window 数据/预取/审计、DCP/RNG/Namespace/G1 Override、Launcher/Config/Vendor 权威。依据当前官方 Host 和已批准项目合同，不按 V2 文件/功能列表要求回迁；这不是全仓每个文件或最新上游升级的完整验收。

**确认六项建议整改的 P1 问题，未证明新的 P0 或运行中 G1 已发生故障。** 其中四类有本轮聚焦 CPU 见证；旧入口和依赖锁权威来自完整源码/合同调用链，未启动这些入口或实际运行环境。所有建议均待确定实施范围，不自动修改当前训练。

## 2. 发现与最小整改

### AUD-01 — P1/HIGH：任务指令缺失或读取失败后，仍以空 Prompt 评测

**位置**：Child `cosmos_framework/simulation/robocasa/closed_loop_eval.py:280–283,297–305`；Server `scripts/action_policy_server_robocasa.py:954–956`；Root `scripts/robocasa_eval_results.py:347–393`。

`get_ep_meta()` 抛错时被替换成 `""`；缺少 lang/空 lang 也得到 `""`。HTTP Server 仅检查 prompt 是字符串，允许空指令继续生成。Rollout 正常返回，`run_recorded_episode()` 写 `error=null`、`outcome=behavioral_failure/success`，完成校验并不检查语言有效性。

**CPU 见证**：实际 `run_policy`、记录器、`finish_attempt` 和 Resume 验证器，以假环境/Local Client/预测和进程见证构造：metadata 抛错和缺少 lang 两种情况均调用预测两次，发送空字符串，最终 `COMPLETE` 且 Resume 跳过。没有真实 Kitchen、策略或物理执行。

**影响**：语言条件损坏可能成为合法 SR 样本，甚至整轮评测都缺少任务指令；文件/进度完整不能排除这个语义错误。

**最小修复**：正式语言条件协议在第一次预测前要求 metadata 为对象、lang 为非空且非纯空白字符串；错误沿现有 runtime_error/partial/Local cleanup 路径传播。不要自动用 Task 名或别的字段替换指令。保留原合法指令字节；空指令实验须显式独立协议。

**回归**：metadata 抛错/None/缺键/空/空白/非字符串都不调用 predict，保留原错误并清理 Session，不能 COMPLETE 或恢复跳过；合法指令保持不变。CPU 足够验证逻辑，不改训练 Config Digest、DCP 或 Local 算法。

### AUD-02 — P1/HIGH：成功判定异常被当成普通“未成功”

**位置**：Child `closed_loop_eval.py:215–219,383–391`；`utils/rollout_evidence.py:97–129`；Root `robocasa_eval_results.py:347–355`。

`check_success()` 捕获 `_check_success()` 的全部 Exception 并返回 False。异常不进入 Rollout 错误或清理见证，最终可能成为 `behavioral_failure/error=null`，影响 SR 并允许 COMPLETE/Resume 跳过。

**重要限定**：真实 RoboCasa 的 `Kitchen.reward()` 在 `env.step()` 内也调用 `_check_success()`。因此“该函数每次都抛错”的真实环境通常会先由 step 冒泡，不能用简化假 step 证明它必然被吞掉。本轮最终探针模拟 step 内第一次检查正常、评测器随后检查间歇性抛错，验证的是**外层成功检查异常传播缺口**，不声称复现真实 Kitchen 已有持续故障。

**CPU 见证**：上述双次检查假环境完成两步、四次检查，外层两次错误均消失；实际结果/Attempt 验证器接受 COMPLETE 和 Resume 跳过。假 Runtime/进程见证明确不是真实运行验收。

**最小修复**：取消该 blanket fallback，或将异常显式传回 runtime_error；沿已有 finally 保存动作、错误、媒体和 Local cleanup，不把 Oracle 失败归入正常行为失败。AUD-01/02 的 fallback 在本轮锁定的官方源码也存在；这是与项目严格评测合同不相容的上游行为，并不因此要求退回 V2。

**回归**：外层成功检查间歇性抛错必须保留异常；普通 False 仍为行为失败，True 仍遵守 latch；step 内抛错同样保持原错误，不被清理异常覆盖。逻辑可 CPU 验证，不改训练/Checkpoint。

### AUD-03 — P1/HIGH：某个非空活跃 Rank 整体缺梯度，可以通过两处安全检查

**位置**：Child `cosmos_framework/trainer/local_memory_grouped.py:187–206,363–381`。

`local_present` 表示本 Rank 有任意梯度；跨 Rank 使用 SUM，最后只判断全世界是否完全没有梯度。因此 Rank0 有有限梯度，就会掩盖 Rank1 对所有非空选中参数的梯度均为 None。两处检查使用相同公式；若 Hook 在第一次检查后清掉一个 Rank 的所有梯度，第二次检查也不会阻止其跳过参数更新。

**CPU 见证**：从锁定源码 AST 提取这两个原始方法，用真实两 Rank CPU Gloo + SGD。非空 Rank1 全 None 时，两 Rank 都不抛错，Rank0 从1变为约0.9，Rank1仍为1；第一次 Guard 后清掉 Rank1 梯度同样通过。对照保留：部分参数 None 但每 Rank 有有效梯度、合法全空本地分片可以通过；全世界 None 和单 Rank Inf 均正确使两 Rank 抛错。

这只证明当前 Guard 的检测性质，**不证明真实 FSDP 或 G1 曾丢失梯度**。SGD 参数是语义替身，不是模拟出完整 FSDP 所有权；当前 Phase5 每 Rank 有 Consumer，不适用尚未设计的闲置 expert/pipeline Rank 豁免。

**最小修复**：按 `requires_grad` 及本地 `numel()>0`（DTensor 经 `to_local()` 后检查）判定活跃参数所有权；拥有实质训练分片但无任何非空本地梯度的 Rank 标为 bad，用 MAX 作全 Rank 一致失败，并继续要求全局至少一份有效梯度。不得要求每个参数 grad 都非 None，也不得把有限零梯度当缺失。保留合法空 FSDP 分片。

**回归**：复用本轮六场景，加入全 Rank 无 optimizer/Local commit 断言。CPU Guard 回归后，涉及真实 DTensor 所有权仍需独立授权的 FSDP 验证。补丁本身不应改模型/DCP 格式或既有 Config Digest；不得自行同步到活动 G1。

### AUD-04 — P1/HIGH：仍可执行的旧 RoboCasa 入口绕过新保护

**位置**：Root `scripts/eval_robocasa.sh:61–107`；`docs/current/evaluation.md:183` 仍有入口指引。

旧脚本仍命名为 V3 Local-TTT 评测，未拒绝或标记为独立诊断协议，但：

- `:67` 不传 `--action-chunk-size 16`，使用 G1 历史 config32 可再次走错误默认。
- `:77–95` 接受端口 `/info` 后仅校验 Local mode，不校验监听 PID、指定 Checkpoint/Config/chunk。
- `:70–73` 仅 kill Server PID，没有统一 Queue 的进程组清理及整个任务时限。
- `:105–107` 不传 runtime lock/digest/Attempt/progress，返回后直接宣告 complete，不调用新完整性验证。

这不是新 Queue 的 HIGH-02/HIGH-07 回退，也不是已发生错误模型评测的证据；问题是**另一条仍可执行且被指引的入口**绕过已批准保护。仅改 README 不能关闭它。

**最小修复**：旧入口在任何写入/进程启动前明确拒绝并指向统一入口，或将参数完整转换后转调严格 Queue。优先停止维护第二份编排。若保留弱检查诊断，必须独立命名/协议，不能产出正式 complete/SR。

**回归**：用 shell/Python/curl stub 证明旧入口在启动前拒绝，或实际转交统一身份、chunk16、Runtime、Attempt、超时/清理及结果验证。无需 GPU；不修改历史 G1 config32 或旧 Evidence。

### AUD-05 — P1/MEDIUM：部分 Worker 线程启动失败后，已启动线程没有被取消/回收

**位置**：Root `scripts/eval_robocasa_18task_queue.py:781–802`；Namespace lease `:496–503`。

逐个 `thread.start()` 时若第二个或后续线程因资源限制抛错，将跳过全部 join，finally 只恢复信号处理。已启动的 non-daemon Worker 没有收到 stop，仍可领取任务。异常沿调用栈退出还会释放 namespace lease，而 Worker 仍活动。

**CPU 见证**：执行该原始 Try AST 块，第一条真实 CPU 线程已启动，第二条注入 start RuntimeError；异常冒泡后 `stop=false`、第一条仍 alive。探针自身随后 stop/join 并确认回收，没有启动 Server/Simulator。

**影响与限定**：启动失败后仍可能加载模型、继续评测、阻塞 Python 退出并丢失独占保护。不是“该异常返回0”的证明，也不能称绝对无限挂起；实际 Worker 仍有每任务预算。

**最小修复**：记录已成功启动的线程；启动异常时登记 Worker/fleet 错误、置 stop，在持有 lease 时回收全部已启动线程并写 INCOMPLETE，再传播原错/非零返回。不能 join 从未启动的线程。

**回归**：第1/第2/最后线程启动失败、正常多 Worker、清理失败保留主错；确认无继续领取任务、无遗留自有进程、summary 保留错误和非零退出。CPU 故障注入足够，不改 Child/训练/锁机制。

### AUD-06 — P1/HIGH：正式依赖校验的权威可以被外部 Lock 替换

**位置**：Root `scripts/robocasa_eval_config.py:52,106,177–184`；Queue `:403–406`；`scripts/robocasa_vendor.py:135–160,268–276`。

正式 CLI/YAML 允许外部 vendor_lock；探针按它提供的 expected commit/version 校验，最终仅复核该外部锁自身 SHA，没有与 Root 版本化批准内容锚定。Batch B r2 review `:13–14` 明确 Authority 为 Root Lock/Patch，并冻结正式依赖。

**源码反例**：复制当前 lock 和 patch，保留有效 patch SHA，仅将 robosuite.patched_commit 改成其他 clean commit；代码将新值直接传给 `audit_source`。没有要求这个版本仍为批准的1ac174。旧未打补丁版本可能在后续 Kitchen 构建失败，但不能据此声称正式版本预检已拒绝偏离 pin。

**限定**：更改锁会更改新 Run identity，旧身份 Resume 会拒绝；这不是跨身份偷渡。MuJoCo native 仍硬编码3.3.1，不是任意运行库都能通过。源码确认此权威缺口；本轮没有实际导入替换 Vendor 或运行完整反例。

**最小修复**：仅正式 Queue 预检要求外部锁与当前 Root 冻结锁内容 SHA 一致，允许同字节副本路径。保留通用 builder 的自定义锁能力；不同依赖须另冻结/审核协议。

**回归**：原锁/同字节副本通过；仅改 patched_commit、RoboCasa commit、NumPy version 的自洽锁在模型/环境 import 和输出 claim 前拒绝；原 wrong patch/dirty source/native/in-process mismatch 负例不放宽。CPU 足够，不改训练配置或历史结果。

## 3. Evidence 与验证边界

本轮证据：[CPU witnesses](../evidence/2026-10-23_V3_current_code_audit_cpu_witnesses/)。两个脚本、完整命令/环境、原始日志与 JSON 已保存。Probe 的 exit0 表示成功复现当前缺口或通过其对照断言，**不是生产代码验收 PASS**。

- Behavior：三种环境/指令故障分别经实际记录器、Attempt commit、Resume validator；另有原始线程启动块故障注入。
- Gradient：六场景 × 两 Rank；执行原始 Guard AST，真实 Gloo/CPU SGD，非完整 FSDP/模型训练。
- Runtime/Local/预测/进程边界为显式 synthetic doubles；未由伪造见证声称真实环境/进程实际安全。媒体关闭，没有渲染、编码、模型加载或真实仿真。
- 没有重跑全仓 Ruff/pytest、没有 DS 独立验收，不继承历史测试计数为本轮通过数。所有缓存和产物在新 `/tmp/v3-audit-20261023` 下，未操作真实数据/DCP/训练目录。

## 4. 已知事项和未发现新缺陷的范围

- F0/F1 主链的 namespace 保护、全 Rank 保存完成确认、Local Sidecar/complete/latest 原子发布、strict RNG、恢复后不重新 Seed 均存在；本轮未证明新的 P0/P1，不能说真实 GPU/存储已经重新验收。
- G1 iter8900-only Override、保留历史 config_digest、完整孤立 Checkpoint 不覆盖、大 shard 不全量 hash 均有明确合同，不当作新回归，也不擅自扩大未来 Resume 权限。
- Batch C 的 C01/C02 已修范围不重新打开：进度/Attempt/Local cleanup 和环境/生成视频分类在当前主链存在。本轮 AUD-01/02 是 Rollout 错误语义问题；完整文件无法识别已被吞掉的错误。
- GradClip 与官方 RoboCasa 配方差异沿用 [前次官方优先复核](2026-10-22_V3_official_latest_first_inheritance_reassessment.md)，需未来任务策略裁决，不自行改 G1 或恢复整个回调组。LIBERO/history/Index8 不扩大为此次整改清单。
- DS 的 Batch C r2 状态仍是 SOURCE_DELIVERY_BLOCKED / TESTS_NOT_RUN，需精确 Root/Child 离线交付；不是测试 FAIL。本轮代码扫描没有代办该交付，不能宣称 DS 已收到。实际依赖/Kitchen/物理/策略效果仍属于独立 Evidence Gate。
- 其他低优先级观察：Local 请求过大时需在解码/Encode1前实施 evidence 上限；`/proc` 读取权限受限时的清理兼容性需目标机确认；partial_sr 应说明按接受的完整结果子集统计。未把这些条件性事项升级为本轮确定 blocker，也不声称它们已修复。

## 5. 建议实施顺序与停止边界

先限定评测整改：AUD-01/02 错误语义、AUD-04 旧入口和 AUD-06 正式依赖权威；AUD-05 Worker 启动失败单列进程故障回归。AUD-03 单独作为训练安全 Guard 批次，不与评测、裁剪策略或算法改动混合。

每批由 Owner/GPT 确认最小范围后，Codex 实现+CPU、自测新 SHA，再独立审核/DS 验收；涉及 DTensor 才另定真实 GPU 验证。不要把本次发现解释为必须停止或同步运行中的 G1，也不为补诊断重做旧 B1 数值等价。

本轮只提交本报告、CPU 见证归档及 SESSION/TODO 记录；生产源码/测试/配置/Child/Gitlink/Vendor 未改，无训练、真实 DCP、GPU、Action Server 或真实仿真操作。
