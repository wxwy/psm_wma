# V3 Phase3.5 real cache vs online Wan VAE parity — GPT fresh source review

- 日期：2026-10-05
- Gate：`V3-REAL-CACHE-ONLINE-VAE-PARITY`
- formal root：`5b0ebdd8394227e3d3f7966ce5bb99aecbfd3327`
- formal child/Gitlink：`6feb9a13ba85b612f738bbb7c305e001722328ca`
- parent Phase3 child：`b6707e2c89fe6078e2a0bb4ff7266205b827825e`
- design authority：`docs/build/PSM-WMA_V3_phase3p5_real_cache_online_vae_parity_design_v1.1_2026-10-05.md`

## Verdict

`REQUEST_CHANGES`

不得授权 ds dry-run/observational。当前 parity 逻辑大部分通过 source review，但真实 Wan multi-device 初始化存在一个 HIGH blocker；synthetic fake tokenizer 没覆盖到。

## PASS findings

1. formal child scope 精确两份新 tool/test，无 production core 修改。
2. exact identity：Phase1A/1B/2 catalog/source/contract 在视频/VAE前构造，selected window使用 exact key/start/global rows，无 nearest/floor。
3. v1.1 chronology 正确：每 episode先完整 rows/timestamps，left/wrist各整 episode decode一次，official compose一次、official float->uint8一次、VideoResize整 episode一次，最后切每个17-frame window独立 full encode。
4. decode timestamps 正确使用 `from_timestamp + episode timestamp`；current `decode_video_frames(path,timestamps,tolerance_s,backend)` API 匹配。
5. active pixel path无 separate-camera VAE/B1/old vision_vae。
6. VAE config从 Phase2 frozen manifest authority resolve，只覆盖 local `bucket_name/vae_path`；streaming/cached encoder均拒绝。
7. pre-crop full5、temporal0..4、official post-crop、z0 metrics均存在；post-crop直接调用 `OmniMoTModel._remove_padding_from_latent`。
8. thresholded run在 encode前强制 >=3 task classes / >=9 exact windows；observational无threshold只报告，不自判PASS。
9. dry-run不构造 tokenizer、不encode；仍检查 exact identities、video files、resolved contract与static geometry。
10. probe唯一文件写操作是 `--output-json`；无 cache/source/latent写入。
11. cx self-test记录：relevant synthetic suite `185 passed`；Ruff/format/py_compile/diff-check PASS；尚无 ds Evidence。

## HIGH blocker — Wan scale tensors 未跟随 requested device

- file:line：child `tools/v3/verify_robocasa_exact_window_real_parity.py:440-443`
- current：
  - `tokenizer = Wan2pt2VAEInterface(...)`
  - 仅执行 `tokenizer.model.model.to(device).eval()`
  - 没有移动 `tokenizer.model.scale=(mean, 1/std)`
- current Wan implementation事实：
  - `WanVAE.__init__` 将 `scale` tensor 创建在 constructor 的默认 `DEVICE`；
  - `WanVAE.encode()` 调 `self.model.encode(videos, self.scale)`；
  - `WanVAE` 本身不是 nn.Module，因此只对 inner `model.to(device)` 不会自动移动 `scale`。
- repository precedent：
  `tools/v3/build_robocasa_b1_h5_cache.py:329-331` 在 model.to(device) 后显式：
  `scale_mean, scale_inv_std = vae.model.scale`
  `vae.model.scale = (scale_mean.to(device), scale_inv_std.to(device))`
- impact：
  当 `--device cuda:1` 等不是 Wan constructor 默认 device 时，真实 encode可能出现 input/model/scale device mismatch；fake CPU tokenizer测试无法发现。
- acceptance：
  1. parity probe在 tokenizer构造后，将 inner model和 `model.scale` 两个 tensor都迁到 requested device，再 eval；
  2. 不导入/调用旧 B1 parity/cache逻辑；只复用当前 Wan object contract；
  3. 增 synthetic定向 test，用 fake tokenizer whose scale tensors起始在不同可判别 device/状态（CPU环境可用 meta/spy或封装可观测 `.to(device)`），证明 requested-device preparation 同时处理 model与scale；
  4. test同时证明 no streaming/cached encoder仍保持；
  5. 重新跑 Phase3.5 + relevant Phase1A/1B/2/3 synthetic tests、Ruff/format/py_compile/diff-check；
  6. fresh child/root exact pair后再审。

## Boundary

本 review 不否定 design v1.1，也不授权真实资产、VAE/GPU、训练、仿真或 Phase4。
ds保持暂停；cx只修上述 device-preparation blocker及正式测试。