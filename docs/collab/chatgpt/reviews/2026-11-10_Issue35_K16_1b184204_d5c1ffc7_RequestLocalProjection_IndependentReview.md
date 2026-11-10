# Issue #35 — 请求内 Prefix K/V 投影复用：GPT 独立实现与真实 H100 审核

**日期：2026-11-10**　**Formal Code Verdict：`APPROVE_CODE`（严格限于本次 B=1 请求内 Prefix K/V 投影复用及 K16 冻结真实输入验证）**。**性能/启动阶段/生产 P99 Gate 未关闭，不批准 V3 合并。**

| 技术 target | 固定 SHA |
|---|---|
| Root implementation | `1b184204e301a51a7a20ed4dde1a11689589cf2d` |
| Child / Root Gitlink | `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2` |
| 上一已批准 Pair | Root `39f60da729a49c9f6514953bf801dcafb7493039` / Child `4be3d702f3008040b830ae09c200d80e273a201a` |
| Draft PR | [Root #38](https://github.com/wxwy/psm_wma/pull/38) / [Child #14](https://github.com/wxwy/cosmos-framework/pull/14) |

Root `74b48c6...` 和本次 review/Inbox 提交仅为证据账本 HEAD，**不得替代**上述 formal implementation SHA。旧 Pair 技术 Gate 仍有效，不重复做其完整历史审核。

## 1. 增量代码与实际语义

GPT通过 GitHub Connector 审阅作者 PR 申请、正式 diff 与真实代码，在授权 data 服务器通过 `git fetch` 精确 SHA 创建隔离 `detached` Root+Child worktrees，复核 Gitlink相等、两仓 tracked clean。Child相对 `4be3d702` 仅修改4个生产文件（`mot/attention.py`、`mot/inference_text_kv_memory.py`、`mot/unified_mot.py`、`omni_mot_model.py`）和1个测试文件 `prefix_text_kv_memory_test.py`；Root实现只含 Gitlink/SESSION/TODO。

本次核心增量：

- 只有原 Prefix-aware text-KV B1 eligible、模型与实际net eval、no-grad、可追踪 `torch.Tensor` 来源的请求，才建立版本化 Prefix binding；同一个token对象、`_version`、data_ptr、shape/stride/storage_offset、dtype/device 必须保持一致；不符合则回退旧投影路径。Binding不跨请求。
- 初次native fill仍由原Attention执行；新增内部 `_FrozenPrefixTextKVToStore` 从**首次原生已物化的 GEN Attention K/V buffer**捕获 Prefix K/V，随后在 decoder外抽取、clone/detach到 request-local cache。不是用独立Eager重新投影替代native BF16结果。
- 后续命中只在上述请求内可证明来源一致时，逐层使用首次原生 Key输入、normalized K、Value；当前GEN K/V、原Memory Prefix注入位置、Mask、Varlen和现有Attention运算均维持。错误/缺字段拒绝，失败finally清理、恢复原dispatch，不写入Session。
- 显式 `use_prefix_projection_cache=False` 保留旧合法路径用于 A/B；训练、grad、未跟踪 inference tensor、无Prefix、非B1以及不可证明来源等路径沿用原实现。

未发现超出冻结范围的生产结构改动。特别留意：同存储但绕开普通版本计数的外部非法原始内存写入不属于此处已证明的“请求内固定 Prefix”契约；此结论不是对任意并发Tensor原地非法修改的保证。

## 2. 独立 CPU Gate

GPT未继承作者出口码，在新 clean formal Pair 上实际重跑已有 scoped CPU Gate 并扩充静态受检文件集合：**314/314 PASS，0 failures/errors/skips；11个文件 Ruff/format/AST PASS；1,487项源码指纹前后相同。** 历史已确认的 W0 assertion **1项明确deselect**，未计入314；原有3处I001静态例外未扩大。无生产代码编辑。

## 3. 仅 K=16/source64：真实 H100 严格数值 Gate

GPU6 H100，原生 Local-TTT iter15000 DCP，B1/H16/raw15、guidance=1、30步UniPC；从之前冻结的RoboCasa真实 `request_0064.pt` 恢复同一Batch、FastState、4×32 Prefix、Torch CPU/CUDA/NumPy/Python RNG。每模式重新加载真实输入，独立记录30步 `_get_velocity`，严格对比 GPT 已独立留存的 **旧原始 Local（KV OFF / Pack OFF）** raw15/Action/Vision，而不是先前存在浮点差异的历史错误Stage2。

| 路径 | raw15 / Action / Vision | 相对原始路径的全部30步速度预测 |
|---|---|---|
| 原始 Local，KV/Pack OFF | **逐元素 exact** | 基准 |
| Stage1 KV ON / Pack OFF / projection ON | **逐元素 exact** | **30/30 exact0** |
| Stage2 KV+Pack ON / projection ON | **逐元素 exact** | **30/30 exact0** |
| Stage2 KV+Pack ON / projection OFF | **逐元素 exact** | **30/30 exact0** |

独立测试还记录到host级 Prefix binding：三种缓存/开关状态按上述顺序分别为 **0、31、31、0** 次有效绑定。由此确认 projection ON **实际满足eligible**，不是悄然回退路径所造成的“假一致”。重新在CPU直接读取4份GPU输出PT和全部30步速度PT逐张量 `torch.equal` 再次PASS。用户明确要求只测 **K16/source64**，本轮没有重新运行K1。

## 4. 真实性能：三组独立进程与同进程交错对照必须同时阅读

指标仅 `native model generation`，**包含当前帧VAE**、不含FW更新、HTTP、Sim、Episode总时间；GPU6 H100，不启用人工GPU负载。固定相同Local checkpoint、同真实K16/source64输入和样本RNG；各模式暖机4次+30正式测量，逐次检查Action/Vision严格一致；没有预设加速目标。

| 独立进程测试 | GPU P50 | GPU P95 |
|---|---:|---:|
| 上一正式 Child `4be3`，projection无此优化 | **689.606ms** | 696.473ms |
| 新Child `d5c1` projection **OFF** | 705.139ms | 713.713ms |
| 新Child `d5c1` projection **ON**，首次30次 | **892.868ms** | 902.541ms |

**必须保留性能异常**：新ON首次30次前22次多在890–900ms，第23次过渡，后7次降至约647–665ms，出现明显的非平稳时延。不能挑后段快速结果宣称全部运行加速，亦不能将首次P50恶化隐藏。

为了复验，GPT在**新独立进程**继续采集 projection ON 50次正式生成：P50 **678.945ms**、P95 **690.409ms**、max **1295.667ms**（长尾保留）。每次Dynamo计数器显示 `unique_graphs=8` 且统计不变，未发现测量过程中的Dynamo重编译，因此不能把时延跳变直接归因于Dynamo重编译；原因仍未知。

**最强单变量性能证据：同一新Child、同一加载模型进程、K16/source64、projection ON/OFF交错30轮（先各暖机4次）**：

| 同进程交错 | projection OFF | projection ON |
|---|---:|---:|
| GPU P50 | **695.998ms** | **664.873ms** |
| GPU mean | 698.140ms | 669.230ms |
| GPU P95 | 705.954ms | 671.668ms |

29/30轮 ON 更快；**逐配对节省时间P50 = 33.853ms**、mean = 28.910ms；有一次ON约786.23ms的较慢样本未剔除。该受控配对证明新投影缓存存在真实生成加速收益，但**不证明首次启动及生产P99稳定性**。Eager子表达式的“可回收约120ms”只是上轮微基准，不可拿来代替此处实际整模型收益。

## 5. 新旧 blocker 与正式限域结论

- `K16_REAL_BF16_STRICT_PARITY`：**CLOSED**，4条模型路径raw15/Action/Vision全exact、3条对照30/30步Velocity exact。
- `K16_REQUEST_BOUND_PROJECTION_CACHE_ACTUALLY_ELIGIBLE`：**CLOSED**，ON记录31次有效binding、OFF为0。缓存复用不跨Session/请求的CPU/finally contract由314 scoped tests覆盖。
- `STEADY_INTERLEAVED_NATIVE_GENERATION_BENEFIT`：**MEASURED**，配对P50节省33.85ms、29/30轮ON更快；无阈值拔高。
- `COLD_START_AND_LONG_TAIL_LATENCY_STABILITY`：**OPEN**。首次ON/重跑ON存在显著跨进程差异，偶发≥1.2s长尾，未找到根因；本次不批准生产 P99、启动性能/整套推理路径达到NoTTT速度。

**正式实现 Verdict：`APPROVE_CODE`，只限固定 `1b184204/d5c1ffc7` 的请求内Prefix K/V投影复用代码及 scoped CPU/K16数值证据。** 新发现的性能非平稳风险需作为独立性能Gate继续调查；本批准**不等于**允许合并 V3、Stage3全部完成、在线RoboCasa任务SR有效、B>1/CFG GPU生产、Global Memory或NoTTT同权重比较。不得因为代码数值PASS提前宣布整体性能完成。

## 6. 私有证据位置和身份

所有原始真实请求、模型权重、Action/Vision/Velocity输出及性能原始记录只在授权服务器，未向GitHub上传：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_gpt_independent_gates_20261104/issue35_prefix_projection_independent_20261110/`。

内含 `cpu_scoped01/gate.json`、`gpu_k16/result.json`、`gpu_k16/velocity_steps_K16.pt`、`perf_old/result.json`、`perf_new_on/result.json`、`perf_new_off/result.json`、`dynamo_repeat/result.json`、`paired_k16/result.json` 与独立回读审计 `independent_final_audit.json`，**审计文件SHA256：`e6e61f94426cc4420a8919b89c0d7dd182302815f2ee6b498122665bd8527d4e`**。实施 pair tracked clean、GPU4–7 0MiB、相关owned进程清理。Review/Inbox文档写入不改变Formal Pair。