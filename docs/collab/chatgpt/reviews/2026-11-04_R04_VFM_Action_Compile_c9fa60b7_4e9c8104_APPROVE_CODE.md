# GPT 独立 Code Gate — R04 VFM Action 动态 Batch 编译边界修复

**审核日期**：2026-11-04  
**Formal Verdict：`APPROVE_CODE`（仅当前窄范围 Action-head 编译边界修复）**  
**审核对象**：Root `c9fa60b7134fda8fb848c29c148f25c7a8901892` / Child-Gitlink `4e9c8104ffd15a373b576bc35ee608de1b60eea1`。

## 1. 精确身份、范围

- 原生产基线：Root `9635cefe3208ab6320ba5fa70b0e0d68fd444790` / Child `1069fe78841228cadbbfbe6afbd767eaed6225da`。
- 新 Root 的实际 Git tree 中，`cosmos-framework` Gitlink 精确为 `4e9c8104ffd15a373b576bc35ee608de1b60eea1`。作者归档提交 `c6e07a51b8747676f8ef6014c72e9926e8805702` 是证据/账本，不是 implementation target。
- Root 实际生产代码未修改，只更新 Gitlink；Child 源码增量正好四项：
  1. `cosmos_framework/model/generator/mot/cosmos3_vfm_network.py`
  2. `cosmos_framework/model/generator/mot/parallelize_vfm_network.py`
  3. `cosmos_framework/model/generator/mot/action_encode_compile_test.py`（新）
  4. `cosmos_framework/model/generator/mot/parallelize_vfm_network_test.py`（旧测试目标名调整、import 排序）。
- 与 Issue#17 Streaming 代码是**两个互不包含的候选 Formal Pair**；本 R04 候选不自动继承 Issue#17 的869 CPU证据，也不自动合并两条Child分支。

## 2. 根因与独立源码判断

**现场根因证据（R04服务器此前只读核查）：** GPU7日志 `torch._dynamo hit config.recompile_limit (8)`，函数 `_encode_action`，至少一条guard涉及 `len(packed_seq.action.domain_id) == 1`，随后 `FailOnRecompileLimitHit`、GENERATING HTTP409、评测停止。未捕获全部历史guards，不把这条当成完整原因集合。

[当前修复的网络源码](https://github.com/wxwy/cosmos-framework/blob/4e9c8104ffd15a373b576bc35ee608de1b60eea1/cosmos_framework/model/generator/mot/cosmos3_vfm_network.py#L1185-L1250)：
- `_encode_action` 仍负责 `pack_action()`、`has_noisy_actions`、timestep embedding、noisy-index应用及scatter。原cast `packed_tokens_action.to(target_dtype)` → `self.action2llm(...)` → optional `self.action_modality_embed` 原顺序移入 `_project_action_tokens(packed_tokens, per_token_domain_id, target_dtype)`。没有另加参数或权重，计算语义未变。
- [编译安装器](https://github.com/wxwy/cosmos-framework/blob/4e9c8104ffd15a373b576bc35ee608de1b60eea1/cosmos_framework/model/generator/mot/parallelize_vfm_network.py#L15-L57) 将编译目标从 `_encode_action` 改为纯Tensor helper，仍使用原 `compile_options`（通常`fullgraph=True,dynamic=True`；whole-forward CUDA graph场景维持既有静态scope），其他四个head不变。Python列表长度不再是这个被编译函数的输入，使R04已记录的列表长度guard在该编译目标上不可达。
- 这属于修复**具体Action编码头的编译边界**，不是全局禁用`torch.compile`、扩大重编译额度或吞掉`FailOnRecompileLimitHit`；默认上限仍为8。
- 网络权重树、Local-TTT逻辑、Session、Max Batch、M/B Resume与科学Manifest没有改动。新候选的Root和Child源码身份不等于R04冻结身份，不能直接覆盖原R04工作树并对剩余252EP执行普通Resume。

## 3. Evidence：直接核对作者机器摘要与测试源码

[作者交接](https://github.com/wxwy/psm_wma/blob/c6e07a51b8747676f8ef6014c72e9926e8805702/docs/collab/codex/reviews/2026-11-04_R04_VFM_Action_Compile_c9fa60b7_4e9c8104_Code_Gate_Request.md) / `artifacts/vfm_action_compile/2026-11-04_cpu/final_summary.json` / `formal-static/static.json` / `formal-eager/summary.json`。

- 旧版受控RED四组均在8次成功编译后第9个不同请求触发预期的`FailOnRecompileLimitHit`；新候选精确Pair CPU：**51/51 PASS**、零FAIL/ERROR/SKIP、Shell0、`source_unchanged=true`、1227源码指纹。8个GPU/L1用例**显式deselect**，未将其误报成实际执行。
- 新版在两个`local_memory_enabled`配置×FP32/BF16组合下，每组1,024次连续B1–8/metadata变化均观察到1个Dynamo graph，期间未reset；默认 `recompile_limit=8` 保持。
- CPU Inductor FP32/BF16各32次交替请求：2图/组，输出对eager在对应精度容差内一致。12个投影类型/embedding/dtype旧eager→新eager用例，作者保存输出、输入梯度与参数梯度逐值一致的合成golden；AOT-eager gradients及状态字典键一致。测试是实际`Cosmos3VFMNetwork`方法及生产`apply_compile`安装器的CPU调用，不是孤立AST helper。
- 实际 Child commit/diff、原测试源码、作者`static.json`共同支持改动确实仅在声明范围。静态Ruff、format、AST报告PASS；此次GPT独立阅读真实源码与相关证据，不声称独立复跑51项。

## 4. 未关闭的外部验证边界（不构成本轮Code blocker）

- CPU Action头测试**不证明**真实GPU/H100 BF16 grouped_mm、FSDP2 unshard/reshard、CUDA Inductor/cuda-graph replay、所有其它头或端到端Action Server的长时运行。
- 还需在匹配的真实checkpoint/config和固定硬件上做**独立授权**的B1–8交替、数值/梯度必要等价、Batch直方图、p95/p99延迟、编译图数量/重编译告警和异常/清理Canary；不能由CPU模拟吞吐推断H100加速。
- R04现场仍有648/900有效Core与冻结Manifest/Source SHA；新候选不授权直接Resume原Run，也不能把648/900写作正式SR。若要使用修复后的源码跑900EP，需单独决定来源可追溯的新Run或经严格审查的迁移协议。
- Issue#17的`551b0362 / 82fa270e`完整作者CPU **869/869 PASS** 是同一技术实现Pair的新Evidence，正式GPT技术审核此前已`APPROVE_CODE`，无需因账本更新而重审；该线可单独进入DS独立CPU。此R04代码审核不能代替Issue#17的DS验收。

## 5. Formal verdict 与停止条件

**`APPROVE_CODE` — R04 VFM Action头纯Tensor投影编译窄修复，当前Formal Root/Child精确Pair的源码Gate通过。**

无新增确认的HIGH/MED源码问题；现有证据足够支持这一窄范围编译边界修正。**不授权**改动共享生产V3/G2、移植Issue17未审代码、修改旧R04输出/源码、训练、真实checkpoint/模型、GPU实验或正式评测。下一步先由DS独立CPU验证该Pair，后续真实GPU Canary需Owner单独授权。审核结论仅绑定本Formal Pair。
