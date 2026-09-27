# V3 Stage B2-C R3 Stage-A Text Transform — Implementation

- Gate `V3-STAGE-B2C-R3-STAGE-A-TEXT-TRANSFORM`，状态 `REVIEW`；本记录不构成 GPU 执行批准或 closure。
- 唯一设计 authority：root `3091df07983d15f4ecad3a30b27fd721522aede4` 的 R3 v0.1。run03 原始 Evidence 保持不变，原执行 pair 仍为 root `5cc69c6fa9e5b4f13aa6b2e4b180ec329c874d61` / child `8029b5ff002a350d22ee955db0463cc2e2d3665a`。
- 本轮 child `f8b81133f22ab01197b7b36003207cf5cfeb2e41` 已推送 `v3-local-ttt`；root Gitlink 指向该 SHA。ChatGPT 设计/审核；用户 owner/最终裁决；cx 实现；ds 执行/测试。

## 实际变更

child 只修改 `examples/psm_wma_robocasa_local_s1.py` 与对应 `_test.py`。保留 CloseFridge ep0 的 raw dataset、frame/index/raw12→raw15 与 16 个 overlap 校验。完成这些校验后，从冻结 Stage-A `config.yaml` 通过 `LazyConfig.load` 读取 RoboCasa 数据配置，构建同一 `ActionTransformPipeline`，以 `random.seed(0)` 对每个原始 payload 的深拷贝执行转换。native callback 只接收转换后的 RGB payload；cached latent 仍仅供 B0 evidence。

转换结果逐 consumer 检查非空 `text_token_ids`、WAM `sequence_plan`、`action_raw=[33,15]`、model-space `action=[33,64]`、RGB/33 帧与单样本 collate。预检 JSON 记录 seed、consumer0 的结构化 caption、token count/SHA256、plan 与动作形状。CFG dropout 保持 Stage-A 的 0.1；固定 seed 只用于此确定性 wiring smoke，任一空 caption 即失败。

## CPU/static Evidence

- V3 `.venv/bin/python`、无 GPU/离线、`-c /dev/null --noconftest -p no:cacheprovider`：R3/B0/B1/B2-A/B2-B/B2-C/R1-A/R1-B 十文件 suite **207/207 PASS**；Stage-A 合同测试另进程 **26/26 PASS**（另有 10 subtests PASS）。Stage-A 测试进程结束时全局 `torch.is_grad_enabled()` 为 `False`，故它与 Local 梯度测试不在同一 Python 进程混跑；该混跑产生的 45 个 grad-mode 失败不是验收证据。
- 真实资产 CPU `--preflight` PASS：`/tmp/cx_v3_b2c_r3_preflight_20260927_01/result.json`。DCP metadata 549 keys、ep0 429 帧、raw15、16 个 payload；consumer0 结构化 caption、152 个文本 token、SHA256 `854e3c085df7ab1b392c0e4960875673123b22e5afd4d051c11c9ac119380aad`、`action=[33,64]`、`action_raw=[33,15]`；CUDA trace 为空。
- 修改的两文件 Ruff check/format PASS；child 与 root `git diff --check` PASS。

## 后续边界

未运行 GPU、模型权重载入、DCP load、VAE forward、optimizer step、训练或评测。待 ChatGPT 与 ds 对 fresh pair 做 CPU/static 审核；只有新的明确批准才可由 ds 在全新目录执行一次 RTX4090 S1 run04，不重跑 run03。此轮不自授 closure。
