# PSM-WMA V3 — RoboCasa365 Local-TTT / No-TTT 训练曲线与证据归档

**状态：已完成两组正式训练的只读数据审计；V3代码仓保留训练Loss、监控曲线、配置、身份和Resume历史。完整逐步标量档案留在原服务器（大数据导出受企业上传限制）。**

## 两组训练与评测关系

| 项目 | Local-TTT | No-TTT |
|---|---:|---:|
| 训练Job | `packed128_droid_fresh_g1_20261019` | `no_ttt_packed128_droid_fresh_30k_world4_ga4` |
| 原始Rank0日志行数 | 27,835 | 30,011 |
| 唯一训练Iteration数 | 27,705 | 30,000 |
| 监控中的重复Iteration额外行 | 130 | 11 |
| 训练GPU / GA | 8GPU / GA2 | 4GPU / GA4 |
| Nominal Global Effective Batch | 2048时间步Consumer | 2048时间步Consumer |
| 在900EP评测中使用的Checkpoint | iter20000、iter27700 | iter28000 |
| 模型Local Memory | On | Off |

共同训练数据为 **RoboCasa365 Target-Atomic全量**，18 underlying任务，9126条Episode/2231347帧，非早期N=100子集。训练原始Monitor按Rank0记账；有效Batch 2048不是2048条独立Episode。配置中Local-TTT旧通用DataLoader `chunk_length=32` **不是实际生效Action Horizon**；从Launch证据可核查实际H16、Local B8/T16/GA2/world8、No-TTT B8/T16/GA4/world4。

## 本仓已保存的内容

`local_ttt/`和`no_ttt/`分别保存：

- **`curve_100step.csv`：逐100个唯一Iteration的训练曲线，含全部主要Loss及梯度、Fast Weight、有效Consumer、LR、训练耗时、显存和数据等待统计**；以每个Iteration最后一条记录代表该步。无需Python依赖即可在GitHub查看。
- `config.yaml`：原始训练配置，文件SHA256在`manifest.json`中。
- `v3_job_identity.json`：Job创建时的Root/Child、原始配置哈希与Semantic Digest。初始Root/Child不能冒称全部Resume阶段的代码身份。
- `launch_history.json`：每次Fresh/Resume的启动合同、实际生效配置和源SHA。
- `manifest.json`：来源完整性、全部监控字段、重复Iteration索引、Checkpoint当前保留状态、逐步数据的离线SHA和服务器位置。

当前仓内**尚未保存全部逐步标量**，所以不把100step均值称作完整原始记录。服务器已建立以下全量只读衍生档案：

- `local_ttt/scalars/*.csv.gz`：27,835条原始顺序的完整数值监控记录、116列，**保留130条重复Iteration**。
- `no_ttt/scalars/*.csv.gz`：30,011条原始顺序的完整数值监控记录、93列，**保留11条重复Iteration**。
- 两组 `task_exposure.csv.gz`：18个任务的逐步采样/累计曝光指标。
- 两组 `sparse_diagnostics.jsonl.gz`：Fast State快照摘要、参数指纹和非空异常。

以上完整档案在服务器：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/training_archive_stage_20261105`。这不是GitHub链接；需经获授权的批量数据导出通道才可同步。**未上传任何权重、Optimizer分片、raw日志、Sensor数据或视频**。

## 监控字段与解释口径

曲线`curve_100step.csv`包括：

- 各种Loss：`outer_loss`、`action_loss`、`vision_loss`、`flow_matching_loss_action`、`flow_matching_loss_vision`；Local-TTT额外`inner_loss_mean`。
- Fast Weight：`fast_state_norm_mean`、`fast_update_norm_mean`（仅Local-TTT，No-TTT为空值，不当作0）。
- 梯度与参数：`total_grad_norm_rank_local`、`generation_grad_norm_rank_local`、`local_grad_norm_rank_local`。
- 训练性能：`valid_consumers`、`step_wall_s`、`lr_max`、`peak_reserved_gib`、`gpu_data_stall_ms`、`data_prepare_ms`。
- 完整服务器档案同时保留近全部可数值化Telemetry键及每步原始`record_index/iteration_occurrence`、抽样CUDA Event/参数范数、任务曝光。

**重复Iteration规则**：完整档案一条不漏；便于画趋势的100step曲线使用每个Iteration**最后出现的记录**，不会将重复监控行当作额外Step。重复记录说明日志存在重叠，不可脱离DCP/Resume证据断言一定重复执行了优化器提交。

**梯度Scope**：`rank0`的Grad Norm是FSDP Rank0局部/Shard值，不是8卡/4卡Global Norm。内外Loss和模型记忆结构不同，不能仅靠两条训练Loss曲线认定No-TTT性能优劣；SR对照要看正式900EP结果。

## Checkpoint存储策略（Owner已确认）

- 中间Checkpoint保留**模型分片**，Optimizer分片按照策略主动删除，不是意外损坏。
- 最后的保留Checkpoint保有完整训练状态：Local-TTT iter27700（8份模型+8份Optimizer）、No-TTT iter30000（4份模型+4份Optimizer）。
- 历史评测Checkpoint：Local-TTT iter20000（8/8模型，0/8 Optimizer）和No-TTT iter28000（4/4模型，0/4 Optimizer）。当前可推理但不能凭旧`complete.v1.json`标记就主张完整Resume。

## 源码及后续评测

详细的900EP SR和Task分析：
[Local-TTT统一评测结果](../../reports/PSM-WMA_V3_RoboCasa365_Local_TTT_Evaluation_Report.md)。
这份训练记录是独立证据：不能把训练Loss改善直接当作SR改善。

本归档仅处理已存在训练数据，未修改任何训练代码、正在运行的评测及服务器Checkpoint/Optimizer文件。
