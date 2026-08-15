# REVIEW + 执行报告 — G0-R05 LIBERO Tiny Overfit

- 执行/审查：Kimi
- 日期：2026-08-15
- 对象：根提交 `d4479e9`、cosmos-framework `1352b12`；Runbook `docs/build/PSM-WMA_G0_R05_tiny_overfit_runbook_v0.1.md`
- 授权：用户明确授权按 Runbook 自动执行 Phase A/B/C/D（无外网、单 GPU 不并发）

## 第一阶段只读审查结论

**APPROVE**

### 代码审查（1352b12 + d4479e9）

- `ActionFixedSubsetCycleDataset`（`action_sft_dataset.py:92-130`）：确定性循环子集，边界校验齐全；仅在显式 `tiny_overfit_num_samples` 时启用（`action_sft_dataset.py:322-325`），与 `iterable_shuffle` 互斥，默认路径不变 ✓
- `action_x0_reconstruction_mae`（`omni_mot_model.py:91-116`）：rectified-flow 恒等式 `|x0_hat-x0| = sigma*|pred_v-target_v|` 数学正确；detached 诊断量，不进 loss；noisy_mask 屏蔽 conditioning 帧、raw_action_dim 截断 padding ✓；单测数值手算复核 1.5 ✓
- `action_policy_libero_edge_tiny_overfit.py`：完整复用 warmstart（含 weight-decay 行保护、EMA off），train subset=4@0、val subset=1@4、`validation_iter=100`、`max_val_iter=1` ✓
- trainer 改动（`trainer/__init__.py:287-289`）：`run_validation_on_start` 扩展到 resumed run，默认 false，其他 recipe 不变 ✓；validation 触发点在 iteration 递增后（366-367 行），`max_iter=100` 时第 100 步会先存 checkpoint 再 validate，时序正确 ✓
- `validate()` 遵守 `max_val_iter`（`trainer/__init__.py:482-483`），held-out 恰好 1 batch ✓
- `collect_r05_gate.py`：iteration 序列断言 1..100 与回调 1-based 记录一致；trend ratio、reload 容差（rtol=1e-5/atol=1e-6）、checkpoint 四件、失败码完整 ✓
- `audit_r05_action_stats.py`：parquet 7D axis-angle → rot6d 10D 转换与数据集 `_build_frame_wise_action` 同路径（`convert_rotation` + `libero_rotation_format`）；tail 阈值 0.10 ✓

### 轻量验证（已执行，CPU 无 GPU）

- fixed subset 单测逻辑复现：PASS（[2,3,4,2,3,4,2,3]）
- x0 MAE 单测逻辑复现：PASS（=1.5）
- stats 产物 `R05_action_stats_sanity.json`：status PASS、101,469 帧、379 parquet、max_outside_rate=0.03069 < 0.10；stats_sha256 `bf20cb01…` 与仓库内置文件实算一致 ✓
- flat index 0–4 归属断言：全部 episode=0、task=0、start 0–4 连续；train [0-3] 与 held-out [4] 不重叠 ✓
- 配置解析 dry-run（`load_experiment_from_toml` + 完整 CLI override 模式）：max_iter=100、run_validation=True、validation_iter=100、max_val_iter=1、train subset (4,0) shuffle=False、val subset (1,4)、r05_metrics 回调注入成功、save_iter=100 ✓
- 注：venv 无 pytest，单测以等价脚本复现断言。

### 审查发现

无阻塞项。LOW-1：runbook 状态仍为 `draft`，建议 Gate 通过后升 reviewed。

## 执行计划与判据（启动前记录）

### Phase A（CPU，无外网）

```
cwd=/gemini/code/psm_wma
PYTHONPATH=/gemini/code/psm_wma/cosmos-framework \
/root/venvs/psm_wma_py313_cu128/bin/python tools/g0/audit_r05_action_stats.py \
  --dataset /gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot \
  --stats cosmos-framework/cosmos_framework/data/generator/action/normalizer_stats/libero_native_frame_wise_relative_rot6d.json \
  --output artifacts/g0/r05/R05_action_stats_sanity.json
```
PASS：status=PASS 且 max_outside_normalized_unit_rate<0.10；FAIL：停止，不进入 Phase B。

### Phase B（GPU，~5h 预估：100 步 × ~3min）

- cwd=`/gemini/code/psm_wma/cosmos-framework`；env：`PYTHONHASHSEED=42`、`PYTHONPATH=cosmos-framework:psm_wma`、`LIBERO_ROOT`、`BASE_CHECKPOINT_PATH`（DCP）、`EDGE_POLICY_CHECKPOINT`、`WAN_VAE_PATH`、`IMAGINAIRE_OUTPUT_ROOT=/gemini/code/psm_wma/artifacts/g0/r05/tiny_overfit_100step`
- 命令：严格按 Runbook §5（torchrun --standalone、--deterministic、r05 TOML、AdamW fused=false、num_workers=0、r05_metrics 回调双 JSONL）；以 nohup 后台替代 `source activate`+tee（等效，日志写 `train.log`）
- 产物：`step_metrics.jsonl`（100 行）、`held_out_metrics.jsonl`（iteration=100 一行）、`checkpoints/iter_000000100/`、`train.log`
- PASS：100/100 步连续、四项 loss 与 grad 全 finite、无 OOM/SIGKILL；FAIL：nonfinite 或步序断裂；BLOCKED：资源不足/平台故障（记 BLOCKED_RESOURCE）

### Phase C（GPU，~10min）

- 按 Runbook §6：`IMAGINAIRE_OUTPUT_ROOT=.../tiny_overfit_reload`，`checkpoint.load_path=iter_000000100`、`load_training_state=true`、`strict_resume=true`、`run_validation_on_start=true`、`max_iter=100`（不新增训练步）
- 产物：`tiny_overfit_reload/held_out_metrics.jsonl`、`reload.log`
- PASS：恢复 iteration=100 且 held-out 四项与 Phase B 末次满足 rtol=1e-5/atol=1e-6

### Phase D（CPU）

- 按 Runbook §7 运行 `collect_r05_gate.py`，输出 `artifacts/g0/r05/R05_libero_tiny_overfit.json`
- 总 PASS 条件 = Runbook §1 七条全满足

### 通用约束

单张 40GB GPU，启动前确认空闲无外网；预计 GPU 分配峰值 ~35GB、RSS <32GB；与其他 GPU 任务不并发。运行中每 ~10 分钟检查一次（含 SIGSTOP 自动 CONT 恢复）。

## 执行记录

### Phase A（2026-08-15，已 PASS）

`audit_r05_action_stats.py` 实跑 PASS：max_outside_rate=0.0307 < 0.10，stats sha256 与 Runbook 记录一致；fixed subset 索引 flat 0-4 同属 episode 0 / task 0，train(0-3) 与 val(4) 不重叠。

### Phase B（2026-08-15，训练步完成；held-out 验证因代码缺陷失败）

- 实际配置三次迭代：nw=0(163s/步）→ nw=2(149s/步）→ **bs=1 + grad_accum_iter=32 + train nw=2/val nw=0(~50s/步，用户拍板）**。
- **Deviation**:Runbook TOML `grad_accum_iter=1`，实际 32(bs=1)。每步样本 32，语义与 packing ~128 样本/步不同，但 deterministic、loss 趋势判据不变。
- 跨配置可复现性证据：nw=2 与 nw=4 两局前两步 loss 完全一致（15.269/14.582)。
- 中断存档：`step_metrics_nw0_first19.jsonl`、`step_metrics_nw2_first2.jsonl`、`step_metrics_nw4_first2.jsonl`；Gate 只用最终完整 100 步 `step_metrics.jsonl`。
- 结果：100/100 步，iteration 1→100，total/action/action_x0/vision 与 grad 全部 finite，日志零 error。GPU 峰值 16653.5 MiB,RSS 峰值 12.3GB。前 10 步 vs 后 10 步中位数 ratio:total 0.7054(≤0.80)、action 0.7451(≤0.80)、action_x0 0.7350(≤0.80)、vision 0.2846(≤1.10)——趋势判据全部满足。
- Checkpoint `iter_000000100` 已保存完整四件（model/optim/scheduler/trainer)。
- **失败点**：第 100 步 checkpoint 保存后，trainer 按 `validation_iter=100` 触发 held-out validation,`OmniMoTModel.validation_step` 是 `pass` 桩（`cosmos_framework/model/generator/omni_mot_model.py:3518-3519`),`trainer/__init__.py:488` 解包 `output_batch, loss = model.validation_step(...)` 抛 `TypeError: cannot unpack non-iterable NoneType object`，进程 exitcode 1,`held_out_metrics.jsonl` 未产出。

### 新增审查发现（执行暴露，原静态审查未覆盖）

- **HIGH-1（REQUEST_CHANGES)**:`omni_mot_model.py:3518` `validation_step` 为桩，与 R05 Gate 的 held-out 判据及 `r05_tiny_overfit_metrics.py:97` 的 `on_validation_step_end` 回调不兼容——回调依赖 `validation_step` 返回 `(output_batch, loss)`，桩返回 None 直接导致 Phase B 末段与 Phase C(reload `run_validation_on_start=true`）必然崩溃。1352b12 只改了 trainer 的 resume-validation 触发条件，没有实现模型侧 validation_step。**Gate 的 held-out 与 reload-consistency 两项当前无法产出，Phase C/D 暂停，待 Codex 修复后从 reload 阶段重跑（训练 100 步与 checkpoint 有效，不需重训）**。建议最小修复：实现 no-grad 的 validation_step（复用 training forward 路径，返回 losses_dict 与 total_loss)，或经 Codex 评估后改回调/validate 流程。
- LOW-2：执行中两次遭遇外部 SIGSTOP(`State=T`),`kill -CONT` 无损恢复；FUSE 网络盘逐样本解码是吞吐瓶颈，worker 数 >2 反而更慢（带宽争用）。

### HIGH-1 修复复审(fbe85a0 + 51958e4,2026-08-15 晚)

**APPROVE**。`validation_step`(`omni_mot_model.py:3518-3522`）加 `@torch.no_grad()` 并委托 `training_step`：返回合同 `(output_batch, loss)` 与 `trainer/__init__.py:488` 解包及 `r05_tiny_overfit_metrics.py:97-118` 回调键一致；`training_step` 体（`omni_mot_model.py:1078-1312`）无 backward/optimizer/参数写入，no_grad 下安全；model.eval() 与 ema_scope 由 trainer validate 负责；单卡无 CP 风险。另核实 deterministic 噪声与训练历史无关：sigma(`rectified_flow.py:150-154`）与 epsilon(`omni_mot_model.py:1856-1860`）均按 `(iteration*65536+rank[+32768])` 播种，因此 reload 在 iteration=100 的 held-out 计算与 Phase B 末段内存内验证数学上等价（权重相同：checkpoint 先于 validate 保存）。

### Phase C 第一次执行(2026-08-15 19:02,失败，现场保留在 reload.log)

- 命令：Runbook §6 原样 + Phase B 已批准 deviation(`dataloader_train.max_samples_per_batch=1 trainer.grad_accum_iter=32`),nohup 后台，日志 `tiny_overfit_reload/reload.log`。
- model 549 keys、optim 4410 keys 读取成功，checkpoint 加载耗时 757s；随后在 optimizer 状态广播阶段崩溃。
- **HIGH-2（REQUEST_CHANGES，阻塞 Phase C)**:`checkpoint/dcp.py:872` optimizer 分支调用 `_broadcast_state_dict` → `_broadcast_tensor_leaf`(`dcp.py:518`)`dist.broadcast(value, src=0)` 对 **CPU 标量张量**（非 capturable AdamW 的 `state['step']`，正是该函数 docstring 点名的场景）走 NCCL 进程组，抛 `RuntimeError: No backend type associated with device type cpu`(`distributed_c10d.py:2907`)。单卡 world_size=1 时 broadcast 语义上是 no-op。该缺陷为 cosmos 既有代码（不属 1352b12/fbe85a0)，此前未被触发是因为 R04 等只加载 HF 转换的 base DCP（无 optimizer 状态）;R05 Phase C 是首个 reload 训练态 checkpoint 的路径。建议最小修复（由 Codex 定）：world_size==1 时在 `_broadcast_state_dict` 直接返回，或 CPU 叶子经 gloo/临时 CUDA 张量广播。
- 现场：`reload.log` 完整保留；无残留训练进程；`held_out_metrics.jsonl` 未产出；Phase B 的 100 步指标与 checkpoint 不受影响。

### Phase C / D

阻塞于 HIGH-2，待 Codex 修复后重跑 Phase C。另注：因 HIGH-1 导致 Phase B 的 in-memory `held_out_metrics.jsonl` 永久丢失，Phase D 的 `--held-out` 将以 reload 产物替代并在报告中记 deviation——依据是上述 iteration 播种的确定性等价论证；criterion 6 将改为两次独立 reload 间比对（验证 reload 确定性 + checkpoint 完整性），而非 train-memory vs reload。
