# GPT → DS_PRO｜V3 B1 实 GPU 数值等价：P0 最小 Smoke → 独立复审 → 完整 B1

**日期：** 2026-10-15  
**Owner 最新明确授权：** 2026-10-15 “直接让ds做B1 P0 GPU Smoke，显存够的，就是计算挤兑”。现在 **P0 repeat0 两腿共享 GPU 执行已获 Owner 授权**，机器上其他任务 100% util 不再单独构成 STOP。正式回执在 V3 `docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_46e9cc0e.json`（不是冻结诊断分支）。
**执行角色：** DS_PRO 可在 /tmp 构造临时验证脚本及报告，但 **不得修改 GitHub 代码、冻结 Root/Child、生产模型、Checkpoint 或正式训练目录**。GPT 承担代码改动及 Gate 审核。  
**当前 Gate：** `B1_GPU_P0_FIXED_TWO_STEP_SMOKE`，先跑 **SOURCE Index8 + TARGET Packed128 各一次独立 8×H100 torchrun、repeat=0、P0_FIXED**，只跑原始 iter1300 后 **1301、1302 两步（GA2）**。**不是**完整 B1 PASS，也不是 Formal30k。  
**硬前置（2026-10-15 已满足 Owner 审批）：** 只能将上述 **V3 官方已授权 JSON** 原样复制到运行机器 `/tmp`，核验精确实现 SHA、B0 全量指纹、r2 数值策略、P0-only 范围和 co-resident 允许条件。**如果训练机暂未拿到并验过该文件，仍不得 torchrun。** 不得以此前 GPU 使用率100% 为单独阻塞；必须实测每卡剩余显存≥16384 MiB、GPU健康。

## 0. 固定 SHA、数据与阈值，禁止改名替换

| 角色 | Root SHA | Child/Gitlink SHA |
|---|---|---|
| 诊断执行器 | `46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a` | `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1` |
| **SOURCE Index8** | `b159f45906f7261d028aecc226ab7f2bb9807eb9` | `937066ffd90f2bf783ad4fbb4909e9c0b8922982` |
| **TARGET Packed128** | `c4731bca1a590663db88bd6cd74dbcf9fd513a85` | `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686` |

Owner 事先批准并冻结 r2 数值阈值，Policy SHA256 `bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda`，唯一权威：`docs/collab/chatgpt/designs/2026-10-15_V3_GateB1_r2_numeric_Owner_frozen_preGPU.md`。B0 原始完整 DCP 指纹 `2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999`，不得修改/重算所有 shard。

**DS_PRO 上轮经核对的真实路径（开工前逐一 stat、核验 SHA；若已不存在，只能使用自己新的 /tmp clean detached checkout，不能修改训练工作树）：**
```bash
export DIAG_ROOT=/tmp/ds_pro_v3_b1_gpu_20261015/diag       # NEW clean detached checkout @ 46e9cc0e
export SRC_ROOT=/tmp/ds_pro_v3_b1_readiness_20261014/source   # b159f459.../937066ff...
export TGT_ROOT=/tmp/ds_pro_v3_b1_readiness_20261014/target   # c4731bca.../c8dabbb3...
export ORIG_CKPT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma_v3/outputs/local_ttt_robocasa_raw15/psm_wma_v3/corrected_phase5/formal_verified_index_30k/checkpoints/iter_000001300
export INDEX_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-verified-index-r1
export CACHE_ROOT=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window
export DATA_ROOT=/mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic
export EDGE_PATH=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID
export VAE_PATH=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Wan2.2-TI2V-5B/Wan2.2_VAE.pth
export BASE_DCP=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/models/Cosmos3-Edge-Policy-DROID-dcp
export B0_FP=2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999
export RESOLUTION=256
export DIAG_PY=/mnt/data/shenzhen/szrobot/logs/.tmp_backup/psm_wma/cosmos-framework/.venv/bin/python
export SMOKE_ROOT=/tmp/psm_v3_b1_p0_smoke_46e9_20261015
```

**注意：** `DIAG_ROOT` 不是现存可信路径的声明，必须新建/核实为精准 SHA（原 `/tmp/.../b1_diag` 上轮仍是旧的 `dfeace66`，绝对不能复用）；`SRC_ROOT/TGT_ROOT` 路径若已消失同理。禁止在正式训练工作树执行 `git checkout/reset/clean`，不得带入新 live V3 Child。 `SMOKE_ROOT` 必须事先检查不存在或为空，并属于独立 /tmp namespace。

## 1. 阶段0 — **CPU/静态准备，现在可执行；不碰 GPU 计算**

1. 使用只读 clone/worktree 取得上述三对准确 SHA；记录三套 Root/Child 的 `git rev-parse HEAD`、`git ls-tree HEAD cosmos-framework`、`git status --porcelain`，任何不符立即 STOP。
2. 核验真实原始 iter1300 DCP 路径、acceptance `receipt.json`、models、cache、数据存在。**不遍历/重新 hash 32 DCP shard 或451GB语料；不调用 full Phase5 preflight**。使用已关闭的 B0/Readiness receipt。
3. 仅用轻量 `_load_config`/先前 DS CPU config receipt 检查 **真实** `rectified_flow_training_config.shift` 中的 `RESOLUTION=256` **键的实际类型**，并检查诊断 `_sampling` 的 `shift_config[args.vision_resolution]` 能在真实 config 上成功索引；若 `KeyError/TypeError`，STOP + 文件:行及证据交 GPT 修代码。**不能猜测、硬改配置、修改冻结 Child 或在 DS /tmp 代码里偷偷绕过正式执行路径。**
4. **Owner 已批准 GPU 共驻**：使用 `nvidia-smi -L` 和 `nvidia-smi --query-gpu=index,memory.free,memory.total,utilization.gpu --format=csv,noheader,nounits` 检查8张 H100 是否健康，逐卡空闲显存是否≥16384 MiB，并记录共享用户负载、/tmp 磁盘、CPU内存。即使所有卡100% util，只要显存安全且不扰动其他进程即可启动；不要 kill/pause/renice 别人的任务。资源波动/OOM/通信异常则停止**自己的** Smoke；共驻的耗时不做独占吞吐指标。
5. 新 `46e9cc0e` 诊断 runner 的 **CPU-only `--mode prepare`**（两个 leg，各 P0 一次）在已有有效 receipt 上 exit0，且返回固定 `PREPARE_ONLY_NO_GPU_OR_DATASET_SCAN`、B0 FP、Root/Child、config digest、`checkpoint_write_authorized=false`。无需重复143/144 CPU tests 或扫描数据。
6. **Owner JSON 现已正式签发到 V3**：从 `V3:docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_46e9cc0e.json` 读回 JSON，复制到训练机 `/tmp` 的只读文件，通过 `_owner_receipt` 及 DS 的独立作用域检查；要求 `P0_FIXED/repeat0/index8→packed128/2 steps/8 H100`，策略/Source/Target/B0 全部匹配。DS 不得自行生成、修改或扩大授权字段。若暂无法读取官方 V3 文件，报告 `AUTH_RECEIPT_NOT_MATERIALIZED`，不要代填 `authorized=true`。

## 2. 阶段1 — **仅 Owner 单独批准 P0 GPU Smoke 后**，先 SOURCE 再 TARGET

授权范围严格为 **两个独立 8-rank torchrun**、`P0_FIXED / repeat=0`，各从原始 iter1300 同一份**只读** DCP 恢复并在内存中完成 `1300→1301→1302` 的两次真实 GA2 更新；不 Save、不改源 DCP/latest，不启动 `Trainer.train()`，只能写入 `SMOKE_ROOT`。每腿有自动 fail-close，错误即停，禁止多次自动重试。

```bash
set -euo pipefail
export HF_HUB_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7
# 这里使用 V3 官方已签发的 Owner JSON，不允许自己构造新 JSON。
# 先在独立的 V3 文档 checkout (不要改动冻结 diag/source/target tree) 执行示例：
# AUTH_REL=docs/collab/chatgpt/approvals/2026-10-15_V3_B1_P0_GPU_co_resident_Owner_authorization_46e9cc0e.json
# git -C "$V3_DOCS_ROOT" show "V3:$AUTH_REL" > /tmp/psm_v3_b1_owner_P0_46e9.json
# chmod 0444 /tmp/psm_v3_b1_owner_P0_46e9.json
# export OWNER_GPU_APPROVAL_JSON=/tmp/psm_v3_b1_owner_P0_46e9.json
: "${OWNER_GPU_APPROVAL_JSON:?Obtain exact Owner-approved P0 receipt from V3}"
test -f "$OWNER_GPU_APPROVAL_JSON"
"$DIAG_PY" - "$OWNER_GPU_APPROVAL_JSON" <<'PY'
import json, sys
x = json.load(open(sys.argv[1], encoding='utf-8'))
scope = x['approved_scope']
assert x['gate'] == 'V3_PACKED128_B1_GPU_OWNER_APPROVED' and x['authorized'] is True
assert x['implementation_sha'] == '46e9cc0e5dc97a1f7f813b2a332b095aa1062a4a'
assert x['numeric_policy_sha256'] == 'bcb9f8d699c0ce6c79d54cf5bb213c157665798c38dae9daeb6b4a1607e63fda'
assert x['checkpoint_fingerprint'] == '2e409afe788f4faf2cc1f5db8d500638a219647dc90283f9687863212d77d999'
assert scope['profiles'] == ['P0_FIXED'] and scope['repeats'] == [0]
assert scope['legs_in_order'] == ['index8','packed128']
assert scope['completed_iterations'] == [1301,1302]
assert scope['maximum_independent_torchrun_jobs'] == 2 and scope['co_resident_with_other_users_approved'] is True
print('OWNER_P0_SCOPE_ACCEPTED')
PY

# 仅在所有阶段0检查 PASS 且 Owner 单独授权时执行。
mkdir -p "$SMOKE_ROOT" "$SMOKE_ROOT/logs"
SCRIPT="$DIAG_ROOT/tools/gates/v3_gateb1_run.py"
COMMON=(
  --mode execute --profile P0_FIXED --repeat 0
  --checkpoint "$ORIG_CKPT"
  --dataset-index-root "$INDEX_ROOT"
  --cache-root "$CACHE_ROOT" --source-root "$DATA_ROOT"
  --edge "$EDGE_PATH" --vae "$VAE_PATH" --base-checkpoint "$BASE_DCP"
  --checkpoint-fingerprint "$B0_FP"
  --vision-resolution "$RESOLUTION"
  --output-root "$SMOKE_ROOT"
  --job-name b1_p0_smoke_46e9_repeat0
  --owner-authorization-json "$OWNER_GPU_APPROVAL_JSON"
)

# Job A: SOURCE Index8 — 跑完后人工检查 8 rank×iter1301/1302 JSON/PT、
#           原始 Checkpoint/latest 未改变、OOM/Traceback/IO/NaN 均为0。
"$DIAG_PY" -m torch.distributed.run --standalone --nproc_per_node=8 \
    "$SCRIPT" --leg index8 --root-worktree "$SRC_ROOT" "${COMMON[@]}" \
    2>&1 | tee "$SMOKE_ROOT/logs/index8_P0_repeat0.log"

# HARD STOP：此处是必须人工操作的安全门，不允许 Source 结束就自动跑 Target。
# 在确认 8 rank × 两 step 全部完成、无异常、原 Checkpoint/latest 未变，
# 且确有 Source 的完整原始证据后，人工键入下面的完整标记。
printf 'SOURCE evidence reviewed? Enter ALLOW_PACKED128 (otherwise STOP): '
if ! read -r SOURCE_GATE || [ "$SOURCE_GATE" != "ALLOW_PACKED128" ]; then
  echo "STOP: Packed128 was NOT launched; retain Source evidence."
  exit 0
fi

# Job B: TARGET Packed128，仅在本次人工安全门通过后独立执行。
"$DIAG_PY" -m torch.distributed.run --standalone --nproc_per_node=8 \
    "$SCRIPT" --leg packed128 --root-worktree "$TGT_ROOT" "${COMMON[@]}" \
    2>&1 | tee "$SMOKE_ROOT/logs/packed128_P0_repeat0.log"
```

**关键：** 2026-10-15 的 P0 co-resident Owner GPU JSON **已存在于 V3**，本次允许 DS 在按规定读回并核验后直接运行两个作业；不需要再次等 Owner 口头确认。此 JSON **不包含 P1/repeat1 授权**。严格遵守 Shell `pipefail`、Source 后人工 STOP、无自动重试和隔离证据。若其他进程已使每卡显存不足16GiB，则仍需停止，不得清退他人任务。

## 3. 每条腿的停机门槛（Source 失败不得跑 Target）

- 正确8 GPU/8rank，Frozen `config_digest`、vision resolution 256；真实模型/Optimizer/Scheduler/Local DCP state from iter1300 strictly restored，load training state full, no warm-start、missing/unexpected FQN 或 dtype 直接 STOP。
- 两个 completed iterations **必须是1301、1302**，每 rank 各2份 JSON/PT；每一份带真实 GA2 Consumer roster、`model_site_witnesses`、`cfg_transform_witnesses`、Full 或 Terminal Partial 与 nonempty gradient+Fast State，不能用原始 B0 mock 代替。
- `restore.source_checkpoint_fingerprint` = 指定 B0 FP，`runtime_shard_contents_rehashed=false`；每次恢复的 `runtime_lightweight_immutability_witness` 必须能记录并**跨所有 rank/leg 相等**。异常 => STOP，不得更改/重新 hash 原始 DCP 以“修复”。
- No `save`/latest 写入、no `Trainer.train()`、no Formal30k 路径；出现 RuntimeError/FailClosed/OOM/非有限/Rank hang 立刻终止作业并保存错误日志，不自行修仓库代码、调精度、加宽 r2 阈值或启用 RECAP/RL。
- 阶段1不再自动扩展到 P1 或 repeat1；需 GPT 对 P0 独立证据进行诊断与增量 Gate 判断。

## 4. P0 两腿完成后的**实际数值比较**（DS 可自建 /tmp CPU 脚本）

从 `SMOKE_ROOT/index8_P0_FIXED_repeat0/` 和 `packed128_P0_FIXED_repeat0/` 逐 rank、逐步（8 ranks × 1301/1302）载入官方 JSON 与 PT，复用正式诊断仓 `tools/gates/v3_gateb1_compare.py` 的 `validate_pair()`、`_compare_numeric()`、`canonical_site_witnesses()` 进行相同 Consumer/CFG/Sigma/Epsilon/Mask/FQN/Optimizer/Local 的严格检查；数值阈值来自固定 r2 SHA，不得自己定义更宽的 threshold。

为防 RAM/磁盘过量，按 rank/step 流式处理、一组一组释放 Tensor；生成精简表格与异常清单，而非打印全部巨型 Tensor。**不能直接运行默认完整 `v3_gateb1_compare.py` 并声称 P0 PASS**：其 `compare_complete_evidence()` 要求 P0+P1 × 两重复，共全部8次作业，本阶段数据未齐，这种失败属于预期不适用而非代码缺陷。

逐 rank×step 报告：
- `validated_pair=true/false`，实测 Full/Terminal 标签及 `ga_counts`，所有 rank 必须形成 Full+Terminal 证据；
- 每选中 FQN 的 Generation / Action / Local gradient、FP32 master ΔP、Adam ΔM1/ΔM2、绝对 moments 与四路 FP32 Fast State 是否满足已冻结 r2；不允许均值掩盖单 FQN 失败；
- 各 active weighted Loss 组件、随机输入站点、CFG payload 逐 Consumer 完全同值；
- `runtime_lightweight_immutability_witness` 必须在8 rank、两个 leg一致，B0 FP 固定；
- 实际运行时间、GPU 峰值显存、PT/JSON证据磁盘量、是否有任何 error。

**P0 Smoke 结果只能为：`PASS_FOR_P0_SMOKE_ONLY`（未完成正式 B1）或 `BLOCKED`**。即使两腿都成功，仍不能称 B1 GPU PASS。

## 5. 下一轮（当前不授权）和 DS 报告

正式 B1 仍需要：`P0_FIXED repeat1` 两腿 + `P1_MATCHED_STOCHASTIC repeat0/repeat1` 四腿，即在 P0 smoke 两作业通过后还需6个独立8卡 job，共8个。每次都检验两步、8 rank、Full+Terminal; 最终需完整比较器统一验证 P0/P1、跨leg、跨repeat 及冻结阈值。**不得自动续跑**。遇到任何 P0 false parity，先分析具体 FQN/随机数/恢复偏差，再决定是否需要 GPT 修实现与新的 SHA/Gate。

DS 报告：`DS_PRO_V3_B1_P0_GPU_Smoke_46e9cc0e_2026-10-15.md`，或若无 Owner GPU 许可则 `DS_PRO_V3_B1_P0_Prepare_Only_46e9cc0e_2026-10-15.md`，均只发给 GPT/Owner，不写 GitHub。至少包含：
1. 3 对 Root/Child/gitlink 全 SHA；Owner Approval 范围/reference（不暴露敏感内容）、Frozen Numeric Policy SHA 与 B0 FP；
2. prepare + GPU 命令、8 rank exit codes、是否 SIGINT/STOP、Wall/显存/磁盘/Log 路径；
3. 原始 DCP/latest 前后未变的轻量 witness；Full/Terminal、Consumer/σ/ε/CFG、两步数值表及失败 FQN；
4. **B1 GPU 正式 PASS 未授予**；Gate M 和 Formal30k 一直 HOLD。

不要重跑 B0 CPU、144个 B1 CPU tests、451GB 数据验收、V3 全仓审计。DS 的每个发现通过精确 `file:line` + stdout/stderr 返回 GPT；所有 GitHub 代码修复由 GPT/Codex 完成。
