# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.11

**状态**：v0.10 已获三方同 SHA `APPROVE_TO_IMPLEMENT`（root `b08ca7b`/Gitlink `dce279a`）并保持有效；本 v0.11 是**实现前评估发现缺口后的 docs-only remediation**，待三方同 SHA 设计审核。仅冻结 terminal provenance 与相应的最小白名单扩增，不授权实现、GPU 或训练。
**基线**：v0.10（root `b08ca7b`）获 ChatGPT=`3d19a46`、Kimi、MM 同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`。除本文件新增条款外，v0.10 及其继承链全部条款不变。

## 1. 缺口：terminal 信号无数据来源（实现前评估的精确证明）

冻结设计（v0.1 §4 / v0.8 §2，经 v0.9/v0.10 逐条继承）要求 owner=episode 的 segment 在满 `ttt_tbptt_steps`(=16) 或 **terminal remainder** 时于该 window 自己的 forward 内 materialize 建 witness 图；terminal 必须在 window 当下可知——witness 必须被同一 micro-batch 的唯一一次 backward 遍历，迟一拍即破坏「每 micro-batch 恰好一次 backward」合同。

评估证明当前无任何合法数据来源：

1. **dataset 不导出 terminal/episode 长度**：LIBERO 样本仅含 `episode_index/start_frame/task_index/window_frame_indices/latent_source_frame_indices/verify_cached_latent` 与 history 键（`libero_lerobot_dataset.py:441-456` extras，经 `base_dataset.py:187-213` `_build_result` 透传）；joint loader 只加 `dataset_name`。terminal 判定所需 `kept_counts[ep]` 仅是 dataset init 局部变量（`libero_lerobot_dataset.py:205,211`），不作为属性保存、不导出。
2. **source audit 早已记录该缺口**：`PSM-WMA_R09_B_TTT_source_audit_v0.2_2026-09-03.md:221`——「当前无 segment schema 或 done 字段……新 sequence manifest/adapter 显式给 `segment_id,offset,valid,is_episode_start,is_episode_end`」。audit 时已知，但 active wiring 白名单（v0.9 §2 / v0.10 §3）未包含任何数据侧文件。
3. **batch 内 lookahead 推导不可行，永不采用**：manifest stream 仅保证同一 owner 的 window 在流内连续（v0.6 :9 连续 run 不变量）；micro-batch 边界可截断 owner run（owner 延续到该 suite 的后续 micro-batch），而 forward 只见当前 batch，无法区分「episode 结束」与「batch 截断」；iterable shuffle 路径（num_workers=12 交错）更不可得。延后一拍建 witness 图违反 v0.8 §2 冻结时序。
4. **结论**：terminal 必须由数据侧显式提供；这超出 v0.10 §3 已批准白名单，按既定 remediation 模式以本 v0.11 冻结后再实现。

## 2. 冻结决议：manifest-route terminal provenance

采用 source audit :221 的既定方向（sequence manifest 显式给 `is_episode_end`），四处最小 additive 改动：

1. **root `tools/g0/build_r09_b2_stream_manifest.py`**：每条 record 新增 `"is_episode_end": bool`。语义：**真实 episode 终止**——`start_frame` 等于该 episode 最后一个 valid window 的 `start_frame`（即该 episode valid window 计数 − 1；builder 持有 `LIBEROLeRobotDataset` 实例，可经 `_valid_cum`/`_ep_vals` 精确判定）。显式禁止以「manifest 内该 episode 出现的最大 start_frame」近似——manifest 可在 episode block 中途截断，近似会让被截断 episode 的 segment 永不关闭。其余 record 字段、顺序、seed 与 SHA 语义不变；header `schema_version` 保持 `r09_b2_stream_manifest_v1`（additive 字段由 verifier required set 承载）。
2. **root `tools/g0/verify_r09_b2_stream_manifest.py`**：`required` 集合增 `is_episode_end`；新增断言——每个 `(suite, epoch, episode_index)` 组内**恰好一条** `is_episode_end=true` 且位于该组最大 `start_frame`（verifier 已重建 dataset identity/`reverse_index`，可独立重算真实 terminal）。旧 manifest 因缺键 FAIL，强制重新生成。
3. **child `cosmos_framework/data/generator/action/datasets/action_sft_dataset.py`**：仅 `B2ManifestAwareIterableDataset.__iter__` 增 additive attach——`item["is_episode_end"] = torch.tensor(bool(record["is_episode_end"]), dtype=torch.bool)`（与既有 `b2_stream_ordinal` 等键同模式，:139-142）；record 缺该键 → `ValueError` fail-closed。非 manifest 路径与 iterable shuffle 路径零改动。
4. **model 侧消费（已在 v0.10 §3 白名单内，无新文件）**：`local_ttt_enabled=True` 时 TTT seam 要求 `data_batch` 含 `is_episode_end`，缺失即 `raise` fail-closed（覆盖非 manifest 路径误入）；owner key 仍为 `(dataset_name, episode_index)`——terminal commit→reset 后 C5A 允许同 owner 新 epoch 从 timestep 0 重新 admission（C6 v0.4 已冻结），epoch 不进入 owner key。

`local_ttt_enabled=False` 时：wrapper attach 仍发生（additive data 键），model 不读取；disabled parity 四判据（参数集合、`keys_to_select`、forward 零新分支、composed config 恰 5 字段）全部不受影响。

## 3. 白名单扩增（本次仅新增三项 + 相邻测试）

在 v0.10 §3 文件集合上仅新增：

- root `tools/g0/build_r09_b2_stream_manifest.py`（additive record 字段）；
- root `tools/g0/verify_r09_b2_stream_manifest.py`（required set + terminal 断言）；
- child `cosmos_framework/data/generator/action/datasets/action_sft_dataset.py`（仅 `B2ManifestAwareIterableDataset.__iter__` attach + 缺键 fail-closed）；
- 相邻测试：child `action_sft_dataset` 相邻测试增 wrapper attach/缺键 fail-closed fixture（合成 records + stub dataset，CPU）；root 侧 builder/verifier 遵循 `tools/g0` 既有 stdlib unittest 模式增补。

`libero_lerobot_dataset.py` 明确**不修改**：terminal provenance 单一来源为 manifest record，不经 dataset 导出。

## 4. 验收增补（CPU/static）

- child pytest：wrapper 对含/缺 `is_episode_end` 的 record 分别 attach/`raise`；合成 terminal=True/False 样本驱动 lifecycle terminal 时序（并入 v0.9 §3 既有 N=1/3/16/terminal 验收矩阵）。
- root stdlib unittest：builder 对每 episode 恰好末尾 valid window 标记 `is_episode_end=true`（含 block 中途截断不误标负例）；verifier 对 terminal 位篡改/缺失 fail-closed。
- 真实 manifest 重新生成 + verifier PASS 属真实数据 I/O，归入 ⑪ GPU smoke Runbook 的前置资产步骤，不在本 CPU/static Gate 内。

## 5. 继承与范围

v0.10 全部条款逐条继承（单阶段 commit、external-backward 双证据生命周期、terminal/skip 语义、pre-write witness、disabled parity、config/owner/selector/checkpoint 边界、v0.10 §3 文件集合）。本 v0.11 仍不授权实现之外的任何真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.11 为准；其余条款继承 v0.10–v0.1 及其引用的 C5A design v0.6、production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
