# DS_PRO / Owner — Formal30k 同模式 Resume：20 GiB 显存启动 Guard（覆盖旧25,000MiB门槛）

**日期:** 2026-10-12
**唯一生效的资源门槛版本:** `OWNER_GPU_MEMORY_GATE_V2_20480_MIB`
**正式 Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Job:** `formal_verified_index_30k`（原始任务，不是C1 Shadow）
**前序手动训练执行合同:** `docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_iter800_owner_manual_same_mode_resume_execution_authorization_444c232b_e9b8a41.md`
**本次 Owner 资源裁决 Review:** `docs/collab/chatgpt/reviews/2026-10-12_V3_Formal30k_owner_resource_risk_acceptance_20GiB_gate_review_444c232b_e9b8a41.md`

## 本次唯一修订：资源判据

- 用户明确表示可接受外部GPU任务对计算资源的竞争，**无须检查其他任务GPU利用率作为启动硬门槛**。GPU利用率达到100%不等同于显存不足；只要求本任务GPU可用显存有足够工程余量，不能保证绝对不OOM。
- **旧 `memory.free>=25000MiB/card` 正式被新 `memory.free>=20480MiB/card` 代替，仅适用于当前固定Formal30k Dense0/0 Resume。** 每张H100都必须达标（共8张）。不得把新的20480默认套用到任何D1-S等独立实验。
- 外部进程原样保留，不杀掉其他作业，不修改GPU数量、训练模型、batch、tensor shape、checkpoint、源代码或环境参数；按服务器GPU使用权限共享，计算竞争允许、显存竞争以实时监控防护。
- 如果任一卡 free<20480MiB，或另一writer使用同一个 Formal Job/存在输入身份漂移，就停止并回报`RESOURCE_BLOCKED`。过去GPU0/1/2/7约24.2kMiB的空闲显存**按新门槛理论足够**，但旧快照不是现在的现场值。

## 正式手动启动前的现场轻量门禁

1. Owner/DS 在同一 Shell 再读GPU 0..7的 `index,memory.free,utilization.gpu` 和对应PID内存；可分两次（相隔10–15秒）确认没有快速显存骤降。**只按 free≥20480 判断硬过/不过**；util%只做观察。
2. 核对Root/Child/Gitlink exact `444c232b976e80ac68cde9e7370e73b9f6410f0e`/`e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`，Child clean，Original Job latest checkpoint指向 `iter_000000800`、五组件+8 sidecar，Original仍无writer、配置Digest未变；之前正式CPU `--preflight` EXIT0（已报告），没有环境/身份变化则不用再次耗时地扫数据。
3. 正式命令执行环境**必须先**：
```bash
cd /mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework
export PYTHONPATH=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/cosmos-framework
export PSM_V3_COMPACT_CACHED_VIDEO=0
export PSM_V3_SHARED_EPISODE_CACHE=0
```
再复用前序经CPU验收的原Formal30k同一 `VENV/ENTRY/ARGS`；`--num-workers 0`、`--phase resume`、`--job-name formal_verified_index_30k`、`T16/B8/GA2/K4/world8/max30000/warmup500/save100`。禁止因本次显存政策改变而改任何训练语义。
4. 保证全8rank stdout/stderr/first_exception、首次iter900 DCP写盘空间、原iter800 SHA基线和历史日志保全。只有 **Owner 手动** 启动**一次** `torchrun --max-restarts=0`，绝不触发后台自动或循环重试。

## 训练后的运行防线

- iter801首次optimizer_committed、required grad/local/RNG/scheduler身份与finite、DCP恢复来源检查，旧iter801–805回放；iter900完整DCP及latest pointer验收。
- 训练期间监控每卡free和自身rank `torch.cuda.max_memory_allocated/reserved`。**如任一 GPU free<4096MiB 属显存即将不足的风险信号，Owner应停止并保留现场**；遇OOM、NCCL异常、NaN/Inf、首次DCP异常立即停，禁止自动重试。
- CPU/NVML监控无法拦住所有其它作业瞬间的显存申请；最终OOM风险并非零。其他作业compute util100%本身不应触发停机；它只可能拖慢执行。

## 状态与交付

`CPU_PREFLIGHT_PASS / RESOURCE_POLICY_REVISED / LIVE_GPU_RECHECK_PENDING / FORMAL30K_STOPPED`。

本授权**只代替旧资源门槛和计算利用率硬条件**。之前的原始Job Owner-manual Resume授权及其全部技术/Checkpoint/配置约束继续有效。DS不自动启动；若现场8卡free均≥20480且身份不变，Owner可按原已批准命令启动，无需GPT再为同一显存阈值多开一轮审核。

启动后DS只需返回实际Resource Gate快照、iter801首个Optimizer Commit与iter900新Checkpoint证据；发生OOM/异常则返回first_exception和各Rank日志。
