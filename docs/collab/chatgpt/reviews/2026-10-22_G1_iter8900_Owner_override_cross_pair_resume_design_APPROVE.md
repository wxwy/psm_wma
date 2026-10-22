# PSM-WMA V3 — G1 iter8900 跨 Root/Child Resume Owner Override — Design Gate

日期：2026-10-22
Gate type：**Owner 修订的受限跨版本恢复设计/授权审查**（不同于历史严格 Same-job Gate，也非新的 Implementation Pair Code Gate）。
对象：原 G1 正式30k（8×H100 packed128）；旧冻结 Root/Child `e0121d34592d10323ede480eb3409468a07371ba` / `2d128ed5a07601cdd424974f99b67832eafeeb41`；完成于 `iter_000008900`；新 Child `35b0ea1ccee9ee26653ed6589c484f0997d1c586`；目标机当前 Root 自述前缀 `8610ad88`（完整SHA在 DS 现场核实）。
相应申请：`docs/collab/chatgpt/requests/2026-10-22_G1_iter8900_owner_authorized_cross_pair_resume_compatibility.md`。

## 1. Owner 最新授权与正式 Design Verdict

Owner 在审查此前 `docs/collab/chatgpt/reviews/2026-10-22_G1_iter8900_same_job_resume_cross_pair_override_design_review.md` 的 `REQUEST_CHANGES` 后，明确要求：“**我要求你放开**”。

**本新设计 Gate Verdict：`APPROVE` — 同意为且仅为 G1 正式 Job 提供在新版 V3 Root/Child 上，从旧 iter8900 DCP 继续训练的显式 Owner-Authorized Cross-pair Resume 兼容路径。**

本裁决**覆盖旧审查“必须还原旧 Root+Child 才能恢复”这一硬性要求**；不再以旧 Pair checkout 作为恢复前置。历史旧 review 的 `REQUEST_CHANGES` 是当时设计边界记录，不删改；本新 Owner 变更只 supersede 这一点。新代码不曾提交/审核，**不得声称已技术实现 APPROVE、已恢复成功或者已经可以启动 GPU**。

Owner 申请明确要求不修改冻结 `v3_job_identity.json`、`config.yaml/config.pkl`、`iter8900` Checkpoint 或旧 Job namespace，不改 Child 通用 Trainer/Optimizer/DCP/模型训练算法。允许在新版 Child 的 Phase5 Resume 身份入口增加**明示 G1 专用 Owner Override**，使恢复在旧版本快照和新版本执行代码间保持可审计边界；非 G1、Fresh、未授权 Resume 仍按旧 strict 规则。真实训练启动由 Owner 后续单独授权。

## 2. 本轮独立源码发现：单纯删 Root/Child 校验仍恢复不了 Local-TTT

直接查固定 Child `35b0ea1c...` 和原 Child `2d128...`：
- `examples/psm_wma_robocasa_corrected_phase5.py:158-205` 的 `check_job_namespace()` 对 frozen record root/child/semantic/canonical SHA严格拒绝；`:232-265` training_identity 嵌入 pair SHA；`:690-724` verify_root_child_lock 要求 HEAD 与 args.expected；`:876-877` `report["config_digest"]=_json_digest({"phase5_digest":digest,"training_identity":semantic})`，因此只改 source SHA 就会改变最终 `config_digest`。
- `cosmos_framework/trainer/local_memory_grouped_resume.py:56-127,169-192`，原 `GroupedLocalMemoryStateCallback` sidecar 的 `state["config_digest"]`、`SegmentProvenance.config_digest` 必须与 trainer/producer当前 `_grouped_config_digest` 字节相等。固定 `cosmos_framework/trainer/local_memory_grouped.py:100-150,240-260` 必须将此 digest 交还 restore callback；`cosmos_framework/model/generator/mot/robocasa_exact_window_local.py:313-320,430-439` Producer 将 digest 写入新生成 segment provenance。故只跳过 Root/Child/semantic 身份，会在真正恢复 fast-state/cursor 时继续失败。
- 当前新 Child `overlay_config` 仍会把遗留旧 dataset node 32镜像为新 launch 的16，`JobLifecycle.write_config` 对 live/YAML snapshot 做新检查。这不意味着允许改写**旧 canonical** config/hash/identity；旧状态和新执行 Config 事实必须双轨记录。

## 3. 已批准的最小实现合同 / Non-negotiable behavior

1. **显式仅 G1 的跨 Pair Resume 开关**，非默认、非通用忽略：约束 `phase=resume`、精确 Job Name、旧 `record.root=e012...` + `record.child=2d128...`、新 Runtime Child `35b0...`、完整新 Runtime Root SHA（现场精确值）、Child Gitlink/clean 仍必需。历史身份 record 不修改；在批准通道内不要求新 Runtime Root 与旧冻结 record root 相等。
2. 在允许 root/child 来源字段不等的同时，**严格逐项比对所有非来源 `training_identity` 字段**；含模型/Optimizer/Scheduler/trainer/model_parallel/data setting、checkpoint schedule、T/B/GA/K/world8、数据索引/来源/cache、RNG和模型权重来源。既有 canonical Config SHA、record semantic self-hash、namespace/diagnostic/symlink/layout约束保持。差异除两个 source SHA 外仍 `BLOCKED`；不允许 skip 整个 semantic comparison。
3. **严格留住冻结 G1 的旧 `config_digest`**：先证明新旧非源 Training identity 完全等价，再以 old frozen `record.semantic` 与按相同算法算得的 `phase5_digest` 形成兼容历史 `config_digest`；须与旧 launch 的 `config_digest`、Checkpoint sidecar 的实际 config_digest吻合；producer/trainer/callback 全部使用相同旧 digest，绝不跳过 Local-TTT state/provenance/frontier restore。若 phase5 digest不同，则 STOP，并不能从新源码/旧语义随便捏造旧摘要。
4. 完整模型/Optimizer/Scheduler/Trainer/dataloader rank0..7 sidecar、iteration/Cursor/fast-state、原同Job DCP存储检查不降低。此前 model-only inference `optim/` 可缺的勘误**不能用于full-training Resume**。
5. 恢复使用新源码而历史 G1 仍由 old source 训练是 **Owner-authorized cross-pair continuation**；不是“相同源 bytes”的虚构声明。新 launch 的 append-only audit 必须记录旧冻结和新运行 Root/Child、旧/新身份对照、旧 digest 延续、Checkpoint8900、具体 Owner flag、运行时环境和 drift检查结果；冻结老文件 bytes 不变。
6. GPU 训练/torchrun/真实resume仍待新的 Implementation Pair 独立 Code Gate、DS 新版本 CPU acceptance 与 Owner 后续启动命令单独批准。Codex 修改范围限于 Child Phase5 resume identity/check_job_namespace/preflight/report config digest 的显式特殊路径及最少 Root launcher flag 和针对性测试；不动通用 Trainer/DCP/优化器/模型/数据/其他训练任务。任何增加 scope 必须返工提审。

## 4. Code/Evidence Gate 验收

Codex 必须提交**新 Root Implementation SHA + Child/Gitlink SHA**、精确diff及CPU测试：
- 原设计红例：旧 G1在新 pair 无 override被拒绝；G1新 pair with explicit flag通过所有源版本与完整非源身份核验；含 old frozen semantic 的兼容摘要在 Sidecar/launch 一致，严格 `restore_grouped_local_state` 有真实路径或等价高保真 CPU回归证据；
- 不提供 override、其它Job/fresh、old record/hash不一致、child不洁净/Gitlink不同、非源 model/optimizer/schedule/local-RNG/cache/source/iteration drift和旧 Sidecar SHA/ConfigDigest mismatch均 fail-closed；
- 原 old G1 canonical Config/Identity/Checkpoint 的 byte/mtime hashes 不变，任何新 launch audit 只在单独授权后写入新记录；
- 定向 CPU all-rank preflight/old data sidecar reset parity 必须先 green；真实 GPU 30k resume 由 Owner单独执行，不因本设计通过自动授权。

## 5. 未解决但被 Owner 接受的证据边界

G1 旧 Root `e012...` 在本次 GitHub public API 查不到，目标训练机当地源码历史/backup ref 和最新 Root `8610ad88...` 的完整40位身份未被 GPT 读取。现有 Config/semantic digest在 DS 报告中只有前缀；新实现测试/验收必须从**真实冻结旧文件**中读取完整值，绝不按前缀造常量。Owner 的 explicit approve 可以允许**不恢复旧 Root checkout**，但不允许填造旧 Digest、跳过当前源码来源记录或假称完整 Checkpoint 必然通过。

**总结：设计 Gate 已按 Owner override 放开；真正 Resume 执行仍为分开的 Gate。**
