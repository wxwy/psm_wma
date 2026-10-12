# DS_PRO — V3 D1 N1/N2 决策后双工作流并行（CPU-only）

**日期：** 2026-10-12
**Formal Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`；**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**当前 Gate:** `C1_CLOSED / D1_PRESTEP_NOT_PASSED / FORMAL30K_STOPPED / D1_GPU_HOLD`
**权威 Review:** `docs/collab/chatgpt/reviews/2026-10-12_V3_D1_N1_N2_frozen_fail_and_next_gate_decision_444c232b_e9b8a41.md`
**本轮仅授权：** M0 原 Formal 同模式恢复可行性取证，S0 新前瞻性随机数值一致性 Gate 设计与覆盖口径纠偏。**两项并行，不等待中间 GPT 审核。**

## M0 — 原正式训练实际运行模式溯源（最高优先级）

目标不是 D1 OFF/ON 等价，而是确定 **Original Formal30k iter1–800 是否存在可证实、可完全保持的 Effective Mode**。

- 仅 CPU/read-only 搜索原正式 `formal_verified_index_30k` 的启动 command/launcher 脚本、原进程环境快照（如有）、stdout/SESSION.md/monitor/progress 日志及配置真实资产身份。具体核对 `PSM_V3_COMPACT_CACHED_VIDEO` 和 `PSM_V3_SHARED_EPISODE_CACHE` 在 iter1–800 **实际生效**的值（OFF/OFF 或 ON/ON 或其它），是否途中改过、是否每 Rank 一致、是否与未来完全相同。代码默认值 `1` 和 `config_digest` 不能代替真实 Effective Mode 证据，因为 env 开关未纳入 digest。
- 记录当时 Formal Root/Child、Optimizer inventory、strict DCP、Data/Cache/Verified Index、env/CUDA/NCCL/Torch 各实值；仅引用已关闭 C1 的 State Load 成功 Evidence，**不重新跑 C1 或扫描巨型数据**。锁定原 DCP latest→iter800 并检查 original Job STOPPED。核对下一次 **原 Job** 真 Same-job `warm_start=False` 的路径合同，不构造 Trainer（constructor 写 config）。
- 结论仅能为 `MODE_MATCH_PROVEN`（提供实际可证来源及将来完整复现命令）、`MODE_MISMATCH` 或 `MODE_IDENTITY_BLOCKED`（日志无实证）。若原模式可证明且计划完全不切换优化 flags，提交**独立、明确标记为新 Gate** 的原 Job Resume Readiness 候选；但此轮不得调用 resume、GPU、optimizer 或创建新 Job，不允许自动“因为 C1 通过就训练”。
- 如果 Original Mode 不可证明，保持 HOLD，不以 `PSM_V3_*` 默认=1 推断过去实际使用=1。

## S0 — 前瞻性 D1-S 随机数值一致性 Gate 草案 + 当前口径纠偏

目标：如果确实需要 OFF/OFF vs ON/ON 模式等价，设计 **独立的新 Gate**，不追认当前严格 D1（8 rank FAIL）为 PASS。

- 使用已存在的旧 GPU Evidence，只为**设计规划/限制识别**，不可将后见噪声分布作为已通过的新容差，也不能采用 `median ratio 0.943` 自动推定等价。保留完整 8-rank frozen comparator FAIL ledger。
- 先解决两个覆盖歧义：① 本次报告的 `v2 REF vs REF/OPT vs OPT run2run 296/296` 在只有一次 v2 REF、一次 v2 OPT 的条件下，各实际配对 **run ID** 是什么？如果是自比较或 mislabeled，请更正并声明无有效重复数据。② 前次 FSDP2 Gate `selected=314`（generation289/action5/local20）与现在 `296 unique FQN / 300 captured entries` 差异的**参数/alias/empty-shard/遗漏**逐项映射。两者未解释前，新 Gate 不能声称全参数覆盖。
- 设计 future independent **same-code, same-Shadow, same-data, same-RNG** 的匹配 repeated-runs protocol（不同 run 目录，H1/H2/H3 的新 exact SHA 冻结；每模式有真实同版本重复观测）。分别对8 Rank与 Generation/Action/Local/w0 完整 local gradient/group aggregates 比较，不把数百个相关 FQN 当成数百次独立实验。
- 设计并**预先冻结**：primary input/loss/Local fast-state exact parity，次级 full-gradient group-wise numerical discrepancy measurement（如归一化 L2/方向/极端值）和明确的 Engineering non-inferiority margin、异常条件、failure semantics、所需独立 run 数、GPU 成本。Margin 必须有独立于已有 FAIL 后观察值的精度/训练敏感性依据；不能事后按输出差异选择。若计划 n=2–3/模式，只能作有限工程 smoke，不能宣称统计学等价检验具有高功效；若要统计等价结论，需更多独立重复和预先定义置信区间/误差界。
- 如不具备可辩护的等价边界，则标 `D1_S_DESIGN_BLOCKED`，不追加盲目 GPU。不要把 NCCL/FSDP2 认定为唯一根因。保留 zero/empty shard `grad=weight` provenance false-positive 作为诊断缺陷，不能抹去旧 Comparator BLOCKED 或 FAIL。
- 此轮**仅设计 CPU**，不修改现有正式 Comparison 的容差/源文件；不构造/运行新 GPU harness，不启动新 torchrun，不动 checkpoint。

## 并行交付和止损

M0/S0 各自独立外部 /tmp Evidence 目录，复用历史只读日志；无 GPU、无训练、无 Fresh/Resume、无生产代码变更、无 DCP Save、无 Dataset/Index/VAE 重新验收、不更改原 Formal Job 任何文件。不需要向 GPT 中间轮询，最后统一提交：

`DS_PRO_V3_D1_NEXT_DECISION_PARALLEL_MODE_AND_STOCHASTIC_DESIGN_2026-10-12.md`

应包含 M0 模式证据与结论、S0 输入/数值测试合同设计与必要 GPU 预算、296/314 inventory mapping、v2 run ID 表、更正后的状态边界，以及明确哪些条件才能另行申请正式 Resume 或新 D1-S GPU。原 Formal30k 必须持续 STOPPED。

**STOP after consolidated report.** 任何新的 8×H100 作业或原 Formal30k iter800→801 Resume 需要 GPT 单独冻结并授权，本文件本身不授权。