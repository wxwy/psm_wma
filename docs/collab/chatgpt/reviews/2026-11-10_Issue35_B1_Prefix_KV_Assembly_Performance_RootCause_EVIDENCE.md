# Issue #35 — 保持 Memory 注入方式不变的性能根因诊断：B=1 Prefix K/V 组装

**日期**：2026-11-10；**类型**：GPT独立源码+服务器GPU性能 Evidence，**不属于新代码Gate**。

**Formal pair未变**：Root `55b74ab461fda27e4ff6490023c828db0abc0a9f` / Child+Gitlink `bf707810f573e885f0966d65c232dc2a610d6a93`，clean、未合并V3；既有数值修复 `APPROVE_CODE` 保持有效。

**Owner明确禁止改变 Memory 注入方式**：不能移动/删除 Prefix、改变每层K/V注入或Attention语义。本轮全部为模型外诊断，不改生产代码、不动训练、FW、Local/GlobalMemory的接口，不重跑NoTTT。

## 1. 同 checkpoint 单变量隔离：两条真实冻结请求

使用**相同Local-TTT iter15000 checkpoint**、GPU6 H100、同一原始Batch/图像/状态/初始化RNG、30步UniPC、B1/guidance1，对每份冻结真实请求执行20轮交错Latin-square顺序A/B/C（每模式先暖机3次）：

- A `native_no_prefix`：仅本次诊断将请求内 `_local_memory_prefixes=None`，当前Local checkpoint的原生推理路径。**这不是重新训练/运行NoTTT checkpoint**。
- B `prefix_no_cache`：保持完全原样的Prefix注入和Attention逻辑，仅KV和Pack缓存关闭。
- C `prefix_kv_pack`：保持相同Prefix注入、KV和Pack缓存均开启（Issue35数值修复后的版本）。
- B/C所有20轮 raw15、Action和Vision都严格对齐同一独立保存的原始Local输出；A动作不同，符合Memory实际进入Action路径的预期。

| GPU模型原生生成P50（含当前帧VAE） | K1/source32 | K16/source64 |
|---|---:|---:|
| A 不注入Prefix / 同Local DCP | **537.371ms** | **531.808ms** |
| B 原Prefix / 不启用两项缓存 | **995.281ms** | **980.972ms** |
| C 同Prefix / KV+Pack开启 | **813.375ms** | **802.984ms** |
| B−A 额外损耗 | 457.910ms | 449.164ms |
| B−C 缓存已回收 | 181.906ms | 177.988ms |
| **C−A 尚未回收** | **276.004ms** | **271.176ms** |

以上是每case n20的同一GPU交错控制实验，真实输入来源及权重相同，**比历史NoTTT独立训练checkpoint mean616.258ms更适合做此项单变量性能归因**。K16在C模式有单次1340.63ms离群，保留于平均值/P99，P50未剔样本。人工`gpu_load_sim`在实验开始时仍在GPU4–7运行（检测其它计算进程时轮询让出计算）；它后来独立停止，本轮没有操作其进程，因此绝对时延含环境限定。两K三个模式交错，P50差异稳定。

## 2. 同输入 CPU/CUDA Profiler：GPU计算不是完整耗时的主要差额

在**同一K1真实请求**、同Local checkpoint，对A/B/C分别warmup3、再抓一次CPU+CUDA ChromeTrace，未改产线代码（Profiler侵入性导致walltime膨胀，不用Profiler walltime代替正式20轮的P50）：

| 单次Profiler统计 | A原生无Prefix | B Prefix无缓存 | C Prefix KV+Pack |
|---|---:|---:|---:|
| GPU Kernel数量 | **17,712** | 47,330 | **35,414** |
| GPU Kernel时间合计 | **113.548ms** | 229.896ms | **155.435ms** |
| `aten::repeat_interleave` CPU calls | **2** | 1,740 | **1,682** |
| `aten::cumsum` CPU calls | **2** | 1,740 | **1,682** |
| CUB Scan相关GPU Kernel | **5** | 5,190 | **5,045** |
| Varlen FlashPrepare Kernel | **0** | 1,680 | **868** |
| FlashAttention SM90 Kernel | **868** | 1,680 | **868** |
| FlashAttention GPU时间合计 | **11.147ms** | 20.434ms | **12.281ms** |

核心观察：**C相对A增加17,702个GPU Kernel事件，但GPU Kernel运行时间总共只多41.887ms**；完整无Profiler模型生成P50却多约271–276ms。说明大头不仅是GPU算术，也包含大量动态GPU launch、CPU调用、Tensor元数据/扫描/搬运和调度序列。不能把Profiler中CPU inclusive/核时间简单相加成某个可以直接节省的精确毫秒。

## 3. 与代码逐项匹配：额外Scan来自重复Prefix K/V元数据组装

生产源码未修改，证据绑定当前Childbf707：

- `cosmos_framework/model/generator/mot/attention.py:276–283`：Memory Prefix存在时**强制Varlen**；随后 `:363–378` 每次GEN Attention调用 `prepend_memory_kv(...)`。
- `cosmos_framework/model/generator/mot/memory_prefix.py:127–174`：`prepend_memory_kv` 为每个样本重算长度和偏移，并执行 `torch.cumsum`、两个 `torch.repeat_interleave`、`arange/索引/两次index_copy` 构造与Prefix合并后的K/V。即使B1、固定k_local=4，也走通用多样本路径。
- 28层×30步=**840次**每请求调用；每次2个`repeat_interleave`，所以Prefix C比原生A**恰好多1,680次**同名CPU调用、1,680次`cumsum`，CUB Scan内核**恰好多5,040个**（约3×1,680），与该实现的反复scan调用精确对应。
- 同时C相对A多8,316个TritonFused、1,710个NVJet类kernel及868个Varlen Prepare内核。FlashAttention主kernel数量**没有增加**（均868）；Flash本体GPU时间只增加约1.13ms，额外Varlen Prepare GPU总时间约2.81ms。这不支持把剩余276ms简单归因于FlashAttention数学工作量。
- 代码仍每层当前Prefix K/V投影并注入，Memory实际作用于Action，**但额外反复重建B1 K/V偏移与索引不是Memory算法本身要求的额外信息量**。
- 此轮配置未启用Global Memory，问题不能归咎于Global Memory。`SetupArgs.diffusion_cache`基类默认False、该Policy没有启用标志；不能把此实验损耗自动解释为SeaCache禁用。

## 4. 不动注入方式的候选优化与已核查边界

不建议立即改Prefix注入位置、Attention Mask或Dense/Varlen策略。**优先仅在`prepend_memory_kv()`内部对 B=1 做布局等价的轻量K/V组装快路径**：一个样本的K/V顺序依然 `[Prefix4, NativeK/V, optional Padding]`，Offset只需相同长度平移，无需每层每步展开两次样本ID/重复做CUB Scan和index-copy。非B1、多视角/CFG/复杂Padding保持现有通用实现。

GPT在**服务器隔离CPU诊断**中对B1 native_len∈{1,32,132,267,400}、pad∈{0,2,8}、float32/BF16共 **30/30组合**，验证直接cat+offset-shift得到的K、V、offset、maxlen与现有`prepend_memory_kv`逐元素一致。**这仅是CPU布局等价，不代表整模型编译后的BF16严格数值Gate已通过。**

任何Codex最小候选必须保持接口、每层Prefix K/V、顺序、原Mask、Padding、同请求慢权重不变，并重新在冻结K1/source32、K16/source64上验证**30/30步velocity及Action/Vision exact**、Prefix变化/恢复、无Prefix/非B1回退、失败清理；真实H100报告新旧同checkpoint/n轮性能，不预设加速阈值。只有新正式Root/Child实现pair才发起下一次技术审核。

## 5. 证据、结论、边界

GPT独立服务器路径：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_prefix_overhead_samecheckpoint_20261110/`。其中:

- `k1/result.json`、`k16/result.json`：各20轮交错3路径、正式原始GPU event时间，均exit0、strict action/vision PASS。
- `profiler/profile_*.json`：3份原始私有ChromeTrace（不上GitHub）；`profiler/summary.json`与`profiler/cpu_cuda_event_classification.json`为派生内核分类。
- `cpu_b1_layout_equivalence.json`：30组B1布局CPU exact equivalence PASS。
- `independent_performance_root_cause.json`：最终独立派生Evidence，SHA256 **`bb871e8bf07e03f7832e60170e50006947e630b1639ce435ec40dbe93c146322`**。

全部原始业务张量/模型/ChromeTrace只保存在授权服务器，本次未外传；两仓clean、GPU4–7结束后均0MiB、未触碰GPU0–3。人工负载模拟器后来退出，并非本诊断主动终止。

**正式Evidence Verdict：`B1_PREFIX_KV_ASSEMBLY_REPEATED_SCAN_AND_KERNEL_LAUNCH_OVERHEAD_CONFIRMED`**，其中完整额外276ms的**精确子项归因仍是未解的剩余工作**；目前已有足够证据指导最小B1组装优化。它不等于第三阶段性能优化完成，不改变现有数值`APPROVE_CODE`、不授权V3合并。