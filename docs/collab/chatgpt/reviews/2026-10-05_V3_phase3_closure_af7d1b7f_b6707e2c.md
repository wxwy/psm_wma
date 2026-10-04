# V3 Phase 3 cached-latent SFT + OmniMoT cache-hit — GPT closure review

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE3-CACHED-SFT-CACHE-HIT
- formal root：af7d1b7fb3b85a79df8d7f8edc00e6f24bde5874
- formal child/Gitlink：b6707e2c89fe6078e2a0bb4ff7266205b827825e
- parent Phase2 child：ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0
- design authority：docs/build/PSM-WMA_V3_phase3_cached_latent_sft_model_cache_hit_design_v1.0_2026-10-05.md
- execution authorization：docs/collab/chatgpt/reviews/2026-10-05_V3_phase3_source_review_af7d1b7f_b6707e2c.md
- ds Evidence：/tmp/psm_wma_v3_phase3_ds_evidence_r1/

## Verdict

APPROVE_PHASE3_CACHED_SFT_CACHE_HIT_ONLY

Phase3 正式关闭。

该 verdict 只确认 synthetic/local CPU/static 下：
- cache-first ActionSFT sample；
- exact video_latent transport ABI；
- model-side cached vision fail-closed seam；
- cache-hit VAE encode count = 0；
- native non-cached path保持；
- native post-VAE crop/temporal/action/noise/loss downstream保持。

不批准 Local-TTT、真实资产 parity、GPU、训练、推理、仿真或 SR。

## Independent Evidence

Exact pair / scope:
- formal root object存在；
- formal gitlink = b6707e2c89fe6078e2a0bb4ff7266205b827825e；
- child HEAD / origin child = same；
- Phase2 child ce07cb6f... 到 formal child scope精确四文件：
  1. robocasa_exact_window_cached_sft.py
  2. robocasa_exact_window_cached_sft_test.py
  3. omni_mot_cached_vision_test.py
  4. omni_mot_model.py

ds target pytest:
- 191 passed, 20 warnings in 102.93s
- 0 failed / error
- warnings均为 parent transforms_test.py 既有未注册 pytest mark，不隐藏 failure。

Static:
- 3 new files Ruff check PASS；
- 3 new files Ruff format --check PASS；
- omni_mot_model.py Ruff check --ignore I001 PASS；
- 4 changed files py_compile PASS；
- formal diff --check PASS；
- repeated scope identical。

Evidence-bound SHA256:
- cached_sft.py: e87dedab8fa7dc5f97007df4eb3430856e04a64d8c5c5702310067eecf84812b
- cached_sft_test.py: 863b2943db09e05f3ce90244457503a693645bb29a90cd3069cfc4736a2e0022
- omni_mot_cached_vision_test.py: 43dffc61d3ff350e0aa9963d69054ba7b0a30a254f0b71f6638eb25c14f96594
- omni_mot_model.py: e55909388d7e06235929b86ae6be764785cd5efd5a03912c4ae14e6897ec8a01

ds未修改仓库、Gitlink、正式测试或代码；Evidence仅落 /tmp。

## Frozen Phase3 result

1. training corpus membership仍由 Phase1A cache manifest定义。
2. Phase1B source binding + Phase2 raw15/state15通过同一 exact window identity接入。
3. raw dataset只提供 zero uint8 composite placeholder [3,17,256,512] 作为 transform geometry carrier；真实视觉 target唯一来自 exact cache video_latent。
4. ActionTransformPipeline / generic collator / PackingDataLoader均未修改。
5. final model cached ABI冻结为 list[B]，每项 Tensor[1,5,48,H,W]。
6. model cache-hit只接受 training / single composite item / fp32 finite exact latent / image_size一致的 frozen ABI。
7. cached_latent_required marker与 video_latent分别传输；marker存在而 latent key缺失时直接 fail，禁止 online VAE fallback。
8. cache-hit完全绕过 online vision VAE encode，包括 balance_vae_encode path。
9. cached latent进入 model后仍走 native _remove_padding_from_latent、temporal positions、vision FM/noise/loss downstream。
10. native noncached/off-mode path不变。
11. exact window Z=[z0..z4] 是后续 Local-TTT 的唯一训练视觉 authority；Phase4 Local只允许从同一个 Z 的 z0派生 visual96。
12. B1 dual-camera/separate-VAE/mean-RMS visual96 route仍是历史，不得进入 corrected active path。

## Explicit remaining boundary

Phase3仍未证明：
- 真实训练服务器 cache 与同一 source/composite/resize/Wan VAE online encode 数值 parity；
- Local visual96 = V2 adaptive_avg_pool2d((1,2)).flatten；
- B_stream batched TTT / configurable T；
- corrected Local inner/outer gradient path；
- checkpoint/resume；
- inference/server/eval；
- GPU训练/仿真/SR。

## Mandatory next Gate before Phase4

先执行独立的 REAL-CACHE-VS-ONLINE-VAE-PARITY Gate：

同一真实 exact cache window：
source left+wrist pixels
-> same pixel composite
-> same VideoResize
-> same resolved Wan VAE
vs
stored exact cache latent

必须比较：
- padded pre-crop full [5,48,H,W]
- native post-crop latent
- current z0
- full z0..z4 sequence

该 Gate只读，不得修改/重编码 cache，不得fallback。

由于历史 root parity工具仍依赖已移除的 vision_vae seam，先由 cx按 current latest child实现一个 read-only parity probe；经 GPT source review后，再由 ds在持有真实 cache/source/Wan VAE资产的服务器执行。

Phase4 Local-TTT integration必须等该 real parity Gate PASS后再开始。