# PSM-WMA V3 EvalV2 — RM-ALL-R01 DS_PRO Independent CPU122 Evidence Gate

- 日期：2026-11-02
- **本轮状态：`DS_INDEPENDENT_PASS` / scoped `CPU122 Gate CLOSED`（依据 DS_PRO 完整执行报告）**
- 上一正式代码审核：`APPROVE_CODE`，`RM-ALL-R01 CLOSED`，**保持不变，本轮 formal pair 未变，不重新做技术/代码审核**。
- **唯一正式技术实现对**：Root `e7ce99d7a0bbb7a81ea7afcee7253548687dc223` / Child-Gitlink `c93f2abf4fb27d36176ff8db094379a853cec796`，隔离候选 `v3-eval-v2-replan-ack-r01-20261102`。
- 技术 Gate 依据：`docs/collab/chatgpt/reviews/2026-11-02_V3_EvalV2_RM_ALL_R01_e7ce99d7_c93f2abf_Incremental_Code_Gate_APPROVE_CODE.md`。
- DS 可执行命令依据：`docs/collab/chatgpt/reviews/2026-11-02_V3_EvalV2_RM_ALL_R01_DS_PRO_CPU122_Independent_Acceptance_Handoff.md`。
- **Evidence 来源界限**：收到 DS_PRO 在本会话提交的《EvalV2 RM-ALL-R01 independent CPU acceptance》自包含报告（记录实际服务器绝对路径、JUnit/gate/invocation 文件名、源码与测试 SHA、环境/退出结论）。GPT 本轮只读核对候选 GitHub refs 和上面已有 Gate/执行合同；**不能通过目前连接远程直接读取 DS 本机原始 JUnit、静态日志或重新运行测试**。因此报告为 DS 独立执行方证据陈述，不得误写成 GPT 在训练服务器亲自验证所有原始字节。

## 1. 身份与范围

- DS 报告 Root detached clean `e7ce99d7a0bbb7a81ea7afcee7253548687dc223`、Child detached clean `c93f2abf4fb27d36176ff8db094379a853cec796`，`git ls-tree HEAD cosmos-framework` 的 gitlink 等于 Child；测试前后两个工作树 `git status --porcelain` 均空。
- GPT 远端只读重新核对候选 `v3-eval-v2-replan-ack-r01-20261102`：Root docs HEAD 在本次记录前 `d9473597f500d187ce526ef176d7855446354a6f`；Child branch HEAD `c93f2abf4fb27d36176ff8db094379a853cec796`；Frozen Root commit 的子模块 Gitlink 仍是 `c93f2abf4fb27d36176ff8db094379a853cec796`；官方 V3 的 Git SHA 与原先不同分支隔离，未发生自动合入。
- DS 独立执行路径：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_cpu70_acceptance/cpu122_r01/root`；证据 `.../cpu122_r01/evidence/{green,regression,static}/`。以上为 DS 报告中的服务器路径，GPT 当前未直读这些文件。

## 2. DS reported tests — 指定 CPU Gate 结论

| 组 | DS Python / Torch | 结果 | 证据 |
|---|---|---|---|
| `--phase green` | Python 3.13.11；Torch 2.10.0+cu128 的 CPU-only 执行 | 74/74 passed、0 fail/error/skip；约37.3s | `evidence/green/{gate.json,invocation.json,junit.xml,pytest.log}` |
| `--phase regression` | Python 3.12.13；Torch 2.8.0+cu128 的 CPU-only 执行 | 48/48 passed、0 fail/error/skip；约14.2s | `evidence/regression/{gate.json,invocation.json,junit.xml,pytest.log}` |
| 定向静态 | Ruff 0.12.7 | Ruff check/format 根仓13文件、子仓9文件 PASS；目标文件 py_compile PASS；production/source-only diff --check PASS | `evidence/static/*.log` |

- **Total 122/122**, 独立 DS 检查不是作者自报 122/122 的重复引用，也不是旧 379 用例的再次计数。
- 冻结测试 `ack_history_test.py` ↔ DS copied `frozen_test.py` SHA256 `2114ca1435316be8ec2f4e13383badc0ebedcfee2da7a44966139fdf7ad53354`。
- 新 Child 生产文件 `robocasa_batch_transactions.py` SHA256 `f8d88ab520ccc241e726f917acf5703e764abd4a366f1c5a42409a1413e6a785`。
- DS 采用与 Codex 不同的兼容解释器/Torch minor 版本，不篡改测试和生产文件，实际全部通过；这不构成阻断项，但不等同在真实 GPU/CUDA 环境通过。
- 独立的 Python3.12 Torch 环境在隔离 venv 准备，DS 报告称只向隔离环境安装额外依赖、未触碰共享训练环境；本轮据其报告处理。

## 3. 静态例外及执行边界备注

- DS 报告 `git diff --check <base>..HEAD` 对**全树**发现历史作者已提交 evidence `junit.xml/pytest.log/*.patch` 的尾随空白，**限定在日志/归档，不涉及本次生产源码/定向测试的 diff**。生产源码范围已作 source-only `diff --check` PASS；因此是**非阻断 Evidence 格式备注**，不要为此覆盖历史不可变证据。
- **执行规约小偏差**：DS 报告称以 `nvidia-smi` compute-app PID list 对比已有训练任务。尽管 DS 声称未干预/未新增 GPU 作业，但此前 Owner 明确要求**不查询、管理别人的 GPU 进程**。这种查询不应在后续 CPU Gate/真实媒体 Canary 重复；未报告管理/停止第三方作业。本项记作运行边界提醒，不凭此推翻122项 CPU 结果；不需要额外测试。
- `CUDA_VISIBLE_DEVICES=''`、`COSMOS_DEVICE=cpu`、`MUJOCO_GL=osmesa`、HF offline/cache 隔离已由 DS 报告；GPU0–3、旧 out2/No-TTT、正在运行训练、Checkpoint/DCP 均不应触碰或修改。

## 4. Gate 与后续范围

**本次 DS independent CPU122 验收已完成，按 DS 提交的可追溯执行报告正式记录为 `DS_INDEPENDENT_PASS`，可关闭 CPU122 Evidence Gate。** 没有新的 Code Gate finding，也没有理由重新检查正式 pair 的源码。

**仍未授权/未完成**：新的严格 all-mode generated MP4 在真实 Cosmos / RoboCasa / GPU / FFmpeg 下的小样本 Hardware Canary；它必须单独获得 Owner 授权。正式900EP SR 评测、正式 V3 promotion、旧 out2 Resume 都不包含在此 Gate。

**推荐的下一项独立 Gate（仅待授权，不启动）**：单独新 Run、真实 Local-TTT 既定 checkpoint、RoboCasa 实际 Task，先1 Task×1EP，启用 `save_generated_video: all`，GPU6 Action Server + GPU4 EGL Simulator（避免已实测 GPU7 EGL 路径故障），M1/B1。检验 `replans == generated MP4 == VIDEO_SAVED receipt == media ACK`、每视频全帧可解码、`media_summary.status=COMPLETE`、Local Reset ACK/owned Encoder cleanup，记录 per-Replan 预测延迟、媒体 decode/encode/verify/fsync/ACK 与 Episode walltime；原始旧 H3/out2 不能替代。执行中不查询其他 GPU 进程，不以已有训练为阻塞条件。只由 DS 在得到新的 Owner 硬件授权后执行；故障仅停止自己新 Run。

> **正式 Code verdict 不变**；此次仅独立 CPU Evidence Gate closure 和下一步建议，不代表已实测或批准 GPU/media 正式评测。
