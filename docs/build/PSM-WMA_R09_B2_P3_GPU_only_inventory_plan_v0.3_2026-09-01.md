# R09-B2 P3 GPU-only Optimizer Inventory Gate 方案 v0.3

**状态**：DRAFT；替代 v0.2 的本地 processor/tokenizer 例外定义。仅请求方案补充审核，禁止 GPU 执行。

## v0.3 精确本地只读例外与硬边界

真实 `OmniMoTModel` 无条件构造 `vlm_config.tokenizer`。因此唯一允许的 tokenizer 行为是：只读构造 recipe 实际 `Cosmos3-Edge` processor/tokenizer 配置，且 `EDGE_POLICY_CHECKPOINT` 必须是已存在的本地目录。此例外不包含 dataloader、VAE、tokenizer/model 权重、数据或 base checkpoint 的加载。

collector 必须在任何模型构造前执行以下 fail-closed gate，并将各项的路径与结果写入 artifact；verifier 必须逐项硬校验：

1. 断言 `EDGE_POLICY_CHECKPOINT` 是本地目录，并以该绝对路径设置 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1` 和 `HUGGINGFACE_HUB_CACHE=<EDGE_POLICY_CHECKPOINT>`；任一环境变量缺失、值不相等或路径不合格即 `BLOCKED`。
2. 断言该目录直接包含四个常规文件：`tokenizer.json`、`tokenizer_config.json`、`chat_template.jinja`、`special_tokens_map.json`；任一缺失即 `BLOCKED`，不得尝试下载、补全或替代。
3. 仅允许构造 recipe-resolved 的 production processor/tokenizer；若构造尝试非本地 repository/revision、remote code 或网络资源，立即 `BLOCKED`。禁止 monkeypatch、synthetic processor 或替代 tokenizer。
4. `BaseVLMProcessor` 的非目录下载分支，以及任何模型权重、VAE、dataloader、数据、base-checkpoint 访问均立即 `BLOCKED`。例外不得绕过 v0.1 第 11–14 行的其余禁止项。

上述 gate 只允许读取本地 tokenizer 配置文件，不允许加载 tokenizer 权重或模型权重。它们是 v0.1 中“无 VAE/tokenizer/data/base-checkpoint 加载”对生产构造路径的精确、最小例外，不改变该项的其他禁止范围。

## 保持不变的 v0.1 合同

除这一精确例外外，v0.1 的全部冻结执行面、verifier-owned recurrent-only prefix、空 selector exclusions、实际 optimizer/state/DCP membership、TTT 五成员排除、单卡 24 GiB 上限和运行二次审批保持不变。尤其不得执行 forward、backward、optimizer/scheduler step、DCP save/load、checkpoint 写入、训练 callback、训练、评测、推理或网络访问。

## 请求

请求确认此例外后，仍仅允许 root-side collector/verifier/tests 实现；GPU 运行继续需要单独 `APPROVE_TO_RUN_GPU_ONLY_P3_GATE`。不授权 B2-T、P4/P5、训练、评测、推理或 checkpoint save/load。
