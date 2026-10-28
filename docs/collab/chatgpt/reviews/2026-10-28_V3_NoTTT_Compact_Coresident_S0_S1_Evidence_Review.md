# PSM-WMA V3 — Compact=1 第二套 No-TTT 共存 S0/S1 增量 Evidence Review

- 日期：2026-10-28。
- **正式证据 Verdict：`REQUEST_CHANGES`（Evidence-only）；S0/S1 运行成功的报告证据受到认可，但正式 S1 closure 尚缺冻结验收要求的直接数据。**
- Gate：`V3_NOTTT_COMPACT_CORESIDENT_SECOND_JOB`，当前仅 S0/S1。**未授权 S2 resume 10/100/30000**。
- Frozen Stage Plan：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_Coresident_Second_Job_StagePlan.md`。
- 运行时 Root：`4cf90fb486db9c8e2a4b93aaa7d9f5438296f642`；Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`。GPT远端核对现Child仍一致，当前Root后续的区别仅其它评测Review和Inbox文档，No-TTT相关 formal implementation/design 无变更，**不重审生产代码**。
- DS报告源证据归档：`docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1_reported.md`，明确记录为用户转述的 DS报告；GPT没有接触训练服务器、原始GPU截图/Rank log/检查点目录，因此不称独立运行PASS。
- 旧正式Job：`no_ttt_packed128_droid_fresh_30k_world4_ga4`；新独立Job：`no_ttt_compact1_corerun_20261028_world4_ga4`。

## 1. 已有报告可确认的范围

- **S0 `PASS_1_STEP_ADMISSION`（报告支持）**：GPU4–7四卡 `total−2×used` 投影余量5205/10377/9789/10457MiB，均≥4096MiB；CPU192 cores，RAM reported available1626GiB；初始磁盘剩约97GiB且used99%；旧Job报告持续无错误。
- **S1 `S1_PASS_CANDIDATE`（报告支持）**：独立`fresh 1`，`Compact=1`，FSDP2世界规模4、GA4/T16/B8。报告Rank0一次`optimizer_committed`，Loss14.9375、action1.2276、vision0.2662，missing/nonfinite0，`peak_reserved=29.84GiB`，`data_prepare=8.6296s`，干净退出；独立新Job的`iter_000000001` DCP报告具备五类组件。旧正式Job iter4828→4858，未报告中断/出错。
- 首次child.venv驱动/cu130依赖失败后改用**旧正式训练同款Python**解决；这本身不是模型Parity失败。
- **GPU4余量纠偏**：按Rank0 29.84GiB峰值≈30556MiB，`81559−38177−30556≈12826MiB≈12.53GiB`（仍非同一时刻NVML全Rank峰值的证明）。不能宣称所报 `13.5GiB` 是精确安全余量。
- **性能外推无效**：旧Dense报告17.5s为多Worker稳定段，新Compact8.63s为首Step、worker0、共存状态；不能声称真实训练稳态加速51%，也不能称“旧 Job 零性能影响”。需要旧Job重叠前/期间/之后的同口径Step Wall分布。

## 2. 当前 Evidence-only blockers

### E1 — MEDIUM：必需的原始 S0/S1 机器证据不在可审核的远端

- **Source位置**：`docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1.json` 与 `...s0_s1.md` —— V3 `NOT_FOUND`。当前只有用户粘贴的表格/摘要，不能直接核对JSON原始字段、配置和 rank0 `optimizer_committed` 实际行。
- **违反的冻结合同**：Stage Plan `5要求原始JSON/MD、JobName、Source SHA、运行环境、Loss/Checkpoint证据归档，再交GPT独立审核。
- **关闭条件**：提供 DS 现有 S0/S1 原始 `.json/.md`、rank0 `optimizer_committed` 与 `checkpoint` log截取，实际新Job `launch.json/config/env compact flag` 只读简表；只需交付原有证据，不需重跑。
- **范围**：Evidence-only；没有新的生产代码缺陷结论。

### E2 — MEDIUM：S1 四Rank共存显存峰值和DCP完整性证据不足

- **Source位置**：上报 S1仅列 Rank0 `peak_reserved=29.84GiB`，未给 Rank1–3 peak、共存NVML时序；DCP五目录仅报告存在，缺`model/optim/scheduler/trainer`的 metadata 检查、`dataloader/rank_0..3.pkl`与实际完成迭代来源。
- **违反的冻结合同**：Stage Plan `5中“每Rank CUDA used/peak、最终迭代、DCP组件完整性、新旧Job进度/隔离检查”。
- **关闭条件**：提交已存在4Rank logs/峰值及S1期间NVML记录（没有历史采样则`NOT_MEASURED`，不得伪造）；只读列出新Job`iter_000000001`组件 metadata+4Rank sidecars+latest；比对旧Job报告前后对应两条Telemetry及异常。若不能补历史全卡峰值，明确其证据限制，S2安全准入仍须新鲜S0及实际峰值。
- **备注**：单步运行成功作为报告结论不被此项否定；此项阻止把“已安全长期共存”当成正式Gate证明。

## 3. S2 额外硬阻断（非 S1 重跑）

### R1 — HIGH：磁盘99%，剩74GiB，不足以保证并发Job长期保存

- 24GiB/新Checkpoint是 DS 的实际S1报告量级；74GiB只相当于约3份这种量级的磁盘空间，且**旧正式NoTTT仍在按自己的Checkpoint频率保存**。
- 必须在允许任何新的 `resume 10`、`resume 100` 或连续30k前，落实独立Job的Checkpoint retention、旧Job保留策略、储存空间与回退方案。**不得未经授权删除旧Job DCP/任何已有Checkpoint**；不可以“空间足够多跑几步”取代长期并发安全验收。
- 下一次有效数据需真实`df -h`/`df -i`对应`OUTPUT_ROOT`所在文件系统、两Job的DCP占用与剩余空间、预计S2下一保存峰值与失败时回退空间。执行前取得Owner明确同意。

## 4. 其它观察（非 S0/S1 blocker）

- 日志字段`num_workers=0`是G1/raw thread参数，不足以证明旧Job`NOTTT_LOADER_WORKERS=0`；S1新Job已明确worker0，旧Job worker profile应从进程/launcher/NoTTT loader telemetry取证。不同Worker设置不可直接用于纯Compact稳态性能比较。
- 新Job S1“成功并且旧Job继续Commit”只支持共存可行且未见故障，不证明共享GPU对旧任务 **zero slowdown**。
- 新版离线CPU Compact0/1 Parity Gate此前`CLOSED`；GPU同权重/同Frozen Batch的Loss/Gradient Parity仍`NOT_RUN`，不能用新Job `fresh 1`代替。
- 因`fresh 1`在新Job使用真实optimizer并保存Checkpoint，确认`trainer.train`真实运行不构成之前独占`GPU parity`禁止Optimizer的违规：**这是不同Owner授权的新共存Job S1 Gate**。

## 5. Verdict 和下一步

- `S0=REPORTED_PASS_1_STEP_ADMISSION`。
- `S1=REPORTED_PASS_CANDIDATE`；正式Evidence `REQUEST_CHANGES`（仅 E1/E2）。
- `S2=NOT_AUTHORIZED / DISK_CAPACITY_BLOCKER`。
- 只让DS提交现有报告、Log和只读DCP+四Rank证据，不重跑S1，不启动S2，不停止原正式NoTTT。
- E1/E2修复后由GPT复审，才能考虑关闭S0/S1 Evidence Gate。后续长训须Owner单独授权、解决R1磁盘风险，且优先完成真实模型 Compact0/1 GPU数值Pariy。
- **落盘条件**：本Review与Canonical `CODEX_INBOX.md` 一起提交才构成正式Verdict。
