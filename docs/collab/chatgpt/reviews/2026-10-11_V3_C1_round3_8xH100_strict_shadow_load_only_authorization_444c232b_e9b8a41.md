# DS_PRO — V3 C1 第三轮严格 Same-job Shadow DCP Load-only 执行授权

**Date:** 2026-10-11
**Scope:** `C1_R3_GPU_STRICT_SHADOW_LOAD_ONLY`，`P4-MONITOR` 并发于单一 GPU Load，随后 `P4-J` 交叉核对。
**Formal Pair:** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`；Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`。
**Prerequisite:** Round2 P1/P2/P3-ISO 全部 PASS，详见 `docs/collab/chatgpt/reviews/2026-10-11_V3_C1_round2_P1_P2_P3ISO_evidence_closure_444c232b_e9b8a41.md`。
**Official Formal30k:** 一直 STOPPED，不允许对此 Job 写入或启动。
**No authorization for:** `train()`、Forward/Backward、optimizer/scheduler step、save、Fresh/Formal Resume、D1/E/F 或并发第二 GPU 作业。

## 0. 固定 Shadow 与资产

- Original Job：`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/`（仅用于前后不变性 witness，禁止 Trainer init）
- **独立 Shadow Root：** `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/ds_pro_shadow_c1_r2/`
- **Shadow Job Name：** `formal_verified_index_30k_shadow`；Shadow relative path `psm_wma_v3/corrected_phase5/formal_verified_index_30k_shadow`
- **Shadow target：** `checkpoints/latest_checkpoint.txt` → `iter_000000800`
- Config digest：`70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`。
- World=8, H100×8, GA=2, T=16, B=8, K=4, max_iter=30000, warmup=500, save_iter=100, raw15, left_wrist, use_state, H_pred=16, **num_workers=0**。只允许根据当前原正式 config 的真实权威资产解析路径设置必要的 `--edge/--vae/--base-checkpoint/--source-root/--cache-root/--dataset-index-root`。

Shadow 名称和根路径**必须保持原样**；不能使用正式 Job 名称对应的原输出根，也不能将其 symlink/hardlink 到原 Job。

## 1. 负载前同步 Guard（P4-G）

**只做必要的增量核对：** Source/Shadow latest 仍 iter800，Shadow 44 文件、关键 hashes/paths/inodes 仍匹配；确保无 source Formal30k 写进程、Root/Child formal SHA 仍锁定，完整 Digest 在 shadow preflight 仍一致。禁止无意义重复 P1/P2/P3 全套。
- 读取 `nvidia-smi` 的 **各 GPU free MiB**，核对占用来自外部 robotwin_server 的实际变化。DS 的先前报告各卡 free=33827–35509MiB；这不是保证值。没有合法的性能预算/资源许可或显存已不足时，直接 `GPU_RESOURCE_BLOCKED`，勿试错 OOM 或驱逐其他作业。
- 保守启动线：全部 8 GPU 当前 `free >= 30720 MiB`（30GiB）且 robotwin_server 稳定；若任一卡低于该门槛，或有其他 GPU 负载尖峰/owner 不允许共享，停止并报告 `BLOCKED`。这只是用于限制试验的保守运行阈值，**不代表可保证不会 OOM**；记录基于真实 load-only 内存峰值/必要临时 buffer 的预算说明。如已知正式历史 peak 更高，以上阈值必须相应提高而不能硬降。
- P4-MONITOR 在单个 GPU 作业期间并行运行：独立 `nvidia-smi` 观测 GPU 内存/外部进程，及源 Formal Job 的 latest/config、metadata/sidecar、manifest 关键不变性；不得修改源文件。监测时间戳/峰值及外部进程状况。监视器不得触发任何训练或 checkpoint 操作。
- 同步 Guard 失败，不启动 GPU，返回 `BLOCKED` 并保留 P1/P2/P3 已通过裁决。

## 2. P4-LOAD — 唯一 8×H100 分布式 GPU 恢复测试

仅新建外部 `/tmp/ds_pro_v3_c1_round3_*/` 下**load-only probe** 和日志，不修改仓库；只运行一个 torchrun 8-rank GPU 作业，不可在另一个进程并发跑正式恢复/训练。

必须基于固定 Child 真正生产路径，按 `ImaginaireTrainer.train` **模型准备顺序**走到但不进入训练：
1. 使用 `IMAGINAIRE_OUTPUT_ROOT=SHADOW_ROOT`、`job.name=formal_verified_index_30k_shadow`；运行生产 `preflight` 构造配置，先断言本机 **full** Config Digest 等于冻结值。禁止对 shadow 之外的原 Job 构造 `GroupedLocalMemoryTrainer`。
2. `distributed.init()` / config.validate() / config.freeze()；`GroupedLocalMemoryTrainer(config)`。其 rank0 写 config.pkl/yaml 是预期且**只能发生在 shadow job**。记录生成的 shadow config 与原始历史配置的差异，不要求保存文件 bytewise 相等（shadow job 名称不同）。
3. `with model_init(): model=instantiate(config.model)`；`trainer.bind_grouped_stream(planner,producer,config_digest=...,num_workers=0)` 先注册真正 `GroupedLocalMemoryStateCallback`。
4. **必须**调用 `require_dcp_grouped_resume_component(trainer.checkpointer)` 并断言 `True`，设置诊断 trainer 的 `_resume_required=True`，不可跳过生产恢复安全检查。
5. 在正式生产顺序下运行 `model.to("cuda", memory_format=config.trainer.memory_format)` → `model.on_train_start(config.trainer.memory_format)` → `model.init_optimizer_scheduler(...)` → `torch.amp.GradScaler("cuda", **config.trainer.grad_scaler_args)`；保持 8 Rank FSDP/distributed、真实 Optimizer allowlist、原始 Scheduler、EMA 选项。**不可用 fake model/optimizer 或替换 Save/Load API**。
6. 从 `trainer.checkpointer.keys_to_resume_during_load()` 核验 `source.warm_start=False`、路径 realpath 在 Shadow、keys 精确覆盖 `model/optim/scheduler/trainer/dataloader`，`strict_resume=True`、`load_training_state=True`。然后只调用一次 `trainer.checkpointer.load(model,optimizer,scheduler,grad_scaler)`，断言所有 8 rank `iteration==800`。日志记录完整组件 load 过程、missing/unexpected、rank-specific RNG/GradScaler/LR/optimizer-state/inventory。不得对异常自动补载或改为 warm-start。
7. `GroupedLocalMemoryStateCallback` 应将每 Rank Dataloader Sidecar 放到 `trainer._pending_grouped_resume`。必须断言其存在且 iteration800，完整 config/source/manifest/profile 正确；初始化**实际** `GroupedLocalMemoryWindow(model,planner)`（未执行 `train()`，故由诊断入口手动构造），调用生产 `restore_grouped_local_state(window,pending,iteration=800,config_digest=full_digest)`，将 fast tensors、Scheduler、Frontier 恢复到 live，清理诊断 pending，并更新 `_grouped_completed_iteration=800`。只在 all-rank barrier 后对比；不创建未提交的 pending Window。
8. 与 P2 预先记录的 8 rank CPU Sidecar 及下一 GA Window 的固定 identities、slot、binding_epoch/cursor/segment_id、source/evidence chronology、fast tensor shape/dtype/CPU byte fingerprint 做**逐 rank** 对比。规划下一 GA Window 只用真实 `planner.plan_window(window.live.frontier)` 的只读形式，不调用 `window.begin` / `training_step`。已恢复身份不许落回 initial frontier、不可重复 committed segments。
9. 对各 Rank 的 model/optim/scheduler/gradscaler/RNG 作具证据的状态断言；`iteration=800`，下一 optimizer step 应为 801。RNG 需要 `rng_state_{rank}` 的 metadata/恢复 witness，不能因 `dcp.py` 在缺少 RNG key 时跳过它而认定 strict PASS。诊断的 RNG fingerprint 应在 load 后立刻采集，额外随机消费要与 restore 紧密区分。Optimizer 选中参数/状态和 scheduler iteration 必须对齐 checkpoint，不接受 missing/partial。保存摘要哈希/计数/状态值，不将完整隐私 checkpoint 数据上传 GitHub。
10. 禁止 forward、backward、optimizer.step、scheduler.step、`trainer.train`、DCP `save`、正式 job 写入。成功后仅结束 shadow 诊断进程。若 OOM、DCP state mismatch、unexpected keys、显存资源冲突、rank barrier timeout，直接保存**第一失败**和 rank 日志，停止，不 retry/unpickle 部分项，报告 FAIL/BLOCKED。任何进程启动时禁止使用 `--phase resume` 正式 runner；只能外部 load-only harness。

## 3. 同步并行 P4-MONITOR / 最终 P4-J

- 在上述唯一 P4-LOAD 运行期间，另一个只读 CPU 进程并行观测原 Formal Job 不变性、Shadow Path/Latest 指针、GPU 资源和故障日志。可同时保存每个 Rank 的 JSON Evidence；并行监视不能改变 GPU 原有进程。
- P4-J **必须等** P4-LOAD 和 P4-MONITOR 数据准备完毕，再做一次交叉比较：P2 CPU fast-state/frontier/next GA vs P4 GPU live state；源 Formal Job 前后清单/小文件 SHA、latest/config 未变；8 Rank load 状态与 Config Digest 一致。
- 若 P4 的任何一 Rank FAIL，则 `C1_RESTORE_PASS` 不成立；分清 **`FAIL`（实际状态不一致/严格恢复错）、`BLOCKED`（内存/环境/隔离条件无法满足）**，不要借成功 Rank 淹没失败 Rank。
- 只允许一轮基于确定性既有 snapshot 的测试。不能因失败自动更换 checkpoint 为 iter700，也不能重启 Fresh。

## 4. 最终交付与停止

单份报告：`DS_PRO_V3_C1_ROUND3_8H100_SHADOW_LOAD_ONLY_2026-10-11.md`，至少包含：
- frozen pair / shadow root / exact digest / source `warm_start=False`、键集合和版本；
- 8 rank 全部 Model/Optimizer/Scheduler/GradScaler/RNG/Trainer/Dataloader Load 实际结果、第一失败；
- Sidecar pending → GPU Live State Restore 的强行为证据和所有 fast state fingerprint；
- P2 CPU vs P4 GPU 下一 GA member 两阶段身份/顺序、terminal/slot/frontier 对照；
- GPU 各 Rank peak allocated/reserved/free 与其它 robotwin_server 状况，加载期是否出现资源干扰；
- 原 Formal Job 的 latest/config/metadata/sidecar 前后 sha/manifest 和保持 STOPPED；
- `C1_RESTORE_PASS / FAIL / BLOCKED` 与未验证项，证据路径。

DS 不修改生产代码、不提交 GitHub；通过 owner 给 GPT。正式 Review/CODEX_INBOX 由 GPT 下一轮审核落盘。

**授权到第三轮 C1 Load-only 即止。任何 Load 成功都不自动批准 iter801 Forward/Backward、D1/E/F、训练或恢复原 Formal30k。**
