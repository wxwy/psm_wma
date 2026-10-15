# GPT → DS_PRO — V3 B1 CFG Local-RNG CPU Gate：真实 Native Token Payload Evidence-only 补验

**日期：** 2026-10-15  
**Gate：** `B1_P0_THREADED_CFG_LOCAL_RNG_CPU_GATE`  
**现有 formal verdict：** `REQUEST_CHANGES`（**HIGH / EVIDENCE-ONLY**；未发现确认的生产诊断代码 blocker）  
**权威详细审核：** `docs/collab/chatgpt/reviews/2026-10-15_V3_B1_CFG_local_rng_a3239591_DS_CPU_evidence_incremental_review.md`

## 0. 精确版本与边界

- B1 diagnostic Root：`a32395911c9913a5e02eb8a17e0bac11fe9ff4e0`
- B1 diagnostic Child：`8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`
- 原始 SOURCE Index8：Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`
- 原始 TARGET Packed128：Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`
- Owner r2 policy SHA256：`bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`
- 原始 iter1300 B0 DCP FP：`2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`

**本轮只补一项缺失的真实 Native CFG Caption/Token Payload Evidence。** DS_PRO 保持只读，独立脚本和日志写在 `/tmp`。不得修改 GitHub、冻结 Child、数据、Checkpoint 或任何正式代码。**不要重跑已经 PASS 的 23 编译 / 23 Ruff / 149 tests / 12 specialized checks。** 不运行 GPU、torchrun、模型/FSDP、DCP、451GB 数据扫描、正式训练或 Gate M。

## 1. 为什么还缺证据

原 DS_CPU 报告显示 `149/149 PASS`、`12/12 specialized PASS`，但新增 `test_v3_gateb1_producer_cfg.py:134-230` 使用了合成的 native-named Tokenizer/Pipeline。两次 replay 的示例 `('', [0])` 不能独立证明冻结 Source/Target **真实的** `TextTokenizerTransform`、真实 JSON prompt、生产 tokenizer processor 输出 `text_token_ids` 的 dtype/shape/完整字节 SHA256 一致。

CPU Gate 的冻结验收不是仅比较 Bernoulli seed 或 synthetic caption；需要真正的 Source/Target 原生 tokenizer 和 B1 clone 在相同 ConsumerKey 下的 Token Payload 逐字节比较，至少各有一次 CFG drop 与 no-drop。

## 2. 最小可验收执行

1. 使用 clean detached worktree，报告各自精确 Root/Child HEAD 和实际 Python import 文件路径及文件 SHA256。三个 Child 的同名 `cosmos_framework` 不得在同一 Python 进程混用；推荐独立 subprocess 分别导入，再用规范化 evidence JSON 交叉比较。
2. **采用真实** `cosmos_framework.data.generator.action.utils.json_formatter.ActionPromptJsonFormatter`、`cosmos_framework.data.generator.action.utils.transforms.ActionTransformPipeline`、`cosmos_framework.data.generator.augmentors.text_tokenizer.TextTokenizerTransform` 实现。选用已验收配置中的 `format_prompt_as_json=True`、`cfg_dropout_rate=0.1`、`caption_key='ai_caption'`、`tokenize_separately=False`、无 idle augmentor。构造一条可打印的小型代表性 JSON prompt 输入；禁止用仅伪造 `__module__` 的合成 class 冒充真实 Native 实现。
3. 优先使用配置一致、CPU 可调用的**真实 tokenizer processor**（只允许 CPU tokenizer，不得加载 Cosmos 4B 或触发 GPU/网络下载）。若不可用，先提供缺失依赖/限制与可独立审核的最强真实 Native 等价证据；不得将 mock token IDs 宣称为真实 Native token 字节。
4. 从**原 B0 ConsumerKey + `stable_seed(key.scoped('cfg_dropout','caption'), domain='python_cfg')`** 选择两个可重现的 Consumer：一个首抽样 `<0.1`，一个 `>=0.1`；不得改变 seed 算法或变更原始 B0 identity。对相同输入分别记录：ConsumerKey 全字段、seed、float draw、drop flag、JSON prompt 转换结果、输出 caption repr/UTF-8 SHA256、`text_token_ids` dtype/shape/按连续 CPU tensor 原始字节的 SHA256；如有 B0 的 transformed-payload-hash，则提供一致的 full payload hash。对两个冻结 leg 分别运行相同规范化输入，再对 B1 cloned path 使用对应真实 Native 实现运行。
5. 以**真实 Native Tokenizer** 的单线程 `random.seed(seed); random.random()` 作为 baseline（在隔离进程中保存/恢复全局 RNG state）；B1 使用 `scoped_keyed_native_caption_transform` + `random.Random(seed)`，加一条真实活跃后台 Python thread；验证 Source vs Target vs B1 的 caption、token tensor dtype/shape/完整 SHA256 均**精确一致**，drop/non-drop 两种情形都覆盖。每个 Consumer 重复至少两次、核对 B1 前后进程全局 RNG state 与原 tokenizer 实例均未被修改。
6. 对 diagnostic Child `8f3672d1` 的 `transform_draw(random.random)`，确认在**未设置 ContextVar scoped RNG** 时 fallback 行为等价于 frozen Source/Target 的直接 `random.random()`；若存在其它有效 scope 或新增随机 draw，必须报告并 STOP，不得用 mock 隐藏。
7. 输出按 case/leg 的逐字段表、原始 stdout/stderr 退出码、所有 SHA256 和消费身份、实际 Native class/processor module/file、环境证明，以及 **PASS/FAIL/INCONCLUSIVE**。任何缺少生产 tokenizer processor 的替代实验必须显式标 `LIMITATION`，供 GPT 再裁决；不得自行宣布 GPU READY。

## 3. 报告和后续授权边界

建议一份报告：`/tmp/DS_PRO_V3_B1_a3239591_authentic_native_token_payload_evidence_2026-10-15.md`，附最小独立 /tmp 脚本及机器可比 JSON。

请把报告返回 GPT。GPT 仅审核这项 Evidence-only blocker，**formal pair 未变不重新审核生产代码**，只做整改复审/补录结论。

旧 `46e9cc0e` 的 Owner GPU 授权不适用于 `a3239591`。通过 CPU Evidence Gate **之后**，Owner 才可能单独批准新 SHA 的 `P0_FIXED repeat=0`、8×H100、有界只读 GPU Smoke；必须在各自冻结 Child 目录 `cd "$LEG_ROOT/cosmos-framework"` 后启动，先 SOURCE 1301/1302 经人工确认，再 TARGET。Gate M 和 Formal30k 保持 HOLD。
