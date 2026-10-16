# GPT → Codex | V3 Packed128 DROID Fresh — P0 Safety Hardening 实施指令（F0→F1）

**Date:** 2026-10-16  
**Execution boundary:** 此指令限于新候选 production code + 聚焦 CPU tests + GitHub SHA；**不授权 GPU / torchrun / 正式DCP / Fresh训练 / Resume训练 / 数据全集扫描**。仅在 Codex 获得 Owner 对代码整改范围的确认后开始实施；Owner GPU/正式训练授权必须独立申请。  
**Codex independent report:** `docs/collab/codex/reviews/2026-10-16_V3_Packed128_Fresh_Training_Independent_Plan_Review.md`（docs-only commit `72c32e07b1335dfe6877bc7ac7edddc861637c32`，verdict REQUEST_CHANGES）。  
**GPT adjudication:** `docs/collab/chatgpt/reviews/2026-10-16_V3_Packed128_Fresh_Codex_plan_five_findings_independent_adjudication.md`（verdict REQUEST_CHANGES，需先执行本整改）。  
**Known unchanged production pair:** Root `2f4dec43eb6b1e35b33a99d844d67813df5922a6` / Child-Gitlink `1d56320c08c56b0f8dd248919d152d81ae12ea7b`. 最新V3 HEAD可能包含审核文档；**先拉取并核对实际远端SHA与Gitlink，不可用此旧 HEAD 覆盖后续其它人的提交**。使用隔离 Child/Root branch，Child 先提交再更新 Root Gitlink，禁止 force push。

## 一、批次裁决

1. **F0 (P0, first)**：正式 Fresh/Resume Job namespace 独占 & 先验证后写配置、明确 corrected Phase5 的规范启动命令/Launcher、`--formal-execution-until` 分段预算且训练 schedule/digest 不变、Resume 语义 config 身份严格绑定。限制目录：Child `examples/psm_wma_robocasa_corrected_phase5.py`、必要的 `cosmos_framework/trainer/__init__.py` 行及局部测试，极简薄launcher可选；不改 grouped Local/FSDP/optimizer数值算法。完成 scoped CPU 自测+提交新 formal pair，然后 **停在 DS_PRO 独立验收/GPT Fresh Review**，不得自行继续 F1 GPU。
2. **F1 (P0, after F0 Gate)**：同步真实 DCP 的 **all-rank Sidecar/Local save completion & atomic latest** + strict per-rank RNG metadata/load 和 deterministic resume 不reseed；局限于 `cosmos_framework/checkpoint/dcp.py`, `checkpoint/base.py`（若不可避免），`trainer/__init__.py`, targeted tests及必要的profile wiring。不要全局重写 `easy_io` 或破坏其它非V3/async/object-store path。F1 独立 Child+Root formal pair, DS CPU独立验证+GPT Fresh Review；**不授权 GPU**。
3. **P1 Index8 可选路径**：Owner 要求最终 `Packed128 DEFAULT + Index8 explicit opt-in`，目前 Phase5仅默认Packed（helper不等于可运行路径）。**兼容入口功能合同仍 OPEN**，另开独立分支/独立Gate，不并入F0/F1、不得阻止新的Packed-only Fresh安全验证。若Owner要求两个模式在同一个正式pair内，先重新确认合并顺序；即使只在旧 frozen Worktree 可跑Index8，也不要谎称新Phase5已提供明确切换。没有任何OOM后fallback。不要为“形式统一”重构已有Packed默认路径。
4. **P1/证据**：Native Loss中aux及Full/Terminal权重、Local FSDP Slow Grad、raw15/mask/action+prefix语义只做 scoped验收；发现真实bug另立修复SHA，不凭B1旧阈值失败直接重写算法。已有 B0/451GB数据集验收和GPU B1 8-job raw captures不重复。

## 二、F0 必须实现的契约、CPU负例

### F0-A：新Job保护与Resume配置身份

- `--phase fresh`：在任何Trainer构造、日志、`config.pkl/yaml`覆盖、正式DCP写入之前，建立真正跨进程原子 namespace claim。rank0仅能独占之前不存在的新目录，验证真实路径/符号链接别名、相对路径逃逸；分布式其余rank收到一致成功/失败结果。不允许existing empty/partial/malformed old job自动复用；失败不改变旧文件的SHA或mtime。旧latest/历史B1全部只读。
- `--phase resume`：只加载完全存在的相同已批准job、canonical原配置/semantic identity；在旧config被重新dump覆盖前 fail-closed 验证exact Root/Child/Layout、本体/动作维数、T/B/GA/K、optimizer FQN/WD skip、raw15、Mask/Loss、precision、seed/RNG策略、DROID/checkpoint source、index/cache source，且尊重实际same-job合法阶段差异（phase、load_path、execution-until、本次job log）**不纳入模型训练语义digest**。保留完整resolved config snapshots供观察，但不强迫fresh/resume的原始Yaml字节全等。
- 新Launcher明确 `examples/psm_wma_robocasa_corrected_phase5.py`，必须8rank world8、DROID base、已冻结Index、num_workers=0、full-segment-prefetch关、Packed128 default。现有旧target_atomic H3F Launcher不是此路线入口，不覆盖/重命名旧脚本以防破坏历史作业。
- CPU 负例：已有latest、仅旧config、仅旧Evidence、existing-empty/partial、新旧目录路径别名、并发两fresh、异SHA/异Layout的resume、resume不覆盖旧config；各有真实CLI/preflight入口而非helper-only mocks，工作树、日志、checkpoint原始字节不变。

### F0-B：正式执行预算与不改变Scheduler

- 新 `--formal-execution-until=N` 或等价新正式参数，可用 `fresh: N=100` 与 `resume: N=500`，但 **configured** `max_iter=30000,warmup=500,save_iter=100` 永远不改变。当前Trainer已有 `_execution_max_iter`，尽量复用；禁以`--max-iter=100`冒充正式分段。
- 执行预算不改变 `config_digest`、DCP训练语义或同Job resumed-compatibility。已恢复iteration >= budget、超上限、负值、失败GA/未commit边界必须 fail-close。必须在完整optimizer/local commit+本步骤到达应保存迭代、对应allrank DCP finalize之后正常退出，不依赖 kill/grep rank0 latest。若用户要求停止101，现有Trainer的非100倍结束会写`iter101`新Checkpoint，需要预算和测试明确；**建议Resume一次到500，在iter101做内部续接观察**，减少额外save/restart。
- 保留诊断 `--stop-after-iter` 的 `bounded_` 专用与 `diagnostic_only_do_not_resume` 规则，不得变成正式Checkpoint的后门。
- CPU负例：fresh100→resume500的目标迭代/一致调度，resume101预算语义及终止保存，启动预算<=已恢复步、超过30000、GA半完成禁止正常退出、save/finalize异常无“成功”记录、原bounded诊断禁止正式resume。正式入口必须真实触达既有Trainer而非独立helper测试。

**F0 Gate输出：**Root+Child新完整SHA, changed-files list, exact commands, measured CPU pass/fail, per-negative output, config hash/digest invariants, fresh namespace unchanged old-byte witness; STOP at DS independent review.

## 三、F1 必须实现的契约、CPU负例

### F1-A：同步 DCP全Rank完整发布协议

- 仅新 corrected Phase5 所需的同步Local checkpoint path：model/optim/scheduler/trainer按DCP既有API；`dataloader/rank_<r>.pkl` 必须每rank先写唯一同FS tmp，再本地flush/fsync+atomic rename。每rank成功后必须经全rank可见的bounded collective/ack；异常应在各rank可收敛上报，不能一方在rank0发布`latest`而另一方失败/仍在写。只在所有预期 8 rank Local和DCP组件验证完毕后rank0写 versioned complete marker，再以tmp/fsync/atomic rename发布`latest_checkpoint.txt`。出现异常时保持之前 **最后完整的** latest 不变，首次无旧latest则仍无指针，永不指向半Checkpoint。
- 注意不能承诺在进程硬死亡后仍可以无条件完成分布式同步；要求失败无误发布+协调超时stop、Owner不误认成功。谨慎保持旧的non-local/async/object-store DCP加载保存语义；不允许静默改变历史DCP bytes/schema。
- CPU负例：gloo 2/多rank延迟最后Rank成功、最后Rank pkl权限/磁盘写失败、rank0快速结束、异常退出临时文件、撕裂latest、旧latest稳定、第一次save失败latest absent、反复save pointer递进、async profile路径旧行为不回归。要求直接集成调用保存路径，不只mock marker helper。运行结果必须可由另一个只读reader确认而非仅断言日志。

### F1-B：same-job strict RNG & restore semantics

- 针对该新Fresh profile，same-job strict resume必须读取每rank完整 `rng_state_<rank>` (torch CPU, torch CUDA, numpy packed length/bytes, Python random packed length/bytes)；缺任意整体key/leaf都抛异常 **在下一Consumer前**。Fresh DROID model-only warm start允许无训练RNG；不得把两者混同。
- 成功加载RNG后即使 `torch.are_deterministic_algorithms_enabled()`为True也不可重新 `misc.set_random_seed()` 覆盖，且应有明确resume标志而非根据`iteration>0`的脆弱猜测。
- CPU负例：rng整rank缺失、单leaf缺失、合法同rank完整状态、crossrank错绑、fresh seed相同、deterministic=True strict_resume下一次Python/NumPy/Torch采样连续；假RNG字段不应绕过。必要时GPU恢复第一消费前额外记录小而非全量的状态witness，但本指令无GPU许可。

**F1 Gate输出：**相同新实现精确Root+Child、源码diff、allrank时序/失败矩阵、RNG Next-Draw witness、既有功能回归; DS_PRO只读独立CPU验收、GPT新SHA fresh incremental review。任何生产修复失败 => `REQUEST_CHANGES`，不得直接训练。

## 四、与DS/Owner分工和下一Gate

- Codex做 F0/F1 提交/CPU自测；**仅在明确允许后实施**，不改冻结Index8 SOURCE `b159f459/937066ff`、TARGET `c4731bca/c8dabbb3`、诊断a323。不得force push或覆盖他人历史提交。相关证明提交 `docs/collab/codex/reviews/` / scoped request/evidence，别将文档提交误记为生产SHA。
- DS_PRO不修改GitHub，仅为新SHA做独立CPU验收；可并行**只读**确认持久磁盘空间和样本RoboCasa Action ABI/index/S0/Full/Partial已有权威，不需要另跑B0/451GB。
- GPT独立审批每个新SHA；Owner只有在F0/F1和S0 CPU gate明确通过后才考虑授权最省 GPU路径：**Fresh to100（前3步自动健康见证） → 全Rank完整Save → Resume至500（iter101首更新续接见证）**，配合首个真实RoboCasa小闭环，后续再决定2000/30k。
- 本指令不构成 `APPROVE_PLAN`、CPU Gate通过、GPU训练授权、Formal30k授权、Gate M迁移批准或旧B1数值标准的任何豁免。
