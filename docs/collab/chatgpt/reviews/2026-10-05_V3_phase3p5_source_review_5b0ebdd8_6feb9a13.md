# V3 Phase 3.5 real cache vs online Wan VAE parity probe — GPT fresh source review

- 日期：2026-10-05
- Gate：V3-REAL-CACHE-ONLINE-VAE-PARITY
- formal root：5b0ebdd8394227e3d3f7966ce5bb99aecbfd3327
- formal child/Gitlink：6feb9a13ba85b612f738bbb7c305e001722328ca
- parent Phase3 child：b6707e2c89fe6078e2a0bb4ff7266205b827825e
- design authority：docs/build/PSM-WMA_V3_phase3p5_real_cache_online_vae_parity_design_v1.1_2026-10-05.md
- design root：62cefe03d393005667192538c030e7fdcf4c35bc

## Verdict

APPROVE_TO_RUN_PHASE3P5_REAL_DRY_RUN_ONLY

这是 source-review + **真实资产 dry-run-only** 授权。

它不是：
- VAE parity PASS；
- observational real VAE encode授权；
- threshold授权；
- Phase4 Local-TTT授权。

ds 只允许在能访问 matching real cache/source/VAE file 的执行环境上做 dry-run；如果资产路径不可用，必须返回 BLOCKED，禁止猜路径、下载、复制或修改资产。

## Formal scope

formal child 相对 Phase3 parent仅新增：
1. tools/v3/verify_robocasa_exact_window_real_parity.py
2. tools/v3/verify_robocasa_exact_window_real_parity_test.py

无 dataset/model/tokenizer/trainer/inference/simulator production修改。

formal root仅：
- Gitlink -> 6feb9a13...
- TODO/SESSION handoff

untracked docs/build/.__dpc... 不属于 formal tree，任何后续提交也不得纳入。

## Source review findings

### 1. Builder-fidelity pixel route — PASS

probe对每个 selected episode：
- 精确读取 Phase1B bound source rows/timestamps；
- cache global-row witness exact check；
- left camera整 episode decode一次；
- wrist camera整 episode decode一次；
- current official RoboCasaLeRobotDataset._compose_left_wrist；
- current official/inherited _convert_video；
- VideoResize entire episode一次；
- resize后才切 selected 17-frame windows。

该组织顺序与历史 exact cache builder一致，避免 per-window video seek/backend差异混入 VAE parity。

历史 compose_robocasa_video 已从 current child移除，但已审其旧实现：
- native 256x256 left_wrist 分支就是 left|wrist pixel concat；
- 与 current _compose_left_wrist 在本 Gate强制 native256 input 下逐值等价。

### 2. Historical/current single-view encode semantic — PASS

历史 cache helper的 single-view encode：
uint8 -> fp32 -> /127.5 - 1 -> tokenizer.encode -> contiguous.float

current active helper：
normalize_uint8_item -> tokenizer.encode -> contiguous.float

数学/布局一致。

新 probe禁止：
- old vision_vae import；
- B1 evidence/cache；
- streaming encode；
- separate-camera VAE。

### 3. Wan runtime contract — PASS

- CorrectedRoboCasaPolicyContract.from_cache_catalog
- full manifest encode_exact_durations保留
- manifest-compatible encode_chunk_frames
- runtime只覆盖 bucket_name="" 与 CLI vae_path
- VAE path在 tokenizer构造前必须是 local file
- use_streaming_encode=False
- no cached encoder
- cudnn.benchmark=False
- tokenizer.model.model.to(device).eval()
- torch.inference_mode()

与原 cache builder关键 runtime设置一致。

### 4. Compare layers — PASS

每 window：
- pre-crop full padded latent；
- 5 temporal latent frame metrics；
- native OmniMoTModel._remove_padding_from_latent post-crop；
- post-crop z0。

工具不复制 native crop公式。

### 5. Gate semantics — PASS

- dry-run => DRY_RUN_PASS, parity_gate_pass=null
- no threshold real encode => OBSERVATIONAL_NO_THRESHOLD, parity_gate_pass=null
- threshold模式在任何 encode前强制 >=3 task classes / >=9 windows
- threshold只由外部参数给定，tool不自动拟合
- threshold breach => FAIL/nonzero

因此单 episode observational不能伪装 final PASS。

### 6. Read-only contract — PASS

正式 probe唯一 write path是 --output-json。
source中无 torch.save/cache write/manifest rewrite/debug tensor dump。

### 7. Test coverage — PASS for source authorization

cx synthetic/offline作者自测：
- combined Phase1A/1B/2/3 + Phase3.5：185 passed
- Phase3.5 new tests：19 passed
- Ruff check/format：PASS
- py_compile：PASS
- formal diff-check：PASS
- exact scope：2 files

正式 tests实际覆盖：
- first/mid/terminal selection
- final 3-task/9-window validator
- whole-episode row/timestamp
- exact witness
- video path
- per-episode/per-camera decode count
- official compose/convert
- real VideoResize geometry
- current normalize
- fake tokenizer encode count
- pre/post/z0 metrics
- shape/dtype/nonfinite
- missing VAE path before tokenizer
- run-level successful dry-run
- run-level fake observational encode
- no legacy/B1 import/write path

作者自测不等于 real parity Evidence，但足够授权 dry-run。

## Authorized ds dry-run

前提：执行环境必须已有、且只读可访问：
- exact cache root
- matching flat LeRobot v3 source root
- Wan VAE file

不要从历史 manifest absolute path猜 runtime path。

建议环境变量由 Owner/执行环境显式提供：
- CACHE_ROOT
- SOURCE_ROOT
- WAN_VAE_PATH
- PARITY_OUT

若任一为空或本地不存在：
- 返回 BLOCKED_ASSET_PATH
- 不执行后续；
- 不搜索整个机器；
- 不下载。

Exact pair lock:
- root object 5b0ebdd8394227e3d3f7966ce5bb99aecbfd3327
- gitlink 6feb9a13ba85b612f738bbb7c305e001722328ca
- child HEAD/origin child必须相同
- child formal scope必须精确两 parity files

Dry-run command from child root：

PYTHONPATH=. HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
/disk/rl/worktrees/cosmos-framework-v3/.venv/bin/python \
tools/v3/verify_robocasa_exact_window_real_parity.py \
  --cache-root "$CACHE_ROOT" \
  --source-root "$SOURCE_ROOT" \
  --vae-path "$WAN_VAE_PATH" \
  --output-json "$PARITY_OUT" \
  --dry-run

本次不要传：
- --max-abs-threshold
- --hash-vae
- --device cuda（dry-run不需要）
- --video-backend（保持 builder/current default语义）

Evidence必须保存：
- exact pair/gitlink/scope
- env path existence/type（只展示路径，不改资产）
- stdout/stderr
- output JSON
- command rc
- repo status before/after

PASS iff：
- rc=0
- status=DRY_RUN_PASS
- parity_gate_pass=null
- cache/source identity/witness/selected video path/resolved VAE contract/expected geometry全部成功
- repo与资产均无修改

dry-run PASS 后仍不得执行 observational VAE encode；把 JSON回 GPT审核后再下下一道授权。