# DS_PRO 执行指令 — V3 No-TTT 正式 Job 现况只读 S0

- 日期：2026-10-29；任务登记入口 **[Issue #10](https://github.com/wxwy/psm_wma/issues/10)**；服务于 [Codex 异步流水线 Issue #9](https://github.com/wxwy/psm_wma/issues/9)。
- **状态：只读现场 S0 请求；当前 Remote Desktop Commander 设备离线，GPT 未运行现场命令。**
- Target 正式 Job 唯一为 `no_ttt_packed128_droid_fresh_30k_world4_ga4`，Owner 告知 iter7600+ 仍在训。新 `no_ttt_compact1_corerun_fresh_20261029_world4_ga4` 的 Fresh10 **不是最终Resume目标**。
- 如服务器不可访问，直接报告 `BLOCKED_CONNECTIVITY`，不从历史值猜测。禁止改/停/杀训练，禁止改变所有权和运行目录。

## 现场 read-only 取证

1. **实际 `NOTTT_LOADER_WORKERS`**：从仍运行的训练 PID/真实 launch command、最晚的实际 `[NoTTT][cpu_loader]` / telemetry / launch.json 交叉核实；区分 `--num-workers 0`（其他控制面）和 `--no-ttt-loader-workers N`（真实 spawn CPU DataLoader）。报告 `CURRENT_NW=0/1/2/4/8/UNKNOWN`，不要根据迭代701–1590历史 nw8 推断现在7600+的值。
2. 仅从现有 `monitor/train_rank0.jsonl`、`rank0.log` 和已写入的 NoTTT loader metrics 取最近10–30个稳定 optimizer committed Step：`step_wall_s`、`data_prepare_s`、`source_read_ms`、`transform_host_ms`、`raw_wait_host_ms`、`forward_s`、`backward_s`、P50/P90 与样本数；缺字段就 `NOT_MEASURED`，特别不能把 `raw_wait` 或零 CPU等待直接当真实 GPU Idle/Overlap。
3. 当前 `last_completed_iteration`、`latest_checkpoint` 以及已有 `complete.v1.json`、4 Rank sidecar manifest 是否存在，最近一次进度/进程 PID 所有权；只读 meta/manifest，不重新 hash 大型 Model DCP payload、不加载CUDA/Checkpoint。
4. 只读 `nvidia-smi` 取当前 GPU4–7 所有进程及同时刻显存，用于观察共存而非阻塞 Owner 已接管的磁盘/retention 策略；禁止直接相加不同进程历史 peak_reserved 后称作即时余量。
5. 限制输出到指定环境、时序、性能字段；不要复制 `/proc/*/environ` 全量、secret/token/代理凭据。允许现场安全只读 shell，**不运行新的模型/GPU计算、性能微基准或改生产文件**，不刷新工作树、`git reset --hard` 或绕过 TLS 校验。

## 输出与后续边界

- 交简洁 `S0_READONLY_REPORT`、取证时刻及时区、数据字段来源/样本数量、真实当前 nw/Compact 值、对未来 nw8+Compact1 的判断只能标 `UNTESTED`。
- 保留 DS 本地4个未推送 Evidence commit，无需现在整批 cherry-pick/强推至 V3；在不更改活训练工作树的单独位置归档。
- 本 S0 完成后 **STOP**。Codex 未来新 Formal Pair 经过 GPT Code Gate，DS 才获得后续**独立 CPU 运行验收**指令；真实GPU/正式Job Resume 仍须 Owner 单独批准。本指令不授权停当前 Job、改worker配置、创建新的Checkpoint、改代码、启动真实GPU/仿真/训练。
