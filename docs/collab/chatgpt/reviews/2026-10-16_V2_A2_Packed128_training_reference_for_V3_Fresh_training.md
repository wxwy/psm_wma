# PSM-WMA V2 A2 Packed128 成功训练经验 → V3 RoboCasa Fresh Packed128：源码对照参考审核

**日期：**2026-10-16  
**类型：**READ-ONLY architecture/implementation reference audit；**不是**新的 V3 implementation Gate verdict，也不重开冻结 B1 GPU r2 的 `REQUEST_CHANGES`。无生产代码修改、无 GPU / DCP / 数据重验。

## 精确代码版本及 Evidence 层级

- **当前 V2 分支：**Root `b13024456e313b545871a0d5de07f5495848f4e3` / Child/Gitlink `e3dc9ecce0a4a7223245dc4f5b5efde7b709fd92`（已用 GitHub 远端 ref+tree 核实）。
- **V2 早期 A2 工程交付规范中的 canonical pair：**Root `2a9df880713da179aee141dd97c6b20a2b1d8c2e` / Child `22acb13c1fdb4f146e51e3c26f1759c73e6d0d7e`，见 `docs/build/PSM-WMA_Local_Memory_A2_delivery_runbook_2026-09-18.md`。这些是当时工程 Gate 的精确 pair，不等于自动确认9月19–20日长训所用的全部二进制 SHA。
- **V3 Frozen Packed128：**Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`。
- **V3 生产线上较新待选实现：**此前生产审查基线 Root `2f4dec43eb6b1e35b33a99d844d67813df5922a6` / Child `1d56320c08c56b0f8dd248919d152d81ae12ea7b`。新的 Fresh 训练必须重新锁定准备实际运行的 exact pair；不能直接借用 B1 Frozen Target 的 CPU Approval。
- **V2 成功长训 Evidence：**`artifacts/g0/localmem_ttt_a2_training_full_record_iter3288_2026-09-22.md` 和机器摘要 JSON 是 Owner 转存的 V2 LIBERO E003 A2 训练记录，原始完整远程日志不在仓库。8×A100-80GB、B_stream8/T16/GA2、FSDP，2026-09-19～20 训练至iter3288，最后完整ckpt iter3200，`raw_last_group_loss` 约16.35→0.79；iter3000 LIBERO 4-suite SR=358/400 (89.5%)。**不应把该结果作为 RoboCasa 训练/成功率证据**。更早9月18日 A2 工程验收手册的 GA16 是不同阶段的验证配置，不应与正式长训 GA2 混为一谈。
- V2 LIBERO iter3000 matched `required/init/off` ablation `358/400 / 350/400 / 280/400`：学得的 Local pathway 明显有效，但 **online fast-update 增量仅为 aggregate +2pp**，不能从 overall SR89.5% 推断 TTT 在线更新必然有强增益。

## V2 实现中值得复用的工程契约（非直接复制代码）

1. **真正的 128 Native Packed Batch：**V2 child `cosmos_framework/model/generator/mot/grouped_active_driver.py:84–160` 由8个 stable slot 各取1个T16段，`stack_segments`，`GroupedPlanMember` 约束一组同一 slot 只能出现一次；`grouped_active_runtime.py:131–215,294–332` 对 B/T 做成组 Fast scan 和 local-prefix Consumer gather；`omni_mot_model.py:1428–1476` 经 `custom_collate_fn([dict(payload) ...])` 一次真实 Native Forward/Backward，注入对齐的 `_psm_local_override=inputs.locals`。V3 `local_memory_grouped_window.py:51–95,162–223` 采用相同核心几何，`pack_native_member` 保留每个有效 Consumer 的 prefix和slot-major顺序，`local_memory_grouped.py:257–318` 对一个 GA 成员调用一次 `model_ddp.training_step(..., _local_memory_prefixes=prefixes)`。
2. **Loss 语义：**V2 `local_memory_segment.py:129–141` `GAWindowPlan.objective` 是 `(planned_n_valid/n_window)*consumer_loss + auxiliary_loss/ga_effective`；V2 `omni_mot_model.py:1462–1476` 将原生 native-total 拆分成 weighted primary 和 auxiliary（Dense 无 aux 时为 zero）。V3 `local_memory_grouped_window.py:200–208` 统一对 Native loss 乘以 `actual_n_valid/n_window`。当两个 GA 成员同128全满且 aux absent 时语义相符；有 auxiliary 且 terminal partial (DS实际 [122,128]) 时**不必相符**。这不是已经证明的 RoboCasa bug，须查实际 aux 有无/模型损失输出及终端权重，不能只看 overall Loss 下降。
3. **Fast State 因果性：**V2 `grouped_active_runtime.py:131–195` 依赖波批式扫同 slot chronology、fresh cursor0 不继承前 Episode、`create_graph=True` 保持 Local Slow Gradient、commit 前把 Fast State detach clone；V3 `local_memory_grouped_window.py:105–155,178–243` 在 candidate state 内扫描并通过 optimizer success 才发布 live window，保留跨 episode S0/prefix 约束。不能用旧 V2 owner/rollback 类整体覆盖 V3 的新事务边界。
4. **比较逻辑正确定位：**V2 `a2_native_validation.py:48–132` 的实际 Nano/MoT grouped-vs-scalar 测试使用 eval 模式、sigma=0.5、epsilon=0，在相同真实样本下比 grouped Loss 和 selected Grad（loss相对误差<=1%、Grad & Local Grad相对L2<=5%），并要求相同梯度参数集合。这是**控制噪声的模型局部功能检验**，不是新鲜重启/逐FQN/每元素的 CUDA bitwise 等价。V2 9月18日交付手册记录 grouped-vs-scalar Loss/Grad PASS、3-step GPU PASS、resume PASS；如需V3非parity语义验收，应仿照此**方法**，不直接将阈值用作当前失败的 B1 r2 放宽。
5. **Trainable slow-parameter / Checkpoint：**V2 `active_local_memory_launch.py:327–356` **明确要求 Local Slow 参数不为 DTensor，复制于各 Rank，广播同步并置于 Root FSDP之外**。V3 Frozen child `local_memory_grouped_window.py:116–129` 则检测 DTensor 并要求已注册 `model-owned scan_local_memory`；DS B1里 `slot_queries` 本地 shard rank4–7 是空形状，证实当前本地分片情况与 V2 不同。V2 成功运行**不能证明 V3 的 FSDP Local Slow 参数分片、每 Rank 梯度或恢复完全正确**。V2 实际长训保存到 iter3200 与3→4 short resume 的历史经验支持 DCP 设计，但 V3 新 Phase5 的自身 full-state Save→Resume 仍必须单独验收。

## 三个不可混淆的 V3 差异

- **数据/行动合同：**V2 LIBERO A2 成功经验主要来自 frame-wise-relative 机器人动作；V2 RoboCasa 旧 config `cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_robocasa_edge_all.py:76–130` 是 `ego` base / `local_history_action_dim=20`。V3 RoboCasa Frozen `examples/psm_wma_robocasa_corrected_phase5.py:199–212,280` 是 `raw15/state15`，缓存 VAE Latent & native data materialization 实现不同。任何不同实际动作/状态/相机语义的成功率**不具备自动传递性**。
- **Full vs terminal partial：**V2 `grouped_active_contract.py:28–34` 要求每行都是 full T16；V3 对 terminal partial 真实执行过 `[122,128]` GA 结构，需单独验证 valid mask、loss weight及 fast prefix/state。
- **计算/训练路径：**V2 是 model-internal active callback / special MoT native forwarding with replicated Local Slow; V3 是自定义 GroupedLocalMemoryTrainer + model-owned Local scan + FSDP/DTensor Local Slow 参数。Native Calling semantics 相似，但不同的源码、不同的 optimizer/distributed lifecycle，不能认作“已经跑过完全相同实现”。

## 当前对 V3 Fresh 的建议（不构成正式训练授权）

支持把 **V2 A2 视为已实证的 architecture proof**，不再把 `Index8↔Packed128` 严格逐FQN r2一致当作任何**新** Fresh 实验的必要目标。旧 B1 `REQUEST_CHANGES / NUMERIC_FAIL` 历史结论不改；新实验独立提出 Owner 授权和验收契约。

建议新 Fresh 路线的最小硬门只保留：
1. **锁定一个实际运行的 V3 Root/Child pair**（Frozen target 或后续生产 corrected；不能混用）；原 DROID baseline 初始化、raw15/camera/state/latent索引和 optimizer generation/action/local FQN inventory。
2. **端到端语义见证：**128 Consumer strict身份、prefix S0和动作/mask/latent正确对齐，full/terminal权重，forward/backward 后 Local slow 和 generation/action 参数在实际非空分片上非零/有限；未见aux则注明，如见aux且终端权重违反契约则必须修复。无需重跑B0/451GB。
3. **新命名空间正式可恢复 Checkpoint 短训：**真实 `fresh` → 100步 → 全8Rank DCP/latest写入完成，独立从保存点恢复至少下一步，并验证 optimizer/scheduler/dataloader/frontier/faststate状态；禁止拿 `--stop-after-iter` diagnostic-only输出当正式 Resume。
4. **监测与评测：**stepwise weighted outer/action/vision/local inner/fast norm/update、每Rank local梯度和非有限/缺失、学习率、step wall/peak/reserved、消费者身份/窗口counts、DCP、训练后固定 RoboCasa rollout（Local required/init/off 更能说明在线TTT作用）。Rank0 scalar telemetry不是整体8Rank evidence。
5. **空间门槛：**此前DS报告根盘仅剩47GB/95%且原B1 PT占595GB。新Fresh前必须有干净足额的独立输出与Checkpoint空间/配额；不能删除B1 raw evidence或覆盖原iter1300。若要归档/清理需另获Owner同意。

**REFERENCE-ONLY 结论：**V2 Packed128(A2)成功长训降低了V3方法性风险，但训练代码路径/FSDP Local/Action ABI/Terminal Partial差异仍保留可观测不到的潜在错误。后续独立 Fresh short-run Save→Resume +目标任务评测比继续追逐非同一实现的bitwise B1 parity更符合当前目标。没有形成新的实现 APPROVE、训练授权、GPU执行或 Gate M 关闭。
