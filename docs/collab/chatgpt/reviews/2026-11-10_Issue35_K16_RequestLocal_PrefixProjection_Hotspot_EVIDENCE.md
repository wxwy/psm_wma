# Issue #35 — B=1 组装优化后的 K=16 Prefix 投影重复计算：GPT 独立证据与下一阶段最小 Gate

**日期**：2026-11-10。**审核类型**：性能根因延伸调查与请求内复用可行性证据，**不是生产代码审查或 APPROVE_CODE**。

- **正式 implementation pair 未变化**：Root `39f60da729a49c9f6514953bf801dcafb7493039` / Child-Gitlink `4be3d702f3008040b830ae09c200d80e273a201a`；Root PR #37 / Child PR #13 继续 Draft，未合并 V3。
- **Owner明确收敛**：后续性能定位只测 **K=16**，不再重复运行 K=1；保留此前 K1/K16 对照。不能改变 Local Memory Prefix 注入位置、顺序、Attention 语义、Action Path、Mask/FastState/训练。Global Memory 在这轮 RoboCasa 上未启用。

## 1. 当前 K=16 同 checkpoint 真实输入对照

GPT直接用授权 H100 GPU6，固定 Local-TTT iter15000、CloseFridge/seed4603 **真实冻结 K16/source_step64**、30-step UniPC、B1/guidance1、同 FastState、Prefix 4×32 和 RNG，20 轮 A/B/C 交错、每模式3次暖机，无新的 No-TTT checkpoint 测试。

| 同 Local DCP 模型原生生成（含当前帧 VAE）P50 | 毫秒 |
|---|---:|
| A：诊断性不注入 Prefix | **521.250** |
| B：保留原 Prefix，KV/Pack OFF | **883.451** |
| C：保留原 Prefix，KV+Pack ON、B1组装已优化 | **684.582** |
| **C−A 尚未回收额外成本** | **163.332** |

B/C 在此冻结请求逐次 raw15/Action/Vision 严格等于已批准的原始Local；A因为缺少Memory输出改变（预期）。本报告只探究残余开销，不建议移除Prefix或变更注入。

## 2. 核实 Prefix Context/K/V 的源码依赖关系

- `mot/cosmos3_vfm_network.py:1602–1611`：每个采样前向都会从相同请求固定4×32 Local tokens经过 `local_memory2llm` + modality embedding 重新建 `MemoryPrefixContext`。
- `mot/unified_mot.py:1474–1477`：28层分别对 Prefix Context 调用本层 `input_layernorm_moe_gen`；`:812–826` 对本层归一化Prefix隐状态调用 `k_proj_moe_gen`、`v_proj_moe_gen`、`k_norm_moe_gen`，然后**仍按现有原位置**把K/V交给 `dispatch_attention_fn`。
- 在同一 `generate_samples_from_batch()` 的30个扩散步骤中，当前所用Prefix token和模型慢权重不发生更新（Local FastState适配在不同Replan之间）；因此这些**独立于变化的噪声/时间步**的前置投影表达式在数学语义上是请求内常量。
- 已批准旧数值修复证明实际 Inductor BF16 fill/hit 图存在舍入边界差异。独立 Eager子表达式值相同**不等于**外提并缓存后整模型 Inductor 数值一定严格相同，不能直接缓存并宣称 APPROVE。

## 3. 已运行的 K=16 独立静态性实验

在授权服务器加载同一真实DCP和K16/source64请求，使用实际网络参数，在 `torch.inference_mode` 中对 `local_memory2llm → Prefix Context → 28层 LayerNorm / KProj / VProj / KNorm` **重复30次**，所有前置 Context / Layer K、V **torch.equal = True，max_abs=0**。修改冻结Prefix一个值，28/28层K/V全部改变；恢复Prefix后全部再次 exact。

结果：`.../issue35_post_B1_remaining_overhead_20261110/static_prefix_projection_report.json`；SHA256 `3aca62b973df06753defca3ecb323706370f34af8b5ff608a296ba76cbc50ed5`。

## 4. 只测 K=16 的重复投影定向计时

另一独立脚本读取相同DCP、冻结K16/source64，H100 GPU6、**Eager 子表达式**，每种模式warmup3、正式计时15轮；每次计时包含所列整组30个模拟采样步骤，不包含真实模型其余Attention/MLP。GPU事件和主机墙钟单独记录。

| 30步投影子表达式 Eager 计时 | GPU event P50 | 主机 wall P50 |
|---|---:|---:|
| 仅重建 Prefix Context ×30 | **1.960ms** | **1.981ms** |
| Context固定，28层 K/V+归一化 ×30 | **120.322ms** | **120.362ms** |
| Context和28层K/V全部重复 ×30 | **123.384ms** | **123.435ms** |
| Context和28层K/V仅执行1次 | **4.178ms** | **4.207ms** |

输出所有K/V在两个独立计算轮次之间严格一致。原始派生数据在服务器私有 `.../issue35_post_B1_remaining_overhead_20261110/k16_projection_microbenchmark.json`，SHA256 **`7c7da9177eddb31f880eb60ce748de93921a6e4bc7f125f93ac6c1d412150741`**。

**重要统计边界**：这不是整模型编译路径计时，不能把 `123.435−4.207` 直接当成真实推理可回收的119ms，也不能和Profiler包含的Kernel时间相加。量化的只是重复子表达式值得优化，实际编译图中投影/归一化的融合程度和cache读入成本仍未验证。

## 5. 现有编译模型 Profiler（历史 K1证据，不是本次新运行）

上一个B1组装批准时在K1固定真实输入采集的单份GPU trace，仅用于跨层算子频次定位，不把它冒充本轮K16实测：Prefix KV+Pack相对NoPrefix **额外1,710个NVJet GEMM**，恰与每层2个K/V投影 `28×30×2=1680` 加每次一次Context投影30的源码频次一致；额外 **5,824 Triton融合 Kernel、868 VarlenPrepare**，FlashAttention SM90 Kernel数量均868。上述计数是强相关线索，不等于把所有GPU kernel因果逐个绑定到这些Python调用。

本次 K16 独立派生汇总：`.../issue35_post_B1_remaining_overhead_20261110/independent_projection_reuse_finding.json`；SHA256 **`ef369e3b61b89c9de10159ff81c1ff6c5a5b012b80ceeda81e692a33f162ff76`**。

## 6. Codex 下一阶段最小候选边界（先正确性，再性能）

**建议下一项独立候选是请求级 Prefix Context/逐层 K/V 投影复用，不改变现有Attention Memory注入**，但应优先**K16验证**；也可先单独尝试层级K/V缓存，避免为了Context仅约2ms而大改结构。

1. 保持每层 Prefix Key/Value 注入位置、顺序、LayerNorm/投影算式、Attention Mask/Varlen、当前Genv K/V、Local FastWeight及模型慢权重完全不变。请求级数据只能在同一 `generate_samples_from_batch()` 有效，失败finally必须释放。严禁跨请求/跨Session重用 Prefix 值。
2. 由于同一固定Prefix可能在 native fill 与 compiled gen-only 图出现 **BF16归一化/投影舍入差异**，**不得只因 Eager静态性通过就直接复用一个独立预计算张量**。若外提/缓存后 Action 或任一Velocity不等于原始 Local，则先停止、找首个不同的投影/归一化Tensor，不要改数值容差凑通过。
3. 编译快路径只能在明确 frozen Prefix + frozen slow weights + B1 inference/two_way/guidance1 条件下开启。训练/grad-enabled、Prefix缺失、更换Prefix、不同B/CFG、失败重试以及不满足编译边界时保持原旧路径；不能改已通过的Stage1文本KV归一化修复合同或B1组装快路径。
4. GPT后续独立 H100 **仅 K16/source64**：①对原始Local KVoff/Packoff与 Stage1 KVON/Packoff及 Stage2 KVON/Packon逐张量 Action/Vision/raw15严格 `torch.equal`；②全部30步Velocity逐元素exact；③Prefix修改/恢复及请求隔离、训练/非B1 fallback CPU；④同DCP/同请求、KV+Pack全开，Old vs New正式pair的暖机/交错/30次完整模型生成P50/P95/P99，**不预设加速百分比**。
5. 只有 Codex提交新正式 Root/Child实现 SHA 和原创 CPU/差异测试后，GPT 才做新 Code Gate。不创建第四套Memory注入结构、不重跑NoTTT、不做900步SR、不自动merge V3。

## 7. 当前结论

**`K16_STATIC_PREFIX_PROJECTION_EXACT_IN_EAGER` + `REPEATED_LAYER_KV_PROJECTION_HAS_MEASURABLE_STANDALONE_COST`，不是生产缓存 APPROVE_CODE**。前一正式 B1组装 `APPROVE_CODE` 不变。所有冻结输入、完整权重、导出张量/Profiler均只在授权服务器。Root/Child tracked clean、相关owned进程全部退出、GPU4–7最后均0MiB。