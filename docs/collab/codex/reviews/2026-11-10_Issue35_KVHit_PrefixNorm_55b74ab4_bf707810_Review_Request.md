# Issue35：真实请求 Text-KV 首次命中数值差异最小修复审核申请

日期：2026-11-10（Asia/Shanghai）。Codex 为实现与作者证据方；申请 GPT 独立窄增量审核。**作者结果为 CPU PASS + 两组冻结真实请求 H100 严格回放 PASS；尚无此新配对的独立 APPROVE_CODE，不授权合并 V3。**

| 对象 | 精确 SHA |
| --- | --- |
| 新 Formal Root | `55b74ab461fda27e4ff6490023c828db0abc0a9f` |
| 新 Child / Gitlink | `bf707810f573e885f0966d65c232dc2a610d6a93` |
| Root 直接父提交（含最新 GPT 真实回放报告） | `796e28a7f36c1c06a323db153b207b60b6f69d7f` |
| 原实现 Root | `18be4a80a5ae4d97bc7d287034d24efab847c496` |
| Child 直接父提交 / 原实现 Child | `193627f42f4cd1ba6d563aefb8fa8f9428ecb56d` |

两仓隔离分支：`v3-local-prefix-kv-parity-issue35-20261110`。后续 docs/evidence 提交只是账本，不替代以上 Formal Pair。Root 实现提交只更新 Gitlink、SESSION、TODO；Child 为 3 个生产文件与 1 个回归测试文件，227 additions / 8 deletions。

## 真实首差异的作者定位

继续使用 GPT 已冻结的 K1/source32 与 K16/source64 完整真实请求，不再次启动 RoboCasa、No-TTT 或性能实验。所有定位先在原 clean `18be4a80 / 193627f4` 上完成。

1. 非侵入性校验：强制每步走原生完整计算并捕获 KV 的诊断，其最终 Action/Vision/raw15 与 GPT 原始 KV-OFF 回放相同；另两条路径也分别复现 GPT 保存的 Stage1/Stage2 输出。
2. 所有 28 层的 UND K/V 在 step0/1 静态不变，缓存读值与同一步原生值逐元素相同。第一处 GEN 层输出差异在 denoise step1：K1 为零基 layer18，K16 为 layer16；进入这些层的 GEN 输入相同。
3. 对以上四个真实层调用（两种 K × full/hit）追加已物化的 GEN Flash operands 作为诊断输出；四次层输出 SHA 与完整生成逐一相同，并再次复现 K1 三种最终输出。无扰动校验通过后才采用中间张量证据。
4. Q 与 V 相同；K 仅 Prefix 的 4 行中 **1 个 BF16 元素**不同，max_abs=`0.00390625`。UND132、GEN267、padding2 行均相同；对应 Attention 输出 max_abs 为 K1 `0.0001220703125`、K16 `0.000244140625`。
5. Prefix 投影输入、可观察的 BF16 投影输出、RMSNorm 权重均相同，GPU eager normalization 的双路径结果也相同；首次不同值位于 **compiled Prefix K normalization**。实际归一化为 `Nemotron3DenseVLRMSNorm`、epsilon=`1e-5`，full/hit 生成的融合图不同。尚未把差异进一步归因于某条 FMA 或归约指令，不做该层面的断言。

因此，旧回放中的差异有直接编译数值路径依据；无需把 UND 缓存内容、Stage2 Pack 或后续仿真轨迹当作已证实原因。完整派生表和原始证据哈希见下方 evidence。

## 最小生产改动

- `attention.py`：在现有 B1 Prefix-aware cache-fill 中，返回明确标记的四 Tensor tuple `_PrefixTextKVToStore`，包含 Prefix K 投影输入、实际原生 GEN K buffer 中的 Prefix 归一化结果和原有 UND K/V。其他 MemoryState 的 GEN/UND tuple 不变。
- `inference_text_kv_memory.py`：以上输入/输出以 detach + clone 保存在**本请求、本层**的缓存中，clear 时同时释放。命中时仍计算当前 Prefix K/V；只有当前投影输入与保存值**全部精确相同**，才用 GPU `torch.where` 选取原生首次归一化结果。输入变化时使用当前归一化值，V 始终为当前值。缺失或形状、dtype、device、B1 身份不匹配继续 fail-closed。
- `unified_mot.py`：仅向已显式启用 Prefix-aware inference memory 的 dispatcher 传入未归一化的当前 Prefix K 投影（+2 行）。
- `prefix_text_kv_memory_test.py`：确定性控制归一化舍入差异、当前 Prefix 改变/恢复、缓存 clone/clear、损坏引用拒绝、dynamic/fullgraph 当前 Prefix 验证。

这依赖与原 Text-KV 缓存相同的前提：单次生成请求内慢权重冻结。没有按容差比较，没有将 Prefix 忽略或固定为跨请求状态，没有跨 Session 缓存，没有改变训练/TTT 算法、全局精度、Attention kernel、编译上限、调度/Resume 或 VAE。

## CPU 证据

| 验证 | 实际结果 |
| --- | --- |
| 原 Child1936 + 新确定性主回归 | RED，1 FAIL、25 deselected，Shell1 |
| 新实现同一主回归 | GREEN，1 PASS、25 deselected，Shell0 |
| exact clean 新 Formal Pair 原 201 项 + 12 项新增 | **213 PASS，0 FAIL/ERROR/SKIP**，Shell0 |
| 历史 W0 失败 | 1 deselected，单独记录，未计为 PASS |
| Ruff / format / AST / 原 benchmark help | PASS；保留原先 3 个 I001 例外 |
| 1,487 项生产/配置/脚本指纹与 clean identity | 前后一致 |

主回归用 BF16 TinyMoT 控制 Prefix normalization 发生一个 ULP 的执行差异。旧代码在 cache-hit 的严格断言处失败，31/96 个合成 GEN 输出元素不同，max_abs=`0.0078125`；新实现同时通过原 Prefix、改变 Prefix 和恢复原 Prefix 三段断言。这个合成负例不冒充真实模型“仅一个 Prefix K 元素变化”的统计。

受控 RED 只有测试文件被临时增加，不能称为 clean Formal Gate；保存了原生产三文件 SHA、新旧相同测试函数的 AST 绑定、当时完整 fixture、原始 JUnit/traceback。最终 213 项才是在已提交 clean Pair 上执行。

CPU 命令：

```bash
cd /workspace/work/psm-wma-attention-issue35
/workspace/.venvs/psm-wma-cpu/bin/python \
  docs/collab/codex/evidence/2026-11-09_issue31_prefix_pack/cpu/cpu_gate.py \
  --root "$PWD" \
  --run /workspace/work/issue35-kv-parity-evidence/author01 \
  --expected-root 55b74ab461fda27e4ff6490023c828db0abc0a9f \
  --expected-child bf707810f573e885f0966d65c232dc2a610d6a93
```

## H100 真实冻结输入严格回放

GPU6 H100，原生 `ActionModelService` + iter15000 Local-TTT DCP + `validate_model_mode(required, use_ema_weights=False)`，真实 15D Action、H16、B1、guidance1、30-step UniPC。PyTorch `2.10.0+cu128` / CUDA12.8，28 层实际为 `OptimizedModule`，`recompile_limit=8` 保持不变。

每条路径重新从 native `torch.save` 恢复完整 request、prepared（包括已冻结 VAE 输出、初始噪声与掩码）、前后 FastRecord、Prefix、Torch CPU/CUDA + NumPy + Python RNG，保留混合设备、stride、alias。没有重新运行 VAE 来替换原输入。三条路径均为 **Local-TTT Prefix ON**：原始 Local KV-OFF/Pack-OFF，Stage1 KV-ON/Pack-OFF，Stage2 KV-ON/Pack-ON。

| 验证 | K1/source32 | K16/source64 |
| --- | --- | --- |
| 新原始 Local 对 GPT 保存的旧原始 Local | Action/Vision/raw15 exact0 | Action/Vision/raw15 exact0 |
| 新 Stage1 对旧原始 Local | Action/Vision/raw15 exact0 | Action/Vision/raw15 exact0 |
| 新 Stage2 对旧原始 Local | Action/Vision/raw15 exact0 | Action/Vision/raw15 exact0 |
| Stage1 对 Stage2 | exact0 | exact0 |
| observer 对无包装生成（3 路径） | exact0 | exact0 |
| Stage1 全部 30 步速度对原始 Local | 30/30 exact0 | 30/30 exact0 |
| Stage2 全部 30 步速度对原始 Local | 30/30 exact0 | 30/30 exact0 |

`author_h10002`: **gate.status=PASS、Shell exit0、source_unchanged=true、protected_inputs_unchanged=true**。1,487 项源码指纹、checkpoint config/DCP metadata、冻结 request/prepared/output、独立旧回放输出哈希均检查。所有路径 FastState/Prefix 输入未变，dispatcher 按原生 finally 恢复。

`source32` 表示已执行 32 个动作后的当前观测（H16 下第 3 次 Replan）；K16/source64 为第 5 次 Replan。两种 K 的请求互不作为对方的模型基线，每个请求只比较其自身的三条路径。

此前 `author_h10001` **FAIL / Shell1** 完整保留：K1 三路径及全 30 步已通过，随后 K16 的回放夹具直接读取未显式提供的 `local_ttt_history_k` 而 KeyError；尚未执行 K16 模型。按已有“缺省 K=H”规则修正外部夹具后，使用相同生产 Pair 在新输出目录执行完整 `author_h10002`。没有为此修改生产代码或将失败改写为通过。

另保留 probe01/02 的输出目录夹具失败、operands01–03 的 Flash 目标识别/关键字参数/observer instrumentation 不完整记录。这些均不计为生产 Gate PASS；operands04/05 的无扰动与完整性核对才是采用的定位依据。

## 证据、资源与审核范围

- [作者 evidence 入口](../evidence/2026-11-10_issue35_kv_hit_parity/README.md)：CPU 原始 JUnit/log/command、受控 RED fixture/provenance、作者 probe 源码、H100 精确命令和**派生标量/哈希**。
- 服务器私有根：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/_codex_issue35_kv_hit_parity_20261110/`。本轮实际模型只在 GPU6；初始发现其他任务占用后未动它们，Owner 明确告知已停止，重新确认空闲才启动。
- 最终 GPU4–7 均0MiB，GPU6 compute PID为空；原 `root2` 仍 clean18be/1936，新候选服务器工作树仍 clean55b/bf707。无 GPU0–3 / 训练 / L2000 操作。
- 私有 844 文件索引 `private_evidence_index01.json` SHA256=`1833504e303cedcfd87a065e921845afb36c1ebbc5d5c68c260f715ce656d623`。原张量、图像、模型、运行日志、编译 FX/generated code **没有外传**。
- 新完整 H100 `gate.json` SHA256=`94bacad2a7c2b1fafabe3d94763464028615fa71cce05ac6a5009e7e2fe6eb28`。
- 历史 GPT 原始回放失败报告、其 scoped APPROVE_CODE 与原失败证据继续保留；作者的新结果不替代独立审核。仅两个已冻结真实请求，尚不能推出所有输入、实际 SR、性能或 P99 改善结论。本轮没有重跑 No-TTT、Sim、SR、900EP，也没有继续第三项 Attention 性能优化。

申请只审核本次数值修复、回归和两个真实输入的作者证据，之后由 GPT 决定独立复核与后续步骤。所有上游 Draft 保持未合并；不自动合并 V3。
