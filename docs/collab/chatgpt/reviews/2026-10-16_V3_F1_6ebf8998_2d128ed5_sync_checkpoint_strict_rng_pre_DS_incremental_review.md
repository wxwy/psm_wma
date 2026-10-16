# PSM-WMA V3 F1 — Sync Checkpoint + Strict RNG | GPT Fresh Incremental Review (pre-DS Evidence)

**日期：**2026-10-16  
**审核身份：**GPT — 独立 Design / Code / Evidence / Gate 审核者  
**Gate：**`V3_F1_SYNC_LOCAL_DCP_STRICT_RNG_CPU_GATE`  
**正式 Implementation Root：**`6ebf8998a7935f2ad690bb547c5db5e5a4322e6d`  
**正式 Child / Root Gitlink：**`2d128ed5a07601cdd424974f99b67832eafeeb41`  
**隔离分支：**`v3-f1-checkpoint-rng-20261016`（文档后继 HEAD `ccfd900bc35fcd39ca9953aa7aa55b85398300ad` **不等于** formal implementation Root）。  
**已关闭 F0 基线：**Root `9e51c94a6d5dba41bd37423b9db8e634ca433789` / Child `7cae7c3049310ccc3b7e44ce9769534e152d1f26`，F0 CPU-only `APPROVE_TO_CLOSE` 见 `2026-10-16_V3_F0_9e51c94a_7cae7c30_DS_CPU_Evidence_closeout.md`。  
**V3 主分支（审核时）：**Docs HEAD `e2a11445bdb5451605a5ef33da312690931845ff`，其生产 Gitlink 仍为旧 `1d56320c08c56b0f8dd248919d152d81ae12ea7b`；尚未合并 F1。  
**冻结验收契约：**`docs/build/PSM-WMA_V3_F1_sync_checkpoint_strict_rng_contract_2026-10-16.md`，作者提供 SHA256 `aa3f7c6db2bdf5a7c193de1398b7ff1aa81b59b08554552f6fa86fc3e2748185`。  
**Codex 作者交接：**`docs/collab/codex/reviews/2026-10-16_V3_F1_sync_checkpoint_strict_rng_author_handoff.md`，57测试方法 +53 subtest 作者 CPU 绿，尚无 DS 独立新 SHA CPU 验收。  
**正式 verdict：`REQUEST_CHANGES` — EVIDENCE-ONLY。** 本轮从精确源码差异中**未确认新的生产语义 blocker**，但独立 CPU/Gloo/真实配置/目标持久卷 Evidence 缺失，不得把作者测试视为 Gate closure；后续只需补这些 Evidence，formal pair 未变则不再技术复审。

## 1. GitHub 精确增量与范围

通过 GitHub 直接读取精确 Root Tree、Child 代码、Child/F0 compare 与 Codex 作者报告：

- `Child 2d128ed5` **比 F0 Child `7cae7c30` ahead 2 commits**；中间生产实现 `c0fc4cadccedb5838d3f2e512ea96179a3c969e9`，最后 `2d128ed5` 只增加真实双 Rank 的 Model/Optim/Local/RNG Restore 正向测试。两者生产代码内容相同。
- 总 Child 变更 **四个文件**：`cosmos_framework/checkpoint/dcp.py` (+418/-1)，`cosmos_framework/checkpoint/dcp_local_safety_test.py` (新增839行)，`cosmos_framework/trainer/__init__.py` (+4/-1)，`examples/psm_wma_robocasa_corrected_phase5.py` (+7/-1)。
- Root 正式 `6ebf8998` Gitlink 精确 `2d128ed5`；其他 Root 生产入口/Native/Local/optimizer 并未在此 Gate 变更。Root 从上一 F0 baseline 的差异主要为 review/ledger、F1 frozen contract 与 Gitlink。新的正式 Pair 需要 fresh incremental review；旧 F0 通过不能自动授权 F1。
- 完全未涉及/不重复：历史 B1 `a3239591` 及 Source/Target 冻结数值 FAIL、旧 Index8/iter1300 DCP、B0 数据索引451GB验证、旧关闭的149项单测、E1/E2、性能优化、Local-TTT 数值算法、原始 V2。

## 2. 源码与冻结契约的逐项核查

### F1-CODE-01 — 正向机制初审：符合 all-rank 发布顺序，非 Gate approval

**代码：**Child `cosmos_framework/checkpoint/dcp.py:1304–1419,1500–1537,1589–1703`。

- 新独立 `SafeLocalDistributedCheckpointer` 为 opt-in，校验同步、本地、strict_resume；创建带超时的 CPU Gloo coordination group；`_checked` 对阶段成功/异常进行全 Rank `all_gather_object`，`_agree_identity` 检查不同 rank iteration/source。
- `save` 先执行所有 Rank 的状态准备和 `model/optim/scheduler/trainer` DCP Save；每个组件经过全 Rank 确认；Rank-local dataloader Sidecar 在同文件系统 tmp 写入/flush/fsync/replace/dir fsync 后再得到大小/SHA；汇集8 Rank witness；仅 Rank0 确认全部 DCP metadata/size 与 Sidecar hash 后创建 complete.v1.json、rename staged→final、原子替换 latest；出版结果再经全 Rank acknowledgement。因此不再是旧实现中 Rank0 写完其 Sidecar 就能独自发布 latest 的流程。
- `_read_latest_checkpoint_file` 和 `validate_checkpoint` 对格式、marker、World Size、component metadata和shard extent、per-rank Sidecar SHA以及RNG metadata fail-closed；`_publish` 在pointer replace之后发生fsync失败时尝试恢复旧pointer。**新旧 pointer 的可见性和崩溃后磁盘持久性不能做无条件保证**；合同清楚区分post-commit uncertainty和fail-before-publish，且失败 staging/完整孤儿不覆盖、不自动删除。
- Metadata和Sidecar做SHA，但模型/Optimizer大Shard只检查metadata引用的存在/size/extent，**不等于大Shard bytes完整性hash**；该可观测性契约已经在frozen设计中声明，不得在新GPU报告中表述为全量字节核验。
- 暂未发现违反冻结发布次序的明确源代码反例。剩余：分布式DCP+Gloo真实完整依赖下的故障测试、预期ext4/fsync/rename目标卷、以及未来H100上NCCL+Gloo混合通信与真实FSDP/DTensor DCP功能门，必须独立验证，不能推断全部通过。

### F1-CODE-02 — strict per-rank RNG / no reseed机制初审：与契约吻合

**代码：**Child `cosmos_framework/checkpoint/dcp.py:1422–1497,1539–1579`，`cosmos_framework/trainer/__init__.py:343–351`。

- `_validate_rng_metadata` 要求精确 `rng_state_0..rng_state_{world-1}` 的9个叶子全量存在，检查torch dtype/shape、单chunk完整覆盖、底层存储索引；`_validate_rng_payload` 校验 Torch CPU/CUDA uint8/size、NumPy/Python packed payload与rank/world/schema，恢复前全 Rank ack。丢失整体rank或单叶子不能隐式以本地初态填充。
- `_load_strict_trainer` 在load/验证后allrank确认，再设置scaler和RNG；失败尝试回滚旧随机状态，且不设置成功 flag。完成后 `rng_restored_from_same_job=True`；Base `load` 入口先重置为False。
- Trainer仅在未成功从same-job恢复时执行确定性模式reseed（不再靠iteration>0判断）；Fresh-from-DROID model-only仍可正常设Seed。
- 现有作者测试使用真CPU Torch/DCP/Gloo，而CUDA RNG是替身：**不能宣称真实CUDA/H100恢复一致性**。该项在新Fresh的真实Resume100→101里另立GPU Gate。
- 暂未发现新的真实生产违规；独立验收需要验证实际dtype/rank-bound/缺失叶子/不同rank next-draw以及deterministic分支，并检查旧Legacy路径回归。

### F1-CODE-03 — 新Profile接线与配置身份

**代码：**Child `examples/psm_wma_robocasa_corrected_phase5.py:226–239,580–590`；`cosmos_framework/trainer/__init__.py:178–184`。

- 仅 corrected Phase5 选择 `SafeLocalDistributedCheckpointer`，关闭async且strict=true，新增`psm_v3_sync_local_v1`进入训练语义；旧默认Packed128、raw15、T16/B8/GA2/K4、30000/500/100未被修改。
- 具体目标 Checkpointer 配置通过 `config.checkpoint.type={"_target_":SafeLocalDistributedCheckpointer}`，需在实际 Cosmos Hydra/instantiate + Config validate/freeze/serializer 环境下确认工厂可实例化且Runtime Type正确。作者只用 Cosmos Config/Log的外部依赖替身；独立 full-env配置证明是尚未填补的 Evidence。
- 保留真实 DROID model-only Fresh无训练RNG；禁止非same-job且load_training_state=true 的外部训练状态warm-start。F0 Job identity/namespace机制没有被减弱。

## 3. CURRENT blockers — Evidence-only（无已确认生产 Bug）

### F1-EVID-01 — HIGH / 真实 CPU 多Rank同步DCP与失败语义尚未独立验收

- **Source:** `dcp.py:1345–1364,1589–1703`，test `checkpoint/dcp_local_safety_test.py`。
- **Frozen contract:** Stage / each DCP component / Local Sidecar / complete marker / latest的顺序与fail-close；延迟rank、同Rank失败、DCP组件失败、首次失败与已有latest保留、bad fsync/marker/pointer、hard-exit/stall的限时错误传播。
- **Missing Evidence:** 只有作者 CPU 环境57测试/53 subtest全绿；DS尚未在指定clean Pair与完整V2/V3依赖、目标持久卷的真实CPU DCP/Gloo再执行。
- **Acceptance:** DS在clean exact Pair完成`docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_F1_sync_checkpoint_strict_rng_CPU_acceptance_6ebf8998.md` §B及§D，真实CPU tiny tensor和2 Rank Gloo负例，独立 reader核验before/after latest marker/Sidecar/extent，rank延迟/失败/死进程/timeout都返回预期结果；无新skip/忽略。若验证暴露生产违约，应升级为Production finding而非仅调整测试。

### F1-EVID-02 — HIGH / strict rank RNG真实依赖/恢复证据缺失

- **Source:** `dcp.py:1422–1497,1539–1579`，`trainer/__init__.py:343–351`。
- **Frozen contract:** same-job每rank9个RNG叶子完整、交叉rank绑定、缺/截断/错type拒绝、restore after validation、deterministic resume不reseed、model-only Fresh仍有正确seed。
- **Missing Evidence:** DS full-dependency同Pair完整负例+正向恢复未执行，作者CPU CUDA字节为替身。
- **Acceptance:** DS 2 Rank正向恢复真实CPU model/optim/scheduler/local/rank-bound RNG+下一次Python/NumPy/Torch抽样，逐类负例，确认真实Trainer deterministic分支不重设Seed，legacy path不回归。实际CUDA RNG需未来单独授权GPU恢复Gate证明，**不以CPU模拟批准CUDA**。

### F1-EVID-03 — MEDIUM / 真实配置Factory与受影响回归未独立验收

- **Source:** `phase5.py:226–239,580–590`，`trainer/__init__.py:178–184`。
- **Frozen contract:** corrected Phase5真实resolved配置选择safe class、sync/local/strict mode且能通过Config.validate/freeze/serializer；正式Fresh/Resume语义digest一致且安全profile身份正确；未变的F0/GroupedTrainer/旧DCP regressions不受影响。
- **Missing Evidence:** 作者CPU只用stub配置信息；真实依赖中Factory能否instantiate待DS验证。
- **Acceptance:** DS用完整Cosmos环境 read-only Preflight验证同一Pair、无任何模型/DCP载荷读取、非训练GPU；F0 tests + Phase5/Grouped/DCP touched regression全绿，受影响Source静态Ruff/format/syntax全绿。保留测试实际RC和legitimate skip原因。用新Pair而非V3旧Mainline。

### F1-EVID-04 — MEDIUM / 目标持久卷fsync/rename故障行为未独立验收

- **Source:** `dcp.py:1366–1387,1582–1587,1665–1703`。
- **Frozen contract:** 本地同FS侧写tmp、原子rename、fsync、异常保留完整old latest并拒绝半成品，完整Orphan只可显式处置。
- **Missing Evidence:** 作者CPU临时FS不能替代DS真实输出卷行为；系统盘/持久卷磁盘free还会变化。
- **Acceptance:** DS在新隔离合成fixture目录的目标持久卷执行 tiny CPU 读写/原子失败场景、文件大小/SHA和独立reader; 不触碰历史Job、B1 595GB、原iter1300。

## 4. Evidence accounting, scope, next action

- 作者报告 `57 test methods (29 F1+28 F0) +53 subtests`、JUnit头`tests=110`；方法数/pytest collection/JUnit subTest计数不可相加称为110个独立testcases。具体通过事实以独立DS输出为准。
- Final Child `2d128ed5` 之前的 `c0fc4cad` 是生产代码实现，最后一次提交仅补双Rank正向恢复test；CPU验收和F1 verdict仍绑定最新**全部pair**，不能使用作者最初 preliminary Root `264cff2f` 取代正式 `6ebf8998`。
- **Existing DS request already complete:** `docs/collab/chatgpt/requests/2026-10-16_DS_PRO_V3_F1_sync_checkpoint_strict_rng_CPU_acceptance_6ebf8998.md`。不要产生重复实验指令；按其A/B/C/D全项实施，任一真实错误停机移交GPT判断，不由DS修改GitHub。
- B0、F0既有闭门、B1历史NUMERIC FAIL及全部旧DCP不变。F1 CPU成功只关闭本Gate，不授权GPU/真实DCP/正式训练或Claim Index8可运行。新Fresh实施/存储容量和有界checkpoint策略是后续独立Gate：不得以B1 numeric PT文件大小当DCP实测容量。
- **Verdict literal = `REQUEST_CHANGES` (Evidence-only).** 只有F1 detailed Review + canonical `CODEX_INBOX_2026-10-15_CONTINUATION.md` 均成功保存才算正式落盘；DS新Evidence完整后对**未变化formal pair**只评审缺失Evidence，不重新技术审查。
