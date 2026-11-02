# Codex 任务 — EvalV2 Replan 视频缺失：仅修 `save_generated_video: all`

**任务来源：Owner 2026-11-02 最新指令。** 900 Episode 的媒体开关由 Owner 手动控制，**不属于本次整改**。当前唯一目标：只要用户主动指定 `save_generated_video: all`，成功完成的视频诊断运行就必须为每一次 Replan 持久保存一份真正完整可解码的 Generated MP4；不得将 `all` 解释为 best-effort 请求。失败时要明确报告媒体不完整，不能默默漏掉文件或错把 `fetched_to_optional_sink` 当成 MP4 落盘确认。

## 冻结身份/边界

- 上轮已批准代码 Formal Pair：Root `4b581493db805c92964cb27e740c736db87c0329` / Child Gitlink `9a8cd6183424bfce245fbca393ca25ed59919ea6`。`APPROVE_CODE` 仅覆盖旧 pair。
- 工作仓 `wxwy/psm_wma`、子模块 `wxwy/cosmos-framework`，当前候选 `v3-eval-v2-render-media-20261101`；**先刷新远端 HEAD；新实现单独分支与新 Formal Root+Child/Gitlink SHA**，需重新走 GPT incremental Code Gate、DS 独立 CPU Gate。
- 只调整 Replan Generated Media 的 candidate 缓存、传输拉取、确认落盘、结束排空必要路径及定向测试。**不修改** Action/Local-TTT 的预测、策略执行、SR 权威、RoundScheduler、GPU 准入/角色、 checkpoint/training、数据集、正式评测媒体开关逻辑；`save_generated_video: none` 仍不请求/生成/保存 MP4；`first` 维持现有能力/默认语义。
- 不修改/覆盖历史 H3 `out`、`out2`、No-TTT 或任何训练/Checkpoint/DCP/视频/日志，不查询/停止其他 GPU 任务，不访问 GPU0–3。**本任务仅授权候选代码与 CPU 测试，不授权 GPU 实跑或 V3 合并。**

## 证据和可复现的具体缺口

真实 H3_swap：`replans=481`，成功 fetch 并形成文件 `401`，服务器 `bounded_spool_unavailable=73`，Episode-end `cancelled_at_episode_end=7`。媒体文件对账显示 `401/401` 已 fetch 的视频都落盘，但 **80/481(16.6%) Replan 缺 MP4**。H3 是历史 evidence，**不要求也不能事后补生原始80个潜在视频**。

核心现有源码（Child `9a8cd6183424bfce245fbca393ca25ed59919ea6`）：

1. `cosmos_framework/inference/robocasa_batch_transactions.py:90–93`：`media_room()` 仅允许 **2 个媒体 jobs、128 MiB**；`:229–242`：room/candidate/bytes/decoder 检查不通过时显式返回 `dropped`，无 backpressure。其 `_pump():143–185` 优先处理新的 inference 队列，媒体解码只在推理队列为空时发生；`media_ack():385–393` 才释放 job。
2. `cosmos_framework/scripts/action_policy_server_robocasa.py:1283–1303`：根据 `media_room()` 才复制 vision latent 到 CPU；如果 room=0 就根本没有媒体 candidate，之后不能从 action response 恢复。
3. `cosmos_framework/simulation/robocasa/eval_v2_transactions.py:115–117,127–152,154–221`：`all` 只表示**每次请求媒体**；当前异步 fetch 有 `_pending<=2` 容量与关闭时 `_stop` 清队列；`cancelled_at_episode_end` 使最后若干 Replan MP4 丢失。`fetched_to_optional_sink` 的标记发生在 `deliver()` 调用后，**并不证明异步编码完成**。
4. `cosmos_framework/evaluation/robocasa_v2/media.py:153–210`：`MediaSink._submit` 使用 `queue.put_nowait`，编码队列满可以 silently drop；`close` 在有限 grace 中用非阻塞 sentinel，且可能强制结束 Encoder。对于 `all` 诊断模式，需保证 ack/落盘时序，不能在原视频尚未持久化时认为传输完成。

## 必须达到的行为（由 Codex 选择最小、安全的实现）

**B1. “all” 严格完成**：每次 Replan 的唯一 `replan_index/request_key` 均产生唯一 MP4，或产生明确、不可被误当做完成的 `MEDIA_INCOMPLETE`/diagnostic-failure 证据；不允许 `dropped`/取消却仍报告 **`all media complete`**。避免错误地把“媒体失败”归因为机器人 Task failure、SR failure 或 Local Reset failure。诊断完成成功时 `replans == number of complete, decodable generated_mp4`；所有文件必须对应正确 Episode+index。

**B2. 有界背压而非扩大无限缓存**：在 `all` 模式下，当服务器 spool 2 jobs/128MiB 或客户端媒体队列满时，不得直接舍弃 Replan latent/video；应有**有界等待/释放后重试或可证明等价的 lossless diagnostic-mode**。不能持锁无限等待，不能把需要用同一 Model Executor 执行的解码饿死，不能阻塞其他 Session End/Local ACK 的安全清理。遇到真实超时/OOM/编码失败，应**明确失败并停止诊断的成功宣告**，而不是吞异常。
 
**B3. Episode 结束必须先排空媒体**：`all` 请求发送后，等待本次 Episode 的已接收媒体 decode → fetch → 编码完成 → 文件落盘/校验，再 ACK/释放 server ticket（或等价严格顺序），最后安全结束 Session；需要独立边界避免任意其他任务/媒体进程污染。**ACK 不得早于落盘确认**。保留 bounded deadline、pidfd/Encoder 安全回收；禁止无限 join 或复活已结束 Session。

**B4. 低负载手动分析优先**：用户只会对关注的 CKPT/Task 人工开启 MP4、Episode 数少，**可以牺牲该诊断模式的吞吐**来实现严格完整性；不需要兼顾900EP视频保存或复杂的高并发吞吐优化。实装时至少保证 1 Task×少量 Episode、M1/B1 的严格保存，同时高并发请求也应 fail explicitly 而不能 silent loss。无需为此重构大规模异步任务平台；如选择对严格模式限制并发，必须在启动前显式安全报错/提示，不可静默改掉用户配置。

**B5. 兼容与科学语义**：`save_generated_video: none` 仍不申请媒体、无额外等待；`first` 保持可用，避免回归；动作输出、Local-TTT、Core/SR/Session Reset ACK、不参与 SR 的媒体诊断数据维持既有权威。不要为媒体问题擅自重跑 Episode/预测动作。不得绕过 API 的绑定身份、Session ownership 或 deadline。

## 必要测试 / Gate

- CPU deterministic 测试：spool 充满（>2 个 media job）、候选 byte budget 不足、服务器解码慢、网络 fetch 慢、客户端队列满、Encoder 慢/出错、Episode 在最后 Replan 后立即结束、重复/迟到响应、deadline/取消、其他 Session 并发 End。测试应在真实公开 API 控制路径进行，模拟可控延时，**不要只测 helper**。
- 两条对照：`none` 必须未改变快路径；`first` 无额外严格等待或错误传染；`all` 在健康有界场景 `10 replans => 10 文件和 10 success acknowledgments`，每文件真正可解码且编号一致；故障场景不能假 PASS、不能泄漏 encoder/feeder/owned processes。
- 根据需要针对少量 `all` Analysis Run 在定向 CPU 驱动中输出 `replans/expected/accepted/encoded/acknowledged/missing`，验证 `missing=0` 才算媒体完整。
- 保留原 Formal Pair 既有 Code Gate/Evidence 与配置 ABI，Ruff、format、py_compile、定向 pytest，冻结 exact Root/Child/Gitlink、测试 JUnit、命令/状态/源码 Diff。新子模块修改需更新 Root gitlink。
- **停止点**：提交孤立候选新 Formal Pair、author CPU evidence、Code handoff 给 GPT 审核后停止；DS independent CPU / 后续真实小规模 GPU Canary 必须再经 Owner 单独授权（目前未授权）。不可自动合并 V3 或修改正在运行作业。

**重要**：修的是 Replan 的传输/落盘语义，不是 GPU7 EGL/真实 B2 batching，也不是 900 Episode SR 评测。保留所有以前实验结果，不改 H3 历史结论。
