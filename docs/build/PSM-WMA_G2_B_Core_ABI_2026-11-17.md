# G2 B core：冻结 UND 与联合 K/V 公共接线

候选 Child **7e888f217dfcddc35ed73782f65c6e0890c72c3a**，直接基于公共 C0
ec9356fafd1fd18cc0bd552b7eb23428f59df7f6。本文随 B-core Root 提交绑定该 Gitlink；
不是 A/C/D 完整集成、独立批准或 GPU 验收。正式 V3/v3-local-ttt 未推广。

## 公共调用

唯一导入 `cosmos_framework.model.generator.mot.g2_contracts`。保留 C0 ABI；新增
`G2_MODEL_ABI_VERSION='psm_g2_b1_v1'`、`G2ConditionBatch`、`GENLayerKV`、
`stack_g2_prepared`、`move_g2_condition`，不另建近似 dataclass。

`G2ConditionBatch(text=EffectiveTextBatch, views=tuple[tuple[SpatialView,...]|None,...])`。
text 是最终 native **causal UND span**，包含现有 BOS/EOS/start_of_generation；
尾部 EOG 若存在仍在原 full split。C 使用原生 `SequenceBuilder.pack_text_tokens` 构造，
B 在实际 pack 校验 sample 数、causal lengths、tokens、mRoPE positions。一次 dropout 不重抽。

可选 `text_features:UNDTextFeatures`、`global_tokens:tuple[Tensor[64,D]|None,...]`、
`gen_text_kv:tuple[GENLayerKV,...]`、`global_kv:tuple[GENLayerKV,...]`。
已准备的 Global tokens 独立确立 presence，缓存命中可不载入 views payload；
没有 tokens 时才由 views 判断 presence。两者皆无则零长度，不占零 token。
GENLayerKV 为当前权重下已归一化/旋转的 `[N,Hkv,Dhead]` K/V，仅 no_grad 推理可用。
文本按 sample text.lengths 排列，Global 按 presence 样本顺序各 64 行。训练拒绝旧 GEN KV
与预投影 Global，使用注册 Reader/projector 和当前 GEN norm/projection，保留输入反向图。

训练 `training_step(...,_g2_condition=...)`，也可由 C 放 `data_batch['g2_condition']`；
生成 `generate_samples_from_batch(...,_g2_condition=...)`，原 `_local_memory_prefixes` 保留。
首版 G2 显式要求 guidance=1、无 batched CFG/prompt upsampling；CP/CUDA Graph/multiview/
multi-control/旧 MemoryState 不混入。只对显式 G2 选择 prepared 入口，旧配置优化不全局关闭。
采样循环前 `prepare_g2_condition` 补齐一次 UND/Global；D 已准备结果可直接使用。

| OmniMoTModel 公开方法 | net 对应方法 | 语义 |
|---|---|---|
| prepare_g2_text(text) | prepare_und_text(text) | 一次冻结原生 UND，post-norm hidden + 各层 base K/V |
| prepare_g2_gen_text_kv(features) | prepare_gen_text_kv(features) | 当前 GEN norm + 捕获 RoPE，推理快照 |
| prepare_g2_task_queries(features) | prepare_task_queries(features) | A 语言适配/任务 queries |
| read_g2_global(queries,views) | read_global(queries,views) | A 视觉 Reader，views 按 batch 嵌套 |
| project_g2_global(reader) | project_global(reader) | A 独立 Global projector/modality |
| prepare_g2_global_kv(projected) | prepare_global_kv(projected) | 每层 GEN input norm/KV projection/key norm，无新 RoPE |
| prepare_g2_condition(condition,net=None) | prepare_global_tokens 等 | 生成请求级补齐，不改输入载体 |

D 已有 `generation_kwargs(text_features=tuple[B1 features], text_kv=tuple[layer tuples],
global_tokens=tuple[None|Tensor[1,64,D]],global_kv=tuple[None|layer tuples])` 可直接返回
`{'_g2_condition': stack_g2_prepared(...)}`。helper 合成唯一 native batch，保持顺序与缺省
Global presence；缺已转换 KV 时回到当前投影。protocol IDs 不同的文本批拒绝近似合并。
签名/权重版本/Session/缓存有界管理仍由 D 唯一实现；B 未改 inference_text_kv_memory.py。

## 注册、配置与 FSDP

`OmniMoTModelConfig` 与 `Cosmos3VFMNetworkConfig`：
`g2_text_enabled=False`、`global_memory_enabled=False`、`global_memory_config=None`、
`global_memory_latent_channels=48`、`global_memory_top_variant='with_robot'`。
Global config dict 与 C0 GlobalMemoryConfig 同字段；显式 enabled 须与总开关一致。
latent channels 必须符合实际 recipe，CPU C4 fixture 显式设 4。Global-off 不 import/构造 A
模块，不增加参数/初始化 RNG；R1 可只开启 g2_text_enabled。

注册名 `net.global_memory_reader.*` 与 `net.global_memory_projector.*`，A reset_parameters
由模型初始化调用。A 模块在独立集成阶段引入，本 B commit 未复制 A 算法。
`model.g2_parameter_inventory()` 返回 `parameters` 内 global/gen/action_adapter/frozen 四个
互斥完整 name tuple，另 `new_state_keys` 是实际 Global state_dict keys。Omni 名字含 net 前缀。
`model.set_trainable_names(完整name集合)` 只改变 requires_grad、同步已建 unsharded flags 和
FSDP2 dtype bookkeeping，不替换 Parameter/optimizer/moments；要求完整 optimizer/Local 事务
结束且 zero_grad(set_to_none=True)、FSDP resharded。阶段与 optimizer 属 C，不在 B 重做。

Root prepare 和 decoder prepare_und/prepare_gen_text_kv/prepare_global_kv 都注册 FSDP forward。
B 的请求准备在各 rank 一致判定文本缓存命中；Global root entry 在 absent/hit rank 仍进入，
局部 Reader 工作才按 presence 分支。**D 按 Session/cache miss 分别调用 hook 的多 rank 模式
尚不能据此宣称支持**：不同 ranks 的调用次数必须一致，或在 D adapter 明确拒绝该模式。
FSDP2 bookkeeping 使用当前 PyTorch 内部字段，真实 A/B 切换/恢复必须执行侧验证。

## 作者 CPU 证据与可运行小样例

最终 scoped suite **198 PASS/0fail/error/skip**，含新 B core 28 项；不累计早期重复运行。
正常/空/混长/pad、FP32/BF16、UND post-norm hidden 和逐层 base KV、GEN 输出、当前 GEN
key norm 梯度、冻结 GEN 对 Global 输入反向、全层 K/V-only/presence/offset/mixed sample 隔离、
zero Value 非 off、参数 inventory/配置关闭/RNG、请求一次准备、D 载体合批均有 CPU 检查。
生产 attention 仍用项目 dispatcher；测试只在 kernel 边界替换 CPU SDPA reference。
9 个新增/主要修改文件 strict Ruff check/format PASS；其余旧文件保留 baseline import-sort debt，
I001 外静态通过。精确旧 C0 源码对照 none/Local-only × B1/mixed 的输出/梯度/构造与前向 RNG
逐位相等，见 `artifacts/g2_model_b_core/disabled_c0_exact.log` 与可复现脚本。

Child cwd，CPU 虚拟环境路径可替换为已满足仓库依赖的 Python：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 \
  /workspace/.venvs/psm-wma-cpu/bin/python -m pytest --noconftest -o addopts='' \
  cosmos_framework/model/generator/mot/g2_core_test.py -q
```

此命令是小型真实 MoT 层 + 合成 prefix；不是实际 A Reader/真实 checkpoint/GPU。
完整 scoped 命令、JUnit、失败迭代与最终 log 见 `artifacts/g2_model_b_core/README.md`。
最初暴露的逐层占位丢失/空文本 helper import 已修正；BF16 首轮是 fixture 把 native FP32
rotary buffer 一起转 BF16，修正 fixture 保留 FP32 后 16 个双精度路径检查通过，不修改 RoPE 规则。

真实 Wan/Edge、GPU attention materialization/compile、实际动作 loss/Local inner/FSDP、TRAIN_A/B
恢复、缓存 on/off 和 Session 混合闭环均未运行。本 B core 尚不包含 A/C/D 最终来源。
