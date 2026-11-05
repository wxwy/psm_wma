# Codex 实现任务：R05 真机仿真验证发现的 VFM `_decode_action` 动态编译缓存溢出

**Owner 指示**：代码修改全部由 Codex 执行；GPT 只负责审核、CPU/GPU/真实 RoboCasa 独立验证。日期 2026-11-05。

## 0. 本次 Formal 基线、隔离开发边界

- Root 仓：`wxwy/psm_wma`，**本轮起始实现** `c9fa60b7134fda8fb848c29c148f25c7a8901892`。
- Child 仓：`wxwy/cosmos-framework`，**本轮起始实现** `4e9c8104ffd15a373b576bc35ee608de1b60eea1`，Root Gitlink 对应同 SHA。
- Root/Child 新开发分支均已建立：`v3-r05-action-decode-compile-20261105`，须实际从上述 Base SHA 开始，先检查 `origin/V3` 最新状态。
- **不要把 docs-only/issue/ledger SHA 当成 Formal implementation pair。** 候选完成后报告新的精确 Root commit + Child commit/Gitlink。
- 本次**独立的窄修复**基于已批准的 Action **encode** 编译修复；它不含 Issue #17 的 Streaming M32/B32 实现。用于发现问题的隔离本地组合 Root `421a87c3915d48ed45c64cac7e4852598fa58866` / Child `b44ae7d2bf4bf5a6d894e8a3ca9232e3295c8954` 是 **R05 临时集成来源，不是当前GitHub正式起始Pair**。后续GPT在独立隔离工作树整合，再做实际RoboCasa Canary。
- 任何情况下不动正式 V3、R04旧运行目录（648条有效EP）或R05这次失败运行目录（12条有效EP）；不重写模型权重、checkpoint、G2或后台任务。

## 1. 真实故障证据（与历史 encode 故障明确区分）

GPT于2026-11-05启动 **R05真实RoboCasa**：原 `iter_000027700` 权重，8个model DCP shard + `.metadata` 对旧R04记录逐字节SHA256匹配；训练 `config.yaml` SHA256匹配；18 Atomic Tasks × 2 Episodes，Phase B、M16/B8（32个物理Sim槽）、GPU4/5 EGL、GPU6/7 Policy、`local_memory_mode=required`，`raw action=[16,15]`，不保存媒体。

真实运行中：
- 12/36 Core已有效提交（12 success），可见原生`[16,15]`动作、Local-TTT fast-state/inner-loss字段及Native Batch1–6，证明真实Sim→Policy→执行→commit链路通；
- 之后24个EP因协调器被迫停止而Invalid，`R05_FRESH_EXIT=1`，无合格36EP SR；
- GPU6 Server于11-05 03:02:32 UTC 输出：
  ```text
  [5/8] torch._dynamo hit config.recompile_limit (8)
  function: '_decode_action' (cosmos3_vfm_network.py:1249)
  last reason: len(packed_seq.action.tokens) == 5
  torch._dynamo.exc.FailOnRecompileLimitHit:
      recompile_limit reached with fullgraph=True
  ```
  `robocasa_batch_transactions.py: _execute_many` 的 GENERATING 阶段返回HTTP 409；上游Sim收到FATAL；Run停止、旧结果保持。此处**不是**已改的`_encode_action`。
- 现场路径（仅便于有权限者只读核验）：`/mnt/data1/data_v2_0617/robocasa_eval_runs/local_ttt_robocasa_raw15/packed128_droid_fresh_g1_20261019/GPT_R05_M16B8_iter27700_real18x2_verified_20261105/logs/GPU6_server.log`。若Codex无服务器权限，可直接以上述文字和GitHub源码为任务输入；**不得声称自己已回读现场文件**。
- 原始`_encode_action`列表导致的上一故障已由Child `4e9c8104` 将Tensor投影提取至`_project_action_tokens`并编译解决，已有CPU51/51及GPT真实H100定向验证。勿回退。

## 2. 目标与约束（由Codex设计最小补丁、实现）

**唯一目标**：让真实动态B1–8切换不再因`_decode_action`的Python列表/元数据结构变化，耗尽Dynamo默认8图重编译额度。

实际源码：
- `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`：`_decode_action`含`has_noisy_tokens(action)`、`action.noisy_frame_indexes` / `action.domain_id` / `token_shapes`列表迭代、`_select_action_domain_ids`、`unpack_action`及对`output_dict`的就地写入；noisy分支核心Tensor算子为`self.llm2action(action_hidden_states, per_token_domain_id)`。
- `cosmos_framework/model/generator/mot/parallelize_vfm_network.py`：当前将**整个`model._decode_action`**送进`torch.compile(fullgraph=True,dynamic=...)`，因此列表长度Guard虽动态Tensor仍会按B变化。
- **建议方向而非代写代码**：保留`_decode_action`作为eager元数据编排（提取noisy-token、domain-id映射、unpack及回写），仅将真正计算密集的Tensor Projection隔离为一个受既有`compile_options`管理的Tensor-only helper。由Codex自行确认最佳函数边界，不增加模型Parameter/Module，不改权重键和外部输入输出。
- 无noisy Action分支的**dummy计算图**要保持与原实现相同的`action2llm`、可选modality embed、`llm2action`顺序，以及`0 * preds_action.sum()`对梯度连接的语义；不能误改成detach/纯zero后让参数失去grad。
- 对真实Action noisy分支，保持`last_hidden_state[action.mse_loss_indexes]`与Domain ID关联、输出顺序、dtype/autocast、`unpack_action`的clean-zero/noisy scatter、形状和浮点语义。
- `compile_options`语义、`fullgraph`与`dynamic`作用范围、原来其他四个VFM heads以及既有`_project_action_tokens`必须正确保留；尤其`use_cuda_graphs/cuda_graph_scope='forward'`原有静态scope不得偷换。
- 不提高默认`recompile_limit=8`，不通过吞掉`FailOnRecompileLimitHit`假装成功；不全局关闭compile/降低B上限；**不改Issue17 Streaming Scheduler/Store、Session/Local-TTT/Media、EGL、Checkpoint/Manifest/Resume**，不修改数据/训练路径。
- 旧`parallelize_vfm_network_test.py`中编译目标名可随必要改动调整，但旧scope/option断言不得放宽/删改。
- 若纯Tensor helper仍被data-dependent dtype/list guard影响，应先以真实`TORCH_LOGS=recompiles`定位，不盲目增加缓存上限或扩大重构范围。

## 3. Codex 必须提交的 CPU Evidence

1. **旧版 RED / 新版 GREEN（同一测试文件字节）**：用实际`Cosmos3VFMNetwork`及真实`apply_compile`触发旧`_decode_action`的同类`len(packed_seq.action.tokens)`重编译失败；新的窄修复在默认limit8下不再触发。
2. 动态`B1–8`反复切换至少1024次/组；包含`noisy/clean`、ragged token长度、scalar/framewise Domain ID、多任务样式、local_memory_enabled on/off、FP32/BF16；记录真实Graph/重编译次数，并证明**连续序列中没有偷偷reset cache**。
3. **数学/梯度匹配**：旧eager vs 新eager（尽量bit-exact），新compiled vs eager（FP32/BF16按明确容差）；检查输入梯度和完整参数梯度，包含dummy no-noisy分支的Action DomainAwareLinear/embedding梯度连接；state_dict keys/parameter identities保持不变。不能只对比`output_dict` key集合。
4. 保留旧VFM heads与`parallelize_vfm_network_test.py`scope回归；适当覆盖`torch.compile`的CPU Inductor以及不支持的输入校验fail-closed。
5. 针对真实线上BF16/CUDA `grouped_mm`路径的GPU验收规划必须使用**真实15D Raw Action、H16、DCP模型与真实推理**。此前5D synthetic会触发对齐失败，改16D synthetic仅能作单元证据，不能冒充真实RoboCasa验收。
6. 作者必须交出原始JUnit/log、环境、可复跑命令、RED失败详情、GREEN统计、静态Ruff/format/AST、前后源码指纹和`source_unchanged`；明确报告哪些GPU/FSDP/CUDA graph尚未运行；独立GPU由GPT在后续Code Gate批准后执行，勿未经授权直接启动真实评测。

## 4. 最小交付/流程

- Codex在**两个隔离候选分支**实现并push；Root仅更新对新Child的Gitlink（和必要测试/交接文档），Child仅修改上面两条实现路径和相应测试，其他生产路径尽量零改动。
- 新Formal Root/Child SHA固定后作者先做针对性CPU测试与源码静态检查，提交独立`docs/collab/codex/reviews/`作者交接、原始证据、变更diff。
- GPT根据新Formal Pair做**独立增量Code Gate**；未审核前不merge V3，不要求DS，禁止改R04/R05旧目录。
- 通过后GPT再将它与Issue17 `551b0362/82fa270e`集成成**新的正式集成Pair**，以新Fresh Run验证真实Checkpoint/真实15D动作、B1–8切换、Torch compile稳定性和吞吐，并根据当前已观察到的Policy排队数据决定M16/B8是否足够，无需盲测M32/B8。
- **M/B Resume严格一致性限制绝不变更。** 原R04（648Core）和本R05（12Core）的冻结Root/Child/Gitlink身份与新源码不一致：**不得普通Resume复用旧结果**；新源码只能使用合规独立新Run或后续另行批准的明确迁移协议。

**最终目的：** 尽可能少改一处编译边界，关闭实际R05`_decode_action`Dynamo重编译问题，同时不牺牲Action数值/梯度/Local-TTT科学语义或真实GPU吞吐。
