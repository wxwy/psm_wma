# PSM-WMA G0-R03 Action Contract Runbook v0.1

状态：`draft`

## 目的

以真实 LIBERO 样本核验 parquet action 到模型 action、domain-aware projection、mask、仿真输出的完整合同，并冻结 Edge-Policy-DROID → LIBERO 的 domain warm-start 策略。

## 前置资产与入口

- 数据：`/gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot`
- checkpoint：`/gemini/code/models/Cosmos3-Edge-Policy-DROID`
- Python：`/root/venvs/psm_wma/bin/python`
- 数据入口：`get_action_libero_sft_dataset`
- projection：`DomainAwareLinear`
- 仿真映射：`cosmos_framework/simulation/libero/closed_loop_eval.py`

## 精确命令

工作目录：`/gemini/code/psm_wma`。不使用 GPU，不访问外网。

```bash
LD_LIBRARY_PATH=/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cudnn/lib:/root/venvs/psm_wma/lib/python3.13/site-packages/nvidia/cu13/lib \
PYTHONPATH=cosmos-framework \
/root/venvs/psm_wma/bin/python tools/g0/audit_r03_action_contract.py \
  --dataset /gemini/code/data/libero/libero_10_no_noops_1.0.0_lerobot \
  --checkpoint /gemini/code/models/Cosmos3-Edge-Policy-DROID \
  --output artifacts/g0/r03/R03_action_contract.json
```

## 输入输出与断言

输出 JSON 必须含 `provenance`、`runtime_contract`、`projection_smoke`、`trainable_scope`、`warm_start_decision`、`simulation_contract`、`failures`。

- 真实 action 链为 7D parquet → 10D rot6d → `quantile_rot` → 64D padding。
- chunk 16、20Hz、concat view、`raw_action_dim=10`、LIBERO domain 5；DROID domain 8。
- DomainAwareLinear 为 64→2048→64，输入输出 finite。
- trainable count 从 checkpoint header 和官方 selector 实算，不把约 1.423B 写成常量。
- 图像 180°/flip、gripper、rot6d→7D env delta 必须有源码锚点。

`PASS`：上述运行时 shape/domain/finite/normalization trace 全部成立，且 trainable scope 可复算。

`FAIL`：shape、domain、finite 或 normalization trace 任一冲突。

`BLOCKED`：数据、checkpoint、TorchCodec/CUDA 动态库不可读。

## Warm-start 决策

继承 shared Generator、time/vision adapters 与 `action_modality_embed`；保留 DROID domain 8 权重。LIBERO 必须使用独立 domain 5，仅重初始化并更新 `action2llm/llm2action` 的 domain 5 行，禁止把 DROID 8D/15Hz/chunk32 合同直接套到 LIBERO。R04 必须验证行级更新保护：仅靠 domain 5 输入产生的零梯度不足以保证其他行不被 AdamW weight decay 改写。

## 产物与失败分流

- 产物：`artifacts/g0/r03/R03_action_contract.json`
- 数据 schema 不兼容：使用已提交的 JSONL/per-episode fallback，不修改资产。
- TorchCodec 找不到 CUDA 库：只修正启动级 `LD_LIBRARY_PATH`。
- checkpoint 数值 forward 不在本 Gate 重复执行，进入 R04。
- 回填 `SESSION.md`、`TODO.md`；独立审查通过前保持 `REVIEW`。
