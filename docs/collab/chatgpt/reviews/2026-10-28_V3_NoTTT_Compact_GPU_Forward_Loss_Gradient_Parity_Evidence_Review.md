# PSM-WMA V3 — No-TTT Compact=0/1 GPU Native Forward/Loss/Gradient Parity：独立 Evidence Review

- 日期：2026-10-28；角色：GPT Independent Evidence Reviewer。
- **Verdict：`REQUEST_CHANGES`（Evidence-only；生产 implementation 当前未发现新 blocker）。GPU数值等价 Gate **没有**达成冻结的所有验收项，不能以“梯度范数落入重复运行区间”直接认定梯度等价。**
- Frozen contract：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md`；Owner后续许可 GPU4–7 **共存**，不自动改写上述 Gate的数学/模型更新边界。
- 与另一 Gate区分：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_Coresident_Second_Job_StagePlan.md` 允许独立新Job **一次** `fresh 1` 共存Smoke；它不是“不执行optimizer”的数值Parity Harness。
- Source formal implementation：Root基线 `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；Child/Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`（当前远端一致）。DS宣称的本地 Root `8c3d0562` 在本轮GitHub远端不可获取，无法独立证明仅3个Evidence文档差异；不能替代真实formal pair。
- Evidence：`docs/collab/chatgpt/evidence/2026-10-28_DS_PRO_NoTTT_Compact_GPU_Three_Fresh1_Report.md`（来自用户上报，并非GPT亲自执行或远端抓取原始Rank JSONL）。正式V3远端目前未见该3 Job的原始 `monitor/train_rank0.jsonl` 和四Rank参数对比工具/JSON。

## 1. 已支持的有限结论

- 三个独立 `fresh 1` 都报告同样的 `outer_loss=14.937467575073242`、`action_loss=1.2275960445404053`、`vision_loss=0.2661505937576294`；所提供标量在报告精度上完全相同。**标量Loss等价的采样结论受支持**。
- 三次报告相同rank0 consumer identity digest（短写`9207fc67…7830`）、`512`有效Consumer（每rank 8任务×64）、no missing/nonfinite gradients、`telemetry_errors=[]`。这些证据与CPU cached-latent逻辑一致，但**Digest不是逐Rank全部输入Tensor逐值比较**。
- Rank0 GPU grad norm A`3.70625925`，B`3.70767379`，C`3.70868754`，报告的相对差`0.038%`和同Compact1模式漂移`0.065%`算术正确。这是**模型有可用梯度/Run-to-run范数差异很小**的证据，但不能推出所有梯度数值均等价。
- DS称三Job均完成正式训练一次和完整DCP保存；该结果是功能Smoke而非本 frozen Gate所要求的原始无Optimizer Parity。

## 2. Findings

### F1 — HIGH / Evidence-only：逐参数梯度Parity未执行，不可判PASS

- **file:line**：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md:38-39,47-49,68-69`；生产`cosmos_framework/trainer/matched_no_ttt.py:316-342`；`examples/psm_wma_robocasa_corrected_telemetry.py:365-398`。
- **Root cause**：提供的数值 `total_grad_norm_rank_local` 仅为Rank0本地所有选定梯度Shard的L2范数总量，未比较逐参数完整梯度的`None mask`、tensor形状/dtype、finite、`torch.allclose`，也没有Rank1–3的梯度数值。
- **Frozen contract violation**：冻结要求四Rank所有`GENERATION_KEYS`可训练参数的FSDP shard `torch.allclose(rtol=1e-3,atol=1e-5)`，输出max_abs、relative_L2、worst10和group coverage；明确“仅grad norm接近不能PASS”。
- **Acceptance remediation**：用**隔离、只读的4Rank FSDP2 Parity Harness**，对同权重/Buffer、同Frozen CPU+device Batch、同Rank RNG与iteration先后运行Dense/Compact各一次，调用 Native`move_cached_native_batch→training_step→weighted.backward`，不执行optimizer/scheduler step或写DCP；在同一Rank本地对每个选中参数对照`None mask/shape/dtype/finite/逐元素allclose`并输出all ranks group coverage/worst10。若真的发现后向非确定性，可依冻结合约再做**一次同模式Dense→Dense**对照以诊断，不能用三个无配对Fresh训练范数替代。

### F2 — MEDIUM / Evidence-only：Forward范围与权重/RNG因果对照未达到冻结强度

- **file:line**：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md:23-28,35-40,44-48`；报告`docs/collab/chatgpt/evidence/2026-10-28_DS_PRO_NoTTT_Compact_GPU_Three_Fresh1_Report.md` `2`。
- **Root cause**：用三套独立Job Fresh1各自构建训练源、随机状态、FSDP初始化、Optimizer和Checkpoint；JobName与运行条件亦不同。只报告3个标量Loss与rank0 identity digest；没有`output`完整tensor key set/value/dtype、输入经过H2D逐Rank数值对照、初始权重/Buffer/RNG逐Rank等价。
- **Frozen contract violation**：禁止调用正式训练launcher/trainer.train、禁止Optimizer/Scheduler Step/Checkpoint Save，必须在同一冻结初始状态A/B Native计算图比较；GPU共存许可只调整资源独占要求。
- **Acceptance remediation**：与F1合并为**一个**Native Harness实验，不再执行额外三套Fresh训练；输出四Rank输入/输出/权重和RNG见证，以及action/vision/total/weighted Loss与其它可见tensor输出的逐项比较。当前已观测标量Loss一致的证据保留，不要求重跑整个CPU Gate。

### F3 — MEDIUM / Evidence-only：DCP组件SHA被误当作参数/梯度数值见证

- **file:line**：`cosmos_framework/checkpoint/dcp.py:1399-1422`（`_file_witness`与`_component_witness`），`docs/collab/chatgpt/evidence/2026-10-28_DS_PRO_NoTTT_Compact_GPU_Three_Fresh1_Report.md` `3`。
- **Root cause**：`complete.v1.json`的`components.model.metadata.sha256`/`components.optim.metadata.sha256`哈希的是各自`.metadata`文件；`files`记录的是shard文件大小，不是参数Tensor或OptimizerTensor payload hash。不同metadata SHA甚至不能确定模型权重不同。
- **Frozen contract violation**：无参数数值对照便推断“权重更新差异属于运行间噪声”，不能代替`model_weight_unchanged`及逐参数梯度比对。
- **Acceptance remediation**：撤回“model/optimizer SHA差异证明数值噪声”表述；F1/F2 Harness直接使用同一冻结原始权重并在Backward后确认模型参数/Buffer未变。不恢复已被删除的三个测试DCP，不新增DCP hash审计。

### F4 — LOW / provenance：原始四Rank证据尚未提供

- **file:line**：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md:62-70`；本次DS仅在用户消息提供表格和部分SHA。
- **Root cause**：原始Rank JSONL和Frozen Parity Harness的report没有提交远端，声称当地`8c3d0562`三Evidence commit也尚不能在origin/V3核查。无法独立确认四Rank同步性或复盘数值来源。
- **Acceptance remediation**：提供现有原始日志/来源证据和后续Harness的机器可读JSON；不为此重新跑三套Fresh1，不要求找回已删测试DCP。

## 3. Non-gate observations

- **三次Fresh训练有积极功能信息**，但其“Optimizer运行/保存DCP”属于另一`co-resident second Job`形式，不可在数值Parity Gate里混用为“无Optimizer更新A/B重放”的证据。DS声称Owner同意GPU共存，但此前冻结的`no optimizer, no formal job`验证限制并未在已存文件中被显式覆盖。此为**实验设计/范围偏差**，不构成直接生产代码Bug。
- **相同模式重复的梯度Norm漂移不等于确定为GPU数值非确定性**，也可能涉及RNG、初始化、调度、异步计算、种子/模型分布式状态差异；三点无配对实验无法识别因果。观察值应作为可复现实验指标而非等价性证明。
- **用户此前已明确委托本地程序管理磁盘/Checkpoint**；本评审不再审查容量、Cleaner或保留策略。DS称手动删除三组新试验Job checkpoint，此处只记录其来源，不启动新磁盘Gate，也不追溯改动Owner资产；不要因本Gate要求重建或恢复它们。
- CPU Compact0/1完整Evidence Gate已经`CLOSED`，本次不重跑CPU脚本、不重审未变NoTTT implementation SHA。

## 4. Formal disposition

- `SCALAR_LOSS_SAMPLED_EQ=SUPPORTED`。
- `FULL_FORWARD_OUTPUT_PARITY=OPEN`。
- `GRAD_PER_PARAM_ALL_RANK_PARITY=OPEN`。
- `DCP_METADATA_HASH_AS_PARAM_PARITY=INVALID_EVIDENCE`。
- `GPU_NATIVE_PARITY_GATE=REQUEST_CHANGES`（Evidence-only；尚不能APPROVE）。
- `S2_LONG_TRAINING=NOT_AUTHORIZED_BY_THIS_GATE`；任何独立新Job继续训练或旧Job切Compact仍需独立Owner决策。
- **唯一新验证任务**：一次4GPU FSDP2 Native Harness的Compact0/1配对Forward/Loss/Grad对照，零Optimizer Step、零生产Checkpoint写入；报告所有Rank参数分片/模型输入输出。不得再用三套`fresh 1`跑重复证明。
- 本Review与 Canonical `CODEX_INBOX.md` 同时落盘构成正式`REQUEST_CHANGES`。无生产代码修改或生产训练操作授权。
