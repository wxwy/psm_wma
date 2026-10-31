# Issue #12 — C12200 独占GPU4–7、同DCP No-TTT nw0 vs nw8 正式性能 Evidence 审核

**审核日期：2026-10-31。Verdict：`APPROVE_PERFORMANCE`（仅本候选Formal Pair的C12200独占匹配A/B、18步稳态Step Wall性能；原始GPU日志属DS_REPORTED，未被GPT直接读取SHA）。**

- Formal implementation Root `fd9021b0908b4b2763b3d02508b1f34df377dc97` / Child+Gitlink `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822` **未改变**：旧`APPROVE_CODE`、真实CPU首包PASS、4rank×8worker有界GPU C9620→9625功能PASS保留，禁止重做技术Code Gate或旧CPU301/58。
- Owner批准来源 GitHub Issue#12 `#issuecomment-6538051198` 与2026-10-31 C12200 Owner Runbook。DS报告Owner亲自使正式NoTTT Job在C12200保存完成后退出，随后按条件独占GPU4–7串行完成A、B。原正式Job/Checkpoint保持不变，A/B各用完整原DCP C12200的独立克隆。
- **证据级别与限制：** Owner在当前会话直接提供DS_PRO《Issue#12 NoTTT候选 nw0 vs nw8 独占GPU性能A/B验收报告（PASS）》；所述 `RUN_MANIFEST.json`、`CLONE_MANIFEST.json`、两臂logs、JSONL/DCP存在于 DS训练服务器 `/mnt/data/shenzhen/szrobot/logs/issue12_ab_20261031/`。GPT未取得原始服务器字节，因此**不能声称独立核算25个DCP文件哈希或18×2原始JSONL**。已直接从GitHub核对固定Formal代码/Launcher/Telemetry语义并对汇总指标重算；本轮接受用户转交的DS实测结果，不以转运ZIP为新障碍。

## 1. Frozen Contract → reported behavior → verdict

| 冻结验收项 | DS报告实测 | 判定 |
| --- | --- | --- |
| exact Formal Pair | root fd9021b0 / child 224c5f3c，独立候选、未合并V3 | 符合；新源码与数据身份需以当前原始Manifest追溯，不能拿V3 HEAD当已测Pair |
| 匹配输入 | 同一 `iter_000012200` 全模型/优化器/调度器/Trainer/rank0–3 sidecars，25个文件hash/size与独立inode匹配 | DS报告完整，源码恢复链路一致；原件哈希未独立取得 |
| 匹配设备与配置 | GPU4–7独占、两臂互斥、world4/GA4/B8/T16、Compact1、same model/seed/data/optimizer，仅NoTTT loader workers0/8不同 | 满足有效性能因果对照的主要实验控制条件 |
| 每臂C+1…C+20 | A/B各20/20 `optimizer_committed`，iter12201–12220，zero Timeout/OOM/errors，完成后各自Checkpoint `iter_000012220 complete=true` | `FUNCTIONAL_A20_B20=PASS_REPORTED`，与Child冻结`MatchedNoTTTTrainer` post-commit/DCP回调合同相符 |
| 冷启动首包 | A first step data7.0s/wall19.2s；B data25.8s/wall37.5s，原120s timeout不变 | 首步B较慢，但在deadline内，后续高吞吐收益成立 |
| 稳态 | 排除前两步后iter12203–12220各18步，见下表 | `MATCHED_STEADY_STEP_WALL=APPROVE_PERFORMANCE` |
| GPU/Host资源 | A/B peak VRAM≈33.06GiB，B每worker峰值RSS约6.1–6.4GiB，无OOM/Worker残留，结束GPU空闲 | 20步无资源异常；不能据此保证余下整段训练的Host内存/IO长期稳定 |

## 2. 成立的正式性能收益（只按真实Step Wall，不借用未核对data口径）

| 量（steady n=18 / arm） | A=Compact1,nw0 | B=Compact1,nw8 | 分析 |
| --- | ---: | ---: | --- |
| `step_wall_s` mean | **15.489s** | **9.611s** | **A/B=1.6116×**，每步减少5.878s、**37.95%** |
| `step_wall_s` p50 | 15.5s | 9.5s | B稳态中位数明确更快 |
| `step_wall_s` p90 | 15.93s | 10.13s | B在尾部延迟也明显更快 |
| Peak GPU memory | 33.06GiB | 33.06GiB | 未见GPU显存增加，Host RSS另算 |
| 训练步阶段前2步 | 19.2/15.3s | 37.5/9.4s | 冷启动单独列，不混入稳态 |

- 按DS汇总计算，20个训练`step_wall`总和估算A≈313.30s、B≈219.90s，**连同首步冷启动**仍有约1.425×步阶段加速；该总和由四舍五入后的均值推算，**不是从完整原始20行独立复算**，不含Parent preflight、DCP保存、torchrun启动。主Parent传统eager Source初始化仍可能≈192s，不能把稳态1.61×宣传成训练进程全流程启动到退出也加速1.61×。
- 这次是Owner批准的独占同DCP互斥A/B，与先前共享GPU下旧nw0/newnw8的描述性1.49×不同。稳态Step Wall的显著收益本身符合冻结Runbook中“step wall明显改善或数据等待显著下降且无其它显著退化”的`APPROVE_PERFORMANCE`判断，**不依赖其它指标49×叙述**。

## 3. 一个必须更正的DS指标解释（不阻断Step Wall性能Gate；原始日志只读补正即可）

**新Finding：REPORT-METRIC-SOURCE，MEDIUM / Evidence semantics only**。

- DS写“data wait mean A5.472s/B0.112s ≈48.86×”、“gpu_data_stall_ms=NOT_MEASURED，因`timing_scope=host_monotonic_not_measured_gpu_idle`与`trace_window_sampled=false`、80条日志没有该字段”。**报告混用了两种不同的数据源**：后两字段属于 Child `cosmos_framework/trainer/no_ttt_async_loader.py` 的**Loader trace**，不能用来判定训练Observer的CUDA事件采样状态。
- 实际Candidate Child `examples/psm_wma_robocasa_formal_monitor.py:30–59` 的 `[CorrectedV3][progress] data=...` **严格来自** `record.gpu_data_stall_ms`，仅当 `gpu_data_stall_status='ready'`才显示数值，否则`n/a`； `examples/psm_wma_robocasa_corrected_telemetry.py:88–115,161–205,430–465,490–538` 默认每步`data_stall_sample_interval=1`并向`[CorrectedV3][train]`写出`gpu_data_stall_ms`与`gpu_data_stall_status`，其意义是**rank0 current CUDA stream gap estimate around CPU data_prepare/batch_collate**，绝非整张GPU idle，也不直接等于`data_wait_ms`或CPU`data_prepare_ms`。
- **若**DS的5.472s/0.112s实际来自进度行`data=...`，那么这些值是**GPU current-stream gap估计**（而非普通data wait），其约48.86倍差异只能按此精确口径报告；DS所谓NOT_MEASURED不成立。若取自独立Host data等待/prepare统计，则必须给原字段名并说明两臂同口径；不可默认把不同字段直接比较。
- **唯一最小补正（无需GPU重跑）**：DS**只读**从现存A/B `monitor/train_rank0.jsonl`抽出iter12203–12220共36条的`iteration,step_wall_s,data_prepare_ms,data_wait_ms,gpu_data_stall_ms,gpu_data_stall_status,gpu_data_stall_sampled`与源日志位置，按`gpu_data_stall_status='ready'`计算有效样本比例/分位数，另对照 `[CorrectedV3][progress] data=...`；提供精简证据摘要即可。不要求重传24GB DCP，不复跑CUDA/CPU实验。
- 此修正只影响data/stall子指标的标签与机制解释，**不影响匹配Step Wall的`APPROVE_PERFORMANCE`**。不允许未完成同字段核对前把“host等待降低49×”、“整卡GPU闲置降低49×”写入正式成果。

## 4. Gate closure 与最少后续工作

- **`APPROVE_PERFORMANCE`**：本候选在C12200相同独占GPU、同完整DCP、仅nw0↔nw8的n18稳态Step Wall对照，B明显更快、P50/P90均更好、无20步内OOM/Timeout/提交失败。关闭本轮NoTTT Async Loader性能Gate；不要求再做新的匹配GPU实验。
- **未授权的操作**：不能由DS直接修改/合并Canonical V3源码、不能重启正式30k、不能动正式iter12200 DCP/JobName/Cleaner、不能把隔离A/B新DCP当正式续训源；这次Approval只表示性能，不自动授权生产行为。
- **建议下一步**：Owner决定是否恢复正式30k时，先由Codex在当前Canonical V3/Child上**最小移植**已通过的Worker Source/Recipe二处生产增量及对应局部测试；当前Canonical Child `0ae313e329d290fc6b8a50fda1112820fb7ac485`与候选 `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`历史已经分叉，**不得整树覆盖Gitlink**，必须保留EvalV2其他改动。再走新Formal pair小范围Code Gate与Owner明确的正式恢复授权。#13“默认progress-only”是另一个Shell日志显示任务，不属于本性能Pair；不能以其改动污染已测对照。

**正式Verdict仅针对这次配对性能条件的DS报告及已核对源码，不代表GPT直接见证运行、原始日志逐字节可信度、长期30k稳定性或正式生产切换。**