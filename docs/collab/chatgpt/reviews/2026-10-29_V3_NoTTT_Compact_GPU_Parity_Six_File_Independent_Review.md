# PSM-WMA V3 — Compact Cached Video GPU Parity 六件原始上传证据：独立增量审核

- 日期：2026-10-29；角色：ChatGPT Independent Evidence Reviewer。
- **正式 Verdict：`REQUEST_CHANGES`（Evidence-only；没有已确认的 Compact production bug）。**
- **既有严格 GPU Gate：`FAIL_PARITY`；Dense→Dense 自身也`FAIL_PARITY`，所以当前不能把失败归因于 Compact，更不能事后修改冻结阈值宣称 PASS。**
- A速度：`RECORDED`（单Step、非稳态）；C新 Job：`READY_BY_STATIC_CHECKS`（不代表真实DCP恢复）。
- Formal implementation历史Root：`49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；Child/Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`。本轮仅新增用户提供的直接 Evidence，不重新 review 相同 No-TTT implementation/design pair。
- Frozen GPU contract：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md`；上一轮 Evidence：`docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_Compact_OneRound_A_Perf_B_Gradient_C_Resume_Evidence_Review.md`。
- 本轮实际读取上传6件（报告/Harness/4Rank JSON），原样/JSON合法化备份于`docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_GPU_Parity_UserUploads/`。README含各文件上传原始SHA、转换边界。**不是Reviewer在训练服务器上执行GPU测试。**

## 1. 上传源码与机器JSON自洽性核查

- 逐Rank`dense0a/dense0b/compact1`的标量`loss`完全一致；Frozen `plan.members[0]`报告一致，n_window=512，Member0=128；DROID model DCP load missing/unexpected=0。
- 四Rank JSON均`raw_allclose_pass=false`、`local_pass=false`、`all_ranks_pass=false`、`verdict=FAIL_PARITY`。
- 294个`GENERATION_KEYS`匹配参数/Rank，7组：`moe_gen=281`、`time_embedder=4`、`action2llm=2`、`llm2action=2`、`vae2llm=2`、`llm2vae=2`、`action_modality_embed=1`。四Rank实际有`548`个`grad is not None`的参数。额外254=548−294，是**未匹配以上七组名称**、但Harness仍为其求导的参数；不能直接用这些254个参数扩充正式训练的Optimizer集合。
- **旧 finding “294/548为何不同”在来源层面CLOSED**：看到了Harness`run_side`遍历所有`model.named_parameters`、且无需`requires_grad`筛选就存储所有`grad≠None`的逻辑。但源差异暴露了新的更严重测试语义问题（下方F1）。
- 基于四份JSON`group_stats`独立重算294个目标参数的失败数：

| Rank | Dense→Dense selected fail/294 | Dense→Compact selected fail/294 | all gradients Dense→Dense /548 | all gradients Dense→Compact /548 | excess_positive /548 | ratio_max |
|---|---:|---:|---:|---:|---:|---:|
|0|138|138|224|225|115|4|
|1|147|141|242|235|98|32|
|2|139|138|227|229|99|8|
|3|151|153|238|245|110|8|

- Rank0七组`intrinsic_noise.group_stats`与`compact_effect.group_stats`完全一致：`moe_gen 150/281` pass、`time_embedder 0/4`、`action_modality_embed 0/1`、`vae2llm 0/2`、`action2llm 2/2`、`llm2action 2/2`、`llm2vae 2/2`。
- 上报的`top50`失败集合重合不是完整548/294集合重合；`ratio_max`高达32且18%–21%全对象Compact max_abs大于Dense自测max_abs。不能从1次对照和“med ratio1.0”推断统计不可区分；`max_abs`的比率本身也不是逐元素对位的误差置信区间。

## 2. 当前 Evidence blockers

### F1 — HIGH：Harness未复现生产No-TTT训练参数冻结，计算图语义不同

- **file:line**：上传`gpu_paired_harness_as_pasted.txt:236-273,275-296,310-324`；Child`cosmos_framework/utils/generator/optimizer.py:202-223,300-306`，`cosmos_framework/trainer/__init__.py:296-305`，Root/Child`examples/psm_wma_robocasa_corrected_phase5.py:704-752,879-895`。
- **Root cause**：真正`trainer.train`会调用`model.init_optimizer_scheduler`，进而`_build_params_with_metadata`用`keys_to_select`冻结不匹配者（`requires_grad=False`），再由`validate_optimizer_inventory`确认。上传Harness只按字符串统计`selected_names=294`，却**未初始化Optimizer也未执行等价的freeze**，直接Forward/Backward并保存`548`个grad。多余254个非选中参数在真实训练的参数冻结路径下不应被当作可训练梯度。
- **违反 frozen contract**：“与生产同一真实NoTTT模型/optimizer selection/trainable inventory/Backward，所有selected参数的真实4Rank FSDP shard”。本次模型`requires_grad`状态和Autograd计算图与正式生产有差异。**无法据此证明非确定性属于生产bf16+FSDP2既有性质，也不能确认该差异解释了多少Dense自测波动。**
- **验收**：测试Harness先复用与生产等价的Optimizer初始化（允许创建但不可`step()`）及`validate_optimizer_inventory(no_ttt=True)`，或以精确生产选择/冻结等价路径施加所有非选中参数`requires_grad=False`；断言所有选中294/Rank相同、所有其余trainable标志为False、优化器选中集合完全一致、实际非None梯度集合符合生产；不得修改生产代码。

### F2 — HIGH：`PASS_CANDIDATE`逻辑绕过冻结的逐参数allclose

- **file:line**：上传Harness`:408-432`。
- **Root cause**：`raw_allclose_pass`在`:418-424`正确要求Compact failure_count=0，但真正`local_pass`与全局`verdict`却使用`compact_failure≤noise_failure`、`excess_positive≤common/2`、`ratio_max≤2`的**未经预授权后验启发式规则**。这可以在`raw_allclose_pass=false`时给出`PASS_CANDIDATE`。
- **违反 frozen contract**：`all ranks`的所有选中Parameter逐元素`torch.allclose(rtol=1e-3,atol=1e-5)`必须全部通过，不能用Dense self-noise非预注册比例替代。
- **验收**：`verdict`的正式pass必须只由完整冻结数学contract驱动；噪声统计可以作为`diagnostic_only`另存、不得触发`PASS_CANDIDATE`。本次四Rank`raw_allclose_pass=false`故`FAIL_PARITY`不受此潜在误判影响。

### F3 — MEDIUM：输入/输出、权重和Buffer不变的见证缺失

- **file:line**：上传Harness`:205-228,275-324`。
- **Root cause**：`plan.members[0]`相同只证明Request计划身份，不证明两次`producer.produce`结果中`video_latent/text_token_ids/action/sequence_plan`和GPU`move_cached_native_batch`后的所有非Video字段相同。`output,loss`只记录后者的标量，未逐字段比`output`。复用同一个`model`且手动`param.grad=None`只说明没有主动`optimizer.step`，**未用权重/Buffer快照证明Run间无状态变化**。
- **违反 frozen contract**：同冻结Native GPU输入、相同权重/Buffer和RNG、所有可见Tensor输出/weighted loss的对照要求。
- **验收**：新测试Harness在同一Frozen CPU Batch→H2D后比较全部非Video tensor、缓存latent、token/action及有效Mask/消费者顺序；跟踪原始权重/Buffer数值见证和起止RNG；比较所有Native输出keys/dtype/shape和值（非只loss）；确认模型权重与Buffer在两侧前后不变。

### F4 — MEDIUM：梯度比较未充分验证dtype/finite/None-mask，输出截断不可复算全量分布

- **file:line**：上传Harness`:293-296,326-371,381-405`。
- **Root cause**：保存的`grads`是所有有梯度者的`DTensor.to_local().clone()`，没有显式验证选中集合上两侧的`grad=None`mask；`compare`先`.float()`使原始dtype信息丢失，未逐对象Assert`finite`。只输出`failures[:50]`/`worst10`、`group_stats`/`failure_count`；没有导出全部选中294项的数值/误差分布，无法通过上传JSON独立复算`excess_positive/ratio`等统计定义。
- **违反 frozen contract**：四Rank选中参数一致、NoneMask/dtype/shape/finite、逐元素`allclose`及完整参数组覆盖见证。
- **验收**：由TestOnly Harness提供所选参数的全量**轻量统计**（name/group/shape/dtype/None/finite/allclose/max_abs/relative_L2，不保存梯度Tensor）及各Rank摘要，使独立审核可复算；没有新增生产测试或GPU重跑授权。

### F5 — LOW / Evidence provenance：上传Harness无法作为字节级可运行脚本

- **file:line**：`gpu_paired_harness_as_pasted.txt:130,444`。
- **Root cause**：用户粘贴版本存在`torch.**version**`和`if **name**=="**main**"`，是Markdown将`__version__/__name__/__main__`转成加粗后的文本。原样`ast.parse`会报SyntaxError；把这两处恢复成Python dunder后语法检查通过，但这**不能证明实际服务器运行文件就是这一份字节序列**。
- **验收**：今后归档真实服务器可运行的Python文件原件（不可从渲染Markdown逆向拼接后声称字节一致）。此项是本轮可追溯性问题，不影响已解析的4Rank JSON本身。

## 3. 非阻断但必须纠正

- 用户附送的第二段Python取`d["grad_parity"]`，但四Rank JSON没有此字段；可用`d["compact_effect"]`和`d["intrinsic_noise"]`查看。JSON未保存`per_param`，不能从现有输出重建所有548项的完整误差分布。
- C静态Resume报告中 `bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 10` 是正确的Shell Launcher接口形式（需在Root并配好全部环境变量），但`resume 10`的语义是**读取当前新Job latest_checkpoint（报告为iter1）并运行至committed iteration10**，**不是“从iter10恢复”**；从什么迭代恢复由实际`latest_checkpoint.txt`决定。C `READY_BY_STATIC_CHECKS`不等于真实恢复已通过、也不授权S2。
- A性能：Compact1`step_wall=25.523/23.482s` vs Dense`45.806s`，平均比`1.869×`；Prepare`9.149/6.889s` vs Dense`30.128s`，观察`3.757×`。均为每job仅1 Step、共存GPU/冷启，非稳态加速。
- Owner明确磁盘/Checkpoint retention由本地程序管理，GPT/DS不复审或干预；`save_iter=100`不变。
- 用户提供的第一段Python打印四Rank `intrinsic_noise/compact_effect/diagnostic` 结果与归档JSON一致；严格Gate仍`FAIL_PARITY`。

## 4. 最终范围与下一任务

- `A=RECORDED`、`B_STRICT_GPU_PARITY=FAIL_PARITY`、`C=READY_BY_STATIC_CHECKS`。
- **Formal review literal：`REQUEST_CHANGES`（Evidence-only；新发现是Harness测试语义，不是NoTTT生产Bug）。**
- 先静态整改Harness：真实生产参数冻结+Optimizer Inventory、严格`raw_allclose_pass`控制formal verdict、完整Input/Output/Buffer与梯度dtype/None/finite见证、修正上传源代码损坏；测试代码形成可审核的独立artifact/差异后再考虑新的限额GPU验证（**本Review不自行授权新GPU或Resume**）。不得以当前噪声指标作为后验统计等价Gate直接签PASS。
- 不要求重复CPU Parity/三套Fresh1，不碰正式oldNoTTT、新Compact1Job的Checkpoint和model；不修改生产代码或旧Job Compact开关。
- 只有本Detailed Review及`CODEX_INBOX.md`同步落盘才构成当前Evidence正式`REQUEST_CHANGES`。
