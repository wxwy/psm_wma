# Issue35 请求内原生 Prefix K/V 投影复用：窄增量代码审核申请

2026-11-10（Asia/Shanghai）。Codex 实现与作者 CPU，GPT 独立代码及真实 H100 验收。**作者 CPU PASS；新配对尚未获得独立 APPROVE_CODE，真实 BF16 数值与性能均待验证；PR保持Draft，不合并V3。**

| 对象 | 精确 SHA |
| --- | --- |
| Formal Root | `1b184204e301a51a7a20ed4dde1a11689589cf2d` |
| Child / Gitlink | `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2` |
| Root直接父提交（最新审核/交接） | `8406fc8650088d5ef1f79bb6d63f46a3be41370b` |
| Child直接父提交（已批准B1组装） | `4be3d702f3008040b830ae09c200d80e273a201a` |
| 上一已批准implementation Root | `39f60da729a49c9f6514953bf801dcafb7493039` |

两仓隔离分支 `v3-local-prefix-projection-issue35-20261110`，均以 `v3-local-prefix-b1-assembly-issue35-20261110` 为 stacked Draft base。Root实现只更新Gitlink/SESSION/TODO；后续文档/证据提交是账本，不替代上表Formal Root。上游RootPR37/ChildPR13保留。

## 根据已批准B1结果收敛本次范围

先显式fetch/readback Root8406fc86，列出4个新审核/证据提交、ancestor检查和ff-only成功；读取正式B1 APPROVE_CODE及K16投影报告、canonical Inbox和[精确Issue交接](https://github.com/wxwy/psm_wma/issues/35#issuecomment-6760985484)。没有重复前一Pair的Code/GPU Gate。

GPT的K16/source64真实模型诊断将剩余开销指向28层每轮重复Prefix投影及归一化。Eager微基准120.32ms与一次4.18ms只是优先级证据，**不是本候选整模型可节省119ms的承诺**。本轮没有新H100计时或服务器访问，后续硬件仅K16，不重复K1/No-TTT。

## 实现：从首轮实际Attention buffer捕获，请求内复用

Child仅4个生产文件（150新增/11删除）和一个测试文件（331新增/10删除），总481+/21-。不改Context构建、已批准B1组装、模型参数/配置或任何训练、仿真代码。

1. `omni_mot_model.py`：只对原有Prefix TextKV eligible请求附加权限，继续B1/two_way/guidance1、无CFG等原条件，并要求模型和实际net均eval、no-grad。新增Python诊断参数 `use_prefix_projection_cache=False` 可保留前一批准路径，未新增CLI/YAML/Manifest参数。
2. `inference_text_kv_memory.py`：在编译decoder外，以Prefix Tensor强引用、版本、storage指针/shape/stride/offset/dtype/device证明仍为同一输入。每个step读取仅Host metadata，不逐层执行all/where或同步GPU。替换、普通原地修改、换storage时不授权复用；Tensor子类、requires-grad、不可追踪版本的inference Tensor等保守回退。native online adapter在inference_mode(False)中构建普通版本化Prefix；无法证明时允许少提速，不能少验证。
3. `attention.py`：首轮真正执行原投影/归一化/组装/Attention，新增私有四Tensor tag返回实际送入GEN FlashAttention的已物化K/V buffer、原始归一化输入和UND索引。保持普通KVToStore四元组合同；**不是Eager预计算，也没有为了缓存重新投影或stack**。decoder外再切取小Prefix K/V、抽取UND并detach.clone，完整GEN buffer不持久存储。
4. `unified_mot.py`：只有明确授权的缓存命中才使用本请求首轮原生rawK、normalizedK和V，跳过重复k_proj/v_proj/k_norm；验证缓存shape/dtype/device/完整性。live GEN K/V仍当前计算，Prefix注入位置、顺序、Mask、Varlen/Flash后端保持。原normalization memo算式AST完全相同，仅文档变化。

缓存仍由每次generate新建并在原finally清理/恢复dispatch，不进入Session或跨Replan。FastWeight更新会为后续请求产生新的Prefix，不能复用上次cache。冻结slow weights的推理合同沿用原TextKV路径；训练和参数更新不在新能力范围内。原路径、未授权changed Prefix继续每步当前投影；无Prefix/多B/CFG等维持既有路径。

**关键待硬件验证的点**：返回原生完整buffer避免额外materialization造成编译数值变化，但改变输出/命中图仍可能影响Inductor融合。CPU严格相等、真实buffer指针与Eager子计算重复相同，都不能替代真实整模型BF16的全部30步检查。

## 作者证据：确定性RED/GREEN与exact clean完整CPU

| 检查 | 实际结果 |
| --- | --- |
| 原Child4be受控预算回归 | 1个预期FAIL；3层每层K/V/KNorm各30次，要求各1次 |
| 相同回归函数新版 | PASS；每层各1次，函数AST与旧RED完全相同 |
| 最终Prefix测试文件 | 59/59 PASS，0失败/错误/跳过 |
| exact clean新Formal Pair完整既有scoped Gate | **314/314 PASS**（原292+新增22），0失败/错误/跳过，Shell0，49.236s JUnit |
| 静态及源码身份 | 11文件Ruff/format/AST通过；1,487项前后指纹相同，Root/Child干净且Gitlink相等 |
| 原有例外 | 1项历史W0明确deselect不计PASS；3项已有I001例外保留，无新增 |
| 真实H100 / 模型内加速 | **NOT_RUN / 不作收益声明** |

59聚焦与314完整重叠，不相加。新增测试覆盖真实generate30步投影次数、FP32/BF16/padding逐30步严格相等、捕获buffer与真实Attention输入指针一致、UND位置与offset不变、源对象/版本/storage改变恢复、inference Tensor与训练/opt-out回退、异常/重试/请求隔离/clear、缓存损坏拒绝，以及CPU fullgraph dynamic=False/True。fullgraph测试使用tensorized因果/样本mask的CPU Attention替身，不声称CUDA后端验证。

开发历史全部保留：首轮58项55PASS/3FAIL是fixture scope/no-grad及Python CPU Attention stub的不适合fullgraph；只修fixture，无放宽容差。中间59PASS的stack capture版本和源码patch也保留；最终改成直接返回native buffer后再59PASS，随后冻结新Pair执行314PASS。旧RED只添加测试，非clean Formal；decisive函数AST一致，不用import错误冒充RED。

原始JUnit、命令/环境/退出码、失败日志、旧fixture、源码前后指纹、版本证明与可复跑命令见[Evidence README](../evidence/2026-11-10_issue35_prefix_projection/README.md)。包装/既有scoped Gate入口未改，仍CPU/offline、OMP/BLAS1线程；没有运行checkpoint或模拟环境。

## 下一道独立真实H100 Gate：仅K16/source64

1. 新clean精确Pair上，保留verify_source、DCP/checkpoint/UUID/PCI校验、BF16、recompile_limit8。使用同一Local iter15000、原生B1/H16/raw15/guidance1/30-step UniPC。服务器已有K16/source64输入、prepared、FastState/Prefix和RNG只在授权服务器内加载，不上传。
2. 同一输入每路重置全部状态，比较原Local KVoff/Packoff、Stage1 KVon/Packoff、Stage2 KVon/Packon；新投影cache ON/OFF对照。先对已批准原Local的30/30步velocity及Action/Vision/raw15要求逐元素exact0；同时检查Prefix改变/恢复、请求清理、下一Replan新状态。任何差异保留首层/首step后停止性能结论。
3. 数值通过后再同DCP/真实输入比较已批准4be与候选d5的native生成；预先固定暖机和至少30轮交错测量，标明是否包含当前帧VAE。记录mean/P50/P95/P99及全部离群值、GPU外部负载；不得剔除P99离群或设未经授权的加速硬目标。
4. 可取新的K16 compiled profiler验证Prefix GEMM/normalization重复次数是否减少、Flash/Varlen合同不变；Profiler不替代正常计时，Eager120ms不作精确可回收预算。若普通inference Tensor回退，明确报告命中状态，不能以旧路径冒充新cache加速。

当前请求只审核这次生产增量与CPU证据，再由GPT执行上列真实Gate。不做新的K1、No-TTT、Sim/SR/900EP、训练或GPU负载管理；没有V3合并授权。所有既有正式批准和原始失败保留，Issue35总体性能/P99结论仍开放。
