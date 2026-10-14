# GPT → DS_PRO｜V3 Gate B1 GPU Readiness — 仅 CPU Prepare + Resolved Config 证据

**日期：** 2026-10-14
**角色：** DS_PRO 仅负责验证、独立测试脚本与证据采集；GPT/Codex 独占 GitHub 代码/仓库文件修改权限。
**本次 Gate：** `B1_GPU_READINESS_PREPARE_AND_CONFIG_CPU_ONLY`
**授权边界：** CPU_ONLY / METADATA_ONLY / READ_ONLY。**不授权 8×H100、torchrun、CUDA 初始化、模型实例化、真实 DCP 载入、训练、保存、Gate M 或 Formal30k。**

## 0. 冻结对象，不得替换

- B1 Comparator **诊断代码 Root**：`dfeace66bbce549bf94a447c18f3d51e5dd2e376`，Gitlink `8f3672d1c15b6bb8e6c1795a7e6af9c2218763b1`。现有 **B1 CPU Code Gate 已 CLOSED**，138 pytest/22 Ruff 全 PASS，不再重复。
- **SOURCE/Index8**：Root `b159f45906f7261d028aecc226ab7f2bb9807eb9` / Child `937066ffd90f2bf783ad4fbb4909e9c0b8922982`，期望 config digest `70e9867fffb5d00568328cdc29a9c49387344a49610b8837597342fb0325df37`。
- **TARGET/Packed128**：Root `c4731bca1a590663db88bd6cd74dbcf9fd513a85` / Child `c8dabbb3f3a7fa3098a0399f4aec3b1c57d90686`，期望 config digest `1ab2bbe4df9954467bb0acf0d371dce40dff8bd04cfa3c81ca0ec6fe76a94b4a`。
- **正式 V3 Child** `1d56320c08c56b0f8dd248919d152d81ae12ea7b` 是启动优化版本，**不得替代** B1 的两个历史冻结 Child。
- 原始 `iter_000001300` Checkpoint、latest 指针、B0 完整 `checkpoint_fingerprint` 不得变更。Fingerprint 从已关闭的 B0 证据读取，**不得为了本次 Gate 再对 32 个 DCP shard 全量 hash**。
- RoboCasa 451GB 数据已离线验收：**不得重跑 VerifiedExactWindowIndex.verify_files、CacheCatalog._audit_files、SourceReader._preflight_metadata，也不得对每 Episode stat/glob/hash/rglob、重新构建冷 Index。**

## 1. CPU Lane A — 合法冻结 Pair 的实际 `prepare`（优先执行）

准备 3 套 **干净且各自独立的只读 checkout/worktree**：B1 诊断 Root（调用脚本），SOURCE 原始 Root+Child，TARGET 原始 Root+Child。不要在正式训练工作树做 checkout/reset、不要强推、不要污染生产 Checkpoint。
记录并核对 `git rev-parse HEAD`、`git ls-tree HEAD cosmos-framework`、child HEAD、`git status --porcelain`。3 套身份任何一项不符，**停止；不要改代码绕过 SHA 校验**。

从 DS 已有 B0 正式证据找到真实 `B0_FINGERPRINT`（64hex）；从当前服务器找到真实的 `ITER1300`、已验收 `INDEX_ROOT`（存在 `receipt.json`）、`CACHE_ROOT`、`SOURCE_ROOT`、`EDGE_PATH`、`VAE_PATH`、`BASE_CKPT`、**实际冻结的** `VISION_BUCKET`。不得把测试占位字符串、凭空构造的 digest/指纹或猜测的 resolution 当作合法回执。

以下是命令模板；**先在 DS 的环境里用真实绝对路径填充环境变量，逐项核验，再执行**：

```bash
export CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 LD_LIBRARY_PATH='' PYTHONDONTWRITEBYTECODE=1
# 环境由 DS 从已验收 B0/Phase5 记录解析；不允许随意填充假值：
# B1_DIAG_ROOT SOURCE_FROZEN_ROOT TARGET_FROZEN_ROOT ITER1300
# INDEX_ROOT CACHE_ROOT SOURCE_ROOT EDGE_PATH VAE_PATH BASE_CKPT
# B0_FINGERPRINT VISION_BUCKET

B1_SCRIPT="$B1_DIAG_ROOT/tools/gates/v3_gateb1_run.py"
for leg in index8 packed128; do
  if [ "$leg" = index8 ]; then ROOT="$SOURCE_FROZEN_ROOT"; else ROOT="$TARGET_FROZEN_ROOT"; fi
  for profile in P0_FIXED P1_MATCHED_STOCHASTIC; do
    python "$B1_SCRIPT" --mode prepare --leg "$leg" --profile "$profile" \
      --root-worktree "$ROOT" --checkpoint "$ITER1300" \
      --dataset-index-root "$INDEX_ROOT" --cache-root "$CACHE_ROOT" \
      --source-root "$SOURCE_ROOT" --edge "$EDGE_PATH" --vae "$VAE_PATH" \
      --base-checkpoint "$BASE_CKPT" --checkpoint-fingerprint "$B0_FINGERPRINT" \
      --vision-resolution "$VISION_BUCKET" \
      --output-root "/tmp/ds_pro_v3_b1_readiness_20261014" \
      --job-name "b1_readiness_only" --repeat 0
  done
done
```

**PASS 证据要求：** 每次 exit=0，stdout 状态严格为 `PREPARE_ONLY_NO_GPU_OR_DATASET_SCAN`；`root`、`child`、`resolved_digest_expected` 分别与本指令冻结值相同；`checkpoint_write_authorized=false`、`gpu_authorized_by_prepare=false`。采集原始 stdout/stderr、耗时、完整参数路径（敏感 token 除外）和操作系统进程退出码。若任一次 `RunBlocked`，保存首个真实错误即 STOP，**不使用假的 Root 跑出来的预期失败冒充合法 `prepare` PASS**。

注意：`--mode prepare` 只核对路径、Git SHA、索引收据存在与预定义 digest **声明**，并不计算实际训练 `config_digest`，也不实际加载 DCP、真实模型或 dataset；不得把 Prepare PASS 说成 GPU Ready PASS。

## 2. CPU Lane B — 正确来源的 Resolved Config Receipt（不可调用重型预检）

**唯一配置来源** 是两个冻结 Child 的 `examples/psm_wma_robocasa_corrected_phase5.py`，而不是历史 H100/H3F。DS 可以在 `/tmp` 自己构建临时 CPU config-only 脚本；不得编辑 GitHub 代码和 test 文件。

尽可能用 `_load_config(args)`、其真正的 `overlay_config` 及**此前已验收的轻量 Receipt/Manifest**构造对应的 contract（需要时按源码 ABI 构造；不得伪造），但**绝不调用完整 `phase5.preflight()`**、LeRobot 全量 dataset 构造、model `instantiate`、real DCP load、`train()`。如果实际解析所需 contract 无法从轻量 metadata 安全构造，应标为 `CONFIG_ONLY_BLOCKED`，注明精确文件/行/依赖，交 GPT 修改代码；**不得转去重扫数据**。

分别记录 SOURCE/TARGET（及逐字段 side-by-side diff）：
1. exact Root/Child、真实 `config_digest` **仅在独立真实计算得出时填写；否则写“EXPECTED_ONLY/NOT_RECOMPUTED”**；`native_batch_layout`；
2. `optimizer_type`、selected parameter key patterns、`lr`、`lr_multipliers`、`weight_decay` 与 skip patterns、`betas`、`eps`、fused/master 标志；
3. Edge `loss_scale`、`action_loss_weight`、vision/action loss 与额外 aux/LBL、归一化/active-mask 开关；
4. `model.precision`、FSDP shard/replicate degree、reduce dtype、Context Parallel，T=16/B=8/GA=2/K=4、action raw15/state15/action-model64、Hpred16；
5. `train_time_video_distribution`、`train_time_action_distribution`、`shift`（按实际 `VISION_BUCKET`）、`independent_action_schedule`、`causal_training_strategy`、CFG caption dropout 率、独立 vision/action `condition_mask`；
6. `sound_gen`、`independent_sound_schedule`、`attention_dropout`（**期望全部禁用/0，若有生效 override 则 BLOCK**）、其他训练可达随机调用点；
7. `trainer.grad_scaler_args`、Optimizer/GradScaler 当前 API、scheduler `max_iter=30000`/`warmup=500`/`save_iter=100`（以真实配置为准，差异必须报告）、callbacks 与 Checkpointer strict/load_training_state/EMA 开关；
8. 两个冻结 Child 的被测训练入口/方法实际 import 路径，不得从 V3 最新 Child 偷换；
9. 记录哪些值是 **SOURCE-DERIVED / RESOLVED / B0-RECEIPT / UNRESOLVED**，绝不可把预期值报为已实测。

对齐必须对照 B1 r2 数值预冻结设计：`docs/collab/chatgpt/designs/2026-10-14_GPT_V3_Packed128_GateB1_numeric_criteria_prefreeze_addendum_r2.md`。预提案阈值仍 `OWNER_NUMERIC_FREEZE_PENDING`，**DS 不得自行批准或调阈值**。

## 3. CPU Lane C — 合法 Root 下的未授权执行拒绝 + 静态安全性

只有 Lane A 合法成功后，才用其中一套**真实冻结 Root 参数**做一次 `--mode execute` 的**无授权文件** CPU 负面测试，确保在 GPU/CUDA/model/DCP 之前因缺失 Owner authorization 而拒绝。复用上方命令，仅改 mode 为 execute；**绝对不传** `--owner-authorization-json`，保持 `CUDA_VISIBLE_DEVICES=''`。若意外通过授权检查，立即 STOP，记录安全缺陷。

仅做针对性静态确认：`NoSave` 覆盖完整 native GA2 两步、相同 ConsumerKey 的 Sigma/Epsilon/Caption CFG 对齐点、Sound/Attention Dropout 真实禁用、不写 Checkpoint/latest、不进入 Formal30k 目录。前轮138个 CPU 测试和冻结 Child ABI 已验收，不再重跑。无法在 CPU 验证的真实 kernel nondeterminism、GPU gradients/moments、Stochastic parity 明确标 `GPU_UNVERIFIED`，不得报告 PASS。

## 4. 统一报告 + Gate 纪律

DS_PRO 交付**一份**报告：
`DS_PRO_V3_B1_GPU_Readiness_CPU_Prepare_Config_2026-10-14.md`

报告至少包含：准确 Code/Root/Child SHA 表、四次合法 Prepare 的命令/退出码/JSON 与声明 digest、原始 DCP/B0 fingerprint 的回执来源、双腿 Resolved Config 逐字段 diff（注明 provenance）、禁用 Sound/Dropout 静态/已解析证据、合法 Root 未授权 `execute` 负面测试、真实遗留风险及明确 `PASS / BLOCKED / UNRESOLVED`；必要时附上 DS 自建临时脚本路径与 SHA，**不提交任何 GitHub 文件或修改生产代码**。

DS 的结论仅为 **EXECUTOR_READINESS_EVIDENCE**；GPT 单独审核此报告，确定是否存在需要 GPT/Codex 修复的真实代码问题，并准备最后的 Owner 数值阈值冻结表。

**硬边界：** 未经后续独立 Owner 批准，不运行 `torchrun --nproc_per_node=8`、`--mode execute`（除上述缺失授权文件、保证 CPU 环境的负向安全检查）、真实 DCP 模型载入、真实 GPU、Checkpoint 迁移、Formal30k。无 451GB 数据复验，无 B0 重跑，无 V3 全仓审计。

**当前正式状态：** B0 CLOSED / B1 CPU Code Gate CLOSED / B1 GPU `GPU_NOT_AUTHORIZED` / Numeric `OWNER_SIGNOFF_PENDING` / Gate M & Formal30k HOLD。
