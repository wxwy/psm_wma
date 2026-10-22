# G1 30k iter8900 — Owner 明确批准跨版本 Same-job Resume Compatibility（Codex 设计/实现请求）

日期：2026-10-22
**Owner 直接裁决：“我要求你放开”。** 该裁决推翻此前“必须回旧 Root/Child 才可恢复”的强制设计边界，批准在**当前新版本 V3**上为**唯一 G1 正式 Job**实现显式跨 Source Pair Resume 兼容通道。批准的是**受限整改的设计/代码/CPU**，不是当前可直接跳过检查/启动 GPU。不得将其变成任意 Job 的默认宽松检查。

## 1. 精确范围与已知身份证据

- Old G1 固定 Job：`packed128_droid_fresh_g1_20261019`，30k / 8×H100 / packed128，T16/B8/GA2/K4/world8、warmup500、save_iter100，截止 30k。SIGTERM 于 iter≈8902；最新确认 completed checkpoint `iter_000008900`。
- Owner/DS 报告冻结来源：old Root `e0121d34592d10323ede480eb3409468a07371ba`；old Child/Gitlink `2d128ed5a07601cdd424974f99b67832eafeeb41`；Config YAML SHA256 `f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e`，语义 digest/配置 digest 以 **现存冻结 G1 record 和原 launch/sidecar** 的完整64位实际值为准（用户报告只给前缀，不得硬编码猜测）。
- 新版 Child/Gitlink 目标 `35b0ea1ccee9ee26653ed6589c484f0997d1c586`；Owner/DS 报告训练机新 Root 本地以 `8610ad88...` 开头。**不把 8 位前缀当完整 SHA**。实际新版 Root 40位在 DS 当前训练机 read-only `git rev-parse HEAD` 精确固定；必须证实 Root Gitlink==actual Child；Root/Gitlink/wtree状态及可执行来源进入 provenance。
- GitHub Connector 本轮可见 V3 Head 为后续审核 docs commit `e04bf9a...`（代码 formal implementation此前为`ba91ebb7...`/Child `35b0...`），无法取得 DS 本地旧 Root `e012...` 对象及本地 `8610ad88...` 的完整 Git tree。不要假装这些已由 GPT 远端查证。Owner **明确不再要求以旧 Pair 实际 checkout 才恢复**；旧 frozen Job Identity 仍作为数据合同 authority。
- Job Namespace、canonical `config.yaml/config.pkl/v3_job_identity.json` 与已有所有 DCP、`latest_checkpoint.txt` 必须原样不可变。不回滚/重写线上 V3，不更新旧 Root 记录，不篡改 old SHA。
- 指定 Child 生产文件 `examples/psm_wma_robocasa_corrected_phase5.py` 的 Resume identity/readiness logic 和针对性 CPU 测试，可在 Root 的 launch facade 添加**传递新 flag**所必需的单行/有限支持。**禁止改**通用 Trainer、Optimizer、DCP、模型、Local Memory算法、数据生产器/采样器和冻结配置。若需额外修改，STOP 报告设计 blocker。

## 2. Owner Override 设计范围：显式仅 G1 Resume 开关

Codex 在隔离 branch 实施、不要直接运行：

1. 增加显式 `--owner-authorized-g1-cross-pair-resume`（实际命名可简化但必须可识别）：
   - 仅 `args.phase=="resume"` 且 `job_name=="packed128_droid_fresh_g1_20261019"`，旧 G1 Record 的 Frozen old Root/Child 严格等于上述 old Pair，canonical Config SHA 和旧 semantic digest 自校验均通过；否则拒绝；
   - 用此标志选择有明确审计的 legacy G1 exception，未给标志、Fresh、其他 Job **全部维持原严格校验**。不在新/旧 Job Namespace 中自动触发迁移；
   - 真正运行的 Child 与 Root Gitlink 必须都是精确新 Child `35b0...` 且 child clean；实际 Root 完整 SHA/状态与用户指定运行版本证据必须记录，不能借口“放开 Root”跳过 Gitlink/代码/状态检查。G1 override 可解除与旧 `record.root` 的 HEAD 等值约束，但 Root runtime identity 不得缺失；
   - 只允许 source pair 字段被明确重映射，不能把任意 old/new 模型语义改动隐藏于 owner override。
2. **`check_job_namespace` 必须保留所有非源身份检查**：冻结 record 的 `schema`、`namespace`、`native_batch_layout`、`diagnostic_only_do_not_resume`、`semantic_digest==hash(semantic)`、canonical `config.pkl/yaml` SHA 和 path/symlink 拒绝不变。计算候选 `training_identity` 与冻结 `record["semantic"]` 后仅归一化/排除最高层 **`root`、`child`** 两个字段作逐字段精确对比；model/optimizer/scheduler/trainer/model_parallel/data_setting、Checkpoint schedule、tokenizer/local memory参数、数据 Index/cache/source、RNG seed/T/B/GA/K/world8/H_pred16等任意差异继续 `BLOCKED`。明确报出残余字段 diff，不允许 broad `ignore`。
3. **关键：保留旧 G1 原 `config_digest`，禁止盲用新版 Source Pair 重算值进入 Dataloader。** 旧 `GroupedLocalMemoryStateCallback` 的每 rank `dataloader` sidecar `state["config_digest"]` 以及 `SegmentProvenance.config_digest` 都与原训练 `report["config_digest"]` 精确绑定。仅当除 root/child 之外完整训练语义一致、`config_digest(catalog, config,...)` 原始 `phase5_digest` 仍与冻结来源对应，允许使用冻结 `record["semantic"]` **仅用于历史 Source Pair 绑定摘要重建**：`original_config_digest = _json_digest({"phase5_digest": current_phase5_digest, "training_identity": frozen_record_semantic})`。须与此前 `launches/.../launch.json` 的原 `config_digest` 以及已保存 sidecar 的原配置摘要逐值相等才能放行。不得单纯屏蔽 Sidecar 的 `config_digest`/frontier/provenance 检查。运行时 producer/trainer 所传 digest 必须与 checkpoint 保持一致；所有 rank 同值。
4. **新旧配置事实区别处理**：旧 canonical `config.yaml` 中 legacy `dataset.chunk_length=32` 永不原地写入16。新 Child 的 `overlay_config` 会在**新 launch 的 RAM/launch-local config snapshot**镜像为16，并写 `effective_data_source`；这是允许的明确兼容结果，不准用新 launch 文件重建/覆盖旧 G1 canonical sha 或重写冻结 Job Identity。对 Trainer 实际训练语义与原 Producer H_pred16/17frame、raw15/state15、Local-TTT T16 精确保持。
5. **原始来源与新运行来源双轨记录**：新 `launches/<new_id>/launch.json` 或新 append-only sidecar 记录 `owner_override=true`、old frozen Root/Child、当前 runtime Root/Child/Gitlink、old semantic digest、原 `config_digest`、完整 frozen Config SHA、iter8900、是否核验 Sidecar/RNG/optimizer/scheduler continuity；新 audit path 在写任何 checkpoint 前落盘且不可更改现有旧身份文件。日志上不能声称二者原 SHA 一样。
6. **绝不解除训练真实存储合同**：保留 `_resume_checkpoint` 对 `iter_000008900` 下 `model/optim/scheduler/trainer` 全组件 metadata 和 `dataloader/rank_0..7.pkl` 的原检查（此处是 full-training resume，不是 model-only inference）；保留原训练与 DCP 加载、Optimizer、Scheduler、RNG、Cursor、Local-TTT Fast State/state restoration、global rank一致性/锁/禁止半步 resume。最新 completed iter 必须准确==8900。Owner 明确未允许绕过坏 shard/sidecar或复写旧 Checkpoint。

## 3. Acceptance：只做安全的 CPU / dry-run tests，不真正 resume GPU

- RED：原版本在新 Root/Child 上的 Source Pair/semantic 拒绝可复现；不得把已有 DCP/数据产物改掉。
- GREEN：仅指定 G1 + explicit Override 能在新 Root/Child CPU all-rank read-only `preflight` (或等价 mock rank一致性)下通过 **身份和 digest continuity**，`report["config_digest"]` 与冻结 launch/sidecar 完全相等，Local resumed callback 用原 `restore_grouped_local_state` /真实侧证据证明匹配；不实际创建权重/optimizer CUDA。
- NEGATIVE：无 flag、Fresh、其他 job、错误 old record Root/Child、错误 runtime Child/Gitlink、dirty Child、canonical SHA drift、模型/optimizer/scheduler/TTT/RNG/cache/source/H_pred/GA/B等字段漂移、Checkpoint不完整、Sidecar config_digest错、Iteration错误全部 fail closed；旧 G1 资产不存在任何 byte/mtime修改。
- 证明新 Config-truth overlay16 无法悄悄改变实际模型/梯度训练合同；原 `JobLifecycle.write_config` 对 canonical 不覆盖，只有以后经 Owner授权发生的合法新 launches/digest标签更新。
- 交新 exact Root Implementation SHA + Child/Gitlink、按源比较的 diff、CPU pytest/日志/Witness/最小迁移审计 JSON；不自动切换服务器 Worktree，不重写 G1，**提交后 STOP 交 GPT 独立增量验收**。

## 4. 执行授权

**Owner 本轮只允许跨 Pair Resume 身份整改 + CPU Evidence。** 此文不得当作 `torchrun`、真实 G1 `--phase resume`、GPU分配、停止别的训练或任何新 Checkpoint 写入许可。新 Pair CPU Gate 完整 CLOSE 后，Owner 再单独明确手动发起真实 iter8900→9000+ Resume。

历史技术审查旧 `REQUEST_CHANGES` 不覆盖此新 Owner 决定；本文件是由新 Owner override 产生的**设计合同变更**，不是无条件移除校验。
