# V3 No-TTT Compact=1 共存 S0/S1 — Evidence-only 增量复审

- 日期：2026-10-28。Gate `V3_NOTTT_COMPACT_CORESIDENT_SECOND_JOB`。
- **Verdict：`REQUEST_CHANGES`（仅 Evidence provenance），`S1_REPORTED_PASS_CANDIDATE`；`R1_STORAGE_HIGH_OPEN`，**`S2_NOT_AUTHORIZED`**。本轮不重审没有变化的 No-TTT 代码。
- Formal No-TTT Root历史基线：`49df7f3c2e0ba8ef5871f9dd490e41fbc3dc5da9`；Child/Gitlink：`746c5cf2f2324104a62fb71510343aa40d3976c5`；DS运行时 Root：`4cf90fb486db9c8e2a4b93aaa7d9f5438296f642`。后续 Root仅有其它评测/账本变更。
- Frozen contract：`docs/collab/chatgpt/requests/2026-10-28_V3_NoTTT_Compact_Coresident_Second_Job_StagePlan.md`；上轮审核：`docs/collab/chatgpt/reviews/2026-10-28_V3_NoTTT_Compact_Coresident_S0_S1_Evidence_Review.md`。
- **本轮新增直接证据**：用户粘贴全文194行，原文归档 `docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1_remediation_user_paste.md`。这是用户提供的 DS_PRO 汇编，**不是 DS服务器上的原生JSON/JSONL/完整Manifest，也不是 GPT运行的真实模型测试**。
- DS宣称同步提交 `docs/collab/chatgpt/evidence/2026-10-28_nott_compact_corerun_s0_s1.{md,json}`，但独立查询 GitHub origin/V3 时两文件仍`NOT_FOUND`（可能只提交在DS本地，未推送）。禁止把粘贴汇编冒充已在远端的机器原始工件。

## E1 — 加强的运行证据 / ORIGINAL_ARTIFACT_PENDING

- DS转录 `launch.json` 关键值：`phase=fresh`、`formal_execution_until=1`、`execution_stop_after_iter=1`，RoboCasa左腕、T16/B8/GA4、raw15/state15、20Hz、17 observation frames；独立新Job namespace。
- `v3_job_identity.json` 给出 `corrected_phase5_f0_v1`、`max_iter=30000`、`save_iter=100`、`strict_resume=true`、4GPU FSDP2、训练语义/数据Cache/Index witness（为关键字段摘录，不是完整原始 JSON）。
- `rank0.log` 的 `iter1 optimizer_committed` 和 `checkpoint_save_ms≈14846.84ms` 原句已转录。`train_rank0.jsonl` 仅提供选字段表格而非完整JSONL行：`outer_loss=14.9374676`、`action_loss=1.2275960`、`vision_loss=0.2661506`、`grad_norm=3.7072084`、missing0/nonfinite0、`compact_cached_video=true`、`valid_consumers=512`、`peak_reserved=29.8398438GiB`。
- **E1结论**：真实完整训练一Optimizer Step成功得到较强直接文本证据；但原先约定的DS原始 `s0_s1.json/md` 远端仍缺，`E1=REPORT_SUPPORTED/ORIGINAL_ARTIFACT_PENDING`。不重跑S1，补现成文件即可。

## E2 — DCP与Old Job证据 / RAW_MANIFEST_PENDING

- 汇编 `complete.v1.json`：`schema=psm_v3_sync_local_v1`、`complete=true`、`iteration=1`、world4、model/optim/scheduler/trainer组件和4RankSidecar，配有大小及meta摘要；旧Job iter4826–4928持续`optimizer_committed`，未报告NaN/NCCL/缺失梯度，rank0峰值35.658GiB稳定。
- **新增审计发现**：文本声称“complete.v1.json 完整”，然而 `sidecars["3"].sha256="read_from_complete_v1_json"` 是占位而非SHA256，不可能作为恢复验证中的真实完整 Witness。冻结 Child `cosmos_framework/checkpoint/dcp.py` 的 `validate_checkpoint:1499-1527` 会逐rank核对文件大小/sha256。需取得已有真实 `complete.v1.json` 的rank3完整sha，不要生成新数据、不要为本轮重Hash整个24GB DCP。
- Rank1–3 `peak_reserved` 均诚实标 `NOT_MEASURED`，本 Gate不强制重跑S1去补造历史；S2新资源准入必须独立获取四Rank即时峰值和NVML共存空间。
- 旧Job“持续Commit且无错误”只能证明未见故障，**不证明零速度损失**。E2 `DCP_STRUCTURE_REPORTED_PASS / RAW_MANIFEST_PENDING`。

## R1 — HIGH：存储与后台清理策略仍阻断 S2

- DS磁盘信息：/mnt/data 7T用99%且可用`97G`；/mnt/data1可用`105G`也99%。新Job iter1 checkpoint组成文件合计 **24,877,757,549 Bytes = 23.169 GiB**（按粘贴model、optim、scheduler、trainer、sidecars字节数计算）；旧Job已有4个Checkpoint≈93G，新Job1个≈24G。
- **算术纠偏：整千Checkpoint在30k只有30份，不是300份**。新Job如果保存30份`≈695 GiB≈0.679TiB`，不是报告`7.2TB`；尽管低10倍仍远超当前`97G`可用空间，旧Job整千也继续增加持久空间。必要时另计latest、临时stage与失败回滚容量。
- **Inodes**：13320266/234422272 = `5.68% 已用、94.32%空闲`；原文“free(6%)”对应已用比例，不能理解为inode耗尽。
- **Cleaner现状/授权尚不透明**：据DS报告，PID2654855的`nottt_ckpt_cleaner_loop.sh`每30分钟对旧Job自动清理，已删掉`iter4700/4800`释放约47G；保留`latest+整千+未完成`。清理脚本未在当前V3远端找到，Owner授权记录亦未提供，不能断言未经授权也不能默认授权。此为**当前发生的破坏性Checkpoint文件操作**，不等同本轮DS只读取证；不得无Owner批准修改/停止Cleaner，但在授权/安全保护范围确认前不能将其视为长期合规存储方案。
- 仅改新Job `save_iter` 可能影响冻结身份/Resume；搬到/mnt/data1余105G无法解决30k长期需求。S2之前需要Owner批准对**新/旧两Job**分别列明哪些恢复点必须保留、自动删除范围、失败rollback/原子保留、清理窗口及最小磁盘余量，或扩充存储。
- **R1=HIGH_OPEN；S2 resume10/100/30000均`NOT_AUTHORIZED`**。此结论不因整千数量勘误而自动放宽。

## Incremental remediations（不重跑S1）

- DS只需提交现成源 `s0_s1.{md,json}` 与完整 `complete.v1.json`/rank3 sha及已有 rank0 原始JSONL（可以隐去敏感路径/用户名）；历史Rank1–3峰值若未测直接标`NOT_MEASURED`，不许补造。
- Owner单独确定正在运行的 Cleaner 的安全/删除权限与长期磁盘保留政策；旧Job和当前新Job均不得在本Review下被停训、Resume、自动清理或改变生产配置。
- CPU Compact parity Gate此前`CLOSED`；独立同权重同Frozen Batch的GPU Forward/Loss/Gradient Parity仍`NOT_RUN`，Fresh1成功不能替代。
- **Gate summary**：`E1_EVIDENCE_PARTIAL`，`E2_EVIDENCE_PARTIAL`，`R1_HIGH_OPEN`，`S1_REQUEST_CHANGES_EVIDENCE_ONLY`，`S2_NOT_AUTHORIZED`，`NO_PRODUCTION_CHANGE`。
