# Issue #31 Stage 2 — Prefix-safe Pack Reuse：独立审核结论更正

**审核更正日期：2026-11-09**  
**Formal Root**：`18be4a80a5ae4d97bc7d287034d24efab847c496`  
**Formal Child / Root Gitlink**：`193627f42f4cd1ba6d563aefb8fa8f9428ecb56d`  
**Stage 1 基线**：Root `5b89f3eddbfe27ee72c173696a386e0b756d7866` / Child `4446be0f6dad9b6dc887ef90af52d0af754d4682`  
**更正后的独立结论：`APPROVE_CODE` — 仅限 Stage2 B1/single-sample/two_way/guidance1 Prefix-safe pack reuse 的实现正确性和同权重 model-only 时延证据。**

## 更正原因（保留原审核历史）

此前独立审核错误地将作者 Benchmark 内部的 `P50 speedup >= 1.05x` 当成 Owner 强制代码通过门槛，并据此判定 `REQUEST_CHANGES`。经 Owner 明确指出，优化不应预设必须提速多少；Issue31 的 Owner 目标是定位瓶颈、保持数值一致性并如实测量性能，不存在必须超过 1.05x 的冻结验收合同。

**这是审核标准适用错误，而非代码修改或数据更改。** 原审核文件 `2026-11-09_Issue31_Stage2_18be4a80_193627f4_PrefixPack_REQUEST_CHANGES.md` 作为历史记录保留，并以本文为该 formal pair 的后续更正。不得修改作者脚本阈值、原始测量数据或历史退出码，也不能将作者当时的 `PERFORMANCE_NOT_MET` 描述为曾经通过。

## 冻结源码与正确性

- Formal Root Gitlink、Child HEAD 及作者提交身份已独立核查一致；PR #33 / Child PR #11 均是 Draft，未合并 V3。
- 唯一变动的 Child 生产函数为 `omni_mot_model.py::generate_samples_from_batch`；针对满足 Stage1 Prefix-aware Text-KV 资格的 B1/two_way/guidance1 请求开启 request-local pack template。已有文本KV缓存、Attention、TTT、VAE、Sim/Worker、训练、模型模式校验及严格 Resume 逻辑不改。
- 每次去噪更新噪声和时间步，维持当前 Prefix/条件 mask/位置/动作元数据；无跨请求模板；unsupported layout、NoPrefix/NoTTT 使用既有路径。独立代码审阅未发现本次新生产逻辑阻断项。
- 作者定向 `201 passed, 1 deselected`（旧W0失败明确排除，未算通过），1487源文件哈希一致；GPT独立在 exact clean pair 服务器执行新增 `prefix_pack_template_test.py`：**14/14 PASS**。旧W0断言曾在旧/新代码分别重现相同失败，非本轮引入。

## 同一 H100 checkpoint、固定合成输入的独立GPU复核

GPT直接审查授权服务器 `_codex_issue31_prefix_pack_20261109/gpu02` 的原始测量、保存输出，不外传原始文件。**31/31** 原始文件 SHA256与公开派生索引匹配。30组均衡AB/BA、60次模型内测量，无样本筛除；双方Text KV均开启，差异仅为Pack OFF/ON；30/30组更快。

| 指标 | Text KV ON / Pack OFF | Text KV ON / Pack ON |
|---|---:|---:|
| H100 Native Generation P50 | 837.0812 ms | **798.8678 ms** |
| P95 | 844.7195 ms | 803.0262 ms |
| P99（小样本插值） | 846.2682 ms | 805.8524 ms |
| Mean | 836.9260 ms | 798.0850 ms |
| VAE P50（含在生成阶段内） | 4.3394 ms | 4.3290 ms |

P50 实际缩短 **4.565%**、加速 **1.047834×**，配对平均节约 **38.841ms**；**这是观察结果，不是成功率或整个Episode的加速结论**。

GPT直接用 `torch.load(weights_only=True)` 比较GPU原始输出：Pack ON/OFF的 Action 和 Vision 逐元素 `torch.equal`；重复原请求输出一致；改变 Prefix 会改变原始 Action（max_abs=1.9608675）。28层×30步的 Prefix Context/KV投影全程存在，KV缓存后29次gen-only；native pack从总31降至2（共同准备1，生成中30→1）。当前单GPU原始模型内数值证据可以支持有限范围的 `APPROVE_CODE`。

## 原Benchmark的真实记录（不能掩盖）

- 作者 Bench 的自设 `>=1.05×` 条件**确实没有达到**；程序记录 `CORRECTNESS_PASS_PERFORMANCE_NOT_MET`、**Shell exit 2**，均应保留。它代表作者该条内部性能目标未达到，**不自动构成 Owner 要求代码返工**。
- Stage1 曾出现一次 P99 离群值，其原因仍未定位。Stage2 本次30组P99数值改善**不意味着**生产长尾已验证。
- 测试仅限合成固定输入、真实Local iter15000模型、B1/30步；不证明NoTTT等价吞吐、真实RoboCasa闭环/SR、多Sim/Batch或生产SLA。

## 结论与边界

**`APPROVE_CODE`（Stage2限域） + `OBSERVED_PERFORMANCE_IMPROVEMENT`（P50 -4.565%） + `AUTHOR_BENCH_INTERNAL_TARGET_NOT_MET`（1.0478x < 1.05x，Shell2）。**

三者同时成立，不矛盾。此结论不批准PR33/11、上游其他Draft PR自动合入V3，也不批准下一阶段Dense Attention重构或生产部署。后续是否继续优化应根据实际收益和剩余瓶颈确定，而非人为跨阈值。正式实现SHA仍是上面的18be/1936，审核文档提交不是新formal pair。
