# DS_PRO — V3 Batch 1 B3 正式训练配置随机 Parity 补证（cfg_dropout_rate=0.1）

**DS 报告日期：** 2026-10-11。**GPT 收件日期：** 2026-10-11。
**Formal Root Implementation:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Formal Child / Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`

> **来源属性：** 本文是用户转交 DS_PRO 总报告的事实记录，非训练服务器原始 JSON/探针脚本文件。原始文件仍位于 DS 主机 `/tmp`，GPT 尚未直接读取这些字节。下列 PASS 是 DS_PRO 的执行裁决，GPT 独立复核与 Gate 结论见关联 Review。

## Scope / authority

- 只读 CPU-only；原 B1/B2/C0/D0 不重跑；不修改生产代码、缓存、Dataset Index、VAE、DCP；不启动 GPU/Trainer/Simulator/Fresh/Resume。
- 证据：`/tmp/probe_b3_cfg_dropout.py`（执行 217.2 秒）输出 `/tmp/psm_wma_v3_batch1_b3_cfg_dropout_report.json`。
- 既有 B3 补证 9 段在 cfg_dropout_rate=0.0 下的 Parity 已记录于 `docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-10_V3_Batch1_B3D0_supplement_owner_relay.md`。

## DS 结论与方法

DS_PRO 报告 `B3 PASS`、无新 production bug，认为新的 cfg_dropout_rate=0.1 配对探针补齐了上一轮 CFG 随机性 Evidence 缺口。

1. 使用正式 Factory 默认 `cfg_dropout_rate=0.1`、`format_prompt_as_json=True`、`max_action_dim=64`、`T=16`；报告携带 expected config_digest 前缀 `70e9867f…`，非生产 full-config/preflight 新测量值。
2. 不再 monkeypatch `_FakeTextTokenizer` 类；改为真实生产 `TextTokenizerTransform` 调用，使用 Python `random.random()` 执行 CFG Dropout。
3. **实际处理器不是正式 Edge tokenizer**：由于本机离线无 VLM/HF 权重，`TextTokenizerTransform` 惰性实例化的 `_processor` 是外部 `b3_cfg_tok.DeterministicCaptionTokenizer`，实现确定性字符级 `caption → token` 编码。此替身用于 token 编码和计数，不是正式 VLM 词表/IDs。
4. OFF/OFF 与 ON/ON 的每组相同请求、种子、Python/NumPy/Torch RNG 状态恢复；比较相同 3 个真实 Episode × 首/中/尾共 9 Segment：CoffeeSetupMug/001744、CloseBlenderLid/000000、CloseBlenderLid/000457。
5. `gather_exact_window_same_index` 使用原生代码比较顺序。

## 9/9 Segment parity（报告数值）

| 字段 | DS 报告 |
|---|---|
| `all_segments_all_equal` | true，9/9 |
| `all_segments_tokens_equal` | true，`text_token_ids` 逐位相等，**使用替身处理器** |
| `all_segments_sequence_plan_equal` | true |
| `all_segments_action_equal` | true，action 和 action_raw |
| `all_segments_evidence_equal` | true，evidence_valid/source_step/visual_summary_prev/executed_action_prev |
| `all_segments_identity_order_equal` | true，slot_id/episode_id/category/provenance |
| `payload_per_key` | 24 keys 报告为 parity，非 video key 相等；video 差异为设计规定的 1B proxy vs 3,133,440B dense，占位行为不同而模型有效输入预期不变 |

## 真实 CFG Dropout 随机执行统计

- 9 段总有效 transform/caption 调用：115。
- OFF 与 ON 各有 17 次 dropout，比例 17/115 = 14.78%；`on_off_dropped_equal=true`、`all_calls_parity=true`，逐调用 dropout 判定对齐。
- 各段 valid 帧数：CloseBlenderLid/000000 cursor0/11/21 = 16/16/9；CloseBlenderLid/000457 cursor0/22/43 = 16/16/9；CoffeeSetupMug/001744 cursor0/7/13 = 16/16/1。合计 115。
- 17 次事件与 p=0.1 的自然随机波动相容。这一事实证明本探针确实执行了非零 Dropout，不证明正式 tokenizer 词表数值。

## 请求、GA 与 same-index

- GA 首窗 member0 八个 slot 0..7：`rows_equal=true`，`binding_epochs=[0]`、`cursors=[0]`、`segment_ids=[0]`、`n_slots_distinct=true`，报告称 OFF/ON 对照中 episode/task/valid_count/terminal 一致。
- native `gather_exact_window_same_index`：index0/7/15 都返回 slot IDs 0..7、consumer_step 分别为该 index × 8；index0 报告跨配置 `slot_ids_equal=true`、`consumer_steps_equal=true`、`slot_ids_sorted=true`。

## 明示的 Evidence 能力边界

**DS_PRO 说明**：本机缺少正式 Edge tokenizer 权重，只验证了 `TextTokenizerTransform` 中真实 CFG Dropout 随机判定、对应输入，以及字符级替身处理器产生的 token 等价。**没有测量真实 Edge tokenizer 词表的 Token IDs。** 文本报告没有附原始探针 JSON、Python 文件全文或独立原始文件 SHA；后续如需补充真实 tokenizer 等价，应单独执行有界 CPU-only 验证，不能回填未发生的测试。

DS_PRO 报告 formal30k 一直 STOPPED；B1/B2/C0/D0 保持以前已经审核的状态。
