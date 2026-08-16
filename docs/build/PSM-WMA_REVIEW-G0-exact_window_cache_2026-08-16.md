# REVIEW G0 exact-window latent cache — 审查与阶梯验证记录

- 日期:2026-08-16
- 审查者/执行者:Kimi(第一技术审查者)
- 规范:`docs/build/PSM-WMA_RGB_representation_and_memory_encoding_plan_v0.1.md` + `MEMORY/DECISIONS.md` D013
- 代码:根仓 `tools/g0/build_cosmos_libero_latent_dataset.py`、`tools/g0/generate_r06_latent_cache_parity.py`;子模块 `cosmos_framework/data/generator/action/latent_cache.py`、`cosmos_framework/model/generator/omni_mot_model.py`(仅 cache 注入 dtype)

## 1. 审查结论:APPROVE_WITH_CHANGES(变更已落实并验证)

| 项 | 结论 | 证据 |
|---|---|---|
| 原生 temporal contract | 17 帧窗口 / chunk16 / stride=1 / concat_view [3,17,256,512] / VAE→[1,48,5,16,32] | `libero_lerobot_dataset.py:185,199,359-362`;`wan2pt2_vae_4x16x16.py:873-887` |
| exact-window 保持原生分布 | 成立(构造上=在线编码提前计算;实测逐位一致) | parity diff=0.0 |
| stride=1 是原生分布 | 成立;LIBERO 路径 `sample_stride` 参数无效 | 同上 + Probe 1 valid_indices=8982 |
| G0-R12 cache | 整段因果编码,与在线窗口路径不等价(diff 4.625),supersede;机制层可复用 | `artifacts/g0/r06/sft_baseline/parity/r06_latent_parity.json` |
| cache 后 forward 保留 noising/loss | 成立,noising 在 x0 注入之后 | `omni_mot_model.py:1815-1933` + 阶梯4 实测 |
| 不做 dedup | 已遵守,逐窗口独立编码存储 | builder `exact_window_v1` |

## 2. 审查驱动的修复(全部经阶梯验证)

1. builder `_encode_window` 补 `_normalize_uint8_vision_item`(uint8→[-1,1]);缺失时 parity 必 FAIL。
2. cache 注入保持 fp32 只搬 device(在线 x0 为 fp32,原 `.to(**tensor_kwargs)` 会提前取整 bf16)。
3. parity 工具对照端改独立在线实现(消除 builder 自参照)。
4. `R12CosmosLatentCache.get_window` 缺 episode 文件回退在线(原 FileNotFoundError 硬崩,阶梯4 首跑实测暴露)。
5. schema_version 修正为 `exact_window_v1`。

## 3. 阶梯验证结果

| 阶梯 | 内容 | 结果 |
|---|---|---|
| 1 | one-sample online/offline parity(独立参照,5 窗口覆盖 start%4 全类) | **PASS diff=0.0 逐位** |
| 2 | one-episode cache(episode 0,198 窗口,97.5MB fp32) | PASS |
| 3 | index/alignment(198/198 窗口键、source_frame_indices、global_row_indices、instruction、metadata) | PASS |
| 4 | cached-latent 真实 forward 3 步(task0 train,混合命中/回退) | PASS:3/3 finite,无 OOM,GPU 峰值 34.2GiB,RSS 10.6GB;iter1 loss 与纯在线 Probe 1 逐位一致(15.59546947479248);iter2/3 相对漂移 ~3e-5(bf16 非确定性量级,LOW 观察项) |
| 5 | multi-worker loader smoke(num_workers=2,8 batch) | PASS:32/32 命中,shape [B,5,48,16,32],RSS 1.5GB |
| 6 | 多 episode cache(ep0/18/22)+ 跨 episode loader + ep18 parity | PASS:604 样本跨边界全命中,边界 identity (0,197)→(18,0) 正确;ep18 parity diff=0.0 |

产物:`/gemini/code/data/libero/exact_window_v1_smoke{,3}/`、`artifacts/g0/r06/exact_window_v1/`(parity JSON×2、forward smoke 日志/metrics)。

## 4. 磁盘与成本(LIBERO-4in1 实测元数据)

1693 episodes / 276,475 帧 / 246,377 窗口(stride=1);fp32 裸量 112.78 GiB(stride2 56.39 / stride4 28.20 GiB)。构建速率实测 ~1.15 min/episode(含窗口编码 ~0.5s/窗),4in1 全量约 32 小时 GPU;libero_10 task0-only(37 训练 episode,8982 窗口)约 45 分钟 / 4.3GB。

## 5. 未执行项

- 阶梯7 LIBERO-4in1 全量编码:待用户决策(范围×stride×dtype 的成本组合)。
- iter2/3 漂移根因未单独定位(非确定性观察项,不阻塞)。

## 6. 剩余风险

- 全量构建时长 32h(stride1/4in1),需排队 GPU 窗口;
- 部分覆盖依赖回退路径(已验证),但正式训练建议全覆盖以避免混合分布;
- iter2/3 的 3e-5 漂移如后续要求严格可复现,需开 deterministic 模式复核。
