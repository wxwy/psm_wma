# V3 Stage B1 v0.2 窄范围整改记录

- Gate：V3-STAGE-B1-LATENT-PRODUCER；状态 REVIEW；ChatGPT 设计/审核，用户 owner/最终裁决，cx 实现，ds 数据/执行取证。
- 设计 authority：`65271367978537c5d7b5bae5fa50b1ee8056f356` 中 `PSM-WMA_V3_stage_b1_latent_producer_gate_design_v0.2_2026-09-27.md`。
- 整改对象：root `bedef75b6bc76cb167f2e27aeaecfe303865f9ab` / child `5f9c39464761665843b0f08c5e1d578f72114b33`；对应 `reviews/2026-09-27_V3_stage_b1_latent_producer_bedef75b_5f9c394.md` 为 REQUEST_CHANGES。
- 本记录承载本轮范围、认领和状态；root 仅新增本记录及最终 Gitlink，不改历史设计/记录、TODO/SESSION 或 artifacts。
- child 只修改原有四个 B1 文件：`robocasa_latent_evidence.py`、`robocasa_latent_evidence_test.py`、`robocasa_segment_producer.py`、`robocasa_segment_producer_test.py`，均位于 `cosmos_framework/model/generator/mot/`。源码工作区仅 `/disk/rl/worktrees/cosmos-framework-v3`；B0、trainer、config、optimizer、checkpoint、policy cached-latent 不动。

## HIGH 整改映射

1. HIGH-1：metadata 固定 H5 root attrs；读取 `frame_count`，不要求、合成或回退 `source_video_frames`，仍核对源 episode 和视频帧数。
2. HIGH-2：reader 精确校验 `range(0,F,4)` 加必要的末端 `F-1`；两路各自必须等于同一向量。独立 lookup 要求严格递增，使用 max(endpoint<=source)，支持不规则terminal但不使用nearest/ceil。
3. HIGH-3：reader 移除任意latent/endpoint/metadata/camera参数；固定 `observation.images.robot0_agentview_left` 和 `observation.images.robot0_eye_in_hand`，读取各自 `latents/`、`indices/latent_source_frame_indices/`、`valid/`。两路fp16 `[N,48,16,16]`、整数endpoint及全真bool valid必须通过；按width融合到fp32 `[48,16,32]` 后计算mean48+RMS48。right camera不参与。
- executed action继续要求调用方提供V3 loader转换的raw15；新增H5实际12D `robot/action`拒绝测试。不将shape验证宣称为已证明真实loader来源，ds仍须提供来源证据。
- consumer的source=t−1、current与previous独立、chunk32/33帧、TTT16、PAD及identity语义均不变。

## 验收和交付

- CPU pytest 132/132 PASS，无跳过，9.84秒；B1共100项（较v0.1新增34项），B0原32项全部通过。四个B1文件Ruff check/format check PASS；两仓diff-check与staged diff-check PASS。日志 `/tmp/cx_v3_b1_v02_cpu.log`；JUnit `/tmp/cx_v3_b1_v02_cpu.xml`，不纳入Git。
- child `1ecebf1ab2fa64bc1d5906959c4cb1fe1d1edc5a`，仅4文件，+174/-68；B0及其他文件相对前formal child无diff。先child commit/push，再root Gitlink+本记录commit/push；root formal SHA为包含本记录的提交，交付报告核对远端exact pair。新pair留待fresh review，不自授closure。
- 全部使用合成H5与CPU tensors，不加载真实缓存/模型、不执行VAE、不联网或GPU。真实数据需ds在新pair按v0.2§7完成至少3任务×2episode取证。

## 验收命令与证据覆盖

工作目录 `/disk/rl/worktrees/cosmos-framework-v3`；仅V3 venv。pytest禁用上游inference conftest及插件自动加载，保持CPU隔离。

```bash
CUDA_VISIBLE_DEVICES='' COSMOS_DEVICE=cpu LD_LIBRARY_PATH='' \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
.venv/bin/python -m pytest -c /dev/null --noconftest -p no:cacheprovider -q \
cosmos_framework/model/generator/mot/robocasa_latent_evidence_test.py \
cosmos_framework/model/generator/mot/robocasa_segment_producer_test.py \
cosmos_framework/model/generator/mot/local_evidence_test.py \
cosmos_framework/model/generator/mot/local_memory_segment_test.py \
cosmos_framework/model/generator/mot/local_memory_segment_adapter_test.py \
--junitxml=/tmp/cx_v3_b1_v02_cpu.xml > /tmp/cx_v3_b1_v02_cpu.log 2>&1
.venv/bin/ruff check --no-cache \
cosmos_framework/model/generator/mot/robocasa_latent_evidence{,_test}.py \
cosmos_framework/model/generator/mot/robocasa_segment_producer{,_test}.py
.venv/bin/ruff format --no-cache --check \
cosmos_framework/model/generator/mot/robocasa_latent_evidence{,_test}.py \
cosmos_framework/model/generator/mot/robocasa_segment_producer{,_test}.py
git diff --check
git diff --cached --check
```

- root `frame_count` fixture成功；有错误的旧attr仍只读取frame_count，缺少root frame_count不回退metadata子group或旧attr。
- F=313/299/280及F=1精确endpoint向量；terminal附近source逐帧对照max<=source；缺失terminal、off-grid interior拒绝。
- left/wrist分别覆盖错误endpoint次序/重复/越界/长度/dtype以及latent形状/dtype/NaN/Inf；两路都必须匹配同一canonical vector。valid分别覆盖False、非bool、长度错和缺失。
- 双路取不同值直接核对width融合mean/RMS精确公式及fp32；任一路未来endpoint变化不影响早期visual96；right camera改成NaN不影响结果；任意camera/keys参数均TypeError拒绝。
- 合成H5真实schema的 `robot/action` 12D直接作为raw15输入时拒绝；原有64D、长度错、非有限拒绝路径保留。
- 保留全部producer时序、cursor0/1/terminal PAD、action精确t−1、identity和chunk32/33帧验证；B0无修改。上述是CPU/static证据，不替代ds对真实raw15来源及缓存的取证。
