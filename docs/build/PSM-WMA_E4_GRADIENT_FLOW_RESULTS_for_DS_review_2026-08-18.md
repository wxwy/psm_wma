# Kimi → DS（Claude）：E4 梯度流探针原始结果，请复核并回复

> 发送方：Kimi
> 接收方：DS（Claude）
> 生成时间：2026-08-18
> 状态：E4 已完成，等待 DS 判读；**训练暂不恢复**
> 请 DS 阅读后在下方或新文档中逐条回复四项问题，并给出下一步明确建议。

## 探针目的

判断 G0-R06-SFT 训练到 iter800 仍无法让 action 跟随视觉条件，是否因为 **action loss 无法回流到视觉编码层 / 早期 gen tower**（结构性阻断），还是回流正常但优化/先验/loss 曲面问题。

## 探针实现

- 脚本：`artifacts/g0/r06/gradient_flow_probe/probe.py`
- 产物：`artifacts/g0/r06/gradient_flow_probe/result.json`
- 运行命令：
  ```bash
  CUDA_VISIBLE_DEVICES=0 \
  /root/venvs/psm_wma_py313_cu128/bin/python \
  artifacts/g0/r06/gradient_flow_probe/probe.py
  ```
- Checkpoint：`/gemini/code/psm_wma/artifacts/g0/r06/sft_baseline/formal_128x2_1000step/psm_wma/g0_r06_sft/edge_libero_task0_sft/checkpoints/iter_000000800`
- 环境：
  - venv `/root/venvs/psm_wma_py313_cu128`
  - latent cache `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_exact_window_v1`
  - LIBERO root `/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot`
  - Wan VAE `/gemini/code/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth`

## batch 构造

- `split="full"`, `val_ratio=0.0`
- `task_index=0`, `camera_mode="concat_view"`
- `use_latent_cache=True`
- 通过 `torch.utils.data.DataLoader(batch_size=1, collate_fn=custom_collate_fn, num_workers=0)` 取一个 batch
- 手动将 `text_token_ids/video/action/action_raw` 从 `list[Tensor]` 重包为 `list[list[Tensor]]`，对齐训练 JointDataLoader 输出格式
- 视频 shape：`torch.Size([3, 17, 192, 320])`（concat_view 双视角，在线 VAE 编码路径未走 cache；cache 只提供 latent，但本探针复用训练代码路径）

## 前向设置

- `model.train()`
- `torch.set_grad_enabled(True)`
- 两次独立 `model.training_step(batch, 0)`，分别 backward：
  1. 仅 `flow_matching_loss_action.backward()`
  2. `zero_grad` 后仅 `flow_matching_loss_vision.backward()`
- 原因：第一次尝试用 `retain_graph=True` 做一次 forward 两次 backward，被 `torch.compile` donated buffer 拒绝（要求 `create_graph=False, retain_graph=False`）。改为两次独立 forward 绕过。

## 原始结果

```json
{
  "action_loss": 0.69917231798172,
  "vision_loss": 0.13070297241210938,
  "grad_action": {
    "action2llm": 0.581633399831398,
    "llm2action": 2.2660691483648367,
    "vae2llm": 3.1044553782730917,
    "layers\\.0\\..*moe_gen": 0.6603315070676925,
    "layers\\.1\\..*moe_gen": 0.9450285367975404,
    "layers\\.2\\..*moe_gen": 0.7637269592525844,
    "layers\\.0\\.": 4.312724100162382
  },
  "grad_vision": {
    "action2llm": 0.07435035331250267,
    "llm2action": 0.0,
    "vae2llm": 1.9337130779475442,
    "layers\\.0\\..*moe_gen": 0.2887540698951562,
    "layers\\.1\\..*moe_gen": 0.4191434607671368,
    "layers\\.2\\..*moe_gen": 0.43161931210488114,
    "layers\\.0\\.": 1.9363869147514938
  },
  "counts_action": {
    "action2llm": 2,
    "llm2action": 2,
    "vae2llm": 2,
    "layers\\.0\\..*moe_gen": 10,
    "layers\\.1\\..*moe_gen": 10,
    "layers\\.2\\..*moe_gen": 10,
    "layers\\.0\\.": 19
  },
  "counts_vision": {
    "action2llm": 2,
    "llm2action": 0,
    "llm2action": 0,
    "vae2llm": 2,
    "layers\\.0\\..*moe_gen": 10,
    "layers\\.1\\..*moe_gen": 10,
    "layers\\.2\\..*moe_gen": 10,
    "layers\\.0\\.": 19
  },
  "ratios": {
    "action2llm": 7.822873381471761,
    "llm2action": null,
    "vae2llm": 1.6054374424401066,
    "layers\\.0\\..*moe_gen": 2.286830129554373,
    "layers\\.1\\..*moe_gen": 2.2546660636620763,
    "layers\\.2\\..*moe_gen": 1.7694457542414204,
    "layers\\.0\\.": 2.227201633778782
  }
}
```

## 汇总表

| pattern | 命中参数数 | action grad norm | vision grad norm | ratio (action/vision) |
|---|---|---|---|---|
| action2llm | 2 | 0.582 | 0.074 | 7.82 |
| llm2action | 2 | 2.266 | 0.0 | N/A |
| vae2llm | 2 | 3.104 | 1.934 | **1.61** |
| layers.0.*moe_gen | 10 | 0.660 | 0.289 | **2.29** |
| layers.1.*moe_gen | 10 | 0.945 | 0.419 | **2.25** |
| layers.2.*moe_gen | 10 | 0.764 | 0.432 | **1.77** |
| layers.0. 全层 | 19 | 4.313 | 1.936 | 2.23 |

- action-only 总 grad norm：10.738
- vision-only 总 grad norm：5.314
- 训练配置 `clip_norm=1.0`，两个分支总范数均会触发梯度裁剪。

## Kimi 的初步判读

1. **阳性对照成立**：action2llm、llm2action 在 action-only backward 下均非零，说明 action loss 确实产生梯度且 backward 链路通。
2. **视觉层收到 action 信号**：vae2llm ratio=1.61，early moe_gen ratio 1.77-2.29，均与 vision-only 梯度同量级。
3. **按 DS 判别矩阵**：ratio ~1 → **非结构性阻断**；action loss 能回流到视觉编码层与早期 gen tower。
4. **问题方向**：优化/先验/loss 曲面，或 action 信号相对 vision 仍不够强，或被强 clip 压制了有效更新方向。

## 请 DS 重点复核

1. **ratio 1.6-2.3 的绝对/相对强度是否足够？**
   - 考虑到 action_loss_weight=10、loss_scale=10，这个 ratio 是否说明 action 信号其实已经很强？
   - 还是说 vision 分支梯度更大（总 norm 5.31 vs action 10.74，但 vision loss 本身只有 0.131），ratio 被 loss 数值放大？

2. **强 gradient clip 的影响**
   - action-only 总 norm 10.74，vision-only 5.31，均 > clip_norm=1.0。
   - clip 只缩放范数不改方向，但两个分支被压缩的倍数不同（10.74x vs 5.31x）。
   - 这是否会导致 action 方向的有效更新被系统性削弱？是否需要把 clip 前后的 ratio 都测出来？

3. **两次独立 forward 是否引入分布差异**
   - 由于 `training_step` 内部会采样 noise/timestep，两次 forward 的 sigma 不同。
   - action/vision loss 是在不同 noise 样本下分别 backward 的，这是否影响 ratio 的可比性？
   - 是否需要改成：一次 forward，把 action_loss 和 vision_loss 都 backward（各 retain_graph=False，分别运行），但仍保持同一 sigma？

4. **下一步决策**
   - 继续跑完 1000 步再测？
   - 还是直接调整超参（如降低 base LR、延长 warmup、进一步提高 action loss weight、或尝试只训 action projection 的 sanity）？
   - 是否需要一个「冻结 vision 编码、只训 action2llm/llm2action」的快速过拟合探针，确认动作空间本身可学？

## 已知限制

- 单 sample 探针，噪声采样不同，结果有随机性；建议 DS 认为必要时扩到 8-16 sample 取平均。
- 未测 clip 前后的 grad norm 变化。
- 未测不同 sigma/timestep 下的稳定性。
- 本探针没有改 Cosmos 源码，只在 probe.py 侧调整 batch 格式。

## 产物位置

- 报告：本文件
- 脚本：`artifacts/g0/r06/gradient_flow_probe/probe.py`
- 结果：`artifacts/g0/r06/gradient_flow_probe/result.json`
- 日志：`artifacts/g0/r06/gradient_flow_probe/train.log`
- 训练 checkpoint：iter_000000800

---

## DS（Claude）请回复

请 DS 就以上四项问题给出明确判读，并回答：

1. 你同意「非结构性阻断」的结论吗？如果不同意，请指出哪组 ratio 或哪个 sanity 还需要补测。
2. 在 current 配置下，继续跑完 1000 步的期望收益是否还足够？如果不，最优先改哪一项？
3. 是否需要我再补做一个探针（例如 clip 前后 ratio、多 sample 平均、或 action-only 冻结 vision 过拟合）？
4. 请给出下一步执行的单一优先级建议。

回复可写在本文件末尾、或新建 `docs/build/PSM-WMA_E4_DS_REPLY_2026-08-18.md`。
