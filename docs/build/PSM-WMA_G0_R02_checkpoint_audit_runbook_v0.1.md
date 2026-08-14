# PSM-WMA G0-R02 Checkpoint Audit Runbook v0.1

状态：`reviewed`

## 目的

在不重复执行全量权重数值 diff 的前提下，核验 Cosmos3-Edge-Policy-DROID 的配置、根索引和 safetensors header，冻结 Edge→LIBERO 的 warm-start 边界。

## 前置资产

- checkpoint：`/gemini/code/models/Cosmos3-Edge-Policy-DROID`
- Python：`/root/venvs/psm_wma/bin/python`
- 审计入口：`tools/g0/audit_r02_checkpoints.py`
- 复用配置：`EDGE_MODEL_CONFIG` 与官方 `action_policy_libero_nano` recipe

## 精确命令

工作目录：`/gemini/code/psm_wma`。不使用 GPU，不访问外网。

```bash
/root/venvs/psm_wma/bin/python tools/g0/audit_r02_checkpoints.py \
  --checkpoint /gemini/code/models/Cosmos3-Edge-Policy-DROID \
  --output artifacts/g0/r02/R02_edge_policy_checkpoint_audit.json
```

## 输入与输出 Schema

输入为 checkpoint 根目录下的 `config.json`、`checkpoint.json`、`model.safetensors.index.json` 及索引引用的 safetensors header。脚本不读取完整张量值。

输出 JSON 的关键字段为：`gate`、`status`、`provenance`、`facts`、`warm_start_decision`、`blockers`。`provenance` 必须记录 UTC 时间、根仓库与 Cosmos commit、脚本路径与 SHA-256、完整 argv 和 run_config。

## 断言和判据

- 原始根索引中的旧导出 K-Norm 别名必须被识别；复用
  `cosmos_framework.inference.model._diffusers_weight_map` 的兼容语义后，每个有效索引键必须存在于引用 shard 的 header。
- action 模型结构必须保留 `action_gen`、action head 和 Edge K-Norm 配置。
- DROID 的 15 Hz、chunk 32、domain 不得冒充 LIBERO 数据契约。
- LIBERO 采用 20 Hz、chunk 16、frame-wise-relative rot6d、`quantile_rot`、agentview+wrist。

`PASS`：项目支持入口生成的有效索引全部可解析，且 warm-start/数据契约均可从本地配置复核。原始发布索引中的已知陈旧别名必须作为事实保留，不得直接误判为文件缺失。

`FAIL`：资产内容与期望模型结构冲突，不能形成安全的 Edge warm-start。

`BLOCKED`：应用项目现有兼容语义后仍有索引问题阻止 checkpoint load。

## 失败分流

- shard 缺失：回到资产准备，不修改模型配置。
- 原始索引键与 header 不一致：先核对支持入口是否已有旧导出兼容；不得修改原始 checkpoint。
- `inference2/_model_io.py` 未同步兼容：记录为入口限制，使用 `cosmos_framework.inference.model`；若后续必须使用 inference2，再单独立项同步。
- 模型字段不一致：停止 R04，回到 R03 配置设计。

## 产物与回填

- 机器可读产物：`artifacts/g0/r02/R02_edge_policy_checkpoint_audit.json`
- 回填：`SESSION.md`、`TODO.md`
- R02 进入 `REVIEW` 前必须关闭全部 blocker，并补做真实 checkpoint load smoke，或显式引用 G0-R01 使用同一受支持入口完成的实际 checkpoint 加载与 finite Policy 推理证据。
