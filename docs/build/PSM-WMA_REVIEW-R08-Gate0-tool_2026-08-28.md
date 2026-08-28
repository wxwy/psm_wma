# R08 Gate-0 工具代码静态审查报告

> 审查方：Kimi
> 被审文件：`tools/g0/verify_r08_z0_suffix_invariance.py`（及引用的 `tools/g0/exact_window_cache.py`）
> 当前提交：根 `a3d11a8`，子模块 `10bc410`
> 审查方式：只读代码审查，未执行 GPU
> 结论：**APPROVE（带 1 项 MEDIUM，需在首次 GPU 运行前关闭）**

---

## 1. 审查范围

1. 是否复用当前训练侧的 concat/uint8/VideoResize/Wan bf16 exact-duration 编码契约。
2. A/B 对构造是否保证首帧 bitwise 相同、suffix 真正不同且合法。
3. 覆盖率是否满足 `>=64 anchors`（4 suites × 4 mods × anchors_per_mod >= 4）。
4. 是否只比较 temporal latent index 0（z0）。
5. 是否输出机器可读 JSON + raw sidecar + provenance。
6. 是否不读取 cache latent、不引入 history/R09/GPU 训练。
7. 代码质量与潜在运行时风险。

---

## 2. 核验结果

| 检查项 | 证据 | 结果 |
|---|---|---|
| 当前 HEAD | 根 `a3d11a8`，子模块 `10bc410` | PASS |
| 脚本语法 | `py_compile` PASS | PASS |
| concat 复用 | `verify_r08_z0_suffix_invariance.py:145-148` 使用 `camera_mode="concat_view"`；`:134` 调用 `dataset._load_video`（内部 `:462-464` concat） | PASS |
| uint8 转换 | `:135` `to_training_uint8`（`exact_window_cache.py:28-32`）与 `base_dataset.py:202` 一致 | PASS |
| VideoResize | `:150` `VideoResize(pad_keys=["video"], keep_aspect_ratio=True)`，`:136` `resolution=None` → 自动 snap 到 192×320（`data/generator/utils.py:45-51`、`transforms.py:44-82`） | PASS |
| Wan exact-duration / bf16 | `:204-208` 使用 `Wan2pt2VAEInterface` + `LIBERO_EXACT_WINDOW_ENCODE_*`；`:39` 经 `encode_uint8_vision_item`（`vision_vae.py:24-30`）归一化后 encode | PASS |
| A 首帧 = B 首帧 | `:122-123` 断言 `torch.equal(a[:, :1], b[:, :1])` | PASS |
| suffix 真正不同 | `:124-127` 断言 `not torch.equal(a[:, 1:], b[:, 1:])` | PASS |
| B 合法 | `:118-128` B 由同一 episode 的另一合法 17 帧窗口拼接 | PASS |
| 只比 z0 | `:162-163` 取 `encode_window(...)[0]` | PASS |
| 覆盖率 | `:191` 默认 `anchors_per_mod=4`；`:195-196` 强制 `>=4`；4 suites × 4 mods × 4 = 64 | PASS |
| JSON + provenance | `:222-250` 输出 JSON，含 schema_version、status、coverage、vae_contract、sidecar、records、provenance | PASS |
| raw sidecar | `:218-221` 保存 `.pt` sidecar 并记录 SHA256；`:237` 标注 retention | PASS |
| 不读 cache latent | 未设置 `latent_cache_root`；仅使用 `_load_video` 解码原始视频 | PASS |
| 无 history/R09 | 代码仅构造 A/B 并编码，无历史流/readout/recurrent/TTT | PASS |

---

## 3. 发现

### BLOCKER

无。

### HIGH

无。

### MEDIUM

1. **VAE encode 未使用 `torch.no_grad()`/`torch.inference_mode()`，会构建 autograd graph。**
   - 证据：`verify_r08_z0_suffix_invariance.py:161-163` 在 `_run_suite` 中直接调用 `encode_window`；`exact_window_cache.py:39` 调用 `encoder.encode(...)`；`Wan2pt2VAEInterface.encode`（`wan2pt2_vae_4x16x16.py:1451-1460`）内部调用 `self.model.encode(state)`，未显式 detach。
   - 影响：运行时会为 64 对 z0 保留计算图，显著增加 GPU 显存占用；若在 CUDA 上运行，可能导致 OOM，且完全无必要（纯诊断，不求梯度）。
   - 建议的最小修复：在 `_run_suite` 的 encode 循环外加 `with torch.no_grad():`，或给 `VisionEncoderAdapter.encode` 加 `@torch.no_grad()`。推荐修改位置：
     - 方案 A：`verify_r08_z0_suffix_invariance.py:161-164` 改为：
       ```python
       with torch.no_grad():
           z0_a = encode_window(a, encoder, device=device)[0]
           z0_b = encode_window(b, encoder, device=device)[0]
       ```
     - 方案 B：`exact_window_cache.py:24-25` 给 `VisionEncoderAdapter.encode` 加 `@torch.no_grad()`。
   - 是否阻止静态 APPROVE：**否**；是否必须在首次 GPU 运行前关闭：**是**。

### LOW

1. **PASS/FAIL 判据未显式检查 "systematic suffix-dependent change"。**
   - 证据：`verify_r08_z0_suffix_invariance.py:217` 仅判断 `max_abs <= atol`。
   - 说明：R08 supplement `:476-496` 定义强 PASS 为 bitwise identical，容忍 PASS 为 `max_abs <= 1e-6` 且无系统性 suffix-dependent 信号。当所有 anchor 的 `max_abs <= 1e-6` 时，系统性信号已被上限约束；因此工具判据与 supplement 的容忍 PASS 等价。可作为 LOW 观察，不阻塞。

2. **JSON 未记录首帧 / VAE 输入的 SHA256，仅记录 z0 摘要。**
   - 证据：`verify_r08_z0_suffix_invariance.py:165-173` 仅将 z0 metrics 写入 record。
   - 说明：sidecar 已保存完整 z0_a/z0_b；若需更强 provenance，可在 record 中增加 `first_frame_sha256` 与 `input_after_resize_sha256`。不阻塞。

3. **`verify_r08_z0_suffix_invariance.py:38-41` 的 `_git_commit` 未处理 dirty tree。**
   - 证据：仅记录 `HEAD` commit，未通过 `git status --porcelain` 标记是否有未提交修改。
   - 说明：当前审计文件本身未提交，但 `root_commit` 仍指向 `a3d11a8`。建议补充 `dirty: bool` 字段，避免未来在有工作区修改时误报 reproducibility。不阻塞。

---

## 4. 已核验的关键源码锚点

- `tools/g0/verify_r08_z0_suffix_invariance.py:114-128` — A/B 对构造
- `tools/g0/verify_r08_z0_suffix_invariance.py:131-137` — 原始视频加载 + VideoResize
- `tools/g0/verify_r08_z0_suffix_invariance.py:145-148` — LIBEROLeRobotDataset 初始化（concat_view、无 cache）
- `tools/g0/verify_r08_z0_suffix_invariance.py:161-163` — z0 encode（缺少 no_grad）
- `tools/g0/verify_r08_z0_suffix_invariance.py:184-194` — CLI 参数与覆盖率默认值
- `tools/g0/verify_r08_z0_suffix_invariance.py:217` — PASS/FAIL 判据
- `tools/g0/verify_r08_z0_suffix_invariance.py:218-250` — sidecar + JSON + provenance
- `tools/g0/exact_window_cache.py:28-43` — uint8 转换与 encode_window
- `cosmos_framework/data/generator/action/datasets/base_dataset.py:202` — 训练侧 uint8 转换
- `cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:448-465` — concat_view
- `cosmos_framework/data/generator/action/utils/transforms.py:362-413` — VideoResize
- `cosmos_framework/data/generator/utils.py:45-51` — `VIDEO_RES_SIZE_INFO["256"]`（含 192×320）
- `cosmos_framework/model/generator/vision_vae.py:12-13` — exact duration constants
- `cosmos_framework/model/generator/vision_vae.py:24-30` — `encode_uint8_vision_item`
- `cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py:1451-1460` — `Wan2pt2VAEInterface.encode`

---

## 5. 已执行的只读命令

```bash
# 1. 确认 HEAD
git -C /gemini/code/psm_wma rev-parse HEAD
# a3d11a8ccae47e93df61655b0b2f5d959cd87f9a

# 2. 脚本语法检查
/root/venvs/psm_wma/bin/python -m py_compile tools/g0/verify_r08_z0_suffix_invariance.py
# PASS

# 3. 核对关键函数位置
grep -n "def encode\|class Wan2pt2VAEInterface\|VIDEO_RES_SIZE_INFO" \
  cosmos-framework/cosmos_framework/model/generator/tokenizers/wan2pt2_vae_4x16x16.py \
  cosmos-framework/cosmos_framework/data/generator/utils.py
```

---

## 6. 未执行的验证及原因

| 未执行项 | 原因 |
|---|---|
| 实际 GPU 运行 Gate-0 | 用户明确 "尚未跑 GPU"；本次为代码静态审查。 |
| 验证 VideoResize 对 uint8 的输出尺寸 | 可由 `VIDEO_RES_SIZE_INFO` 与 `find_closest_target_size` 静态推导；运行时验证在首次 GPU 执行后补充。 |
| 检查 `exact_window_cache.py` 的 `encode_window` 在 bf16 下的数值 | 依赖实际 VAE 运行；静态审查无法完成。 |

---

## 7. 结论

- ✅ Gate-0 工具整体满足 R08 supplement 的合同：真实 concat/uint8/VideoResize/Wan exact-duration 复用、A/B 首帧相同 suffix 不同、>=64 覆盖、只比 z0、JSON+sidecar+provenance、不读 cache latent、无 history/R09。
- ⚠️ **必须在首次 GPU 运行前关闭 MEDIUM-1**（增加 `torch.no_grad()`），否则有显存浪费/OOM 风险。
- LOW-1/2/3 不阻塞，可在后续顺手补齐。

**静态审查结论：APPROVE；关闭 MEDIUM-1 后即可启动 GPU Gate-0。**
