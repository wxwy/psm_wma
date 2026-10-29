# V3 No-TTT Compact A/B/C 单轮证据增量审核（2026-10-29）

**正式结论：`REQUEST_CHANGES`（仅 B GPU Numeric Parity 的 Evidence-only）。**
- A：`RECORDED`（单步速度观测）。
- B：`FAIL_PARITY`（冻结的逐参数 `torch.allclose(rtol=1e-3,atol=1e-5)` 四 Rank 未全部通过）；并不直接等于生产 Compact Bug。
- C：`READY_BY_STATIC_CHECKS`（仅静态，不是可恢复性通过）；报告中的 Resume 命令草案错误。
- 用户上传DS全文证据：`docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_OneRound_DS_PRO_user_paste.md`（388行，可读入口，内嵌三条Rank0 JSONL和Checkpoint结构）。报告声称配套`summary.json`/`gpu_paired_harness.py`/四RankJSON尚未在 origin/V3 可访问，不可把用户粘贴摘要等同于独立检查过的完整机器工件。
- 冻结实施Root基线：`49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；Child/Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`。自上次审核以来 No-TTT实施源未变；只做新 Evidence 增量审核，不重复技术审核。
- 合同：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_OneRound_GPU_Parity_Perf_S2_Readiness_DS_PRO.md`及既有GPU parity阈值。

## A — 已满足本轮只读日志任务（非稳态速度Gate）

同正式配置+Consumer ID SHA：Compact1 Fresh1两次 `step_wall=25.523/23.482s`，Dense0 Fresh1一次 `45.806s`，相对Compact均值 `1.869×`；`data_prepare` Compact1 `9.149/6.889s`，Dense0 `30.128s`，比值 `3.757×`；`gpu_data_stall` 比值`3.817×`。Loss同值，Rank0峰值Reserved Compact1 29.84GiB，Dense 30.68GiB。均为单步、GPU共存、Cold/竞争环境；`gpu_data_stall`是当前stream估计，并非GPU整体空闲率；不推断稳态速度、不要求重跑Fresh1。

## B — 现有严格 Gate `FAIL_PARITY`，仅能推断“Compact特有差异尚未确定”

报告同4Rank FSDP2、Frozen单GA、同权重、同RNG，Dense0a→Dense0b→Compact1，四Rank标量Loss都相同。`Dense-Dense`梯度allclose失败数Rank0..3为`224/242/227/238`；`Dense-Compact`为`225/235/229/245`。因此冻结`allclose`判据未满足。Dense自身重放有大量失败，表明**本次测试不具备有效稳定的严格对照**，但不能直接归结唯一原因于BF16内核非确定性，也不能自动把B更改为Pass。

### F1 HIGH / Evidence-only — 噪声解释不足以证明“Compact效应不存在”
- 文件：`docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_OneRound_DS_PRO_user_paste.md:189-234`。
- 原因：`top50`重叠90–98%并非全部224–245个失败对象的全集重叠；`excess_positive`仍有98–115/548（17.9–21.0%），`ratio_max`高达32。`median_ratio=1.0`及loss一致有参考价值，但不是经过预注册检验的统计等价证明。Dense→Dense自身失败可能来自CUDA非确定性、未受控状态、比较实现等多种原因，现有汇总无法辨别。
- 冻结合同：所有Rank逐参数`allclose`，失败按`FAIL_PARITY`处理，不能事后放宽。
- 验收：先审已生成的`gpu_paired_harness.py`/四RankJSON、完整张量比较与噪声样本定义；如确需noise-calibrated判据，另立独立Gate并在实验前冻结统计阈值，不可把本次严格Gate追认通过。

### F2 MEDIUM / Evidence-only — 294 与 548 个对象的分母不一致
- 文件：`docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_OneRound_DS_PRO_user_paste.md:185-203`。
- 原因：报告所列7个训练参数组计数`281+4+2+2+2+2+1=294`，却使用`548`作为failures和ratio的分母；报告中Rank0分组举例还重复列`vae2llm`。目前无法确认548中是否包含非选中/冻结/无梯度对象，group passed统计与总失败数的映射也不明。
- 冻结合同：需要每Rank所有Optimizer选中可训练参数、None mask、Shape/Dtype、Grad值和Group覆盖的可追溯分母。
- 验收：仅以原始Harness/RankJSON核对`total_named/selected_trainable/present/none/compared`、组名计数与failure归属；无需重跑GPU。

### F3 MEDIUM / Evidence-only — 原始B Harness和四Rank数值工件未提交
- 文件：`docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_OneRound_DS_PRO_user_paste.md:373-381`。
- 原因：V3远端未有报告声明的`docs/collab/chatgpt/evidence/2026-10-28_V3_NoTTT_Compact_OneRound/summary.json`、`gpu_paired_harness.py`、`gpu_parity_rank_jsonl/*`；仅现有摘要不能独立核对RNG、权重/Buffer、逐Tensor比较与统计方法。
- 验收：一次提交现有整组`summary.json`、`gpu_paired_harness.py`、四RankJSON及分析脚本；**不重复已做的GPU实验**。

## C — 静态Checkpoint齐全，但Resume命令错误

`latest_checkpoint.txt`指`iter_000000001`，`complete.v1.json`列4组件、4个rank sidecar（包含Rank3完整SHA `ab1ce5d459ce145f461221d99f8e45ba8e994068bac47460cb87c8f959493f84`），`v3_job_identity.json`记录world4/GA4/`save_iter=100`。原证据明确没有验证全部DCP数据SHA/真实Restore，故仅`READY_BY_STATIC_CHECKS`。

### F4 MEDIUM — 正式Resume launcher调用方式不正确
- 文件：`docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_OneRound_DS_PRO_user_paste.md:351-369`；Root `scripts/train_v3_matched_no_ttt_4gpu.sh:5-15,41-51,68-76`。
- 原因：草案在Child目录用`$PYTHON scripts/train_v3_matched_no_ttt_4gpu.sh --job-name ... --phase resume`调用Shell脚本。实际Launcher要求从Root用`bash scripts/train_v3_matched_no_ttt_4gpu.sh resume EXECUTION_UNTIL`，Job名和数据路径通过`JOB_NAME/OUTPUT_ROOT/SOURCE_ROOT/CACHE_ROOT/DATASET_INDEX_ROOT/EDGE_POLICY_CHECKPOINT/WAN_VAE_PATH/BASE_CHECKPOINT_PATH`环境变量传入。
- 验收：只更正未执行的命令草案；可参考`bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 10`（**仅接口示意，不批准执行**），使用原NoTTT Python环境、Compact1和`NOTTT_LOADER_WORKERS=0`。不得改变`save_iter=100`。

## 限制、Gate状态和下一步
- CPU Parity之前`CLOSED`；未见生产实现新Bug。Owner管理磁盘/Checkpoint保留，不以磁盘清理策略阻断Gate。
- **B `FAIL_PARITY`不转成PASS或代码Bug宣判**；A `RECORDED`，C `READY_BY_STATIC_CHECKS`但尚未实测Resume。
- **`S2_NOT_AUTHORIZED`**，不在本轮改原NoTTT/新Job、DCP、GPU0–3或生产代码。
- 下一步最低成本：DS一次提交现有B完整脚本/四RankJSON/分析脚本，解释参数294/548并修正C命令（**只读与文档动作**）。GPT对原始Evidence再做一次增量审核；是否增设noise-aware Gate需新的预先冻结合同，而不能事后修改本次失败标准。
