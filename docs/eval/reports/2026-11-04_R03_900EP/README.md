# R03 900EP 正式评测报告：Local-TTT iter20000

日期：2026-11-04。本文全部运行时间使用北京时间（UTC+08:00）。

> **最终结果：454 / 900 成功，SR = 50.4444%。18 个任务各 50 EP；139 组实际语言指令。** 运行完成、Core 结果合格、媒体产物完整、CLI exit=0。本报告冻结该次实测结果，不是新代码 Gate，不授权启动下一轮实验。

## 阅读入口

- 本页：总体结果、配置、18 个任务、语言条件差异、运行性能、Local-TTT 实际调用、产物完整性与局限。
- [完整语言指令分项表](instructions.md)：139 组原始指令，逐项列出 N / 成功 / 失败 / SR / 成功与失败 Episode 编号；覆盖全部 900 EP，不只是选例。
- [机器可读汇总与核验信息](audit_summary.json)：计数、性能、完整性、源文件 SHA256；用于以后复核与比较。

## 1. 执行摘要

| 指标 | 结果 |
|---|---:|
| 有效 / 计划 EP | 900 / 900 |
| 成功 / 任务失败 | 454 / 446 |
| Episode 加权总体 SR | **50.4444%** |
| Task 等权平均 SR | **50.4444%**（每个 Task 恰好 50 EP） |
| Task 数 | 18 |
| 实际 `(task, instruction)` 分组 | 139 |
| 不同 instruction 字符串 | 139 |
| 无效 / 中断 / 未完成 EP | 0 / 0 / 0 |
| 初始化错误 / 跳过初始化错误 | 0 / 0 |
| 场景准入尝试 / 被拒绝场景 | 901 / 1（NavigateKitchen；不计入 900 个有效 EP） |
| `results_qualified` / `clean_execution` | true / true |
| 最终 `status` | complete |
| `process_errors` / 未解决进程错误 | 空 / 0 |
| 最终 CLI 标记 | `R03_FRESH_EXIT=0` |

454 个成功 EP 的终止类型均为 `success_latch`；446 个失败 EP 均为 `official_horizon`，不是进程错误或缺失结果。它们只能证明在本次任务判据下达到/未达到成功，不能单凭终止类型断定失败发生在抓取、导航、接触或语言理解的哪个阶段。

**最重要的结论：** 工程链路完整跑通；模型效果在任务之间及同一任务不同指令条件之间差异显著。现阶段没有匹配的 No-TTT 对照，不能把 50.44% 解释为 Local-TTT 的净增益，也不能把个别指令差异直接解释为语言理解的因果影响。

## 2. 运行身份与评测协议

### 2.1 不可混淆的版本

| 项目 | 冻结值 |
|---|---|
| Run 名称 | `R03_900ep_nv_attrib_m1b1` |
| Formal Root implementation | `083b36ac27ad43b6f5127d9a58aed4fac02eaaa7` |
| Child / Gitlink | `1069fe78841228cadbbfbe6afbd767eaed6225da` |
| Checkpoint | `packed128_droid_fresh_g1_20261019/checkpoints/iter_000020000` |
| Manifest digest | `6b96faae57bdd65345588c40aa384b7ab6e2fc2ec9192b43919eed653d2ee155` |
| Model identity digest | `9190bdb20658fec2847693e3aa7d6bb3ebed85e2b1a5c69691304c9b5b4cef21` |
| Runtime identity digest | `0dded4f1c2b672919667bbc79af3f10c4f2eb63db1be60cd7f0858e728727a92` |
| Model config SHA256 | `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e` |

本报告及其后续文档提交的 SHA **不是**本次评测的 implementation SHA。该报告直接添加到 V3 文档目录，不合并 G2 隔离候选，不改训练、评测代码或子模块。

### 2.2 实际运行配置

| 配置 | 实测 / 冻结值 |
|---|---|
| 数据 / 任务范围 | RoboCasa365 Target-Atomic，18 underlying task classes × 50 EP |
| 模式 | `phase_b` / `phase_b_native_batch_v1` |
| Local memory | `required` |
| 推理卡 | GPU6、GPU7；每卡 1 个 Action Server |
| 渲染卡 | GPU4、GPU5；EGL；每卡 1 个 Sim |
| GPU 型号 | 上述四卡均为 NVIDIA H100 80GB HBM3（报告时只读查询） |
| 并发 | `sims_per_gpu=1`、`max_infer_batch_size=1`；总共 2 个 Sim |
| 实际 Batch Histogram | size=1：28,464 次；没有 Batch>1 |
| `batch_wait_ms` | 20 |
| 观测 / 动作 | `left_wrist`；observation_frames=17；action_chunk_size=16 |
| 仿真频率 | 20 Hz |
| raw action / state 维度 | 15 / 15，不能与其他训练配置中的 20D 混写 |
| 采样步数 / guidance | prediction_steps=30 / guidance=1.0 |
| 任务流逻辑 seed | 0 |
| 场景采样 | `dynamic_slot_environment_seed_then_continuous_reset_v3` |
| 调度 | `episode_major_frozen_order_round_barrier_v1` |
| 成功权威 | `env._check_success`；success_latch=1 |
| 初始已成功场景 | `reject_initial_success_bounded_v1`；admission_limit=32 |
| 视频策略 | 所有 EP 保存 rollout；`save_generated_video=all` |
| 媒体队列 | max_jobs=4；max_bytes=536870912；drain_timeout=300s |
| Resume | 本轮只有 1 次 `fresh` invocation，**没有执行 Resume** |

`seed=0` 是逻辑任务流信息，不表示每个 Episode 用同一个静态场景，也不证明未来改变 M/B 后能复现同一批场景。场景与对象差异会影响语言条件统计；后续严格对照需核对实际 scene provenance。

## 3. 统计方法与独立核验

数据来自已完成 Run 的 `manifest.json`、`summary.json`、`media_summary.json`、900 份 `tasks/*/episodes/ep_*/result.json`，以及关联的 `predictions.jsonl`、`local_memory.json`、`core_inventory.json` 和进程关闭回执。2026-11-04 14:49:07（北京时间）完成主统计。

### 3.1 口径

1. 总体 SR = 成功 EP / 全部 900 个有效 EP。Task SR = 该 Task 成功 EP / 50。
2. 语言分组键严格为 `(result.body.task, result.body.instruction)`，保留大小写、标点、空格和原始措辞，**不翻译、不纠错、不归并同义词**。这不是完整的模型序列化 prompt/token 审计。
3. 指令 SR = 该精确字符串下成功 EP / 该字符串的实际 EP 数。不同字符串样本数不同，不能对 139 个 SR 简单等权平均后替代总体 SR。
4. Episode 编号为每个 Task 内的 **0–49**，不是训练集 global episode ID。必须连同 Task 使用。
5. P50/P95 使用排序样本上的线性插值；耗时表分别标明 episode elapsed、请求 latency、native generation、queue 和 batch preparation，不能混用。

### 3.2 本次实际做过的只读核验

| 检查 | 结果 |
|---|---|
| Manifest 内容 digest | 重新计算，与冻结 digest 一致 |
| 900 份结果 envelope | 对 canonical body 重新计算 SHA256，全部一致 |
| `(task, episode)` 集合 | 精确等于 18×{0,…,49}；无重复、无缺失 |
| Core 关联文件 | **3,600 文件**，逐份核对 bytes 与 SHA256；合计 760,020,095 bytes |
| Core 与 summary | 任务级 / 总体成功失败数全部一致 |
| 指令完整性 | 900 条均为非空字符串；139 组加总 900 EP、454 成功、446 失败 |
| Predictions | 28,464 条；各 EP 数量与 replans 一致；replan index 连续 |
| Session / reset | 900 个独立 session_id；900 次 reset_ok=true |
| 视频存在性 | 900 rollout + 28,464 generated，全部非零字节 |
| 媒体汇总 | expected=saved=acknowledged=28,464；900 EP COMPLETE；errors=[] |
| 关闭回执 | 2 Server + 2 Sim 均无 live_group、无 remaining_pids |

检查只在服务器读取源记录并生成文本统计，未重跑模型或仿真。**没有逐个重新解码 MP4、没有观看所有失败视频、没有重新计算全部模型 checkpoint 文件哈希**；媒体内容质量和具体行为根因不应从“文件存在 / ACK 完整”推导出来。

## 4. 18 个任务的最终成功率

按冻结任务顺序排列；每行 N=50。指令数指本次 50 EP 中实际出现的不同原文数量。

| Task | 成功 | 失败 | SR | 指令数 | 官方 horizon |
|---|---:|---:|---:|---:|---:|
| CloseBlenderLid | 4 | 46 | 8.00% | 1 | 900 |
| CloseFridge | 22 | 28 | 44.00% | 2 | 900 |
| CloseToasterOvenDoor | 30 | 20 | 60.00% | 1 | 450 |
| CoffeeSetupMug | 27 | 23 | 54.00% | 1 | 600 |
| NavigateKitchen | 1 | 49 | 2.00% | 13 | 450 |
| OpenCabinet | 37 | 13 | 74.00% | 2 | 1050 |
| OpenDrawer | 19 | 31 | 38.00% | 2 | 750 |
| OpenStandMixerHead | 33 | 17 | 66.00% | 1 | 450 |
| PickPlaceCounterToCabinet | 24 | 26 | 48.00% | 43 | 750 |
| PickPlaceCounterToStove | 39 | 11 | 78.00% | 21 | 600 |
| PickPlaceDrawerToCounter | 15 | 35 | 30.00% | 9 | 750 |
| PickPlaceSinkToCounter | 29 | 21 | 58.00% | 29 | 900 |
| PickPlaceToasterToCounter | 37 | 13 | 74.00% | 1 | 600 |
| SlideDishwasherRack | 26 | 24 | 52.00% | 2 | 450 |
| TurnOffStove | 11 | 39 | 22.00% | 8 | 750 |
| TurnOnElectricKettle | 21 | 29 | 42.00% | 1 | 450 |
| TurnOnMicrowave | 45 | 5 | 90.00% | 1 | 450 |
| TurnOnSinkFaucet | 34 | 16 | 68.00% | 1 | 600 |
| **合计 / 总体** | **454** | **446** | **50.44%** | **139** | 按任务 |

较强任务为 TurnOnMicrowave（90%）、PickPlaceCounterToStove（78%）、OpenCabinet / PickPlaceToasterToCounter（均74%）；明显短板为 NavigateKitchen（2%）、CloseBlenderLid（8%）、TurnOffStove（22%）和 PickPlaceDrawerToCounter（30%）。这些是当前采样下的描述性排序，不是跨 seed 的稳定排名。

## 5. 语言指令细分：Task 平均值掩盖了什么

### 5.1 全覆盖与小样本

139 个分组的样本量分布为：1 EP×62组、2×21、3×19、4×6、5×3、6×3、7×2、8×1、9×2、10×3、12×1、21×3、24×1、26×1、29×3、50×8。

- **62/139 组只有 1 EP**；0% 或 100% 只是单次结果，不是可靠能力估计。
- **108/139 组少于 5 EP**，合计185 EP；只有20组达到 N≥10。
- 8 个 Task 仅出现一种指令，各50 EP；但同一句话仍可能对应不同布局、对象实例、相机和初态。
- 本轮139个字符串是实际在线评测覆盖，不等于训练数据中所有语言 phrasing，也不能冒称穷尽指令空间。

### 5.2 优先关注的条件差异

| Task | 精确原始指令 | 成功 / N | SR |
|---|---|---:|---:|
| CloseFridge | `Close the fridge door.` | 19 / 29 | 65.52% |
| CloseFridge | `Close the fridge doors.` | 3 / 21 | 14.29% |
| OpenCabinet | `Open the cabinet door.` | 19 / 21 | 90.48% |
| OpenCabinet | `Open the cabinet doors.` | 18 / 29 | 62.07% |
| OpenDrawer | `Open the left drawer.` | 12 / 21 | 57.14% |
| OpenDrawer | `Open the right drawer.` | 7 / 29 | 24.14% |
| SlideDishwasherRack | `Fully slide the top dishwasher rack out.` | 20 / 26 | 76.92% |
| SlideDishwasherRack | `Fully slide the top dishwasher rack in.` | 6 / 24 | 25.00% |
| TurnOffStove | `Turn off the front right burner of the stove.` | 5 / 10 | 50.00% |
| TurnOffStove | `Turn off the front left burner of the stove.` | 0 / 9 | 0.00% |
| TurnOffStove | `Turn off the rear right burner of the stove.` | 3 / 12 | 25.00% |
| TurnOffStove | `Turn off the rear left burner of the stove.` | 2 / 10 | 20.00% |

**解释边界：** door/doors 可能关联不同设备与操作数量，left/right 关联目标位置，in/out 对应相反动作。它们不是单纯同义改写实验。当前观察说明“这些语言条件所对应的任务子情形表现不同”，不能推出“模型不理解复数、左右或 in/out”。须在匹配场景与目标条件下比较，或结合失败视频确认。

### 5.3 导航与对象条件

NavigateKitchen 的唯一成功为 `Navigate to the toaster oven.`，1/3，成功 EP29；其余12种导航目标共47 EP均失败。这不能证明模型已掌握 toaster oven 导航，N=3仍很小。完整13目标见附表。

PickPlaceCounterToCabinet 的50 EP分散到43个对象指令，PickPlaceCounterToStove分散到21个，PickPlaceSinkToCounter分散到29个。很多对象仅1–3次，不宜据此排名对象难度。PickPlaceDrawerToCounter 中 `rolling pin` 为4/10、`peeler`为1/9、`ladle`为1/8，可作为失败分析取样线索，但仍不是控制变量实验。

CloseBlenderLid 的原文是 `Close the lid blender by securely placing the lid on top.`，50 EP中4成功；附表保留这句原始措辞，不将其“纠正”为别的字符串。低SR的行为原因尚未观看视频确认。

## 6. 运行耗时、推理性能与并发

### 6.1 时间线与吞吐

| 时间点 | 北京时间 |
|---|---|
| Manifest 创建 | 2026-11-03 23:10:36 |
| 首个 Core 结果落盘 | 2026-11-03 23:15:36 |
| 最后一个 Core 结果落盘 | 2026-11-04 14:41:01 |
| 最终 summary 发布 | 2026-11-04 14:41:10 |
| 最终 media_summary 发布 | 2026-11-04 14:41:17 |

按 manifest→summary 的文件 mtime 口径：**55,834.32 秒 = 15小时30分34秒，58.03 EP/小时**。加入媒体最终汇总约再7秒。此口径不包含更早的命令启动 / preflight，不能作为精确模型加载时间；首结果与 manifest 的5分钟差也不能全部归因于加载。

本轮执行448,106个环境 step、28,464次 replan，平均每EP497.90 step、31.63次 replan。单EP `elapsed_seconds` 均值109.43s、P50 99.19s、P95 204.65s、最大260.89s；900条elapsed之和为98,488.73s。由于2个Sim并行，该和不等于整轮 wall time。

### 6.2 所有 28,464 次请求的时延

下表直接聚合 `predictions.jsonl` 中的数值；单位毫秒。

| 字段 | Mean | P50 | P95 | Max |
|---|---:|---:|---:|---:|
| 记录的请求 `latency_ms` | 1406.95 | 1347.75 | 1872.13 | 13551.65 |
| `native_generation_ms` | 1058.85 | 1028.61 | 1400.35 | 13485.38 |
| `batch_prepare_ms` | 253.88 | 215.93 | 590.12 | 1301.82 |
| `queue_ms` | 0.269 | 0.282 | 0.399 | 1.939 |

这些是各自埋点口径，不把请求时延冒称GPU纯kernel耗时，也不把各分位数相加。M1/B1下请求排队很少；没有高并发测试，不能据此承诺M8/B8的收益或峰值显存。

### 6.3 逐任务耗时

| Task | 平均 steps | 平均 EP秒 | EP P95秒 | Replan总数 |
|---|---:|---:|---:|---:|
| CloseBlenderLid | 878.68 | 195.13 | 218.63 | 2782 |
| CloseFridge | 680.24 | 143.70 | 203.14 | 2155 |
| CloseToasterOvenDoor | 342.70 | 73.89 | 107.89 | 1099 |
| CoffeeSetupMug | 450.30 | 99.37 | 143.19 | 1430 |
| NavigateKitchen | 443.26 | 97.57 | 115.34 | 1429 |
| OpenCabinet | 584.80 | 127.54 | 244.12 | 1848 |
| OpenDrawer | 610.20 | 135.38 | 185.66 | 1921 |
| OpenStandMixerHead | 272.08 | 61.24 | 107.07 | 882 |
| PickPlaceCounterToCabinet | 569.70 | 127.38 | 184.67 | 1794 |
| PickPlaceCounterToStove | 365.66 | 82.19 | 136.92 | 1166 |
| PickPlaceDrawerToCounter | 645.42 | 141.56 | 191.44 | 2028 |
| PickPlaceSinkToCounter | 684.24 | 155.25 | 220.52 | 2167 |
| PickPlaceToasterToCounter | 463.90 | 103.87 | 138.22 | 1471 |
| SlideDishwasherRack | 340.10 | 74.26 | 106.55 | 1095 |
| TurnOffStove | 643.24 | 135.02 | 169.81 | 2020 |
| TurnOnElectricKettle | 370.90 | 82.25 | 109.27 | 1193 |
| TurnOnMicrowave | 206.28 | 42.65 | 91.68 | 676 |
| TurnOnSinkFaucet | 410.42 | 91.54 | 145.18 | 1308 |

耗时同时受horizon、成功提前停止、布局与初始化等影响，不能直接把不同任务的EP/小时解释为模型效率差异。

### 6.4 性能比较的限制

运行期间GPU4–7曾与人工 `gpu_load_sim.py` 负载共存；用户在本轮中途关闭了该进程，11:00的只读检查已确认其退出。确切停止秒数没有进入本次评测manifest；本报告不拟合关闭前后的因果加速倍数。因此58.03 EP/小时是**本次混合资源条件下的实测吞吐**，不是全程独占GPU的标准性能基线。

调度协调数据：claim P50/P95=41.24/81.78ms，core_commit=45.81/83.27ms；二者各900次且0 failed。scheduler_lock_wait P95≈0.001742ms（记录17,490次，保留4,096个样本）；仅一次汇总重建为4.235s。这些数据不能代替完整仿真/渲染/编码分阶段profile。

## 7. Local-TTT 实际在线使用证据

| 指标 | 结果 |
|---|---:|
| Episode独立session | 900 |
| reset_ok=true | 900 / 900 |
| 首次预测 | 900 |
| 首次prefix_present=true | 0 / 900 |
| 首次encoded/adapted/fast_state_norm非零 | 0 / 900 |
| 后续预测 | 27,564 |
| 后续prefix_present=true | 27,564 / 27,564 |
| 后续encoded_steps / adapted_steps | 全部16 / 16 |
| replay=true | 0 |
| rollout / media / cleanup error | 0 / 0 / 0 |

后续预测的fast_state_norm范围9.58567–9.61780，均值9.60484；fast_update_norm范围0.001484–0.053945，均值0.008945；inner_loss_mean均值0.001787、P95 0.007998。以上是运行诊断值的分布，不是训练损失曲线或下游收益指标。

这些记录支持“本次 required-mode Local-TTT 分支被实际调用并有更新”，而不是仅配置启用；但独立session和reset记录本身不构成任意跨episode状态无泄漏的完整证明，更不构成相对于No-TTT的效果消融。

## 8. 产物、完整性与回看索引

| 产物 | 数量 / 状态 | 字节数 |
|---|---|---:|
| Rollout MP4 | 900，全部名为 `rollout.mp4` | 594,147,133 |
| Generated MP4 | 28,464；saved=ACK=expected | 490,915,667 |
| MP4合计 | 29,364；零字节文件0 | 1,085,062,800 |
| 媒体Episode | 900 / 900 COMPLETE | — |
| 媒体错误 | errors=[] | — |
| 已校验Core关联文本文件 | 3,600 | 760,020,095 |

上述字节数仅是相应文件类别，不是整个Run目录占用。未上传任何视频、图像、动作数组或可逆传感数据；仓库只存报告、文字指令与聚合统计。

服务器Run根目录：

```text
/mnt/data1/data_v2_0617/robocasa_eval_runs/local_ttt_robocasa_raw15/packed128_droid_fresh_g1_20261019/R03_900ep_nv_attrib_m1b1
```

附表中任意 `(Task, EP)` 的回看路径为：

```text
<RUN_ROOT>/tasks/<Task>/episodes/ep_<EP:03d>/result.json
<RUN_ROOT>/tasks/<Task>/episodes/ep_<EP:03d>/predictions.jsonl
<RUN_ROOT>/tasks/<Task>/episodes/ep_<EP:03d>/scene_provenance.json
<RUN_ROOT>/tasks/<Task>/episodes/ep_<EP:03d>/media/rollout.mp4
<RUN_ROOT>/tasks/<Task>/episodes/ep_<EP:03d>/media/generated/replan_<index:04d>.mp4
```

例：NavigateKitchen唯一成功为 `tasks/NavigateKitchen/episodes/ep_029/`；CloseBlenderLid成功EP为7、9、30、36。所有其他成功/失败EP均在[指令附表](instructions.md)中，无需猜测视频名称。

### 收尾诊断的正确解释

4个owner进程关闭回执均记录SIGTERM、returncode=-15、live_group=false、remaining_pids=[]；这是协调器收尾记录，不能把子进程-15直接当作主CLI失败。主CLI最终exit=0，summary仍为clean_execution=true。

`_internal/batch_status.json` 留有GPU6的`diagnostic_error=ConnectionError`，其mtime为**2026-11-03 23:10:38**，属于启动阶段遗留快照，不是最终吞吐或Batch权威。本报告用28,464条预测记录统计Batch分布，并保留该异常快照说明，不删除或隐瞒它。

## 9. 结论、尚未回答的问题与下一步

**已经确认：** 该精确版本/checkpoint在本次900EP中得到50.4444% SR；18个Task、139个语言条件、所有有效EP均可追溯；执行与媒体完整性检查通过。

**尚未确认：** Local-TTT净增益；跨seed泛化；同场景同目标下的纯语言改写鲁棒性；失败动作阶段与机制；M8/B8吞吐/峰值显存；中断后的真实Resume。不能以本轮完成替代这些实验。

建议后续按结果证据推进，而不是重跑同一轮：先用附表定位CloseFridge单/多门、OpenDrawer左右、SlideDishwasherRack推/拉，以及NavigateKitchen与CloseBlenderLid的成功/失败视频，做行为级标注；再设计匹配No-TTT对照。性能与Resume用独立新namespace验证，沿用科学协议并明确资源条件，不能混入R03已冻结结果。本报告没有启动这些后续工作。

## 10. 来源绑定与复核

| 源文件 | SHA256 |
|---|---|
| `manifest.json`（文件字节hash，不同于manifest digest） | `36db433a786be7c594cb0b1df8f3f02b3f1d0d8b07a8b5888201af4e9aaa2fc4` |
| `summary.json` | `f8959c940023d3de3c213ec23fe0080d20b9927a87854e4bc61ce98f641ac3b6` |
| `media_summary.json` | `904b1b042fb9d12c50c8305e5c8084da531ecc8ed45d80bfd91a766c030a2520` |
| `_internal/coordination_metrics.json` | `cd92ab9a5ed30d397f9130275dd842ba274c742be57cf9b9b16e65519cd5fd10` |
| `_internal/run_inputs.json` | `32eb68b51ca843d434904ce191f0b6ae7c75620b79cd79081e10940f5955f0ed` |
| `/tmp/r03_900ep_nv_attrib_m1b1_fresh.log` | `eb0f209ad61c0a6ba269199bda3e1d63eaff0cec0bb1446ce275b220d88d8b72` |
| 900条结果文件清单的canonical SHA256 | `14e3449eab40333a4f24486729a096cd3f90c4c80c376794828e33646d682950` |

清单hash计算：按result相对路径排序，形成`[[relative_path, sha256(file_bytes)], ...]`，以UTF-8、sort_keys=true、ensure_ascii=false、separators=(',',':')的JSON编码求SHA256。结果envelope的body校验使用同一canonical编码。语言分组再按Task冻结顺序、组内N降序、instruction字典序排列；Txx-Ixxx是本报告内部索引，不是数据集原生ID。

服务器临时统计记录为 `/tmp/r03_report_analysis_20261104.py` 与 `/tmp/r03_report_20261104_ikckjlew/`（可能被清理，不能替代上述持久Run证据）。本报告是已完成结果的只读汇总；既有缓存、训练、模型、日志与历史失败证据未修改。
