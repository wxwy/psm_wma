# DS_PRO — V3 Batch 1 B3 原生 Edge Tokenizer Token ID Parity 补证

**报告日期：** 2026-10-11。**GPT 登记日期：** 2026-10-11。
**固定 Formal Pair：** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`；Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`。
**来源与可信边界：** 本文件根据 owner 转交的 DS_PRO 总报告保留实际声称的测试范围、关键断言及样例；不是 DS 主机原始 JSON 或原始 Python 脚本。GPT 未独立读取其原始字节，不宣称复现执行。

## 1. 本轮目的和执行边界

补齐上一轮 `B3_NATIVE_TOKENIZER_EVIDENCE_OPEN`：此前 `cfg_dropout_rate=0.1` 的 9 段测试虽然跑了生产 `TextTokenizerTransform`，但 processor 为 `DeterministicCaptionTokenizer`，不能证明真实 Edge 词表产生的 Token ID Parity。

本轮 DS 报告：CPU-only、只读；没有修改生产代码、数据集、VAE/cache/index、DCP；没有 GPU、torchrun、模型训练或仿真。B1/B2/C0/D0 未重跑，`formal_verified_index_30k` STOPPED。

- 探针：`/tmp/probe_b3_native_tokenizer.py`（206.0 s）。
- 原始报告：`/tmp/psm_wma_v3_batch1_b3_native_tokenizer_report.json`（615,385 bytes）。
- 配套本地主机处理器：`/tmp/b3_edge_tok.py`；检查脚本：`/tmp/quick_b3_edge.py`。
- 本地主机官方 tokenizer 资产：`/tmp/cosmos3_edge_tokenizer/`。

## 2. 真实 tokenizer 资产与调用链（DS 报告）

- 来源：经已存在的认证代理从官方 `nvidia/Cosmos3-Edge-Policy-DROID` 获取文件；`tokenizer.json`、`tokenizer_config.json`、`special_tokens_map.json`、`config.json`、`preprocessor_config.json`、`chat_template.jinja` 共 6 个文件。
- `tokenizer.json` 17,077,500 bytes；SHA256 `4dc692a99dca6d92a44e9529ffb53541eb79bb260eec7281bc51268c05d7311c`；探针报告 `tokenizer_json_sha256_matches_gpt=true`。此值与 Hugging Face 官方 `nvidia/Cosmos3-Edge-Policy-DROID` 和 `nvidia/Cosmos3-Edge` 公开的 `tokenizer.json` SHA256 对应。
- `chat_template.jinja` 加载进 tokenizer，报告 `chat_template_loaded=true`；报告未单独列出模板 SHA256 和下载的精确 HF revision，因此这两个字段不可冒称已被单独复核。
- 本轮未完整实例化 4B VLM 或 `Nemotron3DenseVLProcessor`；仅用本地 `EdgeCaptionTokenizer` 处理器适配正式文本分支：`PreTrainedTokenizerFast` + 官方 Edge 词表 + 官方 chat template，`tokenize_text()` 内调用 pinned Child 生产 `tokenize_caption`（`cosmos_framework/model/generator/reasoner/qwen3_vl/utils.py:28-70`）。
- 生产 `tokenize_caption` 使用 `[{"role":"user","content":caption}]`，调用 `apply_chat_template(tokenize=True,add_generation_prompt=True,add_vision_id=False,return_dict=False)`，包括模板分配的 role 和 special tokens，而非裸 `Tokenizer.encode(text)`。
- `TextTokenizerTransform` 的真实 `random.random()` 分支控制 CFG 0.1。相同配对 Segment / Plan / Python、NumPy、Torch RNG 状态用于 OFF/OFF 与 ON/ON 比较。

## 3. 真实数据与 9 Segment 对照

三组真实 episode：`CoffeeSetupMug/001744`、`CloseBlenderLid/000000`、`CloseBlenderLid/000457`，每个首/中/尾 3 cursor，共 9 段。配置：`cfg_dropout_rate=0.1`、TTT=16、`max_action_dim=64`、`format_prompt_as_json=True`；携带 `config_digest=70e9867f…` 前缀（不能替代生产 preflight 实测完整 digest）。

| DS 原始总断言 | 结果 |
|---|---|
| all_segments_all_equal | true (9/9) |
| all_segments_tokens_equal | true |
| all_segments_native_ids_equal | true：全部有效帧真实 Edge Token IDs ON==OFF |
| all_segments_native_caption_equal | true：逐有效帧 tokenizer 输入 caption ON==OFF |
| all_segments_sequence_plan_equal | true |
| all_segments_action_equal | true |
| all_segments_evidence_equal | true |
| all_segments_identity_order_equal | true |
| payload_per_key | 所有非 video key 一致；video 为设计允许的 dense vs 1-byte proxy |

**示例 1：** `CloseBlenderLid/000000 cur0 frame0`，正常 JSON prompt，160 tokens；含 chat role / special tokens；报告 ON/OFF 160 个真实 Edge Token IDs 完全相同，正常帧的长度范围 160–163。

**示例 2：** 同一 Segment frame8 的 CFG dropped 空串，17 tokens；报告 ON/OFF 完整 Token ID 逐位相同：
`[1010,10,25708,1010,11,1010,10,3263,1010,11,1010,10,1503,19464,1010,12,1010]`。
整个 9 段输入的 token 长度范围 17–163。

**随机事件：** 115 个有效 Transform 调用；OFF 和 ON 各 10 次 Dropout（8.70%，与 p=0.1 相容）；`on_off_dropped_equal=true`、`all_calls_parity=true`。
每段触发次数：CloseBlenderLid/000000 cursor0/11/21 = 2/1/1；CloseBlenderLid/000457 = 0/2/1；CoffeeSetupMug/001744 = 1/2/0；合计 10。

**GA/排序：** 首 GA member0 八 slots [0..7] 的 `rows_equal=true`、`binding_epochs=[0]`、`cursors=[0]`、`segment_ids=[0]`、`n_slots_distinct=true`。原生 `gather_exact_window_same_index` 的 index0/7/15 对应 slots [0..7]、steps [idx×8]；index0 ON/OFF slot 和 step 对齐。

## 4. DS 结论及范围

DS_PRO 报 `B3 PASS`，称最后的原生 Edge tokenizer Evidence 缺口被补齐，无新 production Bug。B1/B2/C0/D0 保持此前关闭状态。此次并未反序列化 DCP、加载完整 4B VLM，也没有证明模型 loss/grad 或 same-job Resume。请见 GPT 关联审核：`docs/collab/chatgpt/reviews/2026-10-11_V3_Batch1_GATE_B_closure_native_edge_tokenid_444c232b_e9b8a41.md`。
