# R08 Step 2 Causal-History Data Contract 审查 — 2026-08-28

- 审查目标：根仓 `V2@94a95c623906e951c8a439966e184d1ac7b684de`，子模块 `v2@31983c57057498c210efde4c7c57b392f997d235`
- 审查范围：`cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py`、`cosmos_framework/data/generator/action/datasets/action_sft_dataset.py`、下游 `ActionTransformPipeline` 传播
- 审查性质：只读静态 + CPU 数据 smoke；未跑 GPU/训练/模型
- 结论：**REQUEST_CHANGES**
  - 数据侧因果合同（`j<t`、同 episode、padding+mask、无 target 泄漏、cache-z0 [96]、action normalization 复用）均正确。
  - 但 `history_action` 与现有 `ActionTransformPipeline` 的 `history_action` 钩子命名冲突，导致历史动作被吞进 native action 条件流，无法作为 Local evidence 传播；且训练配置未暴露 `local_history_horizon`，H>0 无法从 recipe 启用。

---

## 1. 已核验通过项

| 检查点 | 证据 | 结果 |
|---|---|---|
| H=0 默认关闭 | `libero_lerobot_dataset.py:95` `local_history_horizon=0`；`:467-468` 直接返回 `{}` | ✓ |
| `j < t` 严格因果 | `:469-471` `available = min(horizon, local_start_frame)`，`source_rows = np.arange(start - available, start)` | ✓ |
| 同 episode 边界 | `available <= local_start_frame` 保证 `source_rows >= ep_start`；不会跨 episode | ✓ |
| target/predicted action 不泄漏 | 历史用 `_row_action[start-available:start]`；当前 target 用 `_row_action[start:start+chunk_length]`；无重叠 | ✓ |
| left padding + mask | `:473-477` mask 全 False，frame/global indices 填 -1；`:508-510` valid 段填真实值 | ✓ |
| cache-z0 → [96] | `:507` `F.adaptive_avg_pool2d(latent[0].unsqueeze(0), output_size=(1,2)).flatten()` | ✓ |
| state raw [8] | `:480` `state_raw` shape `(horizon, 8)`；`:192-195` 断言 shape 与 finite | ✓ |
| action normalization 复用 | `:496-499` 用 `normalize_action(raw_action, self.action_normalization, self._load_norm_stats())`，与 target action 同一 stats | ✓ |
| timestamp / global row 对齐 | `:510-512` `global_row_indices` 和 `dt_s` 来自同一张排序后的 parquet 表 | ✓ |
| py_compile / diff-check | 双文件均 PASS | ✓ |

---

## 2. 独立 CPU Smoke

```bash
cd /gemini/code/psm_wma
PYTHONPATH=/gemini/code/psm_wma/cosmos-framework \
  /root/venvs/psm_wma/bin/python - <<'PY'
from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset

ds = LIBEROLeRobotDataset(
    root='/gemini/code/datasets/nvidia_LIBERO_LeRobot_v3/libero_spatial',
    split='full',
    latent_cache_root='/gemini/code/datasets/libero4in1_wan2.2vae_latent_cosmos_style/libero_spatial',
    latent_cache_verify_ratio=0.0,
    local_history_horizon=16,
)
print('len', len(ds))

# 1) episode start: all padding
s0 = ds[0]
assert s0['start_frame'].item() == 0
assert s0['history_mask'].sum().item() == 0
assert (s0['history_frame_indices'] == -1).all()

# 2) full history later in episode
import numpy as np, torch
idx = int(ds._valid_cum[0]) - 1
s1 = ds[idx]
valid = s1['history_mask'].sum().item()
assert valid == 16
start = s1['start_frame'].item()
assert (s1['history_frame_indices'][s1['history_mask']] < start).all()
assert s1['history_visual_summary'].shape == (16, 96)
assert s1['history_state_raw'].shape == (16, 8)
assert s1['history_action_raw'].shape == (16, 10)
assert s1['history_action'].shape == (16, 10)
assert torch.equal(s1['history_age_steps'][s1['history_mask']], torch.arange(16, 0, -1, dtype=torch.long))
assert (s1['history_dt_s'][s1['history_mask'], 0] > 0).all()
print('CPU smoke PASS')
PY
```

结果：`len 46058`，H=0/partial/full 边界、shape、index、age/dt 全部断言通过。

---

## 3. 发现的问题

### HIGH-1：`history_action` 被 `ActionTransformPipeline` 吞进 native action 条件流

- **位置**：`cosmos_framework/data/generator/action/utils/transforms.py:746-752`
- **问题**：
  - 数据集 `_build_local_history` 返回 `history_action`（已归一化的历史动作），意图作为 R08 Local evidence；
  - 但 `ActionTransformPipeline.__call__` 会 `pop("history_action")` 并将其拼接到当前 `action` 张量前部；
  - `build_sequence_plan_from_mode` 随后把前 `H` 个动作标记为 `condition_frame_indexes_action`，改变原 WAM 的 action 位置/长度语义。
- **证据**：CPU smoke 经 `ActionSFTDataset` 后 `action.shape=(32,64)`、`action_raw.shape=(32,10)`，且输出字典中已无 `history_action`；`condition_frame_indexes_action=[0..15]`。
- **影响**：
  - 历史动作无法以独立字段形式进入 Local evidence encoder；
  - native action stream 被加长，与 R08 supplement 中 "Local 作为独立 optional clean modality"、"不修改 native Vision/Action mRoPE" 的边界冲突；
  - 下游 eval/postprocess 会按 32 步动作处理，破坏原有 16 步 action chunk 合同。
- **建议修复**：
  - 方案 A：将数据集侧 R08 Local 历史动作字段改名为 `local_history_action`（或 `history_action_norm`），避免与 `ActionTransformPipeline` 的 `history_action` 钩子冲突；后续 Local encoder 读取该字段。
  - 方案 B：在 `ActionTransformPipeline` 增加显式开关（如 `prepend_history_action=False`），R08 场景下关闭该拼接。
  - 推荐方案 A，保留现有 `history_action` 钩子给 DROID `use_state` 专用，R08 走独立 Local 字段。

### HIGH-2：训练 recipe 未暴露 `local_history_horizon`

- **位置**：`cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py:97-121`
- **问题**：`get_action_libero_sft_dataset` 已支持 `local_history_horizon`（`action_sft_dataset.py:248,279`），但 `action_policy_libero_edge_all.py` 调用时未传入，也未通过环境变量/配置项暴露。
- **证据**：全仓库搜索 `local_history_horizon` 仅出现在 `libero_lerobot_dataset.py` 与 `action_sft_dataset.py`；recipe 中无对应字段。
- **影响**：无法从现有 TOML/配置启动 H>0 的训练；H>0 只能手写数据集实例使用。
- **建议修复**：在 `action_policy_libero_edge_all.py` 增加 `PSM_LOCAL_HISTORY_HORIZON` 环境变量（默认 0），并传入 `get_action_libero_sft_dataset`。

### MEDIUM-1：`history_state_raw` 未做 per-dim 归一化

- **位置**：`libero_lerobot_dataset.py:480,515`
- **问题**：state 以 raw float32 [8] 直接输出，未按 supplement §8 用训练集统计量做 `state_norm`。当前没有生成/加载 state stats 的逻辑。
- **影响**：后续 Local encoder 输入量级与 action/visual 不一致；但属于可延迟到 encoder 实现的步骤，不阻塞 data contract 审查。
- **建议修复**：在 Step 4/5 实现 Local encoder 时补充 state 统计量与归一化；或在 dataset 中增加可选 `state_normalization` 与 stats 路径。

### MEDIUM-2：缺少落盘的 CPU 证据脚本

- **位置**：`tools/g0/` 下只有 `audit_r08_source.py` 与 `verify_r08_z0_suffix_invariance.py`
- **问题**：本次审查的 CPU smoke 是临时写的，仓库里没有可复用的 H=0/partial/full/episode-boundary 检查工具。
- **影响**：后续 Agent 无法快速回归验证 history contract。
- **建议修复**：新增 `tools/g0/verify_r08_history_alignment.py`，覆盖：
  - H=0 无 history 字段；
  - partial/full history 的 mask、index、age、dt；
  - 同 episode、j<t、不与 target rows 重叠；
  - cache-z0 shape [96]、state shape [8]、action shape [10]；
  - 不依赖 GPU。

### LOW-1：`_load_cached_latent` 默认 shape fallback 与真实 cache 不符

- **位置**：`libero_lerobot_dataset.py:380`
- **问题**：fallback `expected_shape = (5, 48, 16, 32)`，而当前 256 分辨率 cache 真实 shape 为 `(5, 48, 12, 20)`。
- **影响**：只有在 `_validate_latent_cache_manifest` 未被调用时（例如直接调用 `_load_cached_latent` 或 manifest 缺失）才会触发 shape mismatch；正常路径因 manifest 校验而安全。
- **建议修复**：将 fallback 改为从 manifest 读取；若必须 hard-code，至少与当前 256 配置一致。

---

## 4. 判定

- **数据合同核心**：PASS
- **loader/配置传播**：FAIL（HIGH-1/HIGH-2）
- **总体**：REQUEST_CHANGES

必须在以下修复后重新审查：
1. 解决 `history_action` 与 `ActionTransformPipeline` 的命名冲突/语义冲突；
2. 在训练 recipe 中暴露 `local_history_horizon`；
3. （建议）新增落盘 CPU 证据脚本。

修复完成前，不要进入 R08 Step 4/5（LocalEvidenceEncoder / LocalReplayReadout）的 GPU 实验。
