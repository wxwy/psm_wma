# DS_PRO — V3 D1 最终 CPU Prelaunch Gate（3 个独立工作流并行）

**Date:** 2026-10-11
**Authority:** `docs/collab/chatgpt/reviews/2026-10-11_V3_D1_R1_F1_F2_F3_remediation_evidence_review_444c232b_e9b8a41.md`.
**Formal implementation:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Current verdict:** `F1_PASS / F2_CONDITIONAL_PASS / F3_CONDITIONAL_PASS / D1_GPU_HOLD / C1_CLOSED / FORMAL30K_STOPPED`.

本轮只完成真正 GPU paired-parity 前所必需的最后一批**轻量 CPU-only** 交付，不复测已通过的 F1 / C1 / B1/B2/B3/C0/D0。三个 Workstream 立即并行，最后统一报告，无需每完成一项就请 GPT 审核。

## H1 — 外部可执行 Harness 及静态调用链验收（CPU）

- 将已存在 `/tmp/ds_pro_v3_d1_r1/f3/no_optimizer_harness_skeleton.py` 补成**完整外部程序**（仍存 /tmp，不是生产代码变更），但本轮**不运行它的任何 model/CUDA/GPU 路径**。CLI、工作目录、环境变量、Formal Root/Child 固定 SHA、Snapshot source resolution、日志、首次异常写入、输入和输出 schema 必须完备，保证下一轮可直接按明确命令启动。
- 必须走被 C1 证明的 same-job source：`IMAGINAIRE_OUTPUT_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/` + `job.name=formal_verified_index_30k_shadow`，own `latest_checkpoint.txt → iter_000000800`，`source.warm_start=False`，五组件齐全。Reference/Optimized **顺序**执行，各自全新 8-rank 进程+重新加载完整 800 checkpoint/RNG/Local State；`PSM_V3_COMPACT_CACHED_VIDEO` / `PSM_V3_SHARED_EPISODE_CACHE` 的 0/0 与 1/1 应在 launch 前设定。
- 外部脚本严格镜像生产初始化及 true FSDP2 `model.on_train_start` + `init_optimizer_scheduler` / checkpoint.load / `GroupedLocalMemoryStateCallback` pending→`restore_grouped_local_state`；检查 actual model net scan FSDP2 method registered。不可只恢复权重后从 initial frontier 开始。
- 正确构建 `window.begin();` 用原生 `ExactWindowSegmentProducer` 对每个 GA member 的8 slots生成真实 Segments；用与 `GroupedLocalMemoryTrainer.training_step` 相同的 `native_loss` closure：`collate_grouped_native_batch`→`move_cached_native_batch`→`model.training_step(...,_local_memory_prefixes=prefixes)`→output真实 scalar loss，并用与正式相同的 callbacks/hooks; `run_member` 内真实 `len(payloads)/plan.n_window` 加权且 `grad_scaler.scale(weighted_loss).backward(retain_graph)` 与 `model.on_after_backward()`；GA 0/1 均处理完成。检查 candidate sidecar、loss、grad finite 和 FSDP2 rank shards，然后 `window.abort`；全过程不得调用 `trainer.train`、`trainer.training_step` final GA、`window.finish`、`optimizer.step`、`scheduler.step`、DCP save 或向原 Formal30k 写入。
- Static gate：`py_compile`+AST **调用点和禁用点**校验，不止方法名；解析实际参数签名、kwargs、closure 的环境绑定和异常清理（try/finally）；对脚本提供只做路径/参数/配置身份检查、不构造 Trainer 的 `--static-preflight` / `--help` 入口。静态预检必须能够在 CPU-only 环境运行并输出明确可执行 launch plan；其 `no GPU/no trainer constructor` 属性需实证。
- 每 rank 的 stdout/stderr 和 first_exception 先创建**唯一外部**路径，失败不覆盖早期尝试（C1 四次测试曾丢失日志）。不改生产/测试/launcher代码。

## H2 — 数值比较器/验收标准冻结（CPU）

- 准备外部完整 comparator（可在 /tmp），CPU-only 使用小型自造数值数组/张量进行正反例**逻辑自测**，而非只记录设计。不得把 mock 结果当真实 V3 parity。
- 明确 FP32 loss/grad 与 BF16 tensor 的 **各自**固定 `atol/rtol`，以及 near-zero 的 `max_abs`、相对误差分母、dtype/shape/param-FQN/shard-rank、是否 0/None、非有限、缺失字段、归一化权重、Local candidate FastState 和 RNG 作为输入身份的判据；有疑义先静态记录和报告，不得为了将来跑出来的误差事后改变判据。将 `P0_BIT_EXACT` / `P1_WITHIN_FROZEN_TOL` / `FAIL` / `BLOCKED` 分开。
- 期望真实 `w0_fast_*` 的梯度张量存在性遵守已有 frozen FSDP2 w0 parity Gate：`grad=None` 与 present-zero 不相同；全部须同 rank/FQN 比较。FSDP2 local sharded gradients 不能与全局归约结果混淆。没有 per-shard dtype/shape fingerprint 的比较不能宣称 full-grad parity。
- `P0` 优先 bit-exact（数值完全一致时才标为 BIT_EXACT）；`P1` 只在有相应精度机制和固定标准时标 `WITHIN_TOL`。用户报告原 bf16 `1e-3` 可作为候选，但不能覆盖所有 fp32 项；fp32 阈值必须另行设定且说明来源。不能用一个 `max_abs<=1e-3` 与 `atol+rtol*|ref|` 两种不一致口径混着判。
- 保留每 member/有效 idx 的 `native_loss`、按 `len(batch.payloads)/plan.n_window` 加权的 loss、inner/vision/action/outer 已存在的实际生产字段及其 scope；未执行的 optimizer step 和真实 end-to-end throughput 必须标 `NOT_TESTED`。

## H3 — GPU 资源 Guard / 双模式一次性 Launcher 静态验收（CPU）

- 使用既有 C1 NVML 时间线区分 `device global used`、`external robotwin baseline`、`estimated D1 process delta` 与真实 `torch CUDA max_allocated/reserved`（截至当前仍 `UNKNOWN`）。F2 的 ~6.5GiB 是差分推算；F/B +4–7GiB 是估计，不可以二者之和冒充测量。
- 设计两模式顺序 Launcher（不启动 GPU），运行前查询8卡 free，**候选**启动下限每卡 `>=25,000MiB`、外部 `robotwin_server`稳定且有 Owner 的 GPU 分享许可；低于门槛或外部显存趋势恶化标 `RESOURCE_BLOCKED`。24GiB job allocator reserved 与整卡 used 78,000MiB 只能是预警/退出触发器，不能保证抵御 100ms 采样空窗的 OOM。保留原冻结 alloc flags，不自动注入未证实的 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`。
- 在真正 GPU 检查时，一次仅一个 8-rank process group；两模式分别最多一次启动。任何首次错误、NaN/Inf、OOM/NCCL/资源冲突立即停止此模式并**不启动后续模式**，持久化 first exception 和完整 per-rank stdout/stderr，禁止自动改脚本或重试；下一次 GPU 启动须新的 GPT 审核授权。
- Original Formal30k、C1 Shadow DCP/iter800/latest 均必须在测试前后保持字节/身份不变；只允许 Shadow config.pkl/yaml 被其 constructor 重写、其他诊断输出在 /tmp。禁止原 Formal30k 真训练、Fresh/Resume、GPU sim、D1 Optimizer/Scheduler step 或单独 Optimized step。

## 并行与交付

H1/H2/H3 各自外部独立 /tmp 目录；并行 CPU 静态/测试。一次汇总：

`DS_PRO_V3_D1_FINAL_CPU_PRELAUNCH_2026-10-11.md`

须包含每项 `PASS/FAIL/BLOCKED`、完整可执行 launch CLI（*展示但不得运行*）、单个 Harness hash、Comparator hash、Guard/Launcher hash、脚本与源码定位、明确 per-dtype tolerance 与 false-negative测试、每 rank 日志和失败终止保证。确保无任何 GPU/模型实例化、checkpoint deserialize/写入，原 Formal30k STOPPED。

**STOP after H1+H2+H3**。由 GPT 查看该报告，决定是否单独授权两个顺序 GPU reference/optimized 前向+反向无 step。之前的 C1 已关闭，不再反复测试。