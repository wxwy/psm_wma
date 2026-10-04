# V3 Phase 1A cache-first exact-window catalog — GPT source review

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE1A-CACHE-CATALOG`
- formal root：`7c214251f3535116e7b19f964ee907e8653fd388`
- formal child/Gitlink：`e98f293f396df74bb7030d525c40faa21e7d226d`
- design authority：`docs/build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md`
- Phase0 mapping authority：`861849491488258214e96e778cff7d1bd0309089 / c00a014444083c7c554fff7626f48cceaf5c5c31`

## Verdict

`APPROVE_TO_RUN_PHASE1A_CPU_STATIC_EVIDENCE_ONLY`

这是 source-review / execution authorization，不是 Gate closure。
只有 ds 对上述 exact implementation pair 的独立 CPU/static Evidence 全绿后，GPT 才会给 `APPROVE_PHASE1A_CACHE_CATALOG_ONLY` 或新的 `REQUEST_CHANGES`。

## Source review

formal child 只新增：

- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache.py`
- `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py`

formal root 只更新 SESSION/TODO/Gitlink。没有 OmniMoTModel、trainer、inference、server、eval、DCP 或 launcher 改动。

### PASS findings

1. **cache membership authority 正确**：catalog 只从 `dataset_manifest.json` 建立 accepted corpus；不扫描 raw RoboCasa dataset 决定 membership。
2. **initial exact_window_v1 contract 正确**：固定 schema/source/H_pred16/sample_stride1/20Hz/left_wrist，latent shape 必须 `[5,48,H,W]`；完整 `vae_encode_contract` 被保留，exact durations 只要求含17，不错误猜成单值列表。
3. **portable episode locator 正确**：实际 load path 由 `task_slug + episode_index` 推导，不信任 manifest 的 machine-specific absolute `episode_path`。
4. **strict missing/extra 正确**：manifest-declared missing 必停；`tasks/*/episodes/episode_*.pt` 中未声明 task/episode 在 strict mode 被视为 extra 并停。
5. **corpus digest 边界正确**：`manifest_sha256` 记录原始 manifest；semantic `corpus_digest` 排除 machine-specific root/path，绑定核心 contract + sorted episode/window identity。
6. **统计满足 Phase1A 需要**：task/episode/window/effective-consumer/source-frame、declared/discovered/accepted/rejected/extra 等可 machine-read；明确 completeness 只针对 declared cache corpus。
7. **lazy reader 正确**：第一次读取 episode 才 `torch.load(weights_only=True)`；要求 exact start key，不做 nearest/floor fallback；latent 必须 finite fp32 exact shape；17-frame indexes 和5 anchor indexes精确校验。
8. **无错误视觉语义回归**：模块不依赖 raw dataset、Wan/VAE/tokenizer，也不计算 B1 endpoint 或 visual96；本阶段只负责 cache identity/latent retrieval。
9. **GPT early findings 已闭合**：
   - public `episodes` 已返回排序后的 `ExactWindowEpisodeRecord`；
   - audit 已扫描未声明 task slug；
   - malformed `compute_dtype/encode_chunk_frames` 有 fail-closed tests；
   - `source_video_frames/window_count` 不一致有 fail-closed tests。
10. cx 最终自测报告：57 passed；Ruff check/format PASS。该结果仅作作者自测，不替代 ds Evidence。

## Remaining boundary

本 Gate 尚未证明：

- 训练服务器实际 cache manifest 与此 initial contract 一致；
- source dataset action/state/text binding；
- ActionSFT pipeline 对 video_latent 的保键；
- OmniMoTModel cache-hit；
- Local visual96、B_stream batched TTT；
- GPU、训练、DCP、inference、simulation 或 SR。

这些都不是 Phase1A closure 条件，不得借本 review 提前推进。

## Authorized ds Evidence

ds 只执行 exact-pair CPU/static；禁止修改代码/正式测试/Gitlink。任一失败即保留输出并返回，不自行修复、不自动扩大范围。
