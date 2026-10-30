# PSM-WMA V3 — No-TTT Issue #12 真实 DCP Resume / GPU A-B 独立 Evidence 审核

- 审核日期：2026-10-30。
- **执行 Formal Pair（未变）：Root `e0fe911dfb9fd34957234828195cf051713f6c3d` / Child+Gitlink `f6a92d47b6dac7998ddc58b3da26ef93f8068dc7`**。已审 Code Gate `APPROVE_CODE`、独立合成 CPU301 +6/6 raw `PASS` 均继续有效；**本次只对新真实运行 Evidence 评审，不重复技术源码 Gate**。
- Owner 授权文件：`docs/collab/chatgpt/requests/2026-10-30_V3_NoTTT_Real_DCP_Compact1_NW0_vs_NW8_Owner_Authorized_Execute.md`；[Issue #12](https://github.com/wxwy/psm_wma/issues/12)。
- **本次收到的 Evidence**：用户粘贴的 DS_PRO `ISSUE12_EXECUTION_REPORT`（UTC 2026-10-30 04:28）。报告的原始 `arm_a_run.log`、`arm_b_run.log`、`CLONE_MANIFEST.json`、`RUN_MANIFEST.json`、S0与4rank日志仍在 DS 服务器，当前GPT未直接读取其原始字节，也未执行 GPU/真实DCP测试。以下每项实际测量数字为**DS现场报告**，不是GPT本人现场读回的日志。
- **FINAL Evidence Gate verdict = `REQUEST_CHANGES` — 真实 A/B 资格实验未闭环（仅Evidence / 运行未通过，不确证新增生产代码缺陷）。** 分类：`ARM_A=PASS_REPORTED`; `ARM_B=DCP_LOAD_PASS_REPORTED_BUT_FIRST_MATERIALIZE_TIMEOUT`; `ARM_B_OPTIMIZER_COMMITS=0`; `PERFORMANCE=INCONCLUSIVE`；**不授权 promotion、停止正式 Job 或自动重试**。

## 1. Positive 结果与计数（限DS现场报告）

| 冻结项 | DS现场结果 | GPT审核口径 |
| --- | --- | --- |
| C及来源 | `iter_000009600`，`complete.v1.json complete:true`、world4、源/双clone13/13文件哈希相同，双clone各约24G | `REPORTED`；没有原始manifest和hash字节，不擅自声明独立确认 |
| 环境 | Frozen Root/Child一致、独立clean detached、同训练venv，4卡GPU4–7 | `REPORTED` |
| Arm A Compact1,nw0 | checkpoint iteration9600加载，9601..9620的**20/20 optimizer_committed**、退出0、无missing/nonfinite grads、正常Loss/LR，4rank未报错 | **`A_NATIVE_RESUME_AND_TRAINING=PASS_REPORTED`** |
| Arm A稳态 | 9603..9620（18步）Step Wall P50 **20.50s** / P90 **22.70s** / mean20.28s；所谓data wait P50 **5.35s** | wall为DS报告；data wait的**原始字段含义待澄清**，不可认定为GPU空闲或raw wait |
| Arm B Compact1,nw8新Async | checkpoint9600加载成功；第一个`next(self.iterator)`即 `DataLoader timed out after 120.0 seconds`；0 optimizer commits，4rank超时并退出 | **`B_DCP_LOAD=PASS_REPORTED`; `B_RESUME_CONTINUITY=FAIL_NOT_COMPLETED`**。成功加载不等于训练Resume通过 |
| 原正式Job | ds称既有NoTTT旧RAW nw8 Job未被修改，始终占用GPU4–7达100%util | `REPORTED`，GPT未实时见证；构成性能归因混杂因素 |
| 实机性能比较 | B没有一个有效Step，不存在稳态壁钟或H100真实CUDA重叠证据 | **`INCONCLUSIVE`，不得称优化实现真实GPU加速或变慢** |

历史 Compact严格GPU Gradient Parity `FAIL_PARITY`、Dense自重复不稳定、Compact归因 `INCONCLUSIVE` 保持原状。此轮真实A20个健康步骤不是Compact严格梯度Parity恢复通过的证明。

## 2. 新 Evidence Finding（前序 CPU Gate 不重开）

### ISSUE12-E1 — HIGH（真实 B 未完成一次 optimizer commit；根因未确定）

**失败点：** Child `cosmos_framework/trainer/no_ttt_async_loader.py:286-296` 的 `NoTTTAsyncLoader._materialize()` 在 `result=next(self.iterator)`，PyTorch `DataLoader`按`LoaderProfile.timeout_s=120`报超时；原始 `cosmos_framework/trainer/no_ttt_cpu_loader.py:440` wrapper closes/reaps owned Loader。失败发生在**第一份Prepared Segment返回之前**，而不是模型gradient/optimizer阶段。DS报告4rank同时受影响，0次commit、无自动串行fallback。

**两种均未关闭的解释：**

1. **实验资源竞争：** 原正式4rank NoTTT oldRAW/nw8仍在GPU4–7上满载，+新4rank候选、32个新spawn DataLoader workers、额外loky进程、Host CPU和IO复用且数据盘接近99%使用。可造成spawn、文件与缓存读取、Arrow/Tokenizer执行延迟。但**CPU load average/磁盘使用率本身不是独立定量IO吞吐证据**，不能把资源争用当作已证实唯一根因。
2. **新Async Worker冷启动/重建开销：** GPT直接复核生产调用链：`no_ttt_async_loader.py:129-135`每个`PreparedDataset.__getitem__`在该Worker第一次被调用时 `self.recipe.build()`；`no_ttt_async_recipe.py:195-254`重开VerifiedIndex、Cache、`RoboCasaExactWindowSourceReader`、ActionTransformPipeline/Tokenizer；`robocasa_exact_window_source.py:247-258`其中构建非视觉LeRobotDataset。DS同时报告主进程每Rank Preflight `lerobot_init_ms≈186000`、`sft_dataset_create_ms≈190000`。**因此“ArmA/B主Preflight同为190秒，所以Preflight不是首批超时原因”的原推断不充分：B的32个Worker还要分别初始化相似Reader，此开销发生于主Preflight之后，并受120秒第一次 next() 限制。** 是否在独占资源下仍超时尚缺worker自身启动时钟，不能升格为已确证生产缺陷。

**当前Verdict：** `B_RUN_FAIL`确定，`TIMEOUT_CAUSE=INCONCLUSIVE`，**无需在此相同 Formal Pair 上再次进行源码 Code Gate**。不得擅自增加Timeout/减少Worker/修改SourceReader来掩盖本轮缺陷或宣称已修复。若后续独占环境复现，再形成Codex窄修与新正式SHA的独立Gate。

**最低限度下一步证据（现存文件、只读，无GPU重跑）：** B首个Timeout前后±相关段四rank完整stack/timestamps、worker PID启动时间和CPU/RSS/IO/是否有第一个packet、worker内Reader初始化相关日志/定时（如原始日志没有，注明 `NOT_MEASURED`），与A同阶段比较，以及磁盘实际剩余字节、I/O拥塞工具原始采样（如未采集则标 `NOT_MEASURED`）。只用现有现成日志，不能编造不存在的worker stage。

### ISSUE12-E2 — MEDIUM（资源授权边界与A/B可比性）

原 `e5fde3f7` frozen合同第1/2节明确：**正式Job存活或GPU4–7被占则 `BLOCKED_RESOURCE_OR_CHECKPOINT`，不应做GPU A/B，不允许DS停正式Job制造空闲**。DS当前报告额外一句 `Owner waives GPU4-7 exclusivity (run concurrently with formal job)`，但本轮未提供这一后续 Owner 明确修改/授权的原始记录，GPT核对 [Issue#12](https://github.com/wxwy/psm_wma/issues/12) 时未见备案修改和评论。本审核**无法独立认定该豁免的权威性**：如果Owner确实在另一渠道批准，请补精确引用/记录，不能将 `e5fde3f7` 本身说成它授权了并发。

**无论有无有效豁免，共享满载GPU的A20测量与未来独占下B20均非严格同资源条件A/B**；A这次成功可证明共享环境下恢复健康，但不能直接用其壁钟P50作为未来独占B的matched baseline。真实性能结论要求双方同设备占用状态、同 C、相同数据，首选**双方均独占**。

### ISSUE12-E3 — MEDIUM（报告指标语义需用原字段澄清）

DS报告ArmA `DATA(data wait) P50=5.35s`。实际 `examples/psm_wma_robocasa_corrected_telemetry.py:_post_commit` 里 `data_wait_ms` 为 `trainer._grouped_prefetcher.iteration_wait_ms` 或 `None`；No-TTT nw0路径不启用该prefetcher，因此这5.35秒**更可能是 `data_prepare_ms` 等CPU阶段**，不应直接称为rank0 GPU stall。实际 `gpu_data_stall_ms` 是`current_stream_gap` estimate，若`pending_cuda_event`则NOT_MEASURED。补原20行`monitor/train_rank0.jsonl`的字段名称、`data_prepare_ms`/`data_wait_ms`/`gpu_data_stall_ms`/`gpu_data_stall_status`，再给准确描述，不要求重跑。

## 3. Evidence归档与后续决策

- 本轮尚无**GPT可直接读取的原始13/13 DCP SHA清单、ArmA20有效JSONL、ArmB4rank traceback、Shell exits/worker PID/cgroup、Owner waiver记录**；因此不是完整原始证据闭环。DS可通过独立Evidence-only分支上传必要脱敏现存文件，或大粘贴上传给GPT。禁止上传24GB Checkpoint/真实数据，禁止overwrite原Job或重跑GPU。
- **既有 Code Gate `APPROVE_CODE` + Issue#11 CPU301/6raw `PASS`保持不变**。新的真实Gate按本轮`REQUEST_CHANGES`登记；仅运行证据问题，当前**没有独立确认的新生产源码blocker**。
- 当前禁止同 Formal Pair在满载GPU4–7上自动重试B，也禁止仅调timeout即重跑。等证据复核、Owner后续另行授权、正式Job不在且GPU4–7独占/可靠的资源窗口后，**若要有效性能比较，应从同一C重新做隔离matched A/B**（旧A为并发环境，不能和新独占B相减）；也可以先用足够轻量的只读/CPU Worker startup观测定位，但任何另加实机实验也需要明确授权。避免新架构/无端添加Gate。
- **所有正式训练/Checkpoints保持不动**；不改Cleaner、不重跑CPU301、不合并Frozen Pair到当前V3、不触碰仿真技术线。Owner原授权的A20+B20已用掉A20及B一次失败启动，**不自动解释成无限次重试许可**。

**Formal Evidence verdict: `REQUEST_CHANGES` for Issue#12 real native GPU/DCP performance qualification only.** 需原始证据和可用的独占对照后才能重新申请验收；本轮仅做新 Evidence 审核，不重置之前源码/CPU Gate。
