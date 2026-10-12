# DS_PRO — D1 N1/N2 已有 GPU 证据完整复核（Owner-relayed）

**报告日期：** 2026-10-12
**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**状态：** `REQUEST_CHANGES / D1_PRESTEP_NOT_PASSED`
**证据归属：** 本文忠实记录 owner 转交的 DS_PRO 文本。GPT 未直接读取 DS 训练主机 `/tmp` 的 JSON/tensor/probe 源字节，也未执行新 GPU 计算。N1/N2 是对已有 v1/v2 证据的 **CPU-only 分析**。

## N1 — 8 Rank 冻结 Comparator 原结果保留

冻结数值标准未变：fp32 loss atol 1e-6/rtol 1e-5；fp32 grad atol 1e-6/rtol 1e-4；bf16 loss/grad atol=rtol=2e-2；near-zero 双侧 absmax<1e-7。

| rank | bit_exact | within_tol | fail | blocked | unverified | not_tested | total fields | overall | max_abs_diff |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 0 | 72 | 24 | 263 | 2 | 0 | 2 | 363 | FAIL | 2.155e-4 |
| 1 | 60 | 32 | 255 | 2 | 0 | 2 | 351 | FAIL | 1.980e-4 |
| 2 | 80 | 28 | 259 | 0 | 0 | 2 | 369 | FAIL | 2.793e-4 |
| 3 | 78 | 25 | 262 | 2 | 0 | 2 | 369 | FAIL | 3.526e-4 |
| 4 | 78 | 22 | 264 | 3 | 0 | 2 | 369 | FAIL | 4.272e-4 |
| 5 | 78 | 30 | 256 | 3 | 0 | 2 | 369 | FAIL | 1.869e-4 |
| 6 | 66 | 24 | 262 | 3 | 0 | 2 | 357 | FAIL | 7.248e-4 |
| 7 | 77 | 25 | 264 | 1 | 0 | 2 | 369 | FAIL | 3.676e-4 |

DS 报 v2 Reference/Optimized 均为完整 rank-local FSDP2 梯度 tensor 文件，8 rank 之间每 rank 同名 FQN 对齐，无 REF/OPT 同位 shape/dtype/grad-presence mismatch。原始 rank0 `263 FAIL +2 BLOCKED` 仍原样保留，未放宽数值容差。两个 GA member loss、RNG fingerprint、Local Fast State/Committed slots 报告两模式逐位一致。

**参数身份仍待澄清：** DS 本报告称 `selected_grads` 300 条含 4 w0 重复，唯一 FQN 为 **296**；历史正式 FSDP2 Gate 记录每 rank `selected=314`（Generation289/Action5/Local20）。两个计数的观测定义/参数 alias/遗漏原因未在本报告给出；不能未经映射直接声称已覆盖原 Inventory 的全部314个。

## N1 — 数值 FAIL 与 provenance BLOCKED 分开

报告的全部数值 FAIL 是 fp32/bf16 严格容差比较失败，不能据此证明“模式引入了系统误差”，也不能据此声称满足原数值 Gate。

另外的 provenance BLOCKED 在零/空分片：
- `net.action2llm.bias.weight` [4,2048]，双方 all-zero；
- `net.llm2action.bias.weight` [4,64]，双方 all-zero；
- `net.local_memory_runtime.core.slot_queries` [0,64]，空 shard。
DS 报 `pre_step_comparator.py:149` 的 `identical_to_weight == False` 谓词在这些特殊情况产生误判。报告称外部 Harness `no_step_harness.py:209-238` 实际读取 `param.grad` 并保存真实本地分片；这可支持仅 **provenance test 的缺陷归因**，不消除仍存在的数值 FAIL。

## N2 — 同模式波动统计局限

- v1 REF 对 v2 REF：rank0 full gradient 数据有效 **211/296**，因为 v1 出现跨 rank 文件覆盖85项。
- v1 OPT 对 v2 OPT：rank0 full gradient 数据有效 **7/296**；不能把该数据作为优化模式噪声的可靠独立基线。
- v2 REF 对 v2 OPT：数据完整 **296/296**，冻结 Comparator 跨模式仍 FAIL。
- DS N2 表另列 **“v2 REF vs REF run2run 296/296”、“v2 OPT vs OPT run2run 296/296”**，但同一份报告的时间线只列 **一次 v2 REF、一次 v2 OPT**，末节也明确“无 v2 OPT full-tensor run2run baseline”。这两行需要核对真实 run ID/是否自比较，当前**不得**作为有效的同版本重复运行证据。

DS 给出 6/211 个模式差超同模式差2×的 `moe_gen` FQN，最大比5.76；中位数 per-FQN ratio `0.943231441`，为 `md/(rr+1e-30)` 的描述统计，不是置信区间或显著性/等价检验。211个相关 FQN ≠211次独立实验。

**最终 N2 verdict `NOISE_EQUIVALENCE_UNESTABLISHED`。** 不能证明 NCCL/FSDP2 是唯一波动来源。

## 执行版本 / 证据血缘

DS 报当前外部 Harness SHA `834af9f84cb7e6a1e82bb0b62c8589bdb5309b90513463a64f0772ff9eccad36`，Launcher `8d6338893c41013d02720264da7930c4cae7f103a2f29193229d3a5d1f5ee1f6`，Comparator `c47d55e8cc48b38bbec7c3ee3f55f67e14e6a0435c1de8fd0a98c33b2a614712`；与旧授权冻结哈希不同，旧文件未备份，无法 bytewise 重建差异。v1 的 `gpu_run` 曾归档更名为 `gpu_run_v1_corrupted_rank_overwrite`，v2 再使用 `attempt_01` 名称（报告说没有覆盖原文件，但违背之前要求独立 attempt02 的流程规范）。

N1/N2 只读、没有 CUDA/torchrun、DCP Load/Save、生产代码改动或原 Formal30k Resume。Original Formal Job 仍 STOPPED。详细 GPT 裁决在 `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_N1_N2_frozen_fail_and_next_gate_decision_444c232b_e9b8a41.md`。