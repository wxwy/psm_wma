# PSM-WMA V3 — Issue #11 No-TTT Async Overlap DS_PRO 独立301 CPU Evidence 增量审核

- 日期：2026-10-29（Asia/Shanghai）。类型：**新增 DS 运行证据审核；不是同 Formal Pair 源码重复审核。**
- **精确 Formal Root：`e0fe911dfb9fd34957234828195cf051713f6c3d`；Child/Gitlink：`f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`。**
- 已有同 Pair 独立 Code Gate：`APPROVE_CODE`；见 `docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_AsyncOverlap_e0fe911d_f6a92d47_Incremental_Code_Gate_APPROVE_CODE.md`。本轮正式源码版本未变，**该 Code verdict 保持，不重新跑 Code Gate**。
- DS 请求：`docs/collab/chatgpt/requests/2026-10-29_V3_NoTTT_AsyncOverlap_DS_PRO_Independent_CPU_ExactPair.md`；[Issue #11](https://github.com/wxwy/psm_wma/issues/11)。
- **本轮证据材料来源**：2026-10-29 用户粘贴的完整《DS_PRO 独立结果 — Issue #9 No-TTT Async Overlap 301 CPU Gate（精确 Pair）》；DS 的原始 `/tmp/dspro_nott_async_e0fe911d_f6a92d47_UNIQUE/evidence/` **仅在其训练服务器上**。GPT 实际尝试访问既有 Remote Desktop 连接，结果 **Offline**；当前 GitHub Issue #11 也尚未包含该轮原始 DS 文件。以下区分 **DS 现场报告的事实** 与 **GPT 实际已回读的权威仓库文件**，不伪称直接核对服务器 raw XML/trace/Checkpoint/进程。
- **Evidence disposition：`DS_CPU_PASS_REPORTED / REPORT_CONSISTENT / RAW_BYTES_NOT_YET_REVIEWED`。不写成 GPT 独立验证了全部原始 artifact 的 `PASS`。** 这是最低限度证据归档待补，不是另行要求重跑测试。旧 Formal Code Gate `APPROVE_CODE` 继续成立。

## 1. 身份和不重审原则

- GPT 已核对 V3 最新源码索引：当前正式主干 V3 仍未吸收该候选 Child；精确候选 Root commit `e0fe...` 的 Gitlink 指向 `f6a92...`，Child commit 可见。此前 Code Gate 的18/18 source Git Blob逐项比对结果保留，**Formal Pair 未变**，不重复源码审核或原有作者301项测试。
- DS 报告其独立清洁 detached Worktree 的 Root/Child/Gitlink 三项精确一致，原始环境 Python3.13.11、torch2.10.0+cu128、pytest9.0.2、Ruff0.12.7，CUDA隐藏、完全离线、外部独立 Evidence 目录；这些运行环境字段尚无GPT直接读到的 `environment.json` 字节可核验。

## 2. Evidence contract — DS 报告内容与完整性

| 冻结要求 | DS 独立报告结果 | 审核范围 |
| --- | --- | --- |
| exact pair + clean + import_origin | Root/Child/Gitlink一致，双 worktree无dirty，import origin exit0 | 报告一致，raw日志待回读 |
| 72新 async + 229 regression | `301 tests, 0 failures/errors/skips`；原Gate `status=PASS`，shell0 | 报告一致，raw `gate.json` / JUnit待回读 |
| 子项计数 | async = 29 loader +19 recipe +24 trainer =72；regression=52+13+29+15+11+40+20+49=229 | **算术和冻结suite集合一致**，并非新测试 |
| 明确排除真实数据 | `test_optional_real_data_debug_smoke` `NOT_RUN`，不计通过 | 符合本CPU-only Gate范围 |
| 不更改冻结源码 | `source_unchanged=true`；Ruff/format/AST13全部exit0 | 报告一致；直接hash待回读 |
| 真实spawn/时序 | 3 Windows、2个owned worker PID≠trainer PID；192 Source+Transform事件；next-Member Source87.80ms/Transform128.97ms，next-Window Source20.46ms/Transform32.39ms | **DS声称按其独立 raw trace重算**；GPT未见本轮trace原件，不能复制作者旧timeline数值替代 |
| full/terminal/4 logical ranks | GA4 B8 T16，Packed128 / partial顺序与CPU等价 | 对应前序已核查测试源码；DS新运行为报告 |
| RNG/Frontier/Resume合成证据 | `0→8/8→0/8→8` 同Job训练语义、失败不提前提交、worker crash/timeout/foreign隔离 PASS | 合成 CPU 合同成立（报告级）；**非真实DCP/CUDA Resume** |
| 原正式Job | DS现场只读ps见证正在运行原Job，实际CLI `--no-ttt-loader-workers 8`、训练GPU4–7仍被占用；不动其进程/代码/Checkpoints | 用户/DS提供的现场信息，非 GPT 在线独立进程见证 |

## 3. 重要更正与结论限制

1. **原正式Job并非当前 `nw0`，而是已经运行 `nw8` 的旧 `NoTTTCpuLoader` RAW后台路径**。新候选同样选 `nw8`，但会切换为 **Source+Cache+Transform + Cross-Window preview**；同时计划启用 `Compact=1`。`nw8`值相同绝不代表运行时行为相同。
2. 旧 Job `no_ttt_packed128_droid_fresh_30k_world4_ga4` 正在真实训练且 `--formal-execution-until 30000`，不允许在它仍活动时启动第二个同Job Resume，也不能在这个只读DS报告下停止训练。
3. **CPU overlap != GPU overlap/throughput PASS**：本报告的 `fake GPU` 只是CPU回调，未衡量CUDA stream/GPU idle；之前作者CPU cold test甚至出现async7.761s > serial3.315s，不能预设nw8优化必然提升Wall。
4. 旧 Compact0↔1严格GPU Gradient Parity `FAIL_PARITY`，Dense0→Dense0 reference repeatability也FAIL；Compact归因 `INCONCLUSIVE` 仍保持原结论。不可因新独立CPU报告覆盖或宣布PASS。
5. 此次无实机数据、真实Tokenizer、DCP、CUDA、训练级Resume、正式代码合并或任何实验启动。

## 4. 唯一证据补全动作（只读复用，不得重跑）

请 DS_PRO 通过**独立Evidence-only Git分支或其它可供GPT直接读取的方式**发布该次现成 raw：`gate.json`、`async.xml`、`regression.xml`、`environment.json`、`source_sha256.json`、`timelines/overlap_trace.json`、如已有可附`evidence_files.sha256`及最小脱敏stdout/README。冻结本轮目录/字节并保留sha256，避免增补数据冒充已冻结执行。不得将作者 `locked03` artifact 作为 DS 原始数据。**不需要重跑任何 CPU 测试，不需要额外训练/探针。** 不在活动训练工作树执行Git操作；保留DS现有本地未推送提交，禁止强推/reset/覆写。

收到可读原件后，只增量核对 XML真实计数、gate statuses/identity与source unchanged、trace时间交集/worker PID和原始hash，形成最终 Evidence Closure。没有新 Formal Pair，不进行源码重复审核。

## 5. 下一步 GPU/Resume（尚未授权）

准备 `docs/collab/chatgpt/requests/2026-10-29_V3_NoTTT_AsyncCompact_Real_DCP_GPU_Qualification_Proposal.md`：先确认旧正式Job有完整合法 DCP/4rank sidecar，隔离复制同一 frozen Checkpoint；在 Owner 明确安排空闲 GPU4–7、许可实验资源/持久日志后，使用隔离 Clone/Root+Child，对 `Compact=1,nw0` vs `Compact=1,nw8` 做匹配 Resume+真实吞吐测试，同时以现有 oldnw8历史数据作信息性背景（非严格matched）；真实worker RAM/tokenizer/local assets和DCP/CUDA RNG须验收。

只有当在新候选真实GPU的 Source+Transform预取、恢复与训练健康都通过，才可由Owner另行授权原正式Job在完整Checkpoint边界切换新代码。此报告和GPT本轮审核**不授权GPU实验/正式Resume/停止训练/合并V3/更新Child Gitlink**。
