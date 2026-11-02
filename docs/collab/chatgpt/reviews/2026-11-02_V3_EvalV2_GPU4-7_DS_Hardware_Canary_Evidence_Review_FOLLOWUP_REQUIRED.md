# PSM-WMA V3 EvalV2 — DS_PRO GPU4–7 Hardware Canary 独立 Evidence 审核

- 审核日期：2026-11-02
- **Evidence status：`FOLLOWUP_REQUIRED`（证据项，仅补交报告/离线校验，不要求重跑 GPU）**
- **原有正式 Code verdict：`APPROVE_CODE` 保持不变，不执行第二次相同 Formal Pair 源码审核。**
- Formal Root `4b581493db805c92964cb27e740c736db87c0329` / Child-Gitlink `9a8cd6183424bfce245fbca393ca25ed59919ea6`。
- 候选：`v3-eval-v2-render-media-20261101`；review/Inbox commits 仅为文档 bookkeeping。
- 已存在 Owner 一次性 CPU70 + H1/H2/H3 Canary 授权：`docs/collab/chatgpt/reviews/2026-11-01_V3_EvalV2_Owner_Authorization_DS_CPU70_and_GPU4-7_Canary.md`。
- 审核输入：Owner 上传的 DS_PRO 自包含报告 `DS_PRO — EvalV2 GPU4-7 Hardware Canary — Delivery to GPT/Owner`（截至 2026-11-01），以及只读核对的候选真实 `identity.py`、Child `contract.py`、`runtime.py`、Child `store.py` 的相应 Evidence contract。DS 原始 JUnit/完整 MP4、运行时间序列位于 DS 服务器 `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_cpu70_acceptance/`，**未通过当前会话独立远程读取**：所连 Desktop Commander 设备当前 Offline。本轮未跑测试/未访问 GPU/未改变任何训练或 Run。

## 1. 可接受的 DS 报告结论与严格边界

| Stage | DS reported | Evidence assessment |
|---|---|---|
| CPU70 | 70/70 PASS；Ruff/format/compile pass；Root/Child clean | 作者以外的 DS 独立执行，按自包含报告可接受；原始 JUnit 当前未直取 |
| H1 原配 GPU4 Server→GPU6 EGL，M1/B1 1×1 | Core 1/1 valid、Context proof true、H.264 rollout +19 replan、owned clean | **单卡 EGL/真实 Media 功能成功（report-supported）** |
| H2 原配 GPU4/5 Server→GPU6/7 EGL，M2/B2 4×1 | GPU7 关联 `read_pixels` SIGABRT；1 valid/3 invalid；results_qualified false | **FAIL 必须保留，不以 swap 覆盖失败历史** |
| H2 角色交换 GPU6/7 Server→GPU4/5 EGL，M2/B2 4×1 | 4/4 valid、3 success、1 task failure、EGL proof true、clean | **交换角色后的功能成功（report-supported）** |
| H3 角色交换 GPU6/7 Server→GPU4/5 EGL，M8/B2 16×1 | 16/16 valid、9 success/7 task failure；16 Context proof、2 server+16 Sim close evidence、process_errors=[] | **M8/B2 配置的端到端功能成功（report-supported）**；该 16-EP 子集 SR 不构成正式 900EP/科学效果结论 |

角色交换后的映射是当前实证有效配置；目标 GPU7 不适合在此环境担任 EGL Render 的结论有依据，但 **“GPU7 实体硬件/驱动确定坏了”与“400×慢”不可仅凭给定帧/启动时间、SIGABRT 推出**。应写为“GPU7 EGL 路径可复现异常，底层原因尚待系统/驱动进一步隔离”；CUDA server 路径在 H3 正常。对已有可行 workaround 不要求新增代码修改。

## 2. Evidence-only blockers（非 Production blocker）

### EV-HW-01 MEDIUM — Manifest digest 归属矛盾

DS 报告 §1 将 H1/H2/H2_swap/H3_swap 的 Manifest digest 合并写为单一 SHA `a72dc53a59a527fc07722957c8616edb52a19190cba16c569d21eeaed7c09ad2`。但真实 `scripts/robocasa_eval_v2/identity.py:173–181` 将每阶段的 task list、episodes、`execution(cfg)`、`rendering(cfg)` 传给 Child `cosmos_framework/evaluation/robocasa_v2/contract.py:75–146`，其 digest 包含 `gpu_ids`、`sims_per_gpu`、`max_infer_batch_size`、render roles 和 tasks。因此 **H1、H2 原配、H2 swap、H3 swap 的 Manifest digest 不应完全相同**，除非报告中的摘要误用了一个 Run digest 或存在更严重的实际身份/记录错误。

**闭环条件**：DS **离线只读**从四个独立目录的真实 `manifest.json` 和 `summary.json` 导出每 Run 的 manifest digest、ordered Task list/数量、execution、rendering、源 SHA；逐 Run 核对 manifest digest 与对应 summary 完全相同、相互不同。把报告中“各阶段 digest”纠正为实际四个 digest。若四份真实 Manifest 竟同 SHA，作为新的 High identity anomaly 报 GPT/Owner，不准宣称正式实验归属可靠。

### EV-HW-02 MEDIUM — 全媒体闭环的逐文件证据欠缺

授权的 H3 要求“全部 Rollout MP4 + 所有 Replan Predicted MP4”完整且可解码，与 prediction/replan 记录逐个配对。现 DS 报告仅给出 H1 单条 rollout ffprobe 和 H2/H3 文件计数。H3 列出的 16 个 Replan 数量累计 **401**；连同 16 个 Rollout，预期 **417 个 MP4**。目前不能仅由 `summary.results_qualified=true` 推断 417 文件全部可解码：真实 `store.py:1187–1206` 该标志根据 valid Core/未解决进程错误/worker streams 计算，不是逐个 MP4 解码审计。

**闭环条件**：无需重跑模型/GPU；DS 在现有 `H3_swap` 中离线检查 16 Rollout 和 401 Replan 视频真实存在、非零、能由 ffmpeg 完整解码（或既有同等逐文件完整解码证据）、每任务 Replan 编号/文件数量与真实 prediction JSONL 逐条一致，并输出 compact CSV/JSON 摘要、坏文件清单（预期空）。H2_swap 同理，4 Rollout + (20+32+47+18)=117 Generated = **121 MP4**。如已有原始媒体完整校验证据，引用即可。不得修改原视频。

### EV-HW-03 LOW-MEDIUM — 并发与吞吐仅报告计数，不是运行量化

H3 列出 16个 Simulator log、16 Context、18 条 owned cleanup（2 Server+16 Sim），足以证明16个物理 Slot 参与；但没给出进程**实际时间重叠/最大同时活跃数**、`batch_histogram` 的 B2真实命中及 p50/p95、Stage walltime/EP/h。源码 `scripts/robocasa_eval_v2/runtime.py:768–796` 已收集 `batch_histogram`，native `batches` 值(282/198)不能证明任何 size-2 batch 已发生；`queue_high_water=1` 也不能替代 histogram。

**闭环条件**：只读取已有 H3 Server/Sim timestamps、`_internal/batch_status.json`、Server `/info` 或日志中原始 batch histogram / latency / walltime，报告 max_active_sims、size1/size2 batch 分布、effective batching、p50/p95（若数据存在）、end-to-end 时长 / EP/h。自有峰值显存若无已有可复核 telemetry 则标 `not-measured`，不查别的训练任务、不可猜数值。如无充分 overlap/histogram 证据，描述降级为“16 Slots 有效完成，M8/B2 参数配置已生效，实际 B2 利用率未验证”，而非虚报 B2 已实际加速。

### EV-HW-04 LOW — 临时运行包装器需保留复现信息

DS 报告 `canary/run_canary.sh` 带 `sg` group 包装、强制 NVIDIA EGL vendor 环境，现仅列出脚本名。这类外部环境安排是实际 H1/H2/H3 能否复现的关键变量，但不是 production bug。请保存脚本 SHA256、最终解析 YAML、三解释器路径、EGL vendor 环境变量、DRM/group 权限以及确切 H1/H2/H3 命令（可脱敏），确保以后正式900EP 使用经验证的 GPU角色和执行条件。无需修改 EvalV2 生产代码。

## 3. Gate 处理和下一步

- **Source Code Gate 仍 `APPROVE_CODE`；RM-M01/Owner GPU policy 已审已闭，不重审，不派 Codex 改生产代码。**
- **Hardware Canary 的基础功能链路取得重要正面实测证据；全量 Hardware Evidence Gate 当前 `FOLLOWUP_REQUIRED`（仅 Evidence-only），不把 DS 的自评直接转换成无条件 Formal Gate closure。**
- 立即下一步：DS_PRO 从**已有数据离线生成一个短补充 Evidence**，按 EV-HW-01/02/03/04 纠正 digest、做媒体对账、给 batch/concurrency 指标、冻结运行脚本。无需进一步 GPU Run、无需额外架构/测试，原 H2 FAIL 保留。
- 未获得 Owner 新授权，不执行 900 EP、V3 生产分支合并、旧 out2 Resume、No-TTT 工作改动；GPU0–3/其他训练任务完全不触及。
