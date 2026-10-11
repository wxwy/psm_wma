# V3 Batch 1 — B3 原生 Edge Token ID 增量审核与 Gate B 正式关闭

**日期：** 2026-10-11
**Formal evidence verdict：** `B3_PASS / GATE_B_CLOSED`
**Formal implementation root：** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Formal Child/Gitlink：** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Overall：** `GATE_A_CLOSED / B1_PASS / B2_PASS / B3_PASS / C0_PASS_STRUCTURAL_ONLY / D0_PASS / BATCH1_CLOSED / C1_D1_E_F_HOLD / FORMAL30K_STOPPED`

## 审核授权与已有冻结契约

1. 冻结 B1/B2/B3 输入数据契约：`docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateB_real_data_pipeline_parity_authorization_444c232b_e9b8a41.md`；本轮无须重做 Formal Pair 未变化时的技术审查。
2. 合并 Batch1 C0/D0 授权：`docs/collab/chatgpt/reviews/2026-10-10_V3_r2_batch1_parallel_B_C0_D0_execution_authorization_444c232b_e9b8a41.md`。
3. 上次最后一个 Evidence-only blocker：`docs/collab/chatgpt/reviews/2026-10-11_V3_Batch1_B3_native_tokenizer_asset_target_and_acquisition_adjudication_444c232b_e9b8a41.md`。仅针对真实 tokenizer 的 native Token IDs。
4. 新 DS_PRO 报告归档：`docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-11_B3_edge_native_tokenid_parity_owner_relay.md`（owner 转交；原始服务器 `/tmp` JSON 和探针源码 **未被 GPT 直接检查或独立复测**）。本 verdict 是有明示证据来源边界的增量 Evidence Review，而非独立二次执行。
5. 固定 Child 源码对照：`action_policy_robocasa_edge.py:16-30` 用 `EDGE_MODEL_CONFIG` 覆盖 Nano 模型参数，`vlm_config.tokenizer.tokenizer_type` 解析自 `EDGE_POLICY_CHECKPOINT`；`data/generator/processors/__init__.py:119-176` 将 Edge route 指向 Nemotron3DenseVLProcessor；`data/generator/processors/base.py:215-234` 将文本 tokenize 委托 `tokenize_caption`；`model/generator/reasoner/qwen3_vl/utils.py:28-70` 实施聊天模板（user role、generation prompt、special tokens）；`data/generator/augmentors/text_tokenizer.py:99-113` 实施生产 CFG 判定并调用其 processor。
6. 官方 tokenizer SHA256 独立核对：`nvidia/Cosmos3-Edge-Policy-DROID/tokenizer.json` 的 HF 发布哈希为 `4dc692a99dca6d92a44e9529ffb53541eb79bb260eec7281bc51268c05d7311c`、17,077,500 bytes；`nvidia/Cosmos3-Edge/tokenizer.json` 同哈希。参考 `https://huggingface.co/nvidia/Cosmos3-Edge-Policy-DROID/blob/main/tokenizer.json` 和 `https://huggingface.co/nvidia/Cosmos3-Edge/blob/main/tokenizer.json`。

## 逐项行为→证据→裁决

| 检查目标 | 当前 Evidence | GPT 裁决 |
|---|---|---|
| Edge 正式 tokenizer 资产身份 | NVIDIA Edge-Policy-DROID 官方词表，SHA256 与文件长度匹配；不再使用 Nano/Qwen 错误 target | `CLOSED` |
| CFG stochastic recipe | 生产 TextTokenizerTransform，p=0.1；115 有效帧，10 次真实触发，ON/OFF 逐调用相同 RNG 事件 | `CLOSED` |
| 真实 text IDs（含模板） | PreTrainedTokenizerFast 从真实官方 tokenizer.json 建立，并装载官方 chat_template；调用生产 `tokenize_caption` 和 HF `apply_chat_template`；正常 JSON 160 tokens、dropout 空串 17 tokens；逐帧 ON/OFF 原生 IDs 相等 | `CLOSED`（B3 所检 CPU 文本 token 分支） |
| 9 段真实 payload/因果与 GA | identity/consumer/evidence、Action/SequencePlan 9/9 相等；terminal remainder、previous evidence 与 native gather 对照前轮已经成立；本轮补充 GA 身份及顺序 witness | `CLOSED` |
| Optimized vs reference 数据路径 | OFF/OFF 与 ON/ON 9/9 完整 paired parity，允许零视频物理 proxy/storage 差异，未见语义漂移 | `CLOSED` |
| B1/B2/C0/D0 | 既有 Gate 与各自补证已经关闭，本轮无新代码或新反证 | `NO_REOPEN` |

**对 native path 的精确判定：** DS 未在本机加载完整 `Nemotron3DenseVLProcessor` 或 4B Policy；其 `EdgeCaptionTokenizer` 使用正式 Edge BPE 文件、所下载官方 chat template，并**调用 pinned Child 的同一个 `tokenize_caption` helper**。这个 helper 在本验收范围内由 `BaseVLMProcessor.tokenize_text` 调用，所依赖的文本 token IDs 由 tokenizer 的 `apply_chat_template` 生成。故可接受为已覆盖的有限 CPU text-path parity，但**不可推广为完整 native model processor / visual crop / temporal token / loss-gradient parity**。后者独立留给 D1。

**合并解释 B1：** 旧 B1 原始 4-sample probe 的 token 部分使用 synthetic tokenizer，不能说四个 index 都已有 native token ID 验证；这项已披露的限制由后来 B3 在**两类以上真实 task、9 段 115 有效帧、包含首/中/尾及真正 CFG random 分支的 OFF/OFF vs ON/ON 原生 text-token 配对**补强，其余 B1 数据字段与 4 config 分别成立。累计 Evidence 足以回答本 Gate 的真实 tokenizer 输入是否因 compact/cache 优化而改变，不把旧 fake IDs 重新描述成真实数据。

## 当前 Evidence 来源的非阻断限制

- `/tmp/psm_wma_v3_batch1_b3_native_tokenizer_report.json`（DS 声称 615385 bytes）尚未被 GPT 自行读取；GPT 仅审核 owner-relayed DS summary + pinned Child source + 官方 tokenizer 文件发布信息。
- 这份摘要未列出 tokenizer 的 HF 完整下载 revision、单独的 chat_template SHA256 或 probe 的所有原始 per-frame哈希；但明确给出官方词表 SHA、加载模板行为、生产 helper、正常和空串实际 ID 样例及全量 matched summary。它们可作为审计溯源的后续附属材料，但不要求因此重跑已通过的 9 Segment 探针。
- 不宣称 Config Digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` 在本 CPU Evidence 中被生产 strict-resume preflight 重新测量；仍为 expected-only。
- 本 closure 不代表 checkpoint `iter800` 可严格恢复，也不代表显存、训练吞吐、梯度/优化器或 RoboCasa 任务成功率结论。正式 Job 原始 DCP 只读保存。

## Gate Verdict 及后续约束

**正式关闭 B3 与 Gate B；此前 Evidence-only `REQUEST_CHANGES` 对 native Edge tokenizer 的唯一 blocker 变为 `CLOSED`。** 不需要再为本 Gate 重做 tokenizer fake/native、B1/B2、Dataset Index 或 VAE 编码。

**仍 HOLD：** C1（严格 same-job DCP 状态 load 与数据序列连续性）、D1（8×H100 数值、Loss/Gradient、资源与吞吐）、E（真实 Policy/Local 闭环）、F（18-task screening），以及 Formal30k Resume。Gate B 是输入消费对照 Gate，**不自动授权**任何新 GPU、DCP deserialize、torchrun、model load、optimizer step、Fresh 或 Resume。

建议下次起草独立受控的 C1 与 D1 验收授权，C1 必须在不污染 Formal30k 目录的隔离诊断环境中核对 iter800 的 model/optim/scheduler/trainer、8 rank dataloader sidecars、Local fast state、RNG、frontier 与后续消费序列；D1 可按真实依赖关系合并可独立任务，不能通过原正式 Job 试错。
