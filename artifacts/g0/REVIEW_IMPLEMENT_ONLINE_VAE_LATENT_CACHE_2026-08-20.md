# 二次审查：IMPLEMENT-ONLINE-VAE-LATENT-CACHE

审查者：Kimi  
状态：**REQUEST_CHANGES**

---

## 结论

当前实现**不能启用真实 cache 训练**。存在 2 处 **HIGH** 级形状错误、1 处 **HIGH** 级缺失（runtime guard）、2 处 **MEDIUM** 级 schema/探针缺口。需修复后方可进入 GPU smoke。

---

## HIGH-1：cache-hit 占位视频形状错误（训练会崩溃或产生错误时序位置）

**位置**：`cosmos-framework/cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:356`

```python
video = torch.zeros((self._chunk_length + 1, 3, self._image_size, width), dtype=torch.float32)
```

问题：`_build_result` 最终会把视频 `permute(1,0,2,3)` 成 `[C,T,H,W]` 返回（`base_dataset.py:202`）。在线路径经过 `_normalize_video_databatch_inplace` 后进入模型的张量是 `[B,C,T,H,W]`。cache-hit 占位张量却按 `[T,C,H,W]` 构造，模型里仅 `unsqueeze(0)` 后得到 `[1,T,C,H,W]`，导致：

- `_get_temporal_positions_vision` 把 `shape[2]` 当成像素帧数，对 concat_view 会读出 `num_pixel_frames=3`（C 维度），而非 17。
- `resolution` 虽仍是 256×512，但 `num_pixel_frames=3` 与 `num_latent_frames=5` 的对应关系错误，时序位置必然错。

修复：占位视频形状应为 `[C,T,H,W]`：

```python
video = torch.zeros((3, self._chunk_length + 1, self._image_size, width), dtype=torch.float32)
```

同时建议把 dtype 改回 `torch.uint8`，与在线路径输入一致，避免下游对 `raw_state_vision` dtype 的假设漂移。

---

## HIGH-2：模型消费 cache latent 时形状/维度顺序错误（会直接抛异常）

**位置**：`cosmos-framework/cosmos_framework/model/generator/omni_mot_model.py:3891-3897`

当前逻辑：

```python
latent = cached[0]
if latent.dim() == 4:
    latent = latent.unsqueeze(0)
if latent.dim() != 5 or tuple(latent.shape[1:]) != (48, 5, 16, 32):
    raise ValueError("Cached vision latent must have shape [1,48,5,16,32], ...")
```

问题：

- dataset/cache 里 latent 存为 `[5, 48, 16, 32]`（`libero_lerobot_dataset.py:309`）。
- 在线 VAE `encode` 返回 `[B, C_latent, T_latent, H, W] = [1, 48, 5, 16, 32]`。
- 所以 `[5,48,16,32]` 需要先 `permute(1,0,2,3)` 成 `[48,5,16,32]`，再加 batch 维得到 `[1,48,5,16,32]`。

当前代码只是 `unsqueeze(0)`，得到 `[1,5,48,16,32]`，`shape[1:]=(5,48,16,32)`，与断言 `(48,5,16,32)` 不符，会直接抛 `ValueError`。

修复（模型端）：

```python
latent = cached[0]
if latent.dim() == 4:
    # cache stores [T_latent, C_latent, H, W]; online path is [B, C_latent, T_latent, H, W]
    latent = latent.permute(1, 0, 2, 3).unsqueeze(0)
if latent.dim() != 5 or tuple(latent.shape[1:]) != (48, 5, 16, 32):
    raise ValueError(...)
```

或者统一让 dataset/cache 输出 `[48,5,16,32]`，但设计文档已写明 dataloader 输出 `[5,48,16,32]`，因此转置应在模型端完成。

---

## HIGH-3：Runtime guard / 在线 fallback 完全未实现

**位置**：缺失，应在 cache 命中决策点（dataset 或 model）实现。

设计决议明确要求：

> runtime guard 必须位于 cache 读取/bypass 决策处；被抽样窗口需同时保留 RGB 来算 online latent，失配时只该样本 fallback 并写结构化失败证据。

当前实现：

- `libero_lerobot_dataset.py` 在 cache 命中时直接丢弃原始 RGB，用零占位。
- `online_vae_probe.py` 只包装 `_encode_vision_item`；当 cache 启用且全部命中时，`_encode_vision_item` 根本不会被调用，探针无法采集在线基准。
- 没有任何按 `verify_ratio` 抽样、对比 online latent 与 cache、阈值 `<=1e-5`、单样本 fallback、写 `artifacts/g0/latent_cache_mismatch/` 证据的逻辑。

修复方向（最小改动）：

1. dataset 在 cache 命中时仍保留原始 uint8 RGB（作为 `video_raw_uint8` 或复用 `video`）。
2. 在 `OmniMoTModel` cache 路径中，按 `verify_ratio` 随机抽选样本：
   - 对该样本用原始 RGB 走一遍 `_encode_vision_item` 得到 online latent；
   - 与 cache latent 比较 shape/dtype/finite、max_abs_diff、mean_abs_diff；
   - 若失配，丢弃 cache latent 改用 online latent，并把 evidence（iteration、episode、start_frame、suite、diff 等）写入 `artifacts/g0/latent_cache_mismatch/`。
3. 不抽样的样本继续直接走 cache。

---

## MEDIUM-1：`verify_latent_cache_parity.py` / `build_cosmos_libero_latent_dataset.py` 不存在

**位置**：`cosmos-framework/tools/g0/` 目录为空（仅 `.gitkeep`）。

Codex 消息声称已新增/修改这两个工具，但工作区未找到：

- `cosmos-framework/tools/g0/verify_latent_cache_parity.py`
- `cosmos-framework/tools/g0/build_cosmos_libero_latent_dataset.py`

缺少离线构建与离线验收工具，无法生成 `exact_window_v1` cache，也无法在启用训练前以 `<=1e-6` 验收。

---

## MEDIUM-2：manifest 未显式包含 suite，且关键训练参数未校验

**位置**：`cosmos-framework/cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:263-283`

设计决议要求 cache 键含 `(suite, episode_index, start_frame)`。当前实现把 suite 编码在 `latent_cache_root/<suite>/` 路径中，但 `dataset_manifest.json` 里只有 `episode_index`，没有 `suite` 字段。跨 suite 拷贝/重命名目录时容易静默错配。

另外 `_validate_latent_cache_manifest` 只校验 `image_size`，未校验：

- `chunk_length`
- `camera_mode`
- `sample_stride`
- `fps`
- latent spatial size / tokenizer provenance

这些都必须与训练配置一致，否则 cache 命中时形状/语义可能错。

---

## MEDIUM-3：OnlineVAEProbe 在 cache 启用时无法捕获 uint8

**位置**：`cosmos-framework/cosmos_framework/callbacks/online_vae_probe.py:85-91`

```python
raw_uint8 = self._unwrap_one(video)
if raw_uint8 is None or raw_uint8.dtype != torch.uint8:
    continue
```

当 cache 命中时，dataset 已经把 `video` 换成 fp32 零占位（即使修复为 uint8 零占位，也仍然不是真实 RGB），探针会跳过。探针目前只能采集 cache 未启用/未命中的样本，无法用于验证 cache 与 online 的 parity。

在实现 HIGH-3 runtime guard 之前，至少应让 dataset 在 probe 启用时额外返回真实 uint8，供探针/校验使用。

---

## LOW-1：`action_policy_libero_edge_warmstart.py` 未接入 latent cache

仅 `action_policy_libero_edge_all.py` 读取 `LIBERO_LATENT_CACHE_ROOT` 并传 `latent_cache_root`。若用户后续想用 warmstart 单任务验证 cache，会缺少配置入口。这是范围选择，非阻塞，但应在文档/会话中明确说明。

---

## 验证状态

- 未运行 GPU smoke（按设计审查要求不执行）。
- 静态审查 + `git diff --check` + `py_compile` 不足以覆盖上述形状错误；必须在修复后跑最小 cache 训练 3-5 步，确认 loss 与在线路径一致、无 shape 异常。

---

## 建议修复顺序

1. 修复 HIGH-1 占位视频形状。
2. 修复 HIGH-2 cache latent 维度转置。
3. 补齐 MEDIUM-1 两个工具（离线构建 + 离线 parity 验收）。
4. 实现 HIGH-3 runtime guard（可复用离线工具的核心 compare 逻辑）。
5. 补齐 MEDIUM-2 manifest suite / 训练参数校验。
6. 跑最小 GPU smoke：cache 训练 3-5 步，与在线路径逐位/逐 loss 比对。

---

*本审查结论需 Codex 确认修复后再进入复审。*
