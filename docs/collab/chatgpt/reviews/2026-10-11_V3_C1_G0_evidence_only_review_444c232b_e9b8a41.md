# PSM-WMA V3 — C1 第一轮 G0 Evidence-only Review

**Date:** 2026-10-11
**Formal verdict:** `REQUEST_CHANGES`（G0-4 安全隔离 Evidence；非生产代码修复）
**Status:** `G0_1_PASS / G0_2_PASS_LIMITED / G0_3_PASS_ENV_ONLY / G0_4_BLOCKED / C1_GPU_LOAD_HOLD / FORMAL30K_STOPPED`
**Formal Root Implementation:** `444c232b976e80ac68cde9e7370e73b9f6410f0e`
**Formal Child/Gitlink:** `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`
**Owner-relayed DS report:** `docs/collab/chatgpt/evidence/2026-10-11_V3_C1_G0/DS_PRO_2026-10-11_C1_G0_owner_relay_summary.md`

## Scope / evidence limitations

本轮审核为 DS 已执行 G0 静态材料的增量 Evidence 审核，**不重复 Formal Pair 代码审查**。DS 的原始 `/tmp` 命令输出及 JSON 尚未可用，GPT 依据 owner 转交摘要与固定 Child 实际生产代码进行定点核对。

GPT 已通过 GitHub Connector 直接读取 V3 远端 HEAD `93b3b225b0913e2e9ddbcc21da344f804b9c660f`，Child branch/Gitlink `e9b8a412b81fa77c0fc1ee5bf04e5c7a8a90cd3c`；因此 DS 本机 `ls-remote` 的代理异常不是当前安全 blocker。Docs HEAD 非新 Formal Implementation。

## G0 子项裁决

- **G0-1 PASS**：DS 报告本地 Root 为指定实现 SHA、Child/Gitlink 同一指定 SHA、Child clean、Root 无 production dirty。远端已独立确认。
- **G0-2 PASS（仅结构/静态无人写）**：iter800 五个组件及 rank sidecar 均存在、必要小文件指纹留存、目前未发现 Formal Job 写进程。要准确表述为“当前未检测到写进程”，不能写作“原 DCP 不可写”；文件模式 `rw-rw-r--` 表明进程仍可能覆盖文件。
- **G0-3 PASS（资产/可见性）**：报告所列 8×H100、必要 VAE/DROID/Edge/Index 可访问；每卡已有 45.6–47.3GB 的 robotwin_server 占用，**不能**由当前 GPU util=0 或空余约 35GB 直接证明完整 8×H100 DCP Load 足够显存或不会干扰其他作业。正式 GPU P3 仍 HOLD。
- **G0-4 BLOCKED：隔离证据不成立。**
  - **Severity: HIGH**（原 Formal30k 配置被覆盖的实质性风险）。
  - **Frozen constraint:** 2026-10-11 C1 G0 执行约束要求“所有可能写操作与原 Job 物理隔离，原 checkpoint/config 不可覆盖”，且本轮不得执行 Load。
  - **生产位置:** pinned Child `cosmos_framework/trainer/__init__.py:138-145` 在 `GroupedLocalMemoryTrainer` 构造时，rank0 执行 `os.makedirs(config.job.path_local,...)`、`LazyConfig.save_pkl(.../config.pkl)` 和 `LazyConfig.save_yaml(.../config.yaml)`。这些写入发生于 `trainer.train()`/DCP load **之前**。
  - **路径因果:** `cosmos_framework/utils/config.py:200-207` 的 `JobConfig.path_local` 取自 `IMAGINAIRE_OUTPUT_ROOT/project/group/name`；`cosmos_framework/checkpoint/base.py:59-70,161-168,213-225` 的 `save_dirname/latest_checkpoint.txt` 同样由该 Job 输出目录构成。若将 `IMAGINAIRE_OUTPUT_ROOT` 设为正式原输出根，就会让 constructor 直接写原 Job 的 config.yaml/pkl。没有运行 train 只能保证不进入 train loop，**不能**保证 constructor 不写文件。
  - **验收条件:** 必须设计并证明真正物理独立的 Same-job shadow snapshot（不使用指向原件的 symlink/hardlink），在单独 `/tmp` 或其他明确独立目录中保留 `psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/latest_checkpoint.txt` 与完整 iter800 必需组件；原文件、shadow 文件的 inode/realpath 不同；sandbox config.job.path_local/save_dirname 指向 shadow；只在 shadow 有可能写 config.pkl/yaml；same-job source.warm_start=False 且 load keys 完整。不准在原输出根调用 Trainer 构造。
  - **性质:** G0 静态方案的安全遗漏，不代表 DCP 资产或实现本身有 bug。无证据证明已造成写入，因为本轮无 Load。

## 对下一轮的精确授权

由于 G0-4 不成立，不批准直接 8×H100 Load-only，也不批准将任何训练目录设为输出。

允许**彼此独立**的下一轮第二阶段只读/隔离准备：
1. **P1 CPU**：配置完整 Digest 与 DCP Metadata/Component 只读核对（不重复 C0 全量扫）。
2. **P2 CPU**：8 rank Local Sidecar 的可信来源/哈希确认，在复制件上反序列化进行状态 schema/frontier/identity/fast tensors 验证，真实 planner 只读预演；不得将 CPU 静态校验冒称恢复 GPU Live Fast State。
3. **P3-ISO**：创建独立 shadow snapshot，复制 `latest_checkpoint.txt` 与完整 iter800 所需组件（必要时小 config 资产）；不使用 symlink/hardlink/复用原 inode，保留 byte/metadata 签名，对其做路径和目录写入靶向 dry-run（**不实例化真实 Trainer/GPU**）。核查 GPU 余量和 8 卡独占/共享风险，只报告是否具备后续加载条件。

上述三项可并行调度，但不得让重 IO 快照复制与 CPU 性能基准混跑；此次没有正式吞吐基准。以单份 DS 报告返回 P1/P2/P3-ISO 的 PASS/FAIL/BLOCKED；不等待它们各自的单独 GPT 审核。

**C1-G0 仍 OPEN/REQUEST_CHANGES**，不得把 DS `G0_PASS` 直接登记为 GPT Gate closure。只有下一轮 P3-ISO 通过且 P1/P2 无身份/数值 blocker，才能单独授权 8×H100 真正 `checkpointer.load` 与 `restore_grouped_local_state`。

绝对禁止原 Formal30k 新训练、DCP 写入/覆盖、直接 `--phase resume`、Fresh、GPU Load、optimizer/scheduler step、数据/index/VAE 改动、reset/clean/force。E/F/D1 保持 HOLD。
