# R08 Gate-0 GPU Runtime 复审 — 2026-08-28

- 复审目标：根仓 `V2@e7fb1ec3f612bb829c5970029fdee701d3b82b57`
- 运行时代码基线：`V2@5ff9327468aa7c507b528c5fc8095c33df3dde02`（工具脚本与 8778b7e 无差异；e7fb1ec 仅提交产物与文档）
- 子模块：`10bc41085de448d60d2f71b342c03a4cfcca9ee1`
- 复审文件：
  - `artifacts/g0/r08/gate0_z0_suffix_invariance.json`
  - `artifacts/g0/r08/gate0_z0_suffix_invariance.pt`
  - `tools/g0/verify_r08_z0_suffix_invariance.py`
  - `docs/collab/chatgpt/CODEX_INBOX.md`（含 5188a5a scope adjustment）
- 复审性质：只读，不修改文件，不重跑 GPU
- 结论：**APPROVE_TO_CLOSE**

---

## 1. 复审命令与独立验证

```bash
cd /gemini/code/psm_wma

# 1. 提交范围确认
git diff 8778b7e..5ff9327 -- tools/g0/verify_r08_z0_suffix_invariance.py
# 无 diff：GPU 运行时使用的工具与 Kimi 静态 APPROVE 版本一致

git diff --stat 5ff9327..e7fb1ec
# 仅新增 artifact JSON/log + SESSION/TODO + CODEX_INBOX，无工具代码变更

# 2. sidecar SHA256 核对
sha256sum artifacts/g0/r08/gate0_z0_suffix_invariance.pt
# 154f18cd8de9e0a065ef9c766649550b6e456723a3a72b708a3dfb22b9d96e5f

# 3. Python 独立校验（JSON + sidecar）
/root/venvs/psm_wma/bin/python - <<'PY'
import hashlib, json, torch, pathlib
json_path = pathlib.Path('artifacts/g0/r08/gate0_z0_suffix_invariance.json')
pt_path = pathlib.Path('artifacts/g0/r08/gate0_z0_suffix_invariance.pt')

sha = hashlib.sha256(pt_path.read_bytes()).hexdigest()
data = json.loads(json_path.read_text())
assert data['sidecar']['sha256'] == sha
assert data['status'] == 'PASS_STRICT_BITWISE'
assert data['anchor_count'] == 128
assert len(data['records']) == 128
for rec in data['records']:
    assert rec['first_frame_bitwise_equal'] is True
    assert rec['suffix_pixel_bitwise_different'] is True
    fp = rec['input_fingerprints']
    assert fp['first_frame_sha256_a'] == fp['first_frame_sha256_b']
    assert fp['suffix_sha256_a'] != fp['suffix_sha256_b']
    assert fp['suffix_changed_pixel_count'] > 0
    assert rec['z0']['bitwise_equal'] is True and rec['z0']['max_abs'] == 0.0
    assert rec['repeat_control']['bitwise_equal'] is True and rec['repeat_control']['max_abs'] == 0.0
for suite, cov in data['coverage']['by_suite'].items():
    assert len(cov) == 4
    for c in cov:
        assert c['anchor_count'] == c['unique_episode_count'] == c['unique_task_count'] == c['required_unique_task_count'] == 8

car = torch.load(pt_path, map_location='cpu', weights_only=False)
assert car['schema_version'] == 'r08_z0_suffix_invariance_sidecar_v1'
assert len(car['pairs']) == 128
for p in car['pairs']:
    assert torch.equal(p['z0_a'], p['z0_b'])
    assert torch.equal(p['z0_a'], p['z0_a_repeat'])
    assert p['z0_a'].shape == (48, 12, 20)
print('all invariants PASS')
PY
# 输出：all invariants PASS
```

---

## 2. 关键字段核查

| 核查项 | 位置 | 结果 |
|---|---|---|
| Status | `gate0_z0_suffix_invariance.json:3` | `PASS_STRICT_BITWISE` |
| Anchor 总数 | `:6` | 128 |
| Canonical atol | `:5` | `1e-6` |
| Sidecar 路径与 SHA | `:161-165` | `artifacts/g0/r08/gate0_z0_suffix_invariance.pt`，SHA256 与文件实测一致 |
| Coverage | `:7-142` | 4 suites × 4 remainders × 8 anchors；每 remainder 8 unique episodes、8 unique tasks |
| z0 shape | 每条 record | `[48, 12, 20]`，对应 concat 256×512 → resize 192×320 → VAE /16 |
| 输入指纹 | 每条 record `input_fingerprints` | 首帧 SHA256 A/B 一致；suffix SHA256 不同；changed pixel count > 0 |
| z0 A/B 比较 | 每条 record `z0` | `bitwise_equal=true`、`max_abs=0.0`、`l2=0.0` |
| A repeat 控制 | 每条 record `repeat_control` | `bitwise_equal=true`、`max_abs=0.0` |
| Determinism | `:6336-6341` | `cublas_workspace_config=:4096:8`、`cudnn_benchmark=false`、`cudnn_deterministic=true`、`deterministic_algorithms=true` |
| Provenance | `:6312-6344` | 记录 dataset_root、vae_path、argv、seed、device、hostname、时间戳 |

---

## 3. 运行环境与首次失败说明

- 首次运行 `artifacts/g0/r08/gate0_z0_suffix_invariance.log` 在 VAE 加载成功后、首个视频解码前失败：
  - 根因：`torchcodec` 导入时找不到 venv cu13 的 `libnppicc.so.13`。
  - 性质：启动环境 `LD_LIBRARY_PATH` 配置问题，未进入任何 encode 逻辑，不构成 Gate FAIL。
- `attempt2.log` 在预检环境变量后成功，128 anchors 全部 `max_abs=0.000e+00`。

---

## 4. 解释与 scope 对齐

按 `docs/collab/chatgpt/CODEX_INBOX.md` 中 5188a5a 的 scope adjustment，Gate-0 已从“研究硬 Gate”降级为 **Wan z0 causal-contract sanity check**：验证当前 Cosmos wrapper / exact-duration / chunking / bf16 / deterministic runtime 路径**没有破坏** Wan2.2 官方的 causal key-frame-prime 契约，而不是在探索性地证明 Wan2.2 本身的因果性。

本次结果：

- 在 128 个独立 A/B 对中，替换未来 16 帧 suffix 后 `z0` 完全 bitwise 不变；
- 同一输入重复 encode 也 bitwise 不变；
- 输入指纹证明 suffix 确实不同（changed pixel count 约 2M，max pixel diff 最高 252）。

因此 **Cosmos 包装路径的 z0 因果契约 sanity check 通过**，可以按补充设计继续 R08 Step 2（causal history dataset contract / alignment），无需再追加 z0 因果性实验。

---

## 5. 发现与建议

- **无 BLOCKER/HIGH/MEDIUM**。
- **LOW-1（provenance commit 差异）**：`provenance.root_commit` 记录为 `5ff9327`（运行时 HEAD），而本次复审目标/产物提交为 `e7fb1ec`。差异原因是 `e7fb1ec` 仅用于把运行时产物和文档提交入库，工具脚本与运行时一致（`git diff 8778b7e..5ff9327` 对工具为空）。此差异已理解，不推翻 Gate，但建议在 R08 后续 provenance 中若需要严格“运行时 HEAD == 审查 HEAD”，可让 runner 在提交产物前再次 `git rev-parse HEAD` 并在 SESSION 中说明。
- **LOW-2（sidecar 保留）**：JSON `:165` 写 `retain until independent Gate-0 review closes`。本次独立 review 已关闭，sidecar 可继续作为 R08 历史证据保留，不建议删除。

---

## 6. 结论

**G0-R08-GATE0-Z0-SUFFIX-INVARIANCE 可关闭。**

下一步（仍禁止提前进入 R09）：R08 Step 2 causal history dataset contract + Step 3 alignment tests。
