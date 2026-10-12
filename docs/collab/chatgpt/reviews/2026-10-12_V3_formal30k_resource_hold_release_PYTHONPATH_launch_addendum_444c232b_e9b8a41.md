# DS_PRO + Owner — Formal30k GPU 资源等待 / PYTHONPATH 启动补充说明

**日期：** 2026-10-12
**被绑定实现：** Root `444c232b976e80ac68cde9e7370e73b9f6410f0e`; Child/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`.
**当前 Status：** `CPU_PREFLIGHT_PASS / RESOURCE_BLOCKED / FORMAL30K_STOPPED`.
**前序实际手动正式恢复授权：** `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_iter800_owner_manual_same_mode_resume_execution_authorization_444c232b_e9b8a41.md`.
**本次资源报告：** `docs/collab/chatgpt/evidence/2026-10-12_V3_formal30k/DS_PRO_2026-10-12_formal_CPU_preflight_PASS_GPU_resource_BLOCKED_owner_relay.md`. 本文件是**环境与资源 addendum**，不是另开或扩展正式训练 Gate。

## 1. 立即停止状态

4/8 H100（0/1/2/7）free<25000MiB。当前不得启动 `formal_verified_index_30k` 任何新的torchrun/Trainer，也不得降低门槛、换 world size、停止 robotwin_server 或其他Owner的活跃任务、编排自动无限重试。让其他任务正常释放资源或由相关 GPU Owner 自主协调。

**已经完成的 CPU preflight PASS 可复用**，前提是Root/Child/Gitlink、代码工作树、Python环境/变量、Dataset/Verified Index、Original Job DCP最新指针和config digest都未变化；本次无需在资源释放期间无限重复此前约198s的全部初始化。

## 2. GPU 再检查时的单次 CPU-only live Guard

- Owner 先获得与外部 `robotwin_server` 共用8×H100的**明确许可**，并确认无其它Writer使用原 `formal_verified_index_30k` Job。
- 在正式启动的同一会话**重新**读取 `nvidia-smi --query-gpu=index,memory.free,utilization.gpu --format=csv,noheader,nounits` 并保存快照。必须刚好覆盖 GPU0..7，**每卡 free≥25000MiB**，其它工作负载保持稳定。单卡不足 => `RESOURCE_BLOCKED`，只记录并停止；不启动。
- 再次核对 `git -C <root> rev-parse HEAD` = `444c232b976e80ac68cde9e7370e73b9f6410f0e`、`git -C <child> rev-parse HEAD` = `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`、Root HEAD gitlink = `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c` 且 Child clean；原 `latest_checkpoint.txt → iter_000000800`、five DCP组件8Sidecar仍完整、此前小文件SHA未漂移，完整 digest证据持续有效。若任何源/Index/env/DCP变化，则重新运行此前 CPU preflight；未变化只执行轻量复验即可。
- 验证记录 per-rank日志、first error落盘位置和原本有足够磁盘新写iter900 DCP，无权限/目录覆盖错误。

## 3. 使用当前 V3 Child，而非 editable 父仓

Owner 正式命令在同一 shell 中必须先**显式导出**：
```bash
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework
export PYTHONPATH=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework
export PSM_V3_COMPACT_CACHED_VIDEO=0
export PSM_V3_SHARED_EPISODE_CACHE=0
```
然后使用正式执行授权中的**同一 `VENV`、`ENTRY`、`ARGS` 和 `$VENV/torchrun`**；请勿从不同Shell单独复制尾部torchrun命令以免丢失环境。CPU preflight已经以此 PYTHONPATH 实际 PASS，Owner 真启动也必须继承该变量；若导入父仓`e3dc9ec`或Child SHA不符，禁止运行。保留 `--num-workers 0`、原正式 Job `--job-name formal_verified_index_30k`、`--phase resume`、T16/B8/GA2/K4/world8/max30000/warmup500/save100。

不要求 DS 在冻结的Root工作树新增或编辑 `.codex/skills/*.md`、SESSION/TODO 或 review：Docs-only GitHub V3 已有授权，训练服务器保持固定 `444c232b976e80ac68cde9e7370e73b9f6410f0e` 才能通过 Source Lock。读取授权文件可通过Owner转发文本/远端只读文件，不要 `git pull` 或改变当前 pinned HEAD。

## 4. GPU放行后健康检查

正式Owner只允许手动启动一次；`--max-restarts=0`、保存每Rank stdout/stderr和first_exception，不启动其它并行试验。报告 iter801 首次optimizer_committed、Grad/Local/RNG/Scheduler恢复、801–805 replay；iter900 保存 DCP pointer、新8-rank sidecar和模型/优化器/调度器/Trainer组件。若OOM、NaN/Inf、死锁、无效梯度/资源恶化，停机保留证据；不自行修改参数或自动resume。

**既有Owner恢复授权是有条件的，不因本补充文件或CPU preflight PASS而自动开始训练。** 若所有资源条件重查通过，由Owner按原授权手动执行；DS不替Owner启动正式Job。
