# PSM-WMA RGB 表示与 Memory 编码规划 v0.1

> 状态:active(2026-08-16,Kimi 第一技术审查者)
> 适用范围:G0-R06-SFT 及后续所有使用离线视觉 latent 的 Policy/WAM 训练。
> 与 `cosmos-framework/docs_zh/psm_wma/REGULAR_EPISODE_LATENT_OVERFIT.md` 的关系:该文档是**历史候选实验记录**,不是主线;本文件与 `MEMORY/DECISIONS.md` D013 为准。

## 1. 决策

Policy/WAM 的本地 RGB 编码采用 **Cosmos-native exact-window offline latent cache**:把当前在线训练路径的每个 17 帧窗口编码原样提前离线计算并缓存,训练时按 `(episode, start_frame)` 精确取用。不改变原生视觉分布,不为未来 Memory 形式预设任何 latent 语义(D010 延续)。

## 2. 实测契约(源码+运行证据)

- RGB window:17 帧(4n+1,n=4);action horizon:16(chunk_length=16);anchor:episode 内任意 start,`0 <= start <= T-17`。
- 采样分布:LIBERO 数据集窗口枚举为 **stride=1**(`libero_lerobot_dataset.py:185` `_valid_cum=cumsum(counts-16)`,`:199` `start=idx-prev` 不乘 stride;`sample_stride` 参数在 LIBERO 路径无效)。
- camera:concat_view = agentview(左)+wrist(右)水平拼接,单 vision item `[3,17,256,512]`(`libero_lerobot_dataset.py:359-362`);不启用 `enable_per_camera_vae_encoding`(`omni_mot_model.py:3535-3536`,action 数据集与 policy server 均不设置)。
- VAE:`Wan2pt2VAEInterface.encode`,输入 uint8→fp32 `/127.5-1.0`(`_normalize_uint8_vision_item` 契约,在线由 `_normalize_video_databatch_inplace` 完成),T=17 命中 `encode_exact_durations` 不 padding,feat_cache 每窗口清零;输出 `[1,48,5,16,32]`(spatial /16:16×32;temporal 17→5)。
- noising/loss 在 x0 注入之后:`_add_noise_to_input`(`omni_mot_model.py:1815-1933`)——condition_mask 条件帧 σ_eff=0 保持 clean、ε~N(0,I)、σ 按 waver 采样、rectified-flow 插值得 xt/vt、xt 转 bf16;action 独立 σ 加噪。cache bypass 只替换 x0 来源,全部保留。

## 3. 数据流

```
parquet episode → concat_view [T,3,256,512] → 窗口 [3,17,256,512] uint8
→ fp32 /127.5-1 → Wan2pt2VAEInterface.encode → [1,48,5,16,32] fp32
→ cache per-episode .pt: windows{start: latent[5,48,16,32] fp32}
→ dataloader(命中跳 RGB 解码,zeros 占位)→ model bypass → x0_tokens_vision fp32
→ condition_mask/ε/σ/rectified-flow 插值 → Transformer → vision FM + action FM loss
```

## 4. Cache schema(format `exact_window_v1`)

每 episode 一个 `.pt`(atomic 写、断点续跑复用 R12 机制),新目录,不覆盖 R12 历史 artifact:

```
episode_{index:06d}.pt
{
  "format": "exact_window_v1",
  "episode_index": int,
  "windows": { str(start_frame): {
      "latent": FloatTensor [5,48,16,32] fp32,        # [T_latent,C,H,W]
      "source_frame_indices": LongTensor [5],          # start, start+4, ..., start+16
      "global_row_indices": LongTensor [5],
  }},
  "language": {"instruction": str, "instructions": [str]},
  "metadata": {frame_count, window_frames=17, image_size=256, camera_layout="concat_view spatial-left-right",
               num_views=1, normalization="uint8/127.5-1", vae_path, script_revision, task_index, build_config}
}
+ dataset_manifest.json(schema_version, episode/window 计数, git rev, vae_path, image_size)
```

约束(对应任务 item 9):重叠窗口的 latent 各自独立编码、独立存储,**不做 dedup**;不假设不同窗口中同一 RGB endpoint 的 latent 数值相同。

## 5. 存储格式选型(item 8)

per-episode `.pt`(torch.save)+ `R12CosmosLatentCache` LRU(max_cached_episodes=8)。依据:sampler 按 episode 顺序流式读窗口(`ActionIterableShuffleDataset`),随机访问需求低;最坏内存 8 workers × 8 episodes × ~110MB(fp32)≈ 7GB < 32GB 容器;零新依赖。safetensors(memmap)与 npy/memmap 的随机访问优势在该模式下不必要,不引入。

## 6. 磁盘估算(LIBERO-4in1 实测 parquet 元数据)

1693 episodes / 276,475 帧;单窗口 latent fp32 = 480 KiB:

| stride | 窗口数 | fp32 裸量 | 说明 |
|---|---|---|---|
| 1 | 246,377 | 112.78 GiB | 原生分布(默认) |
| 2 | 123,188 | 56.39 GiB | 降采样备选 |
| 4 | 61,594 | 28.20 GiB | 降采样备选 |

分 dataset:libero_10: 379 ep / 95,405 win;libero_goal: 428 / 45,194;libero_object: 454 / 59,720;libero_spatial: 432 / 46,058。

## 7. 与 G0-R12 的关系

- 复用:窗口枚举/get_window_identity、atomic 写、断点续跑、parity 工具骨架、cache 消费骨架、cache bypass。
- supersede:R12 整段 episode 因果编码(2026-08-16 parity 实测与在线窗口路径不等价,max_abs_diff=4.625,对齐窗口仍 1.79)。旧 artifact 全部保留为 R12 Gate 证据,不覆盖、不沿用;新 cache 用新目录 + `exact_window_v1`。

## 8. 执行阶梯(全部需满足才推进)

1. one-sample online/offline parity(cache 构建编码 vs 在线路径同窗口,逐位/≤1e-6);
2. one-episode exact-window cache 构建;
3. index/alignment 验证(source_frame_indices、global_row_indices、窗口计数 == dataset valid_indices);
4. cached-latent 真实模型 forward(短时训练步,loss finite,与在线同 batch 数值对比);
5. multi-worker 小 loader smoke(num_workers>1,无重复/缺窗、RSS 有界);
6. 多 episode cache smoke;
7. 以上全过后,再决定是否执行 LIBERO-4in1 全量编码(单独授权)。

## 9. 已知遗留修复(执行前必须完成)

- builder `_encode_window` 补 `_normalize_uint8_vision_item`(uint8→[-1,1])——未提交工作区版本遗漏;
- cache 注入保持 fp32(只搬 device),不向 bf16 提前取整(`omni_mot_model.py` cache bypass 分支)。
