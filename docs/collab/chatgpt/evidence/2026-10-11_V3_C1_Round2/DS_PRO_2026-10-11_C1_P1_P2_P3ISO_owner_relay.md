# DS_PRO — V3 C1 Round 2 P1/P2/P3-ISO 合并验收（owner-relayed）

- 报告日期/登记录入：2026-10-11
- Formal Root：`444c232b976e80ac68cde9e7370e73b9f6410f0e`；Child/Gitlink：`e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
- 执行条件：只读 CPU/物理 Shadow 复制，未 GPU 加载或运行任何训练。
- **来源边界：** 本文据 owner 转交的 DS_PRO 全文结构化摘录；原始 P1/P2/P3 Python 与 JSON Evidence 仍在 DS 主机 `/tmp`，GPT 没有直接查看其文件字节；以下 PASS 均为 DS 独立报告，不代表 GPT 重跑。

## 合并裁决（DS 报告）

| 项目 | DS 判定 | 关键观察 |
|---|---|---|
| P1 配置与 DCP Metadata | P1_PASS | 生产 `preflight()` 重算完整 Config Digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`；16 个小型 DCP/config 哈希均与 G0 一致，iter800 五组件/8 Sidecar 完整；源 Job manifest 232→232，changed: [] |
| P2 Local Sidecar/Frontier | P2_PASS (8/8) | 8 rank pkl 复制后各 SHA256 匹配；受控反序列化与 schema/iteration=800/三项 source/cache digest/config/profile/slot/terminal/fast tensor fp32 finite 校验 PASS；真实 Planner 从已保存 Frontier 给出下一 GA Window |
| P3-ISO Shadow | P3_ISO_PASS | 复制 24GB Shadow Job；44 文件 44 独立 inode/no symlinks，size/mtime 全对照，已列出的 14 个小文件 SHA 与 G0 相等；shadow latest→iter800，生产 `path_local/save_dirname` 计算仅指向 Shadow；原 Job不变 |

## 关键不可变身份

- Frozen Config Digest: `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`
- `cache_manifest_sha256`: `8e63c73b4e07cdbebd6427d9efdd3f2d8b293ecd10511cae25a55c6566f6db88`
- `cache_corpus_digest`: `0e0c05d09722dc7e65da868326ded3cc23a0885e4ed8841e3fbad1ab2e41fac3`
- `source_binding_digest`: `f91b0b477a048beb439f1d73e7414f6b1d2a0307eee54c858d6cd8503ea19020`
- `episodes=9126`, `verified_index_hit=true`; DS P1 的 CPU preflight 约 188.2s。
- `latest_checkpoint.txt` → `iter_000000800`，6 个 checkpoint 历史文件夹中后续仅 700/800 在 C0 被当作完整候选，不做历史重扫。

## P2 的代表数据

- 8/8 rank `iteration=800`, `checks_ok=true`, `frontier_valid=true`, `issues=[]`。
- 每 Rank 8 slots；Frontier epoch 0、assigned_in_epoch 数量分别 866/869/871/882/890/852/863/877；每 rank committed=8。
- 四种 CPU float32 fast state tensor shapes：`(1,256,64)`、`(1,256)`、`(1,32,256)`、`(1,32)`，非终止 slot 存在对应四 Tensor，所有保存 fast tensors finite。
- 真实 `ExactWindowRankPlanner` 预演 next GA window，下一两个 member 具有 `segment_id=1600/1601`；8 rank 总有效窗口分别 247/229/256/232/248/256/228/256（rank顺序）。
- 该结果不等于真实 4B GPU 模型中 `restore_grouped_local_state` 成功，也不等于 iter801 loss/gradient parity。

## P3-ISO 的确切目标

- Shadow root：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/`
- Shadow Job：`psm_wma_v3/corrected_phase5/formal_verified_index_30k_shadow/`
- Shadow latest：`checkpoints/latest_checkpoint.txt` → `iter_000000800`；iter800 model/optim/scheduler/trainer/dataloader 44 文件，均使用 `cp -r --preserve=mode,timestamps` 的物理复制；没有共享 inode/symlink。
- Shadow 与原 Job 名称不同，是安全隔离的**诊断性同 Job 恢复代码路径**，不代表重启原作业。
- P3 `small SHA` 一项有 14 个 DCP 小型源哈希与前次 G0 预期完全匹配；影子哈希对照 28 个对应项。用户提交的表没有宣称所有大型 shard 的完整 SHA256 被比对，因此不扩展该结论。
- `IMAGINAIRE_OUTPUT_ROOT=SHADOW_ROOT`、`config.job.name=formal_verified_index_30k_shadow` 时，正式 `JobConfig.path_local`、`save_dirname`、`_resume_checkpoint` 应只触及 shadow。
- GPU 资源：8×H100 80GB，每卡 used 45581–47263 MiB、free 33827–35509 MiB，外部 robotwin_server 仍占 GPU，util 0%。不能以闲置 util 代替显存预算或与外部 Job 安全共存证明。

## 实际报告中列示的 DS 本机证据

- `/tmp/ds_pro_v3_c1_round2_p1/p1_result.json`
- `/tmp/ds_pro_v3_c1_round2_p1/job_invariance.json`
- `/tmp/ds_pro_v3_c1_round2_p2/p2_result.json`、`sidecars/rank_{0-7}.pkl`
- `/tmp/ds_pro_v3_c1_round2_p3/p3_result.json`、`gpu_query.csv`、`gpu_procs.csv`、`p3_copy.log`
- 迄今仍未真实运行 8×H100 `checkpointer.load()`、Local GPU Live Restore、Optimizer 或任何训练步骤；Formal30k remains STOPPED。

**GPT 增量裁决与下一轮执行权限另见** `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round2_P1_P2_P3ISO_evidence_closure_444c232b_e9b8a41.md`、`docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round3_8xH100_strict_shadow_load_only_authorization_444c232b_e9b8a41.md`。
