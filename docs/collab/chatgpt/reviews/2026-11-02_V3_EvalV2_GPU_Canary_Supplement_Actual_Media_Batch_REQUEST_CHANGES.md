# PSM-WMA V3 EvalV2 — Hardware Canary 补证复审

- 日期：2026-11-02
- **完整 Hardware Canary Gate verdict：`REQUEST_CHANGES`（仅硬件/媒体/吞吐验收范围）**。
- **已批准的 Source Code Gate `APPROVE_CODE` 不变。** 本轮 Formal implementation pair 未变，**不重新做源码增量 Code Gate**；在原有 Evidence-only `FOLLOWUP_REQUIRED` 后仅审 DS 新提供的 Supplemental Evidence 和直接相关代码的运行契约。此项 REQUEST_CHANGES 不自动撤销历史代码评审。
- Formal Root：`4b581493db805c92964cb27e740c736db87c0329`
- Child/Gitlink：`9a8cd6183424bfce245fbca393ca25ed59919ea6`
- 隔离候选：`v3-eval-v2-render-media-20261101`，本 review/Inbox 的文档提交不改变该 Formal Pair。
- 输入：DS_PRO 2026-11-02《PSM-WMA V3 EvalV2 硬件 Canary — GPT 审查补充证据（Supplementary Evidence）》用户原文及前序 DS H1/H2/H3 自包含交付；候选实际 `cosmos_framework/inference/robocasa_batch_transactions.py`、`cosmos_framework/simulation/robocasa/eval_v2_transactions.py`、`eval_v2_adapter.py`、`scripts/robocasa_eval_v2/runtime.py`、Child `contract.py` 等直接相关真实代码的只读合约核对。远程 DS 服务器未连接；未独立执行测试、读取完整 JUnit/FFmpeg 原始视频或启动 GPU。
- Frozen Owner 目标：所有 Episode 均保存 Rollout MP4，`save_generated_video: all` **每次 Replan 的预测视频完整保留**；真实 2 Server+16 Sim M8/B2 的功能、实际批处理/并发与资源/吞吐验证；GPU 已有训练由 Owner 负责，禁止查询/管理其他 CUDA 进程，禁止碰 GPU0–3/旧 out2/No-TTT。

## 1. 当前已达成的真实硬件功能结果（DS evidence supported）

- CPU70：DS reported 70/70 PASS。
- H1 GPU4 Server → GPU6 EGL：valid1/1，EGL Context verified，视频编码与自身进程清理运行。
- H2 原配置 GPU4/5 Server → GPU6/7 EGL：**FAIL**，GPU7 EGL `read_pixels` 原生 SIGABRT；原失败不因 swap 成功而删去。
- H2 swap GPU6/7 Server → GPU4/5 EGL：valid4/4，3 successes、1 task-level failure，`results_qualified=true`、`clean_execution=true`。
- H3 swap 同一 GPU 角色，M8/B2 16 EP：valid16/16，9 successes、7 task-level failures，16 EGL Context physical proof、2 Server+16 Sim owned-process cleanup、`process_errors=[]`。此科学 SR=9/16 仅为子集 sanity witness，**不是正式900 EP/benchmark 效果**。
- DS 修正 H1/H2/H2_swap/H3_swap 四个不同 Manifest SHA，符合 Child contract 将 ordered tasks、execution GPUs/M/B、rendering GPUs/backend 纳入 digest：H1 `77174f6907eec196c6b8f1a00a8c047bdbc37d5727db39f7e4c2e928d787ac01`；H2 `f3bd9aec1541ef81d0b3d1520ffd6158fd2ba3184a527d332244ce70bde83540`；H2_swap `a72dc53a59a527fc07722957c8616edb52a19190cba16c569d21eeaed7c09ad2`；H3_swap `0ba07f178a04e6b2f90040ce5c5acd31cc4cadfee541b8ab01eee3e015fbf66e`。**EV-HW-01 CLOSED（以 DS 报告为依据，未直接读原始服务器 Manifest）**。
- 已列出 `run_canary.sh`（SHA256 `5eb3344c0e2c64c708df8bd10272ff88065c17d4a54a0f5eca62b1006a5f4ff5`）、YAML（`3a8307d25b423e5bb137e82f9e0bf120dd47ef3d532591e48ce20e93e09e74b2`）、`sg video/render`、`__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json` 等环境关键配置。EV-HW-04 作为证据提供已基本关闭，正式运行务必使用**swap 映射**而非旧示例。
- GPU7 当前环境/驱动下 EGL `read_pixels` 路径可复现首帧异常、后续原生 abort；GPU7 作为 CUDA Server 在 H3 正常。**撤回“硬件损坏”和“持续慢400x”的未证实归因**，该项措辞已 CLOSED。

## 2. 新发现 / 当前完整 Hardware Gate blockers

### HW-CANARY-MEDIA-01 — HIGH — `all` 并非所有 Replan 视频落盘，实际 80/481 未保存（真实 contract gap）

- **直接生产定位**：
  - Child `cosmos_framework/inference/robocasa_batch_transactions.py:90–93`：媒体 spool 上限 2 个待处理任务/128 MiB；
  - 同文件 `:229–242`：媒体请求在 spool 无余量时明确返回 `status=dropped, reason=bounded_spool_unavailable`，不排队保存。
  - Child `cosmos_framework/simulation/robocasa/eval_v2_transactions.py:115–117`：`save_generated_video: all` 对每次预测都**发媒体请求**；
  - 同文件 `:127–150`：`pending` 才进入拉取队列，容量亦有上限；
  - 同文件 `:209–217`：Episode 结束时将未完成任务标记 `cancelled_at_episode_end`，不会保证拉取写盘。
- **DS 真实 H3 evidence**：总 Replan `481` = fetched-to-MP4 `401` + server `dropped` `73` + cancelled at end `7`。逐任务计数自洽，`401` 个已获取 mp4 对应 `401` 条 fetched 记录；16 Rollout+401 Replan=417 MP4。但 Replan 预测视频保存率仅 401/481=83.4%，**缺80次（16.6%）**。
- **性质判断**：DS 已经清晰解释了每个缺口，“无不明文件丢失/无错误视频”可成立；**“每次 Replan 都有 MP4 / all 全量保存”不成立**。这是已批准源码的原有 *best-effort optional media* 设计与 Owner 硬冻结全视频目标之间的**新暴露的行为契约差异**，非此次 Owner GPU 资源策略的回归。不把 `results_qualified=true`、`media status=dropped` 当成科学 Core invalid；但它会阻断**全媒体交付 Gate**。
- **可验收关闭条件**：若 Owner 保持“每次 Replan 视频必须保存”，需独立窄范围 Codex 实现可靠且有界的保存/ACK/关停排空策略，严禁无限缓存、破坏 Action/Local-TTT Core、丢失清理 fail-closed；新 Formal Pair 做独立 Code Gate + DS CPU 定向测试，再作被单独授权的小规模真实有压媒体 Canary，证明 valid EP `replan_count == complete_decodable_generated_mp4_count`、`server_dropped=0`、`cancelled_at_episode_end=0`。或由 Owner **明确变更验收契约**为“每次 Replan 尽力请求，允许有界明确丢弃”，这与当前冻结目标不同，不能由 reviewer 自行默许。

### HW-CANARY-BATCH-02 — MEDIUM — 目标 B2 batching 与16并发的性能声明未实证

- **直接证据**：DS 根据 H3 `predictions.jsonl` 的 `native_batch.size` 复核：真实 `{1:481}`；**`size2=0`**。Server `session_transactions.batch_histogram` 存在真实 Counter（Child `cosmos_framework/inference/robocasa_batch_transactions.py:65–93, :146–168, :271–279`）；配置 `max_infer_batch_size=2` 仅是上限。H3 16 slots 各都执行一 EP，但 DS 根据 `ADMITTED`/episode elapsed 估计 max concurrent active episodes **约3**（准入跨度1349s），并非16路同刻运行；未提供完整时间交叠的 direct evidence。
- **结果边界**：16个物理槽都参与运行、所有Core valid+owned-clean **已证明**；“发生过 B2 实际双样本 native batch”和“16个同时活跃的满载/吞吐能力”**未证明**。真实 H3 有 `p50=2974ms`、`p95=4419ms`、`wall=1613s`、约 `35.7 episodes/hour`，这些是现配/当前 pacing 的实测，不等于充分饱和吞吐。
- **可验收关闭条件**：若完整 Hardware Gate 含真正的 B2 批处理与 16 Sim 同时并发性能目标，需在另行授权的短硬件运行中提供至少一次可复核 `native_batch.size=2` 的实际响应，以及时间轴证实的最大活跃 Sim 数和约定的吞吐基线；可先尝试现有 `batch_wait_ms` / pacing 配置调优，**不要先扩大框架改造**。如 Owner 只要求16个物理槽的配置能力而非真正同时满载/B2有效合批，须在验收说明中显式缩小性能 Gate 范围，不能把 `{1:481}` 冒充已经证明 B2。

### HW-CANARY-MEDIA-03 — LOW — “417/417可解码”的离线方法仍需明确

- DS 新报告声称 `ffprobe` 逐一确认 `417/417`；这可能只验证 MP4 容器/流元信息，不等价完整逐帧解码；报告未提供 ffprobe 的完整 flags 或 ffmpeg 全帧解码的 exit logs。
- **闭环条件**：使用既有媒体仅离线执行 `ffmpeg -v error -i <file> -f null -` 等逐文件真实解码命令并报告 exit code/坏文件清单；同时补 H2 swap 的 4+117=121 MP4 的完整媒体验证，或提供等效已经运行的原始逐帧解码证据。无需 GPU/模型重跑、不得修改原文件。

## 3. Scope 与下一步

**Gate 决定**：H1、H2_swap、H3_swap 的**GPU 角色分离、真实 EGL、真实生成/仿真、Local-TTT/Core、进程清理**功能子项报告支持成功；`HW-CANARY-MEDIA-01` 和 `HW-CANARY-BATCH-02` 当前阻断**原定完整 Canary Gate**。因此：**`REQUEST_CHANGES`**（Hardware scope only; source-code `APPROVE_CODE` historical unchanged）。不是否定已完成的 16/16 有效 Episode，也不要求撤销先前硬件结果。

**当前只授权/建议**：
1. DS 可从现有文件补 Media full-decode evidence，不额外跑 GPU。
2. 如果 Owner 坚持全 Replan 视频，则下一工作应聚焦 Codex 狭义修复 bounded media retention/delivery，再走新 Formal Code Gate；不要增加新的大型架构。
3. 实际 B2 与 16 活跃的 witness 须在新 Owner 授权后做最小硬件压力 Canary，不能仅凭当前 H3 自评宣告达到。
4. 暂不批准正式 18×50=900 EP、正式 V3 merge 或旧 `out2` Resume。现有 GPU4–7 上其他训练继续运行，GPU0–3 不参与，不查询外部 CUDA 作业。
5. 当前补证是**同一个原 Formal Pair**，故只做 Evidence 增量复核与持久化；不能因该证据报告再次给相同源码做技术重审/新版 `APPROVE_CODE`。
