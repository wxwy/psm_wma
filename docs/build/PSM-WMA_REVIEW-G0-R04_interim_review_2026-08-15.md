# PSM-WMA REVIEW-G0-R04 中期审查报告（2026-08-15）

审查人：Kimi（独立复核）
对象：G0-R04 当前进展证据（R04 仍 `IN_PROGRESS`，本报告为中期核验，非 Gate 终审）
基线：根仓库 `ca60d8a`；cosmos-framework 含 `1c0c691`、`321afc4`；环境候选 `/root/venvs/psm_wma_py313_cu128`（Python 3.13.13 + torch 2.10.0+cu128）；GPU `P1.gpu.medium`（A100 sm_80，40GB）

## 结论

**阶段性属实，但附 1 个 MEDIUM 记录错误须修正**。R04 的 forward/backward PASS 证据链完整可信；当前阻塞精确定位为**容器 32GB 内存配额**，不是 CUDA OOM、不是代码 FAIL。Codex 对 SIGKILL 的性质判断方向正确。

## 已核验事实

- `artifacts/g0/r04/py313_cu128_r04_retry_final.log` 尾部：torchrun `ChildFailedError`，root cause `Signal 9 (SIGKILL) received by PID 1132591`，时间 2026-08-15 01:11:54，发生于 FusedAdam 首次创建 optimizer 状态；GPU 占用约 8.5GiB/40GiB。
- 容器内存上限实读：`/sys/fs/cgroup/memory.max = 34359738368`（**32GB**），宿主机 503GB 与容器无关。1.42B 选中参数的 FP32 Adam 状态（master+m+v ≈ 17GB）叠加进程已占内存即触发 cgroup OOM kill。
- GPU 可用性实测（2026-08-14 21:24）：`nvidia-smi` 可见 `P1.gpu.medium` 40,488MiB；torch 报告 sm_80、39.17GiB；4096² matmul finite。
- 环境迁移记录（`4087833`、`2c814dd`）完整：py3.13/cu130 旧环境备份于 `/root/venvs/psm_wma_py313_cu130_backup`；DCP 资产路径已迁入 `/gemini/code/models/` 并由 SESSION.md:94 正确反映。

## 发现

### MEDIUM-1：SESSION.md:100 把 GPU 阻塞改写为"LD_LIBRARY_PATH 误判"，与受控实测矛盾

- 问题：现记录称"此前 exit 151 / `not enough ratio` 是手工动态库路径改变 Orion 加载链导致的误判"。
- 反证（审查人实测）：2026-08-14 21:19 与 21:24 两次以**完全相同的 LD_LIBRARY_PATH** 运行同一最小张量脚本，前者 exit 151、后者成功（`cuda:0`，结果 14.0）；控制变量后是配额在约 21:20-21:24 之间被激活。此外 `orion-client-ctl run` 的 8 张 A100 全部 `not enough ratio` 是调度层响应，与进程内库路径无关。
- 影响：把时变的平台配额阻塞误记为客户端配置问题，会误导下一次同类排查（让人去改 LD_LIBRARY_PATH 而不是查配额）。
- 最小修复：SESSION.md:100 改为双因表述——"配额曾处于未激活状态（时变，调度层 `not enough ratio` 为证）；LD_LIBRARY_PATH 是否干扰 Orion 加载链未单独证实，当前成功路径为干净激活环境"。
- 阻止 R04 终审：是（记录准确性）。

### LOW-1：R04 失败分流可补两条代码侧出路

- 问题：当前分流只写"需 A100 或多卡 FSDP"。实际上 GPU 侧当时富余 31.5GiB，阻塞在 CPU 内存。
- 最小修复：Runbook/SESSION 补记候选缓解——optimizer 状态直接在 GPU 创建（避免 CPU 侧 FP32 副本）、8-bit optimizer、或申请更大容器内存配额；是否采用由 R04 执行者决定。
- 阻止终审：否。

## 未执行的验证及原因

- 未重跑 R04 训练：Gate 在执行中，复跑属于执行者职责；本审查只核验已有日志与系统事实。
- 未验证"干净环境必然成功"：GPU 配额时变，无法复现 21:19 的拒绝态。

## 待办

1. Codex 修正 SESSION.md:100 的 GPU 阻塞归因（MEDIUM-1）。
2. R04 续跑通过 optimizer.step 并产出 `R04_edge_libero_forward_loss.json` 后，再做 Gate 终审。
