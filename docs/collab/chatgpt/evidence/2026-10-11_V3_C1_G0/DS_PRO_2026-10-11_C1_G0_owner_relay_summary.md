# DS_PRO — V3 C1 G0 第一轮并行验收：Owner-relayed Evidence

**报告日期：** 2026-10-11；**记录日期：** 2026-10-11。
**Formal Root：** `444c232b976e80ac68cde9e7370e73b9f6410f0e`；**Child/Gitlink：** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`。
**报告原始路径（DS 主机）：** `/tmp/ds_pro_v3_c1_g0_20261011/`。
**来源说明：** 本文件保存用户转交的 DS_PRO 117 行报告的关键事实与路径。原始本机命令输出、`g0_2_checkpoint_evidence.json` 及脚本尚在 DS 主机，GPT 没有直接访问；DS 对全项 G0_PASS 的结论不是 GPT 的正式裁决。

## DS 自报结论

| 检查 | DS verdict | 报告证据 |
|---|---|---|
| G0-1 Git lock | PASS（远端受限） | 本地 Root HEAD 444c232b，Child/Gitlink e9b8a412；Child clean；Root 仅 SESSION.md 和 DS/MM 非代码资产，Git lock 不存在。DS 的 `ls-remote` 被代理阻断。 |
| G0-2 Checkpoint | PASS | Job stopped；`latest_checkpoint.txt` 为 iter_000000800；44 文件，model+optim+scheduler+trainer+8 rank dataloader pkl；无符号链接；14 个小文件 SHA256 以及 config.yaml/pkl；全部源文件属于当前用户、组可写。 |
| G0-3 Environment | PASS | 8 × H100 80GB，外部 `robotwin_server` 占用每卡约 45.6–47.3 GB，GPU util≈0；本机 venv Python3.13.11、torch2.10.0+cu128、transformers4.57.6；资产 Edge、DROID DCP、VAE、RoboCasa source/cache/verified index 均可访问。 |
| G0-4 Load-only static | PASS（DS 判） | 提议以原 `IMAGINAIRE_OUTPUT_ROOT` 创建 `GroupedLocalMemoryTrainer` 再单独 `checkpointer.load()`；Sidecar 先加载 pending，再调用 `restore_grouped_local_state`；不运行 trainer.train。 |

DS 给出的总裁决是 `G0_PASS`，并声明无 GPU、DCP 反序列化、训练或 Resume，正式 Job 仍 STOPPED。

## 重要具体事实

- Formal Job 目录：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/`
- `latest_checkpoint.txt`：`iter_000000800`，15 bytes。各组件 metadata 存在；model 每 rank shard≈1.685GB、optim≈1.424GB，scheduler rank0 14,506B，rank1–7 0B，trainer 每 rank≈22–24KB，8 个 dataloader rank pkl≈1.1–1.26MB。
- File modes `rw-rw-r--`，此时没有检测到 Formal30k 写进程；**现时无人写≠操作系统级不可写**。
- DS 自报磁盘 `/` 378GB 可用、`/mnt/data` 263GB、`/mnt/data1` 338GB；复制隔离所需空间要实际重查目的文件系统。
- DS 没有执行 DCP load；本轮所谓 loader 方案是**静态推断**。
- DS 的原 G0-2 Evidence：`/tmp/ds_pro_v3_c1_g0_20261011/g0_2_capture.py`、`/tmp/ds_pro_v3_c1_g0_20261011/g0_2_checkpoint_evidence.json`。

**GPT 独立源码复核与下一步范围见** `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_G0_evidence_only_review_444c232b_e9b8a41.md`、`docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round2_parallel_P1_P2_P3_snapshot_prep_authorization_444c232b_e9b8a41.md`。
