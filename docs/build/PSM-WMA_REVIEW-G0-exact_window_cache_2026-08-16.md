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
| 4 | cached-latent 真实 forward 3 步(task0 train,混合命中/回退) | PASS:3/3 finite,无 OOM,GPU 峰值 34.2GiB,RSS 10.6GB;iter1 loss 与纯在线 Probe 1 逐位一致(15.59546947479248)。**措辞更正(DS MEDIUM-2)**:该 batch 为混合命中,collator 对非全样本共有 key 直接 drop(`collators.py:85-110`),iter1 逐位一致实为"全批在线回退"的重现,不能表述为 cache 命中路径已逐位实测;cache 命中端到端验证见阶梯 4b。iter2/3 相对漂移 ~3e-5(bf16 非确定性量级,LOW 观察项) |
| 4b | cache 命中路径端到端 forward(tiny_overfit_num_samples=16,iterable_shuffle=false,全批命中 episode 0 前 16 窗口) | **PASS**:3/3 finite(loss 14.09→13.17→12.67),GPU 峰值 34.2GiB,RSS 7.6GB;离线复核固定子集 16/16 全命中、latent [5,48,16,32] fp32;步耗时 ~50s(在线回退 ~120s),与跳过在线 VAE 编码一致。产物 `forward_smoke_cachehit/`(step_metrics.jsonl、retry 日志、iter_0000003 checkpoint) |
| 5 | multi-worker loader smoke(num_workers=2,8 batch) | PASS:32/32 命中,shape [B,5,48,16,32],RSS 1.5GB |
| 6 | 多 episode cache(ep0/18/22)+ 跨 episode loader + ep18 parity | PASS:604 样本跨边界全命中,边界 identity (0,197)→(18,0) 正确;ep18 parity diff=0.0 |

产物:`/gemini/code/data/libero/exact_window_v1_smoke{,3}/`、`artifacts/g0/r06/exact_window_v1/`(parity JSON×2、forward smoke 日志/metrics)。

## 4. 磁盘与成本(LIBERO-4in1 实测元数据)

1693 episodes / 276,475 帧 / 246,377 窗口(stride=1);fp32 裸量 112.78 GiB(stride2 56.39 / stride4 28.20 GiB)。构建速率实测 ~1.15 min/episode(含窗口编码 ~0.5s/窗),4in1 全量约 32 小时 GPU;libero_10 task0-only(37 训练 episode,8982 窗口)约 45 分钟 / 4.3GB。

## 4.5 DS/Codex 第二审查跟进(2026-08-16 晚)

DS 第二独立审查结论 APPROVE,附四条意见,处置如下:

1. **MEDIUM-1 舍入不一致(已修复+重验)**:builder `build_cosmos_libero_latent_dataset.py:91` 与 parity 参照 `generate_r06_latent_cache_parity.py:65` 原用 `torch.round(video*255)`,与在线路径 `base_dataset.py:214` 的截断 `(video*255.0).clamp(0,255).to(uint8)` 不一致。已统一为截断(legacy R12 `_encode_episode` 路径保留 round 不动)。修复后重建 smoke cache(3 episode/705 窗口)并重跑 parity:ep0 与 ep18 均 **diff=0.0**,覆盖 start%4=0/1/2/3(`smoke_parity.json`、`smoke3_parity_ep18.json`)。Codex 复审 APPROVE。
2. **MEDIUM-2 阶梯4 表述(已更正+补实测)**:阶梯4 行措辞已更正(见上);补阶梯 4b 全批 cache 命中端到端 forward,**PASS**(结果见阶梯表 4b 行)。另记录:torchrun 经脚本路径直启会被 `cosmos_framework/scripts/hydra.py` 遮蔽 hydra 包,必须用 `python -m torch.distributed.run -m cosmos_framework.scripts.train` 形式启动(train.py docstring 即为此口径)。
3. **LOW-1(已修)**:`cosmos-framework/docs_zh/psm_wma/REGULAR_EPISODE_LATENT_OVERFIT.md` 头部加 SUPERSEDED BY D013 横幅。
4. **LOW-2(已修)**:`action_sft_dataset.py` `ActionLatentCacheDataset.__getitem__` 在 sample 已含 `vision_latent_cache`(内层 `libero_lerobot_dataset.py:305-328` 已命中)时跳过重复查询。

## 5. 未执行项

- 阶梯7 LIBERO-4in1 全量编码:待用户决策(范围×stride×dtype 的成本组合)。
- iter2/3 漂移根因未单独定位(非确定性观察项,不阻塞)。

## 6. 剩余风险

- 全量构建时长 32h(stride1/4in1),需排队 GPU 窗口;
- 部分覆盖依赖回退路径(已验证),但正式训练建议全覆盖以避免混合分布;
- iter2/3 的 3e-5 漂移如后续要求严格可复现,需开 deterministic 模式复核。
