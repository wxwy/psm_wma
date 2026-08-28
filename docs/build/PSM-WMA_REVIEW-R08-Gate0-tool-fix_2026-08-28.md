# R08 Gate-0 工具修复复审 — 2026-08-28

- 复审目标：根仓 `V2@8778b7e3d0504040dd12b1eddaa9fabe32b69759`
- 子模块：`10bc41085de448d60d2f71b342c03a4cfcca9ee1`
- 复审文件：`tools/g0/verify_r08_z0_suffix_invariance.py`
- 复审性质：只读静态审查 + 轻量 CPU 单测；不加载 VAE、不跑 GPU、不改文件
- 结论：**APPROVE**。此前 ChatGPT 审查提出的 HIGH-1、MEDIUM-1/2/3 均已关闭，可进入 GPU Gate-0 实跑。

---

## 1. 已关闭的阻塞/重要问题

| 原问题 | 严重级别 | 修复位置 | 修复内容 | 关闭依据 |
|---|---|---|---|---|
| VAE encode 未脱离 autograd | HIGH-1 | `tools/g0/verify_r08_z0_suffix_invariance.py:229-235` | `with torch.inference_mode():` 包裹三次 encode；encode 后 `detach().cpu().contiguous()` | 代码 + 单测：`_configure_determinism` 返回符合预期 |
| 未强制 deterministic runtime | MEDIUM-1 | `:84-99` | 校验 `CUBLAS_WORKSPACE_CONFIG=:4096:8`，设置 `cudnn.benchmark=False`、`cudnn.deterministic=True`、`torch.use_deterministic_algorithms(True)` | 代码 + 单测：三项布尔值均符合 |
| Anchor 选择未真正保证 task diversity | MEDIUM-2 | `:109-169`、`:314-318` | 按 `task_index → episode_index` 分层选择；每 remainder 要求 `unique_task_count >= required_unique_task_count`；输出 `coverage_by_suite` | 单测：4 episode/2 task 场景下 16 个 anchor 的 coverage 均满足断言 |
| Canonical atol 可由 CLI 调大 | MEDIUM-3 | `:37`、`:294-303` | 删除 `--atol` 参数，硬编码 `CANONICAL_ATOL = 1e-6`；状态分 `PASS_STRICT_BITWISE` / `PASS_TOLERANCE_ATOL_1E-6` / `FAIL` 三档 | 单测：`M.CANONICAL_ATOL == 1e-6`；`--help` 无 `--atol` |
| 缺少输入指纹 | LOW-1（推荐） | `:70-81`、`:248` | 新增 `first_frame_sha256_a/b`、`suffix_sha256_a/b`、`suffix_changed_pixel_count`、`suffix_max_abs_pixel_diff` | 已持久化到每条 record |

---

## 2. 代码一致性核查

1. **VAE 契约复用**：`encode_window` 调用 `vision_vae.encode_uint8_vision_item`，使用与训练/cache 一致的 `LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS = [17, 61, 73]` 和 `LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES`（`vision_vae.py:12-13`）。
2. **输入前处理链**：`to_training_uint8` → `VideoResize(resolution=None)` → `Wan2pt2VAEInterface.encode`，与 supplement §6.2 要求一致。
3. **只比 z0**：`encode_window(...)[0]` 仅取 temporal latent index 0。
4. **不读 cache、不改模型/历史/R09**：脚本作用域限定为 diagnostic-only，未引用 `latent_cache_root`。
5. **A/B 构造正确**：`_make_pair` 强制首帧 bitwise 相等且 suffix 不同（`:189-194`）。

---

## 3. 轻量验证结果

```bash
cd /gemini/code/psm_wma
git diff --check a3d11a8..8778b7e -- tools/g0/verify_r08_z0_suffix_invariance.py
# PASS（无 trailing whitespace / conflict marker）

/root/venvs/psm_wma/bin/python -m py_compile tools/g0/verify_r08_z0_suffix_invariance.py
# PY_COMPILE_OK

PYTHONPATH=/gemini/code/psm_wma/cosmos-framework:/gemini/code/psm_wma/tools/g0 \
  CUBLAS_WORKSPACE_CONFIG=:4096:8 \
  /root/venvs/psm_wma/bin/python tools/g0/verify_r08_z0_suffix_invariance.py --help
# help 输出正确，无 --atol 参数

# 独立 CPU 单测（determinism / stratification / A-B construction / atol frozen）
# 全部 PASS，见上表
```

---

## 4. 遗留 LOW（不阻塞 GPU Gate-0）

- **LOW-1**：`_configure_determinism` 报错信息写 "before Python starts"，但实际是运行时检查；语义上仍是 fail-fast，不影响行为。
- **LOW-2**：`_different_suffix_start` 对 frame_count == 17 的 episode 会找不到 alternate suffix 而抛出 `RuntimeError`。本机 LIBERO 单 episode 帧数远大于 17，但若未来遇到极短 episode 会在 Gate-0 构造阶段直接失败；建议在首次 GPU 运行后视数据分布决定是否加 `frame_count >= WINDOW_FRAMES + 1` 的前置过滤。
- **LOW-3**：未实现可选的 "runtime z0 vs cache z0" sampled parity（ChatGPT LOW-2 推荐项）。该增强可让 Gate-0 artifact 更自包含，但不影响 Gate-0 本身的因果判定；可在 GPU 跑完后按需要追加。

---

## 5. 判定

- **REVIEW-R08-Gate0-tool-fix**：满足验收条件。
- 可进入下一步：**GPU Gate-0 实跑**，需记录 `sensitivity.json` 与 raw sidecar（`*.pt`），并在独立审查完成前保留 sidecar。
- GPU 运行前请确保环境变量已设置：`export CUBLAS_WORKSPACE_CONFIG=:4096:8`。
