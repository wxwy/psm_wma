# G0-R06-SFT E4 梯度流探针交接

> 生成时间：2026-08-17
> 生成原因：上下文即将耗尽，记录当前状态与下一步精确动作，避免重启后丢失。

## 当前主线

G0-R06-SFT 训练到 iter800 仍无法让 action 跟随视觉条件。已排除的假设：

- 推理采样问题（E2 teacher-forced 探针：真实视觉 vs 黑帧 action 单步去噪 MAE 几乎无差异，0.3146 vs 0.2768）。
- 开环漂移（iter700 horizon=4 与 horizon=16 均 SR=0/3，且复跑一致）。
- 训练/评测任务错位（已修正为 task_index 0 ↔ 仿真 task_ids 4）。
- 视觉输入视角错位（已修正为 agentview+wrist concat_view 双视角）。
- slot-0 条件泄漏（DS 理论被实证推翻，diff=0.0）。

当前最可能根因：**训练侧 vision→action 信号未学会**。DS 提议的 E4「双分支梯度流探针」用于判断 action loss 是否能有效回流到视觉编码层。

## 已做

- 自己实现脚本 `artifacts/g0/r06/gradient_flow_probe/probe.py`（Codex 未响应）。
- 脚本通过 `ActionModelService` 单进程加载 iter800 checkpoint，调用 `model.training_step(batch, 0)`。
- 已逐个修复前置失败点：
  - `CheckpointOverrides` 要传 `str` 路径。
  - 用 `custom_collate_fn` 处理 `action_processing_record`。
- 最新一次运行（PID 3933871，日志 `artifacts/g0/r06/gradient_flow_probe/run2.log`）在 `pack_text_tokens` 失败：`shifted_text_ids` 是 `int` 而非 `list`，因为 `_load_and_tokenize_text_data` 对 `text_token_ids` 的嵌套层级假设与手动 batch 不一致。

## 当前阻塞点

`_load_and_tokenize_text_data` 期望 `data_batch["text_token_ids"]` 是 `[[tensor]]`（外层 sample、内层可能是 sub-sequence），这样：

```python
[tokens.tolist() for x in input_text_tokens for tokens in x]
```

才能产出 `[[int,...], ...]`。

当前 `probe.py::_collate_one` 用 `custom_collate_fn([item])` 给出的是 `[tensor]`（少一层），导致 packer 解包后把单个 int 当成一个 sample 的 token 序列。

## 下一步（精确动作）

1. 修改 `artifacts/g0/r06/gradient_flow_probe/probe.py` 的 `_collate_one`：
   - 不要直接 `custom_collate_fn([item])`。
   - 改为用 `torch.utils.data.DataLoader(ds, batch_size=1, collate_fn=custom_collate_fn, num_workers=0)` 取一个 batch。
   - 这样完全复现训练内层 dataloader 的输出格式，包括 `text_token_ids` 的嵌套层级。
2. `python -m py_compile artifacts/g0/r06/gradient_flow_probe/probe.py`。
3. 在 tmux 或 nohup 下重跑：
   - cwd: `/gemini/code/psm_wma`
   - venv: `/root/venvs/psm_wma_py313_cu128`
   - 命令：`/root/venvs/psm_wma_py313_cu128/bin/python artifacts/g0/r06/gradient_flow_probe/probe.py`
   - 产物：`artifacts/g0/r06/gradient_flow_probe/result.json` 和 `train.log`
4. 得到 `result.json` 后按 DS 判别矩阵判读：
   - ratio < 0.01 → 结构性阻断（attention/mRoPE/打包问题）
   - 0.1 ~ 1 → 弱回流 + grad clip 压制
   - ~1 → 信号能回流，问题在优化/先验/loss 曲面
5. 把结论同步给 DS 和用户，决定：
   - 恢复训练到 1000 步；或
   - 改 LR/schedule 重训；或
   - 改 attention/position 配置。

## 环境与路径

- 工作目录：`/gemini/code/psm_wma`
- venv：`/root/venvs/psm_wma_py313_cu128`
- checkpoint：`/gemini/code/psm_wma/artifacts/g0/r06/sft_baseline/formal_128x2_1000step/psm_wma/g0_r06_sft/edge_libero_task0_sft/checkpoints/iter_000000800`
- latent cache：`/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot_cosmos_exact_window_v1`
- LIBERO root：`/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot`
- GPU：单卡 A100 40GB；训练仍暂停在 811/1000；当前 GPU 被 E4 探针占用。

## 相关文件

- `artifacts/g0/r06/gradient_flow_probe/probe.py`（待修）
- `artifacts/g0/r06/gradient_flow_probe/run2.log`（失败日志）
- `cosmos_framework/data/generator/joint_dataloader.py`（`custom_collate_fn` 定义）
- `cosmos_framework/model/generator/omni_mot_model.py`（`training_step`、`_load_and_tokenize_text_data`）

## 禁止事项

- 不要直接改 Cosmos 公共接口（如 `_load_and_tokenize_text_data`）来适配 probe；应在 probe 侧构造正确 batch。
- 不要恢复训练或启动正式评测，直到 E4 结论落地。
