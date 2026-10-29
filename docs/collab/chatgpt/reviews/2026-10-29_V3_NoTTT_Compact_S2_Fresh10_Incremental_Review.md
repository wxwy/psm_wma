# Compact=1 No-TTT S2 Fresh10 — 增量执行报告审核

- 日期：2026-10-29（Asia/Shanghai）。
- **正式 verdict：`ACCEPT_S2_FRESH10_REPORT`。接受 fresh 连续训练验收 `PASS_FRESH_CONTINUOUS_10`；实际 Resume 仍未执行。**
- 本轮只审新增执行证据，不重审未变的生产代码，不改写严格 Gradient Gate。
- 输入：[DS_PRO 会话提交报告](../evidence/2026-10-29_V3_NoTTT_Compact_S2_Fresh10_DS_PRO_Submitted_Paste.md)。本轮证据层级为 **Owner 提供的执行报告**，不是 GPT 对服务器原始日志或 checkpoint 的独立数值核验。
- 上轮授权：[S2 至 iter10](2026-10-29_V3_NoTTT_Compact_Parity_Disposition_and_S2_Resume10_Authorization.md)，commit `9cc37557a538d5c9df29923aa069c5c17400f119`。Owner 后续明确“被我清理了，授权 fresh 重建”，并指定新 Job 名；本轮接受该覆盖指令，不再用旧执行文件的禁止 fresh 条款否定本次运行。

## 1. 身份与本轮独立核查范围

历史 No-TTT 实施基线为 Root `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9` / Child `746c5cf2f2324104a62fb71510343aa40d3976c5`。

本轮锁定读取远端 V3 HEAD `0f655489cd04062d72ecdd3cf6bb6baee5888796`；其父提交是 `9cc37557a538d5c9df29923aa069c5c17400f119`，新增内容属于另一条 EvalV2 审核线。远端 tree 的 Child/Gitlink 仍为 `746c5cf2f2324104a62fb71510343aa40d3976c5`，No-TTT launcher blob 仍为 `dd786c9938826124caf6ef01b48ea7805754bb84`。本轮不更改 EvalV2 的结论。

DS 报告的运行身份占位值为 `nott_world4_ga4_source_head_not_verified`。这表示现场 Root/Child SHA 未核实，不能把历史 pair 或本轮远端 HEAD 冒充该次运行的实测源码身份。现有 No-TTT launcher 与 Owner 指令已豁免这个 profile 的 clean/HEAD/Gitlink 硬门，因此不重新引入该阻断条件。

GPT 实际完成：读取当前远端 tree、canonical Inbox、既有授权与 launcher；审查本轮完整报告；从表内已舍入数值计算描述统计；独立交叉审查结论。未执行 PyTorch、GPU、训练或模型测试。当前连接的 Remote Desktop Commander 设备返回 Offline，未能回读 DS 现场文件。

截至上述锁定 HEAD，远端没有本次 fresh 的原始 `launch.log`、`train_rank0.jsonl`、`launch.json`、identity、complete marker。DS 所述本地 4 个未推送 evidence commit 的 SHA 和完整 diff 尚未取得。本次只归档报告正文及审核，不能宣称这 4 个提交或全部现场原件已归档。

## 2. 接受哪些执行结论

以下均以 DS 提交报告为事实来源，接受其在相应范围内的执行结论。

| 验收项 | 接受的结论 | 范围说明 |
| --- | --- | --- |
| 执行变体 | Owner 授权的 fresh 重建 | 新 Job `no_ttt_compact1_corerun_fresh_20261029_world4_ga4`，不等同于原 Job resume |
| 真实训练链路 | 4 卡 FSDP2、GA4/B8/T16、No-TTT、Compact=1 连续迭代 | Base warm-start 于 iter0；iter1–10 共 10 次 `optimizer_committed` |
| 健康 | 报告的 rank0 十步均 294 梯度、0 missing、0 nonfinite、无 telemetry errors | 不扩写为四 Rank 全部梯度逐值核验，也不证明数值等价 |
| 停止边界 | total iter10 完成并正常退出 | 报告 `SUCCESS Done with training.`，没有继续至100/30k |
| 保存 | 报告 iter10 complete=true、world_size=4、latest 指向 iter10，13 个 distcp 文件大小一致 | 支持保存完成；元数据含 SHA 不等于 GPT 已重算 SHA，更不等于实际恢复成功 |
| 训练语义 | max_iter30000 / warmup500 / save_iter100 / workers0 保持 | 执行边界保存 iter10 不意味着 save_iter 被改成10 |
| 共存 | DS 报告旧正式 Job 未被本次触碰且继续推进 | 不推导零性能干扰或每卡显存余量 |

Loss 在 14.2702–14.9375 之间波动，梯度范数报告有限。没有要求 loss 在十步内单调下降，也不能据此宣称训练已收敛。本轮报告没有给出新的 Compact 特有生产缺陷证据。

## 3. Fresh PASS 与 Resume 状态分别记账

报告标题和正文已说明 fresh；第6节的 `S2=PASS（fresh 重建变体）` 应在协作账本写成明确的分项状态，避免后续误读。

| 状态 | 本轮结论 |
| --- | --- |
| `S2_FRESH_CONTINUOUS_TRAINING` | `PASS_FRESH_CONTINUOUS_10`（接受 DS 提交报告） |
| 原 S1 checkpoint 的 S2 Resume | `BLOCKED_BEFORE_RUN`；Owner 已清理原恢复点 |
| 新 Job iter10 checkpoint 的实际 Resume | `NOT_EXECUTED` |
| 本轮现场原件独立核验 | `REPORT_ONLY_RAW_NOT_READ_BACK` |
| `GPU_STRICT_GRADIENT_PARITY` | `FAIL_PARITY`，保留历史结果 |
| `REFERENCE_REPEATABILITY` | `FAIL_AT_FROZEN_TOLERANCE`，保留历史结果 |
| `COMPACT_SPECIFIC_REGRESSION` | `INCONCLUSIVE` |
| 完整输入／输出等见证 | 原 OPEN 子项保留；不新增启动前置条件 |
| 30k 执行范围 | `NOT_AUTHORIZED_BY_THIS_REVIEW` |

Fresh 连续 commit 和 checkpoint 写出已提供有用工程证据。仍未测的具体行为是：从本新 Job 的训练 checkpoint 恢复 model、optimizer、scheduler、trainer 及生产数据 frontier/sidecar，并产生下一次真实 optimizer commit。Base warm-start iter0 不能覆盖这个行为。

CPU Parity 已 CLOSED；F1 生产冻结、F2 formal PASS predicate 已关闭。无需重跑 CPU、Fresh1、Fresh10，或重复一个 Dense→Dense 自己也失败的严格 GPU allclose。未测的 local-memory、aux、param_norm 等字段继续 NOT_MEASURED，不为补可选指标改训练或补跑。

## 4. 性能与报告口径

对报告表中已舍入的十步数据作直接算术统计：wall 合计约203.2秒、均值20.32秒、中位数20.00秒、范围17.9–23.3秒；data_prepare 均值5.54秒、中位数5.40秒。仅 iter2–10 的 wall 均值约20.24秒，data_prepare 均值5.40秒。

这些是当前共存运行的十步描述，不是重新解析原始 JSONL 的高精度统计。本轮没有同时段 Dense 对照，不能生成新的稳态加速比，也不能把历史 Fresh1 的1.87倍直接外推成长训收益。

两项文案需在后续原件归档时轻量澄清，**不构成本轮运行 FAIL，不要求重跑**：

1. **显存时间和指标。** 32.17 GiB 是新 Job rank0 的历史 peak_reserved，35.66 GiB 是旧 Job rank0 的报告峰值；不同进程的历史峰值不能当成同一时刻每卡总占用。报告的“每卡空闲43–46 GiB”缺少采样时刻与指标来源，与“两项峰值相加即每卡占用”的解释也不一致。保留本轮 rank0 峰值与 DS 报告无 OOM 的事实；有现成 nvidia-smi 记录则补时刻和指标，没有就把余量标为未核实，不增设空卡或磁盘 Gate。
2. **时间标记。** 报告声明 CST，临时日志文件名带 `20261029T091427Z`；仅凭文件名不能确定正文09:14使用哪个时区。请标注日志实际时区，无需调整或重跑既有训练。内部时长一致：09:18:12→09:21:36约204秒，与203.2秒表格合计相符；随后约16秒到退出，与报告16.257秒 checkpoint 保存接近。这是内部一致性检查，不是独立原件证明。

## 5. 下一步技术建议：一次实际 Resume，进入既定训练目标

**从工程上建议继续；不新增 11→20→100 的多轮验收。** 连续训练十步已测，新增信息集中在实际恢复行为。

建议 Owner 将同一新 Job 的执行范围一次扩大到总 iter30000。用 `resume 30000` 恢复本 Job 最新合法 checkpoint；按当前报告应从iter10恢复，首个新增commit为iter11，之后沿原调度继续。真实 restore、iter11 与既有健康监测作为该次续训早期检查；实际报错则停本新 Job，成功则按已授权范围继续，不再为iter20或100索要额外审核。

资源与语义保持 GPU4–7、world4/GA4/B8/T16、Compact1、workers0、max_iter30000/warmup500/save_iter100。旧正式 Job 与 Owner 管理的存储策略保持原有安排。输入见证可按既有许可低成本并行补证，仍不是启动前置条件；若查出真实有效输入错误或实际运行异常，则作为新问题处理。

完整可审核的拟执行 payload 见 [Resume 至30k 提案](../requests/2026-10-29_V3_NoTTT_Compact_FreshJob_Resume30k_Proposal.md)。**该文件状态 `PROPOSED_NOT_AUTHORIZED`。** 旧授权和 Owner fresh override 均止于总iter10；本报告提交不自动扩大执行范围，本轮未启动续训或发送执行消息。

如果 Owner 暂不接受长期残余风险，验证唯一剩余恢复行为只需一次从10到11的真实 Resume；它是可选较小范围，不是必须先过的一道 Gate。

## 6. 归档与本地分叉处理

本轮文档提交直接基于当前远端 V3，保留远端新增 EvalV2 review；只新增报告、审核、续训提案及 append Inbox，不操作 DS 的活动工作树。不能据此说 DS 本地分叉已经合并。

本地4个 evidence commit 应先记录 SHA 与路径列表、保留原提交，再在独立归档分支／工作树基于最新 V3 仅整合实际证据文件。普通 Inbox 冲突只保留双方内容并追加；遵守128KiB rollover规则。未经检查不整批 cherry-pick，不强推、不 reset、不在活动训练工作树 merge/pull。这个归档问题不应改写运行 PASS 或变成训练数值 Gate。

补齐现成原件只需关联 launch.log、十步 train_rank0.jsonl、launch.json、identity、complete marker/latest，以及已有 BLOCKED 报告与本地commit身份；无需重新执行实验或全量搬运模型 checkpoint。取得原件后做相应增量核对，不重新发起生产代码审核。

## 7. 本轮交付边界

本轮验收报告、记录状态和准备后续提案；提案命令仅做 `bash -n` 与内嵌 Python AST 静态语法检查，均通过，未执行 payload。无生产代码、测试、配置、Gitlink、checkpoint或清理策略修改，无GPU／训练执行。Owner决定是否把同一新Job的范围从10扩到30000；实际Resume结果在该次启动后据实登记，历史严格FAIL和见证缺口继续保留。
