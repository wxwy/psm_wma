# OWNER AUTHORIZATION — Issue#12 C12200 独占GPU4–7匹配 A/B 20+20步

**授权来源：Owner在2026-10-31明确说：“还有10分钟nottt正式训练会保存到12200，到时候我暂停训练空出GPU4-7，你可以正式测试一把。”** 此授权取代之前仅为正式nw8共享GPU的功能实验豁免；**本次是一个有界、条件性独占资源的匹配性能实验**，并非授权DS去暂停或kill正式Job。实验执行人DS_PRO；GPT设计与审核；仓库代码只由Codex修改，DS可以编辑其仓库外的一次性启动脚本。

**状态：`OWNER_AUTHORIZED_CONDITIONAL_AFTER_FORMAL_JOB_EXIT`。不需Owner再为同一个固定20+20 A/B重复说“授权”；但任何前置条件未满足必须STOP，不允许在原正式Job仍存活时运行。GPT连接的Remote Desktop设备处于Offline，无法直接在训练服务器执行命令，故通过Issue#12/本runbook下发给DS；不要误称GPT已经在机器上启动了任务。**

- Exact candidate Formal Root `fd9021b0908b4b2763b3d02508b1f34df377dc97`、Child+Gitlink `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`（Code Gate `APPROVE_CODE`、CPU真实单Worker`PASS`、共享GPU C9620→9625功能`PASS_REPORTED`）。
- 唯一指定Source DCP为**正式 No-TTT `iter_000012200`**，而非旧C9600/C9620；必须等完整、不可变且正式作业彻底停止。若无完整C12200或身份不兼容，直接BLOCKED，不擅自fallback旧Checkpoint或fresh。
- 必须是相同root/child、相同C12200 clone、相同模型/optimizer/scheduler/trainer/config、world4/B8/T16/GA4、生成式训练/Compact=1、同4卡 `CUDA_VISIBLE_DEVICES=4,5,6,7`、相同Job Identity `no_ttt_packed128_droid_fresh_30k_world4_ga4`、相同120s Timeout语义；**只改变`NOTTT_LOADER_WORKERS`及其必要loader参数（0 vs 8）**。
- Arm A：`nw0`，resume C12200→12220；Arm B：`nw8`，相同DCP C12200→12220，`prefetch_factor=1,persistent=1,timeout_s=120`；**顺序串行，不并发、不得使用0–3卡**。
- 两臂总计**40次optimizer commit**，各20步。每臂首2步不纳入steady summary，剩下18步记录P50/P90/mean；冷启动单独报告。Step Wall与source/transform/data wait/current CUDA stream gap至少分字段统计。

## S0：DS立刻可做只读准备；GPU占用时不能开始

1. 只读确认正式Job `no_ttt_packed128_droid_fresh_30k_world4_ga4`在iter12200的保存过程及`checkpoints/iter_000012200/complete.v1.json`、`latest_checkpoint.txt`、DCP model+optimizer+scheduler+trainer+metadata、4rank `dataloader/rank_{0..3}.pkl`、必要config/job身份。写入前不得检验为complete；**Owner必须先亲自按原方式安全停止正式训练，等所有launcher/rank/其Worker退出；`SIGSTOP`、`Ctrl+Z`只冻结进程且保留CUDA allocations，不算释放GPU**。
2. 只有正式Job不再存活、GPU4–7确实独占、主机CPU可用RAM/Swap/IO与目录空间充足，才满足`S0_RESOURCE_GREEN`。检查每卡进程PID/VRAM/利用率、正式Job PID/Rank/worker不存在，不能以一瞬间0% GPU util替代进程检查。若仍有其它训练/仿真占GPU或Host资源不足：`BLOCKED_RESOURCE`，直接STOP并回报Owner，不杀其它任务，不自动换卡。
3. 只读确认训练服务器中隔离candidate worktree exact root `fd9021b0908b4b2763b3d02508b1f34df377dc97` 和 Child `224c5f3c0bd6911bb49cb6bb0895ba7da53ff822`，Gitlink一致、clean、PYTHONPATH/import来自**候选Child**而非Canonical V3当前Child；固定训练venv、RoboCasa真实source/cache/VerifiedIndex、VAE/Edge配置、旧NOTTT4身份豁免语义。严格检查字段/文件，不可凭路径名称猜对。
4. 使用**只读**完整C12200 DCP源，对A和B分别在有空间的 `/mnt/data` **不同隔离OUTPUT_ROOT**做完整物理/reflink副本及绑定的身份文件/sidecar和独立 `latest_checkpoint.txt`。检查两个克隆与同一个源C12200的hash、文件数、size/identity、**独立inode且无指向正式job的软链接/硬链接**；禁止重写/移动/清理原DCP、原latest、原Job Identity和Cleaner。记录 `CLONE_MANIFEST`、命令/env/exit码/正式源不变见证。禁止使用已近满的`/mnt/data1`保存运行产物。
5. 准备 `OUTPUT_ROOT_A`、`OUTPUT_ROOT_B`、独立Evidence目录，保留原命名 `JOB_NAME=no_ttt_packed128_droid_fresh_30k_world4_ga4`供NoTTT同名合法恢复，不删除源码身份检查、不允许Fresh fallback。S0任一失败就STOP；**不自动降nw8到nw2、不改120s、不借用旧共享GPU A结果**。

## GPU真实执行（S0全绿后由DS立即按本Owner许可执行一次）

Codex隔离候选已发布Launcher `scripts/train_v3_matched_no_ttt_4gpu.sh`；此Launcher在candidate Formal Root `fd9021b0908b4b2763b3d02508b1f34df377dc97` 已核对，接受 `resume EXECUTION_UNTIL`，`--max-iter 30000 --warmup 500 --save-iter 100`固定不变；`EXECUTION_UNTIL=12220` 为**绝对 optimizer 结束迭代**，不是新跑12220步。DS填入S0现场核实的路径，不可猜目录：
```bash
C=12200
STOP_ITER=12220
JOB_NAME=no_ttt_packed128_droid_fresh_30k_world4_ga4
# ROOT_CANDIDATE（exact fd9021b0+224c5f3c）, OUTPUT_ROOT_A, OUTPUT_ROOT_B,
# SOURCE_ROOT, CACHE_ROOT, DATASET_INDEX_ROOT, EDGE_POLICY_CHECKPOINT,
# WAN_VAE_PATH, BASE_CHECKPOINT_PATH, PYTHON，均来自S0确认的真实绝对路径。
# Run A first, only if S0_RESOURCE_GREEN and C12200 clones both verified.
env -u NOTTT_PREFETCH_FACTOR -u NOTTT_PERSISTENT_WORKERS -u NOTTT_LOADER_TIMEOUT_S \
  CUDA_VISIBLE_DEVICES=4,5,6,7 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  NOTTT_LOADER_WORKERS=0 JOB_NAME="$JOB_NAME" OUTPUT_ROOT="$OUTPUT_ROOT_A" \
  SOURCE_ROOT="$SOURCE_ROOT" CACHE_ROOT="$CACHE_ROOT" DATASET_INDEX_ROOT="$DATASET_INDEX_ROOT" \
  EDGE_POLICY_CHECKPOINT="$EDGE_POLICY_CHECKPOINT" WAN_VAE_PATH="$WAN_VAE_PATH" \
  BASE_CHECKPOINT_PATH="$BASE_CHECKPOINT_PATH" PYTHON="$PYTHON" \
  bash "$ROOT_CANDIDATE/scripts/train_v3_matched_no_ttt_4gpu.sh" resume "$STOP_ITER"
# Wait for A complete, verify all rank exits/commits; then ONLY run B:
env CUDA_VISIBLE_DEVICES=4,5,6,7 PSM_V3_COMPACT_CACHED_VIDEO=1 \
  NOTTT_LOADER_WORKERS=8 NOTTT_PREFETCH_FACTOR=1 NOTTT_PERSISTENT_WORKERS=1 \
  NOTTT_LOADER_TIMEOUT_S=120 JOB_NAME="$JOB_NAME" OUTPUT_ROOT="$OUTPUT_ROOT_B" \
  SOURCE_ROOT="$SOURCE_ROOT" CACHE_ROOT="$CACHE_ROOT" DATASET_INDEX_ROOT="$DATASET_INDEX_ROOT" \
  EDGE_POLICY_CHECKPOINT="$EDGE_POLICY_CHECKPOINT" WAN_VAE_PATH="$WAN_VAE_PATH" \
  BASE_CHECKPOINT_PATH="$BASE_CHECKPOINT_PATH" PYTHON="$PYTHON" \
  bash "$ROOT_CANDIDATE/scripts/train_v3_matched_no_ttt_4gpu.sh" resume "$STOP_ITER"
```
两臂共同的RoboCasa dataset，model/optimizer/scheduler/loss，B8/T16/GA4/world4，job name，RNG/CFG，train step count与独占GPU均保持。命令执行前DS把展开后的完整命令/env写入隔离`RUN_MANIFEST`，日志保留到各Arm，不能用未替换的占位符启动。

## 结束标准和证据

- 各20个连续 `optimizer_committed`（iter12201–12220），全部4rank真实恢复/集体提交，worker/Frontier/CFG一致，loss/梯度无NaN/Inf，下一次保存输出完整、无OOM/timeout/污染，Rank PID/worker清理且不残留。**A失败则不要执行B**；B失败保存全日志立即STOP，不自动重跑。
- 每步每Arm rank0原始 `[CorrectedV3][train]` JSONL（不要只贴Progress文本）及 `[NoTTT][cpu_loader]`、每rank log、checkpoint与clone manifest。单独给出冷启动Step12201–12202、steady 12203–12220的step wall P50/P90/mean、consumer/s、data_prepare_ms与Host wait/collate/transfer/forward/backward/optimizer。
- 必须关注 `gpu_data_stall_ms`和`gpu_data_stall_status`（**current CUDA stream gap估计**，不是整GPU idle）；`pending_cuda_event/not_sampled`要保留状态，不能记0。不把`data_prepare_ms`/ `data_wait_ms`/ `raw_wait_host_ms`互换含义。采集Host MemAvailable、SwapPeak、IO、GPU VRAM/RSS、B每rank8 Worker RSS及新Source Arrow retained内存能测则测，不能测标`NOT_MEASURED`。
- 统计只有**两臂互斥同资源窗口**并且没有其它GPU训练/仿真干扰才能标 `MATCHED_A_B`；若环境仍争抢，虽可能提交成功，也只能标`FUNCTIONAL_ONLY_INCONCLUSIVE_PERF`。首包/Optimizer健康优先；不能凭几步wall差提前宣称加速。
- 保留所有原始日志，记录DS source identity、代码/依赖HASH、rank PID和是否与源C12200全匹配；只给GPT审核报告，**不得自动合并V3或恢复/改动正式30k Job**。

## 禁止

本许可不允许：DS停止/kill正式训练（Owner亲自暂停并确保已退出）、对现役Job/Checkpoint/Latest/Cleaner写入、拉取/修改正在训练的工作树、GPU0–3/额外配置、跑Full30k、新增数据集/模型变体、重跑旧CPU301或冷启动/5步GPU功能测试、覆盖V3当前EvalV2 Gitlink、直接修改仓库生产代码（仅Codex）。本次**仅A20+B20两个Arm，不允许失败后自动重试**。
