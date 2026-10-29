# PSM-WMA V3 — No-TTT Compact GPU Parity v2：生产冻结整改 Evidence 增量复审

- 日期：2026-10-29；角色：独立 Evidence Reviewer。
- **本轮正式技术结论：`REQUEST_CHANGES`（Evidence-only）。严格 GPU Gradient Parity 仍为 `FAIL_PARITY`；不是已证实的 Compact production bug，也不能宣称统计等价 PASS。**
- **不重复审核 formal implementation**：No-TTT historical Root `49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9` / Child-Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5` 未变；新 Root bookkeeping/其他评测Review不能代替formal pair。当前只审核新 v2 Harness 执行证据。
- 上轮 Finding：`docs/collab/chatgpt/reviews/2026-10-29_V3_NoTTT_Compact_GPU_Parity_Six_File_Independent_Review.md`（v1 F1=未复现生产freeze、F2=潜在伪PASS、F3/F4=输入输出/梯度见证、F5=粘贴源码损坏）。
- Frozen数学合同：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_GPU_Native_Parity_DS_PRO.md`，所有4Rank真实Optimizer selected梯度 `torch.allclose(rtol=1e-3,atol=1e-5)` 全过方能 `PASS_CANDIDATE`。
- 来源：`docs/collab/chatgpt/evidence/2026-10-29_V3_NoTTT_Compact_GPU_v2_Retest_DS_PRO_Submitted_Paste.md` 是用户提交的 DS_PRO 汇编全文（1011行，原始附件SHA256 `5df382575df66d9bdaa58a003f398bcee3c61b65de3ccd5e30c715495ea9cf03`；仓库存储版本CRLF规范化为LF）。**不是独立取得的 v2 可执行源码或四Rank原始v2 JSON。**
- 本轮在 GitHub V3 递归Tree未见 DS 称已形成的 `gpu_paired_harness_v2_freeze_formalpass_fullwitness.py` 或 `v2_gpu_parity_rank_jsonl/v3_gpu_parity_rank{0..3}_v2.json`；不能用本汇编宣称原始v2工件已审核。

## 1. 新增运行证据：v2 参数冻结问题得到强支持

上传报告 §2.6 + 末尾运行日志列出：
- 使用 `model.init_optimizer_scheduler(config.optimizer, config.scheduler)` 构造**真实**Optimizer；Child `cosmos_framework/utils/generator/optimizer.py:303` 的 `keys_to_select` 会把非选中参数设为 `requires_grad=False`，生产 `examples/psm_wma_robocasa_corrected_phase5.py:704-752` 可验证Optimizer Inventory。
- 日志 `_build_params_with_metadata`: `Total tensors: 549, trainable tensors: 549, selected tensors: 294`；随后报告 `validate_optimizer_inventory(no_ttt=True)` => `generation_tensors=294, local_tensors=0`，`requires_grad={trainable:294,frozen:255}`。
- 4Rank的 Dense0a/Dense0b/Compact1 全部打印 `grads=294`，不再出现v1的548个梯度；三侧各Rank Loss 值一致，`missing/unexpected=0/0`、无Optimizer Step、无DCP write（按DS报告）。
- **旧 F1 HIGH：`RUNTIME_SYMPTOM_RESOLVED; SOURCE_REVIEW_PENDING`。** 运行日志确实支持生产冻结接线已修复，不应要求重复GPU运行；但必须读到v2 Harness原件后，才能把“严格与生产同一Frozen trainable inventory和计算图”标为独立 `CLOSED`。v1的548与本v2的549个参数总数不矛盾：v1只有548个参数存在grad，v2列549个模型参数。

## 2. 四Rank严格梯度结果：`FAIL_PARITY` 不变

| Rank | Dense0a→Dense0b 失败/294 | Dense0a→Compact1 失败/294 | Compact excess positive/294 | Ratio max |
|---|---:|---:|---:|---:|
| 0 | 139（47.3%） | 135（45.9%） | 54 | 4 |
| 1 | 149（50.7%） | 142（48.3%） | 40 | 8 |
| 2 | 140（47.6%） | 148（50.3%） | 49 | 8 |
| 3 | 154（52.4%） | 156（53.1%） | 61 | 16 |

- 四Rank `formal_pass=false` / `verdict=FAIL_PARITY`，终端日志也显示四Rank均退出；说明 v2 **运行时**没有把这次明显失败的比较伪装为PASS。
- Dense→Dense在同路径复测亦失败很多，说明**本次Harness的严格repeatability baseline不可用**。两种差值的数量级相近，是“尚未观察到明显系统性Compact模式效应”的支持性迹象；**不能升级为“已证明都是bf16固有噪声/统计不可区分”**。无法排除输入内容、非确定性、回放状态或比较方法因素；单次控制对照不能完成噪声带统计检验。
- 例如Rank3 `156/294` vs自控 `154/294`，`excess_positive=61/294≈20.7%` 且最大比率16。零星 `noise_ok=True, compact_ok=False` 的对象不能由总失败数近似而忽略；不建议事后放宽`rtol/atol`。
- **严格 Gate的literal不能放宽，继续`FAIL_PARITY`；S2不因本次新Evidence自动获授权。**

## 3. 上轮 Finding 整改状态（只做增量）

### F2 HIGH / 旧v1潜在伪PASS → `RUNTIME_REJECT_CONFIRMED; CODE_PENDING`

- **定位**：v1上传Harness `gpu_paired_harness_as_pasted.txt:408-432`；新报告 `§2.6` / summary JSON `B_gpu_parity.retest_v2.by_rank[0..3].formal_pass=false` / 日志 `[rankX] verdict=FAIL_PARITY`。
- **原因/合同**：冻结合同只能用四Rank选中294个参数全部逐元素allclose作为Pass；v1的`local_pass`另用未经授权的比率启发式。v2 *报告*已修复且运行时四Rank拒绝，属于正向Evidence，但缺真实v2源码就无法审计条件表达式是否存在另一条旁路。
- **验收**：上传现成v2脚本，核对 `formal_pass` 唯一合成路径及全Rank fail-closed；不重复GPU试验。

### F3 MEDIUM / Native Input-Output与模型状态见证 → `PARTIAL; SOURCE/RAW_JSON_PENDING`

- **定位**：源报告 `§2.6` / `B_gpu_parity.retest_v2` 仅提供 `plan.members_eq`、`dcp_missing/unexpected=0`、`weight_buffer_drift=0`（声称549 checked）、Loss相等、`grad_none_mask_eq=true`。
- **原因/合同**：即使计划成员相同，也不证明实际Frozen CPU+CUDA Native Batch的所有非Video tensor逐值相同；所报只是总体loss，没有 `output` 全字段Tensor、dtype/shape/value对照；549个被检查对象恰好等于模型参数数量，尚不清楚非参数Buffer是否也在见证范围。
- **验收**：v2源脚本 + 四Rank机器JSON中真实的输入、完整output和参数/Buffer见证字段；如v2原件本就没有这些数据，须明确“未测”，不能自称`MEDIUM 全部闭环`。不以重新跑GPU为默认补证手段。

### F4 MEDIUM / Grad dtype/None/finite/all-param stats → `PARTIAL; RAW_JSON_PENDING`

- **定位**：上传报告 `§2.6` summary JSON `grad_none_mask_eq=true` / `grad_dtype_mismatch=0` / `only_a/only_b=0`，但未包含完整 v2每参数统计。
- **原因/合同**：这支持Gradient集合/形状结构大体一致，但不能独立检查所有294项的逐元素 `allclose`、finite、原始dtype和worst分布；报告中并无 `finite` 或`full_native_output_eq` 原始字段。
- **验收**：直接提交已有v2四Rank原始JSON和Harness；不要要求复制全量Tensor或重跑。不存在的字段明确`NOT_MEASURED`。

### F5 LOW / v1 Markdown损坏 → `NOT_APPLICABLE_TO_v2; RAW_SOURCE_PENDING`

- v1传输格式造成 `__name__/__version__` 文本损坏，不代表服务器运行文件损坏。本次 v2 Script未随附件送达，故只需要现存可执行原件；不要求为格式问题重复模型实验。

## 4. C/A先前状态不改变

- A已验收 `RECORDED`：Compact1 Fresh1 Step Wall≈24.50s（两次均值）vs Dense0≈45.81s，单步观测比值≈1.87×，非稳态/共存GPU；DataPrepare比值≈3.76×。
- C仅 `READY_BY_STATIC_CHECKS`，没有实测DCP Restore。此前更正的 `bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 10` 表示**从已有latest Checkpoint迭代（如iter1）运行至iter10**，不是“从iter10恢复”。本Gate不执行。
- Owner已明确磁盘/Checkpoint保留由本地程序管理，`save_iter=100`不变。本轮不重新审核容量、Cleaner或清理权限。

## 5. Formal disposition / 唯一后续动作

- `GPU_NATIVE_GRADIENT_PARITY=FAIL_PARITY`（冻结数学合同继续成立）。
- `EVIDENCE_REMEDIATION=REQUEST_CHANGES`（v2操作证据新增且积极；旧F1/F2运行症状已解决，但原始可执行v2源码/四RankJSON尚缺，F3/F4未独立关闭）。
- `PRODUCTION_IMPL_NEW_BLOCKER=NONE_IDENTIFIED`。
- **仅要求DS一次性交付现成的** `gpu_paired_harness_v2_freeze_formalpass_fullwitness.py`、`v3_gpu_parity_rank0..3_v2.json` 以及其已有的分析脚本/日志副本。**不再次启动GPU/三套Fresh1/CPU Gate，也不要求改变`rtol/atol`**。随后一次性验证v2代码与原始结果字段能否完成旧F1-F4 Evidence closure；严格梯度Gate FAIL不因更多文档而改PASS。
- 如之后确需实践上以Compact=1进入长训，应与**本严格Gate的FAIL**分离，另行由Owner授权实践验证/风险接受或先冻结独立噪声校准Gate；不能暗中继承当前未批准的统计结论。
- 本Review与 Canonical `CODEX_INBOX.md` 同步持久化后才形成正式`REQUEST_CHANGES`。
