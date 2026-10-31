# Issue #12 — 4Rank×8Worker候选真实GPU DCP Resume功能Evidence增量审核

2026-10-31。Formal Root `fd9021b0908b4b2763b3d02508b1f34df377dc97`，Child/Gitlink `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`，均未变。本轮不重新审核旧Code/CPU Gates，不修改生产代码。**Verdict：`C9620_C9625_4R8W_FUNCTIONAL=PASS_REPORTED_WITH_CODE_CROSSCHECK`；`GPU_MATCHED_SPEEDUP=INCONCLUSIVE`。**

## 证据及范围

Owner转交DS 2026-10-31报告，已专项授权有界4Rank×8Worker GPU4–7 Resume并豁免本次与原正式nw8作业并发的独占要求。原始launch.log、monitor、iter9625 DCP保存在DS服务器隔离输出，本审核未直接取到原件SHA，仅基于DS报告+独立查冻结Child训练代码；不能把其当作GPT独立4Rank实验。

| 实测DS报告 | 值 | 审核含义 |
|---|---:|---|
| Resume源 | iter_000009620完整DCP clone，load3.75s | 正式身份NOTTT4语义豁免，不等于Root/Child HEAD严格完整byte parity |
| iter9621 C+1 | optimizer_committed，首包数据等待24.2s，wall45.5s | 首包小于原120s，实际完成首个优化器提交 |
| iter9622–9625 C+2…C+5 | 4/4 optimizer_committed，wall13.2/14.2/13.3/16.9s | 5步有界功能连续，非长期稳态资格 |
| DCP保存/进程 | iter_000009625 complete=true，latest_checkpoint指向9625，成功退出 | DS报告完整，新DCP未独立读SHA |
| Worker资源 | world4×nw8，RSS约6.06GiB/worker，VRAM rank0峰32.78GiB，无OOM | 5步无OOM，非30k RAM容量结论 |

冻结Child `matched_no_ttt.py` 中 `_optimizer_step_success`成功后才提交Window/Frontier、触发`post_commit`；Checkpoint只允许committed边界，所以5条`optimizer_committed`和9625保存支持C+1真实功能PASS。另有Loader `raw_wait_host_ms=26235.9ms`与Progress“首包数据等待24.2s”，是不同采样口径，不可直接强行相等。

## 用户要求的现有非独占nw0/nw8初步对比

| 项目 | 旧ArmA Compact1,nw0（共享GPU） | 本次候选Compact1,nw8（共享GPU） |
|---|---|---|
| 区间 | iter9603–9620 18步 | iter9622–9625 4步 |
| Step Wall P50 | 20.49–20.50s（旧review） | **13.75s** |
| Step Wall mean | 20.28s（旧review） | **14.40s** |
| 描述性差值 | — | median少约6.74–6.75s，**减少32.9%、表观吞吐1.49×** |
| 数据侧 | nw0 data_prepare p50约5.88s；旧current-stream data stall约5.35s | nw8报告 data_wait 0.080/0.0941/0.1154/0.1259s，P50=0.10475s；未提供对应current-stream stall |

**严禁把表观1.49×写成严格Matched速度收益**：两者时刻、Checkpoint（旧A从9600训练到9620、新B从9620到9625）、并发争用强度及样本量不相同。Owner并发豁免只允许功能验收；不提升真实性能对照等级。旧失败ArmB在首包120s超时/0 commits根本没有稳态数据，报告提及正式nw8约32s的稳态属于另一个正在运行的Job，不能标为同DCP旧失败ArmB。

`data_prepare_ms`、`data_wait_ms`、`raw_wait_host_ms`、`gpu_data_stall_ms`四者语义不同；`main_thread_wait 4–5s`确实是主线程等待，但是否形成**current CUDA stream**空档未测，不能说“不是等待”也不能当作GPU全部idle。`gpu_data_stall_ms`需有status=ready的current stream event数值才可比较。RSS≈6.06GiB×32的约194GiB**累计RSS**包括共享映射，不能当作私有Host物理RAM；cache_mapped仅旧latent/Episode mmap，不含新的Source Arrow LRU。

## Gate及后续

- `4R8W_GPU_RESUME_CPLUS1_TO_CPLUS5=PASS_REPORTED_WITH_CODE_CROSSCHECK`，初始首包Timeout功能blocker本候选已克服。不重跑相同GPU5步、旧CPU301/58或单Worker CPU探针。
- `STRICT_MATCHED_GPU_PERFORMANCE=INCONCLUSIVE`，需要另获Owner许可、明确排他GPU4–7资源窗口，才能从同一完整合法DCP使用同一候选Root/Child依次跑独立nw0/nw8，只有workers数不同，采集step wall、GPU current-stream stall status与值、Host RAM/IO及Owned worker清理。若正式训练仍占GPU，不应干预它制造排他。
- `CANONICAL_V3_MERGE=NOT_AUTHORIZED`：独立候选仍不可整树覆盖当前EvalV2的V3 Gitlink；未来如合并由Codex窄移植两处生产文件及对应测试，新正式Pair审核。不改已有30k Job和原DCP。

**本文件仅裁决功能Evidence与当前非独占描述性比较，不构成额外GPU执行授权。**