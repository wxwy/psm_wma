# DS_PRO — V3 R0/S1 并行就绪证据（用户转交摘要）

**日期：** 2026-10-12
**当前已审核 Formal Pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` + Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**历史训练时 Child（DS 时间线）：** `71e03c8501c94a2ad5fed60955af657d3f945b85`；历史 Root 未能由本轮来源恢复确切 SHA。
**原正式 Job:** `formal_verified_index_30k`，仍 STOPPED。
**证据边界：** 此记录依据用户转交的 DS_PRO 245 行报告，不代表 GPT 直接访问或重算训练服务器 `/tmp` 的文件、Checkpoint、历史运行日志。GPT 另经 GitHub 检查了固定 Root/Child 和相关真实生产语义。

## R0 自报告：SAME_MODE_RESUME_READY_CANDIDATE

1. 旧运行 Child `71e03c8501c94a2ad5fed60955af657d3f945b85`（Oct9 14:57 UTC）尚无 Compact Placeholder/Shared Episode Reader/Async Raw Prefetch，历史 Dense video `torch.zeros(_COMPOSITE_SHAPE,dtype=uint8)`，等效 0/0。新优化 `d41be4f` Oct10 08:54 UTC 后才加入。当前 formal Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` Oct10 11:32 UTC 提交，晚于原训练结束 Oct10 02:09 UTC，不能把当前 Formal Pair 说成历史训练时相同字节。
2. 原 Formal Job `.../psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/latest_checkpoint.txt` 指向 `iter_000000800`；五组件 model/optim/scheduler/trainer/dataloader 和全部8 rank dataloader pkl 存在。报告称原始作业实际提交到 **iter805**（由 `/tmp/formal30k_train_records.json` 740..805 见证），仅 iter800 有 DCP，因此重新 Resume 必从800 **回放801–805**。
3. 固定 config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`；形态 `T16/B8/GA2/K4/world8,Hpred16,max_iter30000,warmup500,save_iter100`、raw15、left_wrist/use_state、num_workers raw async=0；旧 `JointDataLoader` 配置 worker=4 与新 CLI raw async `--num-workers 0` 不应混淆。
4. DS 报当前 Child `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` 的 Dense OFF/OFF + raw prefetch0 路径在功能上复用旧 SFT zeros、官方 VideoResize 和 Producer 同步路径；`PSM_V3_COMPACT_CACHED_VIDEO=0`, `PSM_V3_SHARED_EPISODE_CACHE=0`, `--num-workers 0`。旧版本和新版本**不是字节级相同实现**。
5. 原 `--job-name formal_verified_index_30k` + 原 `--output-root .../psm_wma_v3/outputs/local_ttt_robocasa_raw15` 会选择 true Same-job `warm_start=False`，读 iter800；绝不能把 C1 Shadow Job 当成正式输出根。CPU `--preflight` 和正式启动命令均已给出，但**本轮 CPU --preflight 尚未执行**。其结果不得写成已 PASS。
6. 建议 GPU 共享许可、每卡实时 free≥25000MiB、独立 per-rank 日志及首异常停止，iter801 status=optimizer_committed/grad finite/local correct，iter900 首次下一个 DCP 保存（save_iter100）。
7. DS 报原 Formal Job 仍 STOPPED且原 DCP未改写。C1 Shadow 的8-rank严格恢复已独立 CLOSED，不重复做。

## S1 自报告：D1_S_DESIGN_READY（未经 GPT 批准）

- 纠正前次 warmup/save 误写，改回 `warmup500/save100`。
- 删除 Wilcoxon“不显著即等价”的规则，将目标表述为**工程确定性一致性**，主规则 `epsilon=0`；在无法保证确定性时，拟用 **两次 Dense 自重复差异**作为跨模式容差上限。该 fallback 的工程变异性估计并未独立建立充分的置信界/独立margin。
- 拟扩展到314个 selected gradient FQN、按 FQN w0去重、零/空 FSDP2 shard 实际 `param.grad` Provenance，canonical semantic video zeros/input fingerprint 分离 storage layout。
- **统计构成存在本轮内部算术错误：** 先称漏18个（正确），随后又称“13 gen +1 action+9 local=23，因 w0 重复4而差5”；可信的上一轮已核对映射应是 `281 moe +4 action +11 core=296`，新增 `8 non-action generation bridges +1 action_modality_embed +9 local other =18`，w0属于core且之前单独多列4，不影响296→314的集合差。不可按有误分桶作为 Gate 完整覆盖。
- 报告还声称“旧 D1 数值结论整体作废”，这不成立：v1 rank-collision的特定比较结果不可用，但**clean v2 对照经过8 rank全量冻结 Comparator，FAIL仍有效**。
- v3 Harness 仅设计，尚未实现/CPU验收；无新 GPU、torchrun、生产代码/Checkpoint写入、训练/正式 Resume。

**GPT Review：** `docs/collab/chatgpt/reviews/2026-10-12_V3_R0_same_mode_resume_readiness_and_S1_design_review_444c232b_e9b8a41.md`。