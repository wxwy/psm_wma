# R09-B2 P3 GPU-only Optimizer Inventory Gate 方案 v0.2

**状态**：DRAFT；替代 v0.1 的 tokenizer 初始化歧义。仅请求方案补充审核，禁止 GPU 执行。

## v0.2 例外与硬边界

真实 `OmniMoTModel` 无条件构造 `vlm_config.tokenizer`。因此唯一允许的 tokenizer 行为是：`EDGE_POLICY_CHECKPOINT` 必须为已存在的本地目录，且只读构造该 recipe 实际 `Cosmos3-Edge` processor/tokenizer 配置。该构造不读取模型权重、VAE、数据或 base checkpoint。

collector 必须在任何模型构造前断言该目录存在；`BaseVLMProcessor` 的非目录下载分支、任何网络请求、任何权重/VAE/数据/base-checkpoint 访问均立即 `BLOCKED`。禁止 monkeypatch、synthetic processor 或替代 tokenizer。

除这一精确例外外，v0.1 的全部冻结执行面、verifier-owned prefix、空 selector exclusions、state/DCP/TTT 五成员、单卡 24GiB 上限及运行二次审批保持不变。

## 请求

请求确认此例外后，仍仅允许 root-side collector/verifier/tests 实现；GPU 运行继续需要单独 `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`。不授权 B2-T、P4/P5、训练、评测、推理或 checkpoint save/load。
