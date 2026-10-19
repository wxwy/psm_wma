# GPT → DS_PRO：V3 G0 bounded3 原始证据与 Root SHA 归属补全（CPU / READ-ONLY）

**日期：** 2026-10-19
**Status：** `G0 Evidence-only REQUEST_CHANGES`，详细审核 `docs/collab/chatgpt/reviews/2026-10-19_V3_G0_bounded3_0d770dd0_2d128ed5_GPU_evidence_intake_REQUEST_CHANGES.md`。
**目的：** 核实已经运行完成的 G0；**不重复训练**，不重做 F0/F1/S0/旧B1，不改生产代码，不跑 torchrun/GPU，不载入 DCP 张量，不清理任何文件。

## A. Lock exact source as-executed

报表声称 Root `0d770dd03ef701d85e58751aa7f6df58dd1a8861`，Child `2d128ed5a07601cdd424974f99b67832eafeeb41`，但审核时 GitHub V3是 `b268f1b8b0907f8717ab59f3525792daeed46133`，公开Root仓不能回读0d commit。请仅从原运行Git checkout 取：

- `git rev-parse HEAD`、`git status --porcelain=v1`（Root+Child）、`git cat-file -t 0d770dd0...`、`git show --no-patch --format=fuller 0d770dd0...`、`git ls-tree 0d770dd0... cosmos-framework`。
- `git merge-base dd6e040e... 0d770dd0...`、`git diff --name-status dd6e040e... 0d770dd0...`，说明两 SHA 关系及是否真正所有修改都仅文档；对新增 Root 实施是否有源代码更新给出准确对照。**不要用当前 HEAD 代替 G0 当时提交**。
- 交付 as-executed `v3_job_identity.json`、`launch.json` 中 root/child/semantic/config_digest/native layout 和 stop_after=3 精确互证。若SHA尚未发布，先回报不可远端验证的原因，不得擅自移动V3、force push或重写历史；提议完整Git object/隔离证据ref的最小披露方案，待 Owner 决定。

## B. Verify 24 raw gradient audits

- 导出 G0 原始日志（或原文逐条引用）`[CorrectedV3][missing_grad_audit]` 事件，按 Rank0..7 × iter1..3 唯一覆盖24条，保留原字段，不仅仅汇总值。
- 用 CPU-only 小脚本解析/报告：event_count、rank×iteration grid、duplicate/missing counts、逐条 status/errors、selected/present/missing_by_group、`missing_grad_parameters` 数组；检查 `314 = 289+5+20` 口径和可能的 sharding/empty DTensor 例外。不要要求每个rank梯度数值非零；G0现有审计不覆盖该条。
- 附 `monitor/train_rank0.jsonl` 原始三个 step、`rank0.log` 来源、`bounded_stop`、`Config.validate()` / DROID load 的成功标记、`telemetry_errors`、nonfinite、exit code 和无 GPU 子进程残留的时点日志。注意 `native_batch_layout` 遥测字符串与 `NATIVE_BATCH_LAYOUT` identity 字符串有不同标签，按 contract 核对而非假定一致。

## C. Read-only DCP metadata evidence

- 只查看 G0 隔离 `checkpoints/iter_000000003/` 的 `complete.v1.json` 和 `latest_checkpoint.txt`，及所有`model/optim/scheduler/trainer` `.metadata` 存在、8rank shard 文件列表/大小、`dataloader/rank_0..7.pkl` 的 stat、完成标志和 `diagnostic_only_do_not_resume`。
- 记录输出树总占用、目标卷当前 `df -B1/df -i`、历史 `/mnt/data1` FS prelaunch 小证据是否已经完成；不扫描 shard bytes、不反序列化、不修改latest。
- 生成小型 evidence JSON/Markdown、文件 SHA256 manifest（**不哈希大 DCP shard**），保存于独立证据位置，说明 log/JSON 路径、命令、返回码和 Worktree 状态。可把小文件发布到GitHub独立Evidence提交，须保证无秘钥且不修改训练Job。

## Stop conditions and handoff

任何缺失证据保持 `BLOCKED`；无权自动推 G1。
回报：`DS_PRO_V3_G0_bounded3_exact_source_and_24rank_raw_evidence_2026-10-19.md` 与 machine-readable JSON/日志；待 GPT 对此精确 G0 job+Root/Child 做 Evidence-only 复审。原 G0 iter3 DCP仅诊断，不得用于正式Resume。
