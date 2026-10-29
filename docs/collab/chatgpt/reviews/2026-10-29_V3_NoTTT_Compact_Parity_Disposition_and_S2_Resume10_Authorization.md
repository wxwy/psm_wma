# PSM-WMA V3 — Compact v2 数值结论分离与 S2 Resume 至 iter10 执行授权

- 日期：2026-10-29（Asia/Shanghai）；角色：ChatGPT 设计／审核。
- **正式本轮 verdict：`APPROVE_S2_RESUME_TO_ITER10_ONLY`。** Owner 在讨论参照重复性与 Gate 合理性后明确回复“好，继续”，授权独立 Compact Job 的短程真实 Resume 与连续提交验收，以及关键输入见证的并行补证。本授权不依赖将旧严格梯度 Gate 改成 PASS。
- **历史数值结果保持：`GPU_STRICT_GRADIENT_PARITY=FAIL_PARITY`；`REFERENCE_REPEATABILITY=FAIL_AT_FROZEN_TOLERANCE`；`COMPACT_SPECIFIC_REGRESSION=INCONCLUSIVE`。**
- **执行状态：`S2_AUTHORIZED_NOT_EXECUTED_BY_GPT`。** 本轮只读 GitHub 源码／既有 Evidence，运行离线标准库统计，写审核／执行要求；没有运行真实模型、CUDA、DCP restore 或训练。S2 最终 PASS/FAIL 等待 DS 真实运行。
- No-TTT 历史实现 Root：`49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`。
- 本轮取证 V3 HEAD：`66a5b99c0a23312525ccbdc0fadb4655bc7d0b19`，Child/Gitlink 仍为上述 SHA。GitHub compare 显示后续生产改动属于评测入口，No-TTT launcher 与 Child 未变；本轮不重复审核未变生产代码，不把 bookkeeping HEAD 当成新训练实现身份。
- 精确 DS 执行要求：[`2026-10-29_V3_NoTTT_Compact_S2_Resume10_DS_PRO.md`](../requests/2026-10-29_V3_NoTTT_Compact_S2_Resume10_DS_PRO.md)。

## 1. 更新归档事实：四 Rank 原件已在 V3，勿重复索取

本轮从上述固定 V3 HEAD 实际读取：

`docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_GPU_v2_Reassembled/`

四个 JSON 均为 7344 行（末尾 LF 不另计一行），能解析，Rank/world 身份正确，SHA256 与目录 README 全部匹配；Git blob SHA 也与 Git tree 一致。Harness 上传文本与原 Review 已存在。先前会话总结“远端归档未完成”已过时，本轮纠正为 **`RAW_V2_ARCHIVE_VERIFIED`**。不要求 DS 重交17份附件，也不重复 CPU Gate、三套 Fresh1 或旧 paired GPU 实验。

| Rank | JSON bytes | SHA256 |
|---|---:|---|
| 0 | 305056 | `10ff7564e70d2d726ea3510202ba0d0a11d4602ce8618534cf345d239d0c6748` |
| 1 | 305250 | `1bf095cbb5803a4fd3b96ba335bba850994f50935fd6dfc5eba600d47a375260` |
| 2 | 305324 | `f72b61abd6ccd8df402d3cde8412f5e0bb0daa5247bf0f51362da6df4e21cd08` |
| 3 | 304610 | `132c81ec536a981d04c62fee867d2b63943169b7e51fcd07397970f2807ac4a0` |

## 2. 已有数值摘要的离线复核

可复现脚本及结果：
- `../evidence/2026-10-29_V3_NoTTT_Compact_v2_Offline_Analysis/analyze_compact_v2_existing_evidence.py`
- `../evidence/2026-10-29_V3_NoTTT_Compact_v2_Offline_Analysis/compact_v2_existing_evidence_analysis.json`

本次是对已经序列化的统计进行解析、交叉核对与汇总，**不是对未保存的原始梯度逐元素重算**。

| Rank | DD FAIL/294 | DC FAIL/294 | DD worst10 最大 max_abs | DC worst10 最大 max_abs |
|---|---:|---:|---:|---:|
| 0 | 139 | 135 | 0.000244140625 | 0.000244140625 |
| 1 | 149 | 142 | 0.00030517578125 | 0.000244140625 |
| 2 | 140 | 148 | 0.0009765625 | 0.000244140625 |
| 3 | 154 | 156 | 0.0029296875 | 0.001953125 |

- 各组 covered 总和294，covered-pass 总和与 failure_count 一致。三侧各 Rank loss 和 weighted 值相同；selected294、frozen255。实际 grad_meta 是 **float32 DTensor**，不能称“存储的 BF16 梯度”。
- Harness 按 max_abs 排序后保存 worst10；上述返回摘要中，跨模式最大绝对差未大于同模式重复。但完整有限性和全梯度见证不齐，不能升级成等价证明。
- 所有非 moe_gen 组在各自 Rank 的 DD/DC 通过数相同；总失败数变化来自 moe_gen 组。这不是 action bridge 全部通过的声明：Rank3 部分 bridge 在 DD 中也已失败。
- diagnostic.worst_excess10 明确保存 rank1 一项、rank2 一项、rank3 两项 DD 通过而 DC 失败的例子；不是完整清单。不能因总体数量接近而抹去这些差异，也不能凭单次三侧运行确认 Compact 因果缺陷。
- 每侧只保存失败名字前50个，前50交集为46/46/46/49；不是完整失败集合交集。worst10 按 max_abs 选择，其 rel_l2 不能代表全294分布；无逐元素超阈比例或 cosine 证据。
- ratio/excess 的全参数汇总是原始记录，生成它们的完整 per_param 字典未序列化，本次不能独立复算。原 comparator 在 reference norm=0 时将 rel_l2 写0，ratio排除零noise分母；这些是统计定义限制，不新增 S2 前置 Gate。
- 四 Rank／294个张量是一次分布式实验的相关组成，不能当成独立重复样本。BF16／FSDP2 的使用不能直接解释具体差异来源。

## 3. Gate 裁决如何分离

旧 allclose 判据 `rtol=1e-3, atol=1e-5` 的结果继续有效；不后验改阈值，也不把 FAIL 改成 PASS。但 Dense 自身重复失败且完整输入／状态控制见证不齐，当前试验不能独立承担“Compact 是否产生额外问题”的归因裁决。

| 项目 | 本轮状态／作用 |
|---|---|
| CPU Compact Parity | CLOSED，不重跑 |
| F1 参数冻结 | CLOSED，沿用已读源码和四Rank证据 |
| F2 formal_pass 裁决 | CLOSED，沿用严格 FAIL 正确返回的证据 |
| 严格 Gradient Parity | FAIL_PARITY，历史保留 |
| Compact 特异性回归判断 | INCONCLUSIVE，未证实也未排除 |
| F3 输入／输出完整值见证 | OPEN；关键入口输入子项可并行补齐 |
| F4 完整状态／有限性／全参数统计 | PARTIAL_OPEN；不阻塞本次独立 S2 |
| F5 上传 Harness 富文本损伤 | OPEN_PROVENANCE_ONLY，原文不改写 |
| 原始 v2 JSON 远端归档 | VERIFIED |
| S2 工程验收 | AUTHORIZED 至总 iter10，实际结果待 DS |
| 30k／旧 Job 切 Compact | 本轮未授权 |

本 Review 在 **S2执行权限** 上取代旧 Review 中的 `S2_NOT_AUTHORIZED`，同时保留其严格数值结果和未闭合证据事实。完整模型等价如以后继续研究，应另行冻结协议；本轮不启动新的重复校准试验。

## 4. 已核对的真实接口及明确范围

- Launcher：`scripts/train_v3_matched_no_ttt_4gpu.sh:22` 默认 Job 是旧 `no_ttt_packed128_droid_fresh_30k_world4_ga4`；`:42` 只读取 JOB_NAME，RUN_NAME不能替代。必须显式指定新 Job。
- `:46-50` 限定物理GPU4–7；`:69-77` 固定 No-TTT/world4/T16/B8/GA4/max_iter30000/warmup500/save_iter100，传递 `--formal-execution-until 10`。
- Child `examples/psm_wma_robocasa_corrected_phase5.py:1038-1052` 将 formal execution 上限与训练／调度 horizon 分离；`:1115-1117` 拒绝恢复点不低于执行上限；`:1347-1348` 设置 committed-boundary 执行上限；`:1398-1404` 验证最后迭代及实际新提交数。
- 目标 Job：`no_ttt_compact1_corerun_20261028_world4_ga4`；原报告 latest=iter1 时应新增 iter2–10 共9次 Optimizer Commit。现场如已推进，保留现有进度并执行至同一上限；达到／超过10不重复启动，不能回滚恢复点。
- **max_iter=30000、warmup=500、save_iter=100 均不改。** 不追加 `--audit-missing-grads` 或改为 fresh／diagnostic launcher；复用现有训练健康监测。
- 只使用GPU4–7，允许与旧No-TTT共存。旧Job、GPU0–3、G1、Cleaner均保持原状；资源冲突只处理本次新Job的确切进程。
- Owner已接管存储管理；不新增容量／保留／Cleaner Gate。不删除、迁移或覆盖 Checkpoint。
- 无需重新确认本轮授权；DS在上述范围内完成检查与一次S2，失败按执行要求停止和报告，不自行扩大至100／30k。

## 5. 工程验收与证据边界

S2通过要求：真实恢复模型／optimizer／scheduler／trainer及已有数据状态；从实际恢复迭代连续提交至10；无训练异常、OOM、NaN/Inf或既有审计报告的新缺失／非有限梯度；正常在执行上限退出。无需9步Loss单调下降、无需每步匹配Dense、无需新跑Parity。

`last_completed_iteration` 与 `last_saved_checkpoint` 分开报告，Checkpoint按现有保存／退出逻辑处理，不为iter10强改保存频率。短程耗时记录只标短程观察；旧Job持续推进仅支持“未见故障”，不能宣称零性能影响或稳态1.87倍。

完整输入见证以已有生产 seam 的递归值检查为范围；若确实发现本应相同的有效输入发生变化，则是新实质缺陷，应暂停新Job并定位。未测字段继续NOT_MEASURED，不要求先补完整输出／逐侧模型快照才能启动S2。

正式S2结束后DS一次性提交原始日志引用、逐步记录及简短结论；GPT据实际证据决定下一阶段。
