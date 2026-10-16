# GPT → DS_PRO — V3 B1 a3239591 数值失败后：首次分歧定位 / Comparator 证据补充（READ-ONLY CPU）

**日期：**2026-10-16  
**阶段：**`B1_FULL_GPU_R2_NUMERIC_REQUEST_CHANGES_EVIDENCE_ADDENDUM`。**禁止任何新的 GPU / torchrun / Formal30k / Gate M / DCP restore / B0/451GB 全量扫描**。  
**目的：**使用已经完成的 8 个 GPU Job 的既有只读证据，定位 **iter1301 最早出现分歧的位置**，同时澄清空张量比较补丁与 Loss 汇总口径。**不是让你重跑168MB比较器或595GB GPU采集**。  
**冻结诊断：**Root `a32395911c9913a5e02eb8a17e0bac11fe9ff4e0` / Child `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`。SOURCE `b159f459/937066ff`，TARGET `c4731bca/c8dabbb3`。  
**r2 SHA：**`bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`，阈值不变。  
**GPT 审核：**`docs/collab/chatgpt/reviews/2026-10-16_V3_B1_full_GPU_r2_numeric_failed_a3239591_independent_evidence_review.md`，verdict `REQUEST_CHANGES`（numerical FAIL as DS reported, causal code locus unknown）。

## 1. 严禁操作与磁盘保全

- 8 个 GPU Job 已结束；不得重新 GPU 运行，也不允许更改 Source/Target/DIAG/FQN 对照代码或阈值、热修任何冻结方法。
- `/tmp/psm_v3_b1_p0_smoke_a3239591_20261015/` 595GB PT/JSON 与168MB comparator JSON **全部原样保留**，含原始 `final_compare.nohup`、`owner_compare.nohup`、两份 Owner receipts、比较包装脚本、逐 job rc、DCP .lwt 等；不得删除、重命名、覆盖、全盘复制、合成新的大 artifact。根盘已约95%使用，尽可能只写 **<10MB** 新的 summary CSV/JSON/MD，不反复 `torch.save`。
- 禁止把已修改比较逻辑说成未改原代码的正式 comparator 结果。DS 只能在 /tmp 用**只读**脚本提取事实，不修改 GitHub 生产实现。

## 2. 第一阶段：从已有 168MB JSON 做 metadata-only 一次性聚合

输出轻量 `b1_numeric_small_summary.json`：
- 每个 profile/repeat/rank/iter 对比的 `cross_leg` vs `same_leg_repeat` 总数及 PASS/FAIL；重新核对128 cases、241152 FQN metrics、2000 Fast State units 的真实分母。
- 按 `{family:generation/action/local, metric:gradient/delta_parameter/delta_m1/delta_m2/absolute_m1_after/absolute_m2_after, dtype, small/large numel bucket, iteration, profile, comparison_kind}` 汇总真实 `count,pass,fail,median/p95/max relative_l2, median/max_abs, median cosine`；找第一步离群大参数，而不是只关注接近零的 ΔM2。
- **纠正 Loss 统计**：按 `loss_components` 每个确切 name 的 `total/pass/fail`，再另算 `case_any_loss_fail`、`all_loss_component_total/pass/fail`。用户上报的 256项/84 fail 与 three-name fail=(63+62+45)=170 若代表同一分母则冲突，必须由原始 machine JSON 自洽解释。
- 每个分组保留代表性 10 个 FAIL 的 `profile,repeat,rank,iteration,leg,fqn,role,relative_l2,absolute norms,max_abs,elementwise_pass,cosine,near_zero,reason`，不输出所有24万项。
- 独立从128份 small JSON report 确认 Consumer roster, CFG/site witness exact equality per cross-leg & same-leg repeat，输出总 `compared_consumer_count` 与 `mismatch_count` 的准确分母。避免仅报告“P1 witnesses 256条”，实际采样序列可能大得多。
- 再核对 DCP `runtime_lightweight_immutability_witness` 矩阵（128项应与 `faf63ff224969b5585419bd4432fa9e554ffdf0742831c7a3a2f9972a3c8411b` 一致）、original latest，无额外 DCP 载入/全 shard rehash。解释 scan log 的 `49/49` 与 frozen helper `44文件` 具体差别，而不是假定两者同单位。

## 3. 第二阶段：选取小批 PT，先查“优化器更新前”与第一次分歧

仅 `torch.load(..., map_location="cpu", weights_only=True)` 读取已有 **有权限的本地 /tmp** 原始 tensor capture。建议先从**P0_FIXED / iter1301** 的 rank0/rank2 开始，再针对 top outlier 增加 rank5/rank7 的 P1 样本；如早期已定位则不需扫描所有595GB。

每组必须分别比较：
1. **同腿跨 repeat**：`index8/r0` vs `index8/r1`; `packed128/r0` vs `packed128/r1`。
2. **跨腿同 repeat**：`index8/r0` vs `packed128/r0`; `index8/r1` vs `packed128/r1`。
3. 对相同 FQN (`net.llm2action.bias.weight`、rank0–3 非空 `net.local_memory_runtime.core.slot_queries`、generation q/norm 典型大、小 shard)：
   - `master_before`、`m1_before`、`m2_before`：dtype/shape/FQN/shard identity、**exact hash or torch.equal**、maxAbs、relative L2、norm（判定同一恢复初态）。
   - 由原始 `losses` 读 `weighted_outer` / action / vision 实际值、逐项差与阈值；如果初态一致而 Loss 已漂移，优先观察 Forward/输入；如果 Loss 一致但 gradient 漂移，优先 Backward/GA/FSDP 路径。
   - 对所选 FQN `gradient`、`delta_p`、`delta_m1`、`delta_m2`，输出 norm、absolute max、cosine、r2 pass。若梯度一致但优化器增量不同，优先 FusedAdam/step/capture 契约。
   - 对同场景 fast state 的四 FP32 tensor 先看非空、首步是否一致（作为另一个下游定位）。
4. 只在必要时取 **iter1302** 同组对照，显示漂移是否从第1步开始、还是第2步才出现。高相对 ΔM2 特别同时输出参考范数和绝对差，确认不是仅微小量级分母问题。
5. 请专列 **P0 repeat0 SOURCE vs TARGET** 和 **同腿 P0 repeat0 vs repeat1** 的相同样本，给出第一步结论；不要先断言“GPU算子非确定性”或“Packed128不等价”作为原因。若所有 master/moments before 已不一致，暂停下游推断，先解释 DCP/capture 是否错位；若初态一致，再定位 forward/grad/optimizer。

运行时避免同时加载许多大的 PT；逐对加载处理并释放引用，必要时限制首批文件数；新输出务必小型。只允许探索性诊断，不直接修改阈值或算法。

## 4. Comparator wrapper provenance / both-empty shard

请交：
- `/tmp/psm_v3_b1_owner_compare.py` 文件 SHA256、完整的**局部比较器补丁 diff**或 ≤100行相关 excerpt、与 pinned original `compare_tensor` 的调用关系。
- 可复核的真正 Owner “都为0，视为一致” 授权记录位置、日期/内容；若没有文档化证据，标明 `OWNER_EMPTY_EXCEPTION_PROVENANCE_PENDING`，把生成 JSON 标为 `NONCANONICAL_EXPLORATORY_COMPARISON`。不要伪造或自签授权。
- 轻量合成 CPU 负例证明：仅相同 dtype、shape、同为0元素、相同 shard role 才允许 empty equality；**一侧空一侧非空、shape/dtype/identity不同、非空非有限或超限**均不得因补丁 PASS。可静态演算/测试，不重复149项已关闭的整套CPU。
- 如果 wrapper 还改了任何非-empty分支或 aggregate 逻辑，停止以其结果作为 frozen r2 direct provenance，向 GPT 报准确 diff。

## 5. 输出格式 / 结束

请回传：
- `DS_PRO_V3_B1_r2_first_divergence_and_comparator_provenance_2026-10-16.md`
- `b1_numeric_small_summary.json`（建议 <10MB）及几个 FQN 选定样本的简表。
- 包含每一个 CPU 分析命令/RC、对应 original evidence hash/路径、完整 coverage denominator、第一发生差异的 confirmed observable stage、无法判明的原始模型站点和后续最小实验建议。
- 报告最终状态 `B1_GPU_NUMERIC_FAILED_ROOT_CAUSE_UNDETERMINED`（除非现有数据真的能直接定位），**STOP**；不要启动后续 GPU / Gate M / Formal30k。

**GPT 将复核同一 formal pair 的证据缺口一次，不重新审核未变的诊断代码。**
