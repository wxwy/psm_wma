# V3 Batch1 DS 定向补证 — GPT 增量 Evidence Review

**日期：** 2026-10-11
**Formal verdict：** **REQUEST_CHANGES**（仅 B3 的冻结配方覆盖 Evidence；不是 production defect）。
**Formal Pair：** Root 444c232b976e80ac68cde9e7370e73b9f6410f0e；Child/Gitlink e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c，未变。分支后续 documentation/ledger HEAD 不改变技术审核目标。
**本轮结果：** GATE_A_CLOSED / B1_PASS / B2_PASS / B3_EVIDENCE_OPEN / C0_PASS_STRUCTURAL_ONLY / D0_CLOSED / C1_D1_E_F_HOLD / FORMAL30K_STOPPED。

## 依据与审核范围

- 冻结 Gate B 契约：docs/collab/chatgpt/reviews/2026-10-10_V3_r2_gateB_real_data_pipeline_parity_authorization_444c232b_e9b8a41.md，尤其“使用真实训练配方、reset Python/NumPy/Torch RNG，不能只为强行一致修改冻结 recipe semantics”。
- D0 契约：docs/collab/chatgpt/reviews/2026-10-10_V3_r2_batch1_parallel_B_C0_D0_execution_authorization_444c232b_e9b8a41.md。
- 上次证据缺口记录：docs/collab/chatgpt/reviews/2026-10-11_V3_Batch1_B_C0_D0_evidence_review_444c232b_e9b8a41.md。
- DS 补证源：docs/collab/chatgpt/evidence/2026-10-11_V3_Batch1_DS/DS_PRO_2026-10-10_V3_Batch1_B3D0_supplement_owner_relay.md（用户原样转交信息结构化保存；未经 GPT 读取服务器原始 JSON 或外部探针代码）。
- 固定 Child 定点源码：cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py:178-203；examples/psm_wma_robocasa_corrected_phase5.py:443-450；cosmos_framework/data/generator/action/utils/transforms.py:496-499,655-665（Child SHA 如上）。无重复全仓技术审核。

## Evidence 裁决

**B1 — PASS 维持，附注 CLOSED。** 4 个窗口明确对应 3 个不同 RoboCasa Task Classes，首/中/尾真实窗口身份已补。视频纠正为 dense uint8 [3,17,192,320] 3,133,440 bytes vs zero-stride proxy uint8 同 shape 1 byte。这只说明物理占位内存差异，不代表真实 4B 视觉 crop/token numerical parity，后者留给 D1。

**B2 — PASS 维持。** 本次没有重新运行也无新 Evidence；保留上次已关闭的缓存输入一致性判断。

**B3 — 现有历史 Evidence-only blocker 部分 CLOSED；仍 REQUEST_CHANGES。**
- **已关闭的部分：** DS 此次明确补全 3 Episode × 3 cursor = 9 段 OFF/OFF 与 ON/ON 配对一致，包含 source/evidence causality、terminal remainder 1/9/9、valid masks、visual96、action、原生 token/SequencePlan；native gather 在相同 index0 的两个配置下 8 slots 顺序一致。未发现生产实现错误。
- **当前 blocker（MEDIUM；Evidence-only）：** DS 补证的 B3 实际设置 **cfg_dropout_rate=0.0**；然而同一 pinned Child 的正式 RoboCasa factory 定义在 cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py:178 **默认 0.1**，并在 :197-203 将该值传给 ActionTransformPipeline。实际 Phase5 构造流程在 examples/psm_wma_robocasa_corrected_phase5.py:443-450 调用此 factory 时未指定该参数，所以正式路径为 **0.1**。transforms.py:496-499 说明该随机概率控制整体 caption 置空，直接改变 prompt/token；0.0 比较不是训练随机 recipe 的对照，违反冻结 Gate B 的“不得通过修改配方语义强制对齐”要求。**证据位置：** 上述新 Evidence 文档 B3 节“cfg_dropout_rate=0.0”与 Gate B 的 Execution constraints #4。
- **最小验收条件：** 首先查既有原始 JSON/探针是否已经有 **实际 factory 默认 0.1** 且 OFF/OFF↔ON/ON、seed 对齐的结果；如无，仅复用既有 9 段和计划做一个受限 **CPU-only paired probe**，保持真实默认 0.1，固定并恢复 Python/NumPy/Torch RNG 状态以确保相同随机事件，不要关 CFG。给 9/9 Segment 完整身份/consumer/evidence/action/visual96/token/SequencePlan 对照，以及 native gather same-index 顺序、CFG dropout 触发/数量的可追溯摘要。现有报告尚未明确列出 binding_epoch / cursor / segment_id / GA member request 的跨配置逐项 witness；请先从既有结构或 JSON 中补列，不需要重跑全 Batch。若真实生产数值不一致，报 FAIL+首个 mismatch；若不可执行，报 BLOCKED；不得假定 PASS。
- **性质：** 这是未覆盖正式随机变换的 Evidence blocker，不是已确认 stochastic parity mismatch，不要求任何 production code 修复。

**C0 — PASS（仅结构）维持。** iter800 是最新结构候选，iter700 同为结构候选，rank1–7 scheduler 0-byte shard 与 DCP dedup writer 一致；真实 checkpoint load、optimizer、scheduler、RNG、fast state 和 data frontier 严格续训仍须 C1。不得将 C0 转称为 Resume 已验证。

**D0 — PASS / CLOSED。**
- 旧 blocker“只有第一段跨 worker fingerprint”已由 workers0/2/4 全部 48 段按相同位置逐一一致 + 消费顺序完整一致关闭。另有独立冷 reader 每 workers 8 miss/8 loads，且 48 指纹与 warm nw0 全部一致；warm/cold wall/counters 均已给出。
- 性能选择：本次 warm 与 cold 两种 CPU 测量中 workers0 均最快，暂定 **num_workers=0** 为保守 Resume 参考。不要外推到 8×H100 D1 或证明多 workers 普遍更慢。
- **LOW 测量限制（非 blocker）：** 三组相同 peak_rss_kb=6020060 和 rss_delta_kb=0，若来自同一 Python 进程历史高水位，不足以单独证明不同 worker 独立峰值完全相等。D0 真正硬门槛是数值/序列一致，已由补证满足。

## 立即允许的唯一执行事项

DS_PRO 可仅针对 **B3 正式 0.1 CFG 随机 recipe 配对 parity** 做缺失字段提取，必要时运行上述受限只读 CPU 探针；不得修改训练/生产代码、测试源、Dataset Index、VAE latent、checkpoint 或既有实验资产。既有 B1/B2/C0/D0 不再重复验证；Formal Pair 不变，不重做技术审核。报告须给出原始环境与 pair/seed/source/index 的可追溯 witness，并清楚区分预期 frozen digest 与实际测量的 digest。

**不授权：** C1 DCP load/恢复试验、D1 GPU/FSDP、E/F Simulator/18-task Screening、正式模型 optimizer step、Fresh、Same-job Resume、覆盖原 Formal30k DCP。正式 job formal_verified_index_30k 必须继续 STOPPED。B3 收到符合冻结配方的证据并正式关闭后，再制定有隔离安全边界的 C1/D1 验收。
