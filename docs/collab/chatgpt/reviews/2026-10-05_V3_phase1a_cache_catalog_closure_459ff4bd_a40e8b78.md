# V3 Phase 1A cache-first exact-window catalog — GPT closure review

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE1A-CACHE-CATALOG`
- formal root：`459ff4bd30959cba916813c30c85faf51fad1db0`
- formal child/Gitlink：`a40e8b782e0692e0a24e2f60893e9f4f8d858961`
- authorization review：`docs/collab/chatgpt/reviews/2026-10-05_V3_phase1a_cache_catalog_source_review_459ff4bd_a40e8b78.md`
- superseded blocker review：`docs/collab/chatgpt/reviews/2026-10-05_V3_phase1a_cache_catalog_source_review_r2_7c214251_e98f293f.md`

## Verdict

`APPROVE_PHASE1A_CACHE_CATALOG_ONLY`

Phase 1A 关闭。该 verdict 只确认 cache-first exact_window_v1 catalog/lazy reader 与其 CPU/static contract；不批准 Phase1B 以后功能、真实 cache、GPU、训练、仿真或 SR。

## Source closure

- cache membership 由 `dataset_manifest.json` 决定，不由 raw RoboCasa 枚举决定；
- manifest-declared missing fail-closed；
- recognized `tasks/*/episodes/*.pt` namespace 的 undeclared/malformed payload 全部纳入 audit；
- strict mode 对 extra fail-closed，non-strict audit 显式计数；
- portable episode path 由 task_slug + episode_index 推导，不信任 absolute provenance path；
- manifest SHA 与 machine-root-independent semantic corpus digest 分离；
- exact_window_v1 要求 H_pred16 / 17-frame / [5,48,H,W]，完整 VAE contract 保留且 exact durations 含17；
- lazy episode read 使用 exact start key，无 nearest/floor fallback；
- latent 必须 finite fp32 exact shape，frame/anchor indexes 精确；
- 模块不依赖 raw dataset、VAE/tokenizer、B1 endpoint 或 visual96。

## ds independent Evidence — rerun1

Evidence 目录：`/tmp/psm_wma_v3_phase1a_ds_evidence_rerun1/`。

A. exact-pair/remote lock：
- root `git fetch origin V3` PASS；
- root advertised SHA == `origin/V3` PASS；
- child fetch / advertised SHA == `origin/v3-local-ttt` PASS；
- formal root gitlink == child `a40e8b...` PASS；
- child HEAD == formal child PASS；
- child formal scope == exact 2 Phase1A files PASS。

B. target pytest：
- `60 passed in 26.65s`
- 0 failed / 0 skipped / 0 error。

C. static：
- Ruff check PASS；
- Ruff format --check PASS；
- formal child diff --check PASS；
- scope PASS。

第一次 ds run 因 root fetch TLS 失败后错误继续执行，已明确降级为 diagnostic 并未计入 closure；本 verdict 仅使用 rerun1 的全新、严格 fail-fast Evidence。

## Explicit remaining boundary

Phase1A 未证明：
- 训练服务器真实 cache manifest/schema；
- cache episode 到 raw source shard/episode/action/state/text 的 binding；
- ActionSFT pipeline 的 video_latent 保键；
- OmniMoTModel cache-hit；
- visual96 / Local producer；
- B_stream batched TTT；
- checkpoint/resume 新 geometry；
- inference/server/eval；
- GPU、训练、仿真、行为效果。

下一阶段只允许 Phase 1B source binding，经独立 design/implementation Gate 推进。