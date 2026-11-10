# Issue35 — B1 Prefix K/V 组装最小优化：代码与 CPU Evidence 审核申请

2026-11-10（Asia/Shanghai）。Codex 实现、静态与作者 CPU 证据；GPT 独立审核和后续真实 H100 验收。**新候选 CPU PASS，真实 H100 数值与性能尚未执行，当前没有新配对的独立 APPROVE_CODE，不授权合并 V3。**

| 对象 | 完整 SHA |
| --- | --- |
| 新 Formal Root | `39f60da729a49c9f6514953bf801dcafb7493039` |
| 新 Child / Gitlink | `4be3d702f3008040b830ae09c200d80e273a201a` |
| Root 直接父提交（最新批准及性能交接） | `f9762003e164a013df13c258ee0ab925fcdc8740` |
| Child 直接父提交 | `bf707810f573e885f0966d65c232dc2a610d6a93` |
| 上一已批准 implementation Root | `55b74ab461fda27e4ff6490023c828db0abc0a9f` |

两仓新隔离分支：`v3-local-prefix-b1-assembly-issue35-20261110`。后续证据、Inbox、review 文档提交是账本，不替代上表 Formal Pair。原 RootPR36/ChildPR12 及上游候选保留。

## 已消费的正式审核与实施边界

同步 before Root5658adab → advertised/tracking f9762003，输出6个新提交、ancestor0并完成ff-only。已读取：

- `2026-11-10_Issue35_55b74ab4_bf707810_KVHit_NumericParity_APPROVE_CODE.md`：上一数值阻断已独立关闭；37+213独立CPU及两K真实三路径/30步严格数值通过，不重复其 Code Gate。
- `2026-11-10_Issue35_PostKVNorm_NativeGeneration_Performance_EVIDENCE.md`。
- `2026-11-10_Issue35_B1_Prefix_KV_Assembly_Performance_RootCause_EVIDENCE.md` 及 [Issue35 精确执行交接](https://github.com/wxwy/psm_wma/issues/35#issuecomment-6759358339)。

GPT 的同 Local checkpoint/真实输入诊断和 profiler 将一项直接可优化的重复工作定位在 `prepend_memory_kv` 的 B1 通用多样本扫描与 scatter。**不能把约271–276ms差距全部归因于这些操作，也不能把运行途中时延档位变化直接归因于 Memory。** 本次没有改变 Memory 的注入位置或方式，没有恢复/停止 `tmux gpu` 或其他工作负载，没有服务器访问或新的 No-TTT 实验。

## 生产增量：一个函数内新增24行

Child 只变更 `cosmos_framework/model/generator/mot/memory_prefix.py` 和其已有 `memory_prefix_test.py`；总205 additions / 0 deletions，其中生产24行、测试181行。Root implementation 仅 Gitlink、SESSION、TODO。

`prepend_memory_kv()` 在原有 K/V shape 检查后增加 B1 **推理**快路径，条件完全由已有静态元数据决定：

- 梯度关闭，Prefix offsets 为一个样本（长度2），Native offsets 为一个样本或一个样本加末尾 padding（长度2或3）。
- Offset 一维，dtype 为原生 int32/int64；完整正长度 Prefix 的行数等于 `k_local`，不写死4。
- 对应 K/V dtype 不发生提升，设备与原生 metadata 一致。

对已有合法、从0开始的原生 offsets，组装等价于：

```python
key = torch.cat((memory_k, native_k))
value = torch.cat((memory_v, native_v))
offsets = torch.cat((native_offsets[:1], native_offsets[1:] + k_local))
max_len = max_native_len + k_local
```

保持 `[Prefix, Native, optional Padding]` 的字节值与排列，padding 仍是独立段；返回 dtype、stride、query offsets 及 max_len 合同不变。没有数据依赖的 host `.item()`、`.tolist()` 或同步，没有新配置开关、缓存或生命周期状态。

所有不符合条件的输入继续原通用代码；梯度开启时也继续原训练路径。**原通用尾部逐字节相同；移除新增快分支后整个生产模块 AST 与 parentbf707 完全一致**。Prefix 的构建、投影与归一化、已批准的 normalization memo、每层当前 K/V、Mask、Varlen/Flash 后端、FW、训练算式、Session、Resume、M/B 一致性均未修改。NoPrefix 原 Action Path 仍不调用此函数。

## 确定性 RED/GREEN 与 CPU Gate

旧 parentbf707 的生产文件 SHA256=`9fe19353053b246976e859d13d370fca3f1d9add88827da683bc40a56383082c`；仅测试文件增加后运行受控 RED。它是旧生产代码+测试新增的实验，**不是 clean Formal Gate**。

| 检查 | 实际结果 |
| --- | --- |
| 旧生产 B1 操作预算回归 | RED，1 FAIL，Shell1；断言处实际 `cumsum=1 / repeat_interleave=2 / index_copy=4` |
| 新实现整个 memory_prefix_test.py | 101/101 PASS，0失败/错误/跳过；包含同一个预算回归 |
| 新旧回归测试文件 | byte-identical，SHA256=`31b363bad88a8db3b894a314abcbc3198212fca74ce1e299ffc514f0f737a4b9` |
| 新 exact clean Formal Pair 完整既有 scoped Gate | **292/292 PASS**（原213+新增79），0失败/错误/跳过、Shell0 |
| 历史 W0 assertion | 1项明确 deselected，未计为PASS；没有扩大排除范围 |
| 静态检查 | 既有9文件加新增2文件，**11文件 PASS**；仅既有3个I001例外，新两文件无例外 |
| 源码身份 | clean Root/Child/Gitlink匹配，1,487项指纹前后相同 |

新增79项包括：

- 60组布局：Native长度1/32/132/267/400 × pad0/2/8 × FP32/BF16 × offsets int32/int64，使用非连续源视图，对原通用路径逐元素比较 K/V/offsets/max_len，检查输入未变。
- B1 预算断言：上述三个扫描/scatter操作均不出现；CPU eager 的操作级证据，不冒充 H100 Kernel 统计或毫秒收益。
- Prefix长度1/4/8，当前K/V改变与恢复；末尾padding与Native值不受Prefix变化影响。
- 多样本、混合有/无Prefix、padding、空Prefix继续原通用扫描；梯度开启的B1继续原通用路径，K/V梯度正确；不兼容dtype、device、shape、样本数仍拒绝。
- dynamic=False/True、两种Offset dtype 的 fullgraph 编译，变化Native长度与padding，保持精确布局且图中无三类操作。此项用CPU backend，不替代H100 Inductor/BF16整模型Gate。

既有 scoped Gate 继续覆盖 Prefix-aware 30步生成、首填充/命中/改变Prefix/回退、NoPrefix/NoTTT、异常finally清理、重试、Session隔离及现有history-K/事务测试。**101聚焦与292完整有重叠，不相加为393。**

精确完整作者命令：

```bash
cd /workspace/work/psm-wma-attention-issue35
/workspace/.venvs/psm-wma-cpu/bin/python \
  /workspace/work/issue35-b1-assembly-evidence/cpu_gate.py \
  --root "$PWD" \
  --out /workspace/work/issue35-b1-assembly-evidence/author01 \
  --expected-root 39f60da729a49c9f6514953bf801dcafb7493039 \
  --expected-child 4be3d702f3008040b830ae09c200d80e273a201a \
  --expected-tests 292
```

包装脚本不修改既有 Gate 入口，实际调用 parent 已有 `docs/collab/codex/evidence/2026-11-09_issue31_prefix_pack/cpu/cpu_gate.py`（SHA256=`b90b71cb41aad3c48b4d81301b61bd872e342aaeba8ccf05acf99a299de0fd1e`），加两新文件严格 Ruff/format/AST 和身份核对。CPU/offline环境、命令、返回码、JUnit、原始日志、前后指纹都保存于 [Evidence目录](../evidence/2026-11-10_issue35_b1_assembly/README.md)。

## 后续独立 H100 Gate：当前全部待执行

由GPT在代码审核通过后按已有原生服务与冻结真实输入入口独立执行。Codex本轮没有启动GPU、远程推理、RoboCasa、NoTTT、SR或900EP，也没有触碰训练及运行任务。

1. 在新的精确clean39f60da7/4be3d702工作树，保留 `verify_source()`、required Local checkpoint/DCP/设备校验、BF16和recompile_limit8。使用原 iter15000、B1/H16/raw15、guidance1、30-step UniPC。
2. 恢复服务器已有 K1/source32 和 K16/source64 完整请求、prepared、FastState/Prefix及四种RNG；每条路径重新加载输入。比较原Local KVoff/Packoff、KVon/Packoff、KVon/Packon，要求对已批准原始Local基线的 Action/Vision/raw15 **全部exact0**，每种K两缓存路径的30/30步velocity也exact0，诊断不能扰动最终输出。新的cat可能改变Inductor融合，CPU布局PASS不能推导此结果；任一差异保留首错，先停性能结论。
3. 数值通过后，比较上一55b74ab4/bf707810与新39f60da7/4be3d702的同checkpoint/同真实输入/同Prefix/KV+Pack路径，保持原生生成含当前帧VAE的既有计时口径，预先固定暖机与交错配对轮数，记录mean/P50/P95/P99、全部离群值和外部负载存在性。若使用冻结prepared跳过VAE，须单独标注计时口径。**没有加速比例硬门槛，不刷NoTTT，不擅自管理负载任务。**
4. 可另抓同输入前后Profiler，核对repeat/cumsum/CUB Scan及总Kernel的实际变化，保持Flash/Varlen语义；Profiler时间不替代正常生成P50，CPU inclusive与GPU时间不相加作精确收益。

本次请求只做这24行组装快路径与CPU证据的窄增量审核，随后推进以上真实数值/性能验收。当前性能Evidence保持 **PENDING**，不能宣称已回收271–276ms、关闭P99或Issue35全部性能工作。所有旧正式批准和原始失败记录保持归档，不自动合并V3或改动上游Draft。
