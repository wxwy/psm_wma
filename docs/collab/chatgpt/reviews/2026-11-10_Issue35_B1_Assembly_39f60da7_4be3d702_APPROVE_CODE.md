# Issue #35 — B=1 Prefix K/V 组装最小优化：GPT 独立正式审核

**日期**：2026-11-10。**Formal Verdict：`APPROVE_CODE`（仅 B=1 Prefix K/V 组装的本轮最小优化）。**

| 对象 | 精确 SHA |
|---|---|
| Formal Root implementation | `39f60da729a49c9f6514953bf801dcafb7493039` |
| Formal Child / Root Gitlink | `4be3d702f3008040b830ae09c200d80e273a201a` |
| 前一已通过数值修复 Root/Child | `55b74ab461fda27e4ff6490023c828db0abc0a9f` / `bf707810f573e885f0966d65c232dc2a610d6a93` |
| 当前候选 | [Root Draft #37](https://github.com/wxwy/psm_wma/pull/37) / [Child Draft #13](https://github.com/wxwy/cosmos-framework/pull/13) |

Root PR #37 的申请/账本 HEAD `b44dd7aac2056df6b09f34c7cd24fc39180dade0` 和后续 review、Inbox commit **都不是 formal implementation SHA**，不得代替上表技术 target。

## 1. 代码增量与冻结边界

GPT 先从 GitHub connector 获取两 PR、正式请求及增量 diff，随后在授权数据服务器通过 git fetch **精确 SHA** 创建了新的 clean detached Root/Child worktree。Root 的实现增量限于 Gitlink、SESSION/TODO；Child 对比 parent `bf707810`，**仅一个生产文件** `cosmos_framework/model/generator/mot/memory_prefix.py` 新增24行（0删除），另一个已有 `memory_prefix_test.py` 新增181行；原 generic 函数体保持不变。

新分支仅在 `prepend_memory_kv()` 的**无梯度、B=1、非空且长度相符的 Prefix**、Offset 长度2（Native 可含一个末尾 padding 段，则长度3）、合法dtype/同设备形状条件下改为直接 `cat(Prefix, Native)` 与 native Offset 平移 `+k_local`。其它条件继续原有 generic path。

实现没有修改：Memory Prefix 注入位置/顺序、每层 Prefix K/V 投影及归一化、当前 V、Attention Mask/Varlen、Fast Weight 更新、Session/事务/Resume、NoPrefix和NoTTT、训练/反传。作者设定的“不能改变当前 Memory 注入方式”得到保留。源码对齐了 `B1 -> [Prefix, Native, optional Padding]` 的原有有效 Offset 合同；该优化不是跳过 Prefix Attention。

## 2. 独立 CPU 与 source identity

GPT 独立运行上一 formal pair 的**完整 scoped CPU Gate**（将新增2个受检生产/测试文件并入原有静态集合，独立外部 driver，未重用作者测试 exit码）。结果：

- **292/292 PASS，0 failure、0 error、0 skip**；此前已确认的历史 W0 失败仍按原冻结合同单独 deselect，不能说全仓所有测试均绿。
- **11个 scoped 静态文件** Ruff、format、AST 检查通过；**1,487个源码指纹前后完全一致**；Root/Child Gitlink严格相同且 checkout tracked clean。
- 新CPU回归覆盖原generic的Grad-enabled/Multi-B/Empty Prefix fallback、B1不同长度与Padding、BF16/FP32、offset int32/int64、变Prefix/恢复，以及动态/fullgraph图上消除 Scan/Scatter；这不代替真实H100数值证据。

独立CPU记录保留在服务器 `.../issue35_b1_assembly_independent_20261110/cpu_scoped01/{gate.json,focused.xml,focused.log,...}`。

## 3. GPT 实际运行 H100 真实输入严格数值 Gate

在 GPU6 H100 上独立加载正式 Root39f/Child4be 和同一 Local-TTT iter15000 DCP，恢复**真实冻结请求 K=1/source32、K=16/source64**的完整Batch、FastState、4×32 Prefix、四类 RNG、原生BF16/编译与30步UniPC；逐模式执行 `KV OFF/Pack OFF`、`KV ON/Pack OFF`、`KV ON/Pack ON`，每模式重新装载真实输入。

| 核验 | K1/source32 | K16/source64 |
|---|---|---|
| 三模式 raw15 / Action / Vision 与**前次GPT独立保存的原始Local输出** | **逐元素 exact0** | **逐元素 exact0** |
| Stage1 KVon相对原始路径 Velocity | **30/30步 exact0** | **30/30步 exact0** |
| Stage2 KVon+Pack相对原始路径 Velocity | **30/30步 exact0** | **30/30步 exact0** |

**重要：** 之前冻结的旧错缓存 Stage2 输出与原始 Local 存在0.00497/0.00707差异，不能把它作为本次数值正确性金标准。GPT另外在CPU上重新读取本轮六组GPU PT以及两组完整Velocity PT，与上一轮独立保存的`original_K*_step*.pt`逐张量 `torch.equal`，全部通过；四组GPU回放进程exit0。没有只依赖作者PASS或最终Action碰巧一样。

独立数值回读SHA256：`0b7d3917a7a8e1bace33847330f980a3862b1930aba92b5aa1be706c7b556355`。

## 4. GPT 实测性能：相同冻结请求、相同DCP、无人工GPU负载

GPT随后单独对比 **parent `55b/bf707` 与 candidate `39f/4be3`** 在完全相同的Local iter15000 DCP和真实请求上、两项 KV+Pack 缓存均ON。GPU6 H100，单模式暖机4次、正式完整生成30次，时间范围包括当前帧VAE、不含FW更新、网络或Sim；每次输出仍用**同一原始Local参考 Action/Vision**核验。分组顺序为 oldK1→newK1→newK16→oldK16，旧新模型分别在隔离进程串行运行。未设必须达到的加速倍率门槛。

| 模型生成 GPU event 时延 | parent bf707 | candidate 4be3 | 实际变化 |
|---|---:|---:|---:|
| **K1 P50** | **789.680ms** | **693.883ms** | **−95.797ms，−12.13%（1.138×）** |
| K1 mean | 790.293ms | 693.970ms | −96.323ms |
| K1 P95 | 796.301ms | 698.169ms | −98.132ms |
| **K16 P50** | **787.289ms** | **680.790ms** | **−106.500ms，−13.53%（1.156×）** |
| K16 mean | 788.327ms | 696.056ms | −92.270ms |
| K16 P95 | 793.439ms | 739.936ms | −53.503ms |

K16 candidate内有较慢样本约729–743ms，完整保留于平均值/P95/P99，没有删样本；样本数30属于受控模型生成测试，不是线上业务P99或SR的证明。无实时NoTTT benchmark，不能拿不同训练checkpoint的NoTTT与它做严格因果归因；也**不能声称已回收此前全部271–276ms Prefix损耗**。

独立原始样本及计算结果：`.../issue35_b1_assembly_independent_20261110/{old_k1,new_k1,new_k16,old_k16}/result.json`，四组exit0。无人工GPU负载与其它Policy进程；只读原始冻结数据和权重。

## 5. H100 CPU/CUDA Profiler：目标 Kernel 真实消失

使用同一 K1/source32 的真实请求，单模式独立暖机3次、分别采集NoPrefix / Prefix无缓存 / Prefix KV+Pack 的侵入式ChromeTrace，派生汇总与上一正式 Parent Profiler比对：

| Prefix+KV+Pack 事件 | parent bf707 | candidate 4be3 |
|---|---:|---:|
| **GPU Kernel总数** | **35,414** | **27,882** |
| GPU Kernel时间合计 | 155.435ms | 141.393ms |
| `aten::repeat_interleave` CPU调用 | **1,682** | **2** |
| `aten::cumsum` CPU调用 | **1,682** | **2** |
| **CUB Scan GPU Kernel** | **5,045** | **5** |
| `FlashAttnFwdSm90` Kernel | **868** | **868** |

这在源码层验证了新增 B1 直接拼接的作用：不再每层每步构造样本ID/重复扫描，目标 Scan Kernel减少5,040个，而FlashAttention主体Kernel数量不变。CPU/GPU Profiler侵入性很高，且parent与candidate profiler来自不同session；这些事件数量用于路径识别，不能将sum kernel time差值直接当作95–106ms壁钟改善的精确分账。实测改善以第4节30次正常生成为准。

GPU核事件派生对照SHA256：`69feb9dfeb6df8ce54f1b906473111f1620ffa7a058a4a3f06c0a437722f7a2d`。

## 6. 正式 Verdict 与边界

**Verdict：`APPROVE_CODE`（仅固定 Root39f/Child4be 的 B1 Prefix K/V 组装最小优化）。** CPU Gate、H100原生BF16严格数值、30步Velocity、同输入性能及目标Kernel证据都通过；无新增当前阻断项。

**未授权**：PR #37/#13及上游自动合并 V3，修改 Memory 注入位置/意义，B>1或多样本GPU生产推广，900步真实Episode/SR、大规模吞吐/线上P99，第三阶段其余Attention改动。当前B>1仅验证旧generic CPU回退；实际线上还可能有 ~150ms 级别的其它Prefix路径差异，需要另行测量，不可当作本轮已关闭。数值修复此前限域 `APPROVE_CODE`仍保留。

所有真实请求、模型输出和ChromeTrace保存在**授权服务器本地**，没有外传；工作树最终tracked clean，GPU4–7 0MiB，其他训练任务未碰。最终独立派生审计文件 `.../issue35_b1_assembly_independent_20261110/independent_final_verdict.json` SHA256：**`c89821a9ac2efc0000a876b0c33daea8aec38abd3da29f2aa1333fdb8be8df46`**。

本review及Inbox写入属于docs bookkeeping，**不改变正式 implementation pair**。