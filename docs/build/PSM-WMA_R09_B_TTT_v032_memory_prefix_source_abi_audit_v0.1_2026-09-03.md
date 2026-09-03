# PSM-WMA R09-B TTT v0.3.2 Memory Prefix source/ABI 审计设计 v0.1

**日期**：2026-09-03  
**状态**：C3 docs-only/static audit，待三方审核  
**当前 C3 remediation/design SHA**：由本文件之后的 Inbox/request ledger 明确绑定；本文件不自嵌会随提交变化的 SHA。
**原始、已 superseded 的 C3 初始设计提交**：`26bd78d4f3feb9659c63459393c61780bc0b94e7`
**设计前/source 根仓基线**：`2a08f4e37ddfa98038b35965fb4b9f79c1b90806`
**子模块基线**：`1d90361aeb21db53129ac27ddcaa1285b258fbbc`（仅作为只读 source baseline）

## 1. 目的与边界

本文件把 v0.3.2 的 Local Memory Prefix 合同映射到当前 Cosmos source，区分已观测事实、尚未实现的 ABI 缺口和下一 Gate 的验收条件。仅允许只读检索、静态断言和文档提交；不修改 `cosmos-framework`，不改 runtime/attention/config/optimizer/checkpoint，不访问模型或数据，不运行 torch/GPU/torchrun，不执行 staging、P4/P5 或训练。

算法权威仍为 `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`：每步一组 K/V 写入，更新后用 `K_local` 组 Q 读取，输出 `[B,K_local,32]`，经 `32 -> 2048` 后进入 K/V-only Memory Prefix；无 `Q_MEM`，AR 不读 Memory，DM 读 `MEM+AR+DM`。

## 2. 当前 source 事实

### 2.1 Local feature projection 与参数

在 `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py:226-228`，`local_memory_enabled` 时创建 `local_memory2llm = nn.Linear(config.local_memory_dim, hidden_size, bias=enable_input_bias)` 与 `local_memory_modality_embed`。`283-290` 对两者执行零初始化。该入口能表达 `K_local` 行 token，但没有声明 Memory Prefix 的独立 K/V 投影或 Prefix 专用 LayerNorm。

### 2.2 当前 Local 注入语义

`cosmos3_vfm_network.py:941-962` 的 `_encode_local_memory()` 将 `PackedSequence.local_memory.tokens` 拼接、检查最后维度等于 `config.local_memory_dim`，投影到 `hidden_size` 后直接写入 `packed_sequence[local_memory.sequence_indexes]`。`1056` 调用该函数，`1077-1078` 将 Local index 加入 `all_gen_indexes`。这是现有普通 GEN-stream 注入路径，不等价于 v0.3.2 所要求的 K/V-only Memory Prefix；在 runtime 接线 Gate 前不得把它当作已实现证据。

### 2.3 attention pack 入口

`cosmos3_vfm_network.py:1119-1144` 调用 `build_packed_sequence()`，并传入 `config.joint_attn_implementation`、UND/GEN index、split/sample lengths。`attention.py:691-780` 当前只接受 `two_way` 或 `three_way`；`attention.py:179-217` 的 `two_way_attention()` 对 GEN 做 full attention、对 UND 做 causal attention。此处尚未观察到 Local Prefix 的独立 K/V stream、Memory pre-attention norm owner 或 AR-memory-blind 的专用 mask ABI。

### 2.4 Local history 到现有 ABI 的边界

`cosmos_framework/model/generator/omni_mot_model.py:941-1019` 将 runtime history 结果写入 `data_batch["local_memory"]`；`cosmos_framework/model/generator/omni_mot_model.py:4212-4238` 将其整理为 `x0_tokens_local_memory`。这证明输入载荷可沿现有 batch/pack 路径传递，但没有证明 persistent fast state、K/V cache 或每 timestep 的更新后 readout 已接入 Cosmos。

### 2.5 Packer cardinality 与当前 runtime cardinality

在子模块 `1d90361` 的 `cosmos_framework/data/generator/sequence_packing/sequence.py:545-588`，`pack_local_memory_tokens()` 已接受每个样本形如 `[K_local,D_local]` 的载荷，按 K 行写入 Local GEN 区域，并使用当前 Local GEN 路径的 text-style mRoPE；该函数不推进 native position cursor。该能力只说明 packer 可容纳多行，不说明生产 runtime 已完成 v0.3.2 multi-slot fast-state/readout 接线。

相反，`cosmos_framework/model/generator/mot/local_evidence.py:616-663` 的 `LocalHistoryRuntime.forward()` 当前仍返回三元组，其中 token 载荷为 `[B,1,D]` 形态的单行兼容结果；该 shape 由同文件 `StatelessLocalReplayReadout`（定义于 `:110`）及其调用路径决定。目标 Memory Prefix 必须在后续 Gate 明确 `K_local` 行的生产来源，并禁止无审计地继承当前 GEN-path 的 RoPE/position 策略。

## 3. C3 必须冻结的 source/ABI 问题

下一 Gate 的设计必须逐项给出 owner、输入输出 shape、失败行为和测试证据：

1. **Prefix owner**：Local token 是否在进入 transformer 前由独立 Memory Prefix 模块产生 K_MEM/V_MEM；禁止继续把 Local 当作 GEN query/output。
2. **Norm/projection**：明确 `[B,K_local,2048]` 的唯一 pre-attention LayerNorm、K/V projection、dtype/device 与参数归属；不得复用未声明的 ordinary GEN norm。
3. **Packed layout**：冻结 `[MEM,AR,DM]` 的 varlen offsets、sample ownership、`K_local=0/1/>1` 和 sparse-present rows 的 ABI。
4. **Visibility**：two-way dense 首版必须证明 AR query 不读取 MEM，DM query 同时读取 MEM、AR、DM；不支持的 attention backend 必须 fail closed。
5. **Position/RoPE**：Memory Prefix 的位置编号、是否参与 RoPE、与 AR/DM 的 offset 关系必须由 source anchor 和 CPU fixture 证明，不能沿用普通 GEN 的隐含索引。
6. **State lifecycle**：persistent W 的 timestep carry、reset、detach/TBPTT 边界与 packed batch 生命周期必须分层；不得把 fast state 伪装成 Cosmos KV cache。
7. **Checkpoint/optimizer**：新增 slow 参数（包括 `slot_queries`、`theta_Q/K/V` 与 Prefix adapter）的 key、初始化、selector 和旧 checkpoint 行为必须另行冻结；C3 不执行 refreeze。

## 4. 后续实现路线（需 C3 三方批准后才能执行）

* **C4**：子模块新增独立 Memory Prefix/attention 接入模块；保留旧 Local GEN 路径为显式禁用或兼容分支，并实现 K/V-only、norm、position、mask 的 CPU contract tests。
* **C5**：接入 causal history 与 persistent fast-state runtime；验证每 timestep 一次 K/V write、更新后 K reads、K=1 等价和 `K_local` shape。
* **C6**：冻结并实现 config/optimizer/checkpoint selector 与加载失败策略；不得静默迁移旧 authority。
* **C7**：完成 CPU/static 全套验证，形成新 root/Gitlink SHA，三方对同一 SHA 复审。
* **C8**：依 D012 先做最小 GPU smoke（少量训练步、一次 validation、一次 checkpoint reload）；通过后才进入执行授权。
* **C9**：在 LIBERO4IN1 latent cache 上先跑 matched no-memory 与 +Local smoke，再按冻结命令启动正式 Local Memory 训练。任何一项审核未齐、smoke FAIL、NaN/OOM 或产物缺失都停止，不启动正式训练。

## 5. 静态审计验收

PASS 需要：每个 source anchor 可由 `git show <submodule SHA>:<path>` 重现；现有 Local GEN 注入与目标 K/V-only Prefix 明确区分；C3.1-C3.7 均有 owner/shape/negative contract；`git diff --check` 通过；未修改子模块、未访问运行资产、未执行项目代码。缺任一项为 FAIL，并不得进入 C4。

## 6. 审核请求

请求 ChatGPT、Kimi、MM 对本审计设计和上述边界给出同一根仓 SHA 的 verdict：

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_MEMORY_PREFIX_SOURCE_ABI_AUDIT` 或 `REQUEST_CHANGES`。

该批准仅授权 C3 docs/static audit 的闭环，不授权 runtime/attention/config/optimizer/checkpoint 修改、GPU、训练或任何真实 P4/P5 操作。
