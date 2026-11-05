# PSM-WMA V3｜RoboCasa365 Local-TTT 仿真评测结果与对比报告

**文档定位：Local-TTT 多Checkpoint、多轮正式评测的统一结果入口。** 不以单个iter或单个Run命名；后续新增Local-TTT评测按同样的身份、协议、结果、诊断与局限要求追加。原R03完整详细报告及其139组指令归档保持冻结；本页在其基础上纳入R07全量正式结果。

- **版本**：v1.0；更新日期 2026-11-05（北京时间）。
- **研究范围**：PSM-WMA V3、RoboCasa365 Target-Atomic、18个Underlying Task、每任务50EP、Local-TTT required、动作H16。
- **权威数据**：完成Run的 `manifest.json`、`summary.json`、每EP `result.json` / `predictions.jsonl` / `local_memory.json`；本报告的汇总与机器归档是只读分析，不改变任何冻结Run。
- **核心纪律**：Checkpoint结果、协议差异、性能及Local-TTT机制证据分别陈述；不能把跨版本的SR差直接作为Local-TTT因果收益，也不能将No-TTT未完成时的部分结果视为正式对照。

## 一、执行摘要

| Local-TTT正式Run | Checkpoint | 结果合格 | 成功/有效EP | 总体SR | 与R03相差 |
|---|---|---|---|---|---|
| R03（2026-11-03～04） | iter20000 | complete / clean | 454 / 900 | **50.4444%** | 基准 |
| R07（2026-11-05） | iter27700 | complete / clean | 580 / 900 | **64.4444%** | **+14.00 pp** |

R07比R03多成功**126个Episode**。18个Task中，15个Task观测SR提升、2个下降、1个持平；Task等权平均与Episode加权平均相等，因为每Task均精确50EP。

**这不是“Local-TTT带来+14pp”的证据**：两次都是Local-TTT required。它们的Checkpoint（20000→27700）、Root/Child代码、并发（M1/B1→M16/B8）、场景采样（v3→v4）及媒体策略不同，连实际出现的语言指令集合也不完全一致。应将+14.00pp定性为**两次完整、但非严格配对的运行之间的描述性差异**。模型净增益需要另行比较同模型家族的No-TTT基线。

## 二、训练数据、模型与运行身份

### 2.1 共同训练背景

两轮Local-TTT模型均来自 `packed128_droid_fresh_g1_20261019` 的正式训练轨迹，加载的训练config SHA256同为 `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e`。底座来自Cosmos3-Edge-Policy-DROID，使用RoboCasa365 **Target-Atomic全量数据**，不是早期用于数据准备的N=100子集。

数据源 `/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic` 的元数据与映射表包含**9,126 Episode、2,231,347帧、18个Underlying Task**（231条task/phrasing元数据行不能误算作231个Underlying Task）。训练使用 `left_wrist`、`raw15/state15`、20Hz、H16、TBPTT=16、K_local=4、fast_hidden=256、TTT dim=64、inner_lr=0.1。

**有效Batch口径必须使用Grouped Trainer的运行时Consumer：**
`8 B_stream × 16时间步 × 2 GA × 8 GPU = 2048`（最大/名义的全局时间步Consumer/optimizer step），不是配置中通用兼容DataLoader的 `batch_size=1`。因此每个Checkpoint代表的训练量需按消费时间步和Epoch解释，不能当作2048条独立Episode。R07的27700步名义消费约5673万时间步Consumer（重复采样累计）。

### 2.2 冻结的模型和评测源码

| 字段 | R03（iter20000） | R07（iter27700） |
|---|---|---|
| Formal Root | `083b36ac27ad43b6f5127d9a58aed4fac02eaaa7` | `3bd1404cf065cc6eae4a07bde6ad0da024596e07` |
| Child / Gitlink | `1069fe78841228cadbbfbe6afbd767eaed6225da` | `1ca308055fc41fb69efaeb9efaa23808f164a18e` |
| Checkpoint | `iter_000020000` | `iter_000027700` |
| Manifest digest | `6b96faae57bdd65345588c40aa384b7ab6e2fc2ec9192b43919eed653d2ee155` | `a07bfa652d8ae1f71cfd041afe7c12b9f7cde0ca3145c79121fdb80d3227f369` |
| Model digest | `9190bdb20658fec2847693e3aa7d6bb3ebed85e2b1a5c69691304c9b5b4cef21` | `0d9ddc6b938379a13a410f8826c5537a118f37da0df5ecdbfa8c726295061944` |

这些是**评测当时**的正式运行身份，而不是发布报告这一文档提交的HEAD。评测结论只能绑定各自Run的来源，不可沿用到新Root/Child或新Checkpoint。

### 2.3 评测协议与不能直接归因的差异

| 项目 | R03 | R07 |
|---|---|---|
| 任务/EP | 18×50＝900 | 18×50＝900 |
| 模式 | `phase_b`、Local-TTT required | `phase_b`、Local-TTT required |
| Policy/Render GPU | Policy6、7；EGL4、5 | Policy6、7；EGL4、5 |
| 并发/Native Batch上限 | M1/B1；合计2个Sim | M16/B8；合计32个Sim |
| Action / observation | raw15、state15、H16、17帧 | raw15、state15、H16、17帧 |
| 采样步数/Guidance | 30 / 1.0 | 30 / 1.0 |
| 场景协议 | `dynamic_slot_environment_seed_then_continuous_reset_v3` | `independent_slot_environment_seed_then_continuous_reset_v4` |
| Task流逻辑seed | 0 | 0 |
| 调度协议 | `episode_major_frozen_order_round_barrier_v1` | `streaming_task_affinity_v2` |
| Rollout MP4 | 900个 | 关闭（0个，设计如此） |
| Generated MP4 | 28,464个 | 关闭（0个，设计如此） |
| 结果质量 | 900 valid / clean | 900 valid / clean |

`seed=0`只是任务流逻辑seed，**不保证R03和R07的同编号EP是同一场景**。场景、对象配置与语言条件混合不同；无法把两轮简单当作同场景配对A/B，也不能只将并发变化视为纯性能差异。R07关闭媒体是降低负载的实验配置，不属于文件缺失/媒体失败；相反，R03媒体落盘已通过原报告的单独完整性审计。

## 三、18 Task 逐项SR：完整结果与历史差值

每一行两轮均各50个**有效**Episode；`Δ` 为 `R07 SR − R03 SR`，单位为百分点（pp）。

| Task | R03成功 | R03 SR | R07成功 | R07 SR | Δ |
|---|---|---|---|---|---|
| CloseBlenderLid | 4/50 | 8% | 14/50 | **28%** | +20 pp |
| CloseFridge | 22/50 | 44% | 31/50 | **62%** | +18 pp |
| CloseToasterOvenDoor | 30/50 | 60% | 44/50 | **88%** | +28 pp |
| CoffeeSetupMug | 27/50 | 54% | 31/50 | **62%** | +8 pp |
| NavigateKitchen | 1/50 | 2% | 8/50 | **16%** | +14 pp |
| OpenCabinet | 37/50 | 74% | 43/50 | **86%** | +12 pp |
| OpenDrawer | 19/50 | 38% | 32/50 | **64%** | +26 pp |
| OpenStandMixerHead | 33/50 | 66% | 32/50 | **64%** | -2 pp |
| PickPlaceCounterToCabinet | 24/50 | 48% | 28/50 | **56%** | +8 pp |
| PickPlaceCounterToStove | 39/50 | 78% | 40/50 | **80%** | +2 pp |
| PickPlaceDrawerToCounter | 15/50 | 30% | 28/50 | **56%** | +26 pp |
| PickPlaceSinkToCounter | 29/50 | 58% | 40/50 | **80%** | +22 pp |
| PickPlaceToasterToCounter | 37/50 | 74% | 49/50 | **98%** | +24 pp |
| SlideDishwasherRack | 26/50 | 52% | 37/50 | **74%** | +22 pp |
| TurnOffStove | 11/50 | 22% | 15/50 | **30%** | +8 pp |
| TurnOnElectricKettle | 21/50 | 42% | 31/50 | **62%** | +20 pp |
| TurnOnMicrowave | 45/50 | 90% | 45/50 | **90%** | +0 pp |
| TurnOnSinkFaucet | 34/50 | 68% | 32/50 | **64%** | -4 pp |
| **合计** | **454/900** | **50.44%** | **580/900** | **64.44%** | **+14.00 pp** |

从观察结果看，增幅最大的任务是 `CloseToasterOvenDoor`（+28pp）、`OpenDrawer`与`PickPlaceDrawerToCounter`（各+26pp）、`PickPlaceToasterToCounter`（+24pp），但上述增量混合了数据采样与版本差异，**不可单独归因于多训练7700步**。

R07的**当前瓶颈**仍集中于 `NavigateKitchen` 8/50（16%）、`CloseBlenderLid` 14/50（28%）和 `TurnOffStove` 15/50（30%）。`OpenStandMixerHead`（−2pp）与`TurnOnSinkFaucet`（−4pp）略低于R03，`TurnOnMicrowave`两轮均90%。仅凭任务级成功标记还无法断言是导航定位、接触规划、视觉目标或执行器动作的哪一种失败。

## 四、语言条件覆盖与细粒度结果

R03有**139**个精确`(task,instruction)`分组、其中62组仅1EP、108组少于5EP；R07有**138**组、其中63组仅1EP、107组少于5EP。对两轮完成的结果文件重聚合发现：**111组原始字符串重合，R03独有28组、R07独有27组**。不同Task的物体、布局或条件频率会不同。因此该指标的变化也不能视作纯语言改写的效果。

以下是若干双方都出现的指令，列出`成功数/该精确指令实际EP数`，不是每组都50EP：

| Task | Instruction（原文） | R03 | R07 |
|---|---|---|---|
| CloseFridge | `Close the fridge door.` | 19/29 | 21/31 |
| CloseFridge | `Close the fridge doors.` | 3/21 | 10/19 |
| OpenDrawer | `Open the left drawer.` | 12/21 | 15/22 |
| OpenDrawer | `Open the right drawer.` | 7/29 | 17/28 |
| SlideDishwasherRack | `Fully slide the top dishwasher rack in.` | 6/24 | 16/27 |
| SlideDishwasherRack | `Fully slide the top dishwasher rack out.` | 20/26 | 21/23 |

门的单/复数、抽屉左/右、架子拉入/推出可能对应不同操作目标，**不是控制变量的同义词实验**。尤其对象型PickPlace任务的字符串重合度更有限，每组通常只有1–3个Episode。

完整语言/EP可追溯索引：**[R03 139组](2026-11-04_R03_900EP/instructions.md)**；**[R07 138组](2026-11-05_R07_900EP/instructions.md)**。两份均保留原始指令（不翻译、不归并）和每组成功/失败的EP编号。Task级成功率不能代替指令分组的样本量分析。

## 五、评测速度、批处理与资源条件

### 5.1 完整时间线及吞吐

| 时间/指标 | R03 | R07 |
|---|---|---|
| 首个结果（北京时间） | 2026-11-03 23:15:36 | 2026-11-05 13:41:50 |
| 最后结果（北京时间） | 2026-11-04 14:41:01 | 2026-11-05 16:25:57 |
| 最终summary（北京时间） | 2026-11-04 14:41:10 | 2026-11-05 16:26:39 |
| Manifest→Summary | 15小时30分34秒 | 2小时49分09秒 |
| 900EP完成吞吐 | 58.03 EP/h | 319.24 EP/h |
| 平均每EP仿真步 | 497.90 | 446.53 |
| 总Replan请求 | 28,464 | 25,566 |
| 平均每EP Replan | 31.63 | 28.41 |

R07从正式Launcher启动（13:35:53）到summary发布约2小时50分47秒，按此口径是316.19 EP/h；上表为了跨轮对齐，统一使用`manifest mtime → summary mtime`口径。R07该口径约为R03的**5.50倍**，但这**不是M16/B8的受控加速比**：并发、源码、checkpoint、任务执行步数、媒体生成及资源共存条件都不同。R03运行中曾与人工GPU压力负载共存，压力停止时点没有对应的精确监控切片，不可套用单一“卡占用”系数修正。

### 5.2 完整Replan请求时延

R03的请求按B1执行；R07的请求处于M16/B8共享Policy队列下。单位毫秒、分位数按全部请求统计。

| 指标 | R03 Mean | R03 P50 | R03 P95 | R07 Mean | R07 P50 | R07 P95 |
|---|---|---|---|---|---|---|
| 记录的请求Latency | 1406.95 | 1347.75 | 1872.13 | 8131.50 | 8050.37 | 11351.75 |
| Native generation | 1058.85 | 1028.61 | 1400.35 | 1956.16 | 1918.68 | 2210.00 |
| Batch preparation | 253.88 | 215.93 | 590.12 | 2876.65 | 2860.46 | 4714.99 |
| Queue wait | 0.27 | 0.28 | 0.40 | 3157.79 | 3132.85 | 5190.66 |

**重点区别**：R07吞吐更高，同时单请求平均延迟和队列等待明显增加，是并发批处理工作负载的结果。不能把`queue_ms`误当GPU计算，也不能把请求延迟和Batch内单帧延迟混同；不同指标分位数不能直接相加。

### 5.3 R07真实Native Batch分布（最终900EP）

从25,566条`predictions.jsonl`的`transaction.native_batch`去重汇总：同一个Batch成员按唯一`(server_epoch,native_batch.id)`计一次，逐一核对成员`index`和声明size，**不是将每条请求都算成一个Batch**。

| 真实Batch size | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | 总Batch |
|---|---|---|---|---|---|---|---|---|---|
| 44 | 85 | 125 | 366 | 795 | 1206 | 1010 | 654 | 4285 |

真实平均Batch Size = **5.966**；B6–B8占**66.98%**的Batch、**76.42%**的请求。R03实际只有B1，共28,464次。

特别说明：R07的`_internal/batch_status.json`是**16:25:54前的快照**，记录4283批、并非最终900EP统计；本报告采用全部25,566条预测去重得到**4285批**，避免把末尾快照误报为最终值。

## 六、Local-TTT在线实际作用：真实Fast Weight更新证据

| 真实Telemetry检查 | R03 | R07 |
|---|---|---|
| Episode独立Session | 900 | 900 |
| Episode reset_ok | 900/900 | 900/900 |
| 首个Replan的Memory Prefix | 0/900 | 0/900 |
| 后续Replan的Memory Prefix | 27,564/27,564 | 24,666/24,666 |
| 后续adapted_steps/encoded_steps | 全部16/16 | 全部16/16 |
| 后续非零Fast Update | R03原报告给出非零分布 | **24,666/24,666** |
| replay=true | 0 | 0 |
| Fast State Norm均值 | 9.60484 | 9.57413 |
| Fast Update Norm均值 | 0.008945 | 0.010386 |
| Fast Update Norm P95 | R03原报告未列 | 0.023924 |
| Inner Loss均值 | 0.001787 | 0.002228 |
| Inner Loss P95 | 0.007998 | 0.009816 |

R07的`OpenCabinet/ep_024`（任务失败）在同一Episode/Session进行了66次Replan，后65次均有非零Fast Update；`CloseBlenderLid/ep_025`（任务成功）进行了27次Replan，后26次均有非零Fast Update。这排除了“只在第一个Replan更新一次”的误读。

实现层面，`local_memory_online.py` 保留每Session的临时fast state，新证据来自上一段已执行的16步；`local_evidence.py` 按每时间步Inner Loss更新 `W_fast`，随后用更新后的状态产生Memory Token，进入后续Action Path；成功生成后才commit。日志中的`fast_update_norm`是每段内局部更新的平均范数，`fast_state_norm`是更新后整体Fast State范数。

**证据边界**：正的Update Norm、相同Session和Memory Prefix是“机制实际执行”的证据，不是证明Local-TTT让SR提升的对照结果；fast state完整参数张量并未落盘，不能以标量范数恢复每个元素值。R03/R07的fast norm均值也不可作为泛化好坏的评分。

## 七、质量Gate、可复核文件与证据边界

| 检查 | R03 | R07 |
|---|---|---|
| 正式状态 | complete / qualified / clean | complete / qualified / clean |
| 结果有效性 | 900/900、0无效/中断/待完成 | 900/900、0无效/中断/待完成 |
| 成功/正常任务失败 | 454 / 446 | 580 / 320 |
| 结束标志 | `R03_FRESH_EXIT=0` | `R07_FRESH_EXIT=0` |
| 进程关闭回执 | 4/4 | 34/34 |
| 900份Core result envelope | 历史报告逐份核验 | 本次重新计算并核对SHA256 900/900 |
| Core关联文件 | R03已逐份复算3,600文件SHA | R07检查900个inventory各列4条；未重哈希所有关联文件 |
| 媒体保存策略 | 900 rollout + 28,464 generated全部落盘 | 媒体明确关闭，不应记作媒体丢失 |
| 语言索引 | 139组、逐EP归档 | 138组、逐EP归档 |

R07核验为**只读**：结果900份完整、不重复，任务级计数与正式summary一致；900个Memory Session/reset有效；25,566条预测的Replan索引连续、与每EP `replans`一致；Native Batch成员数量与batch-id声明全部匹配；34/34受控进程关闭。未重新渲染视频、未进行失败动作人工标注、未重跑仿真或模型。

### 7.1 保留原始运行与冻结证据

- **R03完整历史报告**：[README](2026-11-04_R03_900EP/README.md) · [139组语言指令](2026-11-04_R03_900EP/instructions.md) · [冻结JSON统计](2026-11-04_R03_900EP/audit_summary.json)
- **R07新增证据**：[138组语言指令与900EP索引](2026-11-05_R07_900EP/instructions.md) · [只读机器聚合及源SHA](2026-11-05_R07_900EP/audit_summary.json)

服务器的Run根目录（仅供授权环境内复核）：

```text
R03: /mnt/data1/data_v2_0617/robocasa_eval_runs/local_ttt_robocasa_raw15/packed128_droid_fresh_g1_20261019/R03_900ep_nv_attrib_m1b1
R07: /mnt/data1/data_v2_0617/robocasa_eval_runs/local_ttt_robocasa_raw15/packed128_droid_fresh_g1_20261019/R07_900ep_iter27700_m16b8_v3_nomedia_20261105
```

R07的每个`(Task, EP)`可定位到`tasks/<Task>/episodes/ep_<EP:03d>/result.json`、`predictions.jsonl`、`local_memory.json`、`scene_provenance.json`、`core_inventory.json`。**不存在R07的Rollout MP4路径**，因为明确禁用了媒体保存。

### 7.2 R07主要文件SHA256与身份

| 文件 | SHA256 |
|---|---|
| `R07_LOG` | `a7382ef051ee40a7481de561bb35164c5e3bfbcdd51ce9c822885ebb78d04226` |
| `_internal/batch_status.json` | `bdfc5453f1a00a86d8c7701dd8f3f6c463a7906795d8926114defcab7b88b604` |
| `_internal/coordination_metrics.json` | `089894c934c0aa142a7e9b9ece1e0c9ad72a28338e0eb8196f35f2714332a36a` |
| `_internal/run_inputs.json` | `a40341dab2b1dac7d845d432e18afbe20fb645ec343ba2c50ae31f5cbfec13f7` |
| `manifest.json` | `6cc03918ad21e17f6644842a1b2dec2b83f716a5df42fe9723d381b244b72f7f` |
| `summary.json` | `604c0a2cbf5098f38fb2f80000c234526cf90bf9a141015ea0c6a481c1e0d6b5` |
| 900个结果文件清单canonical digest | `2812ddd3b2a2f3dc09414b3c96c267cb66032056df5331b9c714e06475a5ed42` |

上述`manifest.json`文件字节SHA256与manifest内部`digest`是两种不同标识，不能互换。文档提交本身不改变原始Run、manifest、Checkpoint或formal implementation SHA。

## 八、结论与待完成对照

**成立的结论**：R03 Local-TTT iter20000在900个有效EP上SR为50.4444%；R07 iter27700在900个有效EP上SR为64.4444%；两者各自正式评测完成且Clean；在各自协议内的Local-TTT Online Fast Weight确实执行了持续适应；R07批处理的真实利用率由全量请求记录证实。

**暂不成立的结论**：+14pp完全源于训练推进到27700；Fast Weight在成功任务上必然优于No-TTT；更大的Native Batch使模型本身更聪明；以各个Task/指令的SR直接推断具体行为失败机制。

**下一组对照（独立Run，不写入本报告的Local-TTT结果）：** No-TTT R08已按Owner要求采用**iter28000**（而非先前的iter30000），M16/B8、18×50、同一正式V3评测源码和媒体关闭策略。待No-TTT形成900/900有效结果，首先核查场景采样`scene_provenance`和语言混合，再报告每Task `Local-TTT(27700) − No-TTT(28000)` 差值与统计不确定性；不能预先承诺同编号Episode具有完全相同布局/物体/初态。

**后续维护方式**：这份通用报告持续添加新的正式Local-TTT Run，R03原始历史报告与R07机器审计作为不可覆盖的独立证据保留；任何不同formal Root/Child、Checkpoint、任务集合或采样协议必须保留独立身份与解释边界。本文仅更新研究材料，不授权新训练、修改生产代码或重新运行旧结果。
