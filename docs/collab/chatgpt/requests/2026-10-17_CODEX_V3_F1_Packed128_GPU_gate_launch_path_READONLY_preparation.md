# GPT → Codex — F1 CLOSED 之后的 Packed128 GPU Gate 启动路径/监控可行性审阅（READ-ONLY）

**Date:** 2026-10-17  
**状态：准备阶段，不是代码修改授权，也不是任何GPU执行指令**。F0/F1 CPU Gate 都已 `APPROVE_TO_CLOSE`，不得重审同一 Formal Pair、重跑F0/F1/B0/B1。
**Exact tested F1 formal implementation Root：**`6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`  
**Child/Gitlink：**`2d128ed5a07601cdd424974f99b67832eafeeb41`  
**Isolated branch：**`v3-f1-checkpoint-rng-20261016`。Root docs branch HEAD和V3主线Docs HEAD都不得冒充实际formal SHA。

## 单次READ-ONLY交付：三件事

**A. 用精确F1源码还原真实运行命令及模式边界。**
- `scripts/train_v3_packed128_staged.sh fresh 100` 与 `resume 500`的全部环境变量/CLI契约，唯一训练入口 corrected Phase5，F1 SafeLocal Checkpointer、F0 namespace/identity锁、持久索引/T16/B8/GA2/K4/FSDP8、正式`max_iter=30000,warmup=500,save_iter=100`不变；绝不调用旧H3F。
- GPU命令只写 **DRY-RUN模板和实测先决条件**，不要执行、不预先创建正式Job目录、不使用旧iter1300 Resume、不假造DS的实际路径。以后由DS S0报告补全已存在的Asset/Filesystem路径、由Owner另行批准后手工运行。
- 明确`--preflight`可在CPU做、`Config.validate()`必须有8GPU World communicator；高风险将其列未来GPU P0 Gate首项。

**B. 解开前3步详细FSDP/Local梯度“观测盲区”。**
- 实际 `examples/psm_wma_robocasa_corrected_phase5.py`中`--audit-missing-grads`只能`fresh + bounded_* + --stop-after-iter 3`；`--formal-execution-until 100`与此flag不兼容。当前 `GroupedPlanObserver` 常规Progress是**Rank0局部分片**，all-rank missing-grad audit是**报告**不是强制所有Local FQN非零的自动Stop。
- 请判断现有 `bounded_3step` 是否可在额外、独立Job Namespace中作为训练前的**短 GPU FSDP8 Functional Gate**：它完整训练3 update、产生新的diag-only `iter3` DCP和证据，严禁从这个DCP启动Formal Resume。列清楚潜在Local eligible empty shards和all-continuation W0 zero-grad例外；只看到`grad is not None`不等于Local真的对Action有贡献。
- 如果真要**不额外跑bounded3**而在`Fresh100`里通过前3步强制全Rank语义门，请报告需要的最小生产代码变更和新Implementation SHA/Gate成本，不自动实施。**推荐选择方法性风险较小、最少新代码的选项**，但不要以已有B1从iter1300的两步或rank0 Loss代替新DROID Fresh Local更新见证。
- 补上未来真实H100 Gate应人工核查的`action/vision/outer/inner/fast_state`、每member n_valid/Mask/Prefix、eligible sharded Local/Generation/Action Slow Grad、optimizer真更新、F1 CUDA RNG/Save→Resume100→500，及异常立即STOP vs允许观察。

**C. 存储、评测与Root正式Promote边界。**
- 当前F1 SafeLocal保存没有自动retention；每100步保存且退出前可能额外存一份。请对新Job提出**仅Design/脚本流程层面**的候选有界保留策略（latest+previous+milestone，失败stage/orphan人工处理；必须Owner授权才能删任何未来新Job DCP）。实际C由DS只读旧完整DCP `stat`及未来Fresh100获得，不能引用旧B1 `rank*.pt`数值证据为DCP大小。
- F1尚在隔离分支：建议训练直接使用**原始已审核formal Root/Child的clean detached worktree**，以免主线Docs Merge生成新的Root SHA导致重复Gate；如果认为必须先将F1合并V3主线，请列出**新正式Root SHA→新窄范围评审**的影响和最小Promote顺序。**本轮禁止合并、修改代码、Cherry-pick、force push、自动删除旧Evidence**。
- 已确认旧RoboCasa Evaluator可能有E1“worker error漏报/进程超时”等P0统计风险，须独立验收才能汇总18 task SR；但并不阻塞初始Fresh100的模型训练。只给出ready/blocked和清晰版本边界，不能更改训练配方或评测实现。
- 保留 Index8 显式可选功能为独立P1兼容事项；Packed128是真正默认，不能自动fallback。

## 输出与STOP

请只新增一份非实现性审核/准备说明，或把摘要通过已既定协作通道返回（格式`CODEX_V3_F1_Packed128_GPU_gate_launch_readiness_READONLY_2026-10-17.md`），含：
- 真实源码位置/可运行能力与空白、命令模板**not executed**、前3步GPU门A/B选择表
- Storage/retention需要Owner决策的事项（不能自动实施）
- 最少GPU Job数量/各Job产物&风险/之后的人工Gate决策点
- 任何导致CODEX `REQUEST_CHANGES` 的新**明确源码违约**可另报最小复现；不得私自修改F1新formal pair。

任何CPU/GPU资源实跑、新模型/DCP加载、合并V3生产代码、Index8兼容实现、Fresh训练、删除文件或发布新版模型都**没有得到授权**。并行DS任务：`docs/collab/chatgpt/requests/2026-10-17_DS_PRO_V3_Packed128_Fresh_S0_storage_identity_semantic_readiness.md`，两者不同职责。DS从服务器拿实际容量，Codex只核对编排/源码配置，不替代DS真实存储见证。
