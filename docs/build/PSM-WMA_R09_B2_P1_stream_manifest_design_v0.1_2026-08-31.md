# R09-B2 P1 可强制 Window-ID Stream Manifest 设计 v0.1

**状态**：DRAFT；仅请求方案审核。不得据此修改 `cosmos-framework`、加载模型、读取训练 batch、执行训练、评测或推理。

## 1. 目的

P0 已关闭为 `BLOCKED`：相同 seed 不能证明 recurrent 与 `ttt_fast_weight`
消费同一批窗口。P1 的唯一目的，是为未来 B2-T 定义一个可生成、可消费、可逐项
审计的有序 window stream。它只解决 P0 blocker 1，不解决 capture、optimizer
inventory、D005 或完整 config diff。

## 2. 已确认的现状与缺口

- `LIBEROLeRobotDataset._build_item()` 由 flat `idx` 映射 episode 与 local
  `start_frame`，并已把 `episode_index`、`task_index`、`start_frame` 放入 sample
  extras（`cosmos_framework/data/generator/action/datasets/libero_lerobot_dataset.py:405-456`）。
- `ActionIterableShuffleDataset` 按 episode block 做 epoch shuffle、再在 episode
  内顺序遍历；worker/rank 分片及无限 epoch 在其 `__iter__()` 内完成
  （`action_sft_dataset.py:48-94`）。
- 单卡 4-suite recipe 的 `IterativeJointDataLoader(seed=None)` 固定 round-robin
  suite，但每个 suite 下仍是独立 PyTorch DataLoader；当前 `num_workers` 可大于 0
  且 `in_order=False`（`action_policy_libero_edge_all.py:101-194`）。因此现状无法
  从“seed 相同”推出实际窗口顺序相同。

## 3. 冻结的 P1 contract

未来 B2-T 的 manifest 是**全局消费序列**，不是仅按 suite 排序的候选全集。每条
JSONL record 必须为：

```json
{"ordinal": 0, "epoch": 0, "optimizer_update": 0, "microbatch": 0,
 "sample_in_microbatch": 0, "suite": "libero_spatial", "task_id": 0,
 "episode_index": 402, "start_frame": 1, "dataset_flat_index": 0}
```

其附属 JSON header 必须绑定：schema version、root/submodule/Gitlink、四个
cache `dataset_manifest.json` SHA256、raw dataset `info.json`/parquet index SHA256、
recipe TOML SHA256、suite order、episode-shuffle seed、world size、microbatch、
grad accumulation、required optimizer updates、总 record 数与 JSONL SHA256。

`ordinal` 是 canonical identity；五元组是可读/跨实现 identity；
`dataset_flat_index` 只是通过现有 map-style dataset 重建同一窗口的内部定位符，
不得代替五元组审计。

## 4. 生成与消费

1. 新 root-only builder（后续实现申请）从四 suite 的 current dataset/cache
   contract 枚举合法 flat indices，按当前 episode-block shuffle 语义和
   `IterativeJointDataLoader(seed=None)` 的 1:1:1:1 suite 轮转，生成**恰好**
   `100 × grad_accum_iter × max_samples_per_batch` 条 record；不足即 fail。
2. B2 专用 manifest-aware dataset wrapper 只接受该 suite 的连续 manifest slice，
   对每条 record 以 `dataset_flat_index` 取样后硬校验返回的
   `(suite, task_id, episode_index, start_frame)`；不匹配、缺 cache window、重试
   重采样或越界均立即 fail，绝不随机补样。跨 epoch 重复同一 window 是 baseline
   `ActionIterableShuffleDataset` 的既有无限流语义；记录必须显式带 `epoch`，以
   `(ordinal, epoch, suite, task_index, episode_index, start_frame)` 唯一标识一次消费，
   不得把跨 epoch 重复误判为数据错误。
3. 为使 global ordinal 有实际意义，B2 专用 launcher 必须冻结 `world_size=1`、
   每 suite `num_workers=0`、关闭 DataLoader 的乱序交付；不得复用当前
   `ActionIterableShuffleDataset` 的无限 worker stream。
4. 每个 packed microbatch 将其 record IDs 保留到 batch metadata。一个
   capture-only observer 只追加 observed JSONL（不修改 model/optimizer/RNG/
   cursor）；B2 verifier 逐 ordinal 比较 requested 与 observed，而不仅比较 hash。
5. resume 只能由 `(optimizer_update, microbatch)` 转成 manifest offset，重启后
   消费剩余 slice；不得调用基于 RNG 的 skip/fast-forward。

## 5. 明确不做的事

- 不改变 LIBERO window/camera/action/cache/Local 算法；cache key 仍是 suite 内
  `(episode_index,start_frame)`。
- 不生成或读取 VAE、模型、optimizer、训练 batch；manifest builder 仅做 CPU
  metadata/index 审计。
- 不允许 B2-T、GPU、评测、推理、closed-loop 或 backend freeze。

## 6. 后续实现验收

- 两次独立生成同一输入产生 byte-identical header/JSONL SHA256；任一 source
  SHA、window count、world size 或预算变更均 fail。
- 故意交换一条 record、改 suite 或 start_frame、缺少 cache window、worker>0、
  或 observed ordinal 缺失，均必须 fail；同一 epoch 内 duplicate/ambiguous identity
  必须 fail，跨 epoch 的同一 window 则必须保留并以不同 `ordinal`/`epoch` 区分。
- 一次不加载模型的 CPU-only manifest-aware stream replay，requested/observed
  count、ordinal 与五元组逐项相同；不得把这项称为训练或 B2-T。

## 7. 待审核的最小修改面

预计后续仅新增 root `tools/g0` 的 manifest builder/verifier 和子模块
`action_sft_dataset.py` 的小型 manifest-aware wrapper，配方只在 B2 专用 launcher
显式使用该 wrapper。因涉及 `cosmos-framework` 数据路径，须先获得新的三方
`APPROVE_TO_IMPLEMENT_B2_P1`；本设计本身不授权实现。
