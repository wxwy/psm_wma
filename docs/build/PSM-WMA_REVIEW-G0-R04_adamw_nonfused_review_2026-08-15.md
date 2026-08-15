# REVIEW — G0-R04-ADAMW：非 fused AdamW 单步诊断

- 审查人：Kimi（独立只读审查，未修改文件、未运行训练）
- 日期：2026-08-15
- 对象：cosmos-framework 提交 `c8e65d6`（允许标准AdamW使用非fused优化器）；证据日志 `artifacts/g0/r04/adamw_single_step_retry2.log`
- 前置：`PSM-WMA_REVIEW-G0-R04_interim_review_2026-08-15.md`（SIGKILL 根因 = 32GB cgroup 容器上限，fused Adam 状态分配撞顶）

## 审查结论

**APPROVE**

代码最小修改正确，约束边界符合要求；日志证据链完整覆盖 DCP load → forward/backward → grad clip → optimizer.step → checkpoint → 正常退出；GPU/RSS 峰值数字本身无法从机器可读产物复核（见 MEDIUM-1），但不影响"非 fused AdamW 单步可跑通、SIGKILL 未复现"这一 Gate 结论。

## 逐项核验

### 1. optimizer.py 最小修改（c8e65d6，+11/-11 行）

- 唯一行为变更在守卫条件：`cosmos_framework/utils/generator/optimizer.py:377`
  `if optimizer_type.lower() not in ("adam", "adamw") and not optimizer_kwargs.get("fused", False): raise`
- FusedAdam 约束未变：`fusedadam` 不在白名单，仍需 `fused=True`；其本身即 NVIDIA FusedAdam（`optimizer.py:32, 106`），fused 由构造保证 ✓
- Muon/Dion2 约束未变：`muonwithauxadamw`/`dion2withauxadamw`（`optimizer.py:28`）同样不在白名单，非 fused 仍被拒绝 ✓
- 其余 hunks 均为 docstring 同步（330-338、358-364、506-511 行），无逻辑变化 ✓
- 运行配置确认显式 `fused: false`、`optimizer_type: AdamW`（`artifacts/g0/r04/adamw_single_step_retry2/.../config.yaml:370` 及 optimizer 段）✓

### 2. 日志证据链（adamw_single_step_retry2.log，89 行）

| 环节 | 证据（行号） |
|---|---|
| 分布式/配置初始化 | 6-11（config.pkl/yaml 落盘） |
| LIBERO 数据 | 56（split='train'，375/379 episodes，94250 valid indices） |
| 参数选择 | 63-67：549 trainable、selected 294；组 lr=5e-05（1,414,921,408 元素）+ 2 个 0.00025 组 |
| DCP warm-start load | 70-79：`Cosmos3-Edge-Policy-DROID-dcp`，kept 549 / dropped 0，216.7s 完成 |
| forward/backward + grad clip | 85：`clip_grad_norm/video/global: 22.87500 (iteration 0)`；GradClip `force_finite: True`（19 行），norm 有限 ⇒ 梯度 finite |
| optimizer.step | 无独立日志行，但 86-88 行 step 后 checkpoint `iter_000000001` 保存成功（含 `model/optim/scheduler/trainer` 四件，已核实目录），step 必然已执行 |
| 正常结束 | 89：`Done with training.`（12:23:27），全程无 Traceback/OOM/SIGKILL |

### 3. 资源峰值

- GPU 峰值 `40192/40488 MiB`、RSS 峰值 `16,497,588 KB`：**不出现在日志或 DeviceMonitor 产物中**（DeviceMonitor `every_n=200`，单步无采样，目录为空；已核实）。数字来源是 Codex 外部采样，仅记录在 `SESSION.md:124`。
- 与 interim review 的 32GB cgroup 根因一致：RSS ~15.7GiB < 32GB 上限，SIGKILL 未复现，方向合理，数字可信但不可机器复核。

## 发现（均不阻止本次 APPROVE）

- **MEDIUM-1**：GPU/RSS 峰值无机器可读产物。建议后续 R04 正式 Gate 运行时把 DeviceMonitor `every_n` 调小到 ≤1 或外采 nvidia-smi/`/proc` RSS 落 JSON，否则资源判据永远依赖文字声明。
- **LOW-1**：loss 值未入日志（`training_stats` callback 因缺 `_target_` 被跳过，日志 32-33 行）。单步诊断可接受；R04 正式 PASS 需要 loss finite 的显式记录。
- **LOW-2**：`SESSION.md` 中 R04-ADAMW 旧块"待执行"与新块"单步完成"并存，且"保留 PID 2134986 暂停状态"已过时（该任务已由 Kimi 侧续跑并完成 379/379，当日另有记录）。建议下次提交清理。
- **观察项**：修改后 adam/adamw 完全不传 `fused` 也会静默走 eager（原先要求显式 truthy）。属于放宽默认行为，本次配置显式 `fused: false`，无实际影响。

## 边界确认

- 本结论仅覆盖"非 fused AdamW 单步诊断 PASS"；`SESSION.md:125` 已如实声明其不等同 R04 20–50 steps 正式 PASS。R04 终审仍需：连续多步 run、loss 曲线、行级保护（其他 domain 行不变）核验与 Gate JSON。
- 未违反 R01-R06 顺序与 frozen/locked 治理；修改集中于 Cosmos 扩展点，符合最小修改原则。

## 已执行的只读命令

- `git show c8e65d6`（cosmos-framework）：diff 全文核对
- `Read` adamw_single_step_retry2.log 全文（89 行）
- `grep optimizer.py`：optimizer_type 分发表（28-137 行）确认白名单外路径不变
- `ls/checkpoint 目录`、`grep config.yaml`：optimizer 配置与四件 checkpoint 核实
- `grep SESSION.md`：资源数字来源定位（124 行）

## 未执行的验证及原因

- 未重跑单步或 20-50 steps：训练属正式 GPU 任务，需用户确认；且本次审查对象是其代码与证据而非复现。
- GPU/RSS 峰值无法复核：产物中无采样记录（MEDIUM-1）。
