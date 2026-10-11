# PSM-WMA V3 — B3 cfg=0.1 随机 Parity 增量 Evidence Review

**日期：** 2026-10-11
**Formal Verdict:** `REQUEST_CHANGES`（Evidence-only）
**锁定 Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Formal Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**当前状态：** `GATE_A_CLOSED / B1_B2_C0_D0_CLOSED / B3_STOCHASTIC_PARITY_ACCEPTED_NATIVE_TOKENIZER_EVIDENCE_OPEN / C1_D1_E_F_HOLD / FORMAL30K_STOPPED`

## Scope / authoritative contract

冻结 Gate B 契约：`docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateB_real_data_pipeline_parity_authorization_444c232b_e9b8a41.md`，要求匹配真实 tokenizer/prompt recipe、在固定 RNG 下比较原生 token IDs/SequencePlan。对缺失真实资产明确规定不能用 synthetic 替代并宣称 B PASS。此前待整改：`docs/collab/chatgpt/reviews/2026-10-11_V3_Batch1_B3D0_supplement_evidence_adjudication_444c232b_e9b8a41.md`。

新 DS owner-relayed Evidence：`docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-11_V3_B3_cfg01_stochastic_parity_owner_relay.md`；原始 `/tmp/psm_wma_v3_batch1_b3_cfg_dropout_report.json` 和脚本尚在 DS 主机，GPT 未直接读取其字节。因此只采信 DS 报告列出的字段，不将断言扩大为真实官方 tokenizer 的数值 Evidence。

定点代码核查仅检查与本缺口直接相关的 pinned Child：
- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py:176-207` 的 factory 默认 `cfg_dropout_rate=0.1`，并构建 `ActionTransformPipeline`；
- `examples/psm_wma_robocasa_corrected_phase5.py:443-449` 没覆盖这个默认值；
- `cosmos_framework/data/generator/augmentors/text_tokenizer.py:63-113` 的生产 `TextTokenizerTransform` 使用 `random.random()` 判定 CFG 并调用 `self._processor.tokenize_text(...)` 编码文本；惰性 `_processor` 根据所传 tokenizer_config 构造；
- `cosmos_framework/data/generator/action/utils/transforms.py:785-814` 串联 tokenizer 后生成 SequencePlan。该 SequencePlan 构建依赖 mode/video/action 元数据，并非使用假词表即可证明真实 ID 值。

## 确认完成（不重新审核 B1/B2/C0/D0）

1. 真实配方随机开关 0.1 以及生产 `TextTokenizerTransform` 的 Dropout 决策已经启用；9 段 115 次 caption transform 触发 17 次，ON/OFF 每次随机判定均相同：**先前的 0.0 概率覆盖缺口 CLOSED**。
2. 配对两种配置 9/9 Segment 身份、consumer/evidence、raw/processed action、visual summary、非视频字段等价；native gather slot 顺序一致；新补证的 binding_epoch/cursor/segment_id 的首 GA member 匹配。
3. 9/9 同样经过 `TextTokenizerTransform` 代码，但 `_processor` 用确定性字符编码替身，因此报告的 `all_segments_tokens_equal=true` 只适用于该处理器，**不能标记为官方 Edge tokenizer 词表的 token-ID bytewise parity**。
4. 没有新发现 production bug，也无理由重开已经关闭的 B1/B2/C0/D0。C0 仍是 iter800 等结构候选，并非成功严格恢复。

## 当前唯一 blocker

- **Severity:** MEDIUM，Evidence-only；非 production blocker。
- **Evidence location:** `docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-11_V3_B3_cfg01_stochastic_parity_owner_relay.md:21`（`DeterministicCaptionTokenizer` 实际 `_processor` 是替身）。生产调用点 `cosmos_framework/data/generator/augmentors/text_tokenizer.py:70-113`。
- **Root cause:** 新 probe 恢复了生产随机决策，却替换了真正负责 `caption → text_token_ids` 的 Edge VLM tokenizer processor。冻结 Gate B 明确要求真实 tokenizer 配方及 native token IDs 直接对照；替身产生的相同 IDs 不是对该 frozen behavior 的完整原生观测。
- **Acceptance (minimum):** 优先从已有真实 tokenizer 的原始 Evidence 中提取 paired witness（如 B1 已有无替身的真实 `text_token_ids` 与真实模型 tokenizer 身份），注明 checkpoint/tokenizer provenance、相同输入 caption/RNG、OFF/OFF↔ON/ON 的实际 native token ID/长度及 SequencePlan equality。**无需重做全部 9 段。** 若没有，使用真实 `vlm_config.tokenizer` 指向的 processor，只做少量固定真实 caption（包括 dropout 空串和普通 JSON prompt）的 CPU-only read-only native paired tokenization，输出相同输入的 token IDs / hash / lengths 和 tokenizer identity；不能再替换 processor。优先复用已生成的 9 段 matched caption 字符串与事件记录，不重载 4B Policy。若真实 tokenizer 权重确实不可用，明确报告资产 `BLOCKED`，不得用另一替身宣称 B3 通过。
- **Fail closed:** 如果真实输入文本或真实 tokenization 两路结果不同，报首例 FAIL；如果仅部分范围覆盖，明确未覆盖部分。这个范围只用于填补已知 Evidence，不是要求重跑所有 Window/Segment/Index。

## 权限与后续

这份 Review 是最新同一 Formal Pair 的 **Evidence-only** 裁决，不重复技术审核或更改冻结 implementation SHA。DS 仅可执行上述受限 tokenizer CPU 对照或提取已有实测 Evidence。未经后续单独授权，不得执行真实 4B model / GPU / torchrun / DCP deserialize / optimizer step / simulator / Formal30k Resume 或 Fresh。

`REQUEST_CHANGES` 在 tokenizer-native evidence 完成并正式关闭前仍然有效。保留 B1/B2/C0/D0/Gate A 的已关闭状态和历史记录，不降低原 Gate B 实验契约。
