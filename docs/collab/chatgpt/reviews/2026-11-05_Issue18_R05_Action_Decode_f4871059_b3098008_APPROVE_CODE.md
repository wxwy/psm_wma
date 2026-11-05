# GPT 独立增量 Code Gate — Issue #18 R05 VFM Action Decode 动态编译修复

**日期**：2026-11-05  
**正式技术 Verdict**：`APPROVE_CODE`（只针对下述精确 Formal Pair 的窄范围源码 Gate）  
**生产代码阻断项**：未发现 HIGH / MEDIUM。  
**GPU/真实评测状态**：`NOT_RUN`，本 verdict **不构成** H100 或 RoboCasa Canary 验收通过。

## 1. Formal Pair 与证据分层

| 来源 | SHA |
|---|---|
| 本轮 Formal Root implementation | `f4871059cf28a7e2142325738decbf1d53c3148b` |
| 本轮 Formal Child / Root Gitlink | `b3098008375c275a36dd2f50cbaf757bedf493ea` |
| 上一根仓正式源码基线 | `c9fa60b7134fda8fb848c29c148f25c7a8901892` |
| 上一Child基线（编码修复） | `4e9c8104ffd15a373b576bc35ee608de1b60eea1` |
| 作者申请/Evidence归档 SHA（不是 Formal implementation） | `461bdfeb49e48a242d55c3b1c7f87ccaeee0dc6a` |

已从 GitHub 实际获取新Child commit/diff、Root commit/tree、两仓 base→head diff；确认 Gitlink **精确指向**新Child。Root实际增量只含 `SESSION.md`、`TODO.md`、`cosmos-framework` Gitlink 和先前任务request，没有Root生产源码变化。Child相对原正式基线仅修改以下四个文件：`cosmos3_vfm_network.py`、`parallelize_vfm_network.py`、`parallelize_vfm_network_test.py`，新增`action_decode_compile_test.py`。没有混入Issue#17 Streaming代码或G2变更。审查者依据实际代码得出结论，不继承作者/Peer评价。

## 2. 本次发现与根因（现场证据）

原R05真实验证（独立旧集成源码）在 `iter_000027700`/RoboCasa 18Task×2EP/M16B8/Raw15 H16/Local-TTT required下，完成12个有效EP，后续因GPU6 Policy Server推理错误被迫中止。服务器原始日志显示：

```text
torch._dynamo hit config.recompile_limit (8)
function: '_decode_action' (cosmos3_vfm_network.py:1249)
last reason: len(packed_seq.action.tokens) == 5
```

原来整个`_decode_action` 以 `torch.compile(fullgraph=True,dynamic=True)` 编译；Python列表长度/结构守卫仍随Batch变化，故即使Tensor动态形状编译可用，仍可能触发 `FailOnRecompileLimitHit`。**本 finding 不应混同此前 `_encode_action` 的旧故障**。

## 3. 实际增量代码审核

[新Child `cosmos3_vfm_network.py`](https://github.com/wxwy/cosmos-framework/blob/b3098008375c275a36dd2f50cbaf757bedf493ea/cosmos_framework/model/generator/mot/cosmos3_vfm_network.py)：

- 在`_decode_action`的no-noisy dummy与noisy分支，**仅**用 `self._project_action_predictions(preds_action, dummy_domain_id)` / `self._project_action_predictions(action_hidden_states, per_token_domain_id)` 替换原 `self.llm2action(...)` 的两处调用。
- 新 `_project_action_predictions(Tensor,Tensor)` **直接返回原 `self.llm2action(Tensor,Tensor)`**；无新参数、缓冲区或Module，无新cast、detach、clamp、fallback、捕错或额外运算。
- `_decode_action` 仍在Eager层执行 `has_noisy_tokens`、`action.mse_loss_indexes` gather、`noisy_frame_indexes/domain_id/token_shapes` 列表迭代和合并、`unpack_action`零填充/索引还原、`output_dict.update`；原分支语义未改。
- dummy分支仍执行 `action2llm → optional modality embedding → llm2action`，保留 `preds_action_list[0] += 0 * preds_action.sum()` 以保持无noisy参数梯度连接。action缺失/无tokens原样返回dummy结果，未改成静默全零。
- [新 `parallelize_vfm_network.py`](https://github.com/wxwy/cosmos-framework/blob/b3098008375c275a36dd2f50cbaf757bedf493ea/cosmos_framework/model/generator/mot/parallelize_vfm_network.py) 仅把编译目标从整个 `_decode_action` 迁移到 `_project_action_predictions`；保留之前 `_project_action_tokens`、其余heads以及原 `compile_options`：`fullgraph=True`、常规`dynamic=True`、`cuda_graph_scope='forward'`时原静态选项、可选mode/inductor参数；未调整默认 `recompile_limit=8`。
- 修改的旧`parallelize_vfm_network_test.py`仅同步编译目标列表名称，原scope/option断言继续保留。

**源码独立判断：** 该改动能从`_decode_action`编译输入去除R05已记录的`packed_seq.action.tokens` Python列表长度guard，保留Tensor投影的编译优化；没有发现这次增量对原数学/参数/接口契约的新破坏。**但没有理由推断其它VFM Head永不因自己的动态结构重编译。**

## 4. 作者CPU Evidence审核（非GPT独立CPU通过）

[作者交接](https://github.com/wxwy/psm_wma/blob/461bdfeb49e48a242d55c3b1c7f87ccaeee0dc6a/docs/collab/codex/reviews/2026-11-05_Issue18_R05_Action_Decode_f4871059_b3098008_Code_Gate_Request.md)、`artifacts/vfm_action_decode/2026-11-05_cpu/final_summary.json`、`formal-targeted/summary.json`、`formal-static/static.json`、`formal-eager/summary.json` 均已实际读取。

- 旧`4e9c8104`受控RED：默认cap8，四组输入均在成功编译8张图后第9次不同请求触发 `FailOnRecompileLimitHit`，具体guard与现场同属于`len(packed_seq.action.tokens)`。旧工作树有未追踪新测试，不把整个RED工作树冒充clean。
- 新正式干净Formal Pair：**77/77 PASS**，26新+51既有；0FAIL/ERROR/SKIP，Shell0，1229源码指纹 unchanged；另有8GPU/L1用例明确deselect，**未实际执行**。
- 四组`FP32/BF16 × LocalEnabled on/off`，每组1024个B1–8循环请求期间不reset编译缓存，计数2图/组（保留默认cap8）；CPU Inductor FP32/BF16各32交替请求，3图/组，包含backward。
- 96组原eager与新eager的15D/H16形状合成测试显示输出、dtype、输入梯度、参数梯度、None/zero梯度、state_dict/参数身份逐值一致；compiled vs eager有显式浮点容差。覆盖noisy/clean/absent、混合样本、ragged、framewise/scalar domain、改变noisy索引、三种projector、嵌入on/off。
- 实际Child差分与作者静态报告一致：Ruff/format/AST PASS；作者peer只读检查不是外部独立验收。

**审核者独立执行状态：** 已实际独立读取GitHub精确代码和证据；曾尝试在服务器单独检出Formal Root/Child以复跑77项，Root检出成功，但Child GitHub下载连接长时间不返回，已只终止本次自己启动的悬挂下载；**因此本轮不声称GPT独立CPU77 PASS**。该执行可随后使用精确Pair的无GPU独立Gate重试。技术Code Gate判断不依赖虚构复跑结果。

## 5. Verdict与后续验证边界

**`APPROVE_CODE`：Issue#18仅 `_decode_action` 编译边界窄修复的源码实现可进入下游隔离验收。**

明确不授权将本源码直接合并官方V3、替换R04（648有效Core）或R05（12有效Core）原冻结Source/Manifest普通Resume，也不授权G2合并、模型训练或默认8张图上限调整。M/B Resume严格一致性限制完全保留。

下游需由GPT在独立、干净工作树，将新Child `b3098008` 与Issue#17 Streaming Child `82fa270e`组合并形成**新的集成Formal Root+Child Pair**，依阶段验证：实际环境版本、完整模型Checkpoint `iter27700`、Raw15/H16、Local-TTT required、H100 BF16 CUDA grouped_mm/编译、B1–8动态请求、CPU回归与必要GPU数值、OS Sim Episode有效提交、延迟/NativeBatch/队列及RSS显存。不可用5D/16D合成Act代替真实15D链路；在M16/B8已出现持续Policy积压时不应盲目扩M32/B8。

此处批准的只是上述窄源码Code Gate；真实GPU和生产吞吐结果须单独报告，不由作者77项或GPT静态阅读推断。
