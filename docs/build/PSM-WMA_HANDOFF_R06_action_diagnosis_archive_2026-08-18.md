# G0-R06 action 不随视觉条件变化 — 定位过程完整存档

> 存档方：DS（Claude）+ Kimi
> 日期：2026-08-18
> 状态：**存档关闭本轮探索**，准备换思路
> 范围：G0-R06 SFT（iter800）action 输出与视觉条件解耦问题的全部已执行探针、证据、判读、未决问题

---

## 0. 问题定义

G0-R06 的 action 生成不随视觉条件变化：
- iter800 SFT 与 zero-shot DROID 两个 checkpoint 均 corr(专家)≈0、模板输出
- action 对视觉/文本/场景均不敏感（E0），但 vision 本身生成正常

---

## 1. 完整证据链（已执行，按时间序）

### E0 · 服务器黑帧探针（zero-shot server :8001）
- 方法：`/predict` 黑帧/换 prompt/换场景帧，对比 action 与 video 输出
- 结果：action 对视觉/文本/场景差异 ≤0.02；video 像素差 255（`/tmp/psm_wma_probe_blackframe.json`）
- 结论：action 生成对视觉条件不敏感

### 证据2 · slot0 感受野探针
- 方法：CausalConv3d 前端零填充验证，交换帧构造
- 结果：`slot0_real_vs_staticrepeat_maxdiff=0.0`、`frame0_swapped_maxdiff=2.93`（`artifacts/g0/r06/slot0_probe/result.json`）
- 结论：**slot0 严格 = f(帧0)**，训练/推理逐位一致；推翻「slot0 含未来帧运动泄漏」假说

### E1 · predictions.npz 分桶量化
- 方法：iter800 50 query 按起始帧距离分桶（stride 4）
- 结果：首步 action 距离 <8帧:0.055 / 8-32:0.103 / >32:0.158（单调增长）；corr≈0、pred_std 仅专家 1/4~1/8；iter800 dx std(0.081) 是 zero-shot(0.007) 的 10 倍
- 结论：**action 不是硬断耦，是「弱且错」的耦合**；SFT 放大耦合但方向错误

### F1 · 代码审计：最终 action 输出路径
- 方法：读 omni_mot_model.py 采样循环
- 结果：最终 action = `latents[i][offset:offset+action_dim]`（积分 latent）经 `ActionProcessor.postprocess_action`（omni_mot_model.py:3328-3344）；`llm2action` 只产生**速度** preds_action 供 flow-matching 积分
- 结论：最终输出完全由采样循环中 action token 的速度场决定

### F3 · 代码审计：结构无 mask 隔离
- 方法：读 two_way attention（attention.py:296-313）、pack 路径（packers.py:215-290）
- 结果：`video_temporal_causal=False`（standard pack），two_way dense（flex_attention=False），GEN query 无 mask 地 attend 整个 sample `[text|vision|action]`
- 结论：结构上 action token 能 attend 条件

### 归一化审计
- 方法：训练 config `action_normalization=quantile_rot, action_stats_path=null` → 回退 bundled `libero_native_frame_wise_relative_rot6d.json`，stats_key=`global_raw`
- 结论：训练/推理 round-trip 一致，排除归一化不匹配（`R05_action_stats_sanity.json`）

### E2 · teacher-forced 探针（training_step 双跑）
- 方法：`on_training_step_end` 用同一训练 batch、real vision vs black vision 各跑一次 training_step（`teacher_forced_probe_callback.py`）
- 结果：`real_action_x0_mae=0.3146 / black=0.2768 / delta=+0.0377 / real_fm=0.3582 / black_fm=0.2783 / sigma_action=null`（共享 sigma）
- 结论：
  1. 问题**不在推理采样**（teacher-forced 也几乎无差异）
  2. vision **被使用但有害**（real 比 black 差）
  3. action 路径是「自包含 action 去噪器」，单步 x0 重建 MAE 0.31（±1 范围）很高

### R05 tiny-overfit 对比
- 方法：4 样本×25 epoch（100 步）tiny-overfit 与 iter800 全量对比
- 结果：iter100 `action_x0_mae=0.36 / flow_loss=0.98`，与 E2(0.31/0.36) 同量级；**分模态首末中位**：vision_flow_loss 降 3.5×（0.112→0.032）、action_flow_loss 仅 1.3×（1.162→0.866）
- 结论：排除数据量/步数；**同一数据下 vision 快速收敛、action 几乎不动** → action 学习信号结构性弱

### 全程梯度 clip 证据
- 方法：解析 R06 train.log `clip_grad_norm/video/global` 共 868 条
- 结果：grad norm **min=4.56 / max=40.5 / median=11.66 / q25=9.25 / q75=15.77**，全部 > clip_norm=1.0 → 每次 step 梯度被压缩 5~40 倍
- 结论：clip 是「放大器」（只缩范数不改方向）；若 action 与 vision 梯度方向冲突则系统性压制 action 更新

### E4 · 梯度流探针（本轮核心）
- 方法：单进程加载 iter800，`model.train()` 下分别 backward action_loss / vision_loss，测 vae2llm / early `*_moe_gen` 梯度 L2 norm（`gradient_flow_probe/probe.py`）
- 结果（`gradient_flow_probe/result.json`）：

  | pattern | action grad | vision grad | ratio |
  |---|---|---|---|
  | action2llm | 0.582 | 0.074 | 7.82 |
  | llm2action | 2.266 | 0.0 | N/A |
  | **vae2llm** | 3.104 | 1.934 | **1.61** |
  | layers.0.*moe_gen | 0.660 | 0.289 | **2.29** |
  | layers.1.*moe_gen | 0.945 | 0.419 | **2.25** |
  | layers.2.*moe_gen | 0.764 | 0.432 | **1.77** |
  - action-only 总范数 10.74，vision-only 5.31
- 结论：**action loss 能回流到 vae2llm/early gen tower，且强度 ≥ vision** → **结构性阻断排除**。但仅证明「信号回流强」，未证明方向正确。

---

## 2. 已排除的假说

| 假说 | 排除依据 |
|---|---|
| slot0 含未来帧运动泄漏 | 证据2（slot0=f(帧0)） |
| 数据量/步数不足 | R05（4样本×25epoch 与全量同量级） |
| 归一化不匹配 | quantile_rot→global_raw round-trip 一致 |
| attention mask 硬隔离 | F3（two_way dense，无 mask） |
| 推理采样把耦合洗掉 | E2（teacher-forced 也几乎无差异） |
| 训错层 | warmstart 冻结层已确认（可训=moe_gen/time_embedder/vae2llm/llm2vae/action2llm/llm2action/action_modality_embed） |
| 结构性阻断（action 梯度到不了视觉编码） | E4（vae2llm/early moe_gen ratio 1.61~2.29） |

---

## 3. 仍开放的未知量

1. **grad_action 与 grad_vision 的方向一致性（cosine）** — 从未测量，是最关键分叉点
2. loss 曲面 / DROID 先验 vs 方向冲突 — 未区分
3. action 空间本身是否可学（冻结 vision 的 action-only 过拟合）— 未做
4. attention 中 action query 对 vision 的权重分布（E4 已间接证明非零，未量化分布）

---

## 4. 已建议但未执行的探针（供换思路参考）

1. **方向探针**（优先级最高）：同 sigma 下一次 forward，关 compile + retain_graph 双 backward，测 grad_action 与 grad_vision 在 vae2llm / layers.0-2.*moe_gen 上的 cosine；8-16 sample 平均。判读：cosθ>0.7 → 曲面/先验；<0.1/负 → 方向冲突实锤
2. **action-only 冻结 vision 过拟合**：确认动作空间本身可学
3. 继续跑 1000 步（已判定期望有限，800 已平台）

---

## 5. 关键文件索引

**探针脚本/产物**
- `artifacts/g0/r06/slot0_probe/{probe.py,result.json}` — 证据2
- `artifacts/g0/r06/teacher_forced_probe/{teacher_forced_probe_callback.py,e2_probe.jsonl}` — E2
- `artifacts/g0/r06/gradient_flow_probe/{probe.py,result.json,train.log}` — E4
- `artifacts/g0/r06/open_loop_iter800/predictions.npz` — E1 数据
- `/tmp/psm_wma_probe_blackframe.{py,json}` — E0
- `artifacts/g0/r06/ds_action_diagnosis_claude_2026-08-18.txt`、`ds_e4_review_claude_2026-08-18.txt`

**闭环评测产物（task4 iter300-700 + zeroshot，task0 系列）**
- `artifacts/g0/r06/eval_task4_iter300_sft/`（actions/ gifs/ summary.json eval.log）
- `artifacts/g0/r06/eval_task4_iter500_sft/`（actions/ videos/ summary.json）
- `artifacts/g0/r06/eval_task4_iter600_sft/`（actions/ comparisons/ videos/ summary.json）
- `artifacts/g0/r06/eval_task4_iter700_sft_h4/`（actions/ comparisons/ predictions/ videos/ summary.json summary_noborder_run.json）
- `artifacts/g0/r06/eval_task4_zeroshot_droid/`（actions/ videos/ summary.json）
- `artifacts/g0/r06/eval_task0*`（task0 系列闭环：eval_task0/ iter300_sft/ repeat/ failed_triton）
- `result_v2.json` — **待生成**（E4v2 cosine 方向探针）

**判读/协作文档**
- `docs/build/PSM-WMA_E4_GRADIENT_FLOW_RESULTS_for_DS_review_2026-08-18.md`（Kimi）
- `docs/build/PSM-WMA_E4_DS_REPLY_2026-08-18.md`（DS）
- `/tmp/psm_wma_claude_{action_diagnosis,e2_interpret,e4_review,e4_probe_review}.txt`

**训练配置/checkpoint**
- `artifacts/g0/r06/sft_baseline/formal_128x2_1000step/psm_wma/g0_r06_sft/edge_libero_task0_sft/config.yaml`
- `.../checkpoints/iter_000000800/model`
- `artifacts/g0/r06/sft_baseline/formal_128x2_1000step/step_metrics.jsonl`

---

## 6. 本轮收敛的核心结论

1. action 是「**弱且错**」的耦合（非断耦）：随 vision 变化但方向错误、强度远小于专家分布
2. 问题**不在推理链路**（E2）、不在数据量（R05）、不在结构阻断（E4）
3. 收敛指向：**训练中 action 分支的梯度方向/优化路径问题**（方向冲突 + clip 放大，或 loss 曲面/先验）—— 有待方向探针定案
4. 全程 grad clip（norm 4.5~40 压到 1.0）是系统性放大器，值得在换思路时纳入训练配置审查

---

## 7. 换思路方向（Kimi 提出的 E4v2 cosine 分叉决策树）

当前仍未拿到 grad_action 与 grad_vision 的 cosine（方向一致性），它是下一轮的分叉点：

| cosine 结果 | 含义 | 行动 |
|---|---|---|
| **低（<0.1 或负）** | action 与 vision 梯度方向冲突，被抵消 | 解耦优化 / 提高 action_loss_weight / 冻结 vision 做 action-only 过拟合 |
| **高（>0.7）** | 方向一致，问题在曲面/初始化/先验 | action projection 随机初始化 / 降 base LR / 延长 warmup |
| **通用** | 无论高低 | 放宽 grad_clip（当前 norm 4.5~40 压到 1.0 过激） |

**当前优先级**：E4v2 cosine 方向探针 > 一切训练参数调整。训练暂停中。
