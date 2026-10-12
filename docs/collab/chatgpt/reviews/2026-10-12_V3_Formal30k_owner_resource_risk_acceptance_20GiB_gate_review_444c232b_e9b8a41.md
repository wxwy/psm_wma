# PSM-WMA V3 — Formal30k 恢复资源门槛：Owner 明确调整风险偏好（增量裁决）

**日期:** 2026-10-12
**绑定 Formal implementation Root:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**原训练任务:** `formal_verified_index_30k`，C1 已关闭，原 D1 跨模式严格数值 FAIL 仍保留。
**来源:** Owner 在对话中明确指示「先不管别的 gpu 的任务对计算的占用，只要不 oom 就行」；这是**新的资源政策决策**，并非 DS 更新模型/算法实现，更不是推翻旧 CPU/GPU 证据。
**正式结论:** `RESOURCE_GATE_OWNER_REVISED / LIVE_RECHECK_PENDING / FORMAL30K_STOPPED`。新资源口径在 `docs/collab/chatgpt/reviews/2026-10-12_V3_Formal30k_owner_manual_resume_20GiB_resource_gate_supersession_444c232b_e9b8a41.md`，替代旧 `>=25000MiB` **仅就本原正式任务的启动资源判定**。

## 1. 现有真实观测与判定

- 历史同类 8×H100 Formal30k 单卡 CUDA allocated 峰值约 7.9GiB，D1 在当前 Child 下的无 Optimizer Step 真实 Forward/Backward 进程级峰值约 11.4GiB/rank（均为 DS owner-relayed Evidence；因指标/阶段不同，不能当作整个30k训练的严格内存上界）。
- Owner 转交的 2026-10-12 现场资源快照：GPU0=24213, GPU1=24296, GPU2=24295, GPU3=34895, GPU4=34895, GPU5=35511, GPU6=35511, GPU7=24293MiB 空闲。四卡低于旧25000门槛，但八卡全部高于20,480MiB；GPU2/7计算util100%仅影响计算/通信竞争，不独立证明会OOM。
- 基于保守的约12–13GiB per-rank 历史量级和新的 Owner「只以OOM作为关键资源风险」政策，本任务的 **新启动自由显存硬门槛**定为 **20,480MiB/card (20GiB)**。以历史12GiB为例，预留约8GiB增量/外部显存波动余量；这仅是有证据的工程安全边界，**不是OOM不可能发生的证明**。
- 原 `>=25000MiB` 是 DS/评审为减小与外部GPU作业冲突而增设的保守 Guard，并非 GPU 模型最小需求。用户新指令取代**门槛与计算使用率 blocking**，旧Snapshot `RESOURCE_BLOCKED` 是在旧规则下的真实历史判定，保留不改历史日志。**现在不能凭旧Snapshot说 GPU已放行**，须立即启动前重新测量八张 H100。

## 2. 正式 Gate 修改范围

- **取消**“其他任务 util 高/接近100%”“计算负载显著”“其他 job 计算抢占”作为单独的启动拒绝条件。性能变慢可接受；NCCL超时或实际执行故障依然会使训练停止。
- **新硬启动判据**：在 Owner 手动启动的同一 Shell，GPU0..7全部 `nvidia-smi memory.free>=20480 MiB`；其他外部任务如果仍存在，不得强制停机/kill或释放资源；须保证Owner有服务器8卡共享使用权限。任何卡不足或正式Job已有writer => `RESOURCE_BLOCKED`，不启动。
- 尽可能现场取连续两次实时快照（例如间隔10–15秒），确认显存没在暴跌；这不是CPU重测整个数据集，也不改变训练配置。若资源趋势危险，可以Owner选择暂停，避免OOM。
- 训练期间持续观察剩余显存和 rank CUDA allocated/reserved（不可把整卡NVML used混作单进程显存）；建议 free<4096MiB 时视为可能即将 OOM并由Owner及时停止保留日志；OOM/CUDA allocation/NCCL错误/NaN及原Formal Job身份不符都是停机条件，**不自动重试**。采样监控不能保证100%防止其他作业突然分配。
- 不降低world8或改batch/GA/optimizer/compile/dtype/worker数/缓存flag；**正式恢复始终 Dense 0/0 + raw-prefetch workers=0**，不将本资源规则应用到 D1-S 或其它任务。
- 保留已经通过的 R0 CPU preflight证据；若 Root/Child/Index/Checkpoint/Env/原Job身份未漂移，只做即刻轻量身份守卫，无需重跑约198s的Dataset init。正式启动必须保留 `PYTHONPATH=<V3 Child root>`，`--phase resume`原Job及 `config_digest=70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`，以及iter800五组件/8侧车。
- 原始作业曾完成至805、DCP最新800；恢复重放801–805，在iter801检查optimizer_committed/Local状态，在iter900首个新DCP检查五组件与8rank Sidecar。全程仅Owner可手动启动，DS仅协助检查/监控；不批准后台自动启动、循环轮询后自动发车。

## 3. 与原授权文件的关系

- [原 Owner 手动恢复授权](https://github.com/wxwy/psm_wma/blob/V3/docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_iter800_owner_manual_same_mode_resume_execution_authorization_444c232b_e9b8a41.md) 保持，其它防护和严格身份保持不变。
- [此前 25,000MiB 资源HOLD Addendum](https://github.com/wxwy/psm_wma/blob/V3/docs/collab/chatgpt/reviews/2026-10-12_V3_formal30k_resource_hold_release_PYTHONPATH_launch_addendum_444c232b_e9b8a41.md) 仍记录旧快照与此前合理风险偏好；仅 `>=25,000MiB` 与“利用率/计算竞争阻断”的条款被 Owner本次新决策明确覆盖，**其它条款仍有效**。
- 本次只记录 Owner 资源条件改变，不涉及 Child生产代码、C1、D1技术审核，不构成新Formal Pair。**最新状态直到新现场显存/原Job校验完成仍是 `LIVE_RECHECK_PENDING / FORMAL30K_STOPPED`**。
