# PSM-WMA V3 — Batch1 B3 原生 tokenizer 资产来源纠错与有界获取授权

**日期：** 2026-10-11
**Formal Verdict：** `REQUEST_CHANGES`（Evidence-only；B3 尚未提供 native Token ID Parity）
**Formal Implementation Pair：** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` / Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`（未改变；不重做代码审查）
**状态：** `GATE_A_CLOSED / B1_B2_C0_D0_CLOSED / B3_NATIVE_TOKENIZER_EVIDENCE_OPEN / C1_D1_E_F_HOLD / FORMAL30K_STOPPED`

## 1. 本轮材料与定点审查

- DS owner-relayed 报告：`docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-11_B3_native_tokenizer_asset_blocker_owner_relay.md`。
- 冻结 Gate B：`docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateB_real_data_pipeline_parity_authorization_444c232b_e9b8a41.md`。
- 上一次 Review：`docs/collab/chatgpt/reviews/2026-10-11_V3_Batch1_B3_cfg01_stochastic_parity_evidence_review_444c232b_e9b8a41.md`。
- 仅在 fixed Child 查看直接相关代码：`cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_robocasa_edge.py:9-31`; `cosmos_framework/configs/base/experiment/sft/models/edge_model_config.py:138-173`; `cosmos_framework/data/generator/processors/__init__.py:119-176,188-224`; `cosmos_framework/data/generator/processors/base.py:133-183,215-234`; `cosmos_framework/data/generator/processors/cosmos3_edge_processing.py:90-123`; `cosmos_framework/model/generator/reasoner/qwen3_vl/utils.py:28-70`; `cosmos_framework/data/generator/augmentors/text_tokenizer.py:64-113`。
- 外部官方 Hugging Face 文件索引：`https://huggingface.co/nvidia/Cosmos3-Edge-Policy-DROID/tree/main`；根 `tokenizer.json` `https://huggingface.co/nvidia/Cosmos3-Edge-Policy-DROID/blob/main/tokenizer.json`；`text_tokenizer/` 列表 `https://huggingface.co/nvidia/Cosmos3-Edge-Policy-DROID/tree/main/text_tokenizer`。

## 2. 确认的目标识别错误 — 不能批准原版 Option A

**MEDIUM / Evidence-target blocker**：DS 从 `action_policy_robocasa_nano.py` 和 `nano_model_config.py` 推断实际 tokenizer 为 `Qwen/Qwen3-VL-8B-Instruct`。但 formal `action_policy_robocasa_edge.py:16-30` 先以 `EDGE_MODEL_CONFIG` 覆盖整个 `model.config`，又在 `vlm_config.tokenizer` 中显式设置 `repository=None, revision=None, tokenizer_type="${oc.env:EDGE_POLICY_CHECKPOINT}"`。Edge config 为 Nemotron3DenseVLTextForCausalLM + `build_processor_lazy`，`build_processor` 在 Edge 标识/本地 Edge snapshot 路由至 `Nemotron3DenseVLProcessor`，不是 Nano 的 `create_qwen2_tokenizer_with_download`。

因此不能下载 `Qwen/Qwen3-VL-8B-Instruct` 并用其 token IDs 声称证实本正式 Edge Job；需要记录 **实际 resolved EDGE_POLICY_CHECKPOINT 路径/配置** 与对应官方 tokenizer 标识。如果运行时解析结果意外与上述不同，报告 `BLOCKED` 并提交实际配置 witness，不臆测。

**已经查证存在匹配的官方资产：** HF `nvidia/Cosmos3-Edge-Policy-DROID` 根目录和 `text_tokenizer/` 子目录均列出 `tokenizer.json`，文件大小为 17,077,500 bytes，SHA256 **`4dc692a99dca6d92a44e9529ffb53541eb79bb260eec7281bc51268c05d7311c`**（官方仓库 metadata 显示）。和 DS 说“当前主机缺文件”并不矛盾：在线存在不等于主机当前拥有文件。

## 3. 本次最小执行授权（独立取数路径，不需再次 Owner 往返）

**Option B 优先（无下载）：** 如集群/owner 已有与正式 `EDGE_POLICY_CHECKPOINT` 匹配的模型 snapshot，可将 **同一来源** 的 `tokenizer.json`、`tokenizer_config.json`、`special_tokens_map.json`、`chat_template.jinja` 及 **必要且仅必要** 的 processor metadata 复制到验证主机的全新 `/tmp` 目录。不得破坏集群原始资产；记录原始相对路径、文件哈希、resolved tokenizer config、版本/commit。先检查模型根目录，而非只检查 `text_tokenizer/` 是否已有大文件。

**Option A' 立即备用授权（修正 A 的仓库）：** 若 B 无法在当前主机即时取得，允许 DS 通过**已有认证代理**向官方 `https://huggingface.co/nvidia/Cosmos3-Edge-Policy-DROID` 的 pinned snapshot 读取上述白名单 **tokenizer/processor 文本及 JSON 文件**（包括根目录或者 `text_tokenizer/` 中的 tokenizer.json），保存至全新 `/tmp/psm_wma_v3_b3_edge_tokenizer_<unique>/`，不下载完整模型、VAE 或任何 .safetensors/.bin，目标预算约 18MB 文本资产，若需更多非权重 metadata 必须逐项记录。读取资产及 SHA 后记录 revision/commit/size/actual sha256；对于 17,077,500 bytes 的官方 tokenizer.json，应核对上面的 SHA256，任何不匹配先停报。不得使用镜像文件冒充官方 tokenizer，亦不得泄露代理配置/凭据或改写 git 配置。这个新增取数许可严格限制在 B3 CPU Evidence，不等于 broad external install 权限。

**禁止原 Option A 的两项假等价：** 不取 `Qwen/Qwen3-VL-8B-Instruct` 作为 Edge 的正式词表；不把仅 `tokenizers.Tokenizer.encode(text)` 的裸 BPE 编码等同于训练模型的 `text_token_ids`。生产 `BaseVLMProcessor.tokenize_text` 调用 `tokenize_caption`，其 `apply_chat_template` 会写入 user role、generation prompt 和 special tokens，必须纳入 native token-ID parity。

## 4. 独立 CPU-only 最小验收条件

1. **确认身份**：报告 Frozen pair、实际有效的 Edge tokenizer config（`EDGE_POLICY_CHECKPOINT` 解析值、`build_processor_lazy` 参数）、加载的真实 `tokenizer.json` / chat template SHA256，processor/tokenizer class、Python/transformers/tokenizers 版本。不得把 Nano config 作为 Edge 的证据。
2. **真实 native 调用**：优先调用正式 `build_processor_lazy` / `Nemotron3DenseVLProcessor.tokenize_text` 或使用与 fixed Child 实际一致的 `AutoTokenizer.from_pretrained` **加**正式 `tokenize_caption(..., use_system_prompt=False)`；对等价替代路径必须说明为何与目标 `BaseVLMProcessor.tokenize_text` 语义一致，包含 `apply_chat_template(tokenize=True,add_generation_prompt=True,add_vision_id=False)`。**仅 Rust 原始 BPE** 可以当中间诊断，不能通过 Gate。
3. **小范围对照**：复用已经保存的匹配真实 caption，至少普通非空 JSON Prompt 和已触发的 CFG 空 caption；两路径使用相同的最终 text 与 `cfg_dropout_rate=0.1` 证据，输出 OFF/OFF vs ON/ON 的实际 native `text_token_ids` 全值或者 SHA256+长度、无异常且可对照；正常与 dropped 两类都要覆盖。只做已授权 B3 已知缺口，不重跑 9 段、整批数据或 tokenizer 大规模 benchmark。
4. **失败规则**：若真实 processor 缺运行依赖、HF 资产无法可靠获取、配置/哈希不一致或文本顺序不可确认，明确 `BLOCKED`；若匹配输入发生 token IDs mismatch，明确 `FAIL` 并提供首条 mismatch。不得临时安装/降级系统包、修改代码或以 mock 替代后报 PASS。可读取来自不同 processor 的文件做诊断，但不得将其说成正式 native parity。
5. **返回 Evidence**：DS 用一份简洁报告给 GPT，明确真实 class、来源、hash、输入 identity、两种正文/空串的 `native` token IDs/length/hash、对应 flag、RNG/caption witness、第一异常如有。DS 不提交 GitHub；GPT 在后续 evidence-only review 判断 B3/Gate B closure。

## 5. 边界与持续状态

本裁决仅授权**正确 tokenizer 资产的定向只读取数与 CPU 原生 token 对照**。不允许生产代码、Dataset Index、VAE cache、Gitlink、训练 DCP、其他 agent notes、既有 /tmp Evidence 改动；不得启动 GPU/torchrun/4B Policy/Trainer/optimizer/simulator/Fresh/Resume。除新增的独立 `/tmp` asset/probe/log 目录外不应写入共享项目文件。

`GATE_A_CLOSED / B1_B2_C0_D0_CLOSED / B3_NATIVE_TOKENIZER_EVIDENCE_OPEN / C1_D1_E_F_HOLD / FORMAL30K_STOPPED`。这是执行授权，不是本轮 B3 PASS 或 Formal30k Resume 许可。Formal implementation pair 未变，无重复技术审查。
