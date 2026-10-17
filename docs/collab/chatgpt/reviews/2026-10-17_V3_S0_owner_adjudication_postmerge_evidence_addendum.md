# V3 S0 Owner 裁决增量核对 — Post-merge Evidence-only Addendum

- 日期：2026-10-17
- 性质：**Owner 提供报告 §9 的只读证据增量核对，不是新技术 Formal Gate，不重审 F0/F1，不发布 GPU 授权。**
- 原 S0 Formal Root/Child：`6ebf8998a7935f2ad690bb547c5db5e5a4322e6d` / `2d128ed5a07601cdd424974f99b67832eafeeb41`。
- 已核验 V3 两父 merge implementation Root：`dd6e040ea8229fc3ce81259952444f82dd9897b2`；Child Gitlink 保持 `2d128ed5a07601cdd424974f99b67832eafeeb41`。审核时 V3 docs HEAD `c536e68a315fb8ef9e7c2f7b23a50ec1d1664b30`，**不可替代 implementation Root**。
- 已有原 S0 正式审核：`docs/collab/chatgpt/reviews/2026-10-17_V3_Packed128_DROID_Fresh_S0_DS_Codex_readiness_evidence_review.md`，`APPROVE_TO_CLOSE` **仅限 S0 READ-ONLY EVIDENCE**。本记录不生成第二个同 Pair 技术 verdict。

## 输入与可信度分层

Owner 本轮提供《PSM-WMA V3 — DS_PRO Packed128 DROID Fresh S0 只读就绪验收》§1–§9（§9 为 2026-10-17 后补 Owner 裁决）。GPT 读取原文并远端核对 V3 的 S0 正式审核、F0/F1 promotion merge、post-merge CPU-only request 与 target `/mnt/data1` FS-only request。训练服务器原始 `/tmp/psm_v3_s0_20261017/{s0_readiness.json,preflight_world8.log,c_old_breakdown.json}`、GPU占用、旧 DCP fingerprint、目标卷实时状态无法在本轮独立获取；**DS 报告数值不冒称 GPT 实测**。

Owner 引用三个决策提交简写 `b5f34a12` / `18295c3a` / `26f1038f`：GitHub 根仓远端 commit API 本轮均未返回对应 commit；V3 continuation Inbox 未包含三 SHA。应视为**Owner 提供报告中的裁决已可阅读，但此前 SHA 不是已核验远端落盘证据**。本补充 review 自身将裁决留痕，不替代其原始本地证据。

## 四项 Gate 增量结论

1. **S0-CONFIG：原先 CLOSED，post-merge 身份 PENDING。** 原 `config_digest=65ad8bce52aed0feaecbf399828667683f7a461487f870e0493dad8766abd01f` 绑定旧 Root `6ebf8998...`；新训练必须在 clean `dd6e040e...` / Child `2d128ed5...` 下单独执行只读 world8 preflight，freeze 新 digest，验证 no Job write。已派发：`docs/collab/chatgpt/requests/2026-10-17_DS_PRO_V3_post_merge_dd6e040e_CPU_identity_preflight_only.md`。真正8-GPU `Config.validate()` 仍是后续 GPU Gate HARD_P0。
2. **S0-STORE：Owner 已通过报告选择输出父路径 `/mnt/data1/data_v2_0617/v3_packed128_fresh`，代码不搬移。** Owner报告称该子目录可写、`/mnt/data1` ~338 GiB available；它们是**报告当时状态**。mkdir/write 成功不等于同一目标卷的 mkdir-exclusive、flock、temp/fsync/rename/dir-fsync 的完整并发和原子验证；已另行发出 `docs/collab/chatgpt/requests/2026-10-17_DS_PRO_V3_G0_data1_target_fs_prelaunch_CPU_only.md`。旧 Index8 iter1300 DCP `C_old=24,897,732,763B≈23.19GiB` 只能用于暂估。G0 诊断1份 + G1/G2正式5份 + W50GiB + 应急2份估算约235.5GiB；额外 Resume101 则约258.7GiB。新 C3/C100 未实测；共享容量及 quota 未闭环。
3. **Checkpoint Retention：Owner 选择手动清理，尊重决策，绝不擅自删除。** F1 代码并无自动滚动保留；最多300个正式整百 DCP 不可能直接全部保留在现有卷。手动方案不单独阻塞 G0/G1/经容量预算的 G2→500，但放行长训前必须先明确人工检查频率、protected keep-set 与剩余容量触发停止线。Owner报告称已人工清掉旧 Index8 的部分 DCP，留下500/1000/1300；这是本次 §9 相对原§7的**后续时间变化**，非同时矛盾；原 iter1300 fingerprint完整性和旧证据保留仅为DS声称，未独立读取。
4. **S0-SEMANTIC/GPU Scheme：** 选择 A（独立 `bounded_3step` + 24份 rank×step Missing-Gradient Audit）与 S0 风险分析一致，不要求新代码 SHA。G0 审计必须逐项检查 full-rank 报告、eligible local shard/expected parameter coverage/grad None、NaN、iter3 F1 DCP atomic complete/latest；即便 missing=0 也**不能证明**所有 Local Slow gradient数值非零、optimizer moments发生变化或者 Local→Action 因果效应。它们继续处于后续 GPU/Eval Gate 的明确未覆盖集合。Index8 显式兼容仍是 P1，不阻塞 Packed-only Fresh。

## 最终状态 / 最小下一步

- **S0 READ-ONLY EVIDENCE：维持原 APPROVE_TO_CLOSE；无新正式技术 verdict。**
- **SOURCE_MERGE：结构核验已完成**，正式执行 Root 固定 `dd6e040ea8229fc3ce81259952444f82dd9897b2`，而不是后来 docs HEAD。
- **POST-MERGE CPU IDENTITY 与 DATA1_TARGET_FS：等待 DS 有命令/RC/JSON/容量及未写 Job 目录证据。** 不重做已关闭 F0/F1 CPU / 旧 B1。
- **G0_GPU_EXECUTION_RELEASE：BLOCKED**。Owner报告显示2026-10-17当时8×H100正被他人作业占用；这仅为时点报告。需要重新确认设备可用并取得**单独**的 G0 单次 GPU Owner 授权，先做 GPU `Config.validate()` HARD_P0，再考虑 bounded3。选择执行顺序不等于实际放行。
- 不授权 torchrun、真实 DROID load、训练、G1 Fresh100、G2 Resume、仿真、旧或新 DCP 删除；无生产代码修改。
