# V3 Phase 3 cached-latent SFT + OmniMoT cache-hit — GPT fresh source review

- 日期：2026-10-05
- Gate：`V3-CORRECTED-PHASE3-CACHED-SFT-CACHE-HIT`
- formal root：`af7d1b7fb3b85a79df8d7f8edc00e6f24bde5874`
- formal child/Gitlink：`b6707e2c89fe6078e2a0bb4ff7266205b827825e`
- child baseline：`ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0`
- design authority：`docs/build/PSM-WMA_V3_phase3_cached_latent_sft_model_cache_hit_design_v1.0_2026-10-05.md`
- parent Phase2 closure：`docs/collab/chatgpt/reviews/2026-10-05_V3_phase2_closure_471b7fec_ce07cb6f.md`

## Verdict

`APPROVE_TO_RUN_PHASE3_CPU_STATIC_EVIDENCE_ONLY`

这是 source-review / execution authorization，不是 Phase3 closure。
ds 只允许执行本文 exact-pair 的 CPU/static Evidence；不得修改 production code、正式测试、Gitlink。

## Fresh source findings

### 1. Scope 正确

formal child 相对 Phase2 closure child 仅四文件：

1. ADD `cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft.py`
2. ADD `robocasa_exact_window_cached_sft_test.py`
3. ADD `cosmos_framework/model/generator/omni_mot_cached_vision_test.py`
4. MODIFY `cosmos_framework/model/generator/omni_mot_model.py`

core diff 仅位于 `get_data_and_condition()` 的 cached-vision preparation 附近；未修改：
- generic collator / PackingDataLoader
- ActionTransformPipeline
- official RoboCasa loader
- tokenizer/VAE
- sequence packing / flow loss
- trainer/DCP
- inference/server/eval
- old B1/grouped Local route。

### 2. Cache-first corpus / exact identity 保持

Phase3 raw dataset 的 membership 仍来自 Phase1A catalog / Phase1B cache-driven flat index；
source extra episode不会进入。
每个 sample 同时交叉验证：
- key/start
- global-row witness
- source binding digest
- task class/caption
- exact cache latent window

错误即 fail-closed，无 nearest/floor/remap。

### 3. Active visual authority 正确

raw sample视觉只有：
- zero uint8 composite placeholder `[3,17,256,512]`，仅作为 native transform geometry carrier；
- exact cache `video_latent`，真正视觉 target。

未 import/use：
- B1 H5 / `RoboCasaLatentReader`
- dual-camera separate VAE
- B1 mean/RMS visual96
- Local online VAE。

### 4. Geometry 与 builder/native path 对齐

builder authority：
`left|wrist 256x512 -> VideoResize(resolution=None) -> padded canvas -> exact 17-frame Wan VAE`。

current geometry：
- placeholder pre-resize：256x512
- transformed target canvas：192x320
- content：160x320
- fixed Wan spatial compression factor：16
- cached padded latent：12x20
- native `_remove_padding_from_latent` 后 content latent：10x20

dataset constructor 与 model cache-hit 都按 factor16 fail-closed；early-review 中错误的 /8 synthetic geometry 已修复，正式 tests 固定 192x320 -> 12x20。

### 5. ActionSFT / packing transport ABI 正确

未修改 generic collator/packer，实际 ABI 已按 current code冻结并测试：

inner DataLoader:
- B=1: `Tensor[1,5,48,H,W]`
- B=2: `Tensor[2,5,48,H,W]`

Packing single-sample split:
- `Tensor[1,5,48,H,W]`

final model batch:
- `video_latent = list[B]`
- each item `Tensor[1,5,48,H,W]`

`video` 仍是 current single-item nested ABI：
`list[B]`，每项 length-1 list；
model `_unwrap_vision_item` 与该结构一致。

sample order / start_frame / cache digest / source digest 有双样本 formal tests。

### 6. Independent cache-required marker 可阻止 latent-key 静默丢失

raw dataset每样本固定：
`cached_latent_required=True`

marker和latent使用不同 transport key。
formal collate test实际复现：
- 一个 sample 缺 `video_latent`
- collator 因 optional key规则移除 batch-level `video_latent`
- `cached_latent_required` 仍保留为全 True

model 因 required marker存在且 latent key缺失立即 raise；
不会切回 online VAE。

active dataset/transform path始终同时产出 marker+latent；没有生产代码会 pop 这两个 key。

### 7. OmniMoT cache-hit seam fail-closed

cached path只接受 Phase3 frozen packed ABI：
- training mode only
- video stream only
- one composite vision item/sample
- no per-camera/multi-vision metadata
- no inference `vision_condition_indexes`
- marker required and every sample True
- latent exact rank5 `[1,5,48,H,W]`
- fp32 finite
- `image_size` mandatory
- spatial shape must match padded canvas / runtime tokenizer spatial factor

任一错误直接 raise。

不存在 verify mismatch -> online encode / fallback。

### 8. VAE compute 确实绕过

cached path直接把 cache item：
`[1,5,48,H,W] -> [1,48,5,H,W]`
并移到 model fp32 device/dtype。

cached path不调用：
- `_normalize_video_databatch_inplace`
- `_encode_vision_x0_tokens`
- tokenizer `encode`
- balance-VAE encode/collective

`balance_vae_encode=True` 也不会进入 VAE path。

native off-mode（无 marker、无 `video_latent`）保持旧路径；
formal test在 eval/noncached状态下仍确认 native encoder被调用。

### 9. Native post-VAE semantics 保持

cached x0 生成后仍经过 current native：
- `_remove_padding_from_latent`
- `_get_temporal_positions_vision`
- downstream vision sigma/noise/FM target/loss

placeholder raw_state只提供 T/H/W metadata；
temporal helper仅读取 shape并把整数 frame/resolution传给 tokenizer，随后 temporal positions迁到 x0 device。
placeholder不会作为视觉 target。

training CP payload继续移除 raw pixels，只保存 latent/metadata；
不会把 zero placeholder跨 rank作为训练 target传播。

### 10. dtype/layout 与 native VAE path 一致

native `_encode_vision_item` 输出显式 `.contiguous().float()`；
exact cache也是 fp32 `[T,C,H,W]`。
Phase3转成 native model layout `[1,C,T,H,W]` 后继续原 downstream。

### 11. Policy action/text/native metadata 保持

Phase3 复用：
- Phase1B exact source
- Phase2 official raw15/state15 adapter
- latest official idle-frame helper
- native ActionSFTDataset / ActionTransformPipeline

`conditioning_fps`、`domain_id`、viewpoint/additional-view description与 official RoboCasa path一致；
action仍是 state row + 16 raw15，transform后 raw_action_dim15 / pad64语义不变。

### 12. Phase2 immutable VAE authority 没有在 active factory 中回退

active factory：
- 从一个 catalog构造 Phase2 contract；
- 同一 catalog构造 source reader / cached dataset；
- catalog `vae_encode_contract` property本身返回 deepcopy；
- Phase2 resolver/validator仍读私有 immutable snapshots。

raw dataset constructor存在 public contract参数，但当前 active factory没有外部错配入口。
Phase4/5继续集成时必须保持“same catalog -> contract”或新增 immutable binding validator，不能开始信任可变 public copy。

## cx author self-test（仅参考，待 ds 独立复跑）

cx 报告：
- Phase3 targeted：29 passed
- Phase1A + 1B + 2 + 3 + ActionTransform + OmniMoT combined：191 passed，20 warnings
- 三个新增文件 Ruff check / Ruff format --check PASS
- core `omni_mot_model.py` 的 I001 / whole-file format差异为 parent baseline已存在；本轮无 import改动，changed hunk已按 formatter布局，`ruff check --ignore I001` PASS
- formal diff-check PASS

作者自测不构成 closure。

## Non-blocking historical debt / future Gate

### A. SESSION.md binary/NUL debt

root `SESSION.md` 在 Phase3 parent root就已包含2424个 NUL；
formal root仍是相同2424个，本轮只是正常追加5行。
这是历史 governance-file cleanup，非 Phase3 production blocker。

### B. Real cache-vs-online VAE parity tool目前不能直接复用旧脚本

root历史工具 `tools/g0/exact_window_cache.py` / parity scripts仍 import已从 current child删除的
`cosmos_framework.model.generator.vision_vae` helper。

因此：
- 本 Phase3 CPU/static Gate不运行旧 real-parity工具；
- Phase3 synthetic closure后、正式训练前，必须先由 cx按 latest current VAE seam适配一个 read-only parity probe；
- 再由 ds在真实资产服务器执行 cache vs online exact-window parity；
- 禁止为了让旧工具工作而恢复旧 V2 `vision_vae` production seam或重编码 cache。

## Authorized ds Evidence

工作目录：
`/disk/rl/psm_wma_v3`

fresh Evidence dir：
`/tmp/psm_wma_v3_phase3_ds_evidence_r1/`

### A. exact pair / scope lock

1. fetch root V3
2. fetch child v3-local-ttt
3. verify formal root object：
   `af7d1b7fb3b85a79df8d7f8edc00e6f24bde5874`
4. `git ls-tree <formal-root> cosmos-framework` 必须等于：
   `b6707e2c89fe6078e2a0bb4ff7266205b827825e`
5. child HEAD/origin必须等于 formal child（若需 checkout exact child，只 checkout，不编辑）
6. formal scope相对 `ce07cb6f4a3f7792d85b7583ff6c8bda0bfa0cb0` 必须精确四文件。

### B. CPU/offline pytest

在 child：

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
LD_LIBRARY_PATH='' PYTHONPATH=. OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/disk/rl/worktrees/cosmos-framework-v3/.venv/bin/pytest -q \
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cache_test.py \
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_source_test.py \
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_policy_test.py \
  cosmos_framework/data/generator/action/datasets/robocasa_exact_window_cached_sft_test.py \
  cosmos_framework/model/generator/omni_mot_cached_vision_test.py \
  cosmos_framework/data/generator/action/utils/transforms_test.py \
  cosmos_framework/model/generator/omni_mot_model_test.py \
  -o addopts='' --tb=line
```

Expected：
- 191 passed
- 0 failed/error
- warnings可记录但不能隐藏 failure。

### C. static

formal new files：
- cached_sft.py
- cached_sft_test.py
- omni_mot_cached_vision_test.py

run：
1. Ruff check 三个新文件
2. Ruff format --check 三个新文件
3. `ruff check --ignore I001 cosmos_framework/model/generator/omni_mot_model.py`
4. `python -m py_compile` 四个 formal changed Python files
5. `git diff ce07cb6f...b6707e2c --check`
6. repeated exact scope name-only

注意：
- 不把 whole-file `ruff format --check omni_mot_model.py` 作为本 Gate PASS 条件，因为 parent formal child已有同一历史 format debt；
- ds不得格式化 core文件。

### D. Evidence persistence

保存 raw outputs：
- exact pair/gitlink/origin/scope
- pytest
- Ruff/new-file format
- core Ruff ignore-I001
- py_compile
- diff-check
- timestamp
- changed-file SHA256
- summary

PASS iff：
- exact pair一致；
- 191 tests全绿；
- C项全部PASS；
- scope精确四文件；
- ds未改仓库。

任一失败：
- 立即停止；
- 保存完整输出；
- 返回 GPT；
- ds不修代码、不扩大范围。

## Explicit boundary

即使本 Gate PASS，也只证明 synthetic/local CPU/static Phase3 contract。

仍不授权：
- Local visual96 / Local-TTT / B_stream/T/GA
- trainer/DCP/optimizer
- inference/server/eval
- real cache/source parity
- GPU/训练/仿真/SR

Phase3 closure后先进行 **read-only real cache-vs-online VAE parity Gate**，再进入 Phase4 Local-TTT integration。
