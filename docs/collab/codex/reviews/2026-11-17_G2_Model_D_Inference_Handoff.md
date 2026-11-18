# G2-D 推理与 Session 缓存交接 — M06 / M07-D

**状态：独立候选已完成作者 CPU/static，待 B 集成和独立验收。** 不代表完整 G2 上线、真实模型/GPU 缓存验收或闭环效果。总任务 [#56](https://github.com/wxwy/psm_wma/issues/56)，[D ACK](https://github.com/wxwy/psm_wma/issues/56#issuecomment-6943531508)。

## 固定来源与文件归属

| 项目 | 固定身份 |
|---|---|
| 正式 Root V3：开工及交付复查 | `7a357620b4cc1f6817749c8a8275771cfbb4049c` |
| Root Gitlink：D 不修改 | `d5c1ffc71ba8f501d4c00a8698e9b91d9175b9c2` |
| C0 | `ec9356fafd1fd18cc0bd552b7eb23428f59df7f6` |
| B 核心 | `7e888f217dfcddc35ed73782f65c6e0890c72c3a` |
| A Reader/projector | `4209b151ecc11ab2043b9d08037d43b5e3903618` |
| C 文本/数据适配 | `f262d7ff4156d83356e1d7f790adea2a61e85c6d` |
| D review base：纯依赖组合 | `3bdfaa64af45a42eb2b5adde582505d33a5f08f2` |
| **最终 D Child** | **`6991142cb94256f497347db40f58ad0ee3f482aa`** |
| D tree | `0cd9a38a2aadae13f203850cdbd6fc263926f08b` |
| 初批 D：保留历史，不作为最终 | `209749e5287c5030370464625a7e1f44dfb2ab6f` |

[Child Draft #16](https://github.com/wxwy/cosmos-framework/pull/16)：base `v3-g2-model-d-deps-20261117`，head `v3-g2-model-d-inference-20261117`。base 只组合固定 A/B/C，不含 D 源码，PR diff **仅 D 的 12 文件**。最后的依赖 merge 前后 tree 相同。Root 候选只交本文和证据；公共 TODO/SESSION/Inbox 由 B 汇总，最终 Root Gitlink/V3 集成归 B。

以下相对 Child 的 `cosmos_framework/`：

- 新增 `inference/g2_session_cache.py`、`g2_policy_conditions.py`、`g2_model_hooks.py`；
- 新增 `inference/g2_session_cache_test.py`、`g2_policy_conditions_test.py`、`g2_model_hooks_test.py`、`g2_text_kv_cache_test.py`；
- 薄接入 `inference/robocasa_session_transactions.py`、`robocasa_batch_transactions.py`；
- 扩展 `model/generator/mot/inference_text_kv_memory.py` 的请求 seed helper；
- 服务 `scripts/action_policy_server_robocasa.py` 和新增 `g2_policy_server_test.py`。

B 的核心/公共合同、A Reader/空间编码、C formatter/transforms/训练文件均保持其固定提交 blob，详见 `receipt.json`。没有复制 UND/Reader、重写 Local inner/事务调度/producer，或从新增 inference 模块导入 trainer。Root 工作树的 Child 检出独立候选，与 Root commit tree 中原 Gitlink 的区别明确保留，未 stage Gitlink。

## 原服务与事务内的行为

复用 `SessionTransactions.submit` 的完整 JSON 冻结、原 deadline/lease/frontier、inflight 与 post-ACK 去重。`_execute` / `_execute_many` 继续唯一拥有 Local prepare→generate→quiesce→commit/abort；D 只接 payload 校验、排队计时和 quiescent 清理回调。重试不重复 scan、不延长截止时间；过期、End 或异常不发布 Local candidate。

服务 `_transaction_action` / `_transaction_batch` 在同一模型调用前固定条件，保留原 Local kwargs、seed、采样与输出索引。实际调用 C 的 `prepare_static_task_text(..., dropout_applied=False)` 和 `effective_text_batch(..., special_tokens=model.llm_special_tokens, use_float_positions=actual_native_mode)`。C 的唯一 formatter/序列化及原生 PackedSequenceBuilder 产生 BOS/EOS/start-of-generation 和 `[3,L]` mRoPE；不将裸 tokenizer IDs 当 UND 身份。

同一子任务绑定一份 C StaticTaskText 和固定 recipe。state、局部相机、Local evidence 不进入文本。recipe 使用计划视频长度 `action_chunk_size+1` 与最终 padding 后分辨率，state clean row 不改变 duration。R1/R2 无 idle 字段，正常推理不随机 dropout；旧 G1 默认入口保留。G2 只走既有 owned `/v2` Session API，不由 legacy predict/batch 旁路。

同 episode 换 subtask 更新文本/查询/Global，保留 Local 历史；新 episode/scene 需要原 Session End/reset。原 owner 证明 quiescent 后才释放任务和缓存。参数原位修改、Parameter 替换或版本/config 变化会失效派生缓存；不以 tensor 地址作为内容 key。

## 缓存范围、key 与预算

stage：view_latent、text（UND hidden/frozen features）、text_kv（B 转换后的 GEN 文本 KV）、task_queries、global（Reader）、global_projection、global_kv。仅固定权重、同 Session、同进程；无跨 Session/机器共享、训练跨 step 复用或去噪交互后的全部 GEN hidden/KV 缓存。

key 覆盖实际 tokens/positions、完整/空条件、C recipe、checkpoint/UND/GEN/Reader/projector/位置/精度/config；实际 variant、有序 selected views、content/VAE recipe、projection/raster/type/grouping/version，以及**实际 valid_mask 内容身份**。未选中 view/SG 不进入 key。decision/logical/owner frame 与 owner identity 留在本请求来源记录，只有 owner/frame 前进不使相同输入失效。

默认 with_robot；without_robot 显式选择。缺请求版本报错，不回退。G2ModelHooks 要求请求 variant 与加载配置一致；改配置后重绑 hooks/revision，不在请求中暗改 Reader。只动底盘而无标识图内容/几何不变可复用；箭头内容变化失效。mask 算法版本与额外有效洞的内容身份分别绑定。

候选默认上限：32 Sessions、256 entries、CPU/GPU 各 256 MiB、4096 tensor handles。**不是部署实测定稿。** 先预留容量/淘汰未 pin 的 LRU，再 clone 独立 tensor 存储；采样期间 pin 所有引用。cache-off 临时条目也计入预算，无法容纳时明确失败并由原事务 abort。预算不覆盖模型本体、provider 缓冲或主干临时工作张量。任务绑定有 Session 上限，telemetry 每 stage 最多 1024 条；累计计数标明进程生命周期。

cache-off 每 replan 真实重算同一准备链，仍有预算和 cleanup；不是旧 G1 prompt 对照。真实 GPU parity 需另在同 runtime/精度、输入/RNG 下验收。

## 公共模型与 provider 接口

`inference.g2_model_hooks.G2ModelHooks(model, versions=..., use_float_positions=..., top_variant=...)` 只转发 B 的 `prepare_g2_text`、`prepare_g2_gen_text_kv`、`prepare_g2_task_queries`、`read_g2_global(queries,(views,))`、`project_g2_global`、`prepare_g2_global_kv`。B 的 `stack_g2_prepared` 产生唯一 `_g2_condition`，projected Global presence 支持命中不重载 view payload；禁止覆盖 Local kwargs。

versions 由**已验证的实际加载侧**提供：checkpoint_id、und_version、gen_version、reader_version、projector_version、geometry_encoding_version、mask_version、position_rule、dtype、tokenizer_identity、inference_config_id。不以 task 名、文件路径或 tensor 地址冒充版本。另检查已加载参数的 host version/generation；不可跟踪的 inference tensors 保守逐请求失效，不声称跨 replan 命中。

```python
snapshot(identity: G2SampleIdentity,
         empty_signature: GlobalCacheSignature) -> OnlineSpatialSnapshot
load_view(snapshot: OnlineSpatialSnapshot, index: int) -> SpatialView
```

OnlineSpatialSnapshot 使用 C0 identity/signature、显式 source 和 selected 顺序的 mask_content_ids。provider 填 selected view identity/projection/raster/type，不改模型/文本版本，返回当前 rollout 的必选 top＋初始化 GT 相关实体关联有效图。每张 mask 的 SHA 来自真实 bool mask，miss 时 D 独立重算验证，可调用 mask_content_identity。latent 是完整空间网格，不是 Local Visual96。

真实 provider 必须验证 content/pixels/recipe、初始化 GT 绑定、静态文本资产与当前逻辑空间状态；合法旧 image/geometry/grouping owner 可以不同，future owner 拒绝。fixture 只有手动 allow_fixtures=True 才接受；生产服务构造不会启用它。source 标签或 dataclass 结构检查不能代替真实源验收。

原 payload 新增 `g2 = {identity: asdict(C0 G2SampleIdentity), static_text: asdict(C StaticTaskText), top_variant?: with_robot|without_robot}`，省略 variant 默认 with_robot。episode 必须匹配 lease；decision frame 必须等于 Local consumer frontier；静态文本的 episode/subtask/enhanced instruction 必须一致。当前 state 仍是原独立字段。完整 body hash 包含 g2，同请求改条件由原 replay 防线拒绝。

新配置仅显式启用：g2_profile=legacy|g2_r1|g2_r2、g2_hooks_factory=module:function、g2_provider_factory=module:function、g2_cache_enabled 与 g2_cache_{max_sessions,max_entries,cpu_bytes,gpu_bytes,handles}。可信启动 factory 接收 service，不由请求指定 import。R1 不构造 provider；R2 缺真实 provider/共享 hooks 明确拒绝。首版 guidance=1。

[现有 server 的完整命令与必需变量](../evidence/2026-11-17_g2_model_d_inference/SERVER_RUNBOOK.md) 已用真实 CLI 帮助核对参数名和 cache-off 布尔开关；只解析帮助，没有构造服务或加载模型。实际 provider/identity factory 缺失时保持 BLOCKED，不以模板变量冒充可运行资产。该 runbook 也列出 B 后继3a5c6259的 residual-cache 边界；D 的361仍只属于本文固定来源。

**D runtime 构造和每请求均拒绝 world_size>1，包括 cache-off。** 不让各 Session 的 hit/miss/循环次数决定不同 FSDP collective 次序，不把 B 的方法已注册为 FSDP forward 当作 D 分布式缓存支持。

## CPU/static 证据与复现

[完整原始证据](../evidence/2026-11-17_g2_model_d_inference/README.md)。最终 raw/final-01 的唯一最终计数为 **361 passed，0 failure/error/skip，17 模块，39.69s**。不能与此前重叠的 13/40/256/74/39 等运行相加。

- 实际生产 Session/Batch/Local CPU encoder/core/scan、prepare/commit/abort、deadline、retry、End/reset、混合 Session 路由被行使，相关旧 G1 回归保留。
- 服务实际调用 C 函数、native specials/positions、idle 删除、独立 state 快更新均有断言。
- 实际 B tiny UND/逐层 GEN KV＋A Reader/projector＋C 文本的 cache-on/off 条件张量按预定 **CPU FP32 严格逐元素一致**。完整/空条件分开，图/几何/分组/mask/参数失效均覆盖。attention dispatcher 使用明确 CPU 参考核。
- 服务动作 parity 中 diffusion kernel 是 fixture；真实 CPU Local fast-state 严格一致。不是完整 Cosmos 输出/GPU验收。
- 12 文件 format/syntax PASS、11 文件严格 Ruff PASS；旧 inference_text_kv_memory.py 的唯一 I001 与 review base 诊断逐字相同，原日志保留，其他规则不放宽。
- **1,114 个 tracked Python SHA256 前后相同并与 clean 固定 Child 一致**。A/B/C 受保护 blob、D 文件与完整哈希见 receipt.json。

已有 CPU 环境 Python3.12.14、Torch2.10.0+cpu、pytest9.0.2、Ruff0.12.7；无依赖安装/升级。原环境缺 pytest-custom_exit_code/xdist，前两次收集失败日志保留。最终 runner 用 `-c /dev/null --noconftest` 不加载要求这些插件的根 conftest，断言不变。19 个依赖/既有 warnings 保留，不计 skip。

Root 文档 checkout 后独立检出上述 D Child，不把 Root 原 Gitlink 当成 D source；Child cwd：

```bash
PSM_G2_D_PYTHON=/workspace/.venvs/psm-wma-cpu/bin/python \
  bash ../docs/collab/codex/evidence/2026-11-17_g2_model_d_inference/run_g2_d_cpu.sh \
  ../work/g2-d-rerun
```

脚本显式单线程/空 CUDA，可无联网、checkpoint 或数据集运行。PASS：零失败/错误/跳过；失败使用新目录保留，不覆盖原 raw。静态命令与原作者 receipt 脚本也归档；receipt 脚本不是模型入口。

telemetry 区分 C 格式/分词、UND、文本 KV、任务查询、Reader、Global projection/KV 的 hit/miss host 耗时及 queue/采样上下文；stage 可嵌套，不相加当端到端时间。没有 GPU event 性能、提速比例或生产 P99 结论。

## 具体缺口与 NOT_RUN

1. **真实在线 spatial provider 尚未交付**：需要当前 rollout inventory/图或 latent 版本、实际 geometry/grouping/mask、初始化 GT 实体/初始 SG→静态文本绑定及 handle/buffer 生命周期。D 不读专家缓存，不用奖励、成功或未来轨迹代替绑定。
2. **实际 checkpoint/config versions factory 未冻结**：集成/执行侧提供真实已加载身份，核对 native mRoPE、C recipe/采样配置、VAE recipe/top variant。本候选不编造可部署 factory 路径或资产 SHA。
3. DATA_B Pose5 state15 与 DATA_C 实际对齐/版本仍待验收；D 不另写转换。
4. **NOT_RUN**：真实 Wan/Cosmos checkpoint；GPU BF16/compiled/native buffer parity；真实 cache-on/off 各步速度/动作输出；GPU 时延/显存；实际在线 Session/rollout、B1/mixed GPU batch、仿真/闭环/SR；FSDP/多 rank cache、正式训练/评测。

B 在统一固定代码上集成，执行侧先冻结同 runtime 数值标准、输入/RNG、checkpoint/source 和预算，再验收。作者 CPU PASS 不等于独立审核或执行批准。没有启动 GPU/真实仿真、停止其他服务、升级环境、外传私有资产、在执行服务器 commit/push 或合并正式 V3/v3-local-ttt。
