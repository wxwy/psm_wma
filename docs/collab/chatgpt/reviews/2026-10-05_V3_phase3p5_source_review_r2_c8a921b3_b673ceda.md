# V3 Phase3.5 real cache vs online Wan VAE parity — GPT fresh source review r2

- 日期：2026-10-05
- Gate：`V3-REAL-CACHE-ONLINE-VAE-PARITY`
- formal root：`c8a921b38128ed7430577693e76c8f38d856599a`
- formal child/Gitlink：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- parent formal pair：`5b0ebdd8394227e3d3f7966ce5bb99aecbfd3327 / 6feb9a13ba85b612f738bbb7c305e001722328ca`
- design authority：`docs/build/PSM-WMA_V3_phase3p5_real_cache_online_vae_parity_design_v1.1_2026-10-05.md`

## Verdict

`APPROVE_TO_RUN_PHASE3P5_REAL_DRY_RUN_ONLY`

这是 source-review + **真实资产 dry-run-only** 授权。

它不是：
- real Wan VAE observational encode 授权；
- parity PASS；
- thresholded Gate 授权；
- Phase4 Local-TTT 授权。

## Fresh blocker closure

上一 pair 唯一 HIGH blocker已闭合：

- `prepare_tokenizer_device(tokenizer, device)` 先拒绝 streaming/cached encoder；
- 将 `tokenizer.model.model` 移到 requested device；
- 将 `tokenizer.model.scale=(mean,inv_std)` 两个 tensor 同步移到 requested device；
- 再 `eval()`；
- synthetic spy test以 `cuda:1` 目标证明 model + 两个 scale 均收到同一 requested device，且不需要真实 CUDA。

因此不再存在“inner model在cuda:N而scale仍留默认device”的已知真实GPU blocker。

## Source review closure

formal child相对 parent child只修改两份 Phase3.5 parity文件：
1. `tools/v3/verify_robocasa_exact_window_real_parity.py`
2. `tools/v3/verify_robocasa_exact_window_real_parity_test.py`

其余 parity source contract保持通过：

- exact cache/source identity before video/VAE；
- entire-episode rows/timestamps；
- each camera decode exactly once per selected episode；
- current official left|wrist pixel composite；
- current official float-video→uint8；
- entire-episode VideoResize then exact 17-frame slicing；
- current normal full Wan encode，no streaming/no cached encoder；
- resolved manifest VAE contract，runtime只覆盖 local VAE asset locator；
- padded pre-crop full5 + temporal0..4；
- official native post-crop；
- z0；
- observational no-threshold不自判PASS；
- threshold mode在encode前要求>=3 task classes / >=9 windows；
- only `--output-json` write path；no cache/source mutation/no fallback。

## Author self-test evidence

cx synthetic/offline:
- Phase3.5 + relevant Phase1A/1B/2/3 suite：`186 passed in 105.71s`
- Ruff check PASS
- Ruff format --check PASS
- py_compile PASS
- diff-check PASS
- formal scope still only two parity files

作者自测不是 real parity Evidence，但足够授权 dry-run。

## Authorized ds dry-run

必须在**持有 matching real assets 的执行环境**运行：
- exact-window cache root
- matching flat LeRobot v3 source root
- local Wan VAE file

资产路径必须由执行环境/Owner显式提供。禁止：
- 从历史 manifest absolute path猜当前路径；
- 全盘搜索机器；
- 下载；
- 复制/重建 cache；
- 修改 source/cache/VAE。

若任一资产路径未显式提供或本地不存在：
`BLOCKED_ASSET_PATH`
并停止，不运行 probe。

### exact-pair lock

- root object：`c8a921b38128ed7430577693e76c8f38d856599a`
- root gitlink必须：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- child HEAD/origin child必须同一 SHA
- child Phase3.5 scope相对 Phase3 parent必须仅两 parity files

### command

From child repo:

```bash
PYTHONPATH=. HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python tools/v3/verify_robocasa_exact_window_real_parity.py \
  --cache-root "$CACHE_ROOT" \
  --source-root "$SOURCE_ROOT" \
  --vae-path "$WAN_VAE_PATH" \
  --output-json "$PARITY_OUT" \
  --dry-run
```

本轮不要传：
- `--max-abs-threshold`
- `--hash-vae`
- `--device cuda:...`
- `--video-backend`

dry-run不加载Wan，不需要GPU；但会检查VAE file存在性、cache/source identity、video paths、resolved contract与static geometry。

### Evidence

使用fresh目录，保存：
- root/child fetch与exact SHA
- gitlink/scope
- three asset paths存在性与类型
- command stdout/stderr/rc
- output JSON
- repo status before/after

PASS iff：
- rc=0
- JSON status=`DRY_RUN_PASS`
- parity_gate_pass=null
- identity/witness/video paths/VAE contract/geometry全部成功
- repo/assets无修改

## Current environment note

GPT当前只看到一台在线 Desktop Commander设备：编码服务器 `bitahub-a21313865965105152189478`。
如果 matching real cache/source/Wan VAE 不在该服务器且未显式挂载，本 Gate应记录 `BLOCKED_ASSET_PATH`，不是FAIL，也不得用编码服务器synthetic fixture冒充real dry-run。

dry-run PASS 后仍不得 observational encode；JSON必须先回 GPT/Owner审核，再单独授权真实 Wan observational run。