# DS_PRO — V3 C1 第二轮并行 CPU 审计 + Shadow Snapshot 准备（执行授权）

**Date:** 2026-10-11
**Current formal pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e` / Child+Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**Only authorized now:** `P1_CPU / P2_CPU / P3_ISOLATED_SNAPSHOT_PREP`。
**Still HOLD:** GPU Load、真实 DCP 同 job 恢复、Forward/Backward、optimizer/scheduler step、D1/E/F、Formal30k Resume。
**Review basis:** `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_G0_evidence_only_review_444c232b_e9b8a41.md`.

## 三个并行任务

### P1 — CPU Config + DCP Meta

- 复用已存在 Index/Cache/官方模型路径，按正式 frozen 参数重建和计算**完整** `config_digest`，与 `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37` 对照。明确报告每项身份来源（model/metadata SHA、manifest/source/corpus、optimizer/schedule、world_size=8、T16/B8/GA2/K4、raw15、H_pred16、num_workers0）。
- 只读核对最新指针、四 DCP Metadata、8 Sidecar、小文件当前 SHA 与 G0 记录相同；不得全量扫 dataset、VAE 重编码或加载大型 tensor。
- 输出 schema、config digest、文件身份差异；真实 mismatch `FAIL`，缺资产 `BLOCKED`。

### P2 — CPU Local Sidecar / Frontier

- 从 G0 锁定的 **可信** 8 rank sidecar 复制到独立新 `/tmp`，核对复制 SHA；仅对本项目可信 pickle 做受控反序列化。报告格式、iteration=800、4 个 fast tensors dtype/shape/finite/数值 fingerprint、8 rank profile/config_digest/source-bound digest、frontier/scheduler/slot/cursor/segment_id/terminal 等。
- 使用真实 `ExactWindowRankPlanner`、冻结 planner seed，从 Sidecar saved frontier 对所有 8 Rank 生成下一 GA Window 的 deterministic identity/order；不得发布 state、修改 Source，亦不得调用 optimizer。
- 不要求 P2 构造 4B GPU 模型，因此只能证明保存的 CPU Sidecar schema/plan；**不允许声称已执行** `restore_grouped_local_state` GPU LiveState。
- 如 Sidecar 字段缺失或与 corpus、profile、rank 不匹配，报告真实 mismatch，不自行修复或跳过。

### P3-ISO — 原 DCP 物理隔离副本与 GPU 条件检查

- 只在新的、与原 Job 完全独立的输出根创建 **shadow job**，保留正式相对布局：
  `<SHADOW_ROOT>/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/{latest_checkpoint.txt,iter_000000800/{model,optim,scheduler,trainer,dataloader}}`。
- 复制完整 iter800 所需每一个原始 shard/metadata/sidecar 与 latest；必要时复制 config.yaml/pkl 作为历史 witness；可使用 **CoW reflink** 或普通物理复制，**禁止** symlink、hardlink、bind 原 Job 可写目录、或通过原路径写入。任何单个 inode/realpath 意外与原文件相同，直接 `BLOCKED`。
- 校验 shadow 文件清单、字节尺寸、所有小文件 SHA 与 G0 一致；大型 payload 可用复制完整性校验/流式 hash（在可控 I/O 时间内）或至少源/目标文件大小与独立 inode 并明确未测 full-hash。保留 origin/shadow 逻辑身份与复制时间戳。
- 静态证明在正式生产 `JobConfig.path_local` 和 `AbstractCheckpointer.save_dirname` 计算规则下，`IMAGINAIRE_OUTPUT_ROOT` 使用 **SHADOW_ROOT** 时，`config.job.path_local`、`save_dirname`、`_resume_checkpoint` 与 `latest_checkpoint.txt` 均落到 shadow，且独立 Same-job source 将为 `warm_start=False`。可以通过无副作用对象属性计算与 `pathlib` 审核，不初始化 Trainer、不加载 DCP。
- 统计 8×H100 当前占用和每卡真实可用显存。DS 报告已有 `robotwin_server` 45.6–47.3GB/卡，占用本身不是错误，但**不能**假定剩下约 35GB 必能加载；提出加载前实际空闲阈值/并发预算和 fail-closed 条件。不杀其他作业、不为试验自动腾显存。
- 记录源 Job 的 latest/config/metadata/Sidecar 前后 SHA、文件清单及是否存在新写入；日志只写外部新目录。

## 并行调度与交付

P1/P2/P3-ISO 是独立 workstream，可同时执行、共享 G0 文件身份 witness，但各自持有独立外部输出目录。P3 大文件拷贝期间 P1/P2 只进行小型 CPU/metadata 检查；避免 I/O 激增。不需中间 GPT 轮询。

单份报告：`DS_PRO_V3_C1_ROUND2_P1_P2_P3ISO_REPORT_2026-10-11.md`。

每项独立 `PASS / FAIL / BLOCKED`，列出 exact Formal Pair、命令与环境、摘要和证据路径、首个异常、原资产前后不变性、剩余风险及是否满足真实 Load-only 前提。结果交 owner→GPT，DS 不提交 GitHub。

**STOP AFTER ROUND2。** 此次不启动 CUDA、torchrun、model.to('cuda')、Checkpointer.load、Trainer、training、D1 或 Formal30k Resume。GPT 审核这一轮后再决定是否单独授权 8×H100 C1 Load-only。
