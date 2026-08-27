# R07 Runtime Audit Log

> **SUPERSEDED（2026-08-27）**：本文件中关于 FSDP flat-handle / parameter-gradient
> probe 的诊断不再是 active recommendation。根因已实证为 Edge-4in1 继承 Nano 的
> `keys_to_select` 时漏选两组 Local 参数；子模块 `55a9109` 已仅追加
> `local_memory2llm` 与 `local_memory_modality_embed`。修复后的真实 optimizer step
> checkpoint 中三项 Local 参数均由严格零初始化更新为有限非零，parameter-update 证据
> 覆盖此前 `grad present=false` 的推断。后续 Gate 仅为 No-Memory parity 与同一训练后
> checkpoint 的 fixed-weight Normal/Zero/Shuffle sensitivity。

> 跨子仓视角的 R07 Local Memory 接入运行时审计。子仓代码改动归
> `cosmos-framework/cosmos_framework/`;本文件记录每次只读复核的状态、
> 关键产物路径、未关闭的 Gate 与最小修复建议。

最后更新：2026-08-27

---

## 1. 截至 2026-08-27 的可判证据

| 检查项 | 状态 | 证据 |
|---|---|---|
| 子模块 v2 HEAD = c24b14d | ✅ | `git -C cosmos-framework log --oneline -1` |
| 子模块 v2 含 `R07RuntimeProbeCallback` | ✅ | `cosmos_framework/callbacks/r07_runtime_probe.py` |
| 配方 `action_policy_libero_edge_all` 启用 probe | ✅ | `cosmos-framework/cosmos_framework/configs/base/experiment/action/posttrain_config/action_policy_libero_edge_all.py:196` |
| Normal 3-step 跑完且 loss 有限 | ✅ | `/opt/r07-smoke/local_normal3_probe.json`;loss = 0.854476 / 0.651021 / 0.856807 |
| iter2800 warm-start DCP load | ✅ | 日志 `kept_keys=552 dropped_keys=0`,`kept_read_items=549` |
| Local 三项 present=true / finite / max_abs=0.0 | ✅ | `local_normal3_probe.json` 内 `local_memory2llm_weight/bias`、`local_memory_modality_embed` |
| Local 三项 grad present=true | ❌ | **全部 present=false**(见 §2) |
| 旧 baseline (5b61762) No-Memory parity | ⏳ | Gate A 待跑 |
| save/reload DCP 一致性 | ⏳ | Gate B 待跑 |
| Normal / Zero / Shuffle 三模 loss 对比 | ⏳ | Gate C 待跑 |

> `kept_keys=552` 已包含 Local 三项 → 新模型 ckpt 键集覆盖 Local;`kept_read_items=549` 与 iter2800 旧键集差异的 3 个就是 Local 相关键(已落 Local 零初始化)。

---

## 2. FSDP flat FQN / Local grad 入口定位(本次只读复核)

### 2.1 FSDP 包装结构

- `cosmos-framework/cosmos_framework/model/generator/mot/parallelize_unified_mot.py:249-250` — 仅对 `language_model.model.layers[*]` 各 decoder block 调 `fully_shard`。
- `cosmos-framework/cosmos_framework/model/generator/mot/parallelize_vfm_network.py:90-94` — 对 **整个 vfm network** 调 `fully_shard`。

→ Local 三项(`local_memory2llm.weight/bias`、`local_memory_modality_embed`)不在任何 decoder block 的 `FlatParamHandle` 内,而是挂在**根 FSDPUnit** 的 `FlatParamHandle` 上。

### 2.2 torch 2.10 / venv `/root/venvs/psm_wma` 的真实 API

- `FSDPModule` **不再暴露 `_flat_param` 属性**(`dir(FSDPModule)` 无 `flat/param` 字样,仅 `unshard / reshard / set_* / _apply / _get_fsdp_state`)。
- 正确入口: `torch.distributed.fsdp._traversal_utils._get_fsdp_handles(module)` 返回所有 `FlatParamHandle`;每个 handle 的 `handle.flat_param._fqns`(Tuple[str,...])、`handle.flat_param._shard_param_infos`(Tuple[_ShardParamInfo,...])、`handle.flat_param.grad`(反向 + all-reduce 后的 sharded 梯度)。
- `FlatParameter` 类在 `torch/distributed/fsdp/_flat_param.py:202`,继承自 `nn.Parameter`。

### 2.3 现行 `R07RuntimeProbeCallback` 为何 grad 全部 present=false

`cosmos-framework/cosmos_framework/callbacks/r07_runtime_probe.py:67-90`:

```python
for module in model.modules():
    flat_parameter = getattr(module, "_flat_param", None)
    if flat_parameter is None:
        continue                # ← torch 2.10 下永远 miss
    ...
```

FSDP2 已不挂 `_flat_param` → 所有 module 被 continue → `summaries` 空 → 回退取 `adapter.weight.grad` 等已被 flat 替换的 `Parameter.grad` → 全为 `None` → **3 个 grad 全部 present=false**。

`on_training_step_start` 的 `register_hook` 路径同样失效:hook 跟随 `Parameter` 引用,fully_shard 把内存重定基到 FlatParameter 后,旧 hook 不会接到 FSDP 反向图回流的真实梯度。

> 即便 hook 路径生效,zero-init 下 `max_abs` 解析为零;但 `present=true` 仍可作为"反向确实回流到了 Local 张量"的最弱证据 —— 当前缺失。

### 2.4 最小修复建议(三选一,优先级 L1)

**L1(推荐):改用 `_get_fsdp_handles` + 在根 FlatParameter 上挂 `register_post_accumulate_grad_hook`**

- 在 `parallelize_vfm_network.parallelize_vfm_network` 末尾(`fully_shard` 之后),遍历所有 handle,找出 `flat_param._fqns` 含 `"local_memory"` 的 handle(根 handle)。
- 在 `handle.flat_param` 上注册 `register_post_accumulate_grad_hook`,回调里按 `_shard_param_infos` 切片 → `summary(slice)`。
- 优点:hook API 在 torch ≥ 2.4 推荐,FSDP 包装后挂到 FlatParameter 仍生效;与现有 `_tensor_summary` 字段直接对接,probe JSON schema 不变。

**L2(最小改动):只改 `R07RuntimeProbeCallback._fsdp_gradient_summaries`**

- 把 `getattr(module, "_flat_param", None)` 替换为 `_get_fsdp_handles(model)` 遍历。
- 优点:单文件改动,不动模型侧。
- 缺点:torch 内部 API 跨版本可能改名(锁 torch 2.10 即可)。

**L3(旁路法):反向结束后 `unshard()` 取 full grad**

- `handle.flat_param.unshard()` 后 `fp.grad` 为 unsharded full grad;按 `_shard_param_infos.numel` `torch.split` → 拿到 Local 3 项 full grad。
- 优点:确定性最强,不依赖 hook 时序。
- 缺点:需显式 `reshard()` 平衡。

---

## 3. 未关闭 Gate 的落地方案

### 3.1 Gate A — No-Memory parity

- 旧 baseline:`git worktree add /tmp/r07_old 5b61762`(无 Local 代码)
- 新无 Local:`c24b14d` + `local_memory_enabled=False`
- 同 seed、同 batch、`PSM_LOCAL_DUMMY_ENABLED=0`,对比 loss / grad_norm 差 ≤ 数值噪点(1e-4 量级)。

### 3.2 Gate B — save/reload DCP 一致性

- 触发 `/opt/r07-smoke/probe_normal3/checkpoints/iter_000000001/`(7 GB 已落)重新 DCP load,与 iter2800 对照 Local 三项 `max_abs ≤ 1e-6`。
- 已知差异:`kept_read_items=549 vs kept_keys=552` → 3 个差异键 = Local 三项;expect 一致(均 = 0)。

### 3.3 Gate C — Normal / Zero / Shuffle 三模对比

- `PSM_LOCAL_DUMMY_MODE=zero` 严格全 0(已收紧:`LocalDummyTransform` 不能再加 `sample_offset`)。
- `PSM_LOCAL_DUMMY_MODE=shuffle` 跨 batch payload 真实置换(已收紧:`JointDataLoader._iter_synchronous` 挂 `LocalDummyBatchShuffle`)。
- `PSM_LOCAL_DUMMY_MODE=normal` 默认 closed-form。
- 两两 loss 差 ≥ Local payload 实际贡献量级。

---

## 4. 产物清单(系统盘 `/opt/r07-smoke/`)

| 路径 | 描述 |
|---|---|
| `local_normal_probe.json` | Normal 1-step probe(JSON) |
| `local_normal3_probe.json` | Normal 3-step probe,3 iter loss/grad |
| `local_hook_probe.json` | r07_runtime_probe_v2 schema,single iter |
| `probe_normal3/logs/action_policy_libero_edge_all_sft.log` | Normal 3-step 训练日志 |
| `probe_hook/logs/action_policy_libero_edge_all_sft.log` | r07_runtime_probe 单步训练日志 |
| `probe_normal3/cosmos3_action_libero/.../checkpoints/iter_000000001/` | 7 GB DCP 检查点(已 save) |
| `/opt/Cosmos3-edge-generation-libero4in1/iter_000002800` | 17 GB warm-start 源 ckpt |

---

## 5. 任务跟踪

- 任务列表见本会话 TaskList。
- pending Gate A/B/C 与 probe 修复在 `#25/#26/#27/#28`。
