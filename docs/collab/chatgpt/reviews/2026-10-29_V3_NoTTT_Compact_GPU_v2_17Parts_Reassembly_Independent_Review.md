# PSM-WMA V3 — No-TTT Compact GPU Parity v2：17份分片重组与四Rank完整原始证据增量复审

- 日期：2026-10-29。审核人：GPT independent Evidence reviewer。
- **Formal verdict：`REQUEST_CHANGES`（仅剩 tests/Evidence-only）。严格GPU Native Gradient Parity仍`FAIL_PARITY`，不能从此推断Compact production bug，也不能后验把噪声解释升级为正式数学等价`PASS`。**
- Frozen Numerical Contract：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md`，逐Rank逐参数`torch.allclose(rtol=1e-3,atol=1e-5)`；所有4Rank全部通过才候选PASS。
- **未重审未变生产实现**：formal NoTTT historical root implementation `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9` / Child+Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`；新增文档/bookkeeping V3 HEAD不是新的implementation/design SHA。
- 前置Review：`docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_Compact_GPU_Parity_Six_File_Independent_Review.md` 与`docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_Compact_GPU_v2_ProductionFreeze_Incremental_Evidence_Review.md`。本轮只修正它们当时缺少v2源码/四RankJSON所导致的证据状态。
- **本轮直接原始证据**：用户上传17个附件（一个573行Harness和16个rank JSON片段），已在服务器以外独立重组/JSON解析、按Rank校验，上传到 V3 `docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_GPU_v2_Reassembled/`。可从README查分片编号/重复片段、每Rank校验SHA256；本次GPT没有执行CUDA、训练、DCP或写生产代码。
- 上传Harness有格式损伤（`torch.**version**`、`type(...).**name**`、`if **name**`），属于Markdown转录，保留原文；仅用恢复Python dunder+NBSP→空格的**静态副本**进行`ast.parse`，语法通过；不能宣称实际服务器运行脚本与上传文本字节一致。

## 1. 分片正确重组：原始四Rank证据已到齐

- 每个Rank是`7,344`行完整JSON；`rank0..3`均`json.loads`通过，每个`selected_params.count=294`、`optimizer_inventory.generation_tensors=294`、`requires_grad_counts={trainable:294,frozen:255}`，三侧`grad_params=294`。`rank0..3`并非4个相同副本，所有结果带自身rank/loss/失败数。
- 片段编号不是rank编号；重组映射（上传编号）：`rank0=[5,14,16,17]`，`rank1=[6,11,12,13]`，`rank2=[10,7,8,9]`，`rank3=[5,2,3,4]`。前缀片`5/6/10`文本完全相同、`14/15`重复，因此相同公共前缀可在不同Rank无损复用，没有丢失独有数据。
- 独立重组SHA256（UTF-8/LF）：rank0`10ff7564e70d2d726ea3510202ba0d0a11d4602ce8618534cf345d239d0c6748`；rank1`1bf095cbb5803a4fd3b96ba335bba850994f50935fd6dfc5eba600d47a375260`；rank2`f72b61abd6ccd8df402d3cde8412f5e0bb0daa5247bf0f51362da6df4e21cd08`；rank3`132c81ec536a981d04c62fee867d2b63943169b7e51fcd07397970f2807ac4a0`。
- **上一轮“v2完整原始Rank JSON未上传”Finding `CLOSED`**；不得再向Owner/DS索要同样的17份文件或据此要求重跑。

## 2. 四Rank数值结果独立复算

| Rank | Dense→Dense FAIL/294 | Dense→Compact FAIL/294 | excess-positive /294 | ratio-max | Formal |
|---|---:|---:|---:|---:|---|
|0|139|135|54|4|`FAIL_PARITY`|
|1|149|142|40|8|`FAIL_PARITY`|
|2|140|148|49|8|`FAIL_PARITY`|
|3|154|156|61|16|`FAIL_PARITY`|

- 四Rank`dense0a/dense0b/compact1`各自三个`loss`标量逐值相同，`weighted`也相同；`dcp_load missing/unexpected=0/0`，`plan.members_eq=true`。实际`grad_none_mask_eq`均True、`grad_dtype_eq.mismatch_count=0`，共294个float32 DTensor梯度，255个冻结参数的`grad_meta.dtype=null`，`weight_buffer_invariance.checked_tensors=549/drift_count=0`。
- 这是符合Report的可复查结果，**并不是4Rank梯度严格数值等价**。同路径Dense-Dense严格对照失败更多或相近，说明本次单次`allclose`不能建立稳定重复基线，但不能由此“证明真实生产一定只是bf16固有噪声”或认为统计等价已被验证。

## 3. 前轮 Finding 增量状态

### F1 HIGH（v1不复现生产Optimizer冻结）→ `CLOSED`

- **定位**：上传v2 Harness `gpu_paired_harness_v2_uploaded.txt:298-339`，Child`cosmos_framework/utils/generator/optimizer.py:202-223,300-306`，真实`examples/psm_wma_robocasa_corrected_phase5.py:704-752`；四Rank完整JSON `optimizer_inventory/requires_grad_counts/grad_meta`。
- v2执行`model.init_optimizer_scheduler(config.optimizer,config.scheduler)`，随后`phase5.validate_optimizer_inventory(no_ttt=True)`；四Rank证实294 selected +255 frozen，梯度仅294。前一轮缺少v2源代码的证据边界已关闭。此项无需再跑GPU。

### F2 HIGH（v1启发式LocalPass可伪PASS）→ `CLOSED`

- **定位**：上传Harness`:541-565`和四Rank`formal_pass/raw_allclose_pass/all_ranks_pass/verdict`。
- v2仅用冻结`compact_effect.failure_count==0`与loss/plan/dcp/NoneMask/dtype/weight-state见证决定`formal_pass`，以`dist.all_gather_object`收集4Rank；`diagnostic.ratio/excess`未进入PASS判据。四Rank`formal_pass=false`→`FAIL_PARITY`符合合同。本条旧HIGH已闭环。

### F3 MEDIUM（完整Native GPU Input/Output内容见证）→ `OPEN: VALUE_WITNESS_NOT_IMPLEMENTED`

- **定位**：上传Harness`:95-105,341-372,541-553`；四RankJSON`dense0a/dense0b/compact1.input_fingerprint`和`output_fields`。
- **根因**：Native Batch每Rank有25个顶层字段，全为`list`或`int`等非Tensor类型；代码`type(v).__name__`只记`"list"`/`"int"`，并未递归检查`action/text_token_ids/video_latent`等列表中的Tensor、mask、位置、消费者身份及数值。四Rank`input_fingerprint`表面相等属于**类型一致**，不是内容相等。
- 输出`output_fields`只给3个Scalar Tensor真实数值；4个非Scalar Tensor仅形状/dtype，16个其它字段仅`repr(... )[:200]`。代码从未对三侧`input_fingerprint/output_fields`断言或在`formal_pass`门控。即使数值不等也可能有相同fingerprint。
- **违反冻结合同**：“同Frozen Native GPU输入/所有可见Output tensor数值校验”。目前不能把scalar Loss一致升级为“完整Forward/Output逐位一致”。
- **验收条件**：未来test-only Harness真正递归遍历batch/list/tuple/dict，比较非Video逻辑内容Tensor值、dtype/shape/device；Video接受Dense零像素和Compact逻辑全零代理的等价例外；对全部有意义Output Tensor进行`torch.equal`/预冻`allclose`比较并纳入Gate，给四Rank机读证据。**不应为已失败的严格Gate无意义重跑；未来新验证前先静态补齐。**

### F4 MEDIUM（模型状态与Grad完整见证）→ `PARTIAL_OPEN: WEAK_STATE_WITNESS_AND_FINITE`

- **定位**：Harness`:95-105,398-434,436-483,491-512`与rankJSON`weight_buffer_invariance,grad_meta`。
- **已CLOSED子项**：294 Selected张量`grad=None`集合、四Rankdtype均等，selected各组覆盖明确；v2确实依同Frozen阈值比较294项`torch.allclose`，结果FAIL。
- **仍未覆盖的根因**：`_tensor_fingerprint`先`.float().cpu()`，造成原始Tensor dtype见证失真；仅`shape/abs_sum/abs_max`，不同Tensor甚至不同符号/位置排列可有相同摘要。模型`state_dict`的549个摘要只对三侧运行前后检查一次，未逐Side保全和比较完整Parameter/Buffer值；`compare`对梯度先`.float()`且没有显式`torch.isfinite`判据；仅输出`failures[:50]`/`worst10`，无完整294个参数的误差概要可独立复算所有ratio/excess。
- **违反冻结合同**：“权重/Buffer保持值不变、finite/shape/dtype/None mask、逐Rank逐组可追溯数值见证”。不能将`drift_count=0`解释成全Tensor值逐bit不变，尽管无Optimizer Step使实际变化风险较低。
- **验收条件**：未来test-only检查真实原始dtype/完整精度哈希或逐Tensor`torch.equal`、逐侧状态快照；对所有Selected梯度显式检查Finite、local shape/dtype/None，并导出294项**轻量统计而非全梯度Tensor**。发现梯度形状不同要显式Fail-closed，不依赖后续group统计可能的KeyError。当前不用重复GPU验证来“修复”已经失败的严格Gate。

### F5 LOW（用户上传脚本富文本损伤）→ `OPEN_PROVENANCE_ONLY`

- 源代码转录中的Dunder变成`**...**`不影响已核验的4Rank机读JSON，但不能与真实服务器`py_compile`原件做字节级等价声明。静态恢复后Python AST通过；可在以后提交的test-only源码直接保存`.py`字节，**不需再上传本轮全部RankJSON**。

## 4. 权限、下一步

- `GPU_STRICT_PARITY=FAIL_PARITY`，`EVIDENCE_VERDICT=REQUEST_CHANGES`（仅F3/F4及LOW provenance；**F1/F2和v2四Rank原始Evidence已CLOSED**）。
- 生产代码没有发现新问题，本轮Root文档/Review SHA变化不改变formal implementation/Child pair。
- CPU Compact0/1 parity此前已CLOSED，三组Fresh1已运行且无需重复；A单步速度收益观察1.87x、非稳态；C`READY_BY_STATIC_CHECKS`、真实Resume未跑。
- Owner本地负责磁盘/CKPT保留（`save_iter=100`）；不审容量、不改Cleaner。本轮不授权/执行GPU复测、S2 Resume、原正式NoTTT切Compact、数据或生产改动。
- 现实决策上可单独冻结**实践性S2风险接受Gate**，利用已完成CPU parity、标量loss等价、GPU同模式噪声对照及现有静态Resume证据，但**不能将其包装成原严格Gradient Parity已PASS**。若以后需要严格模型等价，须先冻结明确的新数值或noise-calibrated协议，不能后验调整已失败阈值。
