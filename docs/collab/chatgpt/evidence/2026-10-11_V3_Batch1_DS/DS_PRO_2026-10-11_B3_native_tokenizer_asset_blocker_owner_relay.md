# DS_PRO — V3 Batch1 B3 原生 Tokenizer 资产阻塞（Owner-relayed）

- 日期：2026-10-11。
- Formal Root：`444c232b976e80ac68cde9e7370e73b9f6410f0e`
- Child/Gitlink：`e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
- 来源属性：本文件记录用户转交的 DS_PRO 文本结论；不是原始服务器文件或 GPT 亲自运行结果。DS 的本地 probe、Git 工作区和代理环境由 DS 自行检查，GPT 无直接访问权。

## DS 本轮目标及报告结果

针对上一轮 B3 `REQUEST_CHANGES`，核查原生 tokenizer 资源可用性，以及旧 B1 是否提供真实 native token ID 证据；未重跑 B1/B2/C0/D0，未修改生产代码、数据、DCP，formal30k 保持 STOPPED。

1. **旧 B1 非真实 tokenizer：** DS 检查 `/tmp/probe_b1b2_v2.py:47-51,65-68`，其中 `_FakeTextTokenizer` 固定返回 `text_token_ids=[101,102,103]`，被 monkeypatch 注入。故 B1 旧文字证据不能填补 native Token ID 审核缺口。
2. **DS 的 tokenizer 身份推断：** DS 引用 `action_policy_robocasa_nano.py:182` 与 `nano_model_config.py:141-144`，认为正式 B3 tokenizer 是 `Qwen/Qwen3-VL-8B-Instruct` 加 `Qwen2Tokenizer`。此为 DS 的**初始解释，尚未计入实际 Edge recipe 覆盖**，GPT 审核将在关联 Review 纠正。
3. **本地资产状况（DS 报告）：** 验证主机无 `/gemini` 挂载、本地没有 tokenizer.json/vocab.json/merges.txt；HF cache `nvidia/Cosmos3-Edge-Policy-DROID/text_tokenizer/` 仅 `tokenizer_config.json`、`special_tokens_map.json`、`chat_template.jinja`，无 BPE `tokenizer.json`。直连 huggingface.co 显示网络不可达；既有认证代理 `127.0.0.1:3128` 可用，DS 成功通过代理读取另一 HF 模型的 tokenizer_config.json（HTTP 200）。本文件不记录或传播代理凭据。
4. **工具状况（DS 报告）：** 本地 `tokenizers` 0.13.2 存在，`transformers` 4.53.1 的某套安装与 `huggingface_hub` 0.15.1 存在 API 不兼容（`list_repo_tree`）。真实正式 processor 在本机是否可以完整实例化仍未得到验证。
5. **DS 请求选项：** A 下载 `Qwen/Qwen3-VL-8B-Instruct` 三个 tokenizer 文件至 `/tmp/qwen3vl_tokenizer` 并用 Rust tokenizers 做 CPU Token ID 比对；B 从实际 `/gemini` 或正确的集群/owner 资产源取得文件；C 若无法访问资产则如实 `BLOCKED`。
6. **本轮 DS 状态：** `B1_B2_C0_D0_CLOSED / B3_NATIVE_TOKENIZER_EVIDENCE_OPEN / FORMAL30K_STOPPED`。没有提供真实 tokenizer Token ID 对照，不主张 B3 通过。

## GPT 发现的需要独立纠正的范围

本 Evidence 文件保留 DS 所说的“Nano→Qwen”调查轨迹，不将其变为事实。固定 Child 的实际 `action_policy_robocasa_edge.py` 覆盖了 Nano 的 `model.config`，将 tokenizer 指向 `EDGE_POLICY_CHECKPOINT`，再由 `build_processor_lazy` 路由至 Edge/Nemotron bridge processor。应以实际 *resolved formal Edge recipe* 和权重资产的 tokenizer 文件为准。GPT 纠错裁决、可授权取数路径及最小验收条件参见 `docs/collab/chatgpt/reviews/2026-10-11_V3_Batch1_B3_native_tokenizer_asset_target_and_acquisition_adjudication_444c232b_e9b8a41.md`。

## 服务器原始 Evidence 边界

未接收 DS 宿主机的 `/tmp` JSON、探针源码、HF cache manifest 或代理日志。所列资产访问问题为 DS 转交报告，不是 GPT 自行复测。已经关闭的 B1/B2/C0/D0 维持，B3 未关闭。
