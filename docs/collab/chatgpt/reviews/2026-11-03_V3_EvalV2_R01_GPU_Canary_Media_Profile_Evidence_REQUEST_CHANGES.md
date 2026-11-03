# PSM-WMA V3 EvalV2 — R01 真机型 GPU Canary 证据审查（Media Summary Profile）

- 日期：2026-11-03
- Gate：R01 严格 `save_generated_video=all` 单 Task ×1 EP 真实硬件 Canary
- **Evidence Gate verdict：`REQUEST_CHANGES`（R01 hardware/media-summary；不是新 Formal Source Code Gate）**。
- 原 Formal Root `e7ce99d7a0bbb7a81ea7afcee7253548687dc223` / Child-Gitlink `c93f2abf4fb27d36176ff8db094379a853cec796`；隔离候选 `v3-eval-v2-replan-ack-r01-20261102`。该 Formal Pair **未变**，按审核规范不重复旧 Code Gate，也不重新运行旧122/379测试。先前 `APPROVE_CODE` 和 `DS_INDEPENDENT_PASS` 分别记录原 Code/CPU 范围，不会把本次真实 GPU Fail 变成 Pass。
- 数据来源：DS_PRO 在会话中提交的《R01 GPU Hardware Canary — Evidence Report》（2026-11-03）；本轮直接从该精确 Root SHA 读取 `scripts/robocasa_eval_v2/{config.py,generated_media.py}`，从精确 Child SHA 读取 `cosmos_framework/evaluation/robocasa_v2/contract.py`，并核对 Root `tools/v3/eval_v2_replan_tests/report_test.py`。**DS 服务器 R01 原始 out/ / MP4 /日志未被 GPT 远程直读，19条视频、回执/ACK/清理及耗时属于 DS 报告支持，不能冒称 GPT 亲自运行或逐帧解码。**

## 1. R01 硬件证据结果（独立区分 Core、Media runtime 与 Aggregator）

- DS 报告新 R01：Phase B，GPU6 Action Server + GPU4 EGL Simulator，M1/B1，CloseFridge×1 Episode，`iter_000020000`，`save_generated_video=all`，每 Server 4jobs/512MiB，`media_drain_timeout_s=300`。未修改 production，未合入 V3。
- **科学 Core/SR：报告支持 PASS**：`summary.status=complete`、valid1/1、success1/1、`results_qualified=true`、`clean_execution=true`、无 process errors，304 steps，19 replans，81.79s。
- **Media runtime：报告支持 19/19 完整保存与 ACK**：19 MP4、19 `VIDEO_SAVED` receipt、19 server ACK；`media_diagnostics` drop0/error0，Episode completion `COMPLETE expected=saved=acknowledged=19 missing=[]`，Encoder、feeder、Simulator/Server 关闭正常，无残留进程。DS `ffprobe` 结果 `H264/320×160/17帧`（容器/流探测）；严格视频生成源码的正常 `write_generated` 路径包含逐帧解码校验，因此收据提供额外完整性证据；仍不能将 DS 的 ffprobe 声称等同于本审核员额外重做逐文件完整 decode。
- **Aggregator/CLI：明确 FAIL**：`R01_FRESH_EXIT=1`，`media_summary.json.status=MEDIA_INCOMPLETE`、`saved=acknowledged=0`；该0来自汇总校验提前失败，**不是**实存 MP4 数量。
- **Gate**：Owner 冻结通过标准包括 `media_summary.status=COMPLETE` 与成功退出，因此严格整体 `R01 Hardware Canary FAIL`；只把 runtime behavior 标记为 report-supported functional success，不强行放宽 Gate。

## 2. 新发现唯一 Production blocker

### R01-MEDIA-PROFILE-01 — **MEDIUM / Production** — Coordinator 将原生 Phase B Manifest profile 与 CLI 配置 profile 混用

- **真实源定位**：Root `scripts/robocasa_eval_v2/config.py:244–254` 的 `execution(cfg)` 在 `execution_profile=phase_b` 时返回 `{"profile":"phase_b_native_batch_v1", ...}`；Child `cosmos_framework/evaluation/robocasa_v2/contract.py:107–115` 要求 native execution manifest 的精确 `execution.profile` 等于 `"phase_b_native_batch_v1"`。
- Root `scripts/robocasa_eval_v2/generated_media.py:27–46` 读取 `completion.server_ack_required`（本 R01 `true`）并与 `store.manifest.get("execution",{}).get("profile") == "phase_b"` 比较；真实 Phase B 上判断**必定 false**，导致 `True is not False`，立即抛 `ValueError("MEDIA_INCOMPLETE: generated completion/count binding")`。其 `:47–67` MP4库存、收据 hash/Identity校验**因前置误判而未运行**，成功媒体累计为0，输出误报。
- **Frozen violation**：`save_generated_video=all` 时所有合法 `VIDEO_SAVED` & ACK 且回执/库存完整的 Episode 应使 `media_summary.status=COMPLETE`，CLI 不能把合法 Phase B 报成媒体缺失并 exit1；媒体诊断与 Core/SR 独立性要保留。问题是生产 summary 校验，而非网络 spool/Encoder/GPU7 EGL/Action/Local。
- **检查到的 test coverage gap**：Root `tools/v3/eval_v2_replan_tests/report_test.py:24–67,70–113` 的 positive `publish()` fixture 建的是**无 Phase B execution manifest 的 Store**，`server_ack_required=false`；测试 `wrong_ack_authority=true` 反而被设计成负例。缺少真正的 `execution.profile=phase_b_native_batch_v1` 且 `server_ack_required=true` 的正例，所以 CPU379/122 未检测到。
- **裁决：Production blocker confirmed**。单一、明确的配置口径错误，修复应最小化。已归档的相同 Formal Pair 的 CPU Code PASS 不足以关闭当前真实 R01 Canary。

## 3. 给 Codex 的最小整改与离线验收

**修复范围**：只改 Root `scripts/robocasa_eval_v2/generated_media.py` 的 Phase B/ACK 校验来源，复用规范已冻结的 Native manifest literal `"phase_b_native_batch_v1"`（或 Child contract 的同源 authority），不要拿 CLI 字符串 `"phase_b"` 与 Manifest 比较。不放宽 `server_ack_required` true/false 型别和其余 MP4 receipt/哈希/身份/数量校验；若需要严格验证 unknown profile，应 fail-closed。子模块生产代码不需要改变，Child/Gitlink 不得因重建变动。
**测试**：新增或增强 `tools/v3/eval_v2_replan_tests/report_test.py` 的**真实 manifest** Phase B 正例（`server_ack_required=true`，有效媒体 inventory/receipt，`publish(...).status=COMPLETE`，并检查假 `server_ack_required=false` → `MEDIA_INCOMPLETE`），Phase A/absence 正例 `false` 继续通过。至少该新测试旧 Root RED，新 Root GREEN；定向 CPU、Ruff、format、syntax 及旧相关回归；无须重做整套旧379/122/独立 CPU122。
**预验证**：在不改、覆盖、删除原 R01 `out/R01` 任何字节的前提下，用新代码对**独立拷贝**的既有 R01 输出离线重算 `media_summary`，并执行其 MP4 Inventory、19个 Receipt、SHA/Identity 校验及可选全帧解码（`ffmpeg -v error -i ... -f null -`）。不得只手工把 status 从 FAIL 改为 COMPLETE，也不得覆盖旧 `media_summary` 与旧 `R01_FRESH_EXIT=1`；如果离线汇总仍失败，逐项给真实 source/path 证据。
**之后**：新 Formal Root+Child/Gitlink 提交、GPT fresh Code Gate，再 DS 独立少量 CPU。是否需要重复1EP真实 GPU 由 Owner 决定；可以先用离线验证尽量避免 GPU 重跑。未授权任何GPU新Run。
- Codex 只修改隔离分支（另开新补丁候选优先）；**不合并官方 V3、不启动 GPU 或900Episode、不动 GPU0–3 或正在运行训练、out2/No-TTT/H2/H3/旧 R01 产物或历史证据**。
- 不将既有旧 R01 记录“FAIL”擦除；新 SHA 的结果与离线重算分别独立保存。

## 4. 额外备注（不作为新 blocker）

- DS 报告测得 Episode81.79s、last prediction稳态约1.3s、首推理13.6s、spool峰值1；**没有给出单独的 encode/decode/verify/fsync/ACK 墙钟分解**。这项性能 evidence 后续有已有日志可读则提供，若无记录就标 unavailable；不要臆造延迟、为了单纯性能仪表另起架构改造。
- DS 提到“ffprobe 全部可解码”，更准确是报告每文件有被 ffprobe 识别的正常视频流；严格路径成功 Encoder receipt 在源码层有全帧检查，原始 MP4 可后续由 DS 在隔离只读校验中全帧再核对。
- 真正 R01 Canary 不是 Code Gate，也不自动批准 900EP 或正式 V3 合入。

**最终 Verdict：`REQUEST_CHANGES`（R01 GPU Canary Evidence Gate；单一 confirmed production blocker R01-MEDIA-PROFILE-01）**，原 Formal Pair 未变无需重做上一轮技术 Code review；下一实施提交必须形成新 Root SHA 后 fresh incremental code review。
