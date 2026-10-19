# V3 RoboCasa Local-TTT — Index8 vs Packed128 训练耗时观测记录

**记录日期：** 2026-10-19
**记录性质：** Owner 请求留档；来自 DS_PRO 2026-10-19《G1 Formal Fresh 30k 启动与显存监控报告》，并非 GPT 在训练机原始日志中复算、不是受控/同条件 performance parity Gate，也不是 GPU 授权或训练运行指令。

## 1. 实测报告给出的范围

| 观测指标 | Index8（旧 `formal_verified_index_30k`） | Packed128（新 G1） |
| --- | ---: | ---: |
| `step_wall` | **40–61 s/iter** | **18.7–22.3 s/iter** |
| `data_prepare` | 11.9–13.2 s/iter | 4.5–4.8 s/iter |
| `data_prepare / step_wall` | 约25–30% | 约21–25% |
| `peak_reserved`（rank0） | 9.61 GiB（历史点） | 约29.26–29.86 GiB（初期） |
| `peak_allocated`（rank0） | 7.87 GiB（历史点） | 约24.4–24.6 GiB（初期） |

注：`peak_reserved` 包括 allocator 缓存，**不是**模型参数+梯度+优化器的静态显存；不同模式对应不同动态激活/临时缓冲占用。

## 2. 速度比的适用范围

- 为便于快速估算，以 **Index8 ≈50 s/iter** 与 **Packed128 ≈21 s/iter** 两个近似代表值计算，`50 / 21 ≈2.38`，可概述为 **Packed128 约2.4× 更快（阶段性估算）**。
- 40–61 与18.7–22.3 均是不同训练段的**观测范围，不是全部step的样本均值**；不能由范围推出严格稳态吞吐/端到端30k节省时间。
- Packed128 自报 `gpu_data_stall` 约4.6s为 rank0 当前 CUDA stream 准备数据时的估计间隙，**不等于整机 GPU 空闲时间**。
- index8 与 Packed128 的训练作业、GPU并发和观测窗口可能不同；此对比支持初步吞吐改善，但未构成严格匹配负载与系统条件的性能基准。
- Packed128 加速伴随更高 GPU 内存占用；不得只看step_wall忽视同机并发显存安全余量。

## 3. 运行身份与历史数据锚点（来自 DS 报告）

- Index8：`formal_verified_index_30k`；监控路径（现场）`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/monitor/rank0.log`。
- Packed128：G1 `packed128_droid_fresh_g1_20261019`；据 DS 报告执行时 root `e0121d34592d10323ede480eb3409468a07371ba`（训练机本地）、child `2d128ed5a07601cdd424974f99b67832eafeeb41`、配置摘要 `757de96fa07179dbffc85e9ecf8708959164dc367db68769668cfe9d56ad51e6`。本记录未独立核验该 root 的远端可回读性。
- 新作业实际启动契约：`max_iter=30000` / `warmup=500` / `save_iter=100`，`num_workers=0`，同步producer；报告时约iter110、`iter_000000100` DCP已保存。
- 原始报告中的时间监控路径：`/tmp/g1_30k_gpu_monitor_20261019.tsv`（训练服务器独有，GPT/Codex无直读渠道）。
- 已据 Owner 认可 DS_PRO 负责现场事实与原始证据的核验；本记录为报告观测留档，**不重开 G0/F0/F1/S0，不做新 Gate verdict，不修改生产代码**。
