# DS_PRO — V3 下一步：正式同模式恢复前最后取证 R0 + 新 D1-S 设计整改 S1（CPU-only 并行）

**日期：** 2026-10-12
**当前被审核 Formal Pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**历史 Runtime Child（证据用，**不是**当前正式执行 Child）：** `71e03c8501c94a2ad5fed60955af657d3f945b85`.
**当前状态：** `C1_CLOSED / D1_PRESTEP_NOT_PASSED / FORMAL30K_STOPPED`.
**上轮 M0/S0 Review:** `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_M0_S0_resume_mode_and_stochastic_gate_review_444c232b_e9b8a41.md`.
**本轮仅允许 R0 + S1 两项 CPU-only，并行执行后一次汇总。不启动 GPU/原 Formal Job。**

## R0（高优先）— 固定当前 e9b8a41 + 历史 0/0 的真正 Formal30k Resume Readiness

只读已有正式 job `formal_verified_index_30k` 历史 stdout、SESSION/日志、`config.yaml/config.pkl`、launcher/主机历史/git HEAD（若有）/Traceback，**补充证明原 Job 历史 Root/Child identity**，记录 GitHub 可核验的 Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` 是 2026-10-10 11:32 UTC 后续提交，不能假称它就是此前原训练运行时的 root。对历史 Runtime Child `71e03c8` 提供具体日志与文件见证；如果无法取得真正 historical root，明确列 `HISTORICAL_ROOT_UNKNOWN`，不要虚构。

提出**实际可执行但本轮不启动**的候选恢复命令：当前形式 Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` + Child `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`，原 Formal30k Job Name 与输出根（**不是** C1 Shadow 输出根）、`--phase resume`、`--expected-root` 与实际 checkout 解析一致、`--expected-child` 固定当前 `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`，**明确**在 launcher 环境使用 `PSM_V3_COMPACT_CACHED_VIDEO=0 PSM_V3_SHARED_EPISODE_CACHE=0`、`--num-workers 0`；这是新增 raw Async Prefetch workers=0，原 JointDataLoader worker=4 不应错改。所有原始 Formal30k `T16/B8/GA2/K4/world8/Hpred16/max_iter30000/warmup500/save_iter100` 完全保留，不变更权威 dataset/Index/cache、BaseCheckpoint/Tokenize、EMA/Optimizer allowlist/GradScaler 等。

同一原 Job 真正的 `save_dirname/latest_checkpoint.txt`→iter800 必须有完整五组件和 per-rank sidecar；确认 `warm_start=False`、`strict_resume=True`、`load_training_state=True`、配置摘要 `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`；所有8 rank FSDP2 Optimizer/Scheduler/RNG/Local 恢复已经由 C1 Shadow 验证，不必重新 C1。CPU-only 再核对当前 OFF/OFF/Raw prefetch0 对历史 old dense data path的源码证据和此前 B1/B2/D0/D1 Reference 的已存在证据，发现新的真实数值/接口变更必须报告，不得声称字节级旧新版完全相同。

列出最终操作上的“损坏隔离/首异常暂停/不得自动重试/DCP写入与恢复路径”策略：原 job 文件在启动后 Trainer constructor可能写入config.yaml/pkl，CPU证据阶段不得触发；预先做只读目录清单和小文件SHA，实际 Resume 必须等下一份独立 GPT 授权。提供当前GPU分享许可/robotwin负载是否已知（本轮CPU读即可，不能假定许可）；候选最小健康门槛 iter801第一个成功optimizer commit、无自动继续错误/Gate指示、monitor和故障STOP条件。 **不要执行 GPU step 800→801或真实 Resume。**

R0 仅返回 `SAME_MODE_RESUME_READY_CANDIDATE` / `SAME_MODE_RESUME_BLOCKED`，若历史文件身份不足请显式界定，不得以断言代替。

## S1（并行，不能阻塞 R0 本身）— S0 新验收 Design REQUEST_CHANGES 精确修正

- **必须修复直接 config/digest 冲突：** S0 报告 §5.3 `save500/warmup100` 与正式参数 `save100/warmup500` 不同，实际 `examples/psm_wma_robocasa_corrected_phase5.py::config_digest()` 把两者纳入 schedule SHA。保留 `max_iter30000/warmup500/save_iter100`，freeze `70e9867f...`；不得改 recipe 伪装成同状态。
- **修复等价统计逻辑：**普通 Wilcoxon 的非显著不能证明相等；R3/模式最多为工程烟测，不能宣称独立rank/FQN带来统计power。若要有限工程验收，独立给出预先冻结且有外部依据的 **non-inferiority margin** 与8 rank/各family测量标准；若要统计等价，需 run-level CI/TOST及power，必要时更多独立重复。报告`median跨/内 ≤2`与`10×p90`依据，不能抄已观察的噪声值。若找不到可靠margin，明确`D1_S_DESIGN_BLOCKED`，不新跑GPU。
- **纠正实验 Input/capture:** 方案须涵盖真生产完整314 selected参数/Rank，四个w0不得重复算；真实.grad来源、零/空 shard EQUAL_ZERO；canonical semantic input fingerprint对dense与compact保持逻辑值一致（仍记录storage/stride性能差）；同DCP、数据、RNG/CFG和严格Source identity保持一致。
- 可修改`/tmp` 外部 v3 diagnostic Harness/Comparator 的设计及CPU静态测试（DS权限只限外部诊断，不能碰production）；最好先给差异和CPU自检，不需要造另一个新GPU Gate。旧D1冻结FAIL永不消除，不允许`S1_PASS`就自行启动6次8×H100。
- 本轮`S1_DESIGN_PASS/REQUEST_CHANGES/BLOCKED`只指静态合同是否成熟，不意味着GPU/统计等价真实PASS。

## 一次性合并报告、禁止事项

R0/S1同时开始，各自独立`/tmp` evidence，结束后统一提交：
`DS_PRO_V3_M0_S0_NEXT_PARALLEL_R0_S1_READINESS_2026-10-12.md`。
需精确 Formal Pair + 历史 Child的区分、历史0/0证据、root SHA运行窗口事实、原 Formal Job严格恢复命令草案/运行资源条件、修正S0配置摘要/统计规则/全314覆盖、仍未验证项和证据路径。DS只读生产代码/数据/源DCP；不写仓库、不重新跑任何C1/D1 GPU、不启动训练、不修改原 Formal Job、不调任何 Checkpointer.train/Save/Fresh/Resume。完成停止交GPT；此文件本身**不是**原Formal30k恢复授权，也不是新D1-S GPU授权。
