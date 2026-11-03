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


## Owner 追加决策（2026-11-02）：Spool 可配置默认 4 / 512 MiB；Media Drain + Encoder DONE

以下为 Owner 追加的**具体实现选择**，覆盖上述任何含糊处，但不放宽原“all 每次 Replan 完整保存”的验收标准。

### A. Server spool 参数及传播

- 引入可配置服务器媒体 spool 上限，**默认 `media_spool_max_jobs: 4` 与 `media_spool_max_bytes: 536870912`（512 MiB）**，明确这是每个 Action Server 的资源上限，不是每 Sim 配额。根仓 EvalV2 YAML/CLI 构造→Server 启动参数→`BatchedSessionTransactions` 传递，并校验正整数/有限安全上限；运行/诊断应记录实际生效配置，避免“Yaml 改了但 Server 没收到”。实际字段名可与既有命名风格统一，但保留显式参数与默认值。没有必要更改模型/训练策略/任务调度。
- 保留现有有限缓存和正确的身份/边界，不采用无限队列。**把默认2/128提高到4/512只降低触顶频率，不能被当做零丢视频的完整修复**。当配置容量不可用或单条媒体超出上限，`all` 不能再静默返回 `dropped` 并把 Episode 标成媒体完整；应在可证明正确的请求/队列边界有界等待重新获取容量，或明确标记媒体未完成，并保留 Action/Core/SR 结果。**不可在共享 `_model_lock`、`_lock`、或同一 media executor 内做阻止当前 executor 释放缓存的等待**；务必审计并排除死锁。

### B. Episode 结束后的媒体等待

- Owner 要求：**结束一个 Episode 时，如 Replan 预测视频尚未完成保存，则继续等待到全部完成**，而不是立即取消最后一批 `pending`。
- 清理必须保持安全：用**媒体专用、可配置的有界 drain timeout** 区别于原 Encoder termination grace；正常健康运行时要求等待所有媒体真正完成，遇到磁盘故障/进程死亡/不可恢复超时才报告 `MEDIA_INCOMPLETE` 并继续安全的 Session/Local cleanup。不要无限卡死，不要悄悄把媒体 cancellation 当完整保存。具体默认 drain deadline 可由 Codex 在实现说明与 CPU 延迟测试中确定并说明理由，Owner 本轮只钉住 spool 默认4/512MiB。
- 确认 `PolicyTransport.end` 与 native Local End/Reset 的调用时序：严格模式媒体等待不能使 actor/Session 长期保持不可清理状态，尤其不能在等待模型 executor 解码时占用其执行/关停锁。若分层实现需要先确保 native/local End 安全再独立 drain，必须使服务端媒体 ticket 在 drain 完成前仍合法可 fetch，且不因 Session End 被无意取消；不能改动作、Fast Weight 和 SR 成功权威。

### C. Encoder 可靠落盘的最小协议（重要）

- 现 `MediaSink._submit()` 的 `queue.put_nowait` 会在满队列时丢视频；而客户端 `fetched_to_optional_sink` 发生于传给 queue 之后，**不等于 Encoder/FFmpeg 已完成**。对 `all` 模式改为有界 queue backpressure 和**逐个 Replan 的 Encoder 完成回执**，其身份至少绑定 `Episode/run+replan_index`，对应一条传输回执与一个完成的 MP4。
- Encoder 对单条视频编码到临时文件，完整关闭 writer（使 MP4 封装完成），成功验证已落盘后 `os.replace` 成正式 `replan_{index:04d}.mp4`；**随后才反馈 `VIDEO_SAVED(index,path)`** 给 Parent。编码失败、文件缺失、尺寸/帧数错误、文件损坏应返回明确 `VIDEO_FAILED`，不可发布误导性的最终 MP4。
- `PolicyTransport` 对服务端 `/v2/media/ack` 的确认应在**本地该 index 的 Encoder DONE 回执**之后进行，而不是传进队列立即 ACK。要防止 ACK/Parent/Encoder 相互阻塞；采用必要的独立有界状态/ACK 通道与超时保护，禁止轮询死锁、等待未注册/已退出子进程。即使网络 ACK 失败，也不能把已完成的视频丢弃；应保留状态供诊断。
- Episode 结束时，先对全部预期 Replan 索引完成序列化对账（`expected_replans == saved_and_decodable_mp4 == encoder_done_receipts`），再将媒体 drain 完成。关闭 Encoder 时**sentinel 应在正常待写队列清空/ACK 达成后发送**；不得提前发 sentinel、因2秒 `encoder_grace_s` 直接强杀尚在健康写盘的进程。若真实不可恢复失败，清理仍有界、fail-closed，并分别记录媒体不完整与 process cleanup 是否安全，不污染已提交科学 Core。

### D. 改动和验收范围不变

- 新行为严格限定 `save_generated_video: all`；`none` 不增加模型 decode/HTTP/Video 写入开销，`first` 保留既有行为。900EP 由 Owner 自行选择媒体开关，不作为本任务修改对象。
- 新测试必须包含 `spool_max_jobs=4`、`spool_max_bytes=512MiB` 的有效读取与 server propagation；满 spool、slow decode、slow FFmpeg、pending episode-end、queue full、ACK 先后与崩溃/超时、文件原子替换、其他 Session 并发，均有 deterministic CPU fail/pass。**10 Replans → 10 VIDEO_SAVED → 10 可解码 MP4；零 `MEDIA_INCOMPLETE`**。异常则明确 incomplete 并安全清理；不要求本轮真实 GPU 运行。
