# Issue #35 — 真实冻结输入下的 Prefix-aware 文本 KV 缓存数值差异：GPT 独立执行报告

**审核日期**：2026-11-10。**Formal Root**：`18be4a80a5ae4d97bc7d287034d24efab847c496`。**Formal Child / Gitlink**：`193627f42f4cd1ba6d563aefb8fa8f9428ecb56d`。实施代码、checkpoint、Gitlink均未变。本报告是**新真实输入数值证据**，不是重复做之前的合成输入代码审核。

**当前 Verdict：`REAL_INPUT_STRICT_NUMERICAL_PARITY_FAIL`。** 首次差异发生于 Stage1 Prefix-aware Text KV 的**缓存命中**路径；Stage2 Prefix-safe Pack 并非首次差异来源。**不能据此证明缓存内容必然错误**：需要继续区分 UND KV 的静态性/值、Attention 的排列/掩码/填充和BF16编译舍入。不过已足以阻止宣称真实闭环动作严格数值等价及无条件合并V3。

## 1. 审核执行方式

GPT直接使用授权服务器上的冻结**真实请求**，非作者合成观测：

- K1 `source_step=32`：`_gpt_independent_gates_20261104/issue35_render_group_capture_20261110/k1/capture/request_0032.pt`。
- K16 `source_step=64`：同根的 `k16/capture/request_0064.pt`。每份均包含原始Policy Batch、上一/当前FastRecord与实际FastState、4×32 Prefix、Torch CPU/CUDA+NumPy+Python RNG与同输入的原生 prepared、原始模型输出。
- GPU6 H100 单进程B1，Local-TTT iter15000 DCP，30步UniPC；模型通过真实 ActionModelService 原生加载且`validate_model_mode()` PASS；原有编译上限、BF16、模型模式不改。
- 每种K依次恢复**相同**冻结Request/RNG，并运行：①`KV OFF, Pack OFF`，②`KV ON, Pack OFF`，③`KV ON, Pack ON`。每次重新从保存文件恢复原Request以避免跨模式输入污染。
- 用 `torch.equal`/最大绝对误差比较 GPU 保存的Vision/Action、raw15 action，并**与两次旧代码真实Episode和新代码真实Episode的原始动作**直接验证；全部私有原始张量只在服务器内读写。
- 为寻找首次不同步骤，再独立执行一次仅含①/②的逐步 `_get_velocity` **诊断包装**，捕获30步速度预测；此包装不修改生产代码，并核实其最终Action与无包装回放保持相同。

## 2. 三种路径：真实模型输入下的直接回放

| 严格同Request/RNG | K=1/source32 | K=16/source64 |
|---|---:|---:|
| ① KV OFF、Pack OFF 与**旧真实Episode**动作 | **逐元素完全一致** | **逐元素完全一致** |
| ① 与冻结的**新Stage2** raw15动作最大误差 | **0.0049707889556884766** | **0.007069587707519531** |
| ① 与新Stage2的 Vision 最大误差 | 0.040755629539489746 | 0.026320815086364746 |
| ② KV ON、Pack OFF 与**新真实Episode**动作 | **逐元素完全一致** | **逐元素完全一致** |
| ③ KV ON、Pack ON 与**新真实Episode**动作 | **逐元素完全一致** | **逐元素完全一致** |
| ② 与③之间，Action + Vision | **逐元素完全一致** | **逐元素完全一致** |

因此：旧代码/缓存关闭路径复现旧真实轨迹、开启文本KV复现新真实轨迹；在相同完整真实输入下，**Stage1 KV 的开关足以导致差异**，不依赖后续仿真轨迹分叉或模拟GPU负载，Stage2 Pack复用不影响上述请求结果。

## 3. 逐步速度预测（去噪Step从0开始）

| `_get_velocity` 逐步max_abs：① vs ② | K=1 | K=16 |
|---|---:|---:|
| Step0，缓存首次填充 | **0** | **0** |
| Step1，首次文本KV缓存命中 | **0.03125** | **0.046875** |
| Step2 | 0.046875 | 0.046875 |
| Step3 | 0.0625 | 0.0546875 |

- 两种K均**Step0 exact，Step1首次差异**。因此可把第一差异定位到文本KV缓存命中/GEN-only推理分支，而不是首次填充结果（但不能由此断言缓存的UND K/V错误）。
- 逐步诊断中同样复现原始最终Action最大误差。注意这次仅用于数值定位，采样包含编译/探针开销，**不做性能结论**。

## 4. 服务器证据与清理

- 全部真实输入、原始Action、速度预测PT与工具均保存在**服务器私有目录**：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_real_input_3way_replay_20261110/`。
- 各K有 `k1/result.json`、`k16/result.json`（3路径）、`k1_velocity/result.json`、`k16_velocity/result.json`（逐步），各自行程 `exit0`。详细派生核对 `independent_final_audit.json`，SHA256：`f15d35a5e4697912e233c2d3e2c6a6477f185d72ce76aa413a5dd8877185227e`。
- 两仓 tracked clean 且Root/Child/Gitlink身份一致；GPU4–7退出后均0MiB，独立模型进程无残留。未运行NoTTT、无Sim完整Episode/SR新评测、无生产代码修改或模型权重变更，私有张量未向外复制。

## 5. 现阶段的工程约束

**`Stage1`此前的有限 `APPROVE_CODE` 针对固定合成模型内样例，该审核证据保留；本次新增的真实输入严格数值一致性检验不通过，真实闭环等价/合入V3不得由该旧代码审核自动推出。**

第三项Attention优化不应越过此问题。后续必须进一步判定命中后UND KV是否真正与普通路径逐元素一致，或差异来自GEN-only Attention的BF16/varlen/compile浮点路径；需要在同一冻结输入下检查第一处不同中间张量，随后再决定最小修复与容差要求。无任意预设加速倍率，勿刷NoTTT。Issue35保持Open，但**EGL、输入采集阻塞已经关闭**。