# PSM-WMA V3 — Config Truth Mainline / HIGH-07 兼容性，新 Formal Pair 独立增量审核

日期：2026-10-21
Gate：`V3-CONFIG-TRUTH-MAINLINE-MERGE` + 新 Root/Child 的 iter4000 HIGH-07 静态兼容性
Scope：**新源码 Pair 的设计/生产增量 + 作者 CPU/static Evidence**；无目标机新 Pair 独立复验，无正式训练/模型加载/Action Server/Simulator/GPU 执行授权。

## 1. 精确 Formal Pair 与历史边界

- Implementation Root：`306d235046fe5d578503beb17a56f5c0eb0f5634`
- Child/Gitlink：`35b0ea1ccee9ee26653ed6589c484f0997d1c586`
- HIGH-07 Queue Blob：`4916918aca412a0abc6cb00e28f6053a351e07d8`
- 原已审 HIGH-06 Root/Child：`950b2dbc6ad112205153a18dc0f733812db30706` / `2d128ed5a07601cdd424974f99b67832eafeeb41`。两 SHA 均改变，本轮必须 fresh incremental review；不得沿用旧 Pair verdict。
- 原 HIGH-07 作者 Root：`320fda57c2cf450fbf0042183d7761a70b56f215` / 原 Child；独立隔离 Config Truth 源码 Root：`fa6471c0e9d12c54fa72a425d06abfc80ea491cc` / 新 Child。原 candidate Evidence HEAD：`fb670c2c30305abda318ae8e927b6d8cd7ad6298`。合并 docs HEAD：`e80a930949c5caad5af326a1cad04f1b01c81c92`，不作 Implementation Authority。
- Codex 交接：`docs/collab/codex/reviews/2026-10-21_V3_Config_truth_mainline_merge_handoff.md`；候选作者 Evidence：`docs/collab/codex/evidence/2026-10-21_V3_future_Phase5_config_truth_author_cpu/`；mainline source-pair核对证据：`docs/collab/codex/evidence/2026-10-21_V3_config_truth_merge/`；HIGH-07 原作者证据：`docs/collab/codex/evidence/2026-10-21_V3_iter4000_HIGH07_author_cpu/`。
- Owner 的后续明确授权仅覆盖**合入 V3 仓库**；不是在 G1 训练服务器部署、修改冻结 G1 资产、停止训练或执行 GPU。

## 2. Formal Verdict

**`APPROVE` — 当前 Formal Pair 的 CPU/static source-remediation Gate，仅本项 scope。**

Config-truth 新 job 代码和 HIGH-07 root Queue 在本审查范围内无新增生产 blocker。批准的含义是新 Pair 的限定源码整改与作者 CPU Evidences 相互匹配，**不代表**未来新 job 的真实 Config.validate/训练 DCP 可用、iter4000 模型能加载、动作有效、仿真能成功或 GPU 可执行。后续执行准入 Gate、DS 独立 CPU Gate 和 Owner 授权均为独立事项。

### 已 CLOSED / 未重开
- HIGH-06 normalized Checkpoint identity：先前已 CLOSED，当前 Queue 比较 `(requested_root/model).resolve()` 与 Child `/info.checkpoint`，没有修改/放宽。
- HIGH-07 frozen H16：当前 Root `--action-chunk-size 16`，新旧 Child `action_policy_server_robocasa.py` Git Blob 均为 `dc7757a5042d7d10a937c7611a159a95ca605072`，保持 CLI override > config32 > fallback；`/info.action_chunk_size` 仍严格校验16。对当前源码 Pair 的 CPU/static compatibility 认可，真实 server仍未测。
- HIGH-02 / MEDIUM-05 源码保留不变；撤销的 HIGH-01 非真实 blocker，严禁继续按死锁整改。

## 3. 直接代码与 Diff 审核

- GitHub V3 Implementation Tree 真正 Gitlink 是 `35b0ea1c...`。Child `2d128...`→`35b0...` 精确 diff：仅 `examples/psm_wma_robocasa_corrected_phase5.py` 修改约13行、`examples/psm_wma_robocasa_effective_config.py` 新增、两项旧测试定向扩展以及 `examples/psm_wma_robocasa_effective_config_test.py` 新增；Child model/checkpoint/trainer/Action Server/ExactWindow Policy 原实现未改。
- 与作者 Config-truth candidate Evidence HEAD 比较，合并 Root 的后续差异只有 SESSION/TODO/Inbox append 记录；无冲突后生产源码/Child/test/Evidence 重写。Root HIGH-07 Queue Blob 与作者 `320fda57...` 完全一致。
- `examples/psm_wma_robocasa_corrected_phase5.py:571-578`：`overlay_config()` 在常规新 job 加载旧 recipe 后，执行 `synchronize_legacy_chunk_length(config, contract)`，依实际缓存验证的 `CorrectedRoboCasaPolicyContract(H_pred16, chunk16, frames17)` 同步遗留兼容字段32→16。后续正式样本由 `get_action_robocasa_exact_window_cached_sft_dataset` / `ExactWindowSegmentProducer` / `GroupedLocalMemoryTrainer.bind_grouped_stream` 生产，不依赖 legacy dataset32 数据节点。
- `examples/psm_wma_robocasa_effective_config.py:23-71`：对所有 `dataloader_train` 的 `chunk_length/num_action_per_chunk` 进行扫描，仅允许 canonical RoboCasa Dataset 节点及有效一致的整数32/16遗留值；其它位置、冲突、bool/字符串/零/不支持值、与 raw15/state/fps20/camera/mode/max64 等合同不符均报错，后修改单一兼容字段；不是全局更改任意训练配方。
- `examples/psm_wma_robocasa_effective_config.py:72-135`：版本化 `effective_data_source` 分别记录模型几何、独立 Local-TTT T、真实 Producer 链和旧 dataloader **仅兼容字段**，经 `validate_effective_snapshot()` 校验。
- `examples/psm_wma_robocasa_corrected_phase5.py:297-355`：JobLifecycle 在新 Job canonical namespace claim 前检验 live Config，在 serializer 写入 Launch `config.yaml/config.pkl` 后、正式 canonical `config.yaml/config.pkl/v3_job_identity.json` 前再校验 YAML；每次 Launch 记录 provenance。现有 Job Identity schema、canonical config SHA、exclusive lease 及严格相同 source Pair resume 校验未更改；不从“写入候选文件”冒充已发布身份。
- root `scripts/eval_robocasa_18task_queue.py:275,365`：immutable evaluation protocol 明确 `server_action_chunk_size=16`，所有 worker 显式设置 `--action-chunk-size 16`；协议 `H_pred=16` 与 `R=action_horizon` 仍不同；strict `/info`、checkpoint/config/PID/port、worker error、lock 逻辑保持。
- 该组合 **不回写**已经运行 G1 的 `config.yaml/config.pkl/v3_job_identity.json` 或 `iter_000004000` Checkpoint；旧 G1 仍靠显式 Server CLI16 进行未来的推理 canary。新 source Pair/Root 使 evaluation run digest 变化，不能跨 Root/Child 复用旧 Root 的部分结果。

## 4. 直接 Evidence 与 Limitations

GPT 从 GitHub 精确源码与 Evidence 文件独立对照，不仅采信 Codex 文字：
- Config Truth 原作者 `gate.json`、`manifest.json`、`scope_proof.json`、`pytest.log/xml`、`baseline-red.log`、`witnesses.json` 和源码可核对。**47 passed +32 subtests**，JUnit 79 包含 bookkeeping 子测试，0fail/error/skip；Ruff0.12.7 check/format、语法与 diff检查全部RC0。20 warnings 为测试收集 mark 提醒，不是失败。原旧32 Red 由作者保留。
- Config 正例：原真实 Child `_extract_chunk_length_from_config` AST、原 `LazyConfig` YAML/PKL serializers、真实临时 tiny cache catalog、`SequencePlan` AST 与独立 Local-TTT T 证明32继承字段→16，17帧+raw15，旧字段兼容-only provenance；同源 Fresh→Resume canonical bytes/mtime未变；错字段/冲突/缺失/provenance/YAML drift 拒绝 canonical publication。
- 高07原作者另一套 `33 passed +50 subtests`、55deselected，Ruff/format/syntax PASS。Red旧 Queue 针对 Config32 的1/2/4-worker 运行全部 fail-closed，Green 通过1/2/4 Worker 4任务×5合成 Episode、错误/info32、错 checkpoint/config/mode、外部listener、worker exception 全部拒绝。使用 Child 固定代码的CLI优先级源AST；合并时 Root Queue Blob 与原证据完全相同。
- 合并时没有新运行，**同源码证据复用**成立，但不能宣称已在 V3 merged Pair 上独立执行；GPT 自己也未运行训练服务器 CPU/任何 GPU。
- 这批测试隔离了重量级模型/数据注册导入，故不证明完整 Cosmos Config.validate、真实 8×H100 torchrun、分布式 save/resume、模型加载、RoboCasa 真实 20 Episode 或可解码 MP4/SR。它们属于后续真实执行验收，而不是本次 source-static Gate 的通过证明。

## 5. 后续 Gate — 明确边界

1. **DS_PRO** 在 clean detached 精确 Root `306d2350...` / Child `35b0ea1c...` 做最小的**独立定向 CPU 复验**：Config Truth 原测试入口 inherited32→live/saved YAML/PKL→Child parse16、legacy conflict/invalid fail-before-mutate、Live/YAML drift阻止发布、同 Pair Fresh→Resume canonical identity不变，以及 HIGH-07 1/2/4 Worker actual CLI16/Info fail-closed 的 CPU HTTP stand-in；Ruff/format and SHA/Blob binding，输出命令、RC、raw logs和 witnesses。无需重跑前面已经关闭的所有旧项。失败须 STOP 反馈，不擅改代码。
2. 当前 G1 的训练、Config SHA 与Checkpoint**全部不动**。新 Config Truth 只面向今后独立的新 Corrected Phase5 job。禁止把训练服务器当前 G1 切到新 root/Child后强行 resume；同 source-pair 的保护应如实执行并禁止旧资产迁移。
3. **不需要 GPU 使用率/资源调查，不运行 nvidia-smi**（Owner已明确取消当前 DS GPU 核验）；`optim/` 不属于只做模型推理的前置条件。
4. Owner **自行决定**训练何时停与 GPU 何时释放。在另行明确授权的真实 execution Gate 中，先真实 Action Server model-only Checkpoint加载及 `/info` canary，再按新 run digest/isolated namespace 进行四任务×五Episode；实际失败归类保留原日志/JSON/MP4，不把合成 SR 当现实。

**APPROVE 仅限上述 CPU/static source Gate。没有真实训练、模型、服务、GPU、仿真或生产资产修改授权。**
