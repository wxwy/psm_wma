# DS_PRO → 拉取已合并 V3；Owner 手动仿真启动（2026-11-03）

**Owner 指令**：DS_PRO 负责将已经通过审核、已合并到 Root V3 + Child 官方分支的代码更新到**独立评测 checkout**并回报身份；**不授权 DS 自行启动真实 GPU/模拟器/900EP**。Owner 自己手动选择/执行后续仿真测试。本文件是运维交接，不是新 Production/Code Gate，也不改变已批准正式 Pair。

## 1. GitHub 已合并的身份

- Root V3 生产合并提交：`0f82519dfa22f190141b7a25c1c96fb476855742`，PR #15 `https://github.com/wxwy/psm_wma/pull/15`，双亲 merge，保留 V3 后续 G2 调研/索引更新。
- Child 官方分支：`wxwy/cosmos-framework:v3-local-ttt` 已快进到 `c93f2abf4fb27d36176ff8db094379a853cec796`，Root V3 Gitlink 同此 SHA。
- Root V3 HEAD 可能因**之后只追加 docs/审核交接**而领先生产合并点；DS 必须记录实际 `origin/V3` SHA，并确保上面 merge SHA 为祖先、Child HEAD 与 Gitlink 一致，`git status --porcelain` 干净。
- Core/Media 既有证据：Media CPU379作者、RM-ALL-R01独立CPU122、Root Profile独立CPU42、R01旧GPU生成19 MP4+19 VIDEO_SAVED/ACK、19实数据OFFLINE副本汇总 COMPLETE；**原 R01 Fresh exit1 仍 FAIL_RETAINED**，新代码没有新 GPU Fresh exit0 证据；真正 B2(>=2)硬件 batch 仍未证明。
- **DS 只更新独立 checkout**；训练/旧 R01、out2、NoTTT/H2/H3/旧 Evidence checkout 和任何在运行的 worker/source，均不可 pull/reset/checkout/改动。

## 2. DS_PRO 只读同步 + 回验命令（必须在 DS 自己授权的独立评测 checkout 执行）

下面 `EVAL_ROOT` 是 DS 自己选的**干净、非训练非历史证据**的专用 checkout；不是旧 `cpu122_r01/root` 或 `canary_r01/out/R01`。先检查 clean，不能 clean 就 STOP 并另建隔离 clone；**不要 `git reset --hard`、`git clean`、`git pull --rebase`、force-push**。

```bash
set -euo pipefail
export EVAL_ROOT=/ABS/DS_OWNED_CLEAN_V3_EVAL_CHECKOUT
test -d "$EVAL_ROOT/.git" || { echo "Use a separate clean clone/worktree first"; exit 2; }
test -z "$(git -C "$EVAL_ROOT" status --porcelain)" || { echo "DIRTY_ROOT_STOP"; exit 3; }
git -C "$EVAL_ROOT" fetch origin V3
git -C "$EVAL_ROOT" switch V3
git -C "$EVAL_ROOT" pull --ff-only origin V3
git -C "$EVAL_ROOT" submodule update --init --checkout cosmos-framework
test -z "$(git -C "$EVAL_ROOT" status --porcelain)" || { echo "DIRTY_ROOT_STOP"; exit 4; }
test -z "$(git -C "$EVAL_ROOT/cosmos-framework" status --porcelain)" || { echo "DIRTY_CHILD_STOP"; exit 5; }
git -C "$EVAL_ROOT" merge-base --is-ancestor 0f82519dfa22f190141b7a25c1c96fb476855742 HEAD
test "$(git -C "$EVAL_ROOT" rev-parse HEAD:cosmos-framework)" = "c93f2abf4fb27d36176ff8db094379a853cec796"
test "$(git -C "$EVAL_ROOT/cosmos-framework" rev-parse HEAD)" = "c93f2abf4fb27d36176ff8db094379a853cec796"
printf 'ROOT=%s\nCHILD=%s\nGITLINK=%s\n' \
  "$(git -C "$EVAL_ROOT" rev-parse HEAD)" \
  "$(git -C "$EVAL_ROOT/cosmos-framework" rev-parse HEAD)" \
  "$(git -C "$EVAL_ROOT" rev-parse HEAD:cosmos-framework)"
```

注意 `git worktree` 的 `.git` 可能是文件，不是目录；如果 DS 使用独立 worktree，可把首项检测替换为 `git -C "$EVAL_ROOT" rev-parse --is-inside-work-tree`，但仍必须保持前后 clean 且不触及共享工作树。若现有单独 checkout 仍有旧正式 evidence，建议另建一个**全新独立 clone**，不得破坏旧证据。Git 子模块 URL 来自 `.gitmodules`；下载失败报告 `SYNC_BLOCKED`，不要擅自修改仓库正式 URL。

**DS 交付**：回报 `DS_V3_SYNC_PASS/FAIL`、专用 checkout 绝对路径、实际 V3 Root HEAD、Child HEAD、Gitlink、两仓 clean、最新入口文件存在以及相关输出；同步完**停止**，不自动启动 GPU、仿真或900EP。

## 3. Owner 手动启动：使用官方 EvalV2 CLI

现有入口 `scripts/run_robocasa_eval_v2.sh` → `scripts/robocasa_eval_v2_cli.py`，模式为 `dry-run`、`fresh`、`resume`。**生产/运行源码以最新 V3 + 正确 Child/Gitlink 为准；不要用旧 R01 Root/Child 启动。**

官方模板 `configs/eval/robocasa_eval_v2_phase_b.example.yaml` 的必要环境变量：
`EVAL_CHECKPOINT`, `EVAL_MODEL_CONFIG`, `EVAL_DATASET_ROOT`, `EVAL_OUTPUT_DIR`, `EVAL_SERVER_PYTHON`, `EVAL_SIM_PYTHON`。
全部必须是已确认的真实绝对路径，checkpoint使用既有 `iter_000020000` 只读目标，数据为 RoboCasa365 target-atomic，server 和 simulator 两种解释器沿用此前 DS 硬件成功的版本；不要凭猜测修改环境或训练目录。
模板的 `vendor_lock: third_party/robosuite_patches/vendor.lock.json` 是相对根仓路径，所以**先 `cd "$EVAL_ROOT"`**。

在**新的、隔离的输出目录**建立自己的 YAML 副本，例如：
```bash
cd "$EVAL_ROOT"
export PSM_REPO="$EVAL_ROOT"
# 下列六项必须填写 DS 上已有的真实只读/可执行路径，不是文本中的占位符：
export EVAL_CHECKPOINT=/ABS/READONLY/iter_000020000
export EVAL_MODEL_CONFIG=/ABS/READONLY/model_config.yaml
export EVAL_DATASET_ROOT=/ABS/READONLY/robocasa365-target-atomic
export EVAL_SERVER_PYTHON=/ABS/SERVER_ENV/bin/python
export EVAL_SIM_PYTHON=/ABS/SIM_ENV/bin/python
export EVAL_OUTPUT_DIR=/ABS/NEW_RUN_OUTPUT/R02
export PYTHON="$EVAL_SIM_PYTHON"
export __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json
export CFG=/ABS/NEW_RUN_OUTPUT/eval_phase_b.yaml
mkdir -p "$(dirname "$CFG")"
cp configs/eval/robocasa_eval_v2_phase_b.example.yaml "$CFG"
# 按 Owner 意图检查 YAML 内 save_generated_video: all|first|none，
# 模板为 first。该字段【没有】--save-generated-video CLI override。
```

### A. 最小新 Fresh 验证（CloseFridge ×1EP）

```bash
bash scripts/run_robocasa_eval_v2.sh dry-run --config "$CFG" \
  --execution-profile phase_b --local-memory-mode required \
  --gpus 6 --render-gpus 4 --render-backend egl \
  --sims-per-gpu 1 --max-infer-batch-size 1 --batch-wait-ms 20 \
  --media-spool-max-jobs 4 --media-spool-max-bytes 536870912 --media-drain-timeout-s 300 \
  --tasks CloseFridge --episodes 1 --output-dir "$EVAL_OUTPUT_DIR"
```
手动检查 `dry-run` 的 task/slots/Server6→Render4、resolved config与唯一新输出路径；`dry-run` 不加载模型/不执行仿真。Owner 确认检查通过后，**将同一命令中的 `dry-run` 改为 `fresh`**；根据 DS 已成功先例在 video/render supplemental groups 下运行（`sg video` → `sg render` wrapper），保留 NVIDIA EGL vendor 设置。这些 groups/包装器须用 DS 服务器已实测的原始 launcher，**不要未经核对就省略**；若特殊权限/环境未知停止并让 DS 提交实际命令，不尝试任意 sudo。

严格 `save_generated_video: all` 的 Fresh 成功还应有 `exit0`、`summary.results_qualified=true`、`media_summary.status=COMPLETE`、`replans==MP4==receipt==ACK`、Local reset与process cleanup clean。此前 R01 19/19 已通过离线验证，不要求在本轮额外无限复测。

### B. 正式 18×50 =900EP（由 Owner 另行手动决定运行）

只在 **新的** `EVAL_OUTPUT_DIR` 和 Owner 认可的 YAML/硬件资源下：
```bash
bash scripts/run_robocasa_eval_v2.sh dry-run --config "$CFG" \
  --execution-profile phase_b --local-memory-mode required \
  --gpus 6,7 --render-gpus 4,5 --render-backend egl \
  --sims-per-gpu 1 --max-infer-batch-size 1 --batch-wait-ms 20 \
  --tasks all --episodes 50 --output-dir "$EVAL_OUTPUT_DIR"
```
`--tasks all` 会严格要求18个已支持的 RoboCasa365 target-atomic Task；`--episodes 50` 合计900。预检通过才将 `dry-run` 改成 `fresh` 并用相同video/render group wrapper执行。M1/B1为保守路径；想试M8/B2需另建一次非正式实验、不应将`max_infer_batch_size=2`误认为已经有真实B2合批证据。视频开关继续由 Owner 通过**本次 YAML 副本**独立控制，不要改模型/源配置；`fresh` 不可重用任何既有output目录。

## 4. 边界

此文仅传达 Owner 已明确的“DS 拉取并给启动指令”，**没有远程操控 DS 服务器的事实**，不代表 DS 已完成拉取，不代表 GPU Run 已经开始、被授权由DS启动或已经通过。请由 DS 在独立 checkout 完成同步后回报身份，不接触 GPU0–3/正在运行训练、旧 out2/H2/H3/R01/NoTTT、Checkpoint/DCP与历史日志；不能为了新测试修改历史Canary失败记录。
